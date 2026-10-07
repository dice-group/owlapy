import pytest

from owlapy.class_expression import OWLClass
from owlapy.owl_axiom import (
    OWLAnnotation,
    OWLAnnotationProperty,
    OWLDifferentIndividualsAxiom,
    OWLDisjointClassesAxiom,
    OWLDisjointDataPropertiesAxiom,
    OWLDisjointObjectPropertiesAxiom,
    OWLDisjointUnionAxiom,
    OWLEquivalentClassesAxiom,
    OWLEquivalentDataPropertiesAxiom,
    OWLEquivalentObjectPropertiesAxiom,
    OWLHasKeyAxiom,
    OWLSameIndividualAxiom,
)
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty


@pytest.mark.parametrize("factory, operand_type", [
    (OWLEquivalentClassesAxiom, OWLClass), (OWLDisjointClassesAxiom, OWLClass),
    (OWLDifferentIndividualsAxiom, OWLNamedIndividual), (OWLSameIndividualAxiom, OWLNamedIndividual),
    (OWLEquivalentObjectPropertiesAxiom, OWLObjectProperty), (OWLDisjointObjectPropertiesAxiom, OWLObjectProperty),
    (OWLEquivalentDataPropertiesAxiom, OWLDataProperty), (OWLDisjointDataPropertiesAxiom, OWLDataProperty),
    (lambda operands, **kwargs: OWLHasKeyAxiom(OWLClass("http://example.org/C"), operands, **kwargs), OWLObjectProperty),
])
@pytest.mark.parametrize("duplicate_annotation", [False, True])
def test_reordered_axioms_and_annotations_work_as_dictionary_keys(factory, operand_type, duplicate_annotation):
    a, b = operand_type("http://example.org/a"), operand_type("http://example.org/b")
    prop = OWLAnnotationProperty("http://example.org/comment")
    first, second = OWLAnnotation(prop, OWLLiteral("first")), OWLAnnotation(prop, OWLLiteral("second"))
    left = factory([a, b], annotations=[first, second, first] if duplicate_annotation else [first, second])
    right = factory([b, a], annotations=[second, first])
    assert left == right
    assert len({left, right}) == 1
    assert {left: "cached"}[right] == "cached"


def test_reordered_disjoint_union_axioms_share_hashes():
    a, b, c = (OWLClass(f"http://example.org/{name}") for name in ("A", "B", "C"))
    left, right = OWLDisjointUnionAxiom(a, [b, c]), OWLDisjointUnionAxiom(a, [c, b])
    assert left == right
    assert {left: "cached"}[right] == "cached"
