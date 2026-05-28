#!/usr/bin/env python3
"""
Example demonstrating Phase 2: Batch Similarity Operations

Shows how batch operations can be used in real-world scenarios
like retrieval evaluation and concept learning.
"""

import time
import random
from owlapy.utils import (
    jaccard_similarity,
    f1_set_similarity,
    batch_jaccard_similarity,
    batch_f1_set_similarity,
    _RUST_AVAILABLE
)


def example_retrieval_evaluation():
    """
    Scenario: Evaluating retrieval quality across multiple queries.
    
    In concept learning, you often need to compare predicted instances
    against ground truth for many different class expressions.
    """
    print("=" * 80)
    print("Example: Retrieval Evaluation")
    print("=" * 80)
    
    # Simulate 100 different class expressions
    random.seed(42)
    num_queries = 100
    
    # Ground truth and predictions for each query
    pairs = []
    for i in range(num_queries):
        # Ground truth: random set of instances
        ground_truth = {f"instance_{j}" for j in random.sample(range(1000), 50)}
        # Prediction: somewhat overlapping set
        prediction = {f"instance_{j}" for j in random.sample(range(1000), 50)}
        pairs.append((ground_truth, prediction))
    
    print(f"Evaluating {num_queries} retrievals...")
    
    # Method 1: Sequential (traditional approach)
    start = time.time()
    f1_scores_sequential = [f1_set_similarity(gt, pred) for gt, pred in pairs]
    sequential_time = time.time() - start
    
    # Method 2: Batch (Phase 2)
    start = time.time()
    f1_scores_batch = batch_f1_set_similarity(pairs)
    batch_time = time.time() - start
    
    # Calculate average F1 score
    avg_f1 = sum(f1_scores_batch) / len(f1_scores_batch)
    
    print(f"\n✓ Average F1 Score: {avg_f1:.4f}")
    print(f"✓ Sequential time: {sequential_time*1000:.2f}ms")
    print(f"✓ Batch time: {batch_time*1000:.2f}ms")
    print(f"✓ Speedup: {sequential_time/batch_time:.2f}x")
    print(f"✓ Rust available: {_RUST_AVAILABLE}")


def example_concept_similarity_matrix():
    """
    Scenario: Computing similarity matrix for concept clustering.
    
    When learning concept hierarchies, you need to compute pairwise
    similarities between all concepts.
    """
    print("\n" + "=" * 80)
    print("Example: Concept Similarity Matrix")
    print("=" * 80)
    
    # Simulate 50 concepts (each represented by their instances)
    random.seed(42)
    concepts = []
    for i in range(50):
        instances = {f"ind_{j}" for j in random.sample(range(500), random.randint(10, 100))}
        concepts.append(instances)
    
    # Create all pairs for similarity matrix
    pairs = []
    for i in range(len(concepts)):
        for j in range(i, len(concepts)):  # Upper triangle only
            pairs.append((concepts[i], concepts[j]))
    
    print(f"Computing {len(pairs)} pairwise similarities...")
    
    # Batch computation
    start = time.time()
    similarities = batch_jaccard_similarity(pairs)
    batch_time = time.time() - start
    
    # Find most similar concepts
    max_similarity = 0
    max_pair = (0, 0)
    idx = 0
    for i in range(len(concepts)):
        for j in range(i, len(concepts)):
            if i != j and similarities[idx] > max_similarity:
                max_similarity = similarities[idx]
                max_pair = (i, j)
            idx += 1
    
    print(f"\n✓ Computed {len(pairs)} similarities in {batch_time*1000:.2f}ms")
    print(f"✓ Most similar concepts: {max_pair[0]} and {max_pair[1]} (similarity: {max_similarity:.4f})")


def example_incremental_vs_batch():
    """
    Show the difference between incremental and batch processing.
    """
    print("\n" + "=" * 80)
    print("Example: Incremental vs Batch Processing")
    print("=" * 80)
    
    random.seed(42)
    
    # Simulate a concept learning algorithm that needs to evaluate
    # candidate refinements iteratively
    base_set = {f"item_{i}" for i in range(100)}
    candidates = [
        {f"item_{i}" for i in random.sample(range(100), 30)}
        for _ in range(20)
    ]
    
    print("Scenario: Evaluating 20 concept refinements against base concept")
    
    # Incremental approach (typical in concept learning)
    print("\nIncremental (one-by-one):")
    start = time.time()
    for i, candidate in enumerate(candidates):
        similarity = jaccard_similarity(base_set, candidate)
        if i < 3:  # Show first 3
            print(f"  Candidate {i}: similarity = {similarity:.4f}")
    incremental_time = time.time() - start
    print(f"  ... (17 more)")
    print(f"  Total time: {incremental_time*1000:.2f}ms")
    
    # Batch approach (Phase 2)
    print("\nBatch (all at once):")
    pairs = [(base_set, candidate) for candidate in candidates]
    start = time.time()
    similarities = batch_jaccard_similarity(pairs)
    batch_time = time.time() - start
    
    for i, sim in enumerate(similarities[:3]):
        print(f"  Candidate {i}: similarity = {sim:.4f}")
    print(f"  ... (17 more)")
    print(f"  Total time: {batch_time*1000:.2f}ms")
    print(f"\n✓ Speedup: {incremental_time/batch_time:.2f}x")


def main():
    print("\n" + "=" * 80)
    print("OWLAPY Phase 2: Batch Similarity Operations")
    print("=" * 80)
    print(f"Rust available: {_RUST_AVAILABLE}")
    print("=" * 80)
    
    # Run examples
    example_retrieval_evaluation()
    example_concept_similarity_matrix()
    example_incremental_vs_batch()
    
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print("""
Batch operations are particularly useful for:
1. Retrieval evaluation across multiple queries
2. Computing similarity matrices for concept clustering
3. Parallel hypothesis evaluation in concept learning
4. Large-scale knowledge graph comparison

Key advantages:
✓ Backward compatible - existing code works unchanged
✓ Graceful fallback - works without Rust (just slower)
✓ Parallel processing - uses all CPU cores with Rust+rayon
✓ Type-safe - same input validation as single operations
    """)


if __name__ == "__main__":
    main()
