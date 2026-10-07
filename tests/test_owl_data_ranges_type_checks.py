"""Python-side type-check coverage for owlapy.owl_data_ranges (#271).

OWLNaryDataRange (backing OWLDataIntersectionOf/OWLDataUnionOf) and OWLDataComplementOf
validate their operands against OWLPropertyRange rather than OWLDataRange itself, since
owlapy.utils.nnf.NNF deliberately reuses these constructors to wrap data-side class
expressions (e.g. OWLDataSomeValuesFrom) during negation, not just genuine data ranges.
"""
import pytest

from owlapy.class_expression import OWLDataSomeValuesFrom
from owlapy.iri import IRI
from owlapy.owl_data_ranges import OWLDataComplementOf, OWLDataIntersectionOf, OWLDataUnionOf
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import IntegerOWLDatatype, StringOWLDatatype
from owlapy.owl_property import OWLDataProperty

NS = "http://example.com/data_range_test#"


def data_prop(name):
    return OWLDataProperty(IRI.create(NS, name))


def test_data_intersection_of_rejects_non_property_range_operand():
    with pytest.raises(TypeError):
        OWLDataIntersectionOf((IntegerOWLDatatype, "not a data range"))


def test_data_union_of_rejects_non_property_range_operand():
    with pytest.raises(TypeError):
        OWLDataUnionOf((IntegerOWLDatatype, 42))


def test_data_complement_of_rejects_non_property_range():
    with pytest.raises(TypeError):
        OWLDataComplementOf("not a data range")


def test_data_union_of_accepts_genuine_data_ranges():
    dr = OWLDataUnionOf((IntegerOWLDatatype, StringOWLDatatype))
    assert set(dr.operands()) == {IntegerOWLDatatype, StringOWLDatatype}


def test_data_complement_of_accepts_data_property_restriction_class_expression():
    # NNF deliberately wraps data-property restrictions (OWLClassExpression, not
    # OWLDataRange) in OWLDataComplementOf during negation -- see owlapy.utils.nnf.
    restriction = OWLDataSomeValuesFrom(data_prop("hasAge"), IntegerOWLDatatype)
    complement = OWLDataComplementOf(restriction)
    assert complement.get_data_range() is restriction


def test_data_complement_of_still_rejects_non_owl_object_types():
    with pytest.raises(TypeError):
        OWLDataComplementOf(OWLNamedIndividual(IRI.create(NS, "bob")))
