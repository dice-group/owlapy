"""
Tests for SyncOntology prefix management: get_prefixes() / set_prefix() / remove_prefix(),
and how they carry through save() for both OWL API–backed and rdflib-backed formats.
"""
import os
import unittest

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLDeclarationAxiom, OWLSubClassOfAxiom
from owlapy.owl_ontology import SyncOntology

_HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(_HERE, "saved_formats")

FOAF_NS = "http://xmlns.com/foaf/0.1/"


def _out(filename: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, filename)


def _new_ontology() -> SyncOntology:
    """A fresh in-memory ontology with one class from an external (foaf) namespace."""
    onto = SyncOntology(IRI.create("http://example.com/myonto#"), load=False)
    person = OWLClass(IRI.create("http://example.com/myonto#", "Person"))
    agent = OWLClass(IRI.create(FOAF_NS, "Agent"))
    onto.add_axiom(OWLDeclarationAxiom(person))
    onto.add_axiom(OWLDeclarationAxiom(agent))
    onto.add_axiom(OWLSubClassOfAxiom(person, agent))
    return onto


class TestSyncOntologyPrefixes(unittest.TestCase):

    def test_get_prefixes_has_default_well_known_prefixes(self):
        onto = _new_ontology()
        prefixes = onto.get_prefixes()
        for well_known in ("owl", "rdf", "rdfs", "xsd"):
            self.assertIn(well_known, prefixes)

    def test_set_prefix_registers_mapping(self):
        onto = _new_ontology()
        onto.set_prefix("foaf", FOAF_NS)
        self.assertEqual(onto.get_prefixes()["foaf"], FOAF_NS)

    def test_set_prefix_overwrites_existing_mapping(self):
        onto = _new_ontology()
        onto.set_prefix("foaf", FOAF_NS)
        onto.set_prefix("foaf", "http://example.com/other-foaf#")
        self.assertEqual(onto.get_prefixes()["foaf"], "http://example.com/other-foaf#")

    def test_remove_prefix(self):
        onto = _new_ontology()
        onto.set_prefix("foaf", FOAF_NS)
        self.assertIn("foaf", onto.get_prefixes())
        onto.remove_prefix("foaf")
        self.assertNotIn("foaf", onto.get_prefixes())

    def test_remove_prefix_keeps_other_prefixes(self):
        onto = _new_ontology()
        onto.set_prefix("foaf", FOAF_NS)
        onto.set_prefix("ex", "http://example.com/ex#")
        onto.remove_prefix("foaf")
        prefixes = onto.get_prefixes()
        self.assertNotIn("foaf", prefixes)
        self.assertEqual(prefixes["ex"], "http://example.com/ex#")

    def test_remove_prefix_is_a_noop_for_unknown_prefix(self):
        onto = _new_ontology()
        onto.remove_prefix("does_not_exist")  # must not raise

    def test_save_turtle_owlapi_uses_custom_prefix(self):
        """The OWL API–backed Turtle writer should abbreviate foaf: instead of a full IRI."""
        onto = _new_ontology()
        onto.set_prefix("foaf", FOAF_NS)
        path = _out("prefixes_turtle_owlapi.ttl")
        onto.save(path=path, document_format="turtle")
        content = open(path).read()
        self.assertIn("@prefix foaf: <http://xmlns.com/foaf/0.1/> .", content)
        self.assertIn("foaf:Agent", content)
        self.assertNotIn("<http://xmlns.com/foaf/0.1/Agent>", content)

    def test_save_turtle_rdflib_uses_custom_prefix(self):
        """The rdflib-backed Turtle writer ('turtle2') should also honour the custom prefix."""
        onto = _new_ontology()
        onto.set_prefix("foaf", FOAF_NS)
        path = _out("prefixes_turtle_rdflib.ttl")
        onto.save(path=path, document_format="turtle2")
        content = open(path).read()
        self.assertIn("foaf: <http://xmlns.com/foaf/0.1/>", content)
        self.assertIn("foaf:Agent", content)
        self.assertNotIn("<http://xmlns.com/foaf/0.1/Agent>", content)

    def test_save_without_custom_prefix_uses_full_iri(self):
        """Baseline: without set_prefix(), the external namespace has no abbreviation."""
        onto = _new_ontology()
        path = _out("prefixes_none.ttl")
        onto.save(path=path, document_format="turtle")
        content = open(path).read()
        self.assertIn("<http://xmlns.com/foaf/0.1/Agent>", content)

    def test_remove_prefix_reverts_to_full_iri_on_save(self):
        onto = _new_ontology()
        onto.set_prefix("foaf", FOAF_NS)
        onto.remove_prefix("foaf")
        path = _out("prefixes_removed.ttl")
        onto.save(path=path, document_format="turtle")
        content = open(path).read()
        self.assertIn("<http://xmlns.com/foaf/0.1/Agent>", content)
        self.assertNotIn("foaf:Agent", content)


if __name__ == "__main__":
    unittest.main()
