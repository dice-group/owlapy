"""
Distributed OWL Reasoning with Query Decomposition
==================================================

Additional dependency: pip install ray

Overview
--------
This module implements distributed OWL instance retrieval over horizontally
sharded ontologies using Ray as the distributed computing backend.

Two reasoning strategies are provided:

* **DistributedReasoner** — recursive query decomposition under Closed-World
  Assumption (CWA).  The coordinator breaks an OWL class expression (CE) into
  atomic sub-queries, dispatches each to every shard in parallel, and joins
  results (union / intersection / set-difference) locally.  Cardinality
  restrictions are resolved by counting distinct IRI role fillers across shards
  (CWA counting).

* **CrossShardReasoner** — bottom-up combining of per-shard intermediate
  results under the Open-World Assumption (OWA).  Each shard evaluates the CE
  *and all its sub-CEs* via Pellet, then the coordinator combines results
  bottom-up.  CE types that suffer from cross-shard visibility issues
  (existential restrictions, nominals, ≥1 cardinality) are resolved with
  dedicated cross-shard joins; all other CE types are combined by simple union.
  This strategy is sound under OWA and is the recommended reasoner for
  production use.

Cross-shard inference problem
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The ABox is partitioned round-robin by *subject* individual across N shards;
the TBox is replicated in every shard.  A property assertion ``(s, r, o)``
lives in the shard of the subject ``s``, which may differ from the shard that
holds the class assertions of the object ``o``.  Consequently, per-shard
Pellet evaluation of CEs like ``∃ r.C`` can be **incomplete**: ``s``'s shard
does not know ``o : C``, and ``o``'s shard does not contain ``s``.
``CrossShardReasoner`` resolves this by passing the globally resolved filler
set to every shard and scanning only local property assertions.

Architecture
------------
  ShardReasoner (Ray actor, one per shard)
      Wraps a SyncReasoner (Pellet / HermiT) for a single .owl shard.
      Exposes atomic query methods that return plain IRI strings so that
      results can be serialised across the Ray object store without issues.
      Provides two query entry-points: ``query_instances`` (full CE, used by
      DistributedReasoner) and ``query_instances_with_intermediate`` (full CE
      + all sub-CEs, used by CrossShardReasoner).  Also exposes relational
      helpers (``get_object_property_subjects``, ``get_object_property_map``)
      for cross-shard joins.

  DistributedReasoner (coordinator, CWA, runs on the driver)
      Accepts any OWLClassExpression and recursively decomposes it into
      atomic sub-queries via singledispatch.  Operates under CWA: distinct
      IRIs are treated as distinct individuals.  Supported constructors:
        OWLClass, OWLObjectIntersectionOf, OWLObjectUnionOf,
        OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom,
        OWLObjectComplementOf, OWLObjectHasValue, OWLObjectOneOf,
        OWLObjectMinCardinality, OWLObjectMaxCardinality,
        OWLObjectExactCardinality

  CrossShardReasoner (coordinator, OWA, runs on the driver)
      Extends DistributedReasoner.  Gathers per-shard intermediate results
      and combines them bottom-up by CE type.  Always operates under OWA —
      Pellet is the reasoner on each shard and its OWA semantics are
      preserved.  See the CE-type routing table in the class docstring for
      details on how each constructor is handled.

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

OWA vs CWA considerations
-------------------------
Under the **Open-World Assumption** (OWA), a reasoner cannot conclude that two
individuals are distinct unless an ``owl:AllDifferent`` axiom (or equivalent)
explicitly states so.  This has practical consequences for cardinality
restrictions:

* ``≥n r.C`` with ``n ≥ 2`` — Pellet can only return a subject if it can
  prove that at least ``n`` *distinct* fillers exist.  Without AllDifferent
  axioms the result is typically empty, even when the ABox contains many
  role fillers with different IRIs.
* ``≥1 r.C`` — only one qualifying filler is needed; no distinctness proof
  is required.  This is semantically equivalent to ``∃ r.C``.
* ``≤n r.C`` / ``=n r.C`` — similarly sensitive to AllDifferent axioms.

``CrossShardReasoner`` respects these OWA semantics.  It delegates
cardinality evaluation (≥n with n≥2, ≤n, =n) to per-shard Pellet and unions
the results, which preserves the same answers as a single Pellet instance on
the complete ontology.  Only ``≥1 r.C`` receives special cross-shard join
treatment (identical to ``∃ r.C``).

``DistributedReasoner`` operates under CWA: it counts distinct IRI role
fillers across shards, which can over-count when the ontology lacks
AllDifferent axioms.  Use ``CrossShardReasoner`` when OWA-correct answers are
required.


Regression testing: Any code change should be tested with the following command to ensure that distributed reasoning results remain consistent.  The test runs both reasoners on a complex CE and compares their answers for consistency (OWA vs CWA differences are expected for cardinality).

python ddp_reasoning_eval.py --auto_ray --num_shards 20 --path_kg KGs/Mutagenesis/mutagenesis.owl --cross_shard --open_world --no_negations

======================================================================
EVALUATION SUMMARY
======================================================================

Expression Type Counts:
Type
OWLClass                     86
OWLObjectAllValuesFrom      430
OWLObjectIntersectionOf    4026
OWLObjectMaxCardinality    1290
OWLObjectMinCardinality    1290
OWLObjectSomeValuesFrom    1030
OWLObjectUnionOf           4026
Name: Type, dtype: int64

Mean Metrics by Type:
                         Jaccard Similarity  F1   Runtime Benefits  Runtime Ground Truth  Runtime Distributed
Type                                                                                                         
OWLClass                 1.0                 1.0  0.001125          0.012019              0.010893           
OWLObjectAllValuesFrom   1.0                 1.0 -0.012781          0.020863              0.033644           
OWLObjectIntersectionOf  1.0                 1.0 -0.014230          0.006741              0.020971           
OWLObjectMaxCardinality  1.0                 1.0 -0.012307          0.019270              0.031577           
OWLObjectMinCardinality  1.0                 1.0  2.954170          3.090149              0.135979           
OWLObjectSomeValuesFrom  1.0                 1.0  0.267106          0.502817              0.235711           
OWLObjectUnionOf         1.0                 1.0 -0.009525          0.032987              0.042512           

----------------------------------------------------------------------
Overall Statistics:
  Total expressions evaluated: 12178
  Mean Jaccard Similarity: 1.0000
  Mean F1 Score: 1.0000
  Perfect matches (Jaccard=1.0): 12178/12178
  Mean Runtime Benefit (GT - Dist): 325.92ms
  Mean Speedup: 1.40x

✓ Correctness check PASSED: Mean Jaccard (1.0000) >= threshold (0.0)

"""

import argparse
import os
os.environ.setdefault("RAY_DEDUP_LOGS", "0")
os.environ.setdefault("RAY_ACCEL_ENV_VAR_OVERRIDE_ON_ZERO", "0")
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

    Each shard holds the complete TBox and a disjoint subset of the ABox
    (partitioned round-robin by subject individual).  The actor is pinned to a
    specific Ray resource (``shard_<i>``) so that it can be co-located with the
    shard data on multi-machine clusters.

    All public methods return **plain IRI strings** (``Set[str]`` /
    ``Dict[str, Set[str]]``) rather than ``OWLNamedIndividual`` objects.  This
    avoids serialisation issues across the Ray object store and eliminates
    equality problems between objects created in different JVM sessions.

    Key entry-points
    ~~~~~~~~~~~~~~~~
    * ``query_instances``                  — evaluate a single CE on this shard.
    * ``query_instances_with_intermediate`` — evaluate a CE *and every sub-CE*;
      used by ``CrossShardReasoner`` for bottom-up combining.
    * ``get_object_property_subjects``     — lightweight ABox scan returning all
      subjects ``s`` with ``(s, r, o)`` for ``o`` in a given set.
    * ``get_object_property_map``          — full ``{subject: {objects}}`` map for
      a property; used by ``DistributedReasoner`` for CWA cardinality counting.
    """
    
    def __init__(self, shard_id: str, ontology_path: str, reasoner: str = "Pellet", verbose: bool = True):
        self.shard_id = shard_id
        self.ontology_path = ontology_path
        self.verbose = verbose
        self.sync_reasoner = SyncReasoner(ontology=ontology_path, reasoner=reasoner)
        if self.verbose:
            print(f"--- Shard {shard_id} initialized with {reasoner} reasoner ---")

    def set_verbose(self, verbose: bool) -> None:
        """Update the verbose flag on this shard actor."""
        self.verbose = verbose
    
    def get_shard_id(self) -> str:
        return self.shard_id
    
    # ========== Atomic Query Methods (all return IRI strings) ==========
    
    def query_instances(self, ce: OWLClassExpression, direct: bool = False) -> Set[str]:
        """Pass a full CE directly to this shard's reasoner (no decomposition).
        Used in open-world mode where each shard evaluates independently."""
        return {ind.str for ind in self.sync_reasoner.instances(ce, direct=direct)}
    
    def query_instances_with_intermediate(
        self, 
        ce: OWLClassExpression, 
        direct: bool = False
    ) -> Dict[str, Set[str]]:
        """
        Evaluate CE and return intermediate results for all sub-CEs.
        
        This enables cross-shard inference for nested expressions.
        Returns a dict mapping CE string representations to their instance sets.
        
        For example, for X = exists r1.(exists r2.C):
        {
            "C": {instances of C in this shard},
            "exists r2.C": {instances of exists r2.C in this shard},
            "exists r1.(exists r2.C)": {instances of X in this shard}
        }
        
        Args:
            ce: The class expression to evaluate
            direct: Whether to get only direct instances
            
        Returns:
            Dict mapping CE representations to instance IRI sets
        """
        results = {}
        try:
            self._collect_intermediate_results(ce, direct, results)
        except Exception as e:
            print(f"Error collecting intermediate results on {self.shard_id}: {e}")
            # Fall back to empty results
            results[str(ce)] = set()
        return results
    
    def _collect_intermediate_results(
        self,
        ce: OWLClassExpression,
        direct: bool,
        results: Dict[str, Set[str]]
    ) -> None:
        """Recursively collect intermediate results for CE and all sub-CEs."""
        ce_str = str(ce)
        
        # If already computed, skip
        if ce_str in results:
            return
        
        # Process sub-expressions first (depth-first)
        if isinstance(ce, OWLObjectSomeValuesFrom):
            self._collect_intermediate_results(ce.get_filler(), direct, results)
        elif isinstance(ce, OWLObjectAllValuesFrom):
            self._collect_intermediate_results(ce.get_filler(), direct, results)
        elif isinstance(ce, (OWLObjectIntersectionOf, OWLObjectUnionOf)):
            for operand in ce.operands():
                self._collect_intermediate_results(operand, direct, results)
        elif isinstance(ce, OWLObjectComplementOf):
            self._collect_intermediate_results(ce.get_operand(), direct, results)
        elif isinstance(ce, (OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality)):
            self._collect_intermediate_results(ce.get_filler(), direct, results)
        
        # Compute instances for this CE on this shard
        if self.verbose:
            print(f"    [{self.shard_id}] Evaluating: {ce_str[:60]}...")
        results[ce_str] = self.query_instances(ce, direct)
        if self.verbose:
            print(f"    [{self.shard_id}] Found {len(results[ce_str])} instances")
    
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
        Return all subjects ``s`` such that ``(s, r, o)`` for some ``o`` in
        ``object_iris``, scanning only this shard's local ABox.

        This is the key primitive for cross-shard existential joins.  The caller
        (``CrossShardReasoner._combine_existential_across_shards``) passes the
        globally resolved filler set; this method checks each local individual's
        property values against that set.  Because property assertions are stored
        in the *subject*'s shard, this scan is guaranteed to find all local
        subjects that qualify.

        The scan iterates over ``individuals_in_signature()`` and calls
        ``object_property_values()`` on the underlying Pellet reasoner, so
        inferred property values (via property-chain axioms etc.) are included.

        Args:
            property_iri: The IRI string of the object property.
            is_inverse:   If True, the property is inverted (``r⁻``).
            object_iris:  The set of object IRI strings to match against.

        Returns:
            Set of subject IRI strings that have at least one matching object.
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
        Return a mapping ``{subject_iri: {object_iri, …}}`` for a given property,
        scanning only this shard's local ABox.

        Used by ``DistributedReasoner._gather_property_maps`` to build a global
        property map for CWA cardinality counting.  (CrossShardReasoner does not
        use this method; it delegates cardinality to per-shard Pellet.)

        Args:
            property_iri: The IRI string of the object property.
            is_inverse:   If True, the property is inverted (``r⁻``).

        Returns:
            Dict mapping each subject IRI to its set of object IRIs.
            Subjects with no property values are omitted.
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
    A coordinator that performs distributed OWL reasoning by recursively
    decomposing class expressions into atomic queries, dispatching them to
    shards, and aggregating results.

    Operates under the **Closed-World Assumption** (CWA): distinct IRIs are
    treated as distinct individuals.  This is correct for ontologies that either
    include ``owl:AllDifferent`` axioms or where the Unique Name Assumption
    applies.  For ontologies without such axioms (common in practice),
    cardinality results may **over-count** — e.g. ``≥3 r.C`` may return
    subjects that merely have three differently-named (but not provably
    distinct) fillers.

    For OWA-correct reasoning, use ``CrossShardReasoner`` instead.

    Strategy
    --------
    1. Break down complex CEs (e.g., ``Male ⊓ ∃ hasChild.Parent``) by
       recursively dispatching on CE type via ``singledispatchmethod``.
    2. Gather atomic results from **all** shards (e.g., all Males, all Parents,
       all hasChild relations).
    3. Compute the final answer by joining / intersecting / differencing the
       gathered data.

    Note
    ----
    When ``open_world=True``, the recursive decomposition is bypassed: the
    full CE is sent to each shard and results are unioned.  This preserves
    per-shard Pellet’s OWA answers but suffers from cross-shard visibility
    issues for existentials and nominals.  ``CrossShardReasoner`` is the
    recommended approach for correct OWA distributed reasoning.
    """
    
    def __init__(self, shards: List[ray.actor.ActorHandle], open_world: bool = False, verbose: bool = True):
        """
        Args:
            shards: List of ShardReasoner actor handles
            open_world: If True, pass full CEs directly to each shard and union
                        results (no recursive decomposition). If False, use
                        closed-world recursive decomposition (default).
            verbose: If True, print progress messages (default: True).
        """
        self.shards = shards
        self.open_world = open_world
        self.verbose = verbose
        if self.verbose:
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
        """
        Gather per-shard property maps and merge into a global
        ``{subject_iri: {object_iri, …}}`` dict.

        Used by ``_find_cardinality_iris`` for CWA cardinality counting.
        Each shard returns its local ``{s: {o}}`` map; the coordinator merges
        them by unioning the object sets for each subject.  Because a subject's
        property assertions all live in one shard (by the partitioning scheme),
        each subject key appears in exactly one shard's map and no real merging
        is needed — but the code handles the general case defensively.
        """
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
        Handle cardinality restrictions under CWA by gathering the global
        property map, counting IRI-distinct filler matches per subject, and
        applying the min/max constraint.

        .. warning::

           This method counts **distinct IRIs** as distinct individuals
           (Closed-World Assumption).  Under OWA, Pellet requires explicit
           ``owl:AllDifferent`` axioms to prove distinctness.  Without them,
           this method can **over-count** for ``≥n`` (n ≥ 2) and
           **under-count** for ``≤n`` / ``=n``.  Use ``CrossShardReasoner``
           for OWA-correct cardinality evaluation.

        Args:
            ce:     An ``OWLObjectMinCardinality``, ``OWLObjectMaxCardinality``,
                    or ``OWLObjectExactCardinality`` expression.
            direct: Forwarded to filler resolution.

        Returns:
            Set of subject IRI strings meeting the cardinality constraint.
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


class CrossShardReasoner(DistributedReasoner):
    """
    A distributed reasoner that enables correct cross-shard inference for nested
    OWL class expressions by combining per-shard intermediate results bottom-up.

    Background
    ----------
    The ABox is partitioned round-robin by subject individual across N shards;
    the TBox is replicated in every shard.  This means:

    * A named individual ``a`` has its class-assertion axioms only in its assigned
      shard ``shard_k``.
    * An object-property assertion ``(s, r, o)`` lives in the shard of the *subject*
      ``s``, which may differ from the shard of the *object* ``o``.

    As a consequence, per-shard Pellet evaluation of complex CEs can be incorrect:
    a shard may literally not see the axioms it needs to answer part of the query.

    Strategy
    --------
    1. Every shard evaluates the full CE **and all sub-CEs** via
       ``query_instances_with_intermediate``, returning a ``{ce_str -> IRI set}``
       dict of intermediate results.
    2. The coordinator collects those dicts and combines them **bottom-up**
       (leaves before parents) using the logic described in the table below.
    3. For CE types that require cross-shard joins, the coordinator issues
       additional Ray calls (``get_object_property_subjects``,
       ``get_object_property_map``) to gather the relational data it needs.

    CE-type routing table
    ---------------------
    +---------------------------------------+-----------------------------------+--------------------------------+
    | CE type                               | Coordinator strategy              | Reason                         |
    +=======================================+===================================+================================+
    | OWLClass, OWLObjectUnionOf,           | Union per-shard results           | ABox is subject-keyed: each    |
    | OWLObjectIntersectionOf, etc.         |                                   | individual lives in exactly    |
    |                                       |                                   | one shard, so the union is     |
    |                                       |                                   | the complete set.              |
    +---------------------------------------+-----------------------------------+--------------------------------+
    | OWLObjectOneOf  ({a, b, c})           | Extract IRIs directly from the CE | Nominal members are defined    |
    |                                       | — never query shards              | by the expression, not by      |
    |                                       |                                   | entailment. Per-shard Pellet   |
    |                                       |                                   | returns 0 for individuals whose|
    |                                       |                                   | class assertions are in a      |
    |                                       |                                   | different shard, making the    |
    |                                       |                                   | filler set empty and causing   |
    |                                       |                                   | OWLObjectSomeValuesFrom to     |
    |                                       |                                   | short-circuit to {}.           |
    +---------------------------------------+-----------------------------------+--------------------------------+
    | OWLObjectSomeValuesFrom  (∃ r.C)      | 1. Use combined[filler] (already  | The subject of (s, r, o) lives |
    |                                       |    computed) as the object set.   | in a different shard from o.   |
    |                                       | 2. Call get_object_property_      | Per-shard Pellet only sees one |
    |                                       |    subjects on ALL shards with    | side of the triple.            |
    |                                       |    that object set.               |                                |
    |                                       | 3. Union results.                 |                                |
    +---------------------------------------+-----------------------------------+--------------------------------+
    | OWLObjectMinCardinality  (≥1 r.C)     | Cross-shard existential join      | ≥1 r.C ≡ ∃ r.C: one qualifying|
    |                                       | (same as ∃ r.C above)             | filler suffices, no distinct-  |
    |                                       |                                   | ness proof needed. Same cross- |
    |                                       |                                   | shard filler visibility issue  |
    |                                       |                                   | as OWLObjectSomeValuesFrom.    |
    +---------------------------------------+-----------------------------------+--------------------------------+
    | OWLObjectMinCardinality  (≥n r.C,n≥2) | Union per-shard Pellet results    | OWA requires owl:AllDifferent  |
    | OWLObjectMaxCardinality  (≤n r.C)     |                                   | to prove distinct role fillers.|
    | OWLObjectExactCardinality (=n r.C)    |                                   | Without it Pellet returns 0    |
    |                                       |                                   | for ≥n (n≥2). Subject-keyed    |
    |                                       |                                   | partitioning places every      |
    |                                       |                                   | subject's property assertions  |
    |                                       |                                   | in one shard, so per-shard     |
    |                                       |                                   | Pellet preserves OWA and the   |
    |                                       |                                   | union is correct.              |
    +---------------------------------------+-----------------------------------+--------------------------------+

    Example
    -------
    Shard-1 contains:  ``(compound42, hasBond, bond17)``
    Shard-7 contains:  ``bond17 : Bond-1``  (class assertion for bond17)

    Query: ``∃ hasBond.{bond17}``

    * Per-shard Pellet on Shard-1 returns {} — bond17 is not asserted to be
      anything in Shard-1, so Pellet cannot confirm the query.
    * Per-shard Pellet on Shard-7 returns {} — compound42 is not in Shard-7.
    * CrossShardReasoner:
      1. OWLObjectOneOf({bond17}) → {bond17.iri}  (extracted from CE, no shard query)
      2. OWLObjectSomeValuesFrom → calls get_object_property_subjects on all shards
         with object_iris={bond17.iri} → Shard-1 returns {compound42.iri}
      3. Result: {compound42}  ✓

    Soundness under OWA
    -------------------
    CrossShardReasoner always operates under the Open-World Assumption.  No
    Closed-World counting or Unique-Name reasoning is performed.  Cardinality
    restrictions (≥n with n≥2, ≤n, =n) are evaluated by per-shard Pellet and
    unioned, which exactly reproduces the answers a single Pellet instance
    would return on the complete (unsharded) ontology.  Only ≥1 r.C receives
    special cross-shard treatment (since ≥1 r.C ≡ ∃ r.C and needs the same
    filler-visibility join).

    If the ontology contains ``owl:AllDifferent`` axioms they are replicated
    in every shard via the TBox, so per-shard Pellet will still use them.
    """
    
    def __init__(self, shards: List[ray.actor.ActorHandle], open_world: bool = False, verbose: bool = True):
        """
        Initialise a CrossShardReasoner.

        The reasoner always uses OWA-correct bottom-up combining logic in its
        ``instances`` method, regardless of the ``open_world`` flag (which is
        only forwarded to the parent ``DistributedReasoner`` for API
        compatibility).

        Args:
            shards:     List of ShardReasoner Ray actor handles, one per ontology
                        partition.  Each shard must hold the complete TBox and a
                        disjoint ABox subset.
            open_world: Forwarded to ``DistributedReasoner.__init__`` but has
                        **no effect** on ``CrossShardReasoner.instances``, which
                        always uses the cross-shard bottom-up path.
            verbose:    If True, print progress messages for each CE component
                        being processed (useful for debugging).
        """
        super().__init__(shards, open_world=open_world, verbose=verbose)
        self.verbose = verbose
        # Propagate verbose flag to all shard actors
        ray.get([s.set_verbose.remote(verbose) for s in shards])
        if self.verbose:
            print(f"CrossShardReasoner initialized with {len(shards)} shards (cross-shard intermediate results mode)")
    
    def instances(self, ce: OWLClassExpression, direct: bool = False) -> Set[OWLNamedIndividual]:
        """
        Return all named individuals that are instances of ``ce``.

        Delegates to ``_cross_shard_instances`` which gathers per-shard
        intermediate results and combines them bottom-up according to the
        CE-type routing table described in the class docstring.

        Args:
            ce:     The OWL class expression to evaluate.
            direct: If True, return only direct instances (not inherited).
                    Passed through to each shard's reasoner.

        Returns:
            Set of OWLNamedIndividual objects that satisfy ``ce``.
        """
        iris = self._cross_shard_instances(ce, direct)
        return {OWLNamedIndividual(iri) for iri in iris}
    
    def _cross_shard_instances(self, ce: OWLClassExpression, direct: bool = False) -> Set[str]:
        """
        Core cross-shard inference loop.  Returns a set of individual IRI strings.

        Algorithm
        ---------
        1. **Scatter** — broadcast ``query_instances_with_intermediate(ce)`` to all
           shards in parallel.  Each shard returns a dict
           ``{str(sub_ce): Set[IRI]}`` for every sub-expression it evaluated.
        2. **Collect CE structure** — ``_collect_ce_structure`` walks the CE tree
           on the driver and builds a ``{str(ce): ce_object}`` map so we have the
           actual Python CE objects (needed to dispatch on type).
        3. **Bottom-up combine** — sort CE objects by depth (leaves first), then
           for each CE apply the routing strategy from the class docstring table:

           * ``OWLObjectOneOf``          → extract IRIs directly from the CE.
           * ``OWLObjectSomeValuesFrom`` → cross-shard join via
             ``_combine_existential_across_shards``.
           * ``OWLObjectMinCardinality`` with n=1 → cross-shard existential
             join (≥1 r.C ≡ ∃ r.C).
           * Other cardinality types     → union per-shard Pellet results
             (preserves OWA semantics).
           * Everything else             → union per-shard Pellet results.

        4. **Return** the combined result for the top-level CE.

        Args:
            ce:     The OWL class expression to evaluate.
            direct: Forwarded to each shard's reasoner.

        Returns:
            Set of individual IRI strings satisfying ``ce``.
        """
        if self.verbose:
            print(f"  [cross-shard] Gathering intermediate results from {len(self.shards)} shards...")
        
        # Gather intermediate results from all shards
        futures = [shard.query_instances_with_intermediate.remote(ce, direct) for shard in self.shards]
        shard_results = ray.get(futures)  # List of dicts: ce_str -> instance set
        
        if self.verbose:
            print(f"  [cross-shard] Received results from all shards")
        
        # Build a map of CE string -> combined instances across shards
        combined = {}
        
        # Extract the CE structure and process bottom-up
        ce_by_str = {}
        self._collect_ce_structure(ce, ce_by_str)
        
        if self.verbose:
            print(f"  [cross-shard] Processing {len(ce_by_str)} CE components...")
        
        # Process CEs by depth (leaves first)
        ce_list = sorted(ce_by_str.items(), key=lambda x: self._ce_depth(x[1]))
        
        for idx, (ce_str, ce_obj) in enumerate(ce_list):
            if self.verbose:
                print(f"  [cross-shard] Processing {idx+1}/{len(ce_list)}: {ce_str[:80]}...")
            
            # Check if this is an existential restriction that needs cross-shard joining
            if isinstance(ce_obj, OWLObjectSomeValuesFrom):
                # For exists r.C, we need to find subjects whose r-values satisfy C
                # C's instances have already been combined across shards
                combined[ce_str] = self._combine_existential_across_shards(
                    ce_obj, combined, shard_results
                )
            elif isinstance(ce_obj, OWLObjectOneOf):
                # Members of a nominal are defined by the expression itself — not by what
                # individual shards happen to know.  Relying on per-shard query results
                # fails because the named individuals may lack class assertions in every
                # shard they don't own, so each shard returns 0 and the filler set ends
                # up empty.  Extract the IRIs directly from the CE instead.
                combined[ce_str] = {ind.str for ind in ce_obj.individuals()}
            elif isinstance(ce_obj, OWLObjectMinCardinality) and ce_obj.get_cardinality() == 1:
                # ≥1 r.C ≡ ∃ r.C — a single qualifying filler suffices, so no
                # distinctness proof is needed.  Use the same cross-shard
                # existential join that handles OWLObjectSomeValuesFrom.
                combined[ce_str] = self._combine_existential_across_shards(
                    ce_obj, combined, shard_results
                )
            elif isinstance(ce_obj, (OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality)):
                # Remaining cardinality restrictions (≥n with n≥2, ≤n, =n r.C):
                # union per-shard Pellet results to preserve OWA semantics.
                # Pellet requires owl:AllDifferent to prove distinct role fillers;
                # without it ≥n (n≥2) yields {} on the full ontology anyway.
                # Subject-keyed ABox partitioning places all of a subject's
                # property assertions in exactly one shard, so per-shard Pellet
                # counts are locally exact and the union is correct.
                combined[ce_str] = set()
                for shard_res in shard_results:
                    if ce_str in shard_res:
                        combined[ce_str] |= shard_res[ce_str]
            else:
                # For other CEs (atomic classes, unions, intersections): union across
                # shards is correct because the ABox is partitioned — each individual
                # lives in exactly one shard.
                combined[ce_str] = set()
                for shard_res in shard_results:
                    if ce_str in shard_res:
                        combined[ce_str] |= shard_res[ce_str]
        
        if self.verbose:
            print(f"  [cross-shard] Completed processing")
        
        # Return combined results for the top-level CE
        return combined.get(str(ce), set())
    
    def _collect_ce_structure(self, ce: OWLClassExpression, ce_map: Dict[str, OWLClassExpression]) -> None:
        """
        Recursively walk ``ce`` and populate ``ce_map`` with every sub-expression.

        ``ce_map`` maps ``str(sub_ce)`` → ``sub_ce`` object.  The string key is
        the same key used by ``ShardReasoner.query_instances_with_intermediate``,
        so the coordinator can look up shard results by the same key.

        Args:
            ce:     Root CE to walk.
            ce_map: Accumulator dict (modified in-place).
        """
        ce_str = str(ce)
        if ce_str in ce_map:
            return
        
        ce_map[ce_str] = ce
        
        if isinstance(ce, OWLObjectSomeValuesFrom):
            self._collect_ce_structure(ce.get_filler(), ce_map)
        elif isinstance(ce, OWLObjectAllValuesFrom):
            self._collect_ce_structure(ce.get_filler(), ce_map)
        elif isinstance(ce, (OWLObjectIntersectionOf, OWLObjectUnionOf)):
            for operand in ce.operands():
                self._collect_ce_structure(operand, ce_map)
        elif isinstance(ce, OWLObjectComplementOf):
            self._collect_ce_structure(ce.get_operand(), ce_map)
        elif isinstance(ce, (OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality)):
            self._collect_ce_structure(ce.get_filler(), ce_map)
    
    def _ce_depth(self, ce: OWLClassExpression) -> int:
        """
        Return the nesting depth of ``ce``.

        Atomic CEs (OWLClass, OWLObjectOneOf) have depth 0.  Compound CEs have
        depth 1 + max(children depths).  Used to sort the CE list so that leaf
        nodes are processed before the expressions that depend on them.
        """
        if isinstance(ce, OWLClass):
            return 0
        elif isinstance(ce, OWLObjectOneOf):
            return 0
        elif isinstance(ce, (OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom)):
            return 1 + self._ce_depth(ce.get_filler())
        elif isinstance(ce, (OWLObjectIntersectionOf, OWLObjectUnionOf)):
            return 1 + max((self._ce_depth(op) for op in ce.operands()), default=0)
        elif isinstance(ce, OWLObjectComplementOf):
            return 1 + self._ce_depth(ce.get_operand())
        elif isinstance(ce, (OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality)):
            return 1 + self._ce_depth(ce.get_filler())
        else:
            return 0
    
    def _combine_existential_across_shards(
        self,
        ce,  # OWLObjectSomeValuesFrom or OWLObjectMinCardinality (n=1)
        combined: Dict[str, Set[str]],
        shard_results: List[Dict[str, Set[str]]]
    ) -> Set[str]:
        """
        Evaluate an existential-style restriction using a cross-shard join.

        Handles both ``OWLObjectSomeValuesFrom`` (∃ r.C) and
        ``OWLObjectMinCardinality`` with n=1 (≥1 r.C ≡ ∃ r.C).  Both require
        only ``get_property()`` and ``get_filler()`` from the CE.

        Algorithm
        ---------
        1. Retrieve ``filler_iris = combined[str(C)]`` — the cross-shard instance
           set for the filler C, already computed bottom-up by the caller.  This
           set may contain individuals from *any* shard.
        2. Call ``get_object_property_subjects(r, filler_iris)`` on every shard in
           parallel.  Each shard scans its local property assertions and returns
           any subject ``s`` such that ``(s, r, o)`` exists for some
           ``o ∈ filler_iris``.
        3. Union the per-shard subject sets.

        Why this is necessary
        ---------------------
        The ABox is partitioned by subject, so the triple ``(s, r, o)`` lives in
        ``s``-shard.  When the filler instances come from a *different* shard than
        the subjects, per-shard Pellet evaluation of the full CE misses them:
        ``s``-shard does not know ``o`` exists (no class assertion there), and
        ``o``-shard does not contain ``s``.

        By passing the already-resolved ``filler_iris`` to every shard,
        ``get_object_property_subjects`` only needs to look at local property
        assertions — a lightweight ABox scan without calling the reasoner.

        Supports nested queries, e.g.:
          Shard-1: (o1, r1, o2)    Shard-2: (o2, r2, o3)
          Query:   ∃ r1.(∃ r2.{o3})
          Step 1:  combined[∃ r2.{o3}] = {o2}   (computed in prior iteration)
          Step 2:  get_object_property_subjects(r1, {o2}) on Shard-1 → {o1}
          Result:  {o1}  ✓

        Args:
            ce:            An ``OWLObjectSomeValuesFrom`` or
                           ``OWLObjectMinCardinality`` (n=1) expression.
            combined:      Bottom-up accumulated results; must already contain an
                           entry for ``str(ce.get_filler())``.
            shard_results: Raw per-shard intermediate dicts (not used directly
                           here; the filler result is taken from ``combined``).

        Returns:
            Set of subject IRI strings satisfying the restriction.
        """
        property_expr = ce.get_property()
        filler = ce.get_filler()
        filler_str = str(filler)
        
        # Get combined filler instances (already computed from earlier CEs)
        filler_iris = combined.get(filler_str, set())
        
        if not filler_iris:
            return set()
        
        # Gather property relations from all shards
        is_inverse = isinstance(property_expr, OWLObjectInverseOf)
        prop_iri = property_expr.get_named_property().str if is_inverse else property_expr.str
        
        # Get subjects from all shards that have property values in the filler set
        futures = [
            shard.get_object_property_subjects.remote(prop_iri, is_inverse, filler_iris)
            for shard in self.shards
        ]
        results = ray.get(futures)
        return set().union(*results) if results else set()



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
        all_shards_exist = all(
            (Path(BASE) / f"{ONTOLOGY_STEM}_shard_{i}.owl").exists()
            for i in range(NUM_SHARDS)
        )
        # Also check no extra shards from a previous run with more shards
        extra_shard = (Path(BASE) / f"{ONTOLOGY_STEM}_shard_{NUM_SHARDS}.owl").exists()
        
        if not all_shards_exist or extra_shard:
            print(f"  [auto-shard] Shard files not found (or wrong count) — generating {NUM_SHARDS} shards from {ORIGINAL_ONTOLOGY}...")
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
    
    dist_reasoner = DistributedReasoner(shards, open_world=True)
    
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
