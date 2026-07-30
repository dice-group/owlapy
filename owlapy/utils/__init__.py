"""Owlapy utils.

This is a subpackage (not a single module) so that each cohesive group of helpers -
similarity metrics, expression-length calculation, canonical ordering, NNF/CNF/DNF,
syntactic simplification, signature extraction, and the LRU cache - lives in its own
file. Every name previously importable from ``owlapy.utils`` is re-exported here, so
``from owlapy.utils import X`` keeps working unchanged.
"""
from .cache import LRUCache
from .length import OWLClassExpressionLengthMetric, get_expression_length, measurer
from .nnf import NNF, _get_top_level_form, get_top_level_cnf, get_top_level_dnf
from .ordering import (
    ConceptOperandSorter,
    EvaluatedDescriptionSet,
    HasIndex,
    OrderedOWLObject,
    _avoid_overly_redundand_operands,
    _sort_by_ordered_owl_object,
    as_index,
    combine_nary_expressions,
    iter_count,
)
from .signature import SignatureExtractor
from .similarity import concept_reducer, concept_reducer_properties, f1_set_similarity, jaccard_similarity, run_with_timeout
from .simplify import (
    CESimplifier,
    _factor_negation_outof_oneofs,
    factor_nary_expression,
    get_remaining,
    simplify_class_expression,
    transformer,
)

__all__ = [
    'LRUCache',
    'OWLClassExpressionLengthMetric',
    'get_expression_length',
    'measurer',
    'NNF',
    'get_top_level_cnf',
    'get_top_level_dnf',
    '_get_top_level_form',
    'ConceptOperandSorter',
    'EvaluatedDescriptionSet',
    'HasIndex',
    'OrderedOWLObject',
    'as_index',
    'combine_nary_expressions',
    'iter_count',
    '_avoid_overly_redundand_operands',
    '_sort_by_ordered_owl_object',
    'SignatureExtractor',
    'concept_reducer',
    'concept_reducer_properties',
    'f1_set_similarity',
    'jaccard_similarity',
    'run_with_timeout',
    'CESimplifier',
    'factor_nary_expression',
    '_factor_negation_outof_oneofs',
    'get_remaining',
    'simplify_class_expression',
    'transformer',
]
