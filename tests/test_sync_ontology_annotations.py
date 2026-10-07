"""Unit tests for SyncOntology.annotation_assertion_axioms() (#268).

Retrieving an entity's rdfs:label/rdfs:comment (or any other annotation) previously required
either bypassing owlapy's Python abstraction to call the OWLAPI Java object directly, or
loading the ontology a second time with rdflib -- get_tbox_axioms()/get_abox_axioms() never
included annotation assertions, since OWLAPI itself doesn't categorize them as TBox/ABox/RBox.
"""
from rdflib import OWL, RDF, RDFS, Graph, Literal, URIRef

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_ontology import SyncOntology

NS = "http://example.com/sync_annotation_test#"


def _write_ttl(path, graph):
    graph.serialize(destination=path, format="turtle")


def _annotated_ontology_path(tmp_path):
    g = Graph()
    student = URIRef(NS + "Student")
    person = URIRef(NS + "Person")
    g.add((URIRef("http://example.com/sync_annotation_test"), RDF.type, OWL.Ontology))
    g.add((student, RDF.type, OWL.Class))
    g.add((person, RDF.type, OWL.Class))
    g.add((student, RDFS.label, Literal("Student")))
    g.add((student, RDFS.comment, Literal("A person enrolled in a course of study.")))
    g.add((student, RDFS.seeAlso, person))

    path = str(tmp_path / "annotated.ttl")
    _write_ttl(path, g)
    return path


def test_annotation_assertion_axioms_returns_label_and_comment(tmp_path):
    onto = SyncOntology(_annotated_ontology_path(tmp_path))
    axioms = list(onto.annotation_assertion_axioms(OWLClass(NS + "Student")))
    values_by_property = {a.get_property().str: a.get_value() for a in axioms}
    assert values_by_property[str(RDFS.label)] == OWLLiteral("Student")
    assert values_by_property[str(RDFS.comment)] == OWLLiteral("A person enrolled in a course of study.")


def test_annotation_assertion_axioms_iri_valued_annotation(tmp_path):
    onto = SyncOntology(_annotated_ontology_path(tmp_path))
    axioms = list(onto.annotation_assertion_axioms(OWLClass(NS + "Student")))
    see_also = next(a for a in axioms if a.get_property().str == str(RDFS.seeAlso))
    assert see_also.get_value() == IRI.create(NS, "Person")


def test_annotation_assertion_axioms_accepts_iri_directly(tmp_path):
    onto = SyncOntology(_annotated_ontology_path(tmp_path))
    by_entity = list(onto.annotation_assertion_axioms(OWLClass(NS + "Student")))
    by_iri = list(onto.annotation_assertion_axioms(IRI.create(NS, "Student")))
    assert {a.get_property().str for a in by_entity} == {a.get_property().str for a in by_iri}


def test_annotation_assertion_axioms_empty_for_entity_without_annotations(tmp_path):
    onto = SyncOntology(_annotated_ontology_path(tmp_path))
    assert list(onto.annotation_assertion_axioms(OWLClass(NS + "Person"))) == []
