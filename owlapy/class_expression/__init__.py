""" OWL Class Expressions
https://www.w3.org/TR/owl2-syntax/#Class_Expressions
ClassExpression :=
    owl_class.py:
    Class
    nary_boolean_expression.py:
    ObjectIntersectionOf, ObjectUnionOf
    class_expression.py: ObjectComplementOf

    restriction.py:
    ObjectOneOf, ObjectSomeValuesFrom, ObjectAllValuesFrom, ObjectHasValue,ObjectHasSelf,
    ObjectMinCardinality, ObjectMaxCardinality, ObjectExactCardinality, DataSomeValuesFrom, DataAllValuesFrom,
    DataHasValue, DataMinCardinality, DataMaxCardinality, DataExactCardinality
"""
from .class_expression import OWLAnonymousClassExpression, OWLBooleanClassExpression, OWLClassExpression, OWLObjectComplementOf
from .nary_boolean_expression import OWLNaryBooleanClassExpression, OWLObjectIntersectionOf, OWLObjectUnionOf
from .owl_class import OWLClass
from .restriction import (
                          OWLCardinalityRestriction,
                          OWLDataAllValuesFrom,
                          OWLDataCardinalityRestriction,
                          OWLDataExactCardinality,
                          OWLDataHasValue,
                          OWLDataMaxCardinality,
                          OWLDataMinCardinality,
                          OWLDataOneOf,
                          OWLDataRestriction,
                          OWLDataSomeValuesFrom,
                          OWLDatatypeRestriction,
                          OWLFacet,
                          OWLFacetRestriction,
                          OWLHasValueRestriction,
                          OWLObjectAllValuesFrom,
                          OWLObjectCardinalityRestriction,
                          OWLObjectExactCardinality,
                          OWLObjectHasSelf,
                          OWLObjectHasValue,
                          OWLObjectMaxCardinality,
                          OWLObjectMinCardinality,
                          OWLObjectOneOf,
                          OWLObjectRestriction,
                          OWLObjectSomeValuesFrom,
                          OWLQuantifiedDataRestriction,
                          OWLQuantifiedObjectRestriction,
                          OWLQuantifiedRestriction,
                          OWLRestriction,
)

__all__ = ['OWLClassExpression', 'OWLAnonymousClassExpression', 'OWLBooleanClassExpression', 'OWLObjectComplementOf',
           'OWLNaryBooleanClassExpression', 'OWLObjectUnionOf', 'OWLObjectIntersectionOf', 'OWLRestriction',
           'OWLQuantifiedRestriction', 'OWLObjectCardinalityRestriction', 'OWLObjectHasSelf', 'OWLObjectHasValue',
           'OWLQuantifiedDataRestriction', 'OWLObjectSomeValuesFrom', 'OWLObjectAllValuesFrom',
           'OWLDatatypeRestriction', 'OWLFacet', 'OWLQuantifiedObjectRestriction', 'OWLObjectRestriction',
           'OWLHasValueRestriction', 'OWLDataRestriction', 'OWLCardinalityRestriction', 'OWLFacetRestriction',
           'OWLObjectMinCardinality', 'OWLObjectMaxCardinality', 'OWLObjectExactCardinality', 'OWLDataSomeValuesFrom',
           'OWLDataAllValuesFrom', 'OWLDataHasValue', 'OWLClass', 'OWLDataMinCardinality', 'OWLDataMaxCardinality',
           'OWLDataExactCardinality', 'OWLObjectOneOf', 'OWLDataOneOf', 'OWLDataCardinalityRestriction']

from typing import Final

from ..vocab import OWLRDFVocabulary

OWLThing: Final = OWLClass(OWLRDFVocabulary.OWL_THING.iri)  #: : :The OWL Class corresponding to owl:Thing
OWLNothing: Final = OWLClass(OWLRDFVocabulary.OWL_NOTHING.iri)  #: : :The OWL Class corresponding to owl:Nothing

