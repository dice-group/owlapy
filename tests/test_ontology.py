import unittest
from owlapy.owl_ontology import SyncOntology, Ontology
from owlapy.owl_ontology import RDFLibOntology


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
