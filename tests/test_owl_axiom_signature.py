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
    OWLAnnotation,
    OWLAnnotationAssertionAxiom,
    OWLAnnotationProperty,
    OWLAnnotationPropertyDomainAxiom,
    OWLAnnotationPropertyRangeAxiom,
    OWLClassAssertionAxiom,
    OWLDataPropertyAssertionAxiom,
    OWLDataPropertyDomainAxiom,
    OWLDataPropertyRangeAxiom,
    OWLDatatypeDefinitionAxiom,
    OWLDeclarationAxiom,
    OWLDifferentIndividualsAxiom,
    OWLDisjointClassesAxiom,
    OWLDisjointUnionAxiom,
    OWLEquivalentClassesAxiom,
    OWLFunctionalDataPropertyAxiom,
    OWLFunctionalObjectPropertyAxiom,
    OWLHasKeyAxiom,
    OWLInverseObjectPropertiesAxiom,
    OWLObjectPropertyAssertionAxiom,
    OWLObjectPropertyDomainAxiom,
    OWLObjectPropertyRangeAxiom,
    OWLSameIndividualAxiom,
    OWLSubAnnotationPropertyOfAxiom,
    OWLSubClassOfAxiom,
    OWLSubObjectPropertyOfAxiom,
    OWLSubPropertyChainAxiom,
    OWLTransitiveObjectPropertyAxiom,
)
from owlapy.owl_individual import OWLAnonymousIndividual, OWLNamedIndividual
from owlapy.owl_literal import IntegerOWLDatatype, OWLLiteral, StringOWLDatatype
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

class TestExtendedAxiomSignature(unittest.TestCase):
    """Covers the axiom types added to close out https://github.com/dice-group/owlapy/issues/231."""

    def setUp(self):
        self.person = OWLClass(IRI(NS, "Person"))
        self.student = OWLClass(IRI(NS, "Student"))
        self.worker = OWLClass(IRI(NS, "Worker"))
        self.has_child = OWLObjectProperty(IRI(NS, "hasChild"))
        self.knows = OWLObjectProperty(IRI(NS, "knows"))
        self.age = OWLDataProperty(IRI(NS, "age"))
        self.alice = OWLNamedIndividual(IRI(NS, "Alice"))
        self.bob = OWLNamedIndividual(IRI(NS, "Bob"))
        self.label = OWLAnnotationProperty(IRI(NS, "label"))

    def test_object_property_characteristic_axioms(self):
        self.assertEqual(OWLFunctionalObjectPropertyAxiom(self.has_child).signature(), {self.has_child})
        self.assertEqual(OWLTransitiveObjectPropertyAxiom(self.has_child).signature(), {self.has_child})

    def test_data_property_characteristic_axiom(self):
        self.assertEqual(OWLFunctionalDataPropertyAxiom(self.age).signature(), {self.age})

    def test_sub_object_property_of_axiom(self):
        self.assertEqual(OWLSubObjectPropertyOfAxiom(self.has_child, self.knows).signature(),
                          {self.has_child, self.knows})

    def test_sub_property_chain_axiom(self):
        ax = OWLSubPropertyChainAxiom([self.has_child, self.knows], self.knows)
        self.assertEqual(ax.signature(), {self.has_child, self.knows})

    def test_same_and_different_individuals_axioms(self):
        self.assertEqual(OWLSameIndividualAxiom([self.alice, self.bob]).signature(), {self.alice, self.bob})
        self.assertEqual(OWLDifferentIndividualsAxiom([self.alice, self.bob]).signature(), {self.alice, self.bob})

    def test_inverse_object_properties_axiom(self):
        self.assertEqual(OWLInverseObjectPropertiesAxiom(self.has_child, self.knows).signature(),
                          {self.has_child, self.knows})

    def test_disjoint_union_axiom(self):
        ax = OWLDisjointUnionAxiom(self.person, [self.student, self.worker])
        self.assertEqual(ax.signature(), {self.person, self.student, self.worker})

    def test_has_key_axiom(self):
        ax = OWLHasKeyAxiom(self.person, [self.has_child, self.age])
        self.assertEqual(ax.signature(), {self.person, self.has_child, self.age})

    def test_datatype_definition_axiom(self):
        ax = OWLDatatypeDefinitionAxiom(IntegerOWLDatatype, StringOWLDatatype)
        self.assertEqual(ax.signature(), {IntegerOWLDatatype, StringOWLDatatype})

    def test_annotation_assertion_axiom_with_literal_value(self):
        ax = OWLAnnotationAssertionAxiom(self.person.iri, OWLAnnotation(self.label, OWLLiteral("Person")))
        self.assertEqual(ax.signature(), {self.label, StringOWLDatatype})

    def test_annotation_assertion_axiom_iri_subject_and_value_excluded(self):
        """A raw IRI subject/value contributes nothing -- only the annotation property (an OWLEntity)
        is part of the signature."""
        ax = OWLAnnotationAssertionAxiom(self.person.iri, OWLAnnotation(self.label, IRI(NS, "SomeThing")))
        self.assertEqual(ax.signature(), {self.label})

    def test_sub_annotation_property_of_axiom(self):
        super_label = OWLAnnotationProperty(IRI(NS, "superLabel"))
        ax = OWLSubAnnotationPropertyOfAxiom(self.label, super_label)
        self.assertEqual(ax.signature(), {self.label, super_label})

    def test_annotation_property_domain_and_range_axioms(self):
        self.assertEqual(OWLAnnotationPropertyDomainAxiom(self.label, self.person.iri).signature(), {self.label})
        self.assertEqual(OWLAnnotationPropertyRangeAxiom(self.label, self.person.iri).signature(), {self.label})


if __name__ == '__main__':
    unittest.main()
