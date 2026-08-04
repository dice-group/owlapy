"""Similarity metrics and concept-reduction helpers."""
import concurrent.futures
from typing import Callable, Iterable, Union

from owlapy.class_expression import (
    OWLObjectCardinalityRestriction,
    OWLObjectMaxCardinality,
    OWLObjectMinCardinality,
    OWLQuantifiedObjectRestriction,
)


def jaccard_similarity(set1, set2) -> float:
    """Calculate the Jaccard similarity between two sets.

    Args:
        set1: First set
        set2: Second set

    Returns:
        Jaccard similarity: intersection(set1, set2) / union(set1, set2)
    """
    if len(set1) == 0 and len(set2) == 0:
        return 1.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union


def f1_set_similarity(set1, set2) -> float:
    """Calculate the F1 score between two sets.

    Args:
        set1: First set (treated as ground truth)
        set2: Second set (treated as prediction)

    Returns:
        F1 score
    """
    if len(set1) == 0 and len(set2) == 0:
        return 1.0

    if len(set2) == 0:
        return 0.0

    true_positives = len(set1.intersection(set2))
    precision = true_positives / len(set2) if len(set2) > 0 else 0
    recall = true_positives / len(set1) if len(set1) > 0 else 0

    if precision + recall == 0:
        return 0.0

    return 2 * (precision * recall) / (precision + recall)

def run_with_timeout(func, timeout, args=(), **kwargs):
    # Deliberately not `with ThreadPoolExecutor() as executor:` -- that context manager calls
    # executor.shutdown(wait=True) on exit, which blocks until the submitted task finishes
    # regardless of whether future.result(timeout=...) already timed out, defeating the point
    # of the timeout (the caller would still wait for the full task duration, just get a
    # different return value). shutdown(wait=False) lets this return promptly; the abandoned
    # thread (if any) keeps running in the background -- Python threads cannot be forcibly
    # killed, only abandoned (owlapy#260).
    executor = concurrent.futures.ThreadPoolExecutor()
    future = executor.submit(func, *args, **kwargs)
    try:
        result = future.result(timeout=timeout)
        executor.shutdown(wait=False)
        return result
    except concurrent.futures.TimeoutError:
        executor.shutdown(wait=False)
        return set()


def concept_reducer(concepts:Iterable, opt:Callable):
    """
    Reduces a set of concepts by applying a binary operation to each pair of concepts.

    Args:
        concepts (set): A set of concepts to be reduced.
        opt (function): A binary function that takes a pair of concepts and returns a single concept.

    Returns:
        set: A set containing the results of applying the binary operation to each pair of concepts.

    Example:
        >>> concepts = {1, 2, 3}
        >>> opt = lambda x: x[0] + x[1]
        >>> concept_reducer(concepts, opt)
        {2, 3, 4, 5, 6}

    Note:
        The operation `opt` should be commutative and associative to ensure meaningful reduction in the context of set operations.
    """
    result = set()
    for i in concepts:
        for j in concepts:
            result.add(opt((i, j)))
    return result

def concept_reducer_properties(
        concepts: Iterable, properties, cls: Callable = None, cardinality: int = 2
) -> Iterable[Union[OWLQuantifiedObjectRestriction, OWLObjectCardinalityRestriction]]:
    """
    Map a set of owl concepts and a set of properties into OWL Restrictions

    Args:
        concepts:
        properties:
        cls (Callable): An owl Restriction class
        cardinality: A positive Integer

    Returns: List of OWL Restrictions

    """
    assert isinstance(concepts, Iterable), "Concepts must be an Iterable"
    assert isinstance(properties, Iterable), "properties must be an Iterable"
    assert isinstance(cls, Callable), "cls must be an Callable"
    assert cardinality > 0
    result = set()
    for i in concepts:
        for j in properties:
            if cls == OWLObjectMinCardinality or cls == OWLObjectMaxCardinality:
                result.add(cls(cardinality=cardinality, property=j, filler=i))
                continue
            result.add(cls(j, i))
    return result
