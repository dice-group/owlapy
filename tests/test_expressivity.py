import unittest

from owlapy import get_dl_expressivity
from owlapy.expressivity import get_dl_expressivity as get_dl_expressivity_direct
from owlapy.owl_ontology import SyncOntology


class TestExpressivity(unittest.TestCase):

    def test_father_ontology_expressivity(self):
        onto = SyncOntology("KGs/Family/father.owl")
        self.assertEqual(get_dl_expressivity(onto), "ALC")

    def test_biopax_ontology_expressivity(self):
        onto = SyncOntology("KGs/Biopax/biopax.owl")
        self.assertEqual(get_dl_expressivity(onto), "ALCHN(D)")
        self.assertEqual(onto.get_dl_expressivity(), "ALCHN(D)")

    def test_top_level_and_submodule_exports_agree(self):
        onto = SyncOntology("KGs/Family/father.owl")
        self.assertEqual(get_dl_expressivity(onto), get_dl_expressivity_direct(onto))

    def test_sync_ontology_convenience_method(self):
        onto = SyncOntology("KGs/Family/father.owl")
        self.assertEqual(onto.get_dl_expressivity(), "ALC")

    def test_rejects_non_syncontology(self):
        with self.assertRaises(TypeError):
            get_dl_expressivity("not an ontology")


if __name__ == "__main__":
    unittest.main()
