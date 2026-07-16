import unittest

from owlapy.class_expression import (
    OWLClass,
    OWLDataHasValue,
    OWLDataOneOf,
    OWLDatatypeRestriction,
    OWLObjectComplementOf,
    OWLObjectHasSelf,
    OWLObjectHasValue,
    OWLObjectIntersectionOf,
    OWLObjectMinCardinality,
    OWLObjectOneOf,
    OWLObjectSomeValuesFrom,
    OWLObjectUnionOf,
)
from owlapy.iri import IRI
from owlapy.owl_axiom import (
    OWLClassAssertionAxiom,
    OWLDataPropertyAssertionAxiom,
    OWLDataPropertyDomainAxiom,
    OWLDataPropertyRangeAxiom,
    OWLDeclarationAxiom,
    OWLDisjointClassesAxiom,
    OWLEquivalentClassesAxiom,
    OWLFunctionalObjectPropertyAxiom,
    OWLObjectPropertyAssertionAxiom,
    OWLObjectPropertyDomainAxiom,
    OWLObjectPropertyRangeAxiom,
    OWLSubClassOfAxiom,
)
from owlapy.owl_individual import OWLAnonymousIndividual, OWLNamedIndividual
from owlapy.owl_literal import IntegerOWLDatatype, OWLLiteral
from owlapy.owl_property import OWLDataProperty, OWLObjectInverseOf, OWLObjectProperty
from owlapy.utils import SignatureExtractor

NS = "http://example.com/onto#"


class TestClassExpressionSignature(unittest.TestCase):
    def setUp(self):
        self.person = OWLClass(IRI(NS, "Person"))
        self.student = OWLClass(IRI(NS, "Student"))
        self.has_child = OWLObjectProperty(IRI(NS, "hasChild"))
        self.age = OWLDataProperty(IRI(NS, "age"))
        self.alice = OWLNamedIndividual(IRI(NS, "Alice"))
        self.bob = OWLNamedIndividual(IRI(NS, "Bob"))

    def test_named_class(self):
        self.assertEqual(self.person.signature(), {self.person})

    def test_nested_boolean_expression(self):
        ce = OWLObjectIntersectionOf([
            self.person,
            OWLObjectSomeValuesFrom(self.has_child, OWLObjectUnionOf([self.student, OWLObjectComplementOf(self.person)])),
        ])
        sig = ce.signature()
        self.assertEqual(sig, {self.person, self.student, self.has_child})

    def test_cardinality_restriction(self):
        ce = OWLObjectMinCardinality(2, self.has_child, self.person)
        self.assertEqual(ce.signature(), {self.has_child, self.person})

    def test_object_has_value_and_has_self(self):
        self.assertEqual(OWLObjectHasValue(self.has_child, self.alice).signature(), {self.has_child, self.alice})
        self.assertEqual(OWLObjectHasSelf(self.has_child).signature(), {self.has_child})

    def test_object_one_of(self):
        self.assertEqual(OWLObjectOneOf([self.alice, self.bob]).signature(), {self.alice, self.bob})

    def test_data_has_value_and_one_of(self):
        self.assertEqual(OWLDataHasValue(self.age, OWLLiteral(5)).signature(), {self.age, IntegerOWLDatatype})
        self.assertEqual(OWLDataOneOf([OWLLiteral(1), OWLLiteral(2)]).signature(), {IntegerOWLDatatype})

    def test_datatype_restriction(self):
        self.assertEqual(OWLDatatypeRestriction(IntegerOWLDatatype, []).signature(), {IntegerOWLDatatype})

    def test_object_inverse_of_via_extractor(self):
        # OWLObjectInverseOf is a property expression, not an OWLPropertyRange/OWLAxiom, so it has no
        # .signature() convenience method of its own -- but the extractor still handles it when nested.
        inv = OWLObjectInverseOf(self.has_child)
        self.assertEqual(SignatureExtractor().get_signature(inv), {self.has_child})
        ce = OWLObjectSomeValuesFrom(inv, self.person)
        self.assertEqual(ce.signature(), {self.has_child, self.person})


class TestAxiomSignature(unittest.TestCase):
    def setUp(self):
        self.person = OWLClass(IRI(NS, "Person"))
        self.student = OWLClass(IRI(NS, "Student"))
        self.has_child = OWLObjectProperty(IRI(NS, "hasChild"))
        self.age = OWLDataProperty(IRI(NS, "age"))
        self.alice = OWLNamedIndividual(IRI(NS, "Alice"))
        self.bob = OWLNamedIndividual(IRI(NS, "Bob"))

    def test_declaration_axiom(self):
        self.assertEqual(OWLDeclarationAxiom(self.person).signature(), {self.person})

    def test_class_assertion_axiom(self):
        ax = OWLClassAssertionAxiom(self.alice, self.person)
        self.assertEqual(ax.signature(), {self.alice, self.person})

    def test_object_property_assertion_axiom(self):
        ax = OWLObjectPropertyAssertionAxiom(self.alice, self.has_child, self.bob)
        self.assertEqual(ax.signature(), {self.alice, self.has_child, self.bob})

    def test_data_property_assertion_axiom(self):
        ax = OWLDataPropertyAssertionAxiom(self.alice, self.age, OWLLiteral(42))
        self.assertEqual(ax.signature(), {self.alice, self.age, IntegerOWLDatatype})

    def test_anonymous_individual_excluded_from_signature(self):
        anon = OWLAnonymousIndividual("b0")
        ax = OWLObjectPropertyAssertionAxiom(self.alice, self.has_child, anon)
        sig = ax.signature()
        self.assertNotIn(anon, sig)
        self.assertEqual(sig, {self.alice, self.has_child})

    def test_sub_class_of_axiom(self):
        ax = OWLSubClassOfAxiom(self.student, self.person)
        self.assertEqual(ax.signature(), {self.student, self.person})

    def test_equivalent_and_disjoint_classes_axioms(self):
        self.assertEqual(OWLEquivalentClassesAxiom([self.student, self.person]).signature(),
                         {self.student, self.person})
        self.assertEqual(OWLDisjointClassesAxiom([self.student, self.person]).signature(),
                         {self.student, self.person})

    def test_object_property_domain_and_range_axioms(self):
        self.assertEqual(OWLObjectPropertyDomainAxiom(self.has_child, self.person).signature(),
                         {self.has_child, self.person})
        self.assertEqual(OWLObjectPropertyRangeAxiom(self.has_child, self.person).signature(),
                         {self.has_child, self.person})

    def test_data_property_domain_and_range_axioms(self):
        self.assertEqual(OWLDataPropertyDomainAxiom(self.age, self.person).signature(),
                         {self.age, self.person})
        self.assertEqual(OWLDataPropertyRangeAxiom(self.age, IntegerOWLDatatype).signature(),
                         {self.age, IntegerOWLDatatype})

    def test_extract_classes_doc_example(self):
        """Regression test for https://github.com/dice-group/owlapy/issues/230: axiom.signature()
        must exist and support `cls in axiom.signature()`, as documented in
        markdown_docs/03_ontology_management.md's extract_classes() example."""
        axioms = [
            OWLSubClassOfAxiom(self.student, self.person),
            OWLObjectPropertyDomainAxiom(self.has_child, self.person),
            OWLClassAssertionAxiom(self.alice, self.student),
        ]
        selected = [self.person]
        extracted = [ax for cls in selected for ax in axioms if cls in ax.signature()]
        self.assertEqual(len(extracted), 2)
        self.assertIn(axioms[0], extracted)
        self.assertIn(axioms[1], extracted)
        self.assertNotIn(axioms[2], extracted)

    def test_unimplemented_axiom_type_raises_not_implemented_error(self):
        """Axiom types outside the core set (see issue #231) should fail loudly, not silently
        return an incomplete/wrong signature."""
        with self.assertRaises(NotImplementedError):
            OWLFunctionalObjectPropertyAxiom(self.has_child).signature()


if __name__ == '__main__':
    unittest.main()
