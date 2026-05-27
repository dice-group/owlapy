"""
Regression tests for RDFLibReasoner to ensure Issue #205 fixes remain intact.

These tests verify that:
1. No circular dependencies exist in hierarchy traversal methods
2. All hierarchy operations terminate in reasonable time
3. No duplicate results are returned
4. Performance improvements are maintained
5. The reasoner handles edge cases without hanging
"""
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner_rdflib import RDFLibReasoner


class TestRDFLibReasonerRegressionIssue205(unittest.TestCase):
    """
    Regression tests specifically for Issue #205 fixes.

    Issue #205 identified:
    - Circular dependencies between sub_classes() and super_classes()
    - Inefficient direct subclass retrieval iterating over all classes
    - Missing duplicate protection in direct mode
    """

    @classmethod
    def setUpClass(cls):
        """Set up test ontology."""
        cls.kg_path = Path("KGs/Family/family-benchmark_rich_background.owl")
        if not cls.kg_path.exists():
            raise unittest.SkipTest("Family ontology not available")

        cls.onto = SyncOntology(str(cls.kg_path))
        cls.reasoner = RDFLibReasoner(cls.onto, class_cache=True)

        cls.NS = "http://www.benchmark.org/family#"
        cls.person = OWLClass(IRI(cls.NS, "Person"))
        cls.male = OWLClass(IRI(cls.NS, "Male"))
        cls.father = OWLClass(IRI(cls.NS, "Father"))

    def test_no_circular_dependency_in_subclass_traversal(self):
        """
        REGRESSION: Ensure sub_classes() does NOT call super_classes() during traversal.

        In the original StructuralReasoner (owl_reasoner.py:315), _sub_classes_recursive
        called super_classes, creating circular dependency. This test ensures that
        RDFLibReasoner's _all_subclasses and _direct_subclasses methods are independent.
        """
        # Mock super_classes to detect if it's called during sub_classes traversal
        original_super_classes = self.reasoner.super_classes
        call_count = {'count': 0}

        def tracked_super_classes(*args, **kwargs):
            call_count['count'] += 1
            return original_super_classes(*args, **kwargs)

        with patch.object(self.reasoner, 'super_classes', side_effect=tracked_super_classes):
            # Get all subclasses - should NOT trigger super_classes calls
            _ = list(self.reasoner.sub_classes(self.person, direct=False))

        # Verify super_classes was NOT called during sub_classes traversal
        self.assertEqual(
            call_count['count'],
            0,
            "sub_classes() must NOT call super_classes() - circular dependency detected!"
        )

    def test_no_circular_dependency_in_superclass_traversal(self):
        """
        REGRESSION: Ensure super_classes() does NOT call sub_classes() during traversal.

        In the original StructuralReasoner (owl_reasoner.py:385), _super_classes_recursive
        called sub_classes, creating circular dependency. This test ensures independence.
        """
        # Mock sub_classes to detect if it's called during super_classes traversal
        original_sub_classes = self.reasoner.sub_classes
        call_count = {'count': 0}

        def tracked_sub_classes(*args, **kwargs):
            call_count['count'] += 1
            return original_sub_classes(*args, **kwargs)

        with patch.object(self.reasoner, 'sub_classes', side_effect=tracked_sub_classes):
            # Get all superclasses - should NOT trigger sub_classes calls
            _ = list(self.reasoner.super_classes(self.male, direct=False))

        # Verify sub_classes was NOT called during super_classes traversal
        self.assertEqual(
            call_count['count'],
            0,
            "super_classes() must NOT call sub_classes() - circular dependency detected!"
        )

    def test_direct_subclasses_does_not_iterate_all_classes(self):
        """
        REGRESSION: Ensure direct_subclasses uses SPARQL, not iteration over all classes.

        Original StructuralReasoner (owl_reasoner.py:348) iterated over ALL classes:
            for c in self._ontology.classes_in_signature():

        RDFLibReasoner should use direct SPARQL query instead.
        """
        # Track if classes_in_signature is called (would indicate inefficient approach)
        original_method = self.reasoner._ontology.classes_in_signature
        call_count = {'count': 0}

        def tracked_classes_in_signature():
            call_count['count'] += 1
            return original_method()

        with patch.object(
            self.reasoner._ontology,
            'classes_in_signature',
            side_effect=tracked_classes_in_signature
        ):
            # Get direct subclasses
            _ = list(self.reasoner.sub_classes(self.person, direct=True))

        # Verify we did NOT iterate over all classes
        self.assertEqual(
            call_count['count'],
            0,
            "direct sub_classes() must use SPARQL, not iterate all classes!"
        )

    def test_no_duplicates_in_direct_mode(self):
        """
        REGRESSION: Ensure direct=True mode returns no duplicates.

        Original StructuralReasoner lacked duplicate protection in direct mode.
        """
        # Test direct subclasses
        direct_subs = list(self.reasoner.sub_classes(self.person, direct=True))
        direct_subs_set = set(direct_subs)

        self.assertEqual(
            len(direct_subs),
            len(direct_subs_set),
            f"Direct subclasses contain duplicates: {len(direct_subs)} items, {len(direct_subs_set)} unique"
        )

        # Test direct superclasses
        direct_supers = list(self.reasoner.super_classes(self.male, direct=True))
        direct_supers_set = set(direct_supers)

        self.assertEqual(
            len(direct_supers),
            len(direct_supers_set),
            f"Direct superclasses contain duplicates: {len(direct_supers)} items, {len(direct_supers_set)} unique"
        )

    def test_no_duplicates_in_indirect_mode(self):
        """
        REGRESSION: Ensure direct=False mode returns no duplicates.
        """
        # Test all subclasses
        all_subs = list(self.reasoner.sub_classes(self.person, direct=False))
        all_subs_set = set(all_subs)

        self.assertEqual(
            len(all_subs),
            len(all_subs_set),
            f"All subclasses contain duplicates: {len(all_subs)} items, {len(all_subs_set)} unique"
        )

        # Test all superclasses
        all_supers = list(self.reasoner.super_classes(self.father, direct=False))
        all_supers_set = set(all_supers)

        self.assertEqual(
            len(all_supers),
            len(all_supers_set),
            f"All superclasses contain duplicates: {len(all_supers)} items, {len(all_supers_set)} unique"
        )

    def test_hierarchy_traversal_terminates_quickly(self):
        """
        REGRESSION: Ensure all hierarchy operations complete within reasonable time.

        Circular dependencies could cause infinite recursion or very slow performance.
        All operations should complete in < 5 seconds for Family ontology.
        """
        max_time = 5.0  # seconds

        # Test sub_classes traversal
        start = time.time()
        _ = list(self.reasoner.sub_classes(self.person, direct=False))
        sub_time = time.time() - start

        self.assertLess(
            sub_time,
            max_time,
            f"sub_classes traversal took {sub_time:.2f}s, exceeds {max_time}s limit"
        )

        # Test super_classes traversal
        start = time.time()
        _ = list(self.reasoner.super_classes(self.father, direct=False))
        super_time = time.time() - start

        self.assertLess(
            super_time,
            max_time,
            f"super_classes traversal took {super_time:.2f}s, exceeds {max_time}s limit"
        )

    def test_deep_hierarchy_no_stack_overflow(self):
        """
        REGRESSION: Ensure deep hierarchies don't cause stack overflow.

        RDFLibReasoner uses iterative (not recursive) traversal, so should handle
        arbitrarily deep hierarchies without stack overflow.
        """
        # This should complete without recursion errors
        try:
            all_subs = list(self.reasoner.sub_classes(self.person, direct=False))
            all_supers = list(self.reasoner.super_classes(self.father, direct=False))

            # If we get here, no stack overflow occurred
            self.assertIsInstance(all_subs, list)
            self.assertIsInstance(all_supers, list)
        except RecursionError:
            self.fail("RecursionError occurred - iterative traversal should prevent this!")

    def test_cached_results_are_consistent(self):
        """
        REGRESSION: Ensure caching doesn't introduce inconsistencies.

        Multiple calls with same parameters should return identical results.
        """
        # First call - populates cache
        subs_1 = set(self.reasoner.sub_classes(self.person, direct=True))

        # Second call - uses cache
        subs_2 = set(self.reasoner.sub_classes(self.person, direct=True))

        # Third call - uses cache
        subs_3 = set(self.reasoner.sub_classes(self.person, direct=True))

        self.assertEqual(subs_1, subs_2, "First and second call results differ")
        self.assertEqual(subs_2, subs_3, "Second and third call results differ")
        self.assertEqual(subs_1, subs_3, "First and third call results differ")

    def test_subclass_superclass_symmetry(self):
        """
        REGRESSION: Verify subclass/superclass relationships are symmetric.

        If B is a subclass of A, then A must be a superclass of B.
        This was sometimes violated due to circular dependency issues.
        """
        # Get all direct subclasses of Person
        direct_subs = list(self.reasoner.sub_classes(self.person, direct=True))

        for sub in direct_subs:
            # For each subclass, get its direct superclasses
            supers = set(self.reasoner.super_classes(sub, direct=True))

            # Person should be in the superclasses
            self.assertIn(
                self.person,
                supers,
                f"{sub} is reported as subclass of {self.person}, "
                f"but {self.person} not in superclasses of {sub}"
            )

    def test_performance_cached_vs_uncached(self):
        """
        REGRESSION: Verify that caching provides significant speedup.

        Cached queries should be at least 5x faster than uncached.
        """
        # Warm up
        _ = list(self.reasoner.instances(self.male))

        # Measure cached performance (should be fast)
        start = time.time()
        for _ in range(10):
            _ = list(self.reasoner.instances(self.male))
        cached_time = (time.time() - start) / 10

        # Create new reasoner without cache
        uncached_reasoner = RDFLibReasoner(self.onto, class_cache=False)

        # Measure uncached performance
        start = time.time()
        for _ in range(10):
            _ = list(uncached_reasoner.instances(self.male))
        uncached_time = (time.time() - start) / 10

        # Cached should be significantly faster
        speedup = uncached_time / cached_time if cached_time > 0 else float('inf')

        self.assertGreater(
            speedup,
            5.0,
            f"Cache speedup is only {speedup:.1f}x, expected at least 5x"
        )


class TestRDFLibReasonerEdgeCases(unittest.TestCase):
    """
    Additional regression tests for edge cases that could trigger
    the circular dependency or infinite recursion issues.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test ontology."""
        cls.kg_path = Path("KGs/Family/family-benchmark_rich_background.owl")
        if not cls.kg_path.exists():
            raise unittest.SkipTest("Family ontology not available")

        cls.onto = SyncOntology(str(cls.kg_path))
        cls.reasoner = RDFLibReasoner(cls.onto, class_cache=True)
        cls.NS = "http://www.benchmark.org/family#"

    def test_class_is_not_in_own_subclasses(self):
        """
        REGRESSION: A class should never appear in its own subclasses.

        Circular dependencies could cause this violation.
        """
        person = OWLClass(IRI(self.NS, "Person"))
        all_subs = set(self.reasoner.sub_classes(person, direct=False))

        self.assertNotIn(
            person,
            all_subs,
            "Class appears in its own subclasses - indicates circular reference!"
        )

    def test_class_is_not_in_own_superclasses(self):
        """
        REGRESSION: A class should never appear in its own superclasses.

        Circular dependencies could cause this violation.
        """
        person = OWLClass(IRI(self.NS, "Person"))
        all_supers = set(self.reasoner.super_classes(person, direct=False))

        self.assertNotIn(
            person,
            all_supers,
            "Class appears in its own superclasses - indicates circular reference!"
        )

    def test_empty_subclasses_terminates(self):
        """
        REGRESSION: Getting subclasses of a leaf class should terminate quickly.
        """
        # Grandson is likely a leaf class
        grandson = OWLClass(IRI(self.NS, "Grandson"))

        start = time.time()
        subs = list(self.reasoner.sub_classes(grandson, direct=True))
        elapsed = time.time() - start

        # Should complete almost instantly
        self.assertLess(elapsed, 1.0, f"Empty subclass query took {elapsed:.2f}s")
        self.assertIsInstance(subs, list)

    def test_flush_removes_circular_caches(self):
        """
        REGRESSION: Flushing cache should not break hierarchy traversal.

        After flush, operations should still work correctly.
        """
        person = OWLClass(IRI(self.NS, "Person"))

        # Get results before flush
        subs_before = set(self.reasoner.sub_classes(person, direct=True))

        # Flush cache
        self.reasoner.flush()

        # Get results after flush
        subs_after = set(self.reasoner.sub_classes(person, direct=True))

        # Results should be identical
        self.assertEqual(
            subs_before,
            subs_after,
            "Results differ after cache flush"
        )

    def test_multiple_reasoners_independent(self):
        """
        REGRESSION: Multiple reasoner instances should be independent.

        Ensure no shared state causes interference.
        """
        reasoner1 = RDFLibReasoner(self.onto, class_cache=True)
        reasoner2 = RDFLibReasoner(self.onto, class_cache=True)

        person = OWLClass(IRI(self.NS, "Person"))

        # Get results from both
        subs1 = set(reasoner1.sub_classes(person, direct=True))
        subs2 = set(reasoner2.sub_classes(person, direct=True))

        # Should be identical
        self.assertEqual(subs1, subs2, "Different reasoner instances return different results")

        # Flush one
        reasoner1.flush()

        # The other should still work
        subs2_after = set(reasoner2.sub_classes(person, direct=True))
        self.assertEqual(subs2, subs2_after, "Flushing one reasoner affected another")


class TestRDFLibReasonerPerformanceRegression(unittest.TestCase):
    """
    Performance regression tests to ensure optimizations are maintained.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test ontology."""
        cls.kg_path = Path("KGs/Family/family-benchmark_rich_background.owl")
        if not cls.kg_path.exists():
            raise unittest.SkipTest("Family ontology not available")

        cls.onto = SyncOntology(str(cls.kg_path))

    def test_initialization_time(self):
        """
        REGRESSION: Reasoner initialization should complete in < 5 seconds.
        """
        start = time.time()
        RDFLibReasoner(self.onto, class_cache=True)
        init_time = time.time() - start

        self.assertLess(
            init_time,
            5.0,
            f"Reasoner initialization took {init_time:.2f}s, exceeds 5s limit"
        )

    def test_first_query_reasonable_time(self):
        """
        REGRESSION: First query should complete in < 2 seconds.

        Inefficient SPARQL queries could violate this.
        """
        reasoner = RDFLibReasoner(self.onto, class_cache=True)
        person = OWLClass(IRI("http://www.benchmark.org/family#", "Person"))

        start = time.time()
        _ = list(reasoner.sub_classes(person, direct=True))
        query_time = time.time() - start

        self.assertLess(
            query_time,
            2.0,
            f"First query took {query_time:.2f}s, exceeds 2s limit"
        )

    def test_cached_query_very_fast(self):
        """
        REGRESSION: Cached queries should complete in < 0.01 seconds.
        """
        reasoner = RDFLibReasoner(self.onto, class_cache=True)
        person = OWLClass(IRI("http://www.benchmark.org/family#", "Person"))

        # Warm up cache
        _ = list(reasoner.sub_classes(person, direct=True))

        # Measure cached query
        start = time.time()
        _ = list(reasoner.sub_classes(person, direct=True))
        cached_time = time.time() - start

        self.assertLess(
            cached_time,
            0.01,
            f"Cached query took {cached_time*1000:.2f}ms, exceeds 10ms limit"
        )

    def test_instance_retrieval_scales_linearly(self):
        """
        REGRESSION: Instance retrieval should scale linearly, not quadratically.

        The fix for Issue #205 should prevent O(n²) behavior.
        """
        reasoner = RDFLibReasoner(self.onto, class_cache=False)

        male = OWLClass(IRI("http://www.benchmark.org/family#", "Male"))
        female = OWLClass(IRI("http://www.benchmark.org/family#", "Female"))
        person = OWLClass(IRI("http://www.benchmark.org/family#", "Person"))

        # Measure query times
        times = []
        for cls in [male, female, person]:
            start = time.time()
            instances = list(reasoner.instances(cls))
            query_time = time.time() - start
            times.append((len(instances), query_time))

        # Check that time doesn't grow quadratically
        # If it scales linearly, time ratio should be ~ instance count ratio
        if times[0][0] > 0 and times[2][0] > 0:
            count_ratio = times[2][0] / times[0][0]
            time_ratio = times[2][1] / times[0][1] if times[0][1] > 0 else 1

            # Time ratio should not be much larger than count ratio
            # Allow 3x margin for SPARQL overhead
            self.assertLess(
                time_ratio,
                count_ratio * 3,
                f"Query time scaling appears quadratic: count ratio {count_ratio:.1f}, "
                f"time ratio {time_ratio:.1f}"
            )


if __name__ == '__main__':
    unittest.main()
