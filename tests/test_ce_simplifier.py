import unittest
from owlapy import namespaces, dl_to_owl_expression, owl_expression_to_dl
from owlapy.class_expression import OWLClass, OWLObjectUnionOf
from owlapy.iri import IRI
from owlapy.namespaces import Namespaces
from owlapy.utils import simplify_class_expression

class TestSimplifier(unittest.TestCase):
    ns = "http://example.org/"
    def test_repetition_removal(self):

        ce1 = "A ⊓ C ⊓ A" # ==> "A ⊓ C"
        ce2 = "A ⊔ C ⊔ A ⊔ C" # ==> "A ⊔ C"
        ce3 = "A ⊓ C ⊓ A ⊓ A ⊓ A" # ==> "A ⊓ C"
        ce4 = "A ⊓ A ⊔ A" # ==> "A"
        ce5 = "A ⊓ C ⊓ (A ⊓ A ⊔ A)" # ==> "A ⊓ C"

        ce6 = "A ⊓ (B ⊔ C) ⊓ (B ⊔ C)" # ==> "A ⊓ (B ⊔ C)"
        ce7 = "A ⊓ (∀r1.B ⊔ ¬C) ⊓ (∀r1.B ⊔ ¬C)" # ==> "A ⊓ (∀r1.B ⊔ ¬C)"

        self.assertEqual(owl_expression_to_dl(simplify_class_expression(dl_to_owl_expression(ce1, self.ns))), "A ⊓ C")
        self.assertEqual(owl_expression_to_dl(simplify_class_expression(dl_to_owl_expression(ce2, self.ns))), "A ⊔ C")
        self.assertEqual(owl_expression_to_dl(simplify_class_expression(dl_to_owl_expression(ce3, self.ns))), "A ⊓ C")
        self.assertEqual(owl_expression_to_dl(simplify_class_expression(dl_to_owl_expression(ce4, self.ns))), "A")
        self.assertEqual(owl_expression_to_dl(simplify_class_expression(dl_to_owl_expression(ce5, self.ns))), "A ⊓ C")
        self.assertEqual(owl_expression_to_dl(simplify_class_expression(dl_to_owl_expression(ce6, self.ns))), "A ⊓ (B ⊔ C)")
        self.assertEqual(owl_expression_to_dl(simplify_class_expression(dl_to_owl_expression(ce7, self.ns))), "A ⊓ ((¬C) ⊔ (∀ r1.B))")
