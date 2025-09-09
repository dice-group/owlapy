import unittest
from owlapy import dl_to_owl_expression, owl_expression_to_dl
from owlapy.class_expression import OWLObjectHasValue, OWLObjectSomeValuesFrom, OWLObjectOneOf, OWLObjectUnionOf, \
    OWLObjectIntersectionOf, OWLObjectMinCardinality
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_property import OWLObjectProperty
from owlapy.owl_reasoner import StructuralReasoner, SyncReasoner
from owlapy.utils import simplify_class_expression

class TestSimplifier(unittest.TestCase):
    ns = "http://example.org/"
    def test_repetition_removal(self):

        ce1 = "A ⊓ C ⊓ A"                                   # ==> "A ⊓ C"
        ce2 = "A ⊔ C ⊔ A ⊔ C"                               # ==> "A ⊔ C"
        ce3 = "A ⊓ C ⊓ A ⊓ A ⊓ A"                           # ==> "A ⊓ C"
        ce4 = "A ⊓ A ⊔ A"                                   # ==> "A"
        ce5 = "A ⊓ C ⊓ (A ⊓ A ⊔ A)"                         # ==> "A ⊓ C"
        ce6 = "A ⊓ (B ⊔ C) ⊓ (B ⊔ C)"                       # ==> "A ⊓ (B ⊔ C)"
        ce7 = "A ⊓ (∀r1.B ⊔ ¬C) ⊓ (∀r1.B ⊔ ¬C)"             # ==> "A ⊓ (∀r1.B ⊔ ¬C)"
        ce8 = "A ⊓ (B ⊔ C) ⊓ (B ⊔ C) ⊓ (B ⊔ C) ⊓ (B ⊔ C)"   # ==> "A ⊓ (B ⊔ C)"
        ce9 = "((B ⊔ C) ⊓ (B ⊔ C)) ⊔ ((B ⊔ C) ⊓ (B ⊔ C))"   # ==> "B ⊔ C"
        ce10 = "A ⊔ (B ⊓ C) ⊔ A"                            # ==> "A ⊔ (B ⊓ C)"
        ce11 = "(A ⊓ B) ⊔ (A ⊓ B) ⊔ C"                      # ==> "(A ⊓ B) ⊔ C"
        ce12 = "(A ⊓ (B ⊔ C)) ⊓ (A ⊓ (B ⊔ C))"              # ==> "A ⊓ (B ⊔ C)"
        ce13 = "(A ⊓ B) ⊓ (B ⊓ A)"                          # ==> "A ⊓ B"
        ce14 = "(∀r.A ⊓ ∃s.B) ⊓ (∃s.B ⊓ ∀r.A)"              # ==> "(∃ s.B) ⊓ (∀ r.A)"
        ce15 = "(A ⊔ B) ⊓ (A ⊔ B) ⊔ C ⊔ (A ⊔ B)"            # ==> "A ⊔ B ⊔ C"
        ce16 = "((A ⊓ B) ⊔ C) ⊔ ((A ⊓ B) ⊔ C)"              # ==> "C ⊔ (A ⊓ B)"
        ce17 = "A ⊓ (B ⊔ C ⊔ B ⊔ C) ⊓ A ⊓ (B ⊔ C)"          # ==> "A ⊓ (B ⊔ C)"

        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce1, self.ns)),
                         dl_to_owl_expression("A ⊓ C", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce2, self.ns)),
                         dl_to_owl_expression("A ⊔ C", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce3, self.ns)),
                         dl_to_owl_expression("A ⊓ C", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce4, self.ns)),
                         dl_to_owl_expression("A", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce5, self.ns)),
                         dl_to_owl_expression("A ⊓ C", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce6, self.ns)),
                         dl_to_owl_expression("A ⊓ (B ⊔ C)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce7, self.ns)),
                         dl_to_owl_expression("A ⊓ ((¬C) ⊔ (∀ r1.B))", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce8, self.ns)),
                         dl_to_owl_expression("A ⊓ (B ⊔ C)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce9, self.ns)),
                         dl_to_owl_expression("B ⊔ C", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce10, self.ns)),
                         dl_to_owl_expression("A ⊔ (B ⊓ C)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce11, self.ns)),
                         dl_to_owl_expression("C ⊔ (A ⊓ B)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce12, self.ns)),
                         dl_to_owl_expression("A ⊓ (B ⊔ C)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce13, self.ns)),
                         dl_to_owl_expression("A ⊓ B", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce14, self.ns)),
                         dl_to_owl_expression("(∃ s.B) ⊓ (∀ r.A)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce15, self.ns)),
                         dl_to_owl_expression("A ⊔ B ⊔ C", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce16, self.ns)),
                         dl_to_owl_expression("C ⊔ (A ⊓ B)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce17, self.ns)),
                         dl_to_owl_expression("A ⊓ (B ⊔ C)", self.ns))


    def test_nnf(self):

        ce1 = "¬(¬A)"                   # ==> "A"
        ce2 = "¬(¬(¬C))"                # ==> "¬C"
        ce3 = "¬(A ⊓ B)"                # ==> "(¬A) ⊔ (¬B)"
        ce4 = "¬(A ⊔ B)"                # ==> "(¬A) ⊓ (¬B)"
        ce5 = "¬(∀ r.C)"                # ==> "∃ r.(¬C)"
        ce6 = "¬(∃ r.C)"                # ==> "∀ r.(¬C)"
        ce7 = "¬⊤"                      # ==> "⊥"
        ce8 = "¬⊥"                      # ==> "⊤"
        ce9 = "¬(A ⊓ (B ⊔ C))"          # ==> "(¬A) ⊔ ((¬B) ⊓ (¬C))"
        ce10 = "¬((A ⊓ B) ⊔ C)"         # ==> "(¬C) ⊓ ((¬A) ⊔ (¬B))"
        ce11 = "¬(∀ r.(A ⊓ B))"         # ==> "∃ r.((¬A) ⊔ (¬B))"
        ce12 = "¬(∃ r.(A ⊔ B))"         # ==> "∀ r.((¬A) ⊓ (¬B))"
        ce13 = "¬(∀ r.∃ s.A)"           # ==> "∃ r.(∀ s.(¬A))"
        ce14 = "¬(∃ r.∀ s.B)"           # ==> "∀ r.(∃ s.(¬B))"
        ce15 = "¬(¬(A ⊔ ¬B))"           # ==> "A ⊔ (¬B)"
        ce16 = "¬((∀ r.A) ⊓ (∃ s.B))"   # ==> "(∀ s.(¬B)) ⊔ (∃ r.(¬A))"
        ce17 = "¬((∃ r.A) ⊔ (∀ s.B))"   # ==> "(∀ r.(¬A)) ⊓ (∃ s.(¬B))"
        ce18 = "¬(∀ r.(A ⊔ ∃ s.B))"     # ==> "∃ r.((¬A) ⊓ (∀ s.(¬B)))"
        ce19 = "¬(∃ r.(A ⊓ ∀ s.B))"     # ==> "∀ r.((¬A) ⊔ (∃ s.(¬B)))"
        ce20 = "¬((A ⊓ B) ⊔ (∀ r.C))"   # ==> "((¬A) ⊔ (¬B)) ⊓ (∃ r.(¬C))"

        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce1, self.ns)),
                         dl_to_owl_expression("A", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce2, self.ns)),
                         dl_to_owl_expression("¬C", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce3, self.ns)),
                         dl_to_owl_expression("(¬A) ⊔ (¬B)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce4, self.ns)),
                         dl_to_owl_expression("(¬A) ⊓ (¬B)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce5, self.ns)),
                         dl_to_owl_expression("∃ r.(¬C)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce6, self.ns)),
                         dl_to_owl_expression("∀ r.(¬C)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce7, self.ns)),
                         dl_to_owl_expression("⊥", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce8, self.ns)),
                         dl_to_owl_expression("⊤", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce9, self.ns)),
                         dl_to_owl_expression("((¬B) ⊓ (¬C)) ⊔ (¬A)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce10, self.ns)),
                         dl_to_owl_expression("((¬A) ⊔ (¬B)) ⊓ (¬C)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce11, self.ns)),
                         dl_to_owl_expression("∃ r.((¬A) ⊔ (¬B))", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce12, self.ns)),
                         dl_to_owl_expression("∀ r.((¬A) ⊓ (¬B))", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce13, self.ns)),
                         dl_to_owl_expression("∃ r.(∀ s.(¬A))", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce14, self.ns)),
                         dl_to_owl_expression("∀ r.(∃ s.(¬B))", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce15, self.ns)),
                         dl_to_owl_expression("A ⊔ (¬B)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce16, self.ns)),
                         dl_to_owl_expression("(∃ r.(¬A)) ⊔ (∀ s.(¬B))", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce17, self.ns)),
                         dl_to_owl_expression("(∃ s.(¬B)) ⊓ (∀ r.(¬A))", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce18, self.ns)),
                         dl_to_owl_expression("∃ r.((¬A) ⊓ (∀ s.(¬B)))", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce19, self.ns)),
                         dl_to_owl_expression("∀ r.((¬A) ⊔ (∃ s.(¬B)))", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce20, self.ns)),
                         dl_to_owl_expression("((¬A) ⊔ (¬B)) ⊓ (∃ r.(¬C))", self.ns))


    def test_absorption_law(self):
        ce1 = "A ⊔ (A ⊓ B)"              # ==> "A"
        ce2 = "A ⊓ (A ⊓ B)"              # ==> "A"
        ce3 = "A ⊓ (B ⊔ (A ⊓ B))"        # ==> "A ⊓ B"
        ce4 = "A ⊔ (A ⊓ (B ⊔ C))"        # ==> "A"
        ce5 = "(A ⊓ B) ⊔ (A ⊓ (B ⊔ C))"  # ==> "A ⊓ (B ⊔ C)"
        ce6 = "(A ⊔ B) ⊓ (A ⊔ (B ⊓ C))"  # ==> "A ⊔ (B ⊓ C)"
        ce7 = "A ⊔ (A ⊓ ∃r.B)"           # ==> "A"
        ce8 = "((∀r.A ⊓ ∃r.A) ⊔ ∀r.A)"   # ==> "∀ r.A"
        ce9 = "A ⊓ (B ⊔ (A ⊓ C))"        # ==> "A ⊓ (B ⊔ C)"
        ce10 = "(A ⊓ (B ⊔ A)) ⊔ C"       # ==> "A ⊔ C"
        ce11 = "(A ⊔ (B ⊓ A)) ⊓ D"       # ==> "A ⊓ D"
        ce12 = "(A ⊔ B) ⊓ ((A ⊔ B) ⊔ C)" # ==> "A ⊔ B"
        ce13 = "((A ⊔ (B ⊓ C)) ⊓ (A ⊔ B)) ⊓ (A ⊔ (B ⊓ C))"                  # ==> "A ⊔ (B ⊓ C)"
        ce14 = "A ⊓ (B ⊔ (A ⊓ ((A ⊔ (B ⊓ C)) ⊓ (A ⊔ B)) ⊓ (A ⊔ (B ⊓ C))))"  # ==> "A"
        ce15 = "A ⊓ ((A ⊔ (E ⊔ D)) ⊓ B)"

        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce1, self.ns)),
                         dl_to_owl_expression("A", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce2, self.ns)),
                         dl_to_owl_expression("A ⊓ B", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce3, self.ns)),
                         dl_to_owl_expression("A ⊓ B", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce4, self.ns)),
                         dl_to_owl_expression("A", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce5, self.ns)),
                         dl_to_owl_expression("A ⊓ (B ⊔ C)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce6, self.ns)),
                         dl_to_owl_expression("A ⊔ (B ⊓ C)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce7, self.ns)),
                         dl_to_owl_expression("A", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce8, self.ns)),
                         dl_to_owl_expression("∀ r.A", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce9, self.ns)),
                         dl_to_owl_expression("A ⊓ (B ⊔ C)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce10, self.ns)),
                         dl_to_owl_expression("A ⊔ C", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce11, self.ns)),
                         dl_to_owl_expression("A ⊓ D", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce12, self.ns)),
                         dl_to_owl_expression("A ⊔ B", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce13, self.ns)),
                         dl_to_owl_expression("A ⊔ (B ⊓ C)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce14, self.ns)),
                         dl_to_owl_expression("A", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce15, self.ns)),
                         dl_to_owl_expression("A ⊓ B", self.ns))

    def test_simplification_through_factorization(self):
        ce1 = "(A ⊓ B) ⊔ (A ⊓ B)"  # ==> "A ⊓ B"
        ce2 = "(A ⊓ B) ⊔ (A ⊓ C)"  # ==> "A ⊓ (B ⊔ C)"
        ce3 = "(A ⊔ B) ⊓ (A ⊔ B)"  # ==> "A ⊓ B"
        ce4 = "(A ⊔ B) ⊓ (A ⊔ C)"  # ==> "A ⊔ (B ⊓ C)"
        ce5 = "(A ⊔ B) ⊓ (C ⊔ E)"  # ==> "(A ⊔ B) ⊓ (C ⊔ E)" (same)
        ce6 = "((∀ r.A) ⊓ (∃ r.B)) ⊔ ((∀ r.B) ⊓ (∃ r.A))"  # ==> "((∃ r.A) ⊓ (∀ r.B)) ⊔ ((∃ r.B) ⊓ (∀ r.A))" (same)
        ce7 = "(A ⊓ B) ⊔ (A ⊓ B ⊓ E)"  # ==> "A ⊓ B"
        ce8 = "(A ⊓ B) ⊓ (A ⊓ (B ⊓ (C ⊔ E)))"  # ==> "A ⊓ B ⊓ (C ⊔ E)"
        ce9 = "(A ⊓ B) ⊓ (C ⊓ (B ⊔ (C ⊔ E)))"  # ==> "A ⊓ B ⊓ C"
        ce10 = "(∀r_2.⊥) ⊓ (∀r_2.¬C)" # ==> ∀ r_2.(⊥ ⊓ (¬C))
        ce11 = "(∀r_1.∀r_2.∀r_3.⊥) ⊓ (∀r_1.∀r_2.¬C)" # ==> "∀ r_1.(∀ r_2.((¬C) ⊓ (∀ r_3.⊥)))"
        ce12 = "(∀r_1.∀r_2.∀r_3.(¬⊥ ⊔ B ⊔ E)) ⊓ (∀r_1.∀r_2.¬(C ⊔ (C ⊓ B)))" # ==> "∀ r_1.(∀ r_2.((¬C) ⊓ (∀ r_3.⊤)))"

        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce1, self.ns)),
                         dl_to_owl_expression("A ⊓ B", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce2, self.ns)),
                         dl_to_owl_expression("A ⊓ (B ⊔ C)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce3, self.ns)),
                         dl_to_owl_expression("A ⊔ B", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce4, self.ns)),
                         dl_to_owl_expression("A ⊔ (B ⊓ C)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce5, self.ns)),
                         dl_to_owl_expression("(A ⊔ B) ⊓ (C ⊔ E)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce6, self.ns)),
                         dl_to_owl_expression("((∃ r.A) ⊓ (∀ r.B)) ⊔ ((∃ r.B) ⊓ (∀ r.A))", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce7, self.ns)),
                         dl_to_owl_expression("A ⊓ B", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce8, self.ns)),
                         dl_to_owl_expression("A ⊓ B ⊓ (C ⊔ E)", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce9, self.ns)),
                         dl_to_owl_expression("A ⊓ B ⊓ C", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce10, self.ns)),
                         dl_to_owl_expression("∀ r_2.(⊥ ⊓ (¬C))", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce11, self.ns)),
                         dl_to_owl_expression("∀ r_1.(∀ r_2.((¬C) ⊓ (∀ r_3.⊥)))", self.ns))
        self.assertEqual(simplify_class_expression(dl_to_owl_expression(ce12, self.ns)),
                         dl_to_owl_expression("∀ r_1.(∀ r_2.((¬C) ⊓ (∀ r_3.⊤)))", self.ns))

    def test_other_stuff(self):
        ce1 = "A ⊔ (¬A)" # ==> ⊤ (Law of the excluded middle)
        ce2 = "A ⊓ (¬A)" # ==> ⊥ (Law of non-contradiction)
        ce3 = "¬(A ⊓ (¬A))" # ==> ⊤
        ce4 = "¬(A ⊔ (¬A))" # ==> ⊥

        self.assertEqual("⊤",owl_expression_to_dl(simplify_class_expression(dl_to_owl_expression(ce1, self.ns))))
        self.assertEqual("⊥",owl_expression_to_dl(simplify_class_expression(dl_to_owl_expression(ce2, self.ns))))
        self.assertEqual("⊤",owl_expression_to_dl(simplify_class_expression(dl_to_owl_expression(ce3, self.ns))))
        self.assertEqual('⊥',owl_expression_to_dl(simplify_class_expression(dl_to_owl_expression(ce4, self.ns))))


    def test_simplifier_robustness(self):
        # use reasoner to check if instances of simplified(C) == instances of C
        family_reasoner = StructuralReasoner("KGs/Family/family-benchmark_rich_background.owl")
        carcino_reasoner = StructuralReasoner("KGs/Carcinogenesis/carcinogenesis.owl")
        carcino_syncreasoner = SyncReasoner("KGs/Carcinogenesis/carcinogenesis.owl")
        NS = "http://www.benchmark.org/family#"
        ns_carcino = "http://dl-learner.org/carcinogenesis#"


        # Family class expressions
        ce1 = "Child ⊓ Brother ⊓ Child ⊓ Child ⊓ Brother" # ==> "Child ⊓ Brother"
        ce2 = "((Father ⊔ Brother) ⊓ (Father ⊔ Brother)) ⊔ ((Father ⊔ Brother) ⊓ (Father ⊔ Brother))"   # ==> "Father ⊔ Brother"
        ce3 = "(∀hasChild.Male ⊓ ∃married.Female) ⊓ (∃married.Female ⊓ ∀hasChild.Male)"  # ==> "(∃ married.Female) ⊓ (∀ hasChild.Male)"
        ce4 = "¬((∀ hasChild.Male) ⊓ (∃ married.Female))"   # ==> "(∀ married.(¬Female)) ⊔ (∃ hasChild.(¬Male))"
        ce5 = "(∀married.∀hasChild.∀hasSibling.(¬⊥ ⊔ Female ⊔ Male)) ⊓ (∀married.∀hasChild.¬(Daughter ⊔ (Daughter ⊓ Female)))" # ==> "∀ married.(∀ hasChild.((¬Daughter) ⊓ (∀ hasSibling.⊥)))"
        ce6 = "¬(Male ⊓ (¬Male))"  # ==> ⊤
        ce7 = "¬(Male ⊔ (¬Male))"  # ==> ⊥
        ce8 = "(Male ⊓ Child) ⊓ (Male ⊓ (Child ⊓ (Son ⊔ Brother)))"  # ==> "Male ⊓ Child ⊓ (Son ⊔ Brother)"

        # Carcino class expressions
        ce9 = "(∃ charge.xsd:double[≥ 0.1]) ⊓ (∃ charge.xsd:double[< 0.2])" # ==> ∃ charge.(xsd:double[< 0.2] ⊓ xsd:double[≥ 0.1])
        ce10 = "∃ charge.xsd:integer[> 1 ⊓ > 2 ⊓ > 3]" # ==> ∃ charge.∃ charge.xsd:integer[> 3]
        ce11 = "({d156_1 ⊔ d156_10 ⊔ d156_19}) ⊔ ({d156_11 ⊔ d156_10})" # ==> "{d156_1 ⊔ d156_10 ⊔ d156_19 ⊔ d156_11}"
        ce12 = "({d156_1 ⊔ d156_10 ⊔ d156_19}) ⊓ ({d156_11 ⊔ d156_10})" # ==> "{d156_10}"
        ce15 = "({d156_1 ⊔ d156_11 ⊔ d156_19}) ⊔ (({d156_11 ⊔ d156_1 ⊔ d156_10}) ⊓ Oxygen-50)" # ==> "{d156_1 ⊔ d156_11 ⊔ d156_19} ⊔ ({d156_10} ⊓ Oxygen-50)"
        ce16 = "({d156_1 ⊔ d156_11 ⊔ d156_19}) ⊓ (({d156_11 ⊔ d156_1 ⊔ d156_10}) ⊓ Oxygen-50)" # ==> "({d156_11 ⊔ d156_1}) ⊓ (Oxygen-50)"
        ce17 = "(∃ charge.xsd:double[≥ 0.1]) ⊓ (∃ charge.xsd:double[≥  0.15])" # ==> ∃ charge.xsd:double[≥ 0.15]
        ce18 = "(∃ charge.xsd:double[≥ 0.1]) ⊔ (∃ charge.xsd:double[≥  0.15])" # ==> ∃ charge.xsd:double[≥ 0.1]
        ce21 = "≤ 0 cytogen_ca.xsd:boolean ⊔ ≤ 2 cytogen_ca.xsd:boolean"
        ce22 = "≤ 0 cytogen_ca.xsd:boolean ⊓ ≤ 2 cytogen_ca.xsd:boolean"
        ce23 = "(((((((((((((((¬(∃ amesTestPositive.{true})) ⊓ (¬(∃ chromaberr.{false}))) ⊓ (¬(≥ 20 hasAtom.Hydrogen-3))) ⊓ (¬(∃ hasStructure.Ketone))) ⊓ (≥ 2 hasStructure.Methyl)) ⊔ (((((((((((¬(∃ amesTestPositive.{true})) ⊓ (¬(∃ chromaberr.{false}))) ⊓ (¬(≥ 20 hasAtom.Hydrogen-3))) ⊓ (¬(∃ hasStructure.Ketone))) ⊓ (¬(≥ 2 hasStructure.Methyl))) ⊓ (¬(∃ cytogen_sce.{false}))) ⊓ (¬(∃ hasStructure.Halide10))) ⊓ (¬(∃ mouse_lymph.{false}))) ⊓ (¬(∃ hasAtom.Chlorine-93))) ⊓ (∃ mouse_lymph.{true})) ⊓ (¬(∃ hasStructure.{six_ring-874})))) ⊔ ((((((¬(∃ amesTestPositive.{true})) ⊓ (¬(∃ chromaberr.{false}))) ⊓ (¬(≥ 20 hasAtom.Hydrogen-3))) ⊓ (∃ hasStructure.Ketone)) ⊓ (¬(≥ 4 hasStructure.Methyl))) ⊓ (∃ hasStructure.{ester-486}))) ⊔ (((((((¬(∃ amesTestPositive.{true})) ⊓ (¬(∃ chromaberr.{false}))) ⊓ (¬(≥ 20 hasAtom.Hydrogen-3))) ⊓ (∃ hasStructure.Ketone)) ⊓ (¬(≥ 4 hasStructure.Methyl))) ⊓ (¬(∃ hasStructure.{ester-486}))) ⊓ (∃ hasAtom.{d201_9}))) ⊔ ((((((((¬(∃ amesTestPositive.{true})) ⊓ (¬(∃ chromaberr.{false}))) ⊓ (¬(≥ 20 hasAtom.Hydrogen-3))) ⊓ (¬(∃ hasStructure.Ketone))) ⊓ (¬(≥ 2 hasStructure.Methyl))) ⊓ (∃ cytogen_sce.{false})) ⊓ (¬(∃ hasAtom.{d204_6}))) ⊓ (∃ hasBond.{bond317}))) ⊔ ((((∃ amesTestPositive.{true}) ⊓ (¬(∃ hasBond.{bond2415}))) ⊓ (¬(≥ 6 hasAtom.Chlorine-93))) ⊓ (¬(∃ hasBond.{bond3313})))) ⊔ ((((((((¬(∃ amesTestPositive.{true})) ⊓ (¬(∃ chromaberr.{false}))) ⊓ (¬(≥ 20 hasAtom.Hydrogen-3))) ⊓ (¬(∃ hasStructure.Ketone))) ⊓ (¬(≥ 2 hasStructure.Methyl))) ⊓ (¬(∃ cytogen_sce.{false}))) ⊓ (¬(∃ hasStructure.Halide10))) ⊓ (∃ mouse_lymph.{false}))) ⊔ (((((¬(∃ amesTestPositive.{true})) ⊓ (¬(∃ chromaberr.{false}))) ⊓ (¬(≥ 20 hasAtom.Hydrogen-3))) ⊓ (∃ hasStructure.Ketone)) ⊓ (≥ 4 hasStructure.Methyl))) ⊔ (((((((¬(∃ amesTestPositive.{true})) ⊓ (¬(∃ chromaberr.{false}))) ⊓ (¬(≥ 20 hasAtom.Hydrogen-3))) ⊓ (¬(∃ hasStructure.Ketone))) ⊓ (¬(≥ 2 hasStructure.Methyl))) ⊓ (∃ cytogen_sce.{false})) ⊓ (∃ hasAtom.{d204_6}))) ⊔ (((¬(∃ amesTestPositive.{true})) ⊓ (∃ chromaberr.{false})) ⊓ (¬(∃ hasAtom.Titanium-134)))) ⊔ (((¬(∃ amesTestPositive.{true})) ⊓ (¬(∃ chromaberr.{false}))) ⊓ (≥ 20 hasAtom.Hydrogen-3))) ⊔ (((((((¬(∃ amesTestPositive.{true})) ⊓ (¬(∃ chromaberr.{false}))) ⊓ (¬(≥ 20 hasAtom.Hydrogen-3))) ⊓ (¬(∃ hasStructure.Ketone))) ⊓ (¬(≥ 2 hasStructure.Methyl))) ⊓ (¬(∃ cytogen_sce.{false}))) ⊓ (∃ hasStructure.Halide10))"
        ce23_simplified = "((((((((((((∃ hasAtom.{d204_6}) ⊓ (∃ cytogen_sce.{false})) ⊔ ((∃ hasStructure.Halide10) ⊓ (∀ cytogen_sce.¬{false})) ⊔ ((∀ hasStructure.(¬Halide10)) ⊓ (∃ mouse_lymph.{false}) ⊓ (∀ cytogen_sce.¬{false}))) ⊓ (≤ 1 hasStructure.Methyl)) ⊔ (≥ 2 hasStructure.Methyl)) ⊓ (∀ hasStructure.(¬Ketone))) ⊔ ((((∃ hasStructure.{ester-486}) ⊓ (≤ 3 hasStructure.Methyl)) ⊔ (≥ 4 hasStructure.Methyl)) ⊓ (∃ hasStructure.Ketone)) ⊔ ((∃ hasAtom.{d201_9}) ⊓ (∃ hasStructure.Ketone) ⊓ (∀ hasStructure.(¬{ester-486})) ⊓ (≤ 3 hasStructure.Methyl)) ⊔ ((∃ hasBond.{bond317}) ⊓ (∀ hasAtom.(¬{d204_6})) ⊓ (∀ hasStructure.(¬Ketone)) ⊓ (≤ 1 hasStructure.Methyl) ⊓ (∃ cytogen_sce.{false})) ⊔ ((∀ hasAtom.(¬Chlorine-93)) ⊓ (∀ hasStructure.((¬Halide10) ⊓ (¬Ketone) ⊓ (¬{six_ring-874}))) ⊓ (≤ 1 hasStructure.Methyl) ⊓ (∃ mouse_lymph.{true}) ⊓ (∀ cytogen_sce.¬{false}) ⊓ (∀ mouse_lymph.¬{false}))) ⊓ (≤ 19 hasAtom.Hydrogen-3)) ⊔ (≥ 20 hasAtom.Hydrogen-3)) ⊓ (∀ chromaberr.¬{false})) ⊔ ((∀ hasAtom.(¬Titanium-134)) ⊓ (∃ chromaberr.{false}))) ⊓ (∀ amesTestPositive.¬{true})) ⊔ ((∀ hasBond.(¬{bond2415})) ⊓ (∀ hasBond.(¬{bond3313})) ⊓ (≤ 5 hasAtom.Chlorine-93) ⊓ (∃ amesTestPositive.{true}))"
        ce24 = "(¬{d156_1} ⊔ ¬{d156_10} ⊔ ¬{d156_19}) ⊓ (¬{d156_1 ⊔ d156_10})"


        self.assertCountEqual(family_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce1, NS))),
                              family_reasoner.instances(dl_to_owl_expression("Child ⊓ Brother", NS)))
        self.assertCountEqual(family_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce2, NS))),
                              family_reasoner.instances(dl_to_owl_expression("Father ⊔ Brother", NS)))
        self.assertCountEqual(family_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce3, NS))),
                              family_reasoner.instances(dl_to_owl_expression("(∃ married.Female) ⊓ (∀ hasChild.Male)", NS)))
        self.assertCountEqual(family_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce4, NS))),
                              family_reasoner.instances(dl_to_owl_expression("(∀ married.(¬Female)) ⊔ (∃ hasChild.(¬Male))", NS)))
        self.assertCountEqual(family_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce5, NS))),
                              family_reasoner.instances(dl_to_owl_expression("∀ married.(∀ hasChild.((¬Daughter) ⊓ (∀ hasSibling.⊤)))", NS)))
        self.assertCountEqual(family_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce6, NS))),
                              family_reasoner.instances(dl_to_owl_expression("⊤", NS)))
        self.assertCountEqual(family_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce7, NS))),
                              family_reasoner.instances(dl_to_owl_expression("⊥", NS)))
        self.assertCountEqual(family_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce8, NS))),
                              family_reasoner.instances(dl_to_owl_expression("Male ⊓ Child ⊓ (Son ⊔ Brother)", NS)))

        # checking dataproperty-related ces in carcino
        self.assertCountEqual(carcino_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce9, ns_carcino))),
                              carcino_reasoner.instances(dl_to_owl_expression("∃ charge.(xsd:double[< 0.2] ⊓ xsd:double[≥ 0.1])", ns_carcino)))
        self.assertCountEqual(carcino_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce10, ns_carcino))),
                              carcino_reasoner.instances(dl_to_owl_expression("∃ charge.∃ charge.xsd:integer[> 3]", ns_carcino)))
        self.assertCountEqual(carcino_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce11, ns_carcino))),
                              carcino_reasoner.instances(dl_to_owl_expression("{d156_1 ⊔ d156_10 ⊔ d156_19 ⊔ d156_11}", ns_carcino)))
        self.assertCountEqual(carcino_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce12, ns_carcino))),
                              carcino_reasoner.instances(dl_to_owl_expression("{d156_10}", ns_carcino)))

        hv1 = OWLObjectHasValue(property=OWLObjectProperty("http://dl-learner.org/carcinogenesis#hasAtom"),
                               individual=OWLNamedIndividual(
                                   IRI.create("http://dl-learner.org/carcinogenesis#d156_10")))
        hv2 = OWLObjectHasValue(property=OWLObjectProperty("http://dl-learner.org/carcinogenesis#hasAtom"),
                               individual=OWLNamedIndividual(
                                   IRI.create("http://dl-learner.org/carcinogenesis#d156_10")))
        sv1 = OWLObjectSomeValuesFrom(property=OWLObjectProperty("http://dl-learner.org/carcinogenesis#hasAtom"),
                                      filler=OWLObjectOneOf([OWLNamedIndividual(
                                          IRI.create("http://dl-learner.org/carcinogenesis#d156_10")),
                                                             OWLNamedIndividual(IRI.create(
                                                                 "http://dl-learner.org/carcinogenesis#d156_11"))]))
        sv2 = OWLObjectSomeValuesFrom(property=OWLObjectProperty("http://dl-learner.org/carcinogenesis#hasAtom"),
                                      filler=OWLObjectOneOf([OWLNamedIndividual(
                                          IRI.create("http://dl-learner.org/carcinogenesis#d156_10")),
                                                             OWLNamedIndividual(IRI.create(
                                                                 "http://dl-learner.org/carcinogenesis#d156_12"))]))
        c13 = OWLObjectUnionOf([hv1, hv2, sv1, sv2])
        c14 = OWLObjectIntersectionOf([hv1, hv2, sv1, sv2])

        self.assertCountEqual(
            carcino_reasoner.instances(simplify_class_expression(c13)),
            carcino_reasoner.instances(dl_to_owl_expression("∃ hasAtom.{d156_10 ⊔ d156_12 ⊔ d156_11}", ns_carcino)))
        self.assertCountEqual(
            carcino_reasoner.instances(simplify_class_expression(c14)),
            carcino_reasoner.instances(dl_to_owl_expression("∃ hasAtom.{d156_10}", ns_carcino)))

        self.assertCountEqual(
            carcino_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce15, ns_carcino))),
            carcino_reasoner.instances(dl_to_owl_expression("{d156_1 ⊔ d156_11 ⊔ d156_19} ⊔ ({d156_10} ⊓ Oxygen-50)", ns_carcino)))
        self.assertCountEqual(
            carcino_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce16, ns_carcino))),
            carcino_reasoner.instances(dl_to_owl_expression("({d156_11 ⊔ d156_1}) ⊓ (Oxygen-50)", ns_carcino)))
        self.assertCountEqual(
            carcino_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce17, ns_carcino))),
            carcino_reasoner.instances(dl_to_owl_expression("∃ charge.xsd:double[≥ 0.15]", ns_carcino)))
        self.assertCountEqual(
            carcino_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce18, ns_carcino))),
            carcino_reasoner.instances(dl_to_owl_expression("∃ charge.xsd:double[≥ 0.1]", ns_carcino)))

        omc1 = OWLObjectMinCardinality(2, property=OWLObjectProperty("http://dl-learner.org/carcinogenesis#hasAtom"),
                                      filler=OWLObjectOneOf([OWLNamedIndividual(
                                          IRI.create("http://dl-learner.org/carcinogenesis#d156_10")),
                                                             OWLNamedIndividual(IRI.create(
                                                                 "http://dl-learner.org/carcinogenesis#d156_11")),
                                                             OWLNamedIndividual(IRI.create(
                                                                 "http://dl-learner.org/carcinogenesis#d156_12"))]))
        omc2 = OWLObjectMinCardinality(20, property=OWLObjectProperty("http://dl-learner.org/carcinogenesis#hasAtom"),
                                      filler=OWLObjectOneOf([OWLNamedIndividual(
                                          IRI.create("http://dl-learner.org/carcinogenesis#d156_10")),
                                                             OWLNamedIndividual(IRI.create(
                                                                 "http://dl-learner.org/carcinogenesis#d156_11")),
                                                             OWLNamedIndividual(IRI.create(
                                                                 "http://dl-learner.org/carcinogenesis#d156_12"))]))
        ce19 = OWLObjectUnionOf([omc1, omc2])
        ce20 = OWLObjectIntersectionOf([omc1, omc2])

        self.assertCountEqual(
            carcino_reasoner.instances(simplify_class_expression(ce19)),
            carcino_reasoner.instances(dl_to_owl_expression("≥ 2 hasAtom.{d156_11 ⊔ d156_10 ⊔ d156_12}", ns_carcino)))

        self.assertCountEqual(
            carcino_reasoner.instances(simplify_class_expression(ce20)),
            carcino_reasoner.instances(dl_to_owl_expression("≥ 20 hasAtom.{d156_11 ⊔ d156_10 ⊔ d156_12}", ns_carcino)))

        self.assertCountEqual(
            carcino_syncreasoner.instances(simplify_class_expression(dl_to_owl_expression(ce21, ns_carcino))),
            carcino_syncreasoner.instances(dl_to_owl_expression("≤ 2 cytogen_ca.xsd:boolean", ns_carcino)))

        self.assertCountEqual(
            carcino_syncreasoner.instances(simplify_class_expression(dl_to_owl_expression(ce22, ns_carcino))),
            carcino_syncreasoner.instances(dl_to_owl_expression("≤ 0 cytogen_ca.xsd:boolean", ns_carcino)))

        self.assertCountEqual(
            carcino_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce23, ns_carcino))),
            carcino_reasoner.instances(dl_to_owl_expression(ce23_simplified, ns_carcino))
        )

        self.assertCountEqual(
            carcino_reasoner.instances(simplify_class_expression(dl_to_owl_expression(ce24, ns_carcino))),
            carcino_reasoner.instances(dl_to_owl_expression("(¬{d156_1 ⊔ d156_10})", ns_carcino)))