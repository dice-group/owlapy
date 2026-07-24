"""Targeted unit tests closing coverage gaps in owlapy.owl_axiom.

This module is a large family of simple, mechanically-similar dataclass-like axiom
types: __eq__ methods that return NotImplemented/False for a different type, __hash__,
__repr__, and a scattering of default marker methods (is_annotated, is_logical_axiom,
is_annotation_axiom) on the abstract bases. No JVM/owlready2 involved -- pure Python
value objects -- so this is exercised directly rather than through an ontology.
"""
import pytest

from owlapy.class_expression import OWLClass, OWLNothing, OWLThing
from owlapy.iri import IRI
from owlapy.owl_axiom import (
    OWLAnnotation,
    OWLAnnotationAssertionAxiom,
    OWLAnnotationProperty,
    OWLAnnotationPropertyDomainAxiom,
    OWLAnnotationPropertyRangeAxiom,
    OWLClassAssertionAxiom,
    OWLDataPropertyAssertionAxiom,
    OWLDataPropertyDomainAxiom,
    OWLDatatypeDefinitionAxiom,
    OWLDeclarationAxiom,
    OWLDifferentIndividualsAxiom,
    OWLDisjointClassesAxiom,
    OWLDisjointObjectPropertiesAxiom,
    OWLDisjointUnionAxiom,
    OWLEquivalentClassesAxiom,
    OWLEquivalentObjectPropertiesAxiom,
    OWLFunctionalObjectPropertyAxiom,
    OWLHasKeyAxiom,
    OWLInverseObjectPropertiesAxiom,
    OWLObjectPropertyAssertionAxiom,
    OWLObjectPropertyDomainAxiom,
    OWLSameIndividualAxiom,
    OWLSubAnnotationPropertyOfAxiom,
    OWLSubClassOfAxiom,
    OWLSubPropertyChainAxiom,
)
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import IntegerOWLDatatype, OWLLiteral, StringOWLDatatype
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty

NS = "http://example.com/axiom_test#"


def cls(name):
    return OWLClass(IRI.create(NS, name))


def ind(name):
    return OWLNamedIndividual(IRI.create(NS, name))


def obj_prop(name):
    return OWLObjectProperty(IRI.create(NS, name))


def data_prop(name):
    return OWLDataProperty(IRI.create(NS, name))


# ---------------------------------------------------------------------------
# Base OWLAxiom / OWLLogicalAxiom / OWLAnnotationAxiom marker methods
# ---------------------------------------------------------------------------

def test_axiom_is_annotated():
    without = OWLDeclarationAxiom(cls("A"))
    assert without.is_annotated() is False

    annotation = OWLAnnotation(OWLAnnotationProperty(IRI.create(NS, "comment")), OWLLiteral("hi"))
    with_annotation = OWLDeclarationAxiom(cls("A"), annotations=[annotation])
    assert with_annotation.is_annotated() is True


def test_logical_axiom_is_logical_axiom_true():
    axiom = OWLSubClassOfAxiom(cls("A"), cls("B"))
    assert axiom.is_logical_axiom() is True


def test_declaration_axiom_is_not_logical_or_annotation_axiom():
    axiom = OWLDeclarationAxiom(cls("A"))
    assert axiom.is_logical_axiom() is False
    assert axiom.is_annotation_axiom() is False


def test_annotation_axiom_is_annotation_axiom_true():
    axiom = OWLAnnotationPropertyDomainAxiom(OWLAnnotationProperty(IRI.create(NS, "comment")), IRI.create(NS, "A"))
    assert axiom.is_annotation_axiom() is True


# ---------------------------------------------------------------------------
# OWLDeclarationAxiom / OWLDatatypeDefinitionAxiom / OWLHasKeyAxiom
# ---------------------------------------------------------------------------

def test_declaration_axiom_eq_hash_repr():
    a = OWLDeclarationAxiom(cls("A"))
    b = OWLDeclarationAxiom(cls("A"))
    c = OWLDeclarationAxiom(cls("B"))
    assert a == b
    assert a != c
    assert (a == "not an axiom") is False
    assert hash(a) == hash(b)
    assert "OWLDeclarationAxiom" in repr(a)


def test_datatype_definition_axiom_eq_hash():
    custom_type = OWLDatatype(IRI.create(NS, "MyType"))
    a = OWLDatatypeDefinitionAxiom(custom_type, StringOWLDatatype)
    b = OWLDatatypeDefinitionAxiom(custom_type, StringOWLDatatype)
    c = OWLDatatypeDefinitionAxiom(custom_type, IntegerOWLDatatype)
    assert a == b
    assert a != c
    assert (a == "not an axiom") is False
    assert hash(a) == hash(b)
    assert "OWLDatatypeDefinitionAxiom" in repr(a)


def test_has_key_axiom_operands_eq_hash():
    prop1, prop2 = obj_prop("p1"), data_prop("p2")
    a = OWLHasKeyAxiom(cls("A"), [prop1, prop2])
    b = OWLHasKeyAxiom(cls("A"), [prop1, prop2])
    c = OWLHasKeyAxiom(cls("A"), [prop1])

    assert set(a.operands()) == {prop1, prop2}
    assert a == b
    assert a != c
    assert a != "not an axiom"
    assert hash(a) == hash(b)
    assert "OWLHasKeyAxiom" in repr(a)


# ---------------------------------------------------------------------------
# OWLNaryClassAxiom family (via OWLEquivalentClassesAxiom / OWLDisjointClassesAxiom)
# ---------------------------------------------------------------------------

def test_nary_class_axiom_as_pairwise_axioms_two_operands_returns_self():
    axiom = OWLEquivalentClassesAxiom([cls("A"), cls("B")])
    pairwise = list(axiom.as_pairwise_axioms())
    assert pairwise == [axiom]


def test_nary_class_axiom_as_pairwise_axioms_three_operands_splits_into_pairs():
    axiom = OWLEquivalentClassesAxiom([cls("A"), cls("B"), cls("C")])
    pairwise = list(axiom.as_pairwise_axioms())
    assert len(pairwise) == 3
    assert all(isinstance(p, OWLEquivalentClassesAxiom) for p in pairwise)
    assert all(len(list(p.class_expressions())) == 2 for p in pairwise)


def test_nary_class_axiom_eq_false_for_different_type():
    axiom = OWLEquivalentClassesAxiom([cls("A"), cls("B")])
    assert (axiom == "not an axiom") is False
    assert axiom != OWLDisjointClassesAxiom([cls("A"), cls("B")])


def test_equivalent_classes_axiom_iter_and_named_classes():
    axiom = OWLEquivalentClassesAxiom([cls("A"), OWLNothing, OWLThing])
    assert set(axiom) == {cls("A"), OWLNothing, OWLThing}
    assert axiom.contains_named_equivalent_class() is True
    # named_classes() filters by isinstance(ce, OWLClass); OWLNothing/OWLThing ARE
    # OWLClass instances (singletons), so they're included alongside cls("A").
    assert set(axiom.named_classes()) == {cls("A"), OWLNothing, OWLThing}


def test_equivalent_classes_axiom_contains_owl_nothing_and_thing_are_broken():
    # NOTE: OWLNothing/OWLThing are singleton *instances* of OWLClass (see
    # class_expression/__init__.py), not classes. contains_owl_nothing()/
    # contains_owl_thing() do `isinstance(ce, OWLNothing)` / `isinstance(ce, OWLThing)`,
    # which is always a TypeError ("arg 2 must be a type") regardless of input --
    # these two methods are unconditionally broken as currently written.
    axiom = OWLEquivalentClassesAxiom([cls("A"), OWLNothing, OWLThing])
    with pytest.raises(TypeError):
        axiom.contains_owl_nothing()
    with pytest.raises(TypeError):
        axiom.contains_owl_thing()


# ---------------------------------------------------------------------------
# OWLNaryIndividualAxiom family (via OWLDifferentIndividualsAxiom / OWLSameIndividualAxiom)
# ---------------------------------------------------------------------------

def test_nary_individual_axiom_as_pairwise_axioms():
    two = OWLDifferentIndividualsAxiom([ind("a"), ind("b")])
    assert list(two.as_pairwise_axioms()) == [two]

    three = OWLDifferentIndividualsAxiom([ind("a"), ind("b"), ind("c")])
    pairwise = list(three.as_pairwise_axioms())
    assert len(pairwise) == 3


def test_nary_individual_axiom_eq_false_for_different_type():
    axiom = OWLDifferentIndividualsAxiom([ind("a"), ind("b")])
    assert (axiom == "not an axiom") is False
    assert axiom != OWLSameIndividualAxiom([ind("a"), ind("b")])


# ---------------------------------------------------------------------------
# OWLNaryPropertyAxiom family (via OWLEquivalentObjectPropertiesAxiom)
# ---------------------------------------------------------------------------

def test_nary_property_axiom_as_pairwise_axioms():
    two = OWLEquivalentObjectPropertiesAxiom([obj_prop("p1"), obj_prop("p2")])
    assert list(two.as_pairwise_axioms()) == [two]

    three = OWLEquivalentObjectPropertiesAxiom([obj_prop("p1"), obj_prop("p2"), obj_prop("p3")])
    assert len(list(three.as_pairwise_axioms())) == 3


def test_nary_property_axiom_eq_hash():
    a = OWLEquivalentObjectPropertiesAxiom([obj_prop("p1"), obj_prop("p2")])
    b = OWLEquivalentObjectPropertiesAxiom([obj_prop("p1"), obj_prop("p2")])
    assert a == b
    assert hash(a) == hash(b)
    assert (a == "not an axiom") is False
    assert a != OWLDisjointObjectPropertiesAxiom([obj_prop("p1"), obj_prop("p2")])


def test_inverse_object_properties_axiom_eq_hash():
    p1, p2 = obj_prop("p1"), obj_prop("p2")
    a = OWLInverseObjectPropertiesAxiom(p1, p2)
    b = OWLInverseObjectPropertiesAxiom(p1, p2)
    c = OWLInverseObjectPropertiesAxiom(p2, p1)
    assert a == b
    assert a != c
    assert (a == "not an axiom") is False
    assert hash(a) == hash(b)


# ---------------------------------------------------------------------------
# OWLSubClassOfAxiom / OWLDisjointUnionAxiom / OWLClassAssertionAxiom
# ---------------------------------------------------------------------------

def test_subclass_of_axiom_properties():
    axiom = OWLSubClassOfAxiom(cls("A"), cls("B"))
    assert axiom.sub_class == cls("A")
    assert axiom.super_class == cls("B")
    assert axiom.get_sub_class() == cls("A")
    assert axiom.get_super_class() == cls("B")


def test_disjoint_union_axiom_get_owl_equivalent_classes_axiom_is_broken():
    # NOTE: get_owl_equivalent_classes_axiom() calls
    # OWLEquivalentClassesAxiom(self._cls, OWLObjectUnionOf(self._class_expressions))
    # -- two positional args -- but OWLEquivalentClassesAxiom.__init__ expects a
    # single `class_expressions: List[...]` (plus optional annotations). Passing a
    # bare OWLClass where a list is expected makes `[*class_expressions]` fail.
    # This method currently always raises TypeError.
    axiom = OWLDisjointUnionAxiom(cls("A"), [cls("B"), cls("C")])
    with pytest.raises(TypeError):
        axiom.get_owl_equivalent_classes_axiom()


def test_disjoint_union_axiom_get_owl_disjoint_classes_axiom():
    axiom = OWLDisjointUnionAxiom(cls("A"), [cls("B"), cls("C")])
    disjoint = axiom.get_owl_disjoint_classes_axiom()
    assert isinstance(disjoint, OWLDisjointClassesAxiom)
    assert set(disjoint.class_expressions()) == {cls("B"), cls("C")}


def test_disjoint_union_axiom_eq_hash():
    axiom = OWLDisjointUnionAxiom(cls("A"), [cls("B"), cls("C")])
    other = OWLDisjointUnionAxiom(cls("A"), [cls("B"), cls("C")])
    assert axiom == other
    assert (axiom == "not an axiom") is False
    assert hash(axiom) == hash(other)


def test_class_assertion_axiom_eq_hash():
    a = OWLClassAssertionAxiom(ind("alice"), cls("A"))
    b = OWLClassAssertionAxiom(ind("alice"), cls("A"))
    assert a == b
    assert (a == "not an axiom") is False
    assert hash(a) == hash(b)


# ---------------------------------------------------------------------------
# OWLAnnotation / OWLAnnotationAssertionAxiom / OWLSubAnnotationPropertyOfAxiom /
# OWLAnnotationPropertyDomainAxiom / OWLAnnotationPropertyRangeAxiom
# ---------------------------------------------------------------------------

def test_annotation_property_str():
    prop = OWLAnnotationProperty(IRI.create(NS, "comment"))
    assert prop.str == NS + "comment"


def test_annotation_eq_hash():
    prop = OWLAnnotationProperty(IRI.create(NS, "comment"))
    a = OWLAnnotation(prop, OWLLiteral("hello"))
    b = OWLAnnotation(prop, OWLLiteral("hello"))
    assert a == b
    assert (a == "not an annotation") is False
    assert hash(a) == hash(b)


def test_annotation_assertion_axiom_eq_hash():
    prop = OWLAnnotationProperty(IRI.create(NS, "comment"))
    annotation = OWLAnnotation(prop, OWLLiteral("hello"))
    a = OWLAnnotationAssertionAxiom(IRI.create(NS, "A"), annotation)
    b = OWLAnnotationAssertionAxiom(IRI.create(NS, "A"), annotation)
    assert a == b
    assert (a == "not an axiom") is False
    assert hash(a) == hash(b)


def test_sub_annotation_property_of_axiom_eq_hash():
    sub = OWLAnnotationProperty(IRI.create(NS, "shortComment"))
    sup = OWLAnnotationProperty(IRI.create(NS, "comment"))
    a = OWLSubAnnotationPropertyOfAxiom(sub, sup)
    b = OWLSubAnnotationPropertyOfAxiom(sub, sup)
    assert a == b
    assert (a == "not an axiom") is False
    assert hash(a) == hash(b)


def test_annotation_property_domain_and_range_axioms_eq_hash():
    prop = OWLAnnotationProperty(IRI.create(NS, "comment"))
    domain_a = OWLAnnotationPropertyDomainAxiom(prop, IRI.create(NS, "A"))
    domain_b = OWLAnnotationPropertyDomainAxiom(prop, IRI.create(NS, "A"))
    assert domain_a == domain_b
    assert (domain_a == "not an axiom") is False
    assert hash(domain_a) == hash(domain_b)

    range_a = OWLAnnotationPropertyRangeAxiom(prop, IRI.create(NS, "A"))
    range_b = OWLAnnotationPropertyRangeAxiom(prop, IRI.create(NS, "A"))
    assert range_a == range_b
    assert (range_a == "not an axiom") is False
    assert hash(range_a) == hash(range_b)


# ---------------------------------------------------------------------------
# OWLPropertyAssertionAxiom family
# ---------------------------------------------------------------------------

def test_object_property_assertion_axiom_eq_false_for_different_type():
    axiom = OWLObjectPropertyAssertionAxiom(ind("alice"), obj_prop("knows"), ind("bob"))
    assert (axiom == "not an axiom") is False


def test_data_property_assertion_axiom_eq_false_for_different_type():
    axiom = OWLDataPropertyAssertionAxiom(ind("alice"), data_prop("age"), OWLLiteral(30))
    assert (axiom == "not an axiom") is False


# ---------------------------------------------------------------------------
# OWLObjectPropertyCharacteristicAxiom / OWLDataPropertyCharacteristicAxiom
# (via OWLFunctionalObjectPropertyAxiom, whose eq/hash live on the shared base)
# ---------------------------------------------------------------------------

def test_functional_object_property_axiom_eq_hash():
    p = obj_prop("hasChild")
    a = OWLFunctionalObjectPropertyAxiom(p)
    b = OWLFunctionalObjectPropertyAxiom(p)
    assert a == b
    assert (a == "not an axiom") is False
    assert hash(a) == hash(b)


# ---------------------------------------------------------------------------
# OWLPropertyDomainAxiom / OWLPropertyRangeAxiom (via Object/Data variants)
# ---------------------------------------------------------------------------

def test_object_property_domain_axiom_prop_property_and_eq():
    p = obj_prop("hasChild")
    a = OWLObjectPropertyDomainAxiom(p, cls("A"))
    b = OWLObjectPropertyDomainAxiom(p, cls("A"))
    assert a.prop == p
    assert a == b
    assert (a == "not an axiom") is False
    assert hash(a) == hash(b)


def test_data_property_domain_axiom_eq_and_range_property():
    p = data_prop("age")
    a = OWLDataPropertyDomainAxiom(p, cls("A"))
    b = OWLDataPropertyDomainAxiom(p, cls("A"))
    assert a == b
    assert (a == "not an axiom") is False
    assert hash(a) == hash(b)

    from owlapy.owl_axiom import OWLDataPropertyRangeAxiom
    range_axiom = OWLDataPropertyRangeAxiom(p, StringOWLDatatype)
    assert range_axiom.prop == p
    assert range_axiom.range == StringOWLDatatype
    assert range_axiom.get_range() == StringOWLDatatype


# ---------------------------------------------------------------------------
# OWLSubPropertyChainAxiom
# ---------------------------------------------------------------------------

def test_sub_property_chain_axiom_eq_false_for_different_type():
    chain = [obj_prop("hasParent"), obj_prop("hasParent")]
    axiom = OWLSubPropertyChainAxiom(chain, obj_prop("hasGrandparent"))
    assert (axiom == "not an axiom") is False
    assert axiom == OWLSubPropertyChainAxiom(chain, obj_prop("hasGrandparent"))
    assert list(axiom.get_property_chain()) == chain
