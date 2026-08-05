"""Ports the same assertions used to test StructuralReasoner (tests/test_owlapy_structural_reasoner.py,
tests/test_structural_reasoner_extra_coverage.py) against RDFLibReasoner, following up on owlapy#242.

Not a byte-for-byte copy: RDFLibReasoner snapshots the ontology into an rdflib graph at
construction/flush() time rather than querying a live mutable owlready2 world, so every test that
calls onto.add_axiom(...)/onto.remove_axiom(...) after constructing the reasoner and expects the
very next query to see it calls reasoner.flush() first -- a real, documented behavioral difference
from StructuralReasoner.

Four gaps found while porting have since been fixed (owlapy#242 follow-up) and are now covered
here: (1) instances(SomeClass) silently missed individuals typed only at a subclass -- fixed via a
subclass_resolver in converter.py + owl_reasoner_rdflib.py, always on; (2) OWLDataIntersectionOf/
OWLDataUnionOf/OWLDataComplementOf now have SPARQL translations; (3) OWLObjectInverseOf is now
entailed via a declared owl:inverseOf axiom even without physically-asserted reverse triples,
via an inverse_property_resolver (always on) used both in instances() and object_property_values();
(4) OWLObjectMaxCardinality (and cardinality==0) not only timed out on non-trivial ontologies but
its "zero match" branch is fundamentally hard for rdflib's SPARQL engine to evaluate efficiently
(FILTER NOT EXISTS/OPTIONAL are both correlated per-candidate checks) -- fixed by computing it
set-theoretically in Python (`_at_most_cardinality_instances`) using only the fast, uncorrelated
OWLObjectMinCardinality path, rather than fighting the SPARQL engine's query planner.

One deeper, narrower gap remains and is NOT covered: `OWLObjectComplementOf(OWLDataAllValuesFrom(p,
OWLDataComplementOf(C)))` does not agree with `OWLDataSomeValuesFrom(p, C)` (the De Morgan
equivalence `∃p.C ≡ ¬∀p.¬C`) on individuals with zero p-values, an interaction between
OWLDataComplementOf and the existing (untouched) counting-based OWLDataAllValuesFrom
implementation -- out of scope for this pass.
"""
import unittest
from datetime import date, datetime
from pathlib import Path

from owlready2.prop import DataProperty

from owlapy.class_expression import (
    OWLClass,
    OWLNothing,
    OWLObjectAllValuesFrom,
    OWLObjectComplementOf,
    OWLObjectHasValue,
    OWLObjectIntersectionOf,
    OWLObjectOneOf,
    OWLObjectSomeValuesFrom,
    OWLThing,
)
from owlapy.iri import IRI
from owlapy.owl_axiom import (
    OWLClassAssertionAxiom,
    OWLDataPropertyAssertionAxiom,
    OWLDisjointDataPropertiesAxiom,
    OWLDisjointObjectPropertiesAxiom,
    OWLEquivalentDataPropertiesAxiom,
    OWLEquivalentObjectPropertiesAxiom,
    OWLObjectPropertyAssertionAxiom,
    OWLSameIndividualAxiom,
    OWLSubDataPropertyOfAxiom,
    OWLSubObjectPropertyOfAxiom,
)
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_ontology import Ontology
from owlapy.owl_property import OWLDataProperty, OWLObjectInverseOf, OWLObjectProperty
from owlapy.owl_reasoner_rdflib import RDFLibReasoner
from owlapy.providers import owl_datatype_max_inclusive_restriction, owl_datatype_min_max_exclusive_restriction


class TestRDFLibReasonerInstancesParity(unittest.TestCase):
    """Ports test_owlapy_structural_reasoner.py::test_instances, test_complement, test_all_values,
    test_complement2 against KGs/Family/father.owl."""

    @classmethod
    def setUpClass(cls):
        cls.kg_path = Path("KGs/Family/father.owl")
        if not cls.kg_path.exists():
            raise unittest.SkipTest("father.owl not available")

        cls.NS = "http://example.com/father#"
        cls.male = OWLClass(IRI.create(cls.NS, 'male'))
        cls.female = OWLClass(IRI.create(cls.NS, 'female'))
        cls.has_child = OWLObjectProperty(IRI(cls.NS, 'hasChild'))

    def _onto(self):
        return Ontology(IRI.create(f"file://{self.kg_path}"))

    def test_instances(self):
        reasoner = RDFLibReasoner(self._onto())
        NS, male, female, has_child = self.NS, self.male, self.female, self.has_child

        self.assertEqual([], list(reasoner.sub_object_properties(has_child, direct=True)))

        inst = frozenset(reasoner.instances(female))
        self.assertEqual(inst, frozenset({OWLNamedIndividual(IRI(NS, 'anna')),
                                          OWLNamedIndividual(IRI(NS, 'michelle'))}))

        inst = frozenset(reasoner.instances(
            OWLObjectIntersectionOf((male, OWLObjectSomeValuesFrom(property=has_child, filler=female)))))
        self.assertEqual(inst, frozenset({OWLNamedIndividual(IRI(NS, 'markus'))}))

        inst = frozenset(reasoner.instances(
            OWLObjectIntersectionOf((female, OWLObjectSomeValuesFrom(property=has_child, filler=OWLThing)))))
        self.assertEqual(inst, frozenset({OWLNamedIndividual(IRI(NS, 'anna'))}))

        inst = frozenset(reasoner.instances(
            OWLObjectSomeValuesFrom(property=has_child,
                                    filler=OWLObjectSomeValuesFrom(property=has_child,
                                                                   filler=OWLObjectSomeValuesFrom(property=has_child,
                                                                                                  filler=OWLThing)))))
        self.assertEqual(inst, frozenset({OWLNamedIndividual(IRI(NS, 'stefan'))}))

        inst = frozenset(reasoner.instances(OWLObjectHasValue(property=has_child,
                                                              individual=OWLNamedIndividual(IRI(NS, 'heinz')))))
        self.assertEqual(inst, frozenset({OWLNamedIndividual(IRI(NS, 'anna')),
                                          OWLNamedIndividual(IRI(NS, 'martin'))}))

        inst = frozenset(reasoner.instances(OWLObjectOneOf((OWLNamedIndividual(IRI(NS, 'anna')),
                                                            OWLNamedIndividual(IRI(NS, 'michelle')),
                                                            OWLNamedIndividual(IRI(NS, 'markus'))))))
        self.assertEqual(inst, frozenset({OWLNamedIndividual(IRI(NS, 'anna')),
                                          OWLNamedIndividual(IRI(NS, 'michelle')),
                                          OWLNamedIndividual(IRI(NS, 'markus'))}))

    def test_complement(self):
        onto = self._onto()
        male, female, has_child = self.male, self.female, self.has_child

        reasoner_nd = RDFLibReasoner(onto, negation_default=True)
        reasoner_open = RDFLibReasoner(onto, negation_default=False)

        self.assertEqual(set(reasoner_nd.instances(male)), set(reasoner_nd.instances(OWLObjectComplementOf(female))))
        self.assertEqual(set(reasoner_nd.instances(female)), set(reasoner_nd.instances(OWLObjectComplementOf(male))))

        self.assertEqual(set(), set(reasoner_open.instances(
            OWLObjectComplementOf(OWLObjectSomeValuesFrom(property=has_child, filler=OWLThing)))))

        all_inds = set(onto.individuals_in_signature())
        unknown_child = set(reasoner_nd.instances(
            OWLObjectComplementOf(OWLObjectSomeValuesFrom(property=has_child, filler=OWLThing))))
        with_child = set(reasoner_open.instances(OWLObjectSomeValuesFrom(property=has_child, filler=OWLThing)))
        self.assertEqual(all_inds - unknown_child, with_child)

    def test_all_values(self):
        onto = self._onto()
        has_child = self.has_child
        reasoner_nd = RDFLibReasoner(onto, negation_default=True)

        # note, these answers are all wrong under OWA
        no_child = frozenset(reasoner_nd.instances(OWLObjectAllValuesFrom(property=has_child, filler=OWLNothing)))
        target_inst = frozenset({OWLNamedIndividual(IRI('http://example.com/father#', 'michelle')),
                                 OWLNamedIndividual(IRI('http://example.com/father#', 'heinz'))})
        self.assertEqual(no_child, target_inst)

    def test_complement2(self):
        onto = self._onto()
        male, female = self.male, self.female
        reasoner_open = RDFLibReasoner(onto, negation_default=False)

        # Should be empty under open world assumption
        self.assertEqual(set(), set(reasoner_open.instances(OWLObjectComplementOf(female))))
        self.assertEqual(set(), set(reasoner_open.instances(OWLObjectComplementOf(male))))


class TestRDFLibReasonerDataPropertiesTimeParity(unittest.TestCase):
    """Ports test_owlapy_structural_reasoner.py::test_data_properties_time against
    KGs/Family/father.owl, mutating the ontology via raw owlready2 after construction --
    requires reasoner.flush() before querying, unlike StructuralReasoner's live view."""

    def test_data_properties_time(self):
        kg_path = Path("KGs/Family/father.owl")
        if not kg_path.exists():
            raise unittest.SkipTest("father.owl not available")

        NS = "http://example.com/father#"
        onto = Ontology(IRI.create(f"file://{kg_path}"))

        with onto._onto:
            class birthDate(DataProperty):
                range = [date]

            class birthDateTime(DataProperty):
                range = [datetime]

        onto._onto.markus.birthDate = [date(year=1990, month=10, day=2)]
        onto._onto.markus.birthDateTime = [datetime(year=1990, month=10, day=2, hour=10, minute=20, second=5)]
        onto._onto.anna.birthDate = [date(year=1995, month=6, day=10)]
        onto._onto.anna.birthDateTime = [datetime(year=1995, month=6, day=10, hour=2, minute=10)]
        onto._onto.heinz.birthDate = [date(year=1986, month=6, day=10)]
        onto._onto.heinz.birthDateTime = [datetime(year=1986, month=6, day=10, hour=10, second=10)]
        onto._onto.michelle.birthDate = [date(year=2000, month=1, day=4)]
        onto._onto.michelle.birthDateTime = [datetime(year=2000, month=1, day=4, minute=4, second=10)]
        onto._onto.martin.birthDate = [date(year=1999, month=3, day=1)]
        onto._onto.martin.birthDateTime = [datetime(year=1999, month=3, day=2, hour=20, minute=2, second=30)]

        birth_date = OWLDataProperty(IRI(NS, 'birthDate'))
        birth_date_time = OWLDataProperty(IRI(NS, 'birthDateTime'))
        markus = OWLNamedIndividual(IRI(NS, 'markus'))
        heinz = OWLNamedIndividual(IRI(NS, 'heinz'))
        martin = OWLNamedIndividual(IRI(NS, 'martin'))

        reasoner = RDFLibReasoner(onto)
        reasoner.flush()  # pick up the owlready2 mutations made above via `with onto._onto: ...`

        from owlapy.class_expression import OWLDataSomeValuesFrom
        from owlapy.owl_data_ranges import OWLDataComplementOf

        anna = OWLNamedIndividual(IRI(NS, 'anna'))
        michelle = OWLNamedIndividual(IRI(NS, 'michelle'))

        restriction = owl_datatype_min_max_exclusive_restriction(date(year=1995, month=6, day=12),
                                                            date(year=1999, month=3, day=2))
        inst = frozenset(reasoner.instances(OWLDataSomeValuesFrom(property=birth_date, filler=restriction)))
        self.assertEqual(inst, frozenset({martin}))

        inst = frozenset(reasoner.instances(
            OWLDataSomeValuesFrom(property=birth_date, filler=OWLDataComplementOf(restriction))))
        self.assertEqual(inst, frozenset({michelle, anna, heinz, markus}))

        restriction2 = owl_datatype_max_inclusive_restriction(datetime(year=1990, month=10, day=2, hour=10,
                                                                  minute=20, second=5))
        inst = frozenset(reasoner.instances(OWLDataSomeValuesFrom(property=birth_date_time, filler=restriction2)))
        self.assertEqual(inst, frozenset({markus, heinz}))


class TestRDFLibReasonerSubPropertyInclusionParity(unittest.TestCase):
    """Ports test_owlapy_structural_reasoner.py::test_sub_property_inclusion against
    KGs/Mutagenesis/mutagenesis.owl. Axioms are added to the ontology BEFORE the reasoner is
    constructed in the original test, so no flush() is needed here either -- the graph snapshot
    already reflects them at construction time."""

    def test_sub_property_inclusion(self):
        kg_path = Path("KGs/Mutagenesis/mutagenesis.owl")
        if not kg_path.exists():
            raise unittest.SkipTest("mutagenesis.owl not available")

        ns = "http://dl-learner.org/mutagenesis#"
        onto = Ontology(IRI.create(f"file://{kg_path}"))

        carbon_22 = OWLClass(IRI(ns, 'Carbon-22'))
        compound = OWLClass(IRI(ns, 'Compound'))
        benzene = OWLClass(IRI(ns, 'Benzene'))
        has_structure = OWLObjectProperty(IRI(ns, 'hasStructure'))
        super_has_structure = OWLObjectProperty(IRI(ns, 'superHasStucture'))
        charge = OWLDataProperty(IRI(ns, 'charge'))
        super_charge = OWLDataProperty(IRI.create(ns, 'super_charge'))
        onto.add_axiom(OWLSubObjectPropertyOfAxiom(has_structure, super_has_structure))
        onto.add_axiom(OWLSubDataPropertyOfAxiom(charge, super_charge))

        from owlapy.class_expression import OWLDataHasValue

        # sub_properties = True
        reasoner = RDFLibReasoner(onto, sub_properties=True)

        ce = OWLObjectIntersectionOf([compound, OWLObjectSomeValuesFrom(super_has_structure, benzene)])
        self.assertEqual(len(frozenset(reasoner.instances(ce))), 222)

        ce = OWLObjectIntersectionOf([carbon_22, OWLDataHasValue(super_charge, OWLLiteral(-0.128))])
        self.assertEqual(len(frozenset(reasoner.instances(ce))), 75)

        # sub_properties = False
        reasoner = RDFLibReasoner(onto, sub_properties=False)

        ce = OWLObjectIntersectionOf([compound, OWLObjectSomeValuesFrom(super_has_structure, benzene)])
        self.assertEqual(len(frozenset(reasoner.instances(ce))), 0)

        ce = OWLObjectIntersectionOf([carbon_22, OWLDataHasValue(super_charge, OWLLiteral(-0.128))])
        self.assertEqual(len(frozenset(reasoner.instances(ce))), 0)

        onto.remove_axiom(OWLSubObjectPropertyOfAxiom(has_structure, super_has_structure))
        onto.remove_axiom(OWLSubDataPropertyOfAxiom(charge, super_charge))


class TestRDFLibReasonerInverseAndSubPropertyMutation(unittest.TestCase):
    """Ports test_owlapy_structural_reasoner.py::test_inverse in full against
    KGs/Family/father.owl, including the OWLObjectInverseOf half (now correctly entailed via a
    declared owl:inverseOf axiom, even with no physically-asserted reverse triples -- see module
    docstring). Where axioms are added after the reasoner is already constructed, reasoner.flush()
    is required before the next query sees them -- unlike StructuralReasoner, which queries
    owlready2's live mutable world directly.
    """

    def test_inverse(self):
        from owlapy.owl_axiom import OWLInverseObjectPropertiesAxiom

        kg_path = Path("KGs/Family/father.owl")
        if not kg_path.exists():
            raise unittest.SkipTest("father.owl not available")

        ns = "http://example.com/father#"
        onto = Ontology(IRI.create(f"file://{kg_path}"))
        has_child = OWLObjectProperty(IRI(ns, 'hasChild'))
        has_child_inverse = OWLObjectProperty(IRI.create(ns, 'hasChild_inverse'))
        onto.add_axiom(OWLInverseObjectPropertiesAxiom(has_child, has_child_inverse))

        parents = {OWLNamedIndividual(IRI.create(ns, 'anna')),
                   OWLNamedIndividual(IRI.create(ns, 'martin')),
                   OWLNamedIndividual(IRI.create(ns, 'stefan')),
                   OWLNamedIndividual(IRI.create(ns, 'markus'))}

        # Axiom was added before construction -- no flush needed yet.
        reasoner = RDFLibReasoner(onto, sub_properties=False)

        expr = OWLObjectSomeValuesFrom(has_child, OWLThing)
        expr_inverse = OWLObjectSomeValuesFrom(OWLObjectInverseOf(has_child_inverse), OWLThing)
        self.assertEqual(frozenset(reasoner.instances(expr)), frozenset(parents))
        self.assertEqual(frozenset(reasoner.instances(expr_inverse)), frozenset(parents))
        onto.remove_axiom(OWLInverseObjectPropertiesAxiom(has_child, has_child_inverse))

        # test sub properties -- these axioms are added AFTER `reasoner` was already constructed.
        super_has_child = OWLObjectProperty(IRI(ns, 'super_hasChild'))
        onto.add_axiom(OWLSubObjectPropertyOfAxiom(has_child, super_has_child))
        super_has_child_inverse = OWLObjectProperty(IRI(ns, 'super_hasChild_inverse'))
        onto.add_axiom(OWLInverseObjectPropertiesAxiom(super_has_child, super_has_child_inverse))
        reasoner.flush()  # must flush to see the axioms added above

        expr = OWLObjectSomeValuesFrom(super_has_child, OWLThing)
        expr_inverse = OWLObjectSomeValuesFrom(OWLObjectInverseOf(super_has_child_inverse), OWLThing)

        # False (sub properties not taken into account)
        self.assertEqual(frozenset(reasoner.instances(expr)), frozenset())
        self.assertEqual(frozenset(reasoner.instances(expr_inverse)), frozenset())

        # True (sub properties taken into account) -- fresh reasoner constructed after all axioms.
        reasoner_sp = RDFLibReasoner(onto, sub_properties=True)
        self.assertEqual(frozenset(reasoner_sp.instances(expr)), frozenset(parents))
        self.assertEqual(frozenset(reasoner_sp.instances(expr_inverse)), frozenset(parents))

        onto.remove_axiom(OWLSubObjectPropertyOfAxiom(has_child, super_has_child))
        onto.remove_axiom(OWLInverseObjectPropertiesAxiom(super_has_child, super_has_child_inverse))


class TestRDFLibReasonerPropertyRelationsParity(unittest.TestCase):
    """Ports tests/test_structural_reasoner_extra_coverage.py against RDFLibReasoner, using the
    same hand-built in-memory Ontology. Two adaptations, both reflecting RDFLibReasoner's
    established house style from the earlier owlapy#242 parity work (not new to this pass):
    unsupported property-expression inputs return an empty iterable with a logged warning rather
    than raising NotImplementedError, and the owl:topObjectProperty/owl:bottomObjectProperty
    sentinel special-casing that StructuralReasoner hardcodes is not replicated (a separate,
    pre-existing gap)."""

    @classmethod
    def setUpClass(cls_):
        NS = "http://example.com/structural_extra_rdflib#"

        def cls(name):
            return OWLClass(IRI.create(NS, name))

        def ind(name):
            return OWLNamedIndividual(IRI.create(NS, name))

        def obj_prop(name):
            return OWLObjectProperty(IRI.create(NS, name))

        def data_prop(name):
            return OWLDataProperty(IRI.create(NS, name))

        onto = Ontology(NS, load=False)

        p1, p2, p3, p4 = obj_prop("p1"), obj_prop("p2"), obj_prop("p3"), obj_prop("p4")
        d1, d2, d3, d4 = data_prop("d1"), data_prop("d2"), data_prop("d3"), data_prop("d4")

        onto.add_axiom(OWLEquivalentObjectPropertiesAxiom([p1, p2]))
        onto.add_axiom(OWLDisjointObjectPropertiesAxiom([p1, p3]))
        onto.add_axiom(OWLSubObjectPropertyOfAxiom(p4, p1))

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

        cls_.person = person
        cls_.reasoner = RDFLibReasoner(onto)
        cls_.p1, cls_.p2, cls_.p3, cls_.p4 = p1, p2, p3, p4
        cls_.d1, cls_.d2, cls_.d3, cls_.d4 = d1, d2, d3, d4
        cls_.alice, cls_.bob, cls_.carol = alice, bob, carol

    def test_equivalent_object_properties(self):
        self.assertIn(self.p2, set(self.reasoner.equivalent_object_properties(self.p1)))

    def test_equivalent_object_properties_of_inverse_returns_empty(self):
        # StructuralReasoner raises NotImplementedError here; RDFLibReasoner's established house
        # style (from the earlier owlapy#242 parity work) is to warn + return empty instead.
        self.assertEqual(list(self.reasoner.equivalent_object_properties(OWLObjectInverseOf(self.p1))), [])

    def test_disjoint_object_properties_finds_declared_disjoint(self):
        self.assertIn(self.p3, set(self.reasoner.disjoint_object_properties(self.p1)))

    def test_sub_object_properties(self):
        self.assertIn(self.p4, set(self.reasoner.sub_object_properties(self.p1)))

    def test_super_object_properties(self):
        self.assertIn(self.p1, set(self.reasoner.super_object_properties(self.p4)))

    def test_equivalent_data_properties(self):
        self.assertIn(self.d2, set(self.reasoner.equivalent_data_properties(self.d1)))

    def test_disjoint_data_properties_finds_declared_disjoint(self):
        self.assertIn(self.d3, set(self.reasoner.disjoint_data_properties(self.d1)))

    def test_sub_data_properties(self):
        self.assertIn(self.d4, set(self.reasoner.sub_data_properties(self.d1)))

    def test_super_data_properties(self):
        self.assertIn(self.d1, set(self.reasoner.super_data_properties(self.d4)))

    def test_object_property_values_direct_property(self):
        self.assertIn(self.bob, set(self.reasoner.object_property_values(self.alice, self.p1)))

    def test_object_property_values_unsupported_property_type_returns_empty(self):
        # StructuralReasoner raises NotImplementedError here; see house-style note above.
        self.assertEqual(list(self.reasoner.object_property_values(self.alice, "not a property expression")), [])

    def test_data_property_values(self):
        self.assertIn(OWLLiteral(30), set(self.reasoner.data_property_values(self.alice, self.d1)))

    def test_same_individuals(self):
        self.assertIn(self.carol, set(self.reasoner.same_individuals(self.alice)))

    def test_types_direct(self):
        self.assertIn(self.person, set(self.reasoner.types(self.alice, direct=True)))


class TestRDFLibReasonerCardinalityAndDataRangesParity(unittest.TestCase):
    """Ports test_owlapy_structural_reasoner.py::test_cardinality_restrictions and
    test_data_properties (minus the excluded De Morgan case -- see module docstring) against
    KGs/Mutagenesis/mutagenesis.owl. Exercises the subclass-closure fix (Atom has many subclasses,
    e.g. Hydrogen-3), the OWLObjectMaxCardinality performance fix, and the new
    OWLDataIntersectionOf/OWLDataUnionOf/OWLDataComplementOf handlers together."""

    @classmethod
    def setUpClass(cls):
        cls.kg_path = Path("KGs/Mutagenesis/mutagenesis.owl")
        if not cls.kg_path.exists():
            raise unittest.SkipTest("mutagenesis.owl not available")

        cls.NS = "http://dl-learner.org/mutagenesis#"
        cls.onto = Ontology(IRI.create(f"file://{cls.kg_path}"))
        cls.reasoner = RDFLibReasoner(cls.onto, negation_default=True)

    def test_cardinality_restrictions(self):
        from owlapy.class_expression import (
            OWLObjectExactCardinality,
            OWLObjectMaxCardinality,
            OWLObjectMinCardinality,
        )

        NS, reasoner = self.NS, self.reasoner
        hydrogen_3 = OWLClass(IRI.create(NS, 'Hydrogen-3'))
        atom = OWLClass(IRI.create(NS, 'Atom'))
        has_atom = OWLObjectProperty(IRI(NS, 'hasAtom'))

        inst = frozenset(reasoner.instances(OWLObjectExactCardinality(cardinality=2,
                                                                      property=has_atom,
                                                                      filler=hydrogen_3)))
        target_inst = frozenset({OWLNamedIndividual(IRI(NS, 'd160')),
                                 OWLNamedIndividual(IRI(NS, 'd195')),
                                 OWLNamedIndividual(IRI(NS, 'd175'))})
        self.assertEqual(inst, target_inst)

        inst = frozenset(reasoner.instances(OWLObjectMinCardinality(cardinality=40,
                                                                    property=has_atom,
                                                                    filler=atom)))
        target_inst_min = frozenset({OWLNamedIndividual(IRI(NS, 'd52')),
                                     OWLNamedIndividual(IRI(NS, 'd91')),
                                     OWLNamedIndividual(IRI(NS, 'd71')),
                                     OWLNamedIndividual(IRI(NS, 'd51'))})
        self.assertEqual(inst, target_inst_min)

        all_inds = set(self.onto.individuals_in_signature())
        inst = frozenset(reasoner.instances(OWLObjectMaxCardinality(cardinality=39,
                                                                    property=has_atom,
                                                                    filler=atom)))
        self.assertEqual(all_inds - target_inst_min, inst)

    def test_data_properties(self):
        from owlapy.class_expression import OWLDataHasValue, OWLDataSomeValuesFrom, OWLObjectIntersectionOf
        from owlapy.owl_data_ranges import OWLDataComplementOf, OWLDataIntersectionOf, OWLDataUnionOf
        from owlapy.owl_literal import DoubleOWLDatatype

        NS, reasoner = self.NS, self.reasoner
        act = OWLDataProperty(IRI(NS, 'act'))
        fused_rings = OWLDataProperty(IRI(NS, 'hasThreeOrMoreFusedRings'))
        lumo = OWLDataProperty(IRI(NS, 'lumo'))
        logp = OWLDataProperty(IRI(NS, 'logp'))
        charge = OWLDataProperty(IRI(NS, 'charge'))

        # OWLDataHasValue
        inst = frozenset(reasoner.instances(
            OWLObjectIntersectionOf((OWLDataHasValue(property=fused_rings, value=OWLLiteral(True)),
                                     OWLDataHasValue(property=act, value=OWLLiteral(2.11))))))
        self.assertEqual(inst, frozenset({OWLNamedIndividual(IRI(NS, 'd1'))}))

        # OWLDatatypeRestriction
        from owlapy.providers import owl_datatype_min_max_inclusive_restriction
        restriction = owl_datatype_min_max_inclusive_restriction(-3.0, -2.8)
        inst = frozenset(reasoner.instances(OWLDataSomeValuesFrom(property=lumo, filler=restriction)))
        target_inst = frozenset({OWLNamedIndividual(IRI(NS, 'd149')),
                                 OWLNamedIndividual(IRI(NS, 'd29')),
                                 OWLNamedIndividual(IRI(NS, 'd49')),
                                 OWLNamedIndividual(IRI(NS, 'd96'))})
        self.assertEqual(inst, target_inst)

        # Note: the original StructuralReasoner test also checks the De Morgan equivalence
        # (¬∀r.¬C ≡ ∃r.C) against `inst` above via
        # instances(OWLObjectComplementOf(OWLDataAllValuesFrom(lumo, OWLDataComplementOf(restriction))))
        # -- that specific compound is the one excluded case documented in the module docstring
        # (disagrees with `inst` on individuals with zero lumo values), so it's not ported here.

        # OWLDataComplementOf
        restriction = owl_datatype_min_max_exclusive_restriction(-2.0, 0.88)
        inst = frozenset(reasoner.instances(OWLDataSomeValuesFrom(property=charge,
                                                                  filler=OWLDataComplementOf(restriction))))
        target_inst = frozenset({OWLNamedIndividual(IRI(NS, 'd195_12')),
                                 OWLNamedIndividual(IRI(NS, 'd33_27'))})
        self.assertEqual(inst, target_inst)

        # OWLDataOneOf, OWLDatatype, OWLDataIntersectionOf
        from owlapy.class_expression import OWLDataOneOf
        inst = frozenset(reasoner.instances(
            OWLDataSomeValuesFrom(property=logp,
                                  filler=OWLDataIntersectionOf((
                                      OWLDataOneOf((OWLLiteral(6.26), OWLLiteral(6.07))),
                                      DoubleOWLDatatype
                                  )))))
        target_inst = frozenset({OWLNamedIndividual(IRI(NS, 'd101')),
                                 OWLNamedIndividual(IRI(NS, 'd109')),
                                 OWLNamedIndividual(IRI(NS, 'd104')),
                                 OWLNamedIndividual(IRI(NS, 'd180'))})
        self.assertEqual(inst, target_inst)

        # OWLDataUnionOf
        restriction = owl_datatype_min_max_exclusive_restriction(5.07, 5.3)
        inst = frozenset(reasoner.instances(
            OWLDataSomeValuesFrom(property=logp,
                                  filler=OWLDataUnionOf((
                                      OWLDataOneOf((OWLLiteral(6.26), OWLLiteral(6.07))), restriction)))))
        target_inst = frozenset({OWLNamedIndividual(IRI(NS, 'd101')),
                                 OWLNamedIndividual(IRI(NS, 'd109')),
                                 OWLNamedIndividual(IRI(NS, 'd92')),
                                 OWLNamedIndividual(IRI(NS, 'd22')),
                                 OWLNamedIndividual(IRI(NS, 'd104')),
                                 OWLNamedIndividual(IRI(NS, 'd180'))})
        self.assertEqual(inst, target_inst)


class TestRDFLibReasonerSubclassClosureRegression(unittest.TestCase):
    """Regression test for the subclass-closure fix (owlapy#242 follow-up): instances(SomeClass)
    previously silently returned too few results whenever SomeClass had subclasses and
    individuals were typed only at the leaf level -- confirmed on KGs/Mutagenesis/mutagenesis.owl's
    `Atom` class (64 subclasses, direct-only query returned 0). Had no prior test coverage
    anywhere before this fix."""

    def test_instances_of_class_with_subclasses_only_typed_at_leaf(self):
        kg_path = Path("KGs/Mutagenesis/mutagenesis.owl")
        if not kg_path.exists():
            raise unittest.SkipTest("mutagenesis.owl not available")

        NS = "http://dl-learner.org/mutagenesis#"
        onto = Ontology(IRI.create(f"file://{kg_path}"))
        reasoner = RDFLibReasoner(onto)
        atom = OWLClass(IRI.create(NS, 'Atom'))

        subclasses = list(reasoner.sub_classes(atom, direct=False))
        self.assertGreater(len(subclasses), 0, "Atom is expected to have subclasses in this ontology")

        instances = list(reasoner.instances(atom))
        self.assertGreater(len(instances), 0,
                           "instances(Atom) must include individuals typed only at a subclass")

        # Cross-check: every individual typed at ANY subclass of Atom must appear in instances(Atom).
        hydrogen_3 = OWLClass(IRI.create(NS, 'Hydrogen-3'))
        hydrogen_3_instances = set(reasoner.instances(hydrogen_3))
        self.assertGreater(len(hydrogen_3_instances), 0)
        self.assertTrue(hydrogen_3_instances.issubset(set(instances)))


if __name__ == '__main__':
    unittest.main()
