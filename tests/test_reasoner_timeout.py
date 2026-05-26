"""Tests for timeout functionality in SyncReasoner methods."""
import os
import unittest

from owlapy import dl_to_owl_expression
from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLClassAssertionAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner import SyncReasoner


class TestSyncReasonerTimeout(unittest.TestCase):
    """Test timeout functionality in SyncReasoner."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.ontology_path = None
        for root, dirs, files in os.walk("."):
            for file in files:
                if file == "family-benchmark_rich_background.owl":
                    cls.ontology_path = os.path.abspath(os.path.join(root, file))
                    break
            if cls.ontology_path:
                break

        if cls.ontology_path is None:
            raise FileNotFoundError("Could not locate 'family-benchmark_rich_background.owl' within project structure.")

        cls.namespace = "http://www.benchmark.org/family#"

        try:
            cls.ontology = SyncOntology(cls.ontology_path)
            cls.reasoner = SyncReasoner(cls.ontology, reasoner="Pellet")
        except Exception as e:
            raise RuntimeError(f"Failed to load ontology or initialize reasoner: {e}")

    def test_instances_with_short_timeout(self):
        """Test instances() method completes within reasonable timeout."""
        ce = OWLClass(IRI.create(self.namespace + "Male"))

        # Should complete successfully with a reasonable timeout (10 seconds)
        individuals = set(self.reasoner.instances(ce, timeout=10))

        self.assertIsInstance(individuals, set, "instances() should return a set")
        self.assertGreater(len(individuals), 0, "Should find Male individuals")

    def test_instances_with_complex_expression(self):
        """Test instances() with complex class expression and timeout."""
        dl_expr = "∃ hasChild.Male"
        ce = dl_to_owl_expression(dl_expr, self.namespace)

        # Complex expression with reasonable timeout
        individuals = set(self.reasoner.instances(ce, timeout=15))

        self.assertIsInstance(individuals, set)
        # We expect some individuals to satisfy this expression

    def test_create_axiom_justifications_default_timeout(self):
        """Test create_axiom_justifications with default timeout parameter."""
        individual = OWLNamedIndividual(IRI.create(self.namespace + "F10M171"))
        dl_expr_str = "∃ hasChild.Male"
        target_class = dl_to_owl_expression(dl_expr_str, self.namespace)

        axiom = OWLClassAssertionAxiom(individual, target_class)

        # Should work with default timeout
        justifications = self.reasoner.create_axiom_justifications(axiom, save=False)

        self.assertIsInstance(justifications, list)
        self.assertGreater(len(justifications), 0, "Should find at least one justification")

        for justification in justifications:
            self.assertIsInstance(justification, set)
            self.assertGreater(len(justification), 0, "Each justification should contain axioms")

    def test_create_axiom_justifications_custom_timeout(self):
        """Test create_axiom_justifications with custom timeout."""
        individual = OWLNamedIndividual(IRI.create(self.namespace + "F10M171"))
        dl_expr_str = "∃ hasChild.Male"
        target_class = dl_to_owl_expression(dl_expr_str, self.namespace)

        axiom = OWLClassAssertionAxiom(individual, target_class)

        # Test with custom timeout of 20 seconds
        justifications = self.reasoner.create_axiom_justifications(
            axiom,
            n_max_justifications=5,
            timeout=20,
            save=False
        )

        self.assertIsInstance(justifications, list)
        # Should get at most 5 justifications
        self.assertLessEqual(len(justifications), 5)

    def test_instances_parameter_validation(self):
        """Test that instances method accepts timeout parameter correctly."""
        ce = OWLClass(IRI.create(self.namespace + "Female"))

        # Test with various timeout values
        individuals_short = set(self.reasoner.instances(ce, timeout=5))
        individuals_long = set(self.reasoner.instances(ce, timeout=30))

        # Both should return the same results (just different timeouts)
        self.assertEqual(individuals_short, individuals_long,
                        "Different timeouts should return same results for simple queries")

    def test_instances_direct_parameter_with_timeout(self):
        """Test instances method with both direct and timeout parameters."""
        ce = OWLClass(IRI.create(self.namespace + "Person"))

        # Test with direct=False and timeout
        all_instances = set(self.reasoner.instances(ce, direct=False, timeout=10))

        # Test with direct=True and timeout
        direct_instances = set(self.reasoner.instances(ce, direct=True, timeout=10))

        self.assertIsInstance(all_instances, set)
        self.assertIsInstance(direct_instances, set)
        # Direct instances should be a subset of all instances
        self.assertTrue(direct_instances.issubset(all_instances) or len(direct_instances) == 0)

    @classmethod
    def tearDownClass(cls):
        """Clean up resources."""
        if hasattr(cls, 'reasoner'):
            try:
                from owlapy.static_funcs import stopJVM
                stopJVM()
            except Exception:
                pass  # JVM might already be stopped


if __name__ == '__main__':
    unittest.main()
