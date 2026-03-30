"""Tests for the OWLAPI-based DL Syntax parser and renderer module."""
import unittest

from owlapy.class_expression import (
    OWLClass, OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom,
    OWLObjectIntersectionOf, OWLObjectUnionOf, OWLObjectComplementOf,
    OWLObjectMinCardinality, OWLObjectMaxCardinality,
)
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLSubClassOfAxiom, OWLEquivalentClassesAxiom
from owlapy.owl_property import OWLObjectProperty
from owlapy.owlapi_dlsyntax import OWLAPIDLSyntaxRenderer, OWLAPIDLSyntaxParser

NS = "http://example.org/"

# Note: OWLAPI's DL parser uses '#' as separator between namespace and local name.
# So namespace "http://example.org/" results in IRIs like "http://example.org/#A"
PARSER_NS = "http://example.org/"


def _cls(name: str) -> OWLClass:
    return OWLClass(IRI.create(NS, name))


def _prop(name: str) -> OWLObjectProperty:
    return OWLObjectProperty(IRI.create(NS, name))


class TestOWLAPIDLSyntaxRenderer(unittest.TestCase):
    """Test the OWLAPI-backed DL syntax renderer."""

    @classmethod
    def setUpClass(cls):
        cls.renderer = OWLAPIDLSyntaxRenderer()

    def test_render_class(self):
        A = _cls("A")
        result = self.renderer.render(A)
        self.assertEqual(result, "A")

    def test_render_some_values_from(self):
        A = _cls("A")
        r = _prop("r")
        expr = OWLObjectSomeValuesFrom(r, A)
        result = self.renderer.render(expr)
        self.assertEqual(result, "∃ r.A")

    def test_render_all_values_from(self):
        A = _cls("A")
        r = _prop("r")
        expr = OWLObjectAllValuesFrom(r, A)
        result = self.renderer.render(expr)
        self.assertEqual(result, "∀ r.A")

    def test_render_intersection(self):
        A = _cls("A")
        B = _cls("B")
        expr = OWLObjectIntersectionOf([A, B])
        result = self.renderer.render(expr)
        # OWLAPI may order operands differently; check both are present
        self.assertIn("⊓", result)
        self.assertIn("A", result)
        self.assertIn("B", result)

    def test_render_union(self):
        A = _cls("A")
        B = _cls("B")
        expr = OWLObjectUnionOf([A, B])
        result = self.renderer.render(expr)
        self.assertIn("⊔", result)
        self.assertIn("A", result)
        self.assertIn("B", result)

    def test_render_complement(self):
        A = _cls("A")
        expr = OWLObjectComplementOf(A)
        result = self.renderer.render(expr)
        self.assertIn("¬", result)
        self.assertIn("A", result)

    def test_render_subclass_axiom(self):
        A = _cls("A")
        B = _cls("B")
        r = _prop("r")
        some_expr = OWLObjectSomeValuesFrom(r, B)
        axiom = OWLSubClassOfAxiom(A, some_expr, [])
        result = self.renderer.render(axiom)
        self.assertIn("⊑", result)
        self.assertIn("A", result)
        self.assertIn("∃ r.B", result)

    def test_render_equivalent_classes_axiom(self):
        A = _cls("A")
        B = _cls("B")
        r = _prop("r")
        some_expr = OWLObjectSomeValuesFrom(r, B)
        axiom = OWLEquivalentClassesAxiom([A, some_expr], [])
        result = self.renderer.render(axiom)
        self.assertIn("≡", result)
        self.assertIn("A", result)

    def test_render_min_cardinality(self):
        A = _cls("A")
        r = _prop("r")
        expr = OWLObjectMinCardinality(2, r, A)
        result = self.renderer.render(expr)
        self.assertIn("≥", result)
        self.assertIn("2", result)

    def test_render_max_cardinality(self):
        A = _cls("A")
        r = _prop("r")
        expr = OWLObjectMaxCardinality(3, r, A)
        result = self.renderer.render(expr)
        self.assertIn("≤", result)
        self.assertIn("3", result)


class TestOWLAPIDLSyntaxParser(unittest.TestCase):
    """Test the OWLAPI-backed DL syntax parser."""

    @classmethod
    def setUpClass(cls):
        cls.parser = OWLAPIDLSyntaxParser(namespace=PARSER_NS)

    def test_parse_class(self):
        ce = self.parser.parse_expression("A")
        self.assertIsInstance(ce, OWLClass)
        self.assertIn("A", ce.iri.str)

    def test_parse_some_values_from(self):
        ce = self.parser.parse_expression("∃ r.A")
        self.assertIsInstance(ce, OWLObjectSomeValuesFrom)

    def test_parse_all_values_from(self):
        ce = self.parser.parse_expression("∀ r.A")
        self.assertIsInstance(ce, OWLObjectAllValuesFrom)

    def test_parse_intersection(self):
        ce = self.parser.parse_expression("A ⊓ B")
        self.assertIsInstance(ce, OWLObjectIntersectionOf)

    def test_parse_union(self):
        ce = self.parser.parse_expression("A ⊔ B")
        self.assertIsInstance(ce, OWLObjectUnionOf)

    def test_parse_complement(self):
        ce = self.parser.parse_expression("¬A")
        self.assertIsInstance(ce, OWLObjectComplementOf)

    def test_parse_complex_expression(self):
        ce = self.parser.parse_expression("∃ r.A ⊓ B")
        self.assertIsInstance(ce, OWLObjectIntersectionOf)

    def test_parse_subclass_axiom(self):
        axiom = self.parser.parse_axiom("A ⊑ ∃ r.B")
        self.assertIsInstance(axiom, OWLSubClassOfAxiom)

    def test_parse_equivalent_classes_axiom(self):
        axiom = self.parser.parse_axiom("A ≡ ∃ r.B")
        self.assertIsInstance(axiom, OWLEquivalentClassesAxiom)

    def test_parse_invalid_expression_raises(self):
        with self.assertRaises(Exception):
            self.parser.parse_expression("⊑ ⊑ ⊑")

    def test_namespace_property(self):
        parser = OWLAPIDLSyntaxParser(namespace="http://test.org/")
        self.assertEqual(parser.namespace, "http://test.org/")
        parser.namespace = "http://other.org/"
        self.assertEqual(parser.namespace, "http://other.org/")


class TestOWLAPIDLSyntaxRoundTrip(unittest.TestCase):
    """Test round-tripping: render -> parse -> render."""

    @classmethod
    def setUpClass(cls):
        cls.renderer = OWLAPIDLSyntaxRenderer()
        cls.parser = OWLAPIDLSyntaxParser(namespace=NS)

    def test_roundtrip_some_values_from(self):
        A = _cls("A")
        r = _prop("r")
        original = OWLObjectSomeValuesFrom(r, A)
        dl_str = self.renderer.render(original)
        parsed = self.parser.parse_expression(dl_str)
        re_rendered = self.renderer.render(parsed)
        self.assertEqual(dl_str, re_rendered)

    def test_roundtrip_subclass_axiom(self):
        A = _cls("A")
        B = _cls("B")
        axiom = OWLSubClassOfAxiom(A, B, [])
        dl_str = self.renderer.render(axiom)
        parsed_axiom = self.parser.parse_axiom(dl_str)
        re_rendered = self.renderer.render(parsed_axiom)
        self.assertEqual(dl_str, re_rendered)


if __name__ == '__main__':
    unittest.main()

