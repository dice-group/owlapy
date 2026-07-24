"""Unit tests for owlapy.owl_ontology.RDFLibOntology.

Most of this class's methods immediately `raise NotImplementedError("will be
implemented in future")` as their first statement (the code below the raise is
dead/aspirational code) -- those are covered by simply asserting the raise.
The few genuinely-implemented methods (__init__, __len__, get_tbox_axioms,
get_abox_axioms) are exercised against small hand-built RDF graphs so every
branch (subClassOf, equivalentClass, NamedIndividual type, class assertion,
object-property assertion, and the two error branches) is reached.
"""

import pytest
import rdflib
from rdflib import OWL, RDF, RDFS, Graph, Literal, URIRef

from owlapy.owl_axiom import OWLClassAssertionAxiom, OWLEquivalentClassesAxiom, OWLObjectPropertyAssertionAxiom, OWLSubClassOfAxiom
from owlapy.owl_ontology import RDFLibOntology

NS = "http://example.com/rdflib_onto#"


def _write_graph(path: str, graph: Graph):
    graph.serialize(destination=path, format="xml")


@pytest.fixture
def basic_kg_path(tmp_path):
    """Person subClassOf Agent, Person equivalentClass Human, alice a Person, alice knows bob."""
    g = Graph()
    person = URIRef(NS + "Person")
    agent = URIRef(NS + "Agent")
    human = URIRef(NS + "Human")
    alice = URIRef(NS + "alice")
    bob = URIRef(NS + "bob")
    knows = URIRef(NS + "knows")

    g.add((person, RDF.type, OWL.Class))
    g.add((agent, RDF.type, OWL.Class))
    g.add((human, RDF.type, OWL.Class))
    g.add((person, RDFS.subClassOf, agent))
    g.add((person, OWL.equivalentClass, human))

    g.add((alice, RDF.type, OWL.NamedIndividual))
    g.add((alice, RDF.type, person))
    g.add((bob, RDF.type, OWL.NamedIndividual))
    g.add((alice, knows, bob))

    path = str(tmp_path / "basic.owl")
    _write_graph(path, g)
    return path


@pytest.fixture
def bad_type_kg_path(tmp_path):
    """An individual asserted to be of an rdf:type that is neither a declared
    owl:Class nor owl:NamedIndividual -- triggers the RuntimeError branch."""
    g = Graph()
    alice = URIRef(NS + "alice")
    undeclared = URIRef(NS + "SomethingUndeclared")
    g.add((alice, RDF.type, OWL.NamedIndividual))
    g.add((alice, RDF.type, undeclared))

    path = str(tmp_path / "bad_type.owl")
    _write_graph(path, g)
    return path


@pytest.fixture
def data_property_kg_path(tmp_path):
    """An individual with a data-property (literal-valued) assertion, whose
    predicate/object combination matches neither the type branch nor the
    object-property branch -- triggers the bare NotImplementedError branch."""
    g = Graph()
    alice = URIRef(NS + "alice")
    age = URIRef(NS + "age")
    g.add((alice, RDF.type, OWL.NamedIndividual))
    g.add((alice, age, Literal(30)))

    path = str(tmp_path / "data_prop.owl")
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


def test_get_abox_axioms_class_assertion_and_object_property(basic_kg_path):
    onto = RDFLibOntology(basic_kg_path)
    axioms = onto.get_abox_axioms()

    class_assertions = [a for a in axioms if isinstance(a, OWLClassAssertionAxiom)]
    object_prop_assertions = [a for a in axioms if isinstance(a, OWLObjectPropertyAssertionAxiom)]

    assert any(a.get_individual().str == NS + "alice" and a.get_class_expression().str == NS + "Person"
               for a in class_assertions)
    assert any(a.get_subject().str == NS + "alice" and a.get_object().str == NS + "bob"
               for a in object_prop_assertions)


def test_get_abox_axioms_raises_runtime_error_on_unrecognized_type(bad_type_kg_path):
    onto = RDFLibOntology(bad_type_kg_path)
    with pytest.raises(RuntimeError):
        onto.get_abox_axioms()


def test_get_abox_axioms_raises_not_implemented_for_data_property(data_property_kg_path):
    onto = RDFLibOntology(data_property_kg_path)
    with pytest.raises(NotImplementedError):
        onto.get_abox_axioms()


def test_get_tbox_axioms_raises_not_implemented_for_unknown_predicate(tmp_path):
    g = Graph()
    person = URIRef(NS + "Person")
    g.add((person, RDF.type, OWL.Class))
    g.add((person, RDFS.comment, Literal("a comment, not subClassOf/equivalentClass/type")))
    path = str(tmp_path / "unknown_predicate.owl")
    _write_graph(path, g)

    onto = RDFLibOntology(path)
    with pytest.raises(NotImplementedError):
        onto.get_tbox_axioms()


class TestRDFLibOntologyUnimplementedStubs:
    """Every one of these methods raises NotImplementedError as its first statement."""

    @pytest.fixture(autouse=True)
    def _onto(self, basic_kg_path):
        self.onto = RDFLibOntology(basic_kg_path)

    def test_classes_in_signature(self):
        with pytest.raises(NotImplementedError):
            next(iter(self.onto.classes_in_signature()))

    def test_data_properties_in_signature(self):
        with pytest.raises(NotImplementedError):
            next(iter(self.onto.data_properties_in_signature()))

    def test_object_properties_in_signature(self):
        with pytest.raises(NotImplementedError):
            next(iter(self.onto.object_properties_in_signature()))

    def test_properties_in_signature(self):
        with pytest.raises(NotImplementedError):
            next(iter(self.onto.properties_in_signature()))

    def test_individuals_in_signature(self):
        with pytest.raises(NotImplementedError):
            next(iter(self.onto.individuals_in_signature()))

    def test_get_abox_axioms_between_individuals(self):
        with pytest.raises(NotImplementedError):
            self.onto.get_abox_axioms_between_individuals()

    def test_get_abox_axioms_between_individuals_and_classes(self):
        with pytest.raises(NotImplementedError):
            self.onto.get_abox_axioms_between_individuals_and_classes()

    def test_equivalent_classes_axioms(self):
        from owlapy.class_expression import OWLClass
        with pytest.raises(NotImplementedError):
            next(iter(self.onto.equivalent_classes_axioms(OWLClass(NS + "Person"))))

    def test_general_class_axioms(self):
        with pytest.raises(NotImplementedError):
            next(iter(self.onto.general_class_axioms()))

    def test_data_property_domain_axioms(self):
        from owlapy.owl_property import OWLDataProperty
        with pytest.raises(NotImplementedError):
            next(iter(self.onto.data_property_domain_axioms(OWLDataProperty(NS + "age"))))

    def test_data_property_range_axioms(self):
        from owlapy.owl_property import OWLDataProperty
        with pytest.raises(NotImplementedError):
            next(iter(self.onto.data_property_range_axioms(OWLDataProperty(NS + "age"))))

    def test_object_property_domain_axioms(self):
        from owlapy.owl_property import OWLObjectProperty
        with pytest.raises(NotImplementedError):
            next(iter(self.onto.object_property_domain_axioms(OWLObjectProperty(NS + "knows"))))

    def test_object_property_range_axioms(self):
        from owlapy.owl_property import OWLObjectProperty
        with pytest.raises(NotImplementedError):
            next(iter(self.onto.object_property_range_axioms(OWLObjectProperty(NS + "knows"))))

    def test_add_axiom(self):
        with pytest.raises(NotImplementedError):
            self.onto.add_axiom([])

    def test_remove_axiom(self):
        with pytest.raises(NotImplementedError):
            self.onto.remove_axiom([])

    def test_save(self):
        with pytest.raises(NotImplementedError):
            self.onto.save(path="out.owl")

    def test_get_ontology_id(self):
        with pytest.raises(NotImplementedError):
            self.onto.get_ontology_id()

    def test_eq(self):
        with pytest.raises(NotImplementedError):
            self.onto == self.onto  # noqa: B015

    def test_hash(self):
        with pytest.raises(NotImplementedError):
            hash(self.onto)

    def test_repr(self):
        with pytest.raises(NotImplementedError):
            repr(self.onto)
