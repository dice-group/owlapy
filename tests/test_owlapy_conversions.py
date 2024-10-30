import unittest
from owlapy.iri import IRI
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.parser import DLSyntaxParser
from owlapy.render import DLSyntaxObjectRenderer
from owlapy.class_expression import OWLClass,OWLObjectHasValue, OWLObjectSomeValuesFrom, OWLObjectOneOf, OWLObjectAllValuesFrom

from owlapy.owl_literal import DoubleOWLDatatype, IntegerOWLDatatype, OWLLiteral, BooleanOWLDatatype
from owlapy.class_expression import OWLDataMinCardinality, OWLObjectIntersectionOf, OWLThing, OWLObjectComplementOf, OWLObjectUnionOf, OWLObjectMinCardinality, OWLDataExactCardinality, OWLDataHasValue, OWLDataAllValuesFrom, \
    OWLDataOneOf, OWLDataSomeValuesFrom, \
    OWLDataMaxCardinality

from owlapy.owl_data_ranges import OWLDataComplementOf, OWLDataIntersectionOf, OWLDataUnionOf
from owlapy.providers import owl_datatype_min_max_inclusive_restriction

class TestOWLConversions(unittest.TestCase):
    def test_owlapy_to_dl_str_and_back(self):
        NS = "http://example.com/father#"
        renderer = DLSyntaxObjectRenderer()
        parser = DLSyntaxParser(NS)
        male = OWLClass(IRI.create(NS, 'male'))
        female = OWLClass(IRI.create(NS, 'female'))
        has_child = OWLObjectProperty(IRI(NS, 'hasChild'))
        has_age = OWLDataProperty(IRI(NS, 'hasAge'))
        # (1)
        c = OWLObjectUnionOf((male, OWLObjectSomeValuesFrom(property=has_child, filler=female)))
        rendered_c=renderer.render(c)
        self.assertEqual(c, parser.parse_expression(rendered_c))
        self.assertEqual(rendered_c, "male ⊔ (∃ hasChild.female)")
        # (2)
        c = OWLObjectComplementOf(OWLObjectIntersectionOf((female,
                                                           OWLObjectSomeValuesFrom(property=has_child,
                                                                                   filler=OWLThing))))
        rendered_c = renderer.render(c)
        self.assertEqual(c, parser.parse_expression(rendered_c))
        self.assertEqual(rendered_c, "¬(female ⊓ (∃ hasChild.⊤))")
        # (3)
        c = OWLObjectSomeValuesFrom(property=has_child,
                                    filler=OWLObjectSomeValuesFrom(property=has_child,
                                                                   filler=OWLObjectSomeValuesFrom(property=has_child,
                                                                                                  filler=OWLThing)))
        rendered_c = renderer.render(c)
        self.assertEqual(c, parser.parse_expression(rendered_c))
        self.assertEqual(rendered_c, "∃ hasChild.(∃ hasChild.(∃ hasChild.⊤))")
        # (4)
        i1 = OWLNamedIndividual(IRI.create(NS, 'heinz'))
        i2 = OWLNamedIndividual(IRI.create(NS, 'marie'))
        c = OWLObjectOneOf((i1, i2))
        rendered_c = renderer.render(c)
        self.assertEqual(c, parser.parse_expression(rendered_c))
        self.assertEqual(rendered_c, "{heinz ⊔ marie}")
        # (5)
        c = OWLObjectHasValue(property=has_child, individual=i1)
        rendered_c = renderer.render(c)
        self.assertEqual(c, parser.parse_expression(rendered_c))
        self.assertEqual(rendered_c, "∃ hasChild.{heinz}")
        # (6)
        c = OWLObjectMinCardinality(cardinality=2, property=has_child, filler=OWLThing)
        rendered_c = renderer.render(c)
        self.assertEqual(c, parser.parse_expression(rendered_c))
        self.assertEqual(rendered_c, "≥ 2 hasChild.⊤")
        # (7)
        c = OWLDataSomeValuesFrom(property=has_age, filler=OWLDataComplementOf(DoubleOWLDatatype))
        rendered_c = renderer.render(c)
        self.assertEqual(c, parser.parse_expression(rendered_c))
        self.assertEqual(rendered_c, "∃ hasAge.¬xsd:double")
        # (8)
        c = OWLDataAllValuesFrom(property=has_age, filler=OWLDataUnionOf([owl_datatype_min_max_inclusive_restriction(40, 80), IntegerOWLDatatype]))
        rendered_c = renderer.render(c)
        self.assertEqual(c, parser.parse_expression(rendered_c))
        self.assertEqual(rendered_c, "∀ hasAge.(xsd:integer[≥ 40 , ≤ 80] ⊔ xsd:integer)")
        # (9)
        c = OWLDataSomeValuesFrom(property=has_age,
                                   filler=OWLDataIntersectionOf([OWLDataOneOf([OWLLiteral(32.5), OWLLiteral(4.5)]),
                                                                 IntegerOWLDatatype]))
        rendered_c = renderer.render(c)
        self.assertEqual(c, parser.parse_expression(rendered_c))
        self.assertEqual(rendered_c, "∃ hasAge.({32.5 ⊔ 4.5} ⊓ xsd:integer)")
        # (10)
        c = OWLDataHasValue(property=has_age, value=OWLLiteral(50))
        rendered_c = renderer.render(c)
        self.assertEqual(c, parser.parse_expression(rendered_c))
        self.assertEqual(rendered_c, "∃ hasAge.{50}")
        # (11)
        c = OWLDataExactCardinality(cardinality=1, property=has_age, filler=IntegerOWLDatatype)
        rendered_c = renderer.render(c)
        self.assertEqual(c, parser.parse_expression(rendered_c))
        self.assertEqual(rendered_c, "= 1 hasAge.xsd:integer")
        # (12)
        c = OWLDataMaxCardinality(cardinality=4, property=has_age, filler=DoubleOWLDatatype)
        rendered_c = renderer.render(c)
        self.assertEqual(c, parser.parse_expression(rendered_c))
        self.assertEqual(rendered_c, "≤ 4 hasAge.xsd:double")
        # (13)
        c = OWLDataMinCardinality(cardinality=7, property=has_age, filler=BooleanOWLDatatype)
        rendered_c = renderer.render(c)
        self.assertEqual(c, parser.parse_expression(rendered_c))
        self.assertEqual(rendered_c, "≥ 7 hasAge.xsd:boolean")

        # (14)
        c = OWLObjectHasValue(property=has_child,
                              individual=OWLNamedIndividual(IRI.create(NS, 'A')))
        rendered_c=renderer.render(c)
        self.assertEqual(c, parser.parse_expression(rendered_c))
        self.assertEqual(rendered_c, "∃ hasChild.{A}")

        # (15)
        c = OWLObjectSomeValuesFrom(property=has_child, filler=OWLObjectOneOf([
            OWLNamedIndividual(IRI.create(NS, 'A')),
            OWLNamedIndividual(IRI.create(NS, 'B'))]))
        renderer_c = renderer.render(c)
        self.assertEqual(renderer_c, "∃ hasChild.{A ⊔ B}")
        self.assertEqual(c, parser.parse_expression(renderer_c))
        # (16)
        c = OWLObjectAllValuesFrom(property=has_child, filler=OWLObjectOneOf([
            OWLNamedIndividual(IRI.create(NS, 'A')),
            OWLNamedIndividual(IRI.create(NS, 'B'))]))
        renderer_c = renderer.render(c)
        self.assertEqual(renderer_c, "∀ hasChild.{A ⊔ B}")
        self.assertEqual(c, parser.parse_expression(renderer_c))

    def test_owlapy_to_manchester_str_and_back(self):
        # TODO
        pass


if __name__ == '__main__':
    unittest.main()
