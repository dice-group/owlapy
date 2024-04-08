import unittest

from owlapy.model import OWLDataMinCardinality, OWLObjectIntersectionOf, OWLObjectSomeValuesFrom, \
    OWLThing, OWLObjectComplementOf, OWLObjectUnionOf, OWLNamedIndividual, OWLObjectOneOf, OWLObjectHasValue, \
    OWLObjectMinCardinality, IRI, OWLDataProperty, DoubleOWLDatatype, OWLClass, OWLDataComplementOf, \
    OWLDataIntersectionOf, IntegerOWLDatatype, OWLDataExactCardinality, OWLDataHasValue, OWLDataAllValuesFrom, \
    OWLDataOneOf, OWLDataSomeValuesFrom, OWLDataUnionOf, OWLLiteral, OWLObjectProperty, BooleanOWLDatatype, \
    OWLDataMaxCardinality
from owlapy.model.providers import OWLDatatypeMinMaxInclusiveRestriction
from owlapy.render import DLSyntaxObjectRenderer, ManchesterOWLSyntaxOWLObjectRenderer


class Owlapy_DLRenderer_Test(unittest.TestCase):
    def test_ce_render(self):
        renderer = DLSyntaxObjectRenderer()
        NS = "http://example.com/father#"

        male = OWLClass(IRI.create(NS, 'male'))
        female = OWLClass(IRI.create(NS, 'female'))
        has_child = OWLObjectProperty(IRI(NS, 'hasChild'))
        has_age = OWLDataProperty(IRI(NS, 'hasAge'))

        c = OWLObjectUnionOf((male, OWLObjectSomeValuesFrom(property=has_child, filler=female)))
        r = renderer.render(c)
        print(r)
        self.assertEqual(r, "male ⊔ (∃ hasChild.female)")
        c = OWLObjectComplementOf(OWLObjectIntersectionOf((female,
                                                           OWLObjectSomeValuesFrom(property=has_child,
                                                                                   filler=OWLThing))))
        r = renderer.render(c)
        print(r)
        self.assertEqual(r, "¬(female ⊓ (∃ hasChild.⊤))")
        c = OWLObjectSomeValuesFrom(property=has_child,
                                    filler=OWLObjectSomeValuesFrom(property=has_child,
                                                                   filler=OWLObjectSomeValuesFrom(property=has_child,
                                                                                                  filler=OWLThing)))
        r = renderer.render(c)
        print(r)
        self.assertEqual(r, "∃ hasChild.(∃ hasChild.(∃ hasChild.⊤))")

        i1 = OWLNamedIndividual(IRI.create(NS, 'heinz'))
        i2 = OWLNamedIndividual(IRI.create(NS, 'marie'))
        oneof = OWLObjectOneOf((i1, i2))
        r = renderer.render(oneof)
        print(r)
        self.assertEqual(r, "{heinz ⊔ marie}")

        hasvalue = OWLObjectHasValue(property=has_child, individual=i1)
        r = renderer.render(hasvalue)
        print(r)
        self.assertEqual(r, "∃ hasChild.{heinz}")

        mincard = OWLObjectMinCardinality(cardinality=2, property=has_child, filler=OWLThing)
        r = renderer.render(mincard)
        print(r)
        self.assertEqual(r, "≥ 2 hasChild.⊤")

        d = OWLDataSomeValuesFrom(property=has_age,
                                  filler=OWLDataComplementOf(DoubleOWLDatatype))
        r = renderer.render(d)
        print(r)
        self.assertEqual(r, "∃ hasAge.¬xsd:double")

        datatype_restriction = OWLDatatypeMinMaxInclusiveRestriction(40, 80)

        dr = OWLDataAllValuesFrom(property=has_age, filler=OWLDataUnionOf([datatype_restriction, IntegerOWLDatatype]))
        r = renderer.render(dr)
        print(r)
        self.assertEqual(r, "∀ hasAge.(xsd:integer[≥ 40 , ≤ 80] ⊔ xsd:integer)")

        dr = OWLDataSomeValuesFrom(property=has_age,
                                   filler=OWLDataIntersectionOf([OWLDataOneOf([OWLLiteral(32.5), OWLLiteral(4.5)]),
                                                                 IntegerOWLDatatype]))
        r = renderer.render(dr)
        print(r)
        self.assertEqual(r, "∃ hasAge.({32.5 ⊔ 4.5} ⊓ xsd:integer)")

        hasvalue = OWLDataHasValue(property=has_age, value=OWLLiteral(50))
        r = renderer.render(hasvalue)
        print(r)
        self.assertEqual(r, "∃ hasAge.{50}")

        exactcard = OWLDataExactCardinality(cardinality=1, property=has_age, filler=IntegerOWLDatatype)
        r = renderer.render(exactcard)
        print(r)
        self.assertEqual(r, "= 1 hasAge.xsd:integer")

        maxcard = OWLDataMaxCardinality(cardinality=4, property=has_age, filler=DoubleOWLDatatype)
        r = renderer.render(maxcard)
        print(r)
        self.assertEqual(r, "≤ 4 hasAge.xsd:double")

        mincard = OWLDataMinCardinality(cardinality=7, property=has_age, filler=BooleanOWLDatatype)
        r = renderer.render(mincard)
        print(r)
        self.assertEqual(r, "≥ 7 hasAge.xsd:boolean")


class Owlapy_ManchesterRenderer_Test(unittest.TestCase):
    def test_ce_render(self):
        renderer = ManchesterOWLSyntaxOWLObjectRenderer()
        NS = "http://example.com/father#"

        male = OWLClass(IRI.create(NS, 'male'))
        female = OWLClass(IRI.create(NS, 'female'))
        has_child = OWLObjectProperty(IRI(NS, 'hasChild'))
        has_age = OWLDataProperty(IRI(NS, 'hasAge'))

        c = OWLObjectUnionOf((male, OWLObjectSomeValuesFrom(property=has_child, filler=female)))
        r = renderer.render(c)
        print(r)
        self.assertEqual(r, "male or (hasChild some female)")
        c = OWLObjectComplementOf(OWLObjectIntersectionOf((female,
                                                           OWLObjectSomeValuesFrom(property=has_child,
                                                                                   filler=OWLThing))))
        r = renderer.render(c)
        print(r)
        self.assertEqual(r, "not (female and (hasChild some Thing))")
        c = OWLObjectSomeValuesFrom(property=has_child,
                                    filler=OWLObjectSomeValuesFrom(property=has_child,
                                                                   filler=OWLObjectSomeValuesFrom(property=has_child,
                                                                                                  filler=OWLThing)))
        r = renderer.render(c)
        print(r)
        self.assertEqual(r, "hasChild some (hasChild some (hasChild some Thing))")

        i1 = OWLNamedIndividual(IRI.create(NS, 'heinz'))
        i2 = OWLNamedIndividual(IRI.create(NS, 'marie'))
        oneof = OWLObjectOneOf((i1, i2))
        r = renderer.render(oneof)
        print(r)
        self.assertEqual(r, "{heinz , marie}")

        hasvalue = OWLObjectHasValue(property=has_child, individual=i1)
        r = renderer.render(hasvalue)
        print(r)
        self.assertEqual(r, "hasChild value heinz")

        mincard = OWLObjectMinCardinality(cardinality=2, property=has_child, filler=OWLThing)
        r = renderer.render(mincard)
        print(r)
        self.assertEqual(r, "hasChild min 2 Thing")

        d = OWLDataSomeValuesFrom(property=has_age,
                                  filler=OWLDataComplementOf(DoubleOWLDatatype))
        r = renderer.render(d)
        print(r)
        self.assertEqual(r, "hasAge some not xsd:double")

        datatype_restriction = OWLDatatypeMinMaxInclusiveRestriction(40, 80)

        dr = OWLDataAllValuesFrom(property=has_age, filler=OWLDataUnionOf([datatype_restriction, IntegerOWLDatatype]))
        r = renderer.render(dr)
        print(r)
        self.assertEqual(r, "hasAge only (xsd:integer[>= 40 , <= 80] or xsd:integer)")

        dr = OWLDataSomeValuesFrom(property=has_age,
                                   filler=OWLDataIntersectionOf([OWLDataOneOf([OWLLiteral(32.5), OWLLiteral(4.5)]),
                                                                 IntegerOWLDatatype]))
        r = renderer.render(dr)
        print(r)
        self.assertEqual(r, "hasAge some ({32.5 , 4.5} and xsd:integer)")

        hasvalue = OWLDataHasValue(property=has_age, value=OWLLiteral(50))
        r = renderer.render(hasvalue)
        print(r)
        self.assertEqual(r, "hasAge value 50")

        maxcard = OWLDataExactCardinality(cardinality=1, property=has_age, filler=IntegerOWLDatatype)
        r = renderer.render(maxcard)
        print(r)
        self.assertEqual(r, "hasAge exactly 1 xsd:integer")

        maxcard = OWLDataMaxCardinality(cardinality=4, property=has_age, filler=DoubleOWLDatatype)
        r = renderer.render(maxcard)
        print(r)
        self.assertEqual(r, "hasAge max 4 xsd:double")

        mincard = OWLDataMinCardinality(cardinality=7, property=has_age, filler=BooleanOWLDatatype)
        r = renderer.render(mincard)
        print(r)
        self.assertEqual(r, "hasAge min 7 xsd:boolean")


if __name__ == '__main__':
    unittest.main()
