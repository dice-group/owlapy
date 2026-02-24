"""
Regression test for distributed (DDP) reasoning incompleteness for forall (∀ r.C) queries under OWA.

This test verifies that the ShardEnsembleReasoner is incomplete for ∀ r.C when the ontology is sharded, as described in counterexample_forall_incompleteness.py.

Requirements
------------
- ``ray`` must be installed (``pip install ray``).
- No external files required; ontology is defined inline.
"""

import os
import sys
import unittest
from argparse import Namespace
from pathlib import Path
from owlapy.owl_reasoner import SyncReasoner

REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

NS = "http://example.org/test#"
ONTOLOGY_OWL = """\
<?xml version="1.0"?>
<rdf:RDF xmlns="http://example.org/test#"
     xml:base="http://example.org/test"
     xmlns:owl="http://www.w3.org/2002/07/owl#"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:xml="http://www.w3.org/XML/1998/namespace"
     xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
     xmlns:test="http://example.org/test#">
    <owl:Ontology rdf:about="http://example.org/test"/>
    <owl:Class rdf:about="http://example.org/test#C"/>
    <owl:ObjectProperty rdf:about="http://example.org/test#r">
        <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#FunctionalProperty"/>
    </owl:ObjectProperty>
    <owl:NamedIndividual rdf:about="http://example.org/test#a">
        <test:r rdf:resource="http://example.org/test#b"/>
    </owl:NamedIndividual>
    <owl:NamedIndividual rdf:about="http://example.org/test#b">
        <rdf:type rdf:resource="http://example.org/test#C"/>
    </owl:NamedIndividual>
</rdf:RDF>
"""


class TestForallIncompleteness(unittest.TestCase):
    """Verify that ShardEnsembleReasoner is incomplete for ∀ r.C under OWA.

    Ontology: FunctionalObjectProperty(r), r(a, b), C(b)
    Query: ∀ r.C
    Ground truth: {a}
    Sharded: Should return empty set (incomplete)
    """
    _tmp_dir: str = ""

    @classmethod
    def setUpClass(cls):
        os.environ["PYTHONHASHSEED"] = "1"
        os.environ["RAY_DEDUP_LOGS"] = "0"
        cls._tmp_dir = os.path.join(REPO_ROOT, "debug_forall_test_unittest")
        os.makedirs(cls._tmp_dir, exist_ok=True)
        cls._owl_path = os.path.join(cls._tmp_dir, "forall_test.owl")
        with open(cls._owl_path, "w") as f:
            f.write(ONTOLOGY_OWL)

    def test_forall_incompleteness(self):
        """ShardEnsembleReasoner should miss ∀ r.C (return empty set)."""
        try:
            import ray
        except ImportError:
            self.skipTest("ray is not installed — skipping forall incompleteness test")

        from owlapy.class_expression import (
            OWLClass, OWLObjectAllValuesFrom, OWLObjectSomeValuesFrom,
        )
        from owlapy.owl_property import OWLObjectProperty
        from owlapy.iri import IRI
        from shard_ontology import shard_ontology
        from ddp_reasoning import ShardReasoner, ShardEnsembleReasoner

        num_shards = 2
        # Shard
        shard_ontology(self._owl_path, num_shards, self._tmp_dir)
        
        # Queries
        C = OWLClass(IRI(NS, "C"))
        r = OWLObjectProperty(IRI(NS, "r"))
        forall_r_C = OWLObjectAllValuesFrom(property=r, filler=C)
        exists_r_C = OWLObjectSomeValuesFrom(property=r, filler=C)

        # Ground truth
        # NOTE: SyncReasoner must be created BEFORE ray.init() to avoid a
        # SIGSEGV caused by JPype/Ray JVM conflicts in the driver process.
        gt = SyncReasoner(ontology=self._owl_path, reasoner="Pellet")
        gt_forall = {i.str for i in gt.instances(forall_r_C)}
        gt_exists = {i.str for i in gt.instances(exists_r_C)}


        expected = {f"{NS}a"}

        if not ray.is_initialized():
            ray.init(
                num_cpus=os.cpu_count(),
                resources={f"shard_{i}": 1 for i in range(num_shards)},
            )

        stem = Path(self._owl_path).stem
        shards = [
            ShardReasoner.options(resources={f"shard_{i}": 1}).remote(
                f"Shard-{i}",
                os.path.join(self._tmp_dir, f"{stem}_shard_{i}.owl"),
                "Pellet",
                verbose=False,
            )
            for i in range(num_shards)
        ]
        
        dist = ShardEnsembleReasoner(shards, verbose=False)
        dist_forall = {i.str for i in dist.instances(forall_r_C)}
        dist_exists = {i.str for i in dist.instances(exists_r_C)}


        # ∀ r.C should be empty (incomplete)
        self.assertEqual(
            gt_forall, dist_forall,
            f"∀ r.C should be empty — expected={gt_forall}, Dist={dist_forall}"
        )
        # ∃ r.C should still be empty (since b : C is not visible in the same shard as (a, r, b))
        self.assertEqual(
            gt_exists, dist_exists,
            f"∃ r.C should be empty — expected={gt_exists}, Dist={dist_exists}"
        )

    @classmethod
    def tearDownClass(cls):
        import shutil
        if cls._tmp_dir and os.path.isdir(cls._tmp_dir):
            shutil.rmtree(cls._tmp_dir, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
