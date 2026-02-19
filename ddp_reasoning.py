"""
Distributed OWL Reasoning with Query Decomposition
==================================================

Additional dependency: pip install ray

Overview
--------
This module implements distributed OWL instance retrieval over horizontally
sharded ontologies using Ray as the distributed computing backend.

The core idea is *query decomposition*: instead of sending a full OWL class
expression (CE) to a single reasoner, the coordinator breaks the CE into atomic
sub-queries, dispatches each sub-query to every shard in parallel, and then
combines the results (union / intersection / set-difference) locally. This
allows reasoning over datasets that are too large for a single machine and
delivers super-linear speedups for complex union queries.

Architecture
------------
  ShardReasoner (Ray actor, one per shard)
      Wraps a SyncReasoner (Pellet / HermiT) for a single .owl shard.
      Exposes atomic query methods that return plain IRI strings so that
      results can be serialised across the Ray object store without issues.

  DistributedReasoner (coordinator, runs on the driver)
      Accepts any OWLClassExpression and recursively decomposes it into
      atomic sub-queries via singledispatch.  Supported constructors:
        OWLClass, OWLObjectIntersectionOf, OWLObjectUnionOf,
        OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom,
        OWLObjectComplementOf, OWLObjectHasValue, OWLObjectOneOf,
        OWLObjectMinCardinality, OWLObjectMaxCardinality,
        OWLObjectExactCardinality

  shard_ontology (utility, from shard_ontology.py)
      Splits an ontology into N shards: the TBox is replicated in every
      shard while the ABox is partitioned round-robin across shards.
      Called automatically on first run if the shard files are missing.

Usage
-----
  # Fully automatic — no terminal setup needed:
  python ddp_reasoning.py --auto_ray --num_shards 8

  # Use a different ontology / namespace:
  python ddp_reasoning.py --auto_ray --num_shards 4 \\
      --base /path/to/KG --ns http://example.org/myonto# \\
      --reasoner HermiT

  # Manual Ray cluster (start Ray head node first in a separate terminal):
  #   ray start --head --port=6379 \\
  #       --resources='{"shard_0":1,"shard_1":1,"shard_2":1,"shard_3":1}'
  python ddp_reasoning.py --num_shards 4

CLI Arguments
-------------
  --base          Base directory that contains the ontology and shard files.
  --ontology      Explicit path to the source ontology
                  (default: <base>/<stem>.owl, inferred from --base).
  --num_shards    Number of shards / Ray workers  (default: 1).
  --ns            Namespace URI prefix for the ontology  (default: Mutagenesis).
  --reasoner      OWL reasoner backend: Pellet (default) or HermiT.
  --auto_ray      When set, Ray is initialised in-process using all available
                  CPU cores and the required shard custom resources.
                  Shard .owl files are generated automatically if missing.
                  When not set, the script connects to an existing Ray cluster
                  started via `ray start --head ...`.

Distributed Setup (multi-machine)
----------------------------------
Each physical machine runs `ray start` in its own terminal. The head node
registers shard_0; every additional worker registers its own shard resource.
The driver script can then be run from any machine that can reach the head.

  2 machines (1 shard each):
    Machine 1: ray start --head --port=6379 --resources='{"shard_0": 1}'
    Machine 2: ray start --address='<HEAD_IP>:6379' --resources='{"shard_1": 1}'
    Driver:    python ddp_reasoning.py --num_shards 2

  4 machines (1 shard each):
    Machine 1: ray start --head --port=6379 --resources='{"shard_0": 1}'
    Machine 2: ray start --address='<HEAD_IP>:6379' --resources='{"shard_1": 1}'
    Machine 3: ray start --address='<HEAD_IP>:6379' --resources='{"shard_2": 1}'
    Machine 4: ray start --address='<HEAD_IP>:6379' --resources='{"shard_3": 1}'
    Driver:    python ddp_reasoning.py --num_shards 4

  8 machines (1 shard each):
    Machine 1: ray start --head --port=6379 --resources='{"shard_0": 1}'
    Machine 2: ray start --address='<HEAD_IP>:6379' --resources='{"shard_1": 1}'
    Machine 3: ray start --address='<HEAD_IP>:6379' --resources='{"shard_2": 1}'
    Machine 4: ray start --address='<HEAD_IP>:6379' --resources='{"shard_3": 1}'
    Machine 5: ray start --address='<HEAD_IP>:6379' --resources='{"shard_4": 1}'
    Machine 6: ray start --address='<HEAD_IP>:6379' --resources='{"shard_5": 1}'
    Machine 7: ray start --address='<HEAD_IP>:6379' --resources='{"shard_6": 1}'
    Machine 8: ray start --address='<HEAD_IP>:6379' --resources='{"shard_7": 1}'
    Driver:    python ddp_reasoning.py --num_shards 8

  Multiple shards per machine (declare several resources on one node):
    Machine 1: ray start --head --port=6379 \
                   --resources='{"shard_0":1,"shard_1":1,"shard_2":1,"shard_3":1}'
    Driver:    python ddp_reasoning.py --num_shards 4

Docs: https://docs.ray.io/en/latest/ray-core/configure.html#cluster-resources
"""

import argparse
import os
import ray
from functools import singledispatchmethod
from pathlib import Path
from shard_ontology import shard_ontology
from typing import Set, FrozenSet, List, Dict, Tuple, Iterable
from owlapy.owl_reasoner import SyncReasoner
from owlapy.class_expression import (
    OWLClassExpression, OWLClass, OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom,
    OWLObjectUnionOf, OWLObjectIntersectionOf, OWLObjectComplementOf,
    OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality,
    OWLObjectHasValue, OWLObjectOneOf, OWLThing, OWLNothing
)
from owlapy.owl_property import OWLObjectProperty, OWLObjectPropertyExpression, OWLObjectInverseOf
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.iri import IRI


@ray.remote
class ShardReasoner:
    """
    A Ray actor that wraps a SyncReasoner for a single data shard.
    Provides atomic query methods that return local results.
    """
    
    def __init__(self, shard_id: str, ontology_path: str, reasoner: str = "Pellet"):
        self.shard_id = shard_id
        self.ontology_path = ontology_path
        self.sync_reasoner = SyncReasoner(ontology=ontology_path, reasoner=reasoner)
        print(f"--- Shard {shard_id} initialized with {reasoner} reasoner ---")
    
    def get_shard_id(self) -> str:
        return self.shard_id
    
    # ========== Atomic Query Methods (all return IRI strings) ==========
    
    def query_instances(self, ce: OWLClassExpression, direct: bool = False) -> Set[str]:
        """Pass a full CE directly to this shard's reasoner (no decomposition).
        Used in open-world mode where each shard evaluates independently."""
        return {ind.str for ind in self.sync_reasoner.instances(ce, direct=direct)}
    
    def get_class_instances_iris(self, class_iri: str, direct: bool = False) -> Set[str]:
        """Get instances of a named class from this shard (as IRI strings)."""
        owl_class = OWLClass(class_iri)
        return {ind.str for ind in self.sync_reasoner.instances(owl_class, direct=direct)}
    
    def get_all_individual_iris(self) -> Set[str]:
        """Get all individuals known to this shard (as IRI strings)."""
        return {ind.str for ind in self.sync_reasoner.get_root_ontology().individuals_in_signature()}
    
    def get_object_property_subjects(
        self, 
        property_iri: str,
        is_inverse: bool,
        object_iris: Set[str]
    ) -> Set[str]:
        """
        Get all subjects x such that (x, property, o) for some o in objects.
        This is the key method for resolving ∃ r.C across shards.
        Uses IRI strings to avoid cross-session equality issues.
        """
        # Reconstruct property on the shard side
        prop = OWLObjectProperty(property_iri)
        if is_inverse:
            prop = OWLObjectInverseOf(prop)
        
        subjects = set()
        for ind in self.sync_reasoner.get_root_ontology().individuals_in_signature():
            for obj in self.sync_reasoner.object_property_values(ind, prop):
                if obj.str in object_iris:
                    subjects.add(ind.str)
                    break
        return subjects
    
    def get_object_property_map(
        self, 
        property_iri: str,
        is_inverse: bool
    ) -> Dict[str, Set[str]]:
        """
        Get a mapping of subject IRI -> set of object IRIs for a given property.
        Uses IRI strings to avoid cross-session equality issues.
        """
        # Reconstruct property on the shard side
        prop = OWLObjectProperty(property_iri)
        if is_inverse:
            prop = OWLObjectInverseOf(prop)
        
        prop_map = {}
        for ind in self.sync_reasoner.get_root_ontology().individuals_in_signature():
            objects = {obj.str for obj in self.sync_reasoner.object_property_values(ind, prop)}
            if objects:
                prop_map[ind.str] = objects
        return prop_map
    


class DistributedReasoner:
    """
    A coordinator that performs distributed OWL reasoning by decomposing complex
    class expressions into atomic queries, dispatching them to shards, and 
    aggregating results.
    
    This approach solves the cross-shard inference problem by:
    1. Breaking down complex queries (e.g., Male ⊓ ∃ hasChild.Parent)
    2. Gathering atomic results from ALL shards (e.g., all Males, all Parents, all hasChild relations)
    3. Computing the final answer by joining/intersecting the gathered data
    """
    
    def __init__(self, shards: List[ray.actor.ActorHandle], open_world: bool = False):
        """
        Args:
            shards: List of ShardReasoner actor handles
            open_world: If True, pass full CEs directly to each shard and union
                        results (no recursive decomposition). If False, use
                        closed-world recursive decomposition (default).
        """
        self.shards = shards
        self.open_world = open_world
        print(f"DistributedReasoner initialized with {len(shards)} shards (open_world={open_world})")
    
    def instances(self, ce: OWLClassExpression, direct: bool = False) -> Set[OWLNamedIndividual]:
        """
        Get all instances of a class expression.
        
        If open_world=True: pass the full CE to each shard and union results.
        If open_world=False: decompose the query and gather results from all shards.
        """
        if self.open_world:
            # Open-world: each shard evaluates the full CE independently, union results
            futures = [shard.query_instances.remote(ce, direct) for shard in self.shards]
            results = ray.get(futures)
            iris = set().union(*results) if results else set()
        else:
            # Closed-world: recursive decomposition
            iris = self._find_instance_iris(ce, direct)
        return {OWLNamedIndividual(iri) for iri in iris}
    
    def _gather_iris_from_all_shards(self, method_name: str, *args) -> Set[str]:
        """Helper to call a method on all shards and union the IRI results."""
        futures = [getattr(shard, method_name).remote(*args) for shard in self.shards]
        results = ray.get(futures)
        return set().union(*results) if results else set()
    
    def _gather_property_maps(
        self, 
        property_expr: OWLObjectPropertyExpression
    ) -> Dict[str, Set[str]]:
        """Gather property maps from all shards and merge them (using IRI strings)."""
        # Extract IRI and inverse flag for serialization
        is_inverse = isinstance(property_expr, OWLObjectInverseOf)
        prop_iri = property_expr.get_named_property().str if is_inverse else property_expr.str
        
        futures = [shard.get_object_property_map.remote(prop_iri, is_inverse) for shard in self.shards]
        results = ray.get(futures)
        
        merged = {}
        for prop_map in results:
            for subj_iri, obj_iris in prop_map.items():
                if subj_iri in merged:
                    merged[subj_iri] |= obj_iris
                else:
                    merged[subj_iri] = set(obj_iris)
        return merged
    
    @singledispatchmethod
    def _find_instance_iris(self, ce: OWLClassExpression, direct: bool = False) -> Set[str]:
        """Dispatch based on class expression type. Returns IRI strings."""
        raise NotImplementedError(f"Instances not implemented for {type(ce)}")
    
    @_find_instance_iris.register
    def _(self, ce: OWLClass, direct: bool = False) -> Set[str]:
        """
        Atomic class: Gather instances from all shards (as IRI strings).
        """
        if ce.is_owl_thing():
            return self._gather_iris_from_all_shards("get_all_individual_iris")
        return self._gather_iris_from_all_shards("get_class_instances_iris", ce.str, direct)
    
    @_find_instance_iris.register
    def _(self, ce: OWLObjectIntersectionOf, direct: bool = False) -> Set[str]:
        """
        Intersection (A ⊓ B): Compute intersection of instances.
        
        For Male ⊓ ∃ hasChild.Parent:
        1. Get all Males from all shards
        2. Get all ∃ hasChild.Parent instances (recursively decomposed)
        3. Return intersection
        """
        result = None
        for operand in ce.operands():
            operand_iris = self._find_instance_iris(operand, direct)
            if result is None:
                result = operand_iris
            else:
                result &= operand_iris
        return result if result else set()
    
    @_find_instance_iris.register
    def _(self, ce: OWLObjectUnionOf, direct: bool = False) -> Set[str]:
        """
        Union (A ⊔ B): Compute union of instances.
        """
        result = set()
        for operand in ce.operands():
            result |= self._find_instance_iris(operand, direct)
        return result
    
    @_find_instance_iris.register
    def _(self, ce: OWLObjectSomeValuesFrom, direct: bool = False) -> Set[str]:
        """
        Existential restriction (∃ r.C): 
        Find all x such that ∃ y: (x, r, y) ∧ C(y)
        
        This is the KEY method for cross-shard reasoning!
        
        For ∃ hasChild.Parent:
        1. Get all Parents from ALL shards (the filler instances)
        2. Get all hasChild relations from ALL shards
        3. Find subjects whose objects are in the Parent set
        """
        property_expr = ce.get_property()
        filler = ce.get_filler()
        
        # Step 1: Get instances of the filler from ALL shards (as IRI strings)
        filler_iris = self._find_instance_iris(filler, direct)
        
        if not filler_iris:
            return set()
        
        # Step 2: Find subjects that have at least one filler instance as object
        # Extract IRI and inverse flag for serialization
        is_inverse = isinstance(property_expr, OWLObjectInverseOf)
        prop_iri = property_expr.get_named_property().str if is_inverse else property_expr.str
        
        futures = [
            shard.get_object_property_subjects.remote(prop_iri, is_inverse, filler_iris)
            for shard in self.shards
        ]
        results = ray.get(futures)
        return set().union(*results) if results else set()
    
    @_find_instance_iris.register
    def _(self, ce: OWLObjectAllValuesFrom, direct: bool = False) -> Set[str]:
        """
        Universal restriction (∀ r.C):
        Equivalent to ¬(∃ r.¬C)
        """
        complement_ce = OWLObjectSomeValuesFrom(
            property=ce.get_property(),
            filler=OWLObjectComplementOf(ce.get_filler())
        )
        all_iris = self._gather_iris_from_all_shards("get_all_individual_iris")
        some_iris = self._find_instance_iris(complement_ce, direct)
        return all_iris - some_iris
    
    @_find_instance_iris.register
    def _(self, ce: OWLObjectComplementOf, direct: bool = False) -> Set[str]:
        """
        Complement (¬C): All individuals minus instances of C.
        """
        all_iris = self._gather_iris_from_all_shards("get_all_individual_iris")
        operand_iris = self._find_instance_iris(ce.get_operand(), direct)
        return all_iris - operand_iris
    
    @_find_instance_iris.register
    def _(self, ce: OWLObjectHasValue, direct: bool = False) -> Set[str]:
        """
        Has value (∃ r.{a}): Equivalent to ∃ r.{a}
        """
        return self._find_instance_iris(ce.as_some_values_from(), direct)
    
    @_find_instance_iris.register
    def _(self, ce: OWLObjectOneOf, direct: bool = False) -> Set[str]:
        """
        Nominal ({a, b, c}): Just return the individuals as IRIs.
        """
        return {ind.str for ind in ce.individuals()}
    
    @_find_instance_iris.register
    def _(self, ce: OWLObjectMinCardinality, direct: bool = False) -> Set[str]:
        """
        Min cardinality (≥n r.C): Subjects with at least n r-successors in C.
        """
        return self._find_cardinality_iris(ce, direct)
    
    @_find_instance_iris.register
    def _(self, ce: OWLObjectMaxCardinality, direct: bool = False) -> Set[str]:
        """
        Max cardinality (≤n r.C): Subjects with at most n r-successors in C.
        """
        return self._find_cardinality_iris(ce, direct)
    
    @_find_instance_iris.register
    def _(self, ce: OWLObjectExactCardinality, direct: bool = False) -> Set[str]:
        """
        Exact cardinality (=n r.C): Subjects with exactly n r-successors in C.
        """
        return self._find_cardinality_iris(ce, direct)
    
    def _find_cardinality_iris(self, ce, direct: bool = False) -> Set[str]:
        """
        Handle cardinality restrictions by gathering property maps and filler instances.
        """
        property_expr = ce.get_property()
        filler = ce.get_filler()
        cardinality = ce.get_cardinality()
        
        # Get filler instances from all shards (as IRI strings)
        filler_iris = self._find_instance_iris(filler, direct)
        
        # Get property map from all shards (merged, using IRI strings)
        prop_map = self._gather_property_maps(property_expr)
        
        # Determine min/max based on restriction type
        if isinstance(ce, OWLObjectMinCardinality):
            min_count, max_count = cardinality, None
        elif isinstance(ce, OWLObjectMaxCardinality):
            min_count, max_count = 0, cardinality
        else:  # ExactCardinality
            min_count, max_count = cardinality, cardinality
        
        # Find subjects meeting the cardinality constraint
        result = set()
        all_iris = self._gather_iris_from_all_shards("get_all_individual_iris")
        
        for subj_iri in all_iris:
            obj_iris = prop_map.get(subj_iri, set())
            count = len(obj_iris & filler_iris)
            if count >= min_count and (max_count is None or count <= max_count):
                result.add(subj_iri)
        
        return result



# Timing Benchmark


def run_timing_benchmark(
    ground_truth_reasoner: SyncReasoner,
    dist_reasoner: DistributedReasoner,
    queries: List[Tuple[str, OWLClassExpression]]
) -> List[Dict]:
    """
    Run timing comparison between ground truth and distributed reasoner.
    
    Args:
        ground_truth_reasoner: SyncReasoner with complete ontology
        dist_reasoner: DistributedReasoner with sharded data
        queries: List of (name, OWLClassExpression) tuples
    
    Returns:
        List of timing result dictionaries
    """
    import time
    
    def to_iri_set(individuals: Set[OWLNamedIndividual]) -> Set[str]:
        return {ind.str for ind in individuals}
    
    print("\n" + "=" * 90)
    print("TIMING BENCHMARK: Ground Truth vs Distributed Reasoning")
    print("=" * 90)
    
    timing_results = []
    
    for query_name, query in queries:
        # Time ground truth
        gt_start = time.perf_counter()
        gt_results = to_iri_set(ground_truth_reasoner.instances(query))
        gt_time = time.perf_counter() - gt_start
        
        # Time distributed
        dist_start = time.perf_counter()
        dist_results = to_iri_set(dist_reasoner.instances(query))
        dist_time = time.perf_counter() - dist_start
        
        # Verify correctness
        match = gt_results == dist_results
        speedup = gt_time / dist_time if dist_time > 0 else float('inf')
        
        timing_results.append({
            'query': query_name,
            'gt_time': gt_time,
            'dist_time': dist_time,
            'speedup': speedup,
            'count': len(gt_results),
            'match': match
        })
        
        status = "✓" if match else "✗"
        icon = "⚡" if speedup > 1 else "🐢"
        print(f"\n{status} {query_name}")
        print(f"   Results: {len(gt_results):>6} instances | GT: {gt_time*1000:>8.1f}ms | Dist: {dist_time*1000:>8.1f}ms | {speedup:>5.1f}x {icon}")
        
        if not match:
            missing = len(gt_results - dist_results)
            extra = len(dist_results - gt_results)
            print(f"   ⚠️  MISMATCH: {missing} missing, {extra} extra")
    
    # Summary table
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print(f"{'Query':<55} {'Count':>6} {'GT(ms)':>9} {'Dist(ms)':>9} {'Speedup':>8}")
    print("-" * 90)
    
    total_gt = sum(r['gt_time'] for r in timing_results)
    total_dist = sum(r['dist_time'] for r in timing_results)
    
    for r in timing_results:
        icon = "⚡" if r['speedup'] > 1 else ""
        print(f"{r['query']:<55} {r['count']:>6} {r['gt_time']*1000:>9.1f} {r['dist_time']*1000:>9.1f} {r['speedup']:>7.2f}x {icon}")
    
    print("-" * 90)
    total_speedup = total_gt / total_dist if total_dist > 0 else 0
    print(f"{'TOTAL':<55} {'':>6} {total_gt*1000:>9.1f} {total_dist*1000:>9.1f} {total_speedup:>7.2f}x {'⚡' if total_speedup > 1 else ''}")
    print("=" * 90)
    
    all_passed = all(r['match'] for r in timing_results)
    if all_passed:
        print("✓ All queries returned correct results!")
    else:
        print("✗ Some queries had mismatches!")
    
    return timing_results


def main(args):
    """Setup reasoners and run benchmark with complex class expressions."""
    
    # Configuration 
    BASE = args.base
    ORIGINAL_ONTOLOGY = args.ontology if args.ontology else f"{BASE}/mutagenesis.owl"
    NUM_SHARDS = args.num_shards
    NS = args.ns
    
    # Setup Reasoners 
    print("=" * 60)
    print(f"SETUP: Initializing Reasoners")
    print(f"  - Ground Truth: SyncReasoner (Pellet) on complete ontology")
    print(f"  - Distributed:  {NUM_SHARDS} shard(s)")
    print("=" * 60)
    
    print("\n[1/2] Loading ground truth reasoner (complete ontology)...")
    ground_truth_reasoner = SyncReasoner(ontology=ORIGINAL_ONTOLOGY, reasoner=args.reasoner)
    
    # Derive shard filename prefix from the ontology stem (e.g. "mutagenesis" → "mutagenesis_shard_0.owl")
    ONTOLOGY_STEM = Path(ORIGINAL_ONTOLOGY).stem

    print(f"[2/2] Creating distributed reasoner with {NUM_SHARDS} shard(s)...")

    # Auto-generate shard files if any are missing (single call creates all shards)
    if NUM_SHARDS > 1:
        first_shard = Path(BASE) / f"{ONTOLOGY_STEM}_shard_0.owl"
        if not first_shard.exists():
            print(f"  [auto-shard] Shard files not found — generating {NUM_SHARDS} shards from {ORIGINAL_ONTOLOGY}...")
            shard_ontology(ORIGINAL_ONTOLOGY, NUM_SHARDS, BASE)
            print(f"  [auto-shard] Done.")

    shards = []
    for i in range(NUM_SHARDS):
        if NUM_SHARDS == 1:
            shard_path = ORIGINAL_ONTOLOGY
        else:
            shard_path = str(Path(BASE) / f"{ONTOLOGY_STEM}_shard_{i}.owl")
        # Each shard pinned to its own Ray node via resource constraint
        shard = ShardReasoner.options(resources={f"shard_{i}": 1}).remote(f"Shard-{i}", shard_path, args.reasoner)
        shards.append(shard)
    
    dist_reasoner = DistributedReasoner(shards)
    
    # Define Classes and Properties 
    atom = OWLClass(IRI(NS, 'Atom'))
    bond = OWLClass(IRI(NS, 'Bond'))
    carbon = OWLClass(IRI(NS, 'Carbon'))
    nitrogen = OWLClass(IRI(NS, 'Nitrogen'))
    oxygen = OWLClass(IRI(NS, 'Oxygen'))
    hydrogen = OWLClass(IRI(NS, 'Hydrogen'))
    ring = OWLClass(IRI(NS, 'Ring'))
    benzene = OWLClass(IRI(NS, 'Benzene'))
    bond1 = OWLClass(IRI(NS, 'Bond-1'))
    bond2 = OWLClass(IRI(NS, 'Bond-2'))
    bond3 = OWLClass(IRI(NS, 'Bond-3'))
    
    has_atom = OWLObjectProperty(IRI(NS, 'hasAtom'))
    has_bond = OWLObjectProperty(IRI(NS, 'hasBond'))
    has_structure = OWLObjectProperty(IRI(NS, 'hasStructure'))
    in_bond = OWLObjectProperty(IRI(NS, 'inBond'))
    
    # HIGHLY COMPLEX Class Expressions 
    complex_queries = [
        # UNIONS
        
        # 2-way union
        ("∃hasAtom.Carbon ⊔ ∃hasAtom.Nitrogen",
         OWLObjectUnionOf([
             OWLObjectSomeValuesFrom(property=has_atom, filler=carbon),
             OWLObjectSomeValuesFrom(property=has_atom, filler=nitrogen)
         ])),
        
        # 3-way union
        ("∃hasAtom.Carbon ⊔ ∃hasAtom.Nitrogen ⊔ ∃hasAtom.Oxygen",
         OWLObjectUnionOf([
             OWLObjectSomeValuesFrom(property=has_atom, filler=carbon),
             OWLObjectSomeValuesFrom(property=has_atom, filler=nitrogen),
             OWLObjectSomeValuesFrom(property=has_atom, filler=oxygen)
         ])),
        
        # 4-way union
        ("∃hasAtom.(C ⊔ N ⊔ O ⊔ H)",
         OWLObjectSomeValuesFrom(
             property=has_atom,
             filler=OWLObjectUnionOf([carbon, nitrogen, oxygen, hydrogen])
         )),
        
        # NESTED EXISTENTIALS 
        
        # Depth 2: atoms in bonds
        ("∃hasAtom.(Carbon ⊓ ∃inBond.Bond)",
         OWLObjectSomeValuesFrom(
             property=has_atom,
             filler=OWLObjectIntersectionOf([
                 carbon,
                 OWLObjectSomeValuesFrom(property=in_bond, filler=bond)
             ])
         )),
        
        # Depth 2: atoms in specific bond types
        ("∃hasAtom.(Carbon ⊓ ∃inBond.Bond-1)",
         OWLObjectSomeValuesFrom(
             property=has_atom,
             filler=OWLObjectIntersectionOf([
                 carbon,
                 OWLObjectSomeValuesFrom(property=in_bond, filler=bond1)
             ])
         )),
        
        # COMPLEX UNIONS WITH INTERSECTIONS 
        
        # Union of intersections
        ("(∃hasAtom.C ⊓ ∃hasBond.Bond) ⊔ (∃hasAtom.N ⊓ ∃hasBond.Bond)",
         OWLObjectUnionOf([
             OWLObjectIntersectionOf([
                 OWLObjectSomeValuesFrom(property=has_atom, filler=carbon),
                 OWLObjectSomeValuesFrom(property=has_bond, filler=bond)
             ]),
             OWLObjectIntersectionOf([
                 OWLObjectSomeValuesFrom(property=has_atom, filler=nitrogen),
                 OWLObjectSomeValuesFrom(property=has_bond, filler=bond)
             ])
         ])),
        
        # 3-way union of intersections
        ("(∃hasAtom.C ⊓ ∃hasBond.B) ⊔ (∃hasAtom.N ⊓ ∃hasBond.B) ⊔ (∃hasAtom.O ⊓ ∃hasBond.B)",
         OWLObjectUnionOf([
             OWLObjectIntersectionOf([
                 OWLObjectSomeValuesFrom(property=has_atom, filler=carbon),
                 OWLObjectSomeValuesFrom(property=has_bond, filler=bond)
             ]),
             OWLObjectIntersectionOf([
                 OWLObjectSomeValuesFrom(property=has_atom, filler=nitrogen),
                 OWLObjectSomeValuesFrom(property=has_bond, filler=bond)
             ]),
             OWLObjectIntersectionOf([
                 OWLObjectSomeValuesFrom(property=has_atom, filler=oxygen),
                 OWLObjectSomeValuesFrom(property=has_bond, filler=bond)
             ])
         ])),
        
        
        
        # Nested union in existential
        ("∃hasAtom.((Carbon ⊔ Nitrogen) ⊓ ∃inBond.Bond)",
         OWLObjectSomeValuesFrom(
             property=has_atom,
             filler=OWLObjectIntersectionOf([
                 OWLObjectUnionOf([carbon, nitrogen]),
                 OWLObjectSomeValuesFrom(property=in_bond, filler=bond)
             ])
         )),
        
        # Multiple properties with union
        ("(∃hasAtom.Carbon ⊓ ∃hasStructure.Ring) ⊔ (∃hasAtom.Nitrogen ⊓ ∃hasStructure.Ring)",
         OWLObjectUnionOf([
             OWLObjectIntersectionOf([
                 OWLObjectSomeValuesFrom(property=has_atom, filler=carbon),
                 OWLObjectSomeValuesFrom(property=has_structure, filler=ring)
             ]),
             OWLObjectIntersectionOf([
                 OWLObjectSomeValuesFrom(property=has_atom, filler=nitrogen),
                 OWLObjectSomeValuesFrom(property=has_structure, filler=ring)
             ])
         ])),
        
        #  4-way union with nested existentials
        ("∃hasAtom.(C⊓∃inBond.B1) ⊔ ∃hasAtom.(N⊓∃inBond.B1) ⊔ ∃hasAtom.(O⊓∃inBond.B1) ⊔ ∃hasAtom.(C⊓∃inBond.B2)",
         OWLObjectUnionOf([
             OWLObjectSomeValuesFrom(property=has_atom, filler=OWLObjectIntersectionOf([
                 carbon, OWLObjectSomeValuesFrom(property=in_bond, filler=bond1)])),
             OWLObjectSomeValuesFrom(property=has_atom, filler=OWLObjectIntersectionOf([
                 nitrogen, OWLObjectSomeValuesFrom(property=in_bond, filler=bond1)])),
             OWLObjectSomeValuesFrom(property=has_atom, filler=OWLObjectIntersectionOf([
                 oxygen, OWLObjectSomeValuesFrom(property=in_bond, filler=bond1)])),
             OWLObjectSomeValuesFrom(property=has_atom, filler=OWLObjectIntersectionOf([
                 carbon, OWLObjectSomeValuesFrom(property=in_bond, filler=bond2)]))
         ])),
    ]

    # TODO: CD:

    """
    A scenario:

Lets assume that we have a graph (TBOX, and fragment of ABOX) G_1, G_2

An expression: exists r1 (exists r2. {o3})


(o1 r1 o2) =Abox of G1

(o2 r2 o3) = Abox of G2

Hence, Abox of G1 and G2 contians only single triple each.

Can we return o1 if we retrieve the instance of exists r1 (exists r2. {o3}) ?

Answer: No for the time being

    """
    
    # Run Benchmark 
    run_timing_benchmark(ground_truth_reasoner, dist_reasoner, complex_queries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed OWL Reasoning with Query Decomposition")
    parser.add_argument(
        "--base",
        type=str,
        default="/home/cdemir/Desktop/Softwares/owlapy/KGs/Mutagenesis",
        help="Base directory for the ontology shards"
    )
    parser.add_argument(
        "--ontology",
        type=str,
        default=None,
        help="Path to the original ontology file (defaults to <base>/mutagenesis.owl)"
    )
    parser.add_argument(
        "--num_shards",
        type=int,
        default=1,
        help="Number of shards/workers (1 = baseline comparison, 2/4/8 for scaling)"
    )
    parser.add_argument(
        "--ns",
        type=str,
        default="http://dl-learner.org/mutagenesis#",
        help="Namespace URI for the ontology"
    )
    parser.add_argument(
        "--reasoner",
        type=str,
        default="Pellet",
        help="Reasoner to use (e.g. Pellet, HermiT)"
    )
    parser.add_argument(
        "--auto_ray",
        action="store_true",
        default=False,
        help=(
            "If set, Ray is initialised automatically in-process using all available "
            "CPU cores and the required shard custom resources. "
            "No 'ray start' terminal command is needed. "
            "Run this script with the desired Python interpreter directly, e.g.: "
            "/home/cdemir/anaconda3/envs/temp_owlapy/bin/python ddp_reasoning.py --auto_ray. "
            "If not set (default), the script connects to an already-running Ray cluster "
            "that was started manually via 'ray start --head ...'."
        )
    )
    args = parser.parse_args()

    if args.auto_ray:
        num_cpus = os.cpu_count()
        shard_resources = {f"shard_{i}": 1 for i in range(args.num_shards)}
        print(f"[auto_ray] Starting local Ray cluster with {num_cpus} CPUs and resources: {shard_resources}")
        ray.init(num_cpus=num_cpus, resources=shard_resources)
    else:
        print("[manual_ray] Connecting to existing Ray cluster (address='auto') ...")
        ray.init(address='auto')

    main(args)
