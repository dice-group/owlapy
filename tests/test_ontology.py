import unittest
from owlapy.owl_ontology_manager import SyncOntologyManager, OntologyManager, RDFLibOntologyManager
from owlapy.owl_ontology import SyncOntology, Ontology, RDFLibOntology
from owlapy.owl_ontology import RDFLibOntology


class TestOntology(unittest.TestCase):
    def test_counting(self):
        o_sync: SyncOntology
        o_sync = SyncOntologyManager().load_ontology(path="KGs/Family/father.owl")
        o_owlready: Ontology
        o_owlready = OntologyManager().load_ontology(path="KGs/Family/father.owl")
        o_rdf: RDFLibOntology
        o_rdf = RDFLibOntologyManager().load_ontology(path="KGs/Family/father.owl")

        assert len({i for i in o_sync.get_tbox_axioms()})==len({i for i in o_rdf.get_tbox_axioms()})
        assert len({i for i in o_sync.get_abox_axioms()})==len({i for i in o_rdf.get_abox_axioms()})
