"""
Regression test for distributed (DDP) reasoning correctness.

Runs the evaluation pipeline from ``ddp_reasoning_eval.py`` with a small
sample of the Mutagenesis ontology split into 2 shards and verifies that
every distributed retrieval result exactly matches the ground-truth
SyncReasoner (Jaccard similarity == 1.0 for all expressions).

Requirements
------------
- ``ray`` must be installed (``pip install ray``).
- The Mutagenesis ontology must be present at
  ``KGs/Mutagenesis/mutagenesis.owl`` relative to the repository root.

The test is intentionally lightweight (ratio_sample_nc=0.001,
ratio_sample_object_prop=0.001) so it finishes in under a minute while
still exercising the full distributed pipeline.
"""

import os
import sys
import unittest
from argparse import Namespace
from pathlib import Path

# Ensure the repository root is on sys.path so ddp_reasoning_eval can be
# imported regardless of the working directory pytest / unittest uses.
REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


class TestDDPReasoningRegression(unittest.TestCase):
    """Smoke / regression test: distributed reasoning must match ground truth."""

    @classmethod
    def setUpClass(cls):
        """Set PYTHONHASHSEED for deterministic set/hash ordering."""
        os.environ["PYTHONHASHSEED"] = "1"
        # Suppress Ray log-deduplication banner
        os.environ["RAY_DEDUP_LOGS"] = "0"

    def test_mutagenesis_2_shards_open_world(self):
        """2-shard open-world eval on Mutagenesis (tiny sample) must yield perfect Jaccard."""

        # Skip gracefully when ray is not installed.
        try:
            import ray  # noqa: F401
        except ImportError:
            self.skipTest("ray is not installed — skipping DDP regression test")

        # Import here so PYTHONHASHSEED is already set.
        from ddp_reasoning_eval import execute

        ontology_path = os.path.join(REPO_ROOT, "KGs", "Mutagenesis", "mutagenesis.owl")
        if not os.path.isfile(ontology_path):
            self.skipTest(f"Ontology not found: {ontology_path}")

        args = Namespace(
            path_kg=ontology_path,
            num_shards=2,
            reasoner="Pellet",
            seed=1,
            ratio_sample_nc=0.001,
            ratio_sample_object_prop=0.001,
            min_jaccard_similarity=1.0,
            num_nominals=1,
            path_report=os.path.join(REPO_ROOT, "DDP_Regression_Test_Results.csv"),
            no_negations=False,
            open_world=True,
            cross_shard=False,
            auto_ray=True,
        )

        mean_jaccard, mean_f1 = execute(args)

        self.assertAlmostEqual(
            mean_jaccard, 1.0, places=4,
            msg=f"Mean Jaccard similarity {mean_jaccard:.4f} != 1.0 — distributed retrieval diverged from ground truth!",
        )
        self.assertAlmostEqual(
            mean_f1, 1.0, places=4,
            msg=f"Mean F1 {mean_f1:.4f} != 1.0 — distributed retrieval diverged from ground truth!",
        )

    @classmethod
    def tearDownClass(cls):
        """Shut down Ray if it was started during the test."""
        try:
            import ray
            if ray.is_initialized():
                ray.shutdown()
        except ImportError:
            pass

        # Clean up the test report CSV
        report = os.path.join(REPO_ROOT, "DDP_Regression_Test_Results.csv")
        if os.path.isfile(report):
            os.remove(report)


# ---------------------------------------------------------------------------
# Inline ontology for the cross-shard cardinality counterexample
# ---------------------------------------------------------------------------
_CARDINALITY_NS = "http://example.org/test#"
_CARDINALITY_OWL = """\
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
    <owl:ObjectProperty rdf:about="http://example.org/test#r"/>

    <owl:NamedIndividual rdf:about="http://example.org/test#a">
        <test:r rdf:resource="http://example.org/test#o1"/>
        <test:r rdf:resource="http://example.org/test#o2"/>
    </owl:NamedIndividual>

    <owl:NamedIndividual rdf:about="http://example.org/test#o1">
        <rdf:type rdf:resource="http://example.org/test#C"/>
    </owl:NamedIndividual>
    <owl:NamedIndividual rdf:about="http://example.org/test#o2">
        <rdf:type rdf:resource="http://example.org/test#C"/>
    </owl:NamedIndividual>

    <rdf:Description>
        <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#AllDifferent"/>
        <owl:distinctMembers rdf:parseType="Collection">
            <rdf:Description rdf:about="http://example.org/test#o1"/>
            <rdf:Description rdf:about="http://example.org/test#o2"/>
        </owl:distinctMembers>
    </rdf:Description>
</rdf:RDF>
"""


class TestCrossShardCardinality(unittest.TestCase):
    """Verify that ≥2 r.C is correctly resolved across shards.

    Ontology:  AllDifferent(o1, o2), r(a, o1), r(a, o2), C(o1), C(o2)
    Query:     ≥ 2 r.C
    Expected:  {a}

    With 3 shards the property assertions land in a's shard while the
    class assertions for o1/o2 land in different shards.  Without the
    cross-shard cardinality join the distributed reasoner returns {}.
    """

    _tmp_dir: str = ""

    @classmethod
    def setUpClass(cls):
        os.environ["PYTHONHASHSEED"] = "1"
        os.environ["RAY_DEDUP_LOGS"] = "0"

        cls._tmp_dir = os.path.join(REPO_ROOT, "debug_cardinality_test_unittest")
        os.makedirs(cls._tmp_dir, exist_ok=True)
        cls._owl_path = os.path.join(cls._tmp_dir, "cardinality_test.owl")
        with open(cls._owl_path, "w") as f:
            f.write(_CARDINALITY_OWL)

    def test_min_cardinality_2_cross_shard(self):
        """≥ 2 r.C must return {a} even when fillers are on different shards."""
        try:
            import ray
        except ImportError:
            self.skipTest("ray is not installed — skipping DDP cardinality test")

        from owlapy.owl_reasoner import SyncReasoner
        from owlapy.class_expression import (
            OWLClass, OWLObjectSomeValuesFrom, OWLObjectMinCardinality,
        )
        from owlapy.owl_property import OWLObjectProperty
        from owlapy.iri import IRI
        from shard_ontology import shard_ontology
        from ddp_reasoning import ShardReasoner, ShardEnsembleReasoner

        num_shards = 3
        shard_ontology(self._owl_path, num_shards, self._tmp_dir)

        C = OWLClass(IRI(_CARDINALITY_NS, "C"))
        r = OWLObjectProperty(IRI(_CARDINALITY_NS, "r"))
        min_2_r_C = OWLObjectMinCardinality(2, r, C)
        exists_r_C = OWLObjectSomeValuesFrom(property=r, filler=C)

        # Ground truth — must be created before ray.init()
        gt = SyncReasoner(ontology=self._owl_path, reasoner="Pellet")
        gt_min = {i.str for i in gt.instances(min_2_r_C)}
        gt_exists = {i.str for i in gt.instances(exists_r_C)}

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
        dist = ShardEnsembleReasoner(shards, open_world=True, verbose=False)
        dist_min = {i.str for i in dist.instances(min_2_r_C)}
        dist_exists = {i.str for i in dist.instances(exists_r_C)}

        self.assertEqual(
            gt_min, dist_min,
            f"≥ 2 r.C mismatch — GT={gt_min}, Dist={dist_min}",
        )
        self.assertEqual(
            gt_exists, dist_exists,
            f"∃ r.C mismatch — GT={gt_exists}, Dist={dist_exists}",
        )

    @classmethod
    def tearDownClass(cls):
        try:
            import ray
            if ray.is_initialized():
                ray.shutdown()
        except ImportError:
            pass

        import shutil
        if cls._tmp_dir and os.path.isdir(cls._tmp_dir):
            shutil.rmtree(cls._tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
