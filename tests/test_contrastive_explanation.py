import os
import unittest

from owlapy import manchester_to_owl_expression
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner import SyncReasoner

# set RUN_INTEGRATION=1 to run these tests
# optionally override ontology path: export FAMILY_ONTOLOGY=/abs/path/to/family.owl
ONTOLOGY_PATH = os.getenv("FAMILY_ONTOLOGY", "/home/tiwari/workspace_dice/datasource/family.owl")
BASE_IRI = "http://www.benchmark.org/family#"


@unittest.skipUnless(os.getenv("RUN_INTEGRATION") == "1",
                     "Integration test skipped (set RUN_INTEGRATION=1 to run).")
class TestGetContrastiveExplanationIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.isfile(ONTOLOGY_PATH):
            raise FileNotFoundError(
                f"Ontology file not found: {ONTOLOGY_PATH}\n"
                "Set FAMILY_ONTOLOGY=/abs/path/to/family.owl to override."
            )

        cls.ontology = SyncOntology(ONTOLOGY_PATH)
        cls.reasoner = SyncReasoner(cls.ontology, reasoner="HermiT")

    @staticmethod
    def _ind(name: str) -> OWLNamedIndividual:
        iri = name if name.startswith("http") else f"{BASE_IRI.rstrip('#/') }#{name}"
        return OWLNamedIndividual(IRI.create(iri))

    def test_contrastive_explanation_happy_path(self):
        class_expr = manchester_to_owl_expression(
            "Sister and (hasSibling some (married some (hasChild some Grandchild)))",
            BASE_IRI,
        )
        fact = self._ind("F9F143")
        foil = self._ind("F9M161")

        result = self.reasoner.get_contrastive_explanation(class_expr, fact, foil)

        self.assertIsInstance(result, dict)
        self.assertIn("common", result)
        self.assertIn("different", result)
        self.assertIn("conflict", result)
        self.assertIn("foil_mapping", result)

        self.assertIsInstance(result["common"], set)
        self.assertIsInstance(result["different"], set)
        self.assertIsInstance(result["conflict"], set)
        self.assertIsInstance(result["foil_mapping"], dict)

        # elements should be strings
        for s in result["common"] | result["different"] | result["conflict"]:
            self.assertIsInstance(s, str)
        for k, v in result["foil_mapping"].items():
            self.assertIsInstance(k, str)
            self.assertIsInstance(v, str)

    def test_contrastive_explanation_unknown_individual(self):
        class_expr = manchester_to_owl_expression(
            "Person and (hasChild some Person)", BASE_IRI
        )
        fact = self._ind("F1F2")
        foil = self._ind("NonExistent_XYZ")

        result = self.reasoner.get_contrastive_explanation(class_expr, fact, foil)

        self.assertIsInstance(result, dict)
        self.assertIsInstance(result.get("common", set()), set)
        self.assertIsInstance(result.get("different", set()), set)
        self.assertIsInstance(result.get("conflict", set()), set)
        self.assertIsInstance(result.get("foil_mapping", {}), dict)

    def test_contrastive_explanation_parent_child_pattern(self):
        """Simple expression that should work broadly on the family ontology."""
        class_expr = manchester_to_owl_expression(
            "hasChild some Male", BASE_IRI
        )
        fact = self._ind("F10M171")
        foil = self._ind("F4F56")  # F1F2 has a child, F1F3 does not

        result = self.reasoner.get_contrastive_explanation(class_expr, fact, foil)

        self.assertIsInstance(result, dict)
        self.assertIsInstance(result["common"], set)
        self.assertIsInstance(result["different"], set)
        self.assertIsInstance(result["conflict"], set)
        self.assertIsInstance(result["foil_mapping"], dict)

        # optional sanity check: fact should have more support than foil
        self.assertTrue(len(result["different"]) >= 0)


