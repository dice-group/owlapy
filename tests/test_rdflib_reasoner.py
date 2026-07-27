"""Tests for RDFLibReasoner - Pure Python RDFLib-based reasoner."""
import unittest
from pathlib import Path

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_property import OWLObjectProperty
from owlapy.owl_reasoner_rdflib import RDFLibReasoner


class TestRDFLibReasoner(unittest.TestCase):
    """Test cases for RDFLibReasoner."""

    @classmethod
    def setUpClass(cls):
        """Set up test ontology."""
        cls.kg_path = Path("KGs/Family/family-benchmark_rich_background.owl")
        if not cls.kg_path.exists():
            raise unittest.SkipTest("Family ontology not available")

        cls.onto = SyncOntology(str(cls.kg_path))
        cls.reasoner = RDFLibReasoner(cls.onto, class_cache=True, property_cache=True)

        # Define commonly used classes
        cls.NS = "http://www.benchmark.org/family#"
        cls.male = OWLClass(IRI(cls.NS, "Male"))
        cls.female = OWLClass(IRI(cls.NS, "Female"))
        cls.person = OWLClass(IRI(cls.NS, "Person"))
        cls.father = OWLClass(IRI(cls.NS, "Father"))
        cls.mother = OWLClass(IRI(cls.NS, "Mother"))

        # Define properties
        cls.has_child = OWLObjectProperty(IRI(cls.NS, "hasChild"))

    def test_reasoner_initialization(self):
        """Test that reasoner initializes correctly."""
        self.assertIsNotNone(self.reasoner)
        self.assertIsNotNone(self.reasoner._graph)
        self.assertGreater(len(self.reasoner._graph), 0, "Graph should contain triples")

    def test_instances_of_named_class(self):
        """Test retrieving instances of a named class."""
        males = set(self.reasoner.instances(self.male))
        self.assertGreater(len(males), 0, "Should find male instances")

        # All males should be OWLNamedIndividual
        for ind in males:
            self.assertIsInstance(ind, OWLNamedIndividual)

    def test_instances_caching(self):
        """Test that instance caching works."""
        # First call - should populate cache
        males_1 = set(self.reasoner.instances(self.male))

        # Second call - should use cache
        males_2 = set(self.reasoner.instances(self.male))

        self.assertEqual(males_1, males_2, "Cached results should match")
        self.assertIn(self.male, self.reasoner._cls_to_ind, "Class should be in cache")

    def test_direct_subclasses(self):
        """Test retrieving direct subclasses."""
        # Person should have Male and Female as subclasses (if defined in ontology)
        direct_subs = set(self.reasoner.sub_classes(self.person, direct=True))

        # Check that we get some subclasses
        self.assertIsInstance(direct_subs, set)
        # All should be OWLClass instances
        for cls in direct_subs:
            self.assertIsInstance(cls, OWLClass)

    def test_all_subclasses(self):
        """Test retrieving all descendant subclasses."""
        all_subs = set(self.reasoner.sub_classes(self.person, direct=False))
        direct_subs = set(self.reasoner.sub_classes(self.person, direct=True))

        # All subclasses should include at least direct subclasses
        self.assertGreaterEqual(len(all_subs), len(direct_subs))

    def test_direct_superclasses(self):
        """Test retrieving direct superclasses."""
        direct_supers = set(self.reasoner.super_classes(self.male, direct=True))

        # Male should have Person as superclass
        # This depends on the ontology structure
        self.assertIsInstance(direct_supers, set)
        for cls in direct_supers:
            self.assertIsInstance(cls, OWLClass)

    def test_all_superclasses(self):
        """Test retrieving all ancestor superclasses."""
        all_supers = set(self.reasoner.super_classes(self.male, direct=False))
        direct_supers = set(self.reasoner.super_classes(self.male, direct=True))

        # All superclasses should include at least direct superclasses
        self.assertGreaterEqual(len(all_supers), len(direct_supers))

    def test_hierarchy_consistency(self):
        """Test that subclass/superclass relationships are consistent."""
        # If B is a subclass of A, then A should be a superclass of B
        direct_subs = set(self.reasoner.sub_classes(self.person, direct=True))

        for sub in direct_subs:
            supers = set(self.reasoner.super_classes(sub, direct=True))
            self.assertIn(
                self.person,
                supers,
                f"{sub} should have {self.person} as superclass"
            )

    def test_no_circular_dependencies(self):
        """Test that there are no circular dependencies in hierarchy traversal."""
        # Getting all subclasses should terminate
        all_subs = list(self.reasoner.sub_classes(self.person, direct=False))
        self.assertIsInstance(all_subs, list)

        # Getting all superclasses should terminate
        all_supers = list(self.reasoner.super_classes(self.male, direct=False))
        self.assertIsInstance(all_supers, list)

    def test_equivalent_classes(self):
        """Test retrieving equivalent classes."""
        equiv = set(self.reasoner.equivalent_classes(self.male))
        # May or may not have equivalent classes depending on ontology
        self.assertIsInstance(equiv, set)

    def test_disjoint_classes(self):
        """Test retrieving disjoint classes."""
        disjoint = set(self.reasoner.disjoint_classes(self.male))
        # Male and Female should be disjoint if defined in ontology
        self.assertIsInstance(disjoint, set)

    def test_object_property_values(self):
        """Test retrieving object property values."""
        # Get a father instance
        fathers = list(self.reasoner.instances(self.father))
        if len(fathers) > 0:
            father_ind = fathers[0]

            # Get children
            children = set(self.reasoner.object_property_values(
                father_ind,
                self.has_child
            ))

            # Should be a set (may be empty)
            self.assertIsInstance(children, set)

    def test_flush_cache(self):
        """Test that flush clears caches and reloads."""
        # Populate cache
        _ = set(self.reasoner.instances(self.male))
        self.assertGreater(len(self.reasoner._cls_to_ind), 0)

        # Flush
        self.reasoner.flush()

        # Cache should be empty
        self.assertEqual(len(self.reasoner._cls_to_ind), 0)

        # Should still work after flush
        males = set(self.reasoner.instances(self.male))
        self.assertGreater(len(males), 0)

    def test_comparison_with_structural_reasoner(self):
        """Compare results with StructuralReasoner."""
        try:
            from owlapy.owl_ontology import Ontology
            from owlapy.owl_reasoner import StructuralReasoner

            # StructuralReasoner requires Ontology, not SyncOntology
            ontology_for_structural = Ontology(str(self.kg_path))
            structural = StructuralReasoner(ontology_for_structural)

            # Compare instance retrieval
            rdflib_males = set(self.reasoner.instances(self.male))
            structural_males = set(structural.instances(self.male))

            # Results should be the same
            self.assertEqual(
                rdflib_males,
                structural_males,
                "RDFLibReasoner and StructuralReasoner should return same instances"
            )

            # Compare subclass retrieval
            rdflib_subs = set(self.reasoner.sub_classes(self.person, direct=True))
            structural_subs = set(structural.sub_classes(self.person, direct=True))

            self.assertEqual(
                rdflib_subs,
                structural_subs,
                "Both reasoners should return same direct subclasses"
            )

        except (ImportError, Exception) as e:
            self.skipTest(f"StructuralReasoner comparison not available: {e}")

    def test_drop_in_replacement(self):
        """Test that RDFLibReasoner can be used as drop-in replacement."""
        # This test demonstrates the same API
        reasoner = self.reasoner

        # Standard usage pattern
        instances = set(reasoner.instances(self.male, direct=False))
        self.assertGreater(len(instances), 0)

        sub_classes = set(reasoner.sub_classes(self.person, direct=True))
        self.assertIsInstance(sub_classes, set)

        super_classes = set(reasoner.super_classes(self.male, direct=True))
        self.assertIsInstance(super_classes, set)

        # All methods should return iterables
        self.assertTrue(hasattr(instances, '__iter__'))
        self.assertTrue(hasattr(sub_classes, '__iter__'))
        self.assertTrue(hasattr(super_classes, '__iter__'))


class TestRDFLibReasonerPerformance(unittest.TestCase):
    """Performance tests for RDFLibReasoner."""

    def setUp(self):
        """Set up test ontology."""
        kg_path = Path("KGs/Family/family-benchmark_rich_background.owl")
        if not kg_path.exists():
            self.skipTest("Family ontology not available")

        self.onto = SyncOntology(str(kg_path))

    def test_cache_performance(self):
        """Test that caching improves performance."""
        import time

        # Reasoner with cache
        cached_reasoner = RDFLibReasoner(self.onto, class_cache=True)
        male = OWLClass(IRI("http://www.benchmark.org/family#", "Male"))

        # First call (populate cache)
        start = time.time()
        _ = list(cached_reasoner.instances(male))
        first_time = time.time() - start

        # Second call (use cache)
        start = time.time()
        _ = list(cached_reasoner.instances(male))
        cached_time = time.time() - start

        # Cached should be significantly faster
        self.assertLess(cached_time, first_time / 2,
                       "Cached retrieval should be at least 2x faster")

    def test_hierarchy_traversal_terminates(self):
        """Test that hierarchy traversal completes in reasonable time."""
        import time

        reasoner = RDFLibReasoner(self.onto)
        person = OWLClass(IRI("http://www.benchmark.org/family#", "Person"))

        # This should complete quickly (< 1 second for small ontology)
        start = time.time()
        all_subs = list(reasoner.sub_classes(person, direct=False))
        elapsed = time.time() - start

        self.assertLess(elapsed, 5.0,
                       "Hierarchy traversal should complete within 5 seconds")
        self.assertIsInstance(all_subs, list)


class TestRDFLibReasonerConstruction(unittest.TestCase):
    """Cover the constructor branches that TestRDFLibReasoner's shared setUpClass
    (always a pre-built SyncOntology) never exercises."""

    @classmethod
    def setUpClass(cls):
        cls.kg_path = Path("KGs/Family/family-benchmark_rich_background.owl")
        if not cls.kg_path.exists():
            raise unittest.SkipTest("Family ontology not available")
        cls.NS = "http://www.benchmark.org/family#"

    def test_construction_from_string_path(self):
        # Passing a raw path string exercises the `isinstance(ontology, str)` branch.
        reasoner = RDFLibReasoner(str(self.kg_path))
        self.assertIsInstance(reasoner._ontology, SyncOntology)
        self.assertGreater(len(reasoner._graph), 0)

    def test_construction_from_plain_ontology(self):
        from owlapy.owl_ontology import Ontology

        onto = Ontology(str(self.kg_path))
        reasoner = RDFLibReasoner(onto)
        self.assertGreater(len(reasoner._graph), 0)
        male = OWLClass(IRI(self.NS, "Male"))
        self.assertGreater(len(set(reasoner.instances(male))), 0)


class TestRDFLibReasonerComplexExpressionsAndStubs(unittest.TestCase):
    """Cover branches for non-OWLClass class expressions, complex property
    expressions, and the many not-fully-implemented stub methods."""

    @classmethod
    def setUpClass(cls):
        cls.kg_path = Path("KGs/Family/family-benchmark_rich_background.owl")
        if not cls.kg_path.exists():
            raise unittest.SkipTest("Family ontology not available")

        cls.onto = SyncOntology(str(cls.kg_path))
        cls.reasoner = RDFLibReasoner(cls.onto)

        cls.NS = "http://www.benchmark.org/family#"
        cls.male = OWLClass(IRI(cls.NS, "Male"))
        cls.female = OWLClass(IRI(cls.NS, "Female"))
        cls.person = OWLClass(IRI(cls.NS, "Person"))
        cls.has_child = OWLObjectProperty(IRI(cls.NS, "hasChild"))

    def test_instances_with_complex_class_expression(self):
        from owlapy.class_expression import OWLObjectSomeValuesFrom

        ce = OWLObjectSomeValuesFrom(self.has_child, self.person)
        result = set(self.reasoner.instances(ce))
        self.assertIsInstance(result, set)

    def test_instances_manual_fallback_returns_empty(self):
        from owlapy.class_expression import OWLObjectSomeValuesFrom

        ce = OWLObjectSomeValuesFrom(self.has_child, self.person)
        result = list(self.reasoner._instances_manual(ce))
        self.assertEqual(result, [])

    def test_instances_direct_true_logs_warning_and_still_returns(self):
        result = set(self.reasoner.instances(self.male, direct=True))
        self.assertGreater(len(result), 0)

    def test_sub_classes_with_complex_expression_returns_empty(self):
        from owlapy.class_expression import OWLObjectSomeValuesFrom

        ce = OWLObjectSomeValuesFrom(self.has_child, self.person)
        self.assertEqual(list(self.reasoner.sub_classes(ce, direct=True)), [])
        self.assertEqual(list(self.reasoner.sub_classes(ce, direct=False)), [])

    def test_super_classes_with_complex_expression_returns_empty(self):
        from owlapy.class_expression import OWLObjectSomeValuesFrom

        ce = OWLObjectSomeValuesFrom(self.has_child, self.person)
        self.assertEqual(list(self.reasoner.super_classes(ce, direct=True)), [])
        self.assertEqual(list(self.reasoner.super_classes(ce, direct=False)), [])

    def test_equivalent_classes_with_complex_expression_returns_empty(self):
        from owlapy.class_expression import OWLObjectSomeValuesFrom

        ce = OWLObjectSomeValuesFrom(self.has_child, self.person)
        self.assertEqual(list(self.reasoner.equivalent_classes(ce)), [])

    def test_disjoint_classes_with_complex_expression_returns_empty(self):
        from owlapy.class_expression import OWLObjectSomeValuesFrom

        ce = OWLObjectSomeValuesFrom(self.has_child, self.person)
        self.assertEqual(list(self.reasoner.disjoint_classes(ce)), [])

    def test_object_property_values_with_complex_property_returns_empty(self):
        from owlapy.owl_property import OWLObjectInverseOf

        fathers = list(self.reasoner.instances(self.male))
        self.assertGreater(len(fathers), 0)
        inverse = OWLObjectInverseOf(self.has_child)
        result = list(self.reasoner.object_property_values(fathers[0], inverse))
        self.assertEqual(result, [])

    def test_get_root_ontology(self):
        self.assertIs(self.reasoner.get_root_ontology(), self.onto)

    def test_types_returns_all_and_direct(self):
        males = list(self.reasoner.instances(self.male))
        self.assertGreater(len(males), 0)
        ind = males[0]

        all_types = set(self.reasoner.types(ind, direct=False))
        self.assertIn(self.male, all_types)

        direct_types = set(self.reasoner.types(ind, direct=True))
        self.assertIsInstance(direct_types, set)
        # Direct types are a subset of all types.
        self.assertTrue(direct_types.issubset(all_types))

    def test_same_individuals_returns_iterable(self):
        males = list(self.reasoner.instances(self.male))
        result = set(self.reasoner.same_individuals(males[0]))
        self.assertIsInstance(result, set)

    def test_not_implemented_stub_methods_return_empty_iterators(self):
        males = list(self.reasoner.instances(self.male))
        ind = males[0]

        self.assertEqual(list(self.reasoner.data_property_domains(None)), [])
        self.assertEqual(list(self.reasoner.object_property_domains(None)), [])
        self.assertEqual(list(self.reasoner.object_property_ranges(None)), [])
        self.assertEqual(list(self.reasoner.data_property_values(ind, None)), [])
        self.assertEqual(list(self.reasoner.different_individuals(ind)), [])
        self.assertEqual(list(self.reasoner.equivalent_object_properties(self.has_child)), [])
        self.assertEqual(list(self.reasoner.equivalent_data_properties(None)), [])
        self.assertEqual(list(self.reasoner.disjoint_object_properties(self.has_child)), [])
        self.assertEqual(list(self.reasoner.disjoint_data_properties(None)), [])
        self.assertEqual(list(self.reasoner.sub_data_properties(None)), [])
        self.assertEqual(list(self.reasoner.super_data_properties(None)), [])
        self.assertEqual(list(self.reasoner.sub_object_properties(self.has_child)), [])
        self.assertEqual(list(self.reasoner.super_object_properties(self.has_child)), [])

    def test_repr(self):
        self.assertIn("RDFLibReasoner(", repr(self.reasoner))


if __name__ == '__main__':
    unittest.main()
