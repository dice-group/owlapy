import pytest
from rdflib import OWL, RDF, RDFS, Graph, Literal, Namespace

from owlapy import RDFLibReasoner
from owlapy.class_expression import (
    OWLClass,
    OWLObjectAllValuesFrom,
    OWLObjectComplementOf,
    OWLObjectOneOf,
    OWLObjectSomeValuesFrom,
    OWLThing,
)
from owlapy.owl_axiom import OWLClassAssertionAxiom, OWLDataPropertyAssertionAxiom, OWLObjectPropertyAssertionAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import RDFLibOntology
from owlapy.owl_property import OWLObjectProperty

EX = Namespace("http://example.org/individuals#")


@pytest.fixture
def ontology(tmp_path):
    graph = Graph().parse(data="""
@prefix ex: <http://example.org/individuals#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
ex:ontology a owl:Ontology .
ex:Person a owl:Class ; rdfs:label "Person" ; ex:note ex:schemaReference .
ex:knows a owl:ObjectProperty .
ex:age a owl:DatatypeProperty .
ex:note a owl:AnnotationProperty .
ex:alice a ex:Person ; ex:knows ex:bob ; ex:age 30 ;
    rdfs:label "Alice" ; rdfs:seeAlso ex:reference ; ex:note ex:annotation .
ex:carol ex:score 2 .
ex:dave ex:other ex:erin .
""", format="turtle")
    path = str(tmp_path / "ontology.ttl")
    graph.serialize(path, format="turtle")
    return RDFLibOntology(path)


def test_individual_signature_infers_assertions_and_excludes_annotations(ontology):
    assert {individual.remainder for individual in ontology.individuals_in_signature()} == {
        "alice", "bob", "carol", "dave", "erin",
    }


def test_abox_includes_undeclared_individuals_without_annotations(ontology):
    axioms = list(ontology.get_abox_axioms())
    assert len(axioms) == 5
    assert sum(isinstance(axiom, OWLClassAssertionAxiom) for axiom in axioms) == 1
    assert sum(isinstance(axiom, OWLObjectPropertyAssertionAxiom) for axiom in axioms) == 2
    assert sum(isinstance(axiom, OWLDataPropertyAssertionAxiom) for axiom in axioms) == 2
    assert len(list(ontology.annotation_assertion_axioms(OWLNamedIndividual(str(EX.alice))))) == 3


def test_reasoner_handles_undeclared_and_object_only_individuals(ontology):
    original = set(ontology.rdflib_graph)
    reasoner = RDFLibReasoner(ontology)
    individuals = set(ontology.individuals_in_signature())
    alice, bob = OWLNamedIndividual(str(EX.alice)), OWLNamedIndividual(str(EX.bob))
    person, missing = OWLClass(str(EX.Person)), OWLClass(str(EX.Missing))
    assert set(reasoner.instances(person)) == {alice}
    assert set(reasoner.instances(OWLThing)) == individuals
    assert set(reasoner.instances(OWLObjectOneOf(bob))) == {bob}
    assert set(reasoner.instances(OWLObjectComplementOf(missing))) == individuals
    assert set(reasoner.instances(OWLObjectSomeValuesFrom(
        OWLObjectProperty(str(EX.knows)), OWLObjectComplementOf(missing),
    ))) == {alice}
    assert set(reasoner.instances(OWLObjectAllValuesFrom(OWLObjectProperty(str(EX.unused)), person))) == individuals
    assert set(ontology.rdflib_graph) == original
    assert not list(ontology.rdflib_graph.subjects(RDF.type, OWL.NamedIndividual))


def test_punned_class_is_an_individual_only_when_used_in_an_assertion(tmp_path):
    graph = Graph()
    graph.add((EX.Person, RDF.type, OWL.Class))
    graph.add((EX.Person, RDF.type, EX.MetaClass))
    path = str(tmp_path / "punned.ttl")
    graph.serialize(path, format="turtle")
    ontology = RDFLibOntology(path)
    assert {individual.remainder for individual in ontology.individuals_in_signature()} == {"Person"}
    axioms = list(ontology.get_abox_axioms())
    assert len(axioms) == 1
    assert axioms[0].get_class_expression() == OWLClass(str(EX.MetaClass))


@pytest.mark.parametrize("predicate", [
    RDFS.label, RDFS.comment, RDFS.seeAlso, RDFS.isDefinedBy, OWL.versionInfo,
    OWL.deprecated, OWL.priorVersion, OWL.backwardCompatibleWith, OWL.incompatibleWith, EX.note,
])
def test_annotations_are_not_abox_property_assertions(ontology, predicate):
    ontology.rdflib_graph.add((EX.alice, predicate, Literal("annotation value")))
    axioms = ontology.get_abox_axioms()
    assert all(axiom.get_property().str != str(predicate) for axiom in axioms
               if isinstance(axiom, (OWLDataPropertyAssertionAxiom, OWLObjectPropertyAssertionAxiom)))
