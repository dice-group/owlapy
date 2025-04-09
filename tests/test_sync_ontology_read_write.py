import unittest

from owlapy.iri import IRI
from owlapy.owl_ontology import SyncOntology


class TestSyncReasoner(unittest.TestCase):
    def test_read_write(self):
        # Create an empty ontology
        o1 = SyncOntology(IRI.create("file:/example_ontology.owl"), load=False)
        # () Add tbox axioms from another ontology
        for axiom in SyncOntology("KGs/Family/father.owl").get_tbox_axioms():
            o1.add_axiom(axiom)
        # () Add abox axioms from another ontology
        for axiom in SyncOntology("KGs/Family/father.owl").get_abox_axioms():
            o1.add_axiom(axiom)
        o1.save(path="demo.owl")
        # Check the axiom numbers
        abox = len([i for i in o1.get_abox_axioms()])
        tbox = len([i for i in o1.get_tbox_axioms()])

        o2 = SyncOntology(path="demo.owl")
        assert abox == len([i for i in o2.get_abox_axioms()])
        assert tbox == len([i for i in o2.get_tbox_axioms()])