import os
import tempfile
import unittest

from owlapy.owl_axiom import OWLClassAssertionAxiom, OWLObjectPropertyAssertionAxiom
from owlapy.owl_individual import OWLAnonymousIndividual, OWLNamedIndividual
from owlapy.owl_ontology import SyncOntology

# Minimal reproduction from https://github.com/dice-group/owlapy/issues/217
ONTOLOGY_WITH_ANONYMOUS_INDIVIDUAL = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix ex: <http://example.org/> .

<http://example.org/ontology> a owl:Ontology ;
    rdfs:label "Example Ontology with Anonymous Individual" .

ex:Person a owl:Class ;
    rdfs:label "Person" .

ex:knows a owl:ObjectProperty ;
    rdfs:label "knows" ;
    rdfs:domain ex:Person ;
    rdfs:range ex:Person .

ex:Alice a ex:Person ;
    rdfs:label "Alice" ;
    ex:knows [ a ex:Person ] .
"""


class TestOWLAnonymousIndividual(unittest.TestCase):
    """Unit tests for the OWLAnonymousIndividual class itself (no JVM involved)."""

    def test_generates_distinct_fresh_node_ids(self):
        a = OWLAnonymousIndividual()
        b = OWLAnonymousIndividual()
        self.assertNotEqual(a, b)

    def test_same_explicit_node_id_is_equal(self):
        a = OWLAnonymousIndividual("b0")
        b = OWLAnonymousIndividual("b0")
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))

    def test_strips_blank_node_prefix(self):
        a = OWLAnonymousIndividual("_:b0")
        b = OWLAnonymousIndividual("b0")
        self.assertEqual(a, b)
        self.assertEqual(a.node_id, "b0")

    def test_is_anonymous(self):
        self.assertTrue(OWLAnonymousIndividual("b0").is_anonymous())

    def test_not_equal_to_named_individual(self):
        self.assertNotEqual(OWLAnonymousIndividual("b0"), OWLNamedIndividual("http://example.org/b0"))


class TestOntologyWithAnonymousIndividual(unittest.TestCase):
    """Regression test for issue #217: loading an ontology containing an anonymous
    individual used to crash get_abox_axioms() with a functools.singledispatch error
    while mapping OWLAnonymousIndividualImpl through the OWLAPI bridge."""

    def setUp(self):
        fd, self.ttl_path = tempfile.mkstemp(suffix=".ttl")
        with os.fdopen(fd, "w") as f:
            f.write(ONTOLOGY_WITH_ANONYMOUS_INDIVIDUAL)

    def tearDown(self):
        os.remove(self.ttl_path)

    def test_get_abox_axioms_does_not_raise(self):
        ontology = SyncOntology(self.ttl_path)
        abox_axioms = list(ontology.get_abox_axioms())
        self.assertEqual(len(abox_axioms), 3)

    def test_anonymous_individual_is_consistent_across_axioms(self):
        ontology = SyncOntology(self.ttl_path)
        abox_axioms = list(ontology.get_abox_axioms())

        class_assertions = [a for a in abox_axioms if isinstance(a, OWLClassAssertionAxiom)]
        object_property_assertions = [a for a in abox_axioms if isinstance(a, OWLObjectPropertyAssertionAxiom)]

        anonymous_class_assertions = [a for a in class_assertions if a.get_individual().is_anonymous()]
        self.assertEqual(len(anonymous_class_assertions), 1)
        anonymous_individual = anonymous_class_assertions[0].get_individual()
        self.assertIsInstance(anonymous_individual, OWLAnonymousIndividual)
        self.assertEqual(anonymous_class_assertions[0].get_class_expression(),
                         next(a for a in class_assertions if not a.get_individual().is_anonymous()).get_class_expression())

        self.assertEqual(len(object_property_assertions), 1)
        knows_axiom = object_property_assertions[0]
        self.assertEqual(knows_axiom.get_subject(), OWLNamedIndividual("http://example.org/Alice"))
        # The object of ex:knows must be the very same anonymous individual asserted to be a Person.
        self.assertEqual(knows_axiom.get_object(), anonymous_individual)


if __name__ == '__main__':
    unittest.main()
