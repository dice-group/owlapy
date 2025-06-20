import unittest

from parsimonious.exceptions import IncompleteParseError

from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy import dl_to_owl_expression, manchester_to_owl_expression
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner import SyncReasoner


class TestCreateJustifications(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ontology_path = "E:/Workspace_Dice/DataSource/family.owl"
        cls.namespace = "http://www.benchmark.org/family#"
        try:
            cls.ontology = SyncOntology(cls.ontology_path)
            cls.reasoner = SyncReasoner(cls.ontology, reasoner="Pellet")
        except Exception as e:
            raise RuntimeError(f"Ontology setup failed: {str(e)}")

    def test_create_justifications_with_DL_syntax(self):
        individual = OWLNamedIndividual(IRI.create(self.namespace + "F10M171"))
        dl_expr_str = "∃ hasChild.Male"

        target_class = dl_to_owl_expression(dl_expr_str, self.namespace)
        justifications = self.reasoner.create_justifications({individual}, target_class)

        self.assertIsInstance(justifications, list, "Justifications should be a list.")
        for justification in justifications:
            self.assertIsInstance(justification, set, "Each justification should be a set.")

        # Fake individual
        fake_individual = OWLNamedIndividual(IRI.create(self.namespace + "NonExistentPerson"))
        justifications = self.reasoner.create_justifications({fake_individual}, target_class)
        self.assertEqual(len(justifications), 0, "Justifications for non-existent individual should be empty.")

        # Invalid DL expression
        with self.assertRaises(IncompleteParseError, msg="Invalid DL expression should raise exception."):
            invalid_expr = dl_to_owl_expression("invalid some Expression", self.namespace)
            self.reasoner.create_justifications(invalid_expr, target_class)

    def test_create_justifications_with_Fake_Individual_Invalid_DL_syntax(self):
        individual = OWLNamedIndividual(IRI.create(self.namespace + "F10M171"))
        dl_expr_str = "∃ hasChild.Male"
        target_class = dl_to_owl_expression(dl_expr_str, self.namespace)

        # Fake individual
        fake_individual = OWLNamedIndividual(IRI.create(self.namespace + "NonExistentPerson"))
        justifications = self.reasoner.create_justifications({fake_individual}, target_class)
        self.assertEqual(len(justifications), 0, "Justifications for non-existent individual should be empty.")

        # Invalid DL expression
        with self.assertRaises(IncompleteParseError, msg="Invalid DL expression should raise exception."):
            invalid_expr = dl_to_owl_expression("invalid some Expression", self.namespace)
            self.reasoner.create_justifications(invalid_expr, target_class)



    def test_create_justifications_with_Manchester_syntax(self):
        individual = OWLNamedIndividual(IRI.create(self.namespace + "F1F2"))
        manchester_expr_str = "hasChild some Female"

        target_class = manchester_to_owl_expression(manchester_expr_str, self.namespace)
        justifications = self.reasoner.create_justifications({individual}, target_class)


        self.assertIsInstance(justifications, list)
        for justification in justifications:
            self.assertIsInstance(justification, set)

    def test_create_justifications_with_Fake_Individual_Invalid_Manchester_syntax(self):
        individual = OWLNamedIndividual(IRI.create(self.namespace + "F10M171"))
        manchester_expr_str = "hasChild some Male"
        target_class = manchester_to_owl_expression(manchester_expr_str, self.namespace)

        # Fake individual
        fake_individual = OWLNamedIndividual(IRI.create(self.namespace + "Ghost123"))
        justifications = self.reasoner.create_justifications({fake_individual}, target_class)
        self.assertEqual(len(justifications), 0)

        # Invalid Manchester expression
        invalid_expr = manchester_to_owl_expression("invalid some Expression", self.namespace)
        justifications = self.reasoner.create_justifications({individual}, invalid_expr)
        self.assertEqual(len(justifications), 0, "Justifications for non-existent individual should be empty.")

    def test_create_justifications_empty_inputs(self):

        with self.assertRaises(ValueError):
            self.reasoner.create_justifications(None, None)

        with self.assertRaises(ValueError):
            self.reasoner.create_justifications(set(), None)

    def test_multiple_individuals_and_mixed_results(self):
        valid_individual = OWLNamedIndividual(IRI.create(self.namespace + "F10M171"))
        fake_individual = OWLNamedIndividual(IRI.create(self.namespace + "Ghost"))

        class_expr = dl_to_owl_expression("∃ hasChild.Male", self.namespace)
        justifications = self.reasoner.create_justifications({valid_individual, fake_individual}, class_expr)

        self.assertIsInstance(justifications, list)
        for justification in justifications:
            self.assertIsInstance(justification, set)


if __name__ == "__main__":
    unittest.main()
