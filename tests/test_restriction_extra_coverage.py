"""Targeted unit tests closing coverage gaps in owlapy.class_expression.restriction.

Like owl_axiom.py, this module is a large family of mechanically similar restriction
types whose gaps are almost entirely __eq__ false-branches, __hash__/__repr__, and a
couple of default marker methods (is_data_restriction/is_object_restriction) and
convenience methods (as_intersection_of_min_max). Pure Python, no JVM involved.
"""
import pytest

from owlapy.class_expression import (
    OWLDataAllValuesFrom,
    OWLDataExactCardinality,
    OWLDataHasValue,
    OWLDataMaxCardinality,
    OWLDataMinCardinality,
    OWLDataOneOf,
    OWLDataSomeValuesFrom,
    OWLDatatypeRestriction,
    OWLFacetRestriction,
    OWLObjectAllValuesFrom,
    OWLObjectExactCardinality,
    OWLObjectHasSelf,
    OWLObjectHasValue,
    OWLObjectIntersectionOf,
    OWLObjectMaxCardinality,
    OWLObjectMinCardinality,
    OWLObjectOneOf,
    OWLObjectSomeValuesFrom,
    OWLThing,
)
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import IntegerOWLDatatype, OWLLiteral, StringOWLDatatype
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty
from owlapy.vocab import OWLFacet

NS = "http://example.com/restriction_test#"


def ind(name):
    return OWLNamedIndividual(IRI.create(NS, name))


def obj_prop(name):
    return OWLObjectProperty(IRI.create(NS, name))


def data_prop(name):
    return OWLDataProperty(IRI.create(NS, name))


# ---------------------------------------------------------------------------
# OWLRestriction default markers: is_data_restriction / is_object_restriction
# ---------------------------------------------------------------------------

def test_object_restriction_is_not_a_data_restriction():
    restriction = OWLObjectSomeValuesFrom(obj_prop("hasChild"), OWLObjectOneOf(ind("a")))
    assert restriction.is_object_restriction() is True
    assert restriction.is_data_restriction() is False


def test_data_restriction_is_not_an_object_restriction():
    restriction = OWLDataSomeValuesFrom(data_prop("age"), StringOWLDatatype)
    assert restriction.is_data_restriction() is True
    assert restriction.is_object_restriction() is False


# ---------------------------------------------------------------------------
# OWLHasValueRestriction (via OWLObjectHasValue / OWLDataHasValue)
# ---------------------------------------------------------------------------

def test_object_has_value_eq_hash():
    p = obj_prop("hasChild")
    a = OWLObjectHasValue(p, ind("alice"))
    b = OWLObjectHasValue(p, ind("alice"))
    c = OWLObjectHasValue(p, ind("bob"))
    assert a == b
    assert a != c
    assert (a == "not a restriction") is False
    assert hash(a) == hash(b)


def test_data_has_value_eq_hash():
    p = data_prop("age")
    a = OWLDataHasValue(p, OWLLiteral(30))
    b = OWLDataHasValue(p, OWLLiteral(30))
    assert a == b
    assert (a == "not a restriction") is False
    assert hash(a) == hash(b)


# ---------------------------------------------------------------------------
# Cardinality restrictions: as_intersection_of_min_max, __eq__ false branches
# ---------------------------------------------------------------------------

def test_object_exact_cardinality_as_intersection_of_min_max():
    p, filler = obj_prop("hasChild"), OWLObjectOneOf(ind("a"))
    exact = OWLObjectExactCardinality(2, p, filler)
    result = exact.as_intersection_of_min_max()
    assert isinstance(result, OWLObjectIntersectionOf)
    operands = list(result.operands())
    assert any(isinstance(o, OWLObjectMinCardinality) for o in operands)
    assert any(isinstance(o, OWLObjectMaxCardinality) for o in operands)


def test_data_exact_cardinality_as_intersection_of_min_max():
    p = data_prop("age")
    exact = OWLDataExactCardinality(1, p, StringOWLDatatype)
    result = exact.as_intersection_of_min_max()
    assert isinstance(result, OWLObjectIntersectionOf)
    operands = list(result.operands())
    assert any(isinstance(o, OWLDataMinCardinality) for o in operands)
    assert any(isinstance(o, OWLDataMaxCardinality) for o in operands)


def test_object_cardinality_restriction_eq_false_for_different_type():
    p, filler = obj_prop("hasChild"), OWLObjectOneOf(ind("a"))
    a = OWLObjectMinCardinality(1, p, filler)
    assert (a == "not a restriction") is False
    assert a != OWLObjectMaxCardinality(1, p, filler)


def test_data_cardinality_restriction_eq_false_for_different_type():
    p = data_prop("age")
    a = OWLDataMinCardinality(1, p, StringOWLDatatype)
    assert (a == "not a restriction") is False
    assert a != OWLDataMaxCardinality(1, p, StringOWLDatatype)


# ---------------------------------------------------------------------------
# OWLObjectHasSelf / OWLObjectSomeValuesFrom / OWLDataSomeValuesFrom / OWLDataAllValuesFrom
# ---------------------------------------------------------------------------

def test_object_has_self_eq_false_for_different_type():
    a = OWLObjectHasSelf(obj_prop("hasChild"))
    assert (a == "not a restriction") is False
    assert a == OWLObjectHasSelf(obj_prop("hasChild"))


def test_data_some_values_from_eq_false_for_different_type():
    a = OWLDataSomeValuesFrom(data_prop("age"), StringOWLDatatype)
    assert (a == "not a restriction") is False
    assert a == OWLDataSomeValuesFrom(data_prop("age"), StringOWLDatatype)


def test_data_all_values_from_eq_false_for_different_type():
    a = OWLDataAllValuesFrom(data_prop("age"), StringOWLDatatype)
    assert (a == "not a restriction") is False
    assert a == OWLDataAllValuesFrom(data_prop("age"), StringOWLDatatype)


# ---------------------------------------------------------------------------
# OWLDataOneOf / OWLDatatypeRestriction / OWLFacetRestriction
# ---------------------------------------------------------------------------

def test_data_one_of_eq_false_for_different_type():
    a = OWLDataOneOf([OWLLiteral(1), OWLLiteral(2)])
    assert (a == "not a data range") is False
    assert a == OWLDataOneOf([OWLLiteral(2), OWLLiteral(1)])  # order-insensitive


def test_datatype_restriction_eq_false_for_different_type():
    facet = OWLFacetRestriction(OWLFacet.MIN_INCLUSIVE, OWLLiteral(0))
    a = OWLDatatypeRestriction(IntegerOWLDatatype, facet)
    assert (a == "not a data range") is False
    assert a == OWLDatatypeRestriction(IntegerOWLDatatype, facet)


def test_facet_restriction_eq_false_for_different_type():
    a = OWLFacetRestriction(OWLFacet.MIN_INCLUSIVE, OWLLiteral(0))
    b = OWLFacetRestriction(OWLFacet.MIN_INCLUSIVE, OWLLiteral(0))
    c = OWLFacetRestriction(OWLFacet.MAX_INCLUSIVE, OWLLiteral(0))
    assert a == b
    assert a != c
    assert (a == "not a facet restriction") is False


# ---------------------------------------------------------------------------
# Python-side type checks (owlapy#271): restriction constructors given an
# argument of the wrong OWL construct type must fail immediately with a clear
# TypeError/ValueError, not silently succeed and only blow up once the JVM
# gets involved. These close gaps #272 left in restriction.py -- it fixed
# OWLObjectCardinalityRestriction but missed several parallel constructs.
# ---------------------------------------------------------------------------

def test_object_some_values_from_rejects_data_property():
    with pytest.raises(TypeError):
        OWLObjectSomeValuesFrom(data_prop("age"), OWLThing)


def test_object_some_values_from_rejects_non_class_expression_filler():
    with pytest.raises(TypeError):
        OWLObjectSomeValuesFrom(obj_prop("p"), ind("alice"))


def test_object_all_values_from_rejects_non_class_expression_filler():
    with pytest.raises(TypeError):
        OWLObjectAllValuesFrom(obj_prop("p"), ind("alice"))


def test_object_has_self_rejects_data_property():
    with pytest.raises(TypeError):
        OWLObjectHasSelf(data_prop("age"))


def test_object_has_value_rejects_swapped_arguments():
    with pytest.raises(TypeError):
        OWLObjectHasValue(ind("alice"), obj_prop("p"))


def test_data_some_values_from_rejects_object_property():
    with pytest.raises(TypeError):
        OWLDataSomeValuesFrom(obj_prop("p"), IntegerOWLDatatype)


def test_data_all_values_from_rejects_object_property():
    with pytest.raises(TypeError):
        OWLDataAllValuesFrom(obj_prop("p"), IntegerOWLDatatype)


def test_data_has_value_rejects_non_literal_value():
    with pytest.raises(TypeError):
        OWLDataHasValue(data_prop("age"), ind("alice"))


def test_data_min_cardinality_rejects_object_property():
    with pytest.raises(TypeError):
        OWLDataMinCardinality(1, obj_prop("p"), IntegerOWLDatatype)


def test_data_min_cardinality_rejects_negative_cardinality():
    with pytest.raises(ValueError):
        OWLDataMinCardinality(-1, data_prop("age"), IntegerOWLDatatype)


def test_object_one_of_rejects_non_individual():
    with pytest.raises(TypeError):
        OWLObjectOneOf([ind("alice"), obj_prop("p")])


def test_data_one_of_rejects_non_literal():
    with pytest.raises(TypeError):
        OWLDataOneOf([OWLLiteral(1), ind("alice")])


def test_datatype_restriction_rejects_non_datatype():
    facet = OWLFacetRestriction(OWLFacet.MIN_INCLUSIVE, OWLLiteral(0))
    with pytest.raises(TypeError):
        OWLDatatypeRestriction(ind("alice"), facet)


def test_facet_restriction_rejects_non_facet():
    with pytest.raises(TypeError):
        OWLFacetRestriction("not a facet", OWLLiteral(0))
