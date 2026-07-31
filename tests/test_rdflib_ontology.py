"""Unit tests for owlapy.owl_ontology.RDFLibOntology.

RDFLibOntology is a lightweight, pure-rdflib triple reader: it only understands
axioms expressed directly between *named* entities (classes, individuals,
properties). Anything that would require reconstructing a complex class
expression from blank-node RDF structures (owl:Restriction,
owl:intersectionOf, ...) is out of scope and `general_class_axioms()` raises
`NotImplementedError` to say so explicitly, matching `get_tbox_axioms()`,
which likewise skips blank-node operands. The write API (`add_axiom`,
`remove_axiom`, `save`) is a separate, still-unimplemented piece of work.
"""

import pytest
import rdflib
from rdflib import OWL, RDF, RDFS, XSD, Graph, Literal, URIRef

from owlapy.class_expression import OWLClass
from owlapy.owl_axiom import (
    OWLClassAssertionAxiom,
    OWLDataPropertyAssertionAxiom,
    OWLDataPropertyDomainAxiom,
    OWLDataPropertyRangeAxiom,
    OWLDeclarationAxiom,
    OWLDisjointClassesAxiom,
    OWLEquivalentClassesAxiom,
    OWLObjectPropertyAssertionAxiom,
    OWLObjectPropertyDomainAxiom,
    OWLObjectPropertyRangeAxiom,
    OWLSubClassOfAxiom,
)
from owlapy.owl_ontology import RDFLibOntology
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty

NS = "http://example.com/rdflib_onto#"
ONTOLOGY_IRI = "http://example.com/rdflib_onto"


def _write_graph(path: str, graph: Graph):
    graph.serialize(destination=path, format="xml")


@pytest.fixture
def basic_kg_path(tmp_path):
    """Person subClassOf Agent, Person equivalentClass Human, Person disjointWith Robot,
    knows/age with domain+range, alice a Person with alice knows bob and alice age 30.
    Person also carries an rdfs:comment annotation, to make sure tbox extraction doesn't
    trip over predicates that aren't TBox structure."""
    g = Graph()
    ontology = URIRef(ONTOLOGY_IRI)
    person = URIRef(NS + "Person")
    agent = URIRef(NS + "Agent")
    human = URIRef(NS + "Human")
    robot = URIRef(NS + "Robot")
    alice = URIRef(NS + "alice")
    bob = URIRef(NS + "bob")
    knows = URIRef(NS + "knows")
    age = URIRef(NS + "age")

    g.add((ontology, RDF.type, OWL.Ontology))

    g.add((person, RDF.type, OWL.Class))
    g.add((agent, RDF.type, OWL.Class))
    g.add((human, RDF.type, OWL.Class))
    g.add((robot, RDF.type, OWL.Class))
    g.add((person, RDFS.subClassOf, agent))
    g.add((person, OWL.equivalentClass, human))
    g.add((person, OWL.disjointWith, robot))
    g.add((person, RDFS.comment, Literal("A person is an Agent.")))

    g.add((knows, RDF.type, OWL.ObjectProperty))
    g.add((knows, RDFS.domain, person))
    g.add((knows, RDFS.range, agent))

    g.add((age, RDF.type, OWL.DatatypeProperty))
    g.add((age, RDFS.domain, person))
    g.add((age, RDFS.range, XSD.integer))

    g.add((alice, RDF.type, OWL.NamedIndividual))
    g.add((alice, RDF.type, person))
    g.add((bob, RDF.type, OWL.NamedIndividual))
    g.add((alice, knows, bob))
    g.add((alice, age, Literal(30)))

    path = str(tmp_path / "basic.owl")
    _write_graph(path, g)
    return path


@pytest.fixture
def undeclared_type_kg_path(tmp_path):
    """An individual asserted to be of an rdf:type that is neither a declared owl:Class nor
    owl:NamedIndividual (e.g. only ever referenced as a class via this one triple) -- valid OWL
    (class membership doesn't require an independent `C rdf:type owl:Class` declaration), so
    get_abox_axioms() must still produce a class assertion for it rather than crashing."""
    g = Graph()
    alice = URIRef(NS + "alice")
    undeclared = URIRef(NS + "SomethingUndeclared")
    g.add((alice, RDF.type, OWL.NamedIndividual))
    g.add((alice, RDF.type, undeclared))

    path = str(tmp_path / "undeclared_type.owl")
    _write_graph(path, g)
    return path


@pytest.fixture
def undeclared_individual_target_kg_path(tmp_path):
    """An object-property assertion whose target individual is never independently declared
    `rdf:type owl:NamedIndividual` -- also valid OWL, so it must still be picked up as an
    object-property assertion rather than crashing."""
    g = Graph()
    alice = URIRef(NS + "alice")
    bob = URIRef(NS + "bob")
    knows = URIRef(NS + "knows")
    g.add((alice, RDF.type, OWL.NamedIndividual))
    g.add((alice, knows, bob))

    path = str(tmp_path / "undeclared_individual_target.owl")
    _write_graph(path, g)
    return path


def test_construction_without_load_raises_not_implemented(tmp_path):
    with pytest.raises(NotImplementedError):
        RDFLibOntology(str(tmp_path / "nonexistent.owl"), load=False)


def test_construction_requires_existing_path(tmp_path):
    with pytest.raises(AssertionError):
        RDFLibOntology(str(tmp_path / "does_not_exist.owl"), load=True)


def test_len_returns_number_of_triples(basic_kg_path):
    onto = RDFLibOntology(basic_kg_path)
    assert len(onto) == len(rdflib.Graph().parse(basic_kg_path))
    assert len(onto) > 0


def test_get_tbox_axioms_subclass_and_equivalent(basic_kg_path):
    onto = RDFLibOntology(basic_kg_path)
    axioms = onto.get_tbox_axioms()

    sub_class_axioms = [a for a in axioms if isinstance(a, OWLSubClassOfAxiom)]
    equiv_axioms = [a for a in axioms if isinstance(a, OWLEquivalentClassesAxiom)]

    assert any(a.get_sub_class().str == NS + "Person" and a.get_super_class().str == NS + "Agent"
               for a in sub_class_axioms)
    assert len(equiv_axioms) >= 1


def test_get_tbox_axioms_declarations(basic_kg_path):
    onto = RDFLibOntology(basic_kg_path)
    declarations = [a for a in onto.get_tbox_axioms() if isinstance(a, OWLDeclarationAxiom)]
    declared = {a.get_entity().str for a in declarations}
    assert declared == {NS + "Person", NS + "Agent", NS + "Human", NS + "Robot"}


def test_get_tbox_axioms_disjoint_classes(basic_kg_path):
    onto = RDFLibOntology(basic_kg_path)
    disjoint_axioms = [a for a in onto.get_tbox_axioms() if isinstance(a, OWLDisjointClassesAxiom)]
    assert len(disjoint_axioms) == 1
    operands = {c.str for c in disjoint_axioms[0].class_expressions()}
    assert operands == {NS + "Person", NS + "Robot"}


def test_get_tbox_axioms_ignores_annotation_predicates(basic_kg_path):
    """Person carries an rdfs:comment; this must not raise and must not surface as a TBox axiom."""
    onto = RDFLibOntology(basic_kg_path)
    axioms = onto.get_tbox_axioms()  # must not raise
    assert not any("A person is an Agent." in str(a) for a in axioms)


def test_get_abox_axioms_class_assertion_and_object_property(basic_kg_path):
    onto = RDFLibOntology(basic_kg_path)
    axioms = onto.get_abox_axioms()

    class_assertions = [a for a in axioms if isinstance(a, OWLClassAssertionAxiom)]
    object_prop_assertions = [a for a in axioms if isinstance(a, OWLObjectPropertyAssertionAxiom)]

    assert any(a.get_individual().str == NS + "alice" and a.get_class_expression().str == NS + "Person"
               for a in class_assertions)
    assert any(a.get_subject().str == NS + "alice" and a.get_object().str == NS + "bob"
               for a in object_prop_assertions)


def test_get_abox_axioms_data_property_assertion(basic_kg_path):
    onto = RDFLibOntology(basic_kg_path)
    axioms = onto.get_abox_axioms()

    data_prop_assertions = [a for a in axioms if isinstance(a, OWLDataPropertyAssertionAxiom)]
    assert len(data_prop_assertions) == 1
    axiom = data_prop_assertions[0]
    assert axiom.get_subject().str == NS + "alice"
    assert axiom.get_property().str == NS + "age"
    assert axiom.get_object().to_python() == 30


def test_get_abox_axioms_class_assertion_for_undeclared_class(undeclared_type_kg_path):
    onto = RDFLibOntology(undeclared_type_kg_path)
    axioms = onto.get_abox_axioms()  # must not raise

    class_assertions = [a for a in axioms if isinstance(a, OWLClassAssertionAxiom)]
    assert any(a.get_individual().str == NS + "alice" and a.get_class_expression().str == NS + "SomethingUndeclared"
               for a in class_assertions)


def test_get_abox_axioms_object_property_to_undeclared_individual(undeclared_individual_target_kg_path):
    onto = RDFLibOntology(undeclared_individual_target_kg_path)
    axioms = onto.get_abox_axioms()  # must not raise

    object_prop_assertions = [a for a in axioms if isinstance(a, OWLObjectPropertyAssertionAxiom)]
    assert any(a.get_subject().str == NS + "alice" and a.get_object().str == NS + "bob"
               for a in object_prop_assertions)


class TestRDFLibOntologyReadAPI:
    """Read-only signature/axiom-retrieval methods, exercised against `basic_kg_path`."""

    @pytest.fixture(autouse=True)
    def _onto(self, basic_kg_path):
        self.onto = RDFLibOntology(basic_kg_path)

    def test_classes_in_signature(self):
        classes = {c.str for c in self.onto.classes_in_signature()}
        assert classes == {NS + "Person", NS + "Agent", NS + "Human", NS + "Robot"}

    def test_data_properties_in_signature(self):
        assert {p.str for p in self.onto.data_properties_in_signature()} == {NS + "age"}

    def test_object_properties_in_signature(self):
        assert {p.str for p in self.onto.object_properties_in_signature()} == {NS + "knows"}

    def test_properties_in_signature(self):
        assert {p.str for p in self.onto.properties_in_signature()} == {NS + "age", NS + "knows"}

    def test_individuals_in_signature(self):
        assert {i.str for i in self.onto.individuals_in_signature()} == {NS + "alice", NS + "bob"}

    def test_get_abox_axioms_between_individuals(self):
        axioms = self.onto.get_abox_axioms_between_individuals()
        assert all(isinstance(a, OWLObjectPropertyAssertionAxiom) for a in axioms)
        assert any(a.get_subject().str == NS + "alice" and a.get_object().str == NS + "bob" for a in axioms)

    def test_get_abox_axioms_between_individuals_and_classes(self):
        axioms = self.onto.get_abox_axioms_between_individuals_and_classes()
        assert all(isinstance(a, OWLClassAssertionAxiom) for a in axioms)
        assert any(a.get_individual().str == NS + "alice" and a.get_class_expression().str == NS + "Person"
                   for a in axioms)

    def test_equivalent_classes_axioms(self):
        axioms = list(self.onto.equivalent_classes_axioms(OWLClass(NS + "Person")))
        assert len(axioms) == 1
        operands = {c.str for c in axioms[0].class_expressions()}
        assert operands == {NS + "Person", NS + "Human"}

    def test_equivalent_classes_axioms_reverse_direction(self):
        # Human is only ever the *object* of owl:equivalentClass in the fixture graph;
        # querying from that side must still find the (Person, Human) pair.
        axioms = list(self.onto.equivalent_classes_axioms(OWLClass(NS + "Human")))
        assert len(axioms) == 1
        operands = {c.str for c in axioms[0].class_expressions()}
        assert operands == {NS + "Person", NS + "Human"}

    def test_general_class_axioms_not_supported(self):
        with pytest.raises(NotImplementedError):
            next(iter(self.onto.general_class_axioms()))

    def test_data_property_domain_axioms(self):
        axioms = list(self.onto.data_property_domain_axioms(OWLDataProperty(NS + "age")))
        assert len(axioms) == 1
        assert isinstance(axioms[0], OWLDataPropertyDomainAxiom)
        assert axioms[0].get_domain().str == NS + "Person"

    def test_data_property_range_axioms(self):
        axioms = list(self.onto.data_property_range_axioms(OWLDataProperty(NS + "age")))
        assert len(axioms) == 1
        assert isinstance(axioms[0], OWLDataPropertyRangeAxiom)
        assert axioms[0].get_range().str == "http://www.w3.org/2001/XMLSchema#integer"

    def test_object_property_domain_axioms(self):
        axioms = list(self.onto.object_property_domain_axioms(OWLObjectProperty(NS + "knows")))
        assert len(axioms) == 1
        assert isinstance(axioms[0], OWLObjectPropertyDomainAxiom)
        assert axioms[0].get_domain().str == NS + "Person"

    def test_object_property_range_axioms(self):
        axioms = list(self.onto.object_property_range_axioms(OWLObjectProperty(NS + "knows")))
        assert len(axioms) == 1
        assert isinstance(axioms[0], OWLObjectPropertyRangeAxiom)
        assert axioms[0].get_range().str == NS + "Agent"

    def test_domain_range_axioms_empty_when_unasserted(self):
        undeclared = OWLObjectProperty(NS + "doesNotExist")
        assert list(self.onto.object_property_domain_axioms(undeclared)) == []
        assert list(self.onto.object_property_range_axioms(undeclared)) == []

    def test_get_ontology_id(self):
        oid = self.onto.get_ontology_id()
        assert oid.get_ontology_iri().as_str() == ONTOLOGY_IRI
        assert oid.get_version_iri() is None
        assert not oid.is_anonymous()

    def test_eq_same_path(self, basic_kg_path):
        assert self.onto == RDFLibOntology(basic_kg_path)

    def test_eq_different_path(self, tmp_path):
        g = Graph()
        g.add((URIRef(NS + "Other"), RDF.type, OWL.Class))
        other_path = str(tmp_path / "other.owl")
        _write_graph(other_path, g)
        assert self.onto != RDFLibOntology(other_path)

    def test_hash_stable_for_equal_ontologies(self, basic_kg_path):
        assert hash(self.onto) == hash(RDFLibOntology(basic_kg_path))

    def test_repr_contains_path(self, basic_kg_path):
        assert basic_kg_path in repr(self.onto)


def test_get_ontology_id_is_anonymous_without_ontology_declaration(tmp_path):
    g = Graph()
    g.add((URIRef(NS + "Person"), RDF.type, OWL.Class))
    path = str(tmp_path / "no_ontology_decl.owl")
    _write_graph(path, g)

    onto = RDFLibOntology(path)
    oid = onto.get_ontology_id()
    assert oid.is_anonymous()
    assert oid.get_ontology_iri() is None


class TestRDFLibOntologyWriteAPIUnimplemented:
    """The write API (add/remove/save) is a separate, still-unimplemented piece of work."""

    @pytest.fixture(autouse=True)
    def _onto(self, basic_kg_path):
        self.onto = RDFLibOntology(basic_kg_path)

    def test_add_axiom(self):
        with pytest.raises(NotImplementedError):
            self.onto.add_axiom([])

    def test_remove_axiom(self):
        with pytest.raises(NotImplementedError):
            self.onto.remove_axiom([])

    def test_save(self):
        with pytest.raises(NotImplementedError):
            self.onto.save(path="out.owl")
