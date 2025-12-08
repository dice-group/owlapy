import unittest
import os
from owlapy.owl_ontology import SyncOntology, Ontology, RDFLibOntology
from owlapy.class_expression import OWLClass
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
from owlapy.iri import IRI
from owlapy.owl_axiom import (
    OWLClassAssertionAxiom, OWLObjectPropertyAssertionAxiom,
    OWLDataPropertyAssertionAxiom, OWLSubClassOfAxiom,
    OWLEquivalentClassesAxiom, OWLDisjointClassesAxiom,
    OWLObjectPropertyDomainAxiom, OWLObjectPropertyRangeAxiom,
    OWLDataPropertyDomainAxiom, OWLDataPropertyRangeAxiom,
    OWLFunctionalObjectPropertyAxiom, OWLInverseFunctionalObjectPropertyAxiom,
    OWLFunctionalDataPropertyAxiom,
)
from owlapy.owl_reasoner import SyncReasoner


class TestOntology(unittest.TestCase):
    def test_counting(self):
        o_sync: SyncOntology
        o_sync = SyncOntology(path="KGs/Family/father.owl")
        o_owlready: Ontology
        o_owlready = Ontology(ontology_iri="KGs/Family/father.owl")
        o_rdf: RDFLibOntology
        o_rdf = RDFLibOntology(path="KGs/Family/father.owl")

        assert len({i for i in o_sync.get_tbox_axioms()})==len({i for i in o_rdf.get_tbox_axioms()})
        assert len({i for i in o_sync.get_abox_axioms()})==len({i for i in o_rdf.get_abox_axioms()})

class TestOntologyCreation(unittest.TestCase):
    """Test ontology creation and basic operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_files = []
        self.ns = "http://example.com/test#"

    def tearDown(self):
        """Clean up test files."""
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_create_empty_ontology_sync(self):
        """Test creating empty SyncOntology."""
        onto = SyncOntology(self.ns, load=False)

        self.assertIsNotNone(onto)

    def test_create_empty_ontology_owlready(self):
        """Test creating empty Ontology."""
        onto = Ontology(self.ns, load=False)

        self.assertIsNotNone(onto)

    def test_load_existing_ontology(self):
        """Test loading existing ontology."""
        onto = SyncOntology("KGs/Family/father.owl")

        self.assertIsNotNone(onto)

    def test_ontology_id(self):
        """Test getting ontology ID."""
        onto = SyncOntology(self.ns, load=False)
        onto_id = onto.get_ontology_id()

        self.assertIsNotNone(onto_id)

    def test_classes_in_signature(self):
        """Test getting classes in signature."""
        onto = SyncOntology("KGs/Family/father.owl")
        classes = list(onto.classes_in_signature())

        self.assertGreater(len(classes), 0)

    def test_object_properties_in_signature(self):
        """Test getting object properties in signature."""
        onto = SyncOntology("KGs/Family/father.owl")
        props = list(onto.object_properties_in_signature())

        self.assertGreater(len(props), 0)

    def test_data_properties_in_signature(self):
        """Test getting data properties in signature."""
        onto = SyncOntology(self.ns, load=False)

        # Add a data property
        dp = OWLDataProperty(IRI.create(self.ns, "hasAge"))
        ind = OWLNamedIndividual(IRI.create(self.ns, "Alice"))
        lit = OWLLiteral(30)
        axiom = OWLDataPropertyAssertionAxiom(ind, dp, lit)
        onto.add_axiom(axiom)

        props = list(onto.data_properties_in_signature())
        self.assertIn(dp, props)

    def test_individuals_in_signature(self):
        """Test getting individuals in signature."""
        onto = SyncOntology("KGs/Family/father.owl")
        individuals = list(onto.individuals_in_signature())

        self.assertGreater(len(individuals), 0)


class TestAxiomOperations(unittest.TestCase):
    """Test axiom operations."""

    def setUp(self):
        """Set up test fixtures."""
        self.ns = "http://example.com/test#"
        self.onto = SyncOntology(self.ns, load=False)

    def test_add_class_assertion_axiom(self):
        """Test adding class assertion axiom."""
        person = OWLClass(IRI.create(self.ns, "Person"))
        alice = OWLNamedIndividual(IRI.create(self.ns, "Alice"))

        axiom = OWLClassAssertionAxiom(alice, person)
        self.onto.add_axiom(axiom)

        axioms = list(self.onto.get_abox_axioms())
        self.assertIn(axiom, axioms)

    def test_add_object_property_assertion_axiom(self):
        """Test adding object property assertion axiom."""
        knows = OWLObjectProperty(IRI.create(self.ns, "knows"))
        alice = OWLNamedIndividual(IRI.create(self.ns, "Alice"))
        bob = OWLNamedIndividual(IRI.create(self.ns, "Bob"))

        axiom = OWLObjectPropertyAssertionAxiom(alice, knows, bob)
        self.onto.add_axiom(axiom)

        axioms = list(self.onto.get_abox_axioms())
        self.assertIn(axiom, axioms)

    def test_add_data_property_assertion_axiom(self):
        """Test adding data property assertion axiom."""
        has_age = OWLDataProperty(IRI.create(self.ns, "hasAge"))
        alice = OWLNamedIndividual(IRI.create(self.ns, "Alice"))
        age = OWLLiteral(30)

        axiom = OWLDataPropertyAssertionAxiom(alice, has_age, age)
        self.onto.add_axiom(axiom)

        axioms = list(self.onto.get_abox_axioms())
        self.assertIn(axiom, axioms)

    def test_add_subclass_axiom(self):
        """Test adding subclass axiom."""
        person = OWLClass(IRI.create(self.ns, "Person"))
        male = OWLClass(IRI.create(self.ns, "Male"))

        axiom = OWLSubClassOfAxiom(male, person)
        self.onto.add_axiom(axiom)

        axioms = list(self.onto.get_tbox_axioms())
        self.assertIn(axiom, axioms)

    def test_add_equivalent_classes_axiom(self):
        """Test adding equivalent classes axiom."""
        person = OWLClass(IRI.create(self.ns, "Person"))
        human = OWLClass(IRI.create(self.ns, "Human"))

        axiom = OWLEquivalentClassesAxiom([person, human])
        self.onto.add_axiom(axiom)

        axioms = list(self.onto.get_tbox_axioms())
        self.assertIn(axiom, axioms)

    def test_add_disjoint_classes_axiom(self):
        """Test adding disjoint classes axiom."""
        male = OWLClass(IRI.create(self.ns, "Male"))
        female = OWLClass(IRI.create(self.ns, "Female"))

        axiom = OWLDisjointClassesAxiom([male, female])
        self.onto.add_axiom(axiom)

        axioms = list(self.onto.get_tbox_axioms())
        self.assertIn(axiom, axioms)

    def test_add_object_property_domain_axiom(self):
        """Test adding object property domain axiom."""
        knows = OWLObjectProperty(IRI.create(self.ns, "knows"))
        person = OWLClass(IRI.create(self.ns, "Person"))

        axiom = OWLObjectPropertyDomainAxiom(knows, person)
        self.onto.add_axiom(axiom)

        axioms = list(self.onto.get_tbox_axioms())
        self.assertIn(axiom, axioms)

    def test_add_object_property_range_axiom(self):
        """Test adding object property range axiom."""
        knows = OWLObjectProperty(IRI.create(self.ns, "knows"))
        person = OWLClass(IRI.create(self.ns, "Person"))

        axiom = OWLObjectPropertyRangeAxiom(knows, person)
        self.onto.add_axiom(axiom)

        axioms = list(self.onto.get_tbox_axioms())
        self.assertIn(axiom, axioms)

    def test_add_data_property_domain_axiom(self):
        """Test adding data property domain axiom."""
        has_age = OWLDataProperty(IRI.create(self.ns, "hasAge"))
        person = OWLClass(IRI.create(self.ns, "Person"))

        axiom = OWLDataPropertyDomainAxiom(has_age, person)
        self.onto.add_axiom(axiom)

        axioms = list(self.onto.get_tbox_axioms())
        self.assertIn(axiom, axioms)

    def test_add_data_property_range_axiom(self):
        """Test adding data property range axiom."""
        from owlapy.owl_datatype import OWLDatatype
        from owlapy.vocab import XSDVocabulary

        has_age = OWLDataProperty(IRI.create(self.ns, "hasAge"))
        int_type = OWLDatatype(XSDVocabulary.INTEGER)

        axiom = OWLDataPropertyRangeAxiom(has_age, int_type)
        self.onto.add_axiom(axiom)

        axioms = list(self.onto.get_tbox_axioms())
        self.assertIn(axiom, axioms)

    def test_add_functional_property_axiom(self):
        """Test adding functional property axiom."""
        has_father = OWLObjectProperty(IRI.create(self.ns, "hasFather"))

        axiom = OWLFunctionalObjectPropertyAxiom(has_father)
        self.onto.add_axiom(axiom)

        axioms = list(self.onto.get_tbox_axioms())
        self.assertIn(axiom, axioms)

    def test_add_inverse_functional_property_axiom(self):
        """Test adding inverse functional property axiom."""
        has_social_security = OWLObjectProperty(IRI.create(self.ns, "hasSocialSecurity"))

        axiom = OWLInverseFunctionalObjectPropertyAxiom(has_social_security)
        self.onto.add_axiom(axiom)

        axioms = list(self.onto.get_tbox_axioms())
        self.assertIn(axiom, axioms)

    def test_add_functional_data_property_axiom(self):
        """Test adding functional data property axiom."""
        has_birth_year = OWLDataProperty(IRI.create(self.ns, "hasBirthYear"))

        axiom = OWLFunctionalDataPropertyAxiom(has_birth_year)
        self.onto.add_axiom(axiom)

        axioms = list(self.onto.get_tbox_axioms())
        self.assertIn(axiom, axioms)

    def test_remove_axiom(self):
        """Test removing axiom."""
        person = OWLClass(IRI.create(self.ns, "Person"))
        alice = OWLNamedIndividual(IRI.create(self.ns, "Alice"))

        axiom = OWLClassAssertionAxiom(alice, person)
        self.onto.add_axiom(axiom)

        self.assertIn(axiom, list(self.onto.get_abox_axioms()))

        self.onto.remove_axiom(axiom)

        self.assertNotIn(axiom, list(self.onto.get_abox_axioms()))


class TestOntologySaveLoad(unittest.TestCase):
    """Test saving and loading ontologies."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_files = []
        self.ns = "http://example.com/test#"

    def tearDown(self):
        """Clean up test files."""
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_save_ontology(self):
        """Test saving ontology."""
        onto = SyncOntology(self.ns, load=False)

        # Add some axioms
        person = OWLClass(IRI.create(self.ns, "Person"))
        alice = OWLNamedIndividual(IRI.create(self.ns, "Alice"))
        axiom = OWLClassAssertionAxiom(alice, person)
        onto.add_axiom(axiom)

        path = "test_save.owl"
        self.test_files.append(path)

        onto.save(path=path)

        self.assertTrue(os.path.exists(path))

    def test_save_and_load_ontology(self):
        """Test saving and loading ontology."""
        onto1 = SyncOntology(self.ns, load=False)

        # Add some axioms
        person = OWLClass(IRI.create(self.ns, "Person"))
        alice = OWLNamedIndividual(IRI.create(self.ns, "Alice"))
        axiom = OWLClassAssertionAxiom(alice, person)
        onto1.add_axiom(axiom)

        path = "test_save_load.owl"
        self.test_files.append(path)

        onto1.save(path=path)

        # Load the ontology
        onto2 = SyncOntology(path)

        axioms = list(onto2.get_abox_axioms())
        self.assertGreater(len(axioms), 0)


class TestRDFLibOntology(unittest.TestCase):
    """Test RDFLibOntology specific functionality."""

    def test_load_rdflib_ontology(self):
        """Test loading ontology with RDFLib."""
        onto = RDFLibOntology("KGs/Family/father.owl")

        self.assertIsNotNone(onto)

    def test_rdflib_get_axioms(self):
        """Test getting axioms from RDFLib ontology."""
        onto = RDFLibOntology("KGs/Family/father.owl")

        tbox = list(onto.get_tbox_axioms())
        abox = list(onto.get_abox_axioms())

        self.assertGreater(len(tbox) + len(abox), 0)


class TestOntologyQueries(unittest.TestCase):
    """Test ontology query methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.onto = SyncOntology("KGs/Family/father.owl")

    def test_get_type_instances(self):
        """Test getting instances of a type."""
        # Get all classes
        classes = list(self.onto.classes_in_signature())
        reasoner = SyncReasoner(self.onto)
        if classes:
            cls = classes[0]
            instances = list(reasoner.instances(cls))
            # May or may not have instances, just check it doesn't crash
            self.assertIsInstance(instances, list)

    def test_get_property_values(self):
        """Test getting object property values."""
        individuals = list(self.onto.individuals_in_signature())
        props = list(self.onto.object_properties_in_signature())
        reasoner = SyncReasoner(self.onto)
        if individuals and props:
            ind = individuals[0]
            prop = props[0]
            values = list(reasoner.object_property_values(ind, prop))
            # May or may not have values
            self.assertIsInstance(values, list)

        """Test getting data property values."""
        individuals = list(self.onto.individuals_in_signature())
        props = list(self.onto.data_properties_in_signature())

        if individuals and props:
            ind = individuals[0]
            prop = props[0]
            values = list(reasoner.data_property_values(ind, prop))
            # May or may not have values
            self.assertIsInstance(values, list)

if __name__ == '__main__':
    unittest.main()
