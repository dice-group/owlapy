import unittest

from owlapy import namespaces
from owlapy.namespaces import Namespaces
from owlapy.model import OWLClass, OWLObjectUnionOf, IRI

base = Namespaces("ex", "http://example.org/")


class Owlapy_Test(unittest.TestCase):
    def test_iri(self):
        i1 = IRI(base, "I1")
        i2 = IRI(base, "I2")
        i1x = IRI(base, "I1")
        self.assertEqual(i1, i1x)
        self.assertIs(i1, i1x)
        self.assertNotEqual(i1, i2)

    def test_class(self):
        c1 = OWLClass(IRI(base, "C1"))
        c2 = OWLClass(IRI(base, "C2"))
        c1x = OWLClass(IRI(base, "C1"))
        thing = OWLClass(IRI(namespaces.OWL, "Thing"))
        self.assertTrue(thing.is_owl_thing())
        self.assertEqual(c1, c1x)
        self.assertNotEqual(c2, c1)

    def test_union(self):
        c1 = OWLClass(IRI(base, "C1"))
        c2 = OWLClass(IRI(base, "C2"))
        c3 = OWLObjectUnionOf((c1, c2))
        self.assertSequenceEqual(list(c3.operands()), [c1, c2])

    def test_iri_fixed_set(self):
        fs = frozenset({IRI.create(base, "C1"), IRI.create(base, "C2")})
        self.assertIn(IRI.create(base, "C1"), fs)
        self.assertNotIn(IRI.create(base, "C3"), fs)
        self.assertNotEqual(fs & {IRI.create(base, "C2")}, fs & {IRI.create(base, "C1")})
        self.assertEqual(fs & {IRI.create(base, "C1")}, fs & {IRI.create(base, "C1")})
        self.assertEqual(fs & {IRI.create(base, "C3")}, frozenset())
        self.assertEqual(set(), frozenset())
        self.assertSequenceEqual(list([IRI.create(base, "C1")]), [IRI.create(base, "C1")])


if __name__ == '__main__':
    unittest.main()
