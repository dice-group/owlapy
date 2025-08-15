import unittest
from owlapy import dl_to_owl_expression, owl_expression_to_dl
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
        ce12 = "(∀r_1.∀r_2.∀r_3.(¬⊥ ⊔ B ⊔ E)) ⊓ (∀r_1.∀r_2.¬(C ⊔ (C ⊓ B)))" # ==> "∀ r_1.(∀ r_2.((¬C) ⊓ (∀ r_3.⊥)))"

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
        print("test_simplifier_robustness")