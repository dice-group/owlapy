"""IMPORTANT: per the project's JPype constraint (a JVM cannot be restarted once shut down
in the same process), this file never calls stopJVM() on the main-process `SyncReasoner`
baselines it builds for comparison -- matching the convention established in
test_sync_reasoner_extra_coverage.py / test_reasoner_timeout.py. ParallelReasoner's own
workers run in separate spawned processes with their own JVMs, so they are unaffected
either way -- but the main-process comparison reasoner must stay alive for later tests
in the same pytest session.
"""
import unittest

from owlapy.class_expression import OWLClass, OWLObjectSomeValuesFrom
from owlapy.iri import IRI
from owlapy.owl_property import OWLObjectProperty
from owlapy.owl_reasoner import SyncReasoner
from owlapy.parallel_reasoner import ParallelReasoner

NS = "http://example.com/father#"
PATH = "KGs/Family/father.owl"

male = OWLClass(IRI(NS, "male"))
female = OWLClass(IRI(NS, "female"))
has_child = OWLObjectProperty(IRI(NS, "hasChild"))
has_child_female = OWLObjectSomeValuesFrom(has_child, female)


class TestParallelReasoner(unittest.TestCase):

    def test_matches_sync_reasoner_hermit(self):
        with ParallelReasoner(PATH, reasoner="HermiT", num_workers=2) as pr:
            parallel_result = pr.instances(male)

        sync_reasoner = SyncReasoner(ontology=PATH, reasoner="HermiT")
        expected = set(sync_reasoner.instances(male))
        sync_reasoner.close()

        self.assertEqual(parallel_result, expected)
        self.assertTrue(len(expected) > 0)

    def test_matches_sync_reasoner_pellet(self):
        with ParallelReasoner(PATH, reasoner="Pellet", num_workers=2) as pr:
            parallel_result = pr.instances(has_child_female)

        sync_reasoner = SyncReasoner(ontology=PATH, reasoner="Pellet")
        expected = set(sync_reasoner.instances(has_child_female))
        sync_reasoner.close()

        self.assertEqual(parallel_result, expected)

    def test_direct_not_supported(self):
        with ParallelReasoner(PATH, reasoner="HermiT", num_workers=2) as pr:
            with self.assertRaises(NotImplementedError):
                pr.instances(male, direct=True)

    def test_invalid_reasoner_name_rejected_eagerly(self):
        with self.assertRaises(AssertionError):
            ParallelReasoner(PATH, reasoner="NotAReasoner")

    def test_pool_reused_across_calls(self):
        with ParallelReasoner(PATH, reasoner="HermiT", num_workers=2) as pr:
            males = pr.instances(male)
            females = pr.instances(female)
            pool_after_first_two_calls = pr._pool
            self.assertIsNotNone(pool_after_first_two_calls)

        self.assertTrue(males.isdisjoint(females))

    def test_empty_individual_domain_returns_empty_set_without_error(self):
        with ParallelReasoner(PATH, reasoner="HermiT", num_workers=2) as pr:
            result = pr.instances(male, individuals=[])
        self.assertEqual(result, set())

    def test_per_individual_timeout_excludes_rather_than_raises(self):
        # A timeout of 0s forces SyncReasoner.is_entailed() to raise TimeoutError on
        # (almost) every individual inside the worker; ParallelReasoner must swallow
        # that per-individual and return a (conservative, possibly empty) result
        # instead of letting the exception propagate out of instances().
        with ParallelReasoner(PATH, reasoner="HermiT", num_workers=2) as pr:
            result = pr.instances(male, timeout=0)
        self.assertEqual(result, set())


if __name__ == "__main__":
    unittest.main()
