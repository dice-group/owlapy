import unittest

from owlapy.model import OWLObjectProperty, OWLObjectSomeValuesFrom, OWLObjectUnionOf, \
    OWLClass, IRI, OWLDataProperty, OWLDataSomeValuesFrom, OWLNamedIndividual, OWLObjectComplementOf, \
    OWLObjectIntersectionOf, OWLObjectMinCardinality, OWLObjectOneOf
from owlapy.model.providers import OWLDatatypeMinExclusiveRestriction
from owlapy.util import TopLevelCNF, TopLevelDNF


class TopLevelNFTest(unittest.TestCase):

    def setUp(self):
        namespace = 'http://test.org/test#'

        # Classes
        self.a = OWLClass(IRI(namespace, 'A'))
        self.b = OWLClass(IRI(namespace, 'B'))
        self.c = OWLClass(IRI(namespace, 'C'))
        self.d = OWLClass(IRI(namespace, 'D'))
        self.e = OWLClass(IRI(namespace, 'E'))
        self.f = OWLClass(IRI(namespace, 'F'))
        self.g = OWLClass(IRI(namespace, 'G'))
        self.h = OWLClass(IRI(namespace, 'H'))

        # Object Properties
        self.op1 = OWLObjectProperty(IRI.create(namespace, 'op1'))

        # Data Properties
        self.dp1 = OWLDataProperty(IRI.create(namespace, 'dp1'))

        # Complex Expressions
        self.c1 = OWLObjectSomeValuesFrom(self.op1,
                                          OWLObjectUnionOf([self.a, OWLObjectIntersectionOf([self.a, self.b])]))
        self.c2 = OWLDataSomeValuesFrom(self.dp1, OWLDatatypeMinExclusiveRestriction(5))
        self.c3 = OWLObjectSomeValuesFrom(self.op1, OWLObjectOneOf(OWLNamedIndividual(IRI(namespace, 'AB'))))

    def test_cnf(self):
        cnf = TopLevelCNF()

        # A or ( A and B)
        c = OWLObjectUnionOf([self.a, OWLObjectIntersectionOf([self.a, self.b])])
        c = cnf.get_top_level_cnf(c)
        # (A or A) and (A or B)
        true_c = OWLObjectIntersectionOf([OWLObjectUnionOf([self.a, self.a]), OWLObjectUnionOf([self.a, self.b])])
        self.assertEqual(true_c, c)

        # op1 some (A or ( A and B))
        c = cnf.get_top_level_cnf(self.c1)
        self.assertEqual(self.c1, c)

        # (A and c2) or c1 or (D and E)
        c = OWLObjectUnionOf((OWLObjectIntersectionOf((self.a, self.c2)), self.c1,
                              OWLObjectIntersectionOf((self.d, self.e))))
        c = cnf.get_top_level_cnf(c)
        # (A or D or c1) and (A or E or c1) and (D or c1 or c2) and (E or c1 or c2)
        true_c = OWLObjectIntersectionOf((OWLObjectUnionOf((self.a, self.d, self.c1)),
                                          OWLObjectUnionOf((self.a, self.e, self.c1)),
                                          OWLObjectUnionOf((self.d, self.c1, self.c2)),
                                          OWLObjectUnionOf((self.e, self.c1, self.c2))))
        self.assertEqual(true_c, c)

        # A or ((C and D) or B)
        c = OWLObjectUnionOf((self.a, OWLObjectUnionOf((OWLObjectIntersectionOf((self.c, self.d)), self.b))))
        c = cnf.get_top_level_cnf(c)
        # (A or B or C) and (A or B or D)
        true_c = OWLObjectIntersectionOf((OWLObjectUnionOf((self.a, self.b, self.c)),
                                          OWLObjectUnionOf((self.a, self.b, self.d))))
        self.assertEqual(true_c, c)

        # (c1 and B) or (C and c2) or (E and c3)
        c = OWLObjectUnionOf((OWLObjectIntersectionOf((self.c1, self.b)),
                              OWLObjectIntersectionOf((self.c, self.c2)),
                              OWLObjectIntersectionOf((self.e, self.c3))))
        # (B or C or E) and (B or C or c3) and (B or E or c2) and (B or c3 or c2) and (C or E or c1)
        # and (C or c1 or c3) and (E or c1 or c2) and (c1 or c3 or c2)
        c = cnf.get_top_level_cnf(c)
        true_c = OWLObjectIntersectionOf((OWLObjectUnionOf((self.b, self.c, self.e)),
                                          OWLObjectUnionOf((self.b, self.c, self.c3)),
                                          OWLObjectUnionOf((self.b, self.e, self.c2)),
                                          OWLObjectUnionOf((self.b, self.c3, self.c2)),
                                          OWLObjectUnionOf((self.c, self.e, self.c1)),
                                          OWLObjectUnionOf((self.c, self.c1, self.c3)),
                                          OWLObjectUnionOf((self.e, self.c1, self.c2)),
                                          OWLObjectUnionOf((self.c1, self.c3, self.c2))))
        self.assertEqual(true_c, c)

        # not (A or (B or (C and (D or (E and (F and (G or H)))))))
        c = OWLObjectComplementOf(
                OWLObjectUnionOf((
                    self.a,
                    OWLObjectUnionOf((
                        self.b,
                        OWLObjectIntersectionOf((
                            self.c,
                            OWLObjectUnionOf((
                                self.d,
                                OWLObjectIntersectionOf((
                                    self.e,
                                    OWLObjectIntersectionOf((self.f, OWLObjectUnionOf((self.g, self.h)))))))))))))))
        c = cnf.get_top_level_cnf(c)
        # ((not C) or (not D)) and ((not C) or (not E) or (not F) or (not G)) and ((not C) or
        # (not E) or (not F) or (not H)) and (not A) and (not B)
        true_c = OWLObjectIntersectionOf((OWLObjectUnionOf((OWLObjectComplementOf(self.c),
                                                            OWLObjectComplementOf(self.d))),
                                          OWLObjectUnionOf((OWLObjectComplementOf(self.c),
                                                            OWLObjectComplementOf(self.e),
                                                            OWLObjectComplementOf(self.f),
                                                            OWLObjectComplementOf(self.g))),
                                          OWLObjectUnionOf((OWLObjectComplementOf(self.c),
                                                            OWLObjectComplementOf(self.e),
                                                            OWLObjectComplementOf(self.f),
                                                            OWLObjectComplementOf(self.h))),
                                          OWLObjectComplementOf(self.a), OWLObjectComplementOf(self.b)))
        self.assertEqual(true_c, c)

    def test_dnf(self):
        dnf = TopLevelDNF()

        # A and ( A or B)
        c = OWLObjectIntersectionOf([self.a, OWLObjectUnionOf([self.a, self.b])])
        c = dnf.get_top_level_dnf(c)
        # (A and A) or (A and B)
        true_c = OWLObjectUnionOf([OWLObjectIntersectionOf([self.a, self.a]),
                                   OWLObjectIntersectionOf([self.a, self.b])])
        self.assertEqual(true_c, c)

        # op1 min 5 (A and ( A or B))
        old_c = OWLObjectMinCardinality(5, self.op1,
                                        OWLObjectIntersectionOf([self.a, OWLObjectUnionOf([self.a, self.b])]))
        c = dnf.get_top_level_dnf(old_c)
        self.assertEqual(old_c, c)

        # (A or c2) and c1 and (D or E)
        c = OWLObjectIntersectionOf((OWLObjectUnionOf((self.a, self.c2)), self.c1, OWLObjectUnionOf((self.d, self.e))))
        c = dnf.get_top_level_dnf(c)
        # (A and D and c1) or (A and E and c1) or (D and c1 and c2) or (E and c1 and c2)
        true_c = OWLObjectUnionOf((OWLObjectIntersectionOf((self.a, self.d, self.c1)),
                                   OWLObjectIntersectionOf((self.a, self.e, self.c1)),
                                   OWLObjectIntersectionOf((self.d, self.c1, self.c2)),
                                   OWLObjectIntersectionOf((self.e, self.c1, self.c2))))
        self.assertEqual(true_c, c)

        # c1 and ((C or D) and B)
        c = OWLObjectIntersectionOf((self.c1, OWLObjectIntersectionOf((OWLObjectUnionOf((self.c, self.d)), self.b))))
        c = dnf.get_top_level_dnf(c)
        # (B and C and c1) or (B and D and c1)
        true_c = OWLObjectUnionOf((OWLObjectIntersectionOf((self.b, self.c, self.c1)),
                                   OWLObjectIntersectionOf((self.b, self.d, self.c1))))
        self.assertEqual(true_c, c)

        # (c1 or B) and (C or c2) and (E or c3)
        c = OWLObjectIntersectionOf((OWLObjectUnionOf((self.c1, self.b)),
                                     OWLObjectUnionOf((self.c, self.c2)),
                                     OWLObjectUnionOf((self.e, self.c3))))
        # (B and C and E) or (B and C and c3) or (B and E and c2) or (B and c3 and c2) or (C and E and c1)
        # or (C and c1 and c3) or (E and c1 and c2) or (c1 and c3 and c2)
        c = dnf.get_top_level_dnf(c)
        true_c = OWLObjectUnionOf((OWLObjectIntersectionOf((self.b, self.c, self.e)),
                                   OWLObjectIntersectionOf((self.b, self.c, self.c3)),
                                   OWLObjectIntersectionOf((self.b, self.e, self.c2)),
                                   OWLObjectIntersectionOf((self.b, self.c3, self.c2)),
                                   OWLObjectIntersectionOf((self.c, self.e, self.c1)),
                                   OWLObjectIntersectionOf((self.c, self.c1, self.c3)),
                                   OWLObjectIntersectionOf((self.e, self.c1, self.c2)),
                                   OWLObjectIntersectionOf((self.c1, self.c3, self.c2))))
        self.assertEqual(true_c, c)

        # not (A and (B and (C or (D and (E or (F or (G and H)))))))
        c = OWLObjectComplementOf(
                OWLObjectIntersectionOf((
                    self.a,
                    OWLObjectIntersectionOf((
                        self.b,
                        OWLObjectUnionOf((
                            self.c,
                            OWLObjectIntersectionOf((
                                self.d,
                                OWLObjectUnionOf((
                                    self.e,
                                    OWLObjectUnionOf((self.f, OWLObjectIntersectionOf((self.g, self.h)))))))))))))))
        c = dnf.get_top_level_dnf(c)
        # ((not C) and (not D)) or ((not C) and (not E) and (not F) and (not G)) or ((not C) and
        # (not E) and (not F) and (not H)) or (not A) or (not B)
        true_c = OWLObjectUnionOf((OWLObjectIntersectionOf((OWLObjectComplementOf(self.c),
                                                            OWLObjectComplementOf(self.d))),
                                   OWLObjectIntersectionOf((OWLObjectComplementOf(self.c),
                                                            OWLObjectComplementOf(self.e),
                                                            OWLObjectComplementOf(self.f),
                                                            OWLObjectComplementOf(self.g))),
                                   OWLObjectIntersectionOf((OWLObjectComplementOf(self.c),
                                                            OWLObjectComplementOf(self.e),
                                                            OWLObjectComplementOf(self.f),
                                                            OWLObjectComplementOf(self.h))),
                                   OWLObjectComplementOf(self.a), OWLObjectComplementOf(self.b)))
        self.assertEqual(true_c, c)
