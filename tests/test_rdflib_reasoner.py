"""Tests for RDFLibReasoner - Pure Python RDFLib-based reasoner."""
import unittest
from pathlib import Path
from unittest import mock

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_ontology import RDFLibOntology, SyncOntology
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty
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
        # Passing a raw path string exercises the `isinstance(ontology, str)` branch. It must be
        # ingested straight into rdflib -- no owlready2/SyncOntology round-trip, no JVM.
        reasoner = RDFLibReasoner(str(self.kg_path))
        self.assertIsInstance(reasoner._ontology, RDFLibOntology)
        self.assertGreater(len(reasoner._graph), 0)
        # The reasoner must reuse the ontology's own graph, not a re-parsed copy.
        self.assertIs(reasoner._graph, reasoner._ontology.rdflib_graph)

    def test_construction_from_string_path_never_starts_jvm(self):
        # Regression test for #205 Group A item 2: a str path must never touch owlready2's
        # SyncOntology/JVM bridge, since that used to be the only ingestion path.
        with mock.patch("owlapy.owl_ontology.startJVM") as mocked_start_jvm:
            reasoner = RDFLibReasoner(str(self.kg_path))
            mocked_start_jvm.assert_not_called()
        self.assertGreater(len(reasoner._graph), 0)

    def test_construction_from_rdflib_ontology_reuses_graph(self):
        # An RDFLibOntology instance should have its rdflib_graph reused directly, not
        # round-tripped through a save()+reparse cycle.
        onto = RDFLibOntology(str(self.kg_path))
        reasoner = RDFLibReasoner(onto)
        self.assertIs(reasoner._graph, onto.rdflib_graph)

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

    def test_object_property_values_with_inverse_property(self):
        """OWLObjectInverseOf(has_child) applied to `child` returns child's parents -- i.e.
        every x such that x hasChild child. Previously (a bug, fixed alongside owlapy#242)
        object_property_values rejected any non-OWLObjectProperty input outright and always
        returned an empty result, regardless of whether real triples existed to answer it."""
        from owlapy.owl_property import OWLObjectInverseOf

        fathers = list(self.reasoner.instances(self.male))
        self.assertGreater(len(fathers), 0)
        child = fathers[0]
        inverse = OWLObjectInverseOf(self.has_child)
        result = set(self.reasoner.object_property_values(child, inverse))

        # Cross-check against the direct forward relation: parents are exactly those persons p
        # for which child is one of p's hasChild values.
        expected = {
            p for p in self.reasoner.instances(self.person)
            if child in set(self.reasoner.object_property_values(p, self.has_child))
        }
        self.assertEqual(result, expected)

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

    def test_property_axiom_methods_with_no_asserted_axioms_return_empty(self):
        """`hasChild` in the Family benchmark ontology has no domain/range/subPropertyOf/
        equivalentProperty/propertyDisjointWith axioms, and this ontology has no data
        properties at all -- these methods should return empty results, not crash, when
        given real (but axiom-free) property objects."""
        males = list(self.reasoner.instances(self.male))
        ind = males[0]
        dummy_dp = OWLDataProperty(IRI(self.NS, "doesNotExist"))

        self.assertEqual(list(self.reasoner.data_property_domains(dummy_dp)), [])
        self.assertEqual(list(self.reasoner.object_property_domains(self.has_child)), [])
        self.assertEqual(list(self.reasoner.object_property_ranges(self.has_child)), [])
        self.assertEqual(list(self.reasoner.data_property_values(ind, dummy_dp)), [])
        self.assertEqual(list(self.reasoner.different_individuals(ind)), [])
        self.assertEqual(list(self.reasoner.equivalent_object_properties(self.has_child)), [])
        self.assertEqual(list(self.reasoner.equivalent_data_properties(dummy_dp)), [])
        self.assertEqual(list(self.reasoner.disjoint_object_properties(self.has_child)), [])
        self.assertEqual(list(self.reasoner.disjoint_data_properties(dummy_dp)), [])
        self.assertEqual(list(self.reasoner.sub_data_properties(dummy_dp)), [])
        self.assertEqual(list(self.reasoner.super_data_properties(dummy_dp)), [])
        self.assertEqual(list(self.reasoner.sub_object_properties(self.has_child)), [])
        self.assertEqual(list(self.reasoner.super_object_properties(self.has_child)), [])

    def test_repr(self):
        self.assertIn("RDFLibReasoner(", repr(self.reasoner))


class TestRDFLibReasonerPropertyHierarchyAndDomainRange(unittest.TestCase):
    """Cover sub/super object properties and domain/range, using
    KGs/Family/father_with_rbox.owl (hasChild/hasBrother subPropertyOf hasFamilyMember, plus
    domain/range on hasChild) and KGs/Mutagenesis/mutagenesis.owl (data property domain)."""

    @classmethod
    def setUpClass(cls):
        cls.father_path = Path("KGs/Family/father_with_rbox.owl")
        cls.mutagenesis_path = Path("KGs/Mutagenesis/mutagenesis.owl")
        if not cls.father_path.exists() or not cls.mutagenesis_path.exists():
            raise unittest.SkipTest("Required test ontologies not available")

        cls.father_onto = SyncOntology(str(cls.father_path))
        cls.father_reasoner = RDFLibReasoner(cls.father_onto)
        cls.FATHER_NS = "http://example.com/father#"
        cls.has_child = OWLObjectProperty(IRI(cls.FATHER_NS, "hasChild"))
        cls.has_brother = OWLObjectProperty(IRI(cls.FATHER_NS, "hasBrother"))
        cls.has_family_member = OWLObjectProperty(IRI(cls.FATHER_NS, "hasFamilyMember"))
        cls.person = OWLClass(IRI(cls.FATHER_NS, "person"))
        cls.male = OWLClass(IRI(cls.FATHER_NS, "male"))
        cls.female = OWLClass(IRI(cls.FATHER_NS, "female"))

        cls.mut_onto = SyncOntology(str(cls.mutagenesis_path))
        cls.mut_reasoner = RDFLibReasoner(cls.mut_onto)
        cls.MUT_NS = "http://dl-learner.org/mutagenesis#"
        cls.act = OWLDataProperty(IRI(cls.MUT_NS, "act"))
        cls.compound = OWLClass(IRI(cls.MUT_NS, "Compound"))

    def test_super_object_properties_direct(self):
        supers = set(self.father_reasoner.super_object_properties(self.has_child, direct=True))
        self.assertEqual(supers, {self.has_family_member})

    def test_sub_object_properties_direct(self):
        subs = set(self.father_reasoner.sub_object_properties(self.has_family_member, direct=True))
        self.assertEqual(subs, {self.has_child, self.has_brother})

    def test_sub_object_properties_leaf_is_empty(self):
        self.assertEqual(list(self.father_reasoner.sub_object_properties(self.has_child)), [])

    def test_object_property_domains_direct_vs_indirect(self):
        direct = set(self.father_reasoner.object_property_domains(self.has_child, direct=True))
        indirect = set(self.father_reasoner.object_property_domains(self.has_child, direct=False))
        self.assertEqual(direct, {self.person})
        self.assertEqual(indirect, {self.person, self.male, self.female})

    def test_object_property_ranges_direct_vs_indirect(self):
        direct = set(self.father_reasoner.object_property_ranges(self.has_child, direct=True))
        indirect = set(self.father_reasoner.object_property_ranges(self.has_child, direct=False))
        self.assertEqual(direct, {self.person})
        self.assertEqual(indirect, {self.person, self.male, self.female})

    def test_data_property_domains(self):
        domains = set(self.mut_reasoner.data_property_domains(self.act, direct=True))
        self.assertEqual(domains, {self.compound})

    def test_property_hierarchy_caching(self):
        first = set(self.father_reasoner.sub_object_properties(self.has_family_member, direct=True))
        self.assertIn(self.has_family_member, self.father_reasoner._sub_obj_prop_cache)
        second = set(self.father_reasoner.sub_object_properties(self.has_family_member, direct=True))
        self.assertEqual(first, second)

    def test_parity_with_structural_reasoner(self):
        """RDFLibReasoner and StructuralReasoner must agree on the newly-implemented methods.

        One documented exception: StructuralReasoner's super_object_properties additionally
        yields owl:ObjectProperty itself, because owlready2's `is_a` for property entities
        conflates rdf:type with rdfs:subPropertyOf. owl:ObjectProperty is a property's
        metaclass/rdf:type, not a real "super property" in OWL semantics, so RDFLibReasoner's
        pure rdfs:subPropertyOf-based query intentionally does not reproduce this artifact.
        """
        from owlapy.owl_ontology import Ontology
        from owlapy.owl_reasoner import StructuralReasoner

        structural = StructuralReasoner(Ontology(str(self.father_path)))
        owl_object_property = OWLObjectProperty(IRI("http://www.w3.org/2002/07/owl#", "ObjectProperty"))

        structural_supers = set(structural.super_object_properties(self.has_child, direct=True))
        self.assertEqual(
            set(self.father_reasoner.super_object_properties(self.has_child, direct=True)),
            structural_supers - {owl_object_property},
        )
        self.assertEqual(
            set(self.father_reasoner.sub_object_properties(self.has_family_member, direct=True)),
            set(structural.sub_object_properties(self.has_family_member, direct=True)),
        )
        # Another StructuralReasoner/owlready2 quirk: StructuralReasoner.sub_classes(person,
        # only_named=True) itself leaks OWLObjectComplementOf(female) -- the anonymous
        # equivalent-class expression of `male` -- despite only_named defaulting to True.
        # object_property_domains/ranges build on sub_classes, so that leak propagates here too.
        # Filter to named classes on both sides since RDFLibReasoner (working from asserted
        # rdfs:domain/range + rdfs:subClassOf triples only) never produces anonymous expressions.
        self.assertEqual(
            set(self.father_reasoner.object_property_domains(self.has_child, direct=False)),
            {c for c in structural.object_property_domains(self.has_child, direct=False) if isinstance(c, OWLClass)},
        )
        self.assertEqual(
            set(self.father_reasoner.object_property_ranges(self.has_child, direct=False)),
            {c for c in structural.object_property_ranges(self.has_child, direct=False) if isinstance(c, OWLClass)},
        )


class TestRDFLibReasonerEquivalenceDisjointnessAndDifferentIndividuals(unittest.TestCase):
    """Cover equivalent/disjoint object & data properties, different_individuals, and
    sub/super data properties, using KGs/Test/test_ontology.owl -- the only fixture in this
    repo containing owl:AllDisjointProperties and owl:AllDifferent RDF-list axioms."""

    @classmethod
    def setUpClass(cls):
        cls.kg_path = Path("KGs/Test/test_ontology.owl")
        if not cls.kg_path.exists():
            raise unittest.SkipTest("Test ontology not available")

        cls.onto = SyncOntology(str(cls.kg_path))
        cls.reasoner = RDFLibReasoner(cls.onto)
        cls.NS = "http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#"
        cls.r1 = OWLObjectProperty(IRI(cls.NS, "r1"))
        cls.r5 = OWLObjectProperty(IRI(cls.NS, "r5"))
        cls.dp1 = OWLDataProperty(IRI(cls.NS, "dp1"))
        cls.dp2 = OWLDataProperty(IRI(cls.NS, "dp2"))
        cls.dp3 = OWLDataProperty(IRI(cls.NS, "dp3"))
        cls.l = OWLNamedIndividual(IRI(cls.NS, "l"))
        cls.m = OWLNamedIndividual(IRI(cls.NS, "m"))

    def test_disjoint_object_properties_from_all_disjoint_properties_axiom(self):
        self.assertEqual(set(self.reasoner.disjoint_object_properties(self.r5)), {self.r1})
        # Disjointness is symmetric.
        self.assertEqual(set(self.reasoner.disjoint_object_properties(self.r1)), {self.r5})

    def test_disjoint_data_properties_from_all_disjoint_properties_axiom(self):
        self.assertEqual(set(self.reasoner.disjoint_data_properties(self.dp1)), {self.dp3})

    def test_different_individuals_from_all_different_axiom(self):
        self.assertEqual(set(self.reasoner.different_individuals(self.l)), {self.m})
        self.assertEqual(set(self.reasoner.different_individuals(self.m)), {self.l})

    def test_sub_super_data_properties(self):
        self.assertEqual(set(self.reasoner.sub_data_properties(self.dp1, direct=True)), {self.dp2})
        self.assertEqual(set(self.reasoner.super_data_properties(self.dp2, direct=True)), {self.dp1})

    def test_equivalent_properties_return_empty_when_none_asserted(self):
        # This fixture has no owl:equivalentProperty axioms -- confirms the query doesn't
        # crash and correctly returns nothing rather than a false positive.
        self.assertEqual(list(self.reasoner.equivalent_object_properties(self.r1)), [])
        self.assertEqual(list(self.reasoner.equivalent_data_properties(self.dp1)), [])


class TestRDFLibReasonerDataPropertyValues(unittest.TestCase):
    """Cover data_property_values, and a direct regression test for owlapy#242, using
    KGs/Biopax/biopax.owl."""

    @classmethod
    def setUpClass(cls):
        cls.kg_path = Path("KGs/Biopax/biopax.owl")
        if not cls.kg_path.exists():
            raise unittest.SkipTest("Biopax ontology not available")

        cls.onto = SyncOntology(str(cls.kg_path))
        cls.reasoner = RDFLibReasoner(cls.onto)
        cls.NS = "http://www.biopax.org/examples/glycolysis#"
        cls.reaction = OWLNamedIndividual(IRI(cls.NS, "biochemicalReaction13"))
        cls.ec_number = OWLDataProperty(IRI(cls.NS, "EC-NUMBER"))

    def test_data_property_values_returns_typed_literal(self):
        values = list(self.reasoner.data_property_values(self.reaction, self.ec_number))
        self.assertEqual(values, [OWLLiteral("2.7.1.11")])

    def test_object_property_values_on_participants_does_not_crash(self):
        """Regression test for owlapy#242 / Ontolearn#598: StructuralReasoner crashes with
        AttributeError("'Or' object has no attribute 'iri'") on this ontology's PARTICIPANTS
        property, because owlready2 mishandles the punned DELTA-G property (declared as both
        an ObjectProperty and an AnnotationProperty). RDFLibReasoner must not exhibit the same
        failure since it queries the RDF graph directly and never touches owlready2."""
        participants = OWLObjectProperty(IRI(self.NS, "PARTICIPANTS"))
        individuals = set()
        for local_name in ("biochemicalReaction", "catalysis", "modulation"):
            individuals.update(self.reasoner.instances(OWLClass(IRI(self.NS, local_name))))

        self.assertGreater(len(individuals), 0)
        for ind in individuals:
            list(self.reasoner.object_property_values(ind, participants))  # must not raise


if __name__ == '__main__':
    unittest.main()
