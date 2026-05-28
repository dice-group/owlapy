"""
Regression tests for batch similarity operations (Phase 2).

Tests both Rust (parallel) and Python (sequential) implementations
to ensure correctness and backward compatibility.
"""

import unittest
import time
import random
from typing import List, Tuple, Set

from owlapy.utils import (
    batch_jaccard_similarity,
    batch_f1_set_similarity,
    batch_jaccard_similarity_python,
    batch_f1_set_similarity_python,
    jaccard_similarity,
    f1_set_similarity,
    _RUST_AVAILABLE
)


class TestBatchSimilarityCorrectness(unittest.TestCase):
    """Verify batch operations produce identical results to single operations."""
    
    def test_batch_jaccard_empty_pairs(self):
        """Batch should handle empty list of pairs."""
        pairs = []
        result = batch_jaccard_similarity(pairs)
        self.assertEqual(result, [])
    
    def test_batch_jaccard_single_pair(self):
        """Batch with one pair should match single call."""
        set1 = {"a", "b", "c"}
        set2 = {"b", "c", "d"}
        
        single_result = jaccard_similarity(set1, set2)
        batch_result = batch_jaccard_similarity([(set1, set2)])
        
        self.assertEqual(len(batch_result), 1)
        self.assertAlmostEqual(batch_result[0], single_result, places=10)
    
    def test_batch_jaccard_multiple_pairs(self):
        """Batch should match individual calls for multiple pairs."""
        pairs = [
            ({"a", "b", "c"}, {"b", "c", "d"}),
            ({1, 2, 3, 4}, {3, 4, 5, 6}),
            (set(), set()),
            ({"x"}, {"y"}),
            ({"a", "b"}, {"a", "b"}),
        ]
        
        batch_results = batch_jaccard_similarity(pairs)
        single_results = [jaccard_similarity(s1, s2) for s1, s2 in pairs]
        
        self.assertEqual(len(batch_results), len(pairs))
        for i, (batch_res, single_res) in enumerate(zip(batch_results, single_results)):
            with self.subTest(pair_index=i):
                self.assertAlmostEqual(batch_res, single_res, places=10)
    
    def test_batch_f1_empty_pairs(self):
        """Batch F1 should handle empty list."""
        pairs = []
        result = batch_f1_set_similarity(pairs)
        self.assertEqual(result, [])
    
    def test_batch_f1_single_pair(self):
        """Batch F1 with one pair should match single call."""
        set1 = {"a", "b", "c"}
        set2 = {"b", "c", "d"}
        
        single_result = f1_set_similarity(set1, set2)
        batch_result = batch_f1_set_similarity([(set1, set2)])
        
        self.assertEqual(len(batch_result), 1)
        self.assertAlmostEqual(batch_result[0], single_result, places=10)
    
    def test_batch_f1_multiple_pairs(self):
        """Batch F1 should match individual calls."""
        pairs = [
            ({"a", "b", "c"}, {"b", "c", "d"}),
            ({1, 2, 3}, {2, 3, 4}),
            (set(), set()),
            ({1, 2, 3}, set()),
            (set(), {4, 5, 6}),
            ({"x"}, {"x"}),
        ]
        
        batch_results = batch_f1_set_similarity(pairs)
        single_results = [f1_set_similarity(s1, s2) for s1, s2 in pairs]
        
        self.assertEqual(len(batch_results), len(pairs))
        for i, (batch_res, single_res) in enumerate(zip(batch_results, single_results)):
            with self.subTest(pair_index=i):
                self.assertAlmostEqual(batch_res, single_res, places=10)
    
    def test_batch_jaccard_large_sets(self):
        """Batch should work with large sets."""
        random.seed(42)
        pairs = [
            ({f"item_{i}" for i in range(1000)}, 
             {f"item_{i}" for i in range(500, 1500)})
            for _ in range(10)
        ]
        
        batch_results = batch_jaccard_similarity(pairs)
        single_results = [jaccard_similarity(s1, s2) for s1, s2 in pairs]
        
        self.assertEqual(len(batch_results), len(pairs))
        for batch_res, single_res in zip(batch_results, single_results):
            self.assertAlmostEqual(batch_res, single_res, places=10)
    
    def test_batch_integer_sets(self):
        """Batch should handle integer sets (via str conversion)."""
        pairs = [
            ({1, 2, 3}, {2, 3, 4}),
            ({10, 20, 30}, {30, 40, 50}),
            ({100}, {100}),
        ]
        
        batch_results = batch_jaccard_similarity(pairs)
        
        # Should work without errors
        self.assertEqual(len(batch_results), 3)
        for res in batch_results:
            self.assertGreaterEqual(res, 0.0)
            self.assertLessEqual(res, 1.0)
    
    def test_batch_mixed_types(self):
        """Batch should handle mixed set types (strings, ints, floats)."""
        pairs = [
            ({"a", "b", "c"}, {"b", "c", "d"}),
            ({1, 2, 3}, {2, 3, 4}),
            ({1.5, 2.5}, {2.5, 3.5}),
        ]
        
        batch_results = batch_jaccard_similarity(pairs)
        self.assertEqual(len(batch_results), 3)


@unittest.skipIf(not _RUST_AVAILABLE, reason="Rust extension not available")
class TestBatchRustVsPython(unittest.TestCase):
    """Compare Rust and Python batch implementations for correctness."""
    
    def test_rust_python_agreement_jaccard(self):
        """Rust and Python batch Jaccard should agree."""
        random.seed(42)
        pairs = [
            ({f"item_{i}" for i in range(100)}, 
             {f"item_{i}" for i in range(50, 150)})
            for _ in range(50)
        ]
        
        rust_results = batch_jaccard_similarity(pairs)
        python_results = batch_jaccard_similarity_python(pairs)
        
        self.assertEqual(len(rust_results), len(python_results))
        for i, (rust_res, py_res) in enumerate(zip(rust_results, python_results)):
            with self.subTest(pair_index=i):
                self.assertAlmostEqual(rust_res, py_res, places=10)
    
    def test_rust_python_agreement_f1(self):
        """Rust and Python batch F1 should agree."""
        random.seed(42)
        pairs = [
            ({f"item_{i}" for i in range(100)}, 
             {f"item_{i}" for i in range(50, 150)})
            for _ in range(50)
        ]
        
        rust_results = batch_f1_set_similarity(pairs)
        python_results = batch_f1_set_similarity_python(pairs)
        
        self.assertEqual(len(rust_results), len(python_results))
        for i, (rust_res, py_res) in enumerate(zip(rust_results, python_results)):
            with self.subTest(pair_index=i):
                self.assertAlmostEqual(rust_res, py_res, places=10)


@unittest.skipIf(not _RUST_AVAILABLE, reason="Rust extension not available")
class TestBatchPerformance(unittest.TestCase):
    """Benchmark batch operations (informational, not strict requirements)."""
    
    def test_batch_jaccard_performance(self):
        """BENCHMARK: Compare batch vs sequential Jaccard."""
        random.seed(42)
        # Create 100 pairs of 1000-element sets
        pairs = [
            ({f"item_{i}" for i in range(1000)}, 
             {f"item_{i}" for i in range(500, 1500)})
            for _ in range(100)
        ]
        
        # Sequential (individual calls)
        start = time.time()
        sequential_results = [jaccard_similarity(s1, s2) for s1, s2 in pairs]
        sequential_time = time.time() - start
        
        # Batch (parallel in Rust)
        start = time.time()
        batch_results = batch_jaccard_similarity(pairs)
        batch_time = time.time() - start
        
        speedup = sequential_time / batch_time if batch_time > 0 else 0
        
        print(f"\n📊 Batch Jaccard Performance:")
        print(f"   Sequential: {sequential_time*1000:.2f}ms")
        print(f"   Batch:      {batch_time*1000:.2f}ms")
        print(f"   Speedup:    {speedup:.2f}x")
        
        # Verify correctness
        self.assertEqual(len(sequential_results), len(batch_results))
        for seq, batch in zip(sequential_results, batch_results):
            self.assertAlmostEqual(seq, batch, places=10)
        
        # Batch should not be significantly slower (allow for overhead)
        self.assertGreater(speedup, 0.5, 
            f"Batch should not be >2x slower, got {speedup:.2f}x")
    
    def test_batch_f1_performance(self):
        """BENCHMARK: Compare batch vs sequential F1."""
        random.seed(42)
        pairs = [
            ({f"item_{i}" for i in range(1000)}, 
             {f"item_{i}" for i in range(500, 1500)})
            for _ in range(100)
        ]
        
        # Sequential
        start = time.time()
        sequential_results = [f1_set_similarity(s1, s2) for s1, s2 in pairs]
        sequential_time = time.time() - start
        
        # Batch
        start = time.time()
        batch_results = batch_f1_set_similarity(pairs)
        batch_time = time.time() - start
        
        speedup = sequential_time / batch_time if batch_time > 0 else 0
        
        print(f"\n📊 Batch F1 Performance:")
        print(f"   Sequential: {sequential_time*1000:.2f}ms")
        print(f"   Batch:      {batch_time*1000:.2f}ms")
        print(f"   Speedup:    {speedup:.2f}x")
        
        # Verify correctness
        self.assertEqual(len(sequential_results), len(batch_results))
        for seq, batch in zip(sequential_results, batch_results):
            self.assertAlmostEqual(seq, batch, places=10)


class TestBackwardCompatibility(unittest.TestCase):
    """Ensure Phase 2 doesn't break existing functionality."""
    
    def test_single_functions_still_work(self):
        """Original single-call functions must work unchanged."""
        set1 = {"a", "b", "c"}
        set2 = {"b", "c", "d"}
        
        # These should work exactly as before
        jaccard = jaccard_similarity(set1, set2)
        f1 = f1_set_similarity(set1, set2)
        
        self.assertIsInstance(jaccard, float)
        self.assertIsInstance(f1, float)
        self.assertGreater(jaccard, 0)
        self.assertGreater(f1, 0)
    
    def test_python_fallback_exists(self):
        """Python versions must always be available."""
        # Even if Rust is available, Python versions should exist
        self.assertIsNotNone(batch_jaccard_similarity_python)
        self.assertIsNotNone(batch_f1_set_similarity_python)
        
        pairs = [({"a"}, {"b"})]
        result = batch_jaccard_similarity_python(pairs)
        self.assertEqual(len(result), 1)


if __name__ == '__main__':
    unittest.main()
