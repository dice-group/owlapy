import os
import unittest

from owlapy import manchester_to_owl_expression
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner import SyncReasoner


DEFAULT_FAMILY = os.path.join("KGs", "Family", "family-benchmark_rich_background.owl")
ONTOLOGY_PATH = os.getenv("FAMILY_ONTOLOGY", DEFAULT_FAMILY)
BASE_IRI = "http://www.benchmark.org/family#"


class TestGetContrastiveExplanation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.isfile(ONTOLOGY_PATH):
            raise unittest.SkipTest(
                f"Ontology file not found: {ONTOLOGY_PATH}. "
                "Set FAMILY_ONTOLOGY=/abs/path/to/family.owl to run this test."
            )

        cls.ontology = SyncOntology(ONTOLOGY_PATH)
        cls.reasoner = SyncReasoner(cls.ontology, reasoner="HermiT")

    @staticmethod
    def _ind(name: str) -> OWLNamedIndividual:
        iri = name if name.startswith("http") else f"{BASE_IRI.rstrip('#/') }#{name}"
        return OWLNamedIndividual(IRI.create(iri))

    def _debug_print_on_mismatch(
        self,
        label: str,
        result: dict,
        expected_common: set,
        expected_different: set,
        expected_conflict: set,
        expected_foil_mapping: dict,
    ):
        if (
            result.get("common") != expected_common
            or result.get("different") != expected_different
            or result.get("conflict") != expected_conflict
            or result.get("foil_mapping") != expected_foil_mapping
        ):
            from pprint import pprint
            print(f"\n=== contrastive explanation mismatch ({label}) ===")
            pprint(
                {
                    "common": sorted(result.get("common", set())),
                    "different": sorted(result.get("different", set())),
                    "conflict": sorted(result.get("conflict", set())),
                    "foil_mapping": result.get("foil_mapping", {}),
                }
            )

    def test_contrastive_explanation_happy_path(self):
        class_expr = manchester_to_owl_expression(
            "Sister and (hasSibling some (married some (hasChild some Grandchild)))",
            BASE_IRI,
        )
        fact = self._ind("F9F143")
        foil = self._ind("F9M161")

        result = self.reasoner.get_contrastive_explanation(class_expr, fact, foil)

        expected_common = {
            "ObjectPropertyAssertion(<http://www.benchmark.org/family#hasChild> <_X11> <_X26>)",
            "ClassAssertion(<http://www.benchmark.org/family#Grandson> <_X26>)",
            "ObjectPropertyAssertion(<http://www.benchmark.org/family#married> <_X17> <_X11>)",
        }
        expected_different = {
            "ClassAssertion(<http://www.benchmark.org/family#Sister> <_X39>)",
            "ObjectPropertyAssertion(<http://www.benchmark.org/family#hasSibling> <_X39> <_X17>)",
        }
        expected_conflict = set()
        expected_foil_mapping = {
            "<_X11>": "<http://www.benchmark.org/family#F9M159>",
            "<_X26>": "<http://www.benchmark.org/family#F9M161>",
            "<_X17>": "<http://www.benchmark.org/family#F9F160>",
            "<_X39>": "<http://www.benchmark.org/family#F9M161>",
        }

        self._debug_print_on_mismatch(
            "happy_path",
            result,
            expected_common,
            expected_different,
            expected_conflict,
            expected_foil_mapping,
        )

        self.assertSetEqual(result["common"], expected_common)
        self.assertSetEqual(result["different"], expected_different)
        self.assertSetEqual(result["conflict"], expected_conflict)
        self.assertDictEqual(result["foil_mapping"], expected_foil_mapping)

    def test_contrastive_explanation_unknown_individual(self):
        class_expr = manchester_to_owl_expression("Person and (hasChild some Person)", BASE_IRI)
        fact = self._ind("F1F2")
        foil = self._ind("NonExistent_XYZ")

        result = self.reasoner.get_contrastive_explanation(class_expr, fact, foil)

        self.assertIsInstance(result, dict)
        self.assertIsInstance(result.get("common", set()), set)
        self.assertIsInstance(result.get("different", set()), set)
        self.assertIsInstance(result.get("conflict", set()), set)
        self.assertIsInstance(result.get("foil_mapping", {}), dict)

    def test_contrastive_explanation_parent_child_pattern(self):
        class_expr = manchester_to_owl_expression("hasChild some Male", BASE_IRI)
        fact = self._ind("F10M171")
        foil = self._ind("F4F56")

        result = self.reasoner.get_contrastive_explanation(class_expr, fact, foil)

        self.assertIsInstance(result, dict)
        self.assertIsInstance(result["common"], set)
        self.assertIsInstance(result["different"], set)
        self.assertIsInstance(result["conflict"], set)
        self.assertIsInstance(result["foil_mapping"], dict)

        atoms = result["common"] | result["different"] | result["conflict"]

        # Must mention hasChild somewhere in the explanation
        self.assertTrue(
            any("ObjectPropertyAssertion(<http://www.benchmark.org/family#hasChild>" in s for s in atoms),
            f"Expected a hasChild assertion in explanation, got: {sorted(atoms)}",
        )

        # Must mention some male-like type assertion (Male or common subclasses)
        male_like = ("#Male", "#Father", "#Brother", "#Husband", "#Grandfather", "#Son")
        self.assertTrue(
            any(("ClassAssertion(" in s and any(t in s for t in male_like)) for s in atoms),
            f"Expected a male-like ClassAssertion in explanation, got: {sorted(atoms)}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
