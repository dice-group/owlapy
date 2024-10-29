import unittest
from owlapy.iri import IRI
from owlapy.owl_property import OWLObjectProperty
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.parser import DLSyntaxParser
from owlapy.render import DLSyntaxObjectRenderer
from owlapy.class_expression import OWLObjectHasValue

class TestOWLObjectHasValueConversions(unittest.TestCase):
    def test_render(self):
        renderer = DLSyntaxObjectRenderer()
        NS = "http://example.com/father#"
        parser = DLSyntaxParser(NS)
        has_child = OWLObjectProperty(IRI(NS, 'hasChild'))

        c = OWLObjectHasValue(property=has_child,
                              individual=OWLNamedIndividual(IRI.create(NS, 'Demir')))
        rendered_c=renderer.render(c)
        self.assertEqual(c, parser.parse_expression(rendered_c))

        self.assertEqual(rendered_c, "∃ hasChild.{Demir}")


if __name__ == '__main__':
    unittest.main()
