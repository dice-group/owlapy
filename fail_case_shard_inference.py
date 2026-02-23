"""
Test: Cross-Shard Inference for Nested Existential Queries
==========================================================

Scenario
--------
  Two shards G_1 and G_2 share the TBox but have disjoint ABox fragments:

    G_1 ABox:  (o1  r1  o2)      -- only this one triple
    G_2 ABox:  (o2  r2  o3)      -- only this one triple

  Query:  exists r1.(exists r2.{o3})

  Centralised answer: {o1}
    because  o1 --r1--> o2 --r2--> o3

  Question: Can the BaseShardReasoner return o1?

Open-world mode  (open_world=True, cross_shard=False)
------------------------------------------------------
  Each shard evaluates the FULL CE independently, then results are unioned.

    G_1 evaluates exists r1.(exists r2.{o3}):
      o1 has r1->o2, but o2 has NO r2 values in G_1  ->  {}

    G_2 evaluates exists r1.(exists r2.{o3}):
      nobody has r1 values in G_2  ->  {}

    Union: {}  ->  o1 is NOT returned.

  Conclusion: open-world mode CANNOT return o1 for this cross-shard scenario.

Cross-shard mode  (open_world=True, cross_shard=True)
------------------------------------------------------
  Each shard evaluates the CE and returns intermediate results for all sub-CEs.
  The coordinator combines these intermediate results bottom-up.

  1. Each shard evaluates:
       - {o3}  (instances of the innermost filler)
       - exists r2.{o3}  (instances of inner existential)
       - exists r1.(exists r2.{o3})  (instances of full query)

  2. Combine across shards for {o3}:
       G_1: {o3}  G_2: {o3}  ->  Union: {o3}

  3. Combine across shards for exists r2.{o3}:
       - Combined filler instances: {o3}
       - Get r2 property relations from all shards
       - G_1: no (x r2 o3) triples  ->  {}
       - G_2: (o2 r2 o3), o3 in filler  ->  {o2}
       - Union: {o2}  <- o2 found via cross-shard join

  4. Combine across shards for exists r1.(exists r2.{o3}):
       - Combined filler instances (from step 3): {o2}
       - Get r1 property relations from all shards
       - G_1: (o1 r1 o2), o2 in filler  ->  {o1}
       - G_2: no (x r1 o2) triples  ->  {}
       - Union: {o1}  <- o1 found via cross-shard join

  Conclusion: cross-shard mode CAN return o1.

Usage
-----
  conda activate temp_owlapy
  python fail_case_shard_inference.py
"""

import os
import ray
import tempfile
import shutil

from owlapy.owl_ontology import SyncOntology
from owlapy.owl_axiom import (
    OWLDeclarationAxiom,
    OWLObjectPropertyAssertionAxiom,
)
from owlapy.class_expression import OWLClass, OWLObjectSomeValuesFrom, OWLObjectOneOf
from owlapy.owl_property import OWLObjectProperty
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_reasoner import SyncReasoner
from owlapy.iri import IRI

from ddp_reasoning import ShardReasoner, BaseShardReasoner, ShardEnsembleReasoner


NS = "http://example.org/test#"


def build_ontology(path, abox_triples):
    """
    Create a minimal .owl file with declarations for all entities
    and only the given ABox triples.

    Args:
        path: Where to save the .owl file.
        abox_triples: List of (subject_name, property_name, object_name) tuples.
    """
    onto = SyncOntology(IRI.create(NS[:-1]), load=False)

    # Declarations for every entity that appears
    names = set()
    prop_names = set()
    for s, p, o in abox_triples:
        names.update([s, o])
        prop_names.add(p)

    for n in names:
        onto.add_axiom(OWLDeclarationAxiom(OWLNamedIndividual(IRI(NS, n))))
    for p in prop_names:
        onto.add_axiom(OWLDeclarationAxiom(OWLObjectProperty(IRI(NS, p))))

    # ABox assertions
    for s, p, o in abox_triples:
        onto.add_axiom(OWLObjectPropertyAssertionAxiom(
            subject=OWLNamedIndividual(IRI(NS, s)),
            property_=OWLObjectProperty(IRI(NS, p)),
            object_=OWLNamedIndividual(IRI(NS, o)),
        ))

    onto.save(path)
    print(f"  Saved {path}  ({len(abox_triples)} ABox triple(s))")


def main():
    tmp_dir = tempfile.mkdtemp(prefix="cross_shard_test_")
    print(f"Working directory: {tmp_dir}\n")

    try:
        # -- Build ontologies -----------------------------------------------
        # Complete ontology (ground truth)
        full_path = os.path.join(tmp_dir, "full.owl")
        build_ontology(full_path, [("o1", "r1", "o2"), ("o2", "r2", "o3")])

        # Shard G_1: only (o1 r1 o2)
        shard1_path = os.path.join(tmp_dir, "shard_0.owl")
        build_ontology(shard1_path, [("o1", "r1", "o2")])

        # Shard G_2: only (o2 r2 o3)
        shard2_path = os.path.join(tmp_dir, "shard_1.owl")
        build_ontology(shard2_path, [("o2", "r2", "o3")])

        # -- Ground truth (centralised) ------------------------------------
        print("\n-- Ground Truth (full ontology) --")
        gt_reasoner = SyncReasoner(ontology=full_path, reasoner="Pellet")

        r1 = OWLObjectProperty(IRI(NS, "r1"))
        r2 = OWLObjectProperty(IRI(NS, "r2"))
        o3 = OWLNamedIndividual(IRI(NS, "o3"))

        query = OWLObjectSomeValuesFrom(
            property=r1,
            filler=OWLObjectSomeValuesFrom(
                property=r2,
                filler=OWLObjectOneOf([o3])
            )
        )
        gt_results = {ind.str for ind in gt_reasoner.instances(query)}
        print(f"  Query:   exists r1.(exists r2.{{o3}})")
        print(f"  Result:  {gt_results}")

        # -- Distributed reasoning (OPEN WORLD) ----------------------------
        print("\n-- Distributed Reasoning: OPEN WORLD (2 shards) --")

        # Initialise Ray locally with 2 shard resources
        if not ray.is_initialized():
            ray.init(num_cpus=2, resources={"shard_0": 1, "shard_1": 1})

        shard_actors_ow = [
            ShardReasoner.options(resources={"shard_0": 1}).remote(
                "Shard-0", shard1_path, "Pellet"),
            ShardReasoner.options(resources={"shard_1": 1}).remote(
                "Shard-1", shard2_path, "Pellet"),
        ]

        open_world_reasoner = BaseShardReasoner(shard_actors_ow, open_world=True)
        ow_results = {ind.str for ind in open_world_reasoner.instances(query)}
        print(f"  Query:   exists r1.(exists r2.{{o3}})")
        print(f"  Result:  {ow_results}")

        # -- Distributed reasoning (CROSS-SHARD MODE) ----------------------
        print("\n-- Distributed Reasoning: CROSS-SHARD MODE (2 shards) --")

        # Kill the open-world actors so their shard resources become available
        for actor in shard_actors_ow:
            ray.kill(actor)

        shard_actors_cs = [
            ShardReasoner.options(resources={"shard_0": 1}).remote(
                "Shard-0", shard1_path, "Pellet"),
            ShardReasoner.options(resources={"shard_1": 1}).remote(
                "Shard-1", shard2_path, "Pellet"),
        ]

        cross_shard_reasoner = ShardEnsembleReasoner(shard_actors_cs)
        cs_results = {ind.str for ind in cross_shard_reasoner.instances(query)}
        print(f"  Query:   exists r1.(exists r2.{{o3}})")
        print(f"  Result:  {cs_results}")

        # -- Verdict --------------------------------------------------------
        o1_iri = IRI(NS, "o1").str
        # -- Verdict --------------------------------------------------------
        gt_has_o1 = o1_iri in gt_results
        ow_has_o1 = o1_iri in ow_results
        cs_has_o1 = o1_iri in cs_results
        ow_match  = gt_results == ow_results
        cs_match  = gt_results == cs_results

        W = 62
        print()
        print("=" * W)
        print("  VERDICT".center(W))
        print("=" * W)

        # Results table
        header = f"  {'Mode':<25} {'Contains o1?':>14} {'Matches GT?':>14}"
        print(header)
        print("  " + "-" * (W - 4))
        for label, has_o1, match in [
            ("Ground truth",  gt_has_o1, None),
            ("Open-world",    ow_has_o1, ow_match),
            ("Cross-shard",   cs_has_o1, cs_match),
        ]:
            col1 = ("YES" if has_o1 else "NO").center(14)
            col2 = ("—" if match is None else ("YES" if match else "NO")).center(14)
            print(f"  {label:<25} {col1} {col2}")

        print()

        # Open-world analysis
        if not ow_has_o1:
            print("  [CONFIRMED] Open-world mode cannot return o1.")
            print("    - Each shard evaluates the full CE independently.")
            print("    - G_1: o1 ->r1-> o2, but o2 has no r2 values locally.")
            print("    - G_2: o2 ->r2-> o3, but nobody has r1 values locally.")
            print("    - Neither shard can complete the chain alone.")
        else:
            print("  [UNEXPECTED] Open-world mode returned o1.")

        print()

        # Cross-shard analysis
        if cs_has_o1:
            print("  [SUCCESS] Cross-shard mode correctly returns o1!")
            print("    Bottom-up intermediate-result combination:")
            print("      Step 1  Combine {{o3}} instances across shards  -> {{o3}}")
            print("      Step 2  Find r2 subjects with object in {{o3}} -> {{o2}}")
            print("      Step 3  Find r1 subjects with object in {{o2}} -> {{o1}}")
        else:
            print("  [FAILED] Cross-shard mode did not return o1.")

        print("=" * W)

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        if ray.is_initialized():
            ray.shutdown()


if __name__ == "__main__":
    main()
