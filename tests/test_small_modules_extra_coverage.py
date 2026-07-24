"""Targeted unit tests closing small remaining coverage gaps in a handful of
self-contained, low-risk modules: owl_property.py, namespaces.py, owl_annotation.py,
owl_object.py, vocab.py (OWLFacet.from_str), providers.py, and iri.py.

Each of these modules is tiny and pure-Python (no JVM/owlready2 involved), so the
gaps are almost entirely default/marker methods on abstract base classes and a
couple of numeric-coercion branches -- straightforward to exercise directly.
"""
import pytest

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.namespaces import Namespaces
from owlapy.owl_individual import OWLAnonymousIndividual
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty
from owlapy.providers import (
    owl_datatype_min_max_exclusive_restriction,
    owl_datatype_min_max_inclusive_restriction,
)
from owlapy.vocab import OWLFacet

NS = "http://example.com/test#"


# ---------------------------------------------------------------------------
# owl_property.py: default marker methods on the abstract property hierarchy
# ---------------------------------------------------------------------------

def test_object_property_expression_defaults():
    op = OWLObjectProperty(IRI.create(NS, "hasChild"))
    assert op.is_data_property_expression() is False
    assert op.is_owl_top_data_property() is False
    assert op.is_object_property_expression() is True


def test_data_property_expression_defaults():
    dp = OWLDataProperty(IRI.create(NS, "age"))
    assert dp.is_object_property_expression() is False
    assert dp.is_owl_top_object_property() is False
    assert dp.is_data_property_expression() is True


def test_object_property_is_owl_top_object_property():
    top = OWLObjectProperty(IRI.create("http://www.w3.org/2002/07/owl#", "topObjectProperty"))
    assert top.is_owl_top_object_property() is True
    non_top = OWLObjectProperty(IRI.create(NS, "hasChild"))
    assert non_top.is_owl_top_object_property() is False


def test_data_property_is_owl_top_data_property():
    top = OWLDataProperty(IRI.create("http://www.w3.org/2002/07/owl#", "topDataProperty"))
    assert top.is_owl_top_data_property() is True


def test_data_property_repr_eq_hash():
    a = OWLDataProperty(IRI.create(NS, "age"))
    b = OWLDataProperty(IRI.create(NS, "age"))
    c = OWLDataProperty(IRI.create(NS, "name"))
    assert repr(a) == f"OWLDataProperty({repr(a.iri)})"
    assert a == b
    assert a != c
    assert a != "not a property"
    assert hash(a) == hash(b)


def test_object_inverse_of_get_inverse_property_and_named_property():
    from owlapy.owl_property import OWLObjectInverseOf

    prop = OWLObjectProperty(IRI.create(NS, "hasChild"))
    inv = OWLObjectInverseOf(prop)
    assert inv.get_inverse() == prop
    assert inv.get_inverse_property() == prop
    assert inv.get_named_property() == prop
    assert repr(inv) == f"OWLObjectInverseOf({repr(prop)})"
    assert inv == OWLObjectInverseOf(prop)
    assert inv != OWLObjectInverseOf(OWLObjectProperty(IRI.create(NS, "other")))
    assert inv != "not an inverse"
    assert hash(inv) == hash(OWLObjectInverseOf(prop))


# ---------------------------------------------------------------------------
# namespaces.py
# ---------------------------------------------------------------------------

def test_namespaces_hash_and_equality_variants():
    ns_a = Namespaces("ex", "http://example.com/")
    ns_b = Namespaces("ex", "http://example.com/")
    ns_c = Namespaces("ex2", "http://example.org/")

    assert hash(ns_a) == hash(("ex", "http://example.com/"))
    assert ns_a == ns_b
    assert ns_a != ns_c
    # Equality against a plain string compares the namespace URI directly.
    assert ns_a == "http://example.com/"
    assert ns_a != "http://other.com/"
    # Equality against an unrelated type falls through to False.
    assert (ns_a == 42) is False


# ---------------------------------------------------------------------------
# owl_annotation.py: default marker methods, reached via concrete subclasses
# that only override one of the four (IRI overrides as_iri; OWLAnonymousIndividual
# overrides as_anonymous_individual).
# ---------------------------------------------------------------------------

def test_iri_default_annotation_object_methods():
    iri = IRI.create(NS, "Something")
    assert iri.as_anonymous_individual() is None
    assert iri.is_literal() is False
    assert iri.as_literal() is None
    # Overridden on IRI itself.
    assert iri.as_iri() is iri


def test_anonymous_individual_default_annotation_object_methods():
    anon = OWLAnonymousIndividual("_:b0")
    assert anon.as_iri() is None
    assert anon.is_literal() is False
    assert anon.as_literal() is None
    # Overridden on OWLAnonymousIndividual itself.
    assert anon.as_anonymous_individual() is anon


# ---------------------------------------------------------------------------
# owl_object.py: OWLNamedObject.__lt__ (inherited by concrete entities like OWLClass)
# ---------------------------------------------------------------------------

def test_named_object_ordering():
    a = OWLClass(IRI.create(NS, "Alpha"))
    b = OWLClass(IRI.create(NS, "Beta"))
    assert a < b
    assert not (b < a)


def test_named_object_ordering_against_unrelated_type_raises_type_error():
    a = OWLClass(IRI.create(NS, "Alpha"))
    with pytest.raises(TypeError):
        _ = a < "not an owl object"


# ---------------------------------------------------------------------------
# vocab.py: OWLFacet.from_str
# ---------------------------------------------------------------------------

def test_owl_facet_from_str_valid():
    assert OWLFacet.from_str(">=") == OWLFacet.MIN_INCLUSIVE


def test_owl_facet_from_str_invalid_raises_value_error():
    with pytest.raises(ValueError):
        OWLFacet.from_str("not-a-real-facet-symbol")


# ---------------------------------------------------------------------------
# providers.py: int -> float coercion branches in the min/max restriction helpers
# ---------------------------------------------------------------------------

def test_min_max_exclusive_restriction_coerces_int_min_to_float():
    restriction = owl_datatype_min_max_exclusive_restriction(1, 2.5)
    facets = {fr.get_facet(): fr.get_facet_value().parse_double() for fr in restriction.get_facet_restrictions()}
    assert facets[OWLFacet.MIN_EXCLUSIVE] == 1.0
    assert facets[OWLFacet.MAX_EXCLUSIVE] == 2.5


def test_min_max_inclusive_restriction_coerces_int_min_to_float():
    restriction = owl_datatype_min_max_inclusive_restriction(1, 2.5)
    facets = {fr.get_facet(): fr.get_facet_value().parse_double() for fr in restriction.get_facet_restrictions()}
    assert facets[OWLFacet.MIN_INCLUSIVE] == 1.0
    assert facets[OWLFacet.MAX_INCLUSIVE] == 2.5


# ---------------------------------------------------------------------------
# iri.py: IRI.create branches not hit elsewhere (is_file_path, reserved
# vocabulary check, as_iri)
# ---------------------------------------------------------------------------

def test_iri_create_with_is_file_path():
    iri = IRI.create("/home/user/ontology.owl", is_file_path=True)
    assert iri.as_str() == "/home/user/ontology.owl"


def test_iri_is_reserved_vocabulary():
    owl_iri = IRI.create("http://www.w3.org/2002/07/owl#", "Thing")
    assert owl_iri.is_reserved_vocabulary() is True

    custom_iri = IRI.create(NS, "Something")
    assert custom_iri.is_reserved_vocabulary() is False


def test_iri_as_iri_returns_self():
    iri = IRI.create(NS, "Something")
    assert iri.as_iri() is iri
