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


if __name__ == "__main__":
    unittest.main()
