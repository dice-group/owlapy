"""RDFLibOntology.add_axiom()/remove_axiom() for annotation axioms (#310, prerequisite of 1.6).

The OWL API (SyncOntology) reading the saved file is the oracle, as in test_rdflib_write_complex_ce.py.
"""

import pytest
from rdflib import OWL, RDF, URIRef

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_axiom import (
    OWLAnnotation,
    OWLAnnotationAssertionAxiom,
    OWLAnnotationProperty,
    OWLAnnotationPropertyDomainAxiom,
    OWLAnnotationPropertyRangeAxiom,
    OWLClassAssertionAxiom,
    OWLDeclarationAxiom,
    OWLSubAnnotationPropertyOfAxiom,
)
from owlapy.owl_individual import OWLAnonymousIndividual, OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_ontology import RDFLibOntology, SyncOntology
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty

NS = "http://example.com/ann#"
ONTOLOGY_IRI = "http://example.com/ann"
RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#"

LABEL = OWLAnnotationProperty(RDFS_NS + "label")
COMMENT = OWLAnnotationProperty(RDFS_NS + "comment")
NOTE = OWLAnnotationProperty(NS + "note")
PARENT_NOTE = OWLAnnotationProperty(NS + "parentNote")
A = OWLClass(NS + "A")
a = OWLNamedIndividual(NS + "a")
r = OWLObjectProperty(NS + "r")
age = OWLDataProperty(NS + "age")


def _assertion(subject, prop, value):
    return OWLAnnotationAssertionAxiom(subject, OWLAnnotation(prop, value))


ANNOTATION_AXIOMS = {
    "label": _assertion(A.iri, LABEL, OWLLiteral("A class")),
    "comment": _assertion(r.iri, COMMENT, OWLLiteral("an object property")),
    "custom_integer": _assertion(a.iri, NOTE, OWLLiteral(3)),
    "custom_boolean": _assertion(a.iri, NOTE, OWLLiteral(True)),
    "custom_double": _assertion(age.iri, NOTE, OWLLiteral(1.5)),
    "iri_value": _assertion(A.iri, NOTE, IRI.create(NS + "B")),
    "sub_property": OWLSubAnnotationPropertyOfAxiom(NOTE, PARENT_NOTE),
    "domain": OWLAnnotationPropertyDomainAxiom(NOTE, IRI.create(NS + "D")),
    "range": OWLAnnotationPropertyRangeAxiom(NOTE, IRI.create(NS + "R")),
}


def _written(axioms):
    onto = RDFLibOntology(ONTOLOGY_IRI, load=False)
    onto.add_axiom(axioms)
    return onto


def _save(tmp_path, onto, fmt="rdfxml"):
    path = tmp_path / f"out.{'ttl' if fmt == 'ttl' else 'owl'}"
    onto.save(path=str(path), document_format=fmt)
    return str(path)


@pytest.mark.parametrize("axiom", ANNOTATION_AXIOMS.values(), ids=ANNOTATION_AXIOMS.keys())
def test_owlapi_reads_back_what_we_wrote(tmp_path, axiom):
    assert axiom in set(SyncOntology(_save(tmp_path, _written([axiom]))).get_axioms())


def test_turtle_round_trip(tmp_path):
    axioms = list(ANNOTATION_AXIOMS.values())
    assert set(axioms) <= set(SyncOntology(_save(tmp_path, _written(axioms), fmt="ttl")).get_axioms())


@pytest.mark.parametrize("reload", [False, True], ids=["in_memory", "reloaded"])
def test_annotation_assertion_axioms_reads_them_back(tmp_path, reload):
    axioms = [ANNOTATION_AXIOMS[k] for k in ("label", "custom_integer", "custom_boolean", "iri_value")]
    onto = _written(axioms)
    if reload:
        onto = RDFLibOntology(_save(tmp_path, onto))
    assert set(onto.annotation_assertion_axioms(A)) == {ANNOTATION_AXIOMS["label"], ANNOTATION_AXIOMS["iri_value"]}
    assert set(onto.annotation_assertion_axioms(a.iri)) == {ANNOTATION_AXIOMS["custom_integer"], ANNOTATION_AXIOMS["custom_boolean"]}


def test_custom_property_is_declared_and_builtins_are_not(tmp_path):
    onto = _written([ANNOTATION_AXIOMS["label"], ANNOTATION_AXIOMS["sub_property"]])
    graph = onto.rdflib_graph
    assert (URIRef(NOTE.str), RDF.type, OWL.AnnotationProperty) in graph
    assert (URIRef(PARENT_NOTE.str), RDF.type, OWL.AnnotationProperty) in graph
    assert (URIRef(LABEL.str), RDF.type, OWL.AnnotationProperty) not in graph
    declared = {ax for ax in SyncOntology(_save(tmp_path, onto)).get_axioms() if isinstance(ax, OWLDeclarationAxiom)}
    assert declared == {OWLDeclarationAxiom(NOTE), OWLDeclarationAxiom(PARENT_NOTE)}


def test_explicit_declaration_of_builtin_is_kept():
    onto = _written([OWLDeclarationAxiom(LABEL)])
    assert (URIRef(LABEL.str), RDF.type, OWL.AnnotationProperty) in onto.rdflib_graph


def test_annotations_are_not_abox_axioms_or_individuals(tmp_path):
    # Without the owl:AnnotationProperty declaration, `a note 3` would read back as a data property assertion.
    axioms = [OWLClassAssertionAxiom(a, A), ANNOTATION_AXIOMS["label"], ANNOTATION_AXIOMS["custom_integer"],
              ANNOTATION_AXIOMS["iri_value"], ANNOTATION_AXIOMS["comment"]]
    for onto in (_written(axioms), RDFLibOntology(_save(tmp_path, _written(axioms)))):
        assert onto.get_abox_axioms() == [OWLClassAssertionAxiom(a, A)]
        assert set(onto.individuals_in_signature()) == {a}
        assert not list(onto.data_properties_in_signature())


@pytest.mark.parametrize("axiom", ANNOTATION_AXIOMS.values(), ids=ANNOTATION_AXIOMS.keys())
def test_remove_axiom(tmp_path, axiom):
    onto = _written([axiom])
    onto.remove_axiom(axiom)
    assert axiom not in set(SyncOntology(_save(tmp_path, onto)).get_axioms())


def test_remove_annotation_property_declaration():
    onto = _written([ANNOTATION_AXIOMS["custom_integer"]])
    onto.remove_axiom(OWLDeclarationAxiom(NOTE))
    assert (URIRef(NOTE.str), RDF.type, OWL.AnnotationProperty) not in onto.rdflib_graph
    assert NOTE.str not in onto.str_owl_annotation_properties


@pytest.mark.parametrize("axiom", [
    _assertion(OWLAnonymousIndividual("x"), LABEL, OWLLiteral("anon")),
    _assertion(A.iri, NOTE, OWLAnonymousIndividual("y")),
], ids=["anonymous_subject", "anonymous_value"])
def test_anonymous_individuals_raise_without_side_effects(axiom):
    onto = RDFLibOntology(ONTOLOGY_IRI, load=False)
    before = set(onto.rdflib_graph)
    with pytest.raises(NotImplementedError, match="anonymous individuals"):
        onto.add_axiom(axiom)
    assert set(onto.rdflib_graph) == before
    with pytest.raises(NotImplementedError, match="anonymous individuals"):
        onto.remove_axiom(axiom)
