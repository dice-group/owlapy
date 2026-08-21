"""Unit tests for owlapy.owl_ontology.RDFLibOntology.

RDFLibOntology is a lightweight, pure-rdflib triple reader/writer: it only understands
axioms expressed directly between *named* entities (classes, individuals,
properties). Anything that would require reconstructing/emitting a complex class
expression from blank-node RDF structures (owl:Restriction,
owl:intersectionOf, ...) is out of scope and `general_class_axioms()` raises
`NotImplementedError` to say so explicitly, matching `get_tbox_axioms()`,
which likewise skips blank-node operands. `add_axiom()`/`remove_axiom()` raise
`NotImplementedError` for the same reason on any axiom involving a complex
expression, or an axiom type not yet supported by the write API.
"""

import os

import pytest
import rdflib
from rdflib import OWL, RDF, RDFS, XSD, Graph, Literal, URIRef

from owlapy.class_expression import OWLClass, OWLObjectIntersectionOf
from owlapy.iri import IRI
from owlapy.owl_axiom import (
    OWLAsymmetricObjectPropertyAxiom,
    OWLClassAssertionAxiom,
    OWLDataPropertyAssertionAxiom,
    OWLDataPropertyDomainAxiom,
    OWLDataPropertyRangeAxiom,
    OWLDeclarationAxiom,
    OWLDisjointClassesAxiom,
    OWLEquivalentClassesAxiom,
    OWLFunctionalDataPropertyAxiom,
    OWLFunctionalObjectPropertyAxiom,
    OWLInverseFunctionalObjectPropertyAxiom,
    OWLIrreflexiveObjectPropertyAxiom,
    OWLObjectPropertyAssertionAxiom,
    OWLObjectPropertyDomainAxiom,
    OWLObjectPropertyRangeAxiom,
    OWLReflexiveObjectPropertyAxiom,
    OWLSameIndividualAxiom,
    OWLSubClassOfAxiom,
    OWLSubDataPropertyOfAxiom,
    OWLSubObjectPropertyOfAxiom,
    OWLSymmetricObjectPropertyAxiom,
    OWLTransitiveObjectPropertyAxiom,
)
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_data_ranges import OWLDataUnionOf
from owlapy.owl_literal import DoubleOWLDatatype, IntOWLDatatype
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
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


def test_construction_without_load_creates_blank_ontology_with_given_iri(tmp_path):
    # `path` is not required to exist when load=False -- it's the new ontology's IRI, not a file.
    onto = RDFLibOntology(str(tmp_path / "nonexistent.owl"), load=False)
    assert onto.get_ontology_id().get_ontology_iri().as_str() == str(tmp_path / "nonexistent.owl")


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


def test_construction_with_load_false_creates_blank_ontology():
    onto = RDFLibOntology(ONTOLOGY_IRI, load=False)
    assert len(onto) == 1  # just the owl:Ontology declaration triple
    assert list(onto.classes_in_signature()) == []
    assert list(onto.individuals_in_signature()) == []
    assert list(onto.object_properties_in_signature()) == []
    assert list(onto.data_properties_in_signature()) == []
    oid = onto.get_ontology_id()
    assert not oid.is_anonymous()
    assert oid.get_ontology_iri().as_str() == ONTOLOGY_IRI


def test_construction_with_load_false_accepts_iri_object():
    onto = RDFLibOntology(IRI.create(ONTOLOGY_IRI), load=False)
    assert onto.get_ontology_id().get_ontology_iri().as_str() == ONTOLOGY_IRI


def test_add_axiom_empty_iterable_is_a_no_op():
    onto = RDFLibOntology(ONTOLOGY_IRI, load=False)
    onto.add_axiom([])
    assert len(onto) == 1


class TestRDFLibOntologyAddAxiom:
    """add_axiom() on a blank ontology, checked both by re-reading through the public read API
    and by inspecting the raw triple where the read API doesn't expose the axiom kind."""

    @pytest.fixture(autouse=True)
    def _onto(self):
        self.onto = RDFLibOntology(ONTOLOGY_IRI, load=False)
        self.Person = OWLClass(NS + "Person")
        self.Agent = OWLClass(NS + "Agent")
        self.Human = OWLClass(NS + "Human")
        self.Robot = OWLClass(NS + "Robot")
        self.knows = OWLObjectProperty(NS + "knows")
        self.age = OWLDataProperty(NS + "age")
        self.alice = OWLNamedIndividual(NS + "alice")
        self.bob = OWLNamedIndividual(NS + "bob")

    def test_add_axiom_sets_is_modified(self):
        assert self.onto.is_modified is False
        self.onto.add_axiom(OWLDeclarationAxiom(self.Person))
        assert self.onto.is_modified is True

    def test_declaration_axiom_class(self):
        self.onto.add_axiom(OWLDeclarationAxiom(self.Person))
        assert self.Person.str in {c.str for c in self.onto.classes_in_signature()}

    def test_declaration_axiom_individual(self):
        self.onto.add_axiom(OWLDeclarationAxiom(self.alice))
        assert self.alice.str in {i.str for i in self.onto.individuals_in_signature()}

    def test_declaration_axiom_object_property(self):
        self.onto.add_axiom(OWLDeclarationAxiom(self.knows))
        assert self.knows.str in {p.str for p in self.onto.object_properties_in_signature()}

    def test_declaration_axiom_data_property(self):
        self.onto.add_axiom(OWLDeclarationAxiom(self.age))
        assert self.age.str in {p.str for p in self.onto.data_properties_in_signature()}

    def test_class_assertion_auto_declares_individual_and_class(self):
        self.onto.add_axiom(OWLClassAssertionAxiom(self.alice, self.Person))
        assert self.alice.str in {i.str for i in self.onto.individuals_in_signature()}
        assert self.Person.str in {c.str for c in self.onto.classes_in_signature()}
        axioms = [a for a in self.onto.get_abox_axioms() if isinstance(a, OWLClassAssertionAxiom)]
        assert any(a.get_individual().str == self.alice.str and a.get_class_expression().str == self.Person.str
                   for a in axioms)

    def test_object_property_assertion_auto_declares_everything(self):
        self.onto.add_axiom(OWLObjectPropertyAssertionAxiom(self.alice, self.knows, self.bob))
        assert {self.alice.str, self.bob.str} <= {i.str for i in self.onto.individuals_in_signature()}
        assert self.knows.str in {p.str for p in self.onto.object_properties_in_signature()}
        axioms = list(self.onto.get_abox_axioms_between_individuals())
        assert any(a.get_subject().str == self.alice.str and a.get_object().str == self.bob.str for a in axioms)

    def test_data_property_assertion_round_trips_literal(self):
        self.onto.add_axiom(OWLDataPropertyAssertionAxiom(self.alice, self.age, OWLLiteral(30)))
        axioms = [a for a in self.onto.get_abox_axioms() if isinstance(a, OWLDataPropertyAssertionAxiom)]
        assert len(axioms) == 1
        assert axioms[0].get_object().to_python() == 30

    def test_sub_class_of_auto_declares_both_operands(self):
        self.onto.add_axiom(OWLSubClassOfAxiom(self.Person, self.Agent))
        classes = {c.str for c in self.onto.classes_in_signature()}
        assert {self.Person.str, self.Agent.str} <= classes
        subs = [a for a in self.onto.get_tbox_axioms() if isinstance(a, OWLSubClassOfAxiom)]
        assert any(a.get_sub_class().str == self.Person.str and a.get_super_class().str == self.Agent.str
                   for a in subs)

    def test_sub_class_of_rejects_complex_expression(self):
        with pytest.raises(NotImplementedError):
            self.onto.add_axiom(OWLSubClassOfAxiom(OWLObjectIntersectionOf([self.Agent, self.Robot]), self.Person))

    def test_equivalent_classes_three_operands_found_from_any_side(self):
        self.onto.add_axiom(OWLEquivalentClassesAxiom([self.Person, self.Human, self.Robot]))
        # add_axiom() chains Person->Human->Robot; equivalent_classes_axioms() looks both ways.
        found_from_person = {c.str for a in self.onto.equivalent_classes_axioms(self.Person) for c in a.class_expressions()}
        found_from_robot = {c.str for a in self.onto.equivalent_classes_axioms(self.Robot) for c in a.class_expressions()}
        assert self.Human.str in found_from_person
        assert self.Human.str in found_from_robot

    def test_disjoint_classes_pairwise(self):
        self.onto.add_axiom(OWLDisjointClassesAxiom([self.Person, self.Agent, self.Robot]))
        disjoint_axioms = [a for a in self.onto.get_tbox_axioms() if isinstance(a, OWLDisjointClassesAxiom)]
        pairs = {frozenset(c.str for c in a.class_expressions()) for a in disjoint_axioms}
        assert frozenset({self.Person.str, self.Agent.str}) in pairs
        assert frozenset({self.Person.str, self.Robot.str}) in pairs
        assert frozenset({self.Agent.str, self.Robot.str}) in pairs

    def test_object_property_domain_and_range(self):
        self.onto.add_axiom(OWLObjectPropertyDomainAxiom(self.knows, self.Person))
        self.onto.add_axiom(OWLObjectPropertyRangeAxiom(self.knows, self.Agent))
        domains = list(self.onto.object_property_domain_axioms(self.knows))
        ranges = list(self.onto.object_property_range_axioms(self.knows))
        assert len(domains) == 1 and domains[0].get_domain().str == self.Person.str
        assert len(ranges) == 1 and ranges[0].get_range().str == self.Agent.str

    def test_data_property_domain_and_range(self):
        xsd_int = OWLDatatype("http://www.w3.org/2001/XMLSchema#integer")
        self.onto.add_axiom(OWLDataPropertyDomainAxiom(self.age, self.Person))
        self.onto.add_axiom(OWLDataPropertyRangeAxiom(self.age, xsd_int))
        domains = list(self.onto.data_property_domain_axioms(self.age))
        ranges = list(self.onto.data_property_range_axioms(self.age))
        assert len(domains) == 1 and domains[0].get_domain().str == self.Person.str
        assert len(ranges) == 1 and ranges[0].get_range().str == xsd_int.str

    def test_data_property_range_rejects_non_datatype(self):
        with pytest.raises(TypeError):
            self.onto.add_axiom(OWLDataPropertyRangeAxiom(self.age, self.Person))
        with pytest.raises(NotImplementedError):
            complex_datatype = OWLDataUnionOf([OWLDatatype(XSD.integer), OWLDatatype(XSD.double)])
            self.onto.add_axiom(OWLDataPropertyRangeAxiom(self.age, complex_datatype))

    def test_sub_object_property_of(self):
        sub = OWLObjectProperty(NS + "hasCloseFriend")
        self.onto.add_axiom(OWLSubObjectPropertyOfAxiom(sub, self.knows))
        assert (URIRef(sub.str), RDFS.subPropertyOf, URIRef(self.knows.str)) in self.onto.rdflib_graph
        assert sub.str in {p.str for p in self.onto.object_properties_in_signature()}

    def test_sub_data_property_of(self):
        sub = OWLDataProperty(NS + "preciseAge")
        self.onto.add_axiom(OWLSubDataPropertyOfAxiom(sub, self.age))
        assert (URIRef(sub.str), RDFS.subPropertyOf, URIRef(self.age.str)) in self.onto.rdflib_graph

    @pytest.mark.parametrize(("axiom_cls", "owl_term"), [
        (OWLFunctionalObjectPropertyAxiom, OWL.FunctionalProperty),
        (OWLInverseFunctionalObjectPropertyAxiom, OWL.InverseFunctionalProperty),
        (OWLSymmetricObjectPropertyAxiom, OWL.SymmetricProperty),
        (OWLAsymmetricObjectPropertyAxiom, OWL.AsymmetricProperty),
        (OWLTransitiveObjectPropertyAxiom, OWL.TransitiveProperty),
        (OWLReflexiveObjectPropertyAxiom, OWL.ReflexiveProperty),
        (OWLIrreflexiveObjectPropertyAxiom, OWL.IrreflexiveProperty),
    ])
    def test_object_property_characteristics(self, axiom_cls, owl_term):
        self.onto.add_axiom(axiom_cls(self.knows))
        assert (URIRef(self.knows.str), RDF.type, owl_term) in self.onto.rdflib_graph
        assert self.knows.str in {p.str for p in self.onto.object_properties_in_signature()}

    def test_functional_data_property_characteristic(self):
        self.onto.add_axiom(OWLFunctionalDataPropertyAxiom(self.age))
        assert (URIRef(self.age.str), RDF.type, OWL.FunctionalProperty) in self.onto.rdflib_graph
        assert self.age.str in {p.str for p in self.onto.data_properties_in_signature()}

    def test_add_axiom_list_batch(self):
        self.onto.add_axiom([
            OWLDeclarationAxiom(self.Person),
            OWLClassAssertionAxiom(self.alice, self.Person),
            OWLObjectPropertyAssertionAxiom(self.alice, self.knows, self.bob),
        ])
        assert len(list(self.onto.get_abox_axioms())) == 2

    def test_unsupported_axiom_type_raises(self):
        with pytest.raises(NotImplementedError):
            self.onto.add_axiom(OWLSameIndividualAxiom([self.alice, self.bob]))


class TestRDFLibOntologyRemoveAxiom:
    @pytest.fixture(autouse=True)
    def _onto(self):
        self.onto = RDFLibOntology(ONTOLOGY_IRI, load=False)
        self.Person = OWLClass(NS + "Person")
        self.Agent = OWLClass(NS + "Agent")
        self.knows = OWLObjectProperty(NS + "knows")
        self.age = OWLDataProperty(NS + "age")
        self.alice = OWLNamedIndividual(NS + "alice")
        self.bob = OWLNamedIndividual(NS + "bob")
        self.onto.add_axiom([
            OWLDeclarationAxiom(self.Person),
            OWLDeclarationAxiom(self.Agent),
            OWLSubClassOfAxiom(self.Person, self.Agent),
            OWLClassAssertionAxiom(self.alice, self.Person),
            OWLObjectPropertyAssertionAxiom(self.alice, self.knows, self.bob),
            OWLDataPropertyAssertionAxiom(self.alice, self.age, OWLLiteral(30)),
            OWLObjectPropertyDomainAxiom(self.knows, self.Person),
        ])

    def test_remove_axiom_sets_is_modified(self):
        self.onto.is_modified = False
        self.onto.remove_axiom(OWLObjectPropertyDomainAxiom(self.knows, self.Person))
        assert self.onto.is_modified is True

    def test_remove_class_assertion(self):
        self.onto.remove_axiom(OWLClassAssertionAxiom(self.alice, self.Person))
        assert not any(isinstance(a, OWLClassAssertionAxiom) for a in self.onto.get_abox_axioms())
        # the individual itself remains declared -- removal doesn't cascade
        assert self.alice.str in {i.str for i in self.onto.individuals_in_signature()}

    def test_remove_object_property_assertion(self):
        self.onto.remove_axiom(OWLObjectPropertyAssertionAxiom(self.alice, self.knows, self.bob))
        assert not list(self.onto.get_abox_axioms_between_individuals())

    def test_remove_data_property_assertion(self):
        self.onto.remove_axiom(OWLDataPropertyAssertionAxiom(self.alice, self.age, OWLLiteral(30)))
        assert not any(isinstance(a, OWLDataPropertyAssertionAxiom) for a in self.onto.get_abox_axioms())

    def test_remove_sub_class_of_does_not_undeclare_classes(self):
        self.onto.remove_axiom(OWLSubClassOfAxiom(self.Person, self.Agent))
        subs = [a for a in self.onto.get_tbox_axioms() if isinstance(a, OWLSubClassOfAxiom)]
        assert not subs
        assert {self.Person.str, self.Agent.str} <= {c.str for c in self.onto.classes_in_signature()}

    def test_remove_property_domain(self):
        self.onto.remove_axiom(OWLObjectPropertyDomainAxiom(self.knows, self.Person))
        assert not list(self.onto.object_property_domain_axioms(self.knows))

    def test_remove_equivalent_classes_clears_both_directions(self):
        human = OWLClass(NS + "Human")
        self.onto.add_axiom(OWLEquivalentClassesAxiom([self.Person, human]))
        assert list(self.onto.equivalent_classes_axioms(human))  # asserted Person->Human, found from Human too
        self.onto.remove_axiom(OWLEquivalentClassesAxiom([self.Person, human]))
        assert not list(self.onto.equivalent_classes_axioms(self.Person))
        assert not list(self.onto.equivalent_classes_axioms(human))

    def test_remove_property_characteristic(self):
        self.onto.add_axiom(OWLFunctionalObjectPropertyAxiom(self.knows))
        assert (URIRef(self.knows.str), RDF.type, OWL.FunctionalProperty) in self.onto.rdflib_graph
        self.onto.remove_axiom(OWLFunctionalObjectPropertyAxiom(self.knows))
        assert (URIRef(self.knows.str), RDF.type, OWL.FunctionalProperty) not in self.onto.rdflib_graph

    def test_remove_declaration_undeclares_entity(self):
        self.onto.remove_axiom(OWLDeclarationAxiom(self.Person))
        assert self.Person.str not in {c.str for c in self.onto.classes_in_signature()}

    def test_remove_unsupported_axiom_type_raises(self):
        with pytest.raises(NotImplementedError):
            self.onto.remove_axiom(OWLSameIndividualAxiom([self.alice, self.bob]))


class TestRDFLibOntologySave:
    @pytest.fixture(autouse=True)
    def _onto(self, tmp_path):
        self.tmp_path = tmp_path
        self.onto = RDFLibOntology(ONTOLOGY_IRI, load=False)
        self.Person = OWLClass(NS + "Person")
        self.alice = OWLNamedIndividual(NS + "alice")
        self.onto.add_axiom([OWLDeclarationAxiom(self.Person), OWLClassAssertionAxiom(self.alice, self.Person)])

    def test_save_default_format_is_rdfxml_and_reloads(self):
        out = str(self.tmp_path / "out.owl")
        self.onto.save(path=out)
        reloaded = RDFLibOntology(out)
        assert self.Person.str in {c.str for c in reloaded.classes_in_signature()}

    def test_save_turtle_format_and_reloads(self):
        out = str(self.tmp_path / "out.ttl")
        self.onto.save(path=out, document_format="turtle")
        reloaded = RDFLibOntology(out)
        assert self.alice.str in {i.str for i in reloaded.individuals_in_signature()}

    def test_save_accepts_iri_path(self):
        out = str(self.tmp_path / "out_iri.owl")
        self.onto.save(path=IRI.create(out))
        assert os.path.exists(out)

    def test_save_inplace_overwrites_original(self, tmp_path):
        onto = RDFLibOntology(str(tmp_path / "orig.owl"), load=False)
        onto.add_axiom(OWLDeclarationAxiom(self.Person))
        onto.save(path=str(tmp_path / "orig.owl"), inplace=True)
        reloaded = RDFLibOntology(str(tmp_path / "orig.owl"))
        assert self.Person.str in {c.str for c in reloaded.classes_in_signature()}

    def test_save_creates_missing_parent_directories(self):
        out = str(self.tmp_path / "nested" / "dir" / "out.owl")
        self.onto.save(path=out)
        assert os.path.exists(out)

    def test_save_unsupported_format_raises_value_error(self):
        with pytest.raises(ValueError):
            self.onto.save(path=str(self.tmp_path / "out.owl"), document_format="manchester")

    def test_save_without_path_and_without_inplace_raises(self):
        with pytest.raises(AssertionError):
            self.onto.save()
