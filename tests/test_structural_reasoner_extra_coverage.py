"""Targeted unit tests closing coverage gaps in StructuralReasoner (owlapy.owl_reasoner),
focused on object/data property relations (equivalent/disjoint/sub/super) and property
value retrieval -- built on a small hand-crafted in-memory Ontology so every branch
(top/bottom sentinels, equivalence workarounds, inverse properties) is reachable
without depending on the shape of the Family benchmark ontology used elsewhere.
"""
import time
import unittest
from unittest.mock import patch

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_axiom import (
    OWLClassAssertionAxiom,
    OWLDataPropertyAssertionAxiom,
    OWLDisjointDataPropertiesAxiom,
    OWLDisjointObjectPropertiesAxiom,
    OWLEquivalentDataPropertiesAxiom,
    OWLEquivalentObjectPropertiesAxiom,
    OWLInverseObjectPropertiesAxiom,
    OWLObjectPropertyAssertionAxiom,
    OWLSameIndividualAxiom,
    OWLSubDataPropertyOfAxiom,
    OWLSubObjectPropertyOfAxiom,
)
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import (
    OWLBottomDataProperty,
    OWLBottomObjectProperty,
    OWLLiteral,
    OWLTopDataProperty,
    OWLTopObjectProperty,
)
from owlapy.owl_ontology import Ontology
from owlapy.owl_property import OWLDataProperty, OWLObjectInverseOf, OWLObjectProperty
from owlapy.owl_reasoner import StructuralReasoner

NS = "http://example.com/structural_extra#"


def cls(name):
    return OWLClass(IRI.create(NS, name))


def ind(name):
    return OWLNamedIndividual(IRI.create(NS, name))


def obj_prop(name):
    return OWLObjectProperty(IRI.create(NS, name))


def data_prop(name):
    return OWLDataProperty(IRI.create(NS, name))


class TestStructuralReasonerPropertyRelations(unittest.TestCase):
    @classmethod
    def setUpClass(cls_):
        onto = Ontology(NS, load=False)

        p1, p2, p3, p4 = obj_prop("p1"), obj_prop("p2"), obj_prop("p3"), obj_prop("p4")
        d1, d2, d3, d4 = data_prop("d1"), data_prop("d2"), data_prop("d3"), data_prop("d4")
        inv_p1 = obj_prop("invP1")

        onto.add_axiom(OWLEquivalentObjectPropertiesAxiom([p1, p2]))
        onto.add_axiom(OWLDisjointObjectPropertiesAxiom([p1, p3]))
        onto.add_axiom(OWLSubObjectPropertyOfAxiom(p4, p1))
        onto.add_axiom(OWLInverseObjectPropertiesAxiom(p1, inv_p1))

        onto.add_axiom(OWLEquivalentDataPropertiesAxiom([d1, d2]))
        onto.add_axiom(OWLDisjointDataPropertiesAxiom([d1, d3]))
        onto.add_axiom(OWLSubDataPropertyOfAxiom(d4, d1))

        person = cls("Person")
        alice, bob, carol = ind("alice"), ind("bob"), ind("carol")
        onto.add_axiom(OWLClassAssertionAxiom(alice, person))
        onto.add_axiom(OWLClassAssertionAxiom(bob, person))
        onto.add_axiom(OWLClassAssertionAxiom(carol, person))
        onto.add_axiom(OWLObjectPropertyAssertionAxiom(alice, p1, bob))
        onto.add_axiom(OWLDataPropertyAssertionAxiom(alice, d1, OWLLiteral(30)))
        onto.add_axiom(OWLSameIndividualAxiom([alice, carol]))

        cls_.onto = onto
        cls_.reasoner = StructuralReasoner(onto)
        cls_.p1, cls_.p2, cls_.p3, cls_.p4, cls_.inv_p1 = p1, p2, p3, p4, inv_p1
        cls_.d1, cls_.d2, cls_.d3, cls_.d4 = d1, d2, d3, d4
        cls_.alice, cls_.bob, cls_.carol = alice, bob, carol

    # -- equivalent / disjoint / sub / super object properties --------------

    def test_equivalent_object_properties(self):
        equiv = set(self.reasoner.equivalent_object_properties(self.p1))
        self.assertIn(self.p2, equiv)

    def test_equivalent_object_properties_of_inverse_raises_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            list(self.reasoner.equivalent_object_properties(OWLObjectInverseOf(self.p1)))

    def test_disjoint_object_properties_finds_declared_disjoint(self):
        disjoint = set(self.reasoner.disjoint_object_properties(self.p1))
        self.assertIn(self.p3, disjoint)

    def test_disjoint_object_properties_bottom_sentinel(self):
        disjoint = set(self.reasoner.disjoint_object_properties(OWLBottomObjectProperty))
        self.assertIn(OWLTopObjectProperty, disjoint)

    def test_disjoint_object_properties_top_sentinel(self):
        disjoint = set(self.reasoner.disjoint_object_properties(OWLTopObjectProperty))
        self.assertEqual(disjoint, {OWLBottomObjectProperty})

    def test_sub_object_properties(self):
        subs = set(self.reasoner.sub_object_properties(self.p1))
        self.assertIn(self.p4, subs)

    def test_super_object_properties(self):
        supers = set(self.reasoner.super_object_properties(self.p4))
        self.assertIn(self.p1, supers)

    # -- equivalent / disjoint / sub / super data properties -----------------

    def test_equivalent_data_properties(self):
        equiv = set(self.reasoner.equivalent_data_properties(self.d1))
        self.assertIn(self.d2, equiv)

    def test_disjoint_data_properties_finds_declared_disjoint(self):
        disjoint = set(self.reasoner.disjoint_data_properties(self.d1))
        self.assertIn(self.d3, disjoint)

    def test_disjoint_data_properties_bottom_sentinel(self):
        disjoint = set(self.reasoner.disjoint_data_properties(OWLBottomDataProperty))
        self.assertIn(OWLTopDataProperty, disjoint)

    def test_disjoint_data_properties_top_sentinel(self):
        disjoint = set(self.reasoner.disjoint_data_properties(OWLTopDataProperty))
        self.assertEqual(disjoint, {OWLBottomDataProperty})

    def test_sub_data_properties(self):
        subs = set(self.reasoner.sub_data_properties(self.d1))
        self.assertIn(self.d4, subs)

    def test_super_data_properties(self):
        supers = set(self.reasoner.super_data_properties(self.d4))
        self.assertIn(self.d1, supers)

    # -- property values / same individuals -----------------------------------

    def test_object_property_values_direct_property(self):
        values = set(self.reasoner.object_property_values(self.alice, self.p1))
        self.assertIn(self.bob, values)

    def test_object_property_values_explicit_inverse(self):
        values = set(self.reasoner.object_property_values(self.bob, OWLObjectInverseOf(self.p1)))
        self.assertIn(self.alice, values)

    def test_object_property_values_unsupported_property_type_raises(self):
        with self.assertRaises(NotImplementedError):
            list(self.reasoner.object_property_values(self.alice, "not a property expression"))

    def test_data_property_values(self):
        values = set(self.reasoner.data_property_values(self.alice, self.d1))
        self.assertIn(OWLLiteral(30), values)

    def test_all_data_property_values_direct(self):
        values = set(self.reasoner.all_data_property_values(self.d1, direct=True))
        self.assertIn(OWLLiteral(30), values)

    def test_same_individuals(self):
        same = set(self.reasoner.same_individuals(self.alice))
        self.assertIn(self.carol, same)

    def test_types_direct(self):
        direct_types = set(self.reasoner.types(self.alice, direct=True))
        self.assertIn(cls("Person"), direct_types)

    # -- instances() timeout (regression test for owlapy#260) -----------------

    def test_instances_timeout_is_enforced(self):
        # Previously, StructuralReasoner.instances(timeout=...) never actually enforced
        # anything: _instances() was a generator function, so the timeout only ever bounded
        # how long it took to *create* the generator (near-instant), not to enumerate it --
        # the real work happened lazily, outside the timeout-protected region. Simulate a slow
        # underlying computation and assert the call now genuinely returns within the timeout
        # (with an empty result) instead of blocking for the full duration.
        def _slow_find_instances(self_, ce):
            time.sleep(2)
            return frozenset({self.alice})

        with patch.object(type(self.reasoner), "_find_instances", _slow_find_instances):
            start = time.time()
            result = self.reasoner.instances(cls("Person"), timeout=0.2)
            elapsed = time.time() - start

        self.assertEqual(result, set())
        self.assertLess(elapsed, 1.0)


if __name__ == '__main__':
    unittest.main()
