from datetime import date, datetime
import unittest

from owlapy.class_expression import OWLObjectOneOf, OWLObjectSomeValuesFrom, OWLThing, OWLObjectComplementOf, \
    OWLObjectAllValuesFrom, OWLNothing, OWLObjectHasValue, OWLClass, OWLDataAllValuesFrom, OWLDataHasValue, \
    OWLDataOneOf, OWLDataSomeValuesFrom, OWLObjectExactCardinality, OWLObjectMaxCardinality, OWLObjectMinCardinality, \
    OWLObjectIntersectionOf
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLSubDataPropertyOfAxiom, OWLInverseObjectPropertiesAxiom, OWLSubObjectPropertyOfAxiom
from owlapy.owl_data_ranges import OWLDataComplementOf, OWLDataIntersectionOf, OWLDataUnionOf
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import DoubleOWLDatatype, OWLLiteral
from owlapy.owl_ontology import Ontology
from owlapy.owl_property import OWLObjectInverseOf, OWLObjectProperty, OWLDataProperty
from owlready2.prop import DataProperty

from owlapy.owl_reasoner import StructuralReasoner

from owlapy.providers import owl_datatype_min_max_inclusive_restriction, owl_datatype_min_max_exclusive_restriction, \
                             owl_datatype_max_inclusive_restriction


class Owlapy_StructuralReasoner_Test(unittest.TestCase):
    # noinspection DuplicatedCode
    def test_instances(self):
        NS = "http://example.com/father#"
        onto = Ontology(IRI.create("file://KGs/Family/father.owl"))

        male = OWLClass(IRI.create(NS, 'male'))
        female = OWLClass(IRI.create(NS, 'female'))
        has_child = OWLObjectProperty(IRI(NS, 'hasChild'))

        reasoner = StructuralReasoner(onto)

        self.assertEqual([], list(reasoner.sub_object_properties(has_child, direct=True)))

        inst = frozenset(reasoner.instances(female))
        target_inst = frozenset({OWLNamedIndividual(IRI(NS, 'anna')),
                                 OWLNamedIndividual(IRI(NS, 'michelle'))})
        self.assertEqual(inst, target_inst)

        inst = frozenset(reasoner.instances(
            OWLObjectIntersectionOf((male, OWLObjectSomeValuesFrom(property=has_child, filler=female)))))
        target_inst = frozenset({OWLNamedIndividual(IRI(NS, 'markus'))})
        self.assertEqual(inst, target_inst)

        inst = frozenset(reasoner.instances(
            OWLObjectIntersectionOf((female, OWLObjectSomeValuesFrom(property=has_child, filler=OWLThing)))))
        target_inst = frozenset({OWLNamedIndividual(IRI(NS, 'anna'))})
        self.assertEqual(inst, target_inst)

        inst = frozenset(reasoner.instances(
            OWLObjectSomeValuesFrom(property=has_child,
                                    filler=OWLObjectSomeValuesFrom(property=has_child,
                                                                   filler=OWLObjectSomeValuesFrom(property=has_child,
                                                                                                  filler=OWLThing)))))
        target_inst = frozenset({OWLNamedIndividual(IRI(NS, 'stefan'))})
        self.assertEqual(inst, target_inst)

        inst = frozenset(reasoner.instances(OWLObjectHasValue(property=has_child,
                                                              individual=OWLNamedIndividual(IRI(NS, 'heinz')))))
        target_inst = frozenset({OWLNamedIndividual(IRI(NS, 'anna')),
                                 OWLNamedIndividual(IRI(NS, 'martin'))})
        self.assertEqual(inst, target_inst)

        inst = frozenset(reasoner.instances(OWLObjectOneOf((OWLNamedIndividual(IRI(NS, 'anna')),
                                                            OWLNamedIndividual(IRI(NS, 'michelle')),
                                                            OWLNamedIndividual(IRI(NS, 'markus'))))))
        target_inst = frozenset({OWLNamedIndividual(IRI(NS, 'anna')),
                                 OWLNamedIndividual(IRI(NS, 'michelle')),
                                 OWLNamedIndividual(IRI(NS, 'markus'))})
        self.assertEqual(inst, target_inst)

    def test_complement(self):
        NS = "http://example.com/father#"
        onto = Ontology(IRI.create("file://KGs/Family/father.owl"))

        male = OWLClass(IRI.create(NS, 'male'))
        female = OWLClass(IRI.create(NS, 'female'))
        has_child = OWLObjectProperty(IRI(NS, 'hasChild'))

        reasoner_nd = StructuralReasoner(onto, negation_default=True)
        reasoner_open = StructuralReasoner(onto, negation_default=False)

        self.assertEqual(set(reasoner_nd.instances(male)), set(reasoner_nd.instances(OWLObjectComplementOf(female))))
        self.assertEqual(set(reasoner_nd.instances(female)), set(reasoner_nd.instances(OWLObjectComplementOf(male))))

        self.assertEqual(set(), set(reasoner_open.instances(
            OWLObjectComplementOf(
                OWLObjectSomeValuesFrom(property=has_child, filler=OWLThing)))))

        all_inds = set(onto.individuals_in_signature())
        unknown_child = set(reasoner_nd.instances(
            OWLObjectComplementOf(
                OWLObjectSomeValuesFrom(property=has_child, filler=OWLThing))))
        with_child = set(reasoner_open.instances(
            OWLObjectSomeValuesFrom(property=has_child, filler=OWLThing)))
        self.assertEqual(all_inds - unknown_child, with_child)

    def test_all_values(self):
        NS = "http://example.com/father#"
        onto = Ontology(IRI.create("file://KGs/Family/father.owl"))

        has_child = OWLObjectProperty(IRI(NS, 'hasChild'))

        reasoner_nd = StructuralReasoner(onto, negation_default=True)

        # note, these answers are all wrong under OWA
        no_child = frozenset(reasoner_nd.instances(OWLObjectAllValuesFrom(property=has_child, filler=OWLNothing)))
        target_inst = frozenset({OWLNamedIndividual(IRI('http://example.com/father#', 'michelle')),
                                 OWLNamedIndividual(IRI('http://example.com/father#', 'heinz'))})
        self.assertEqual(no_child, target_inst)

    def test_complement2(self):
        NS = "http://example.com/father#"
        onto = Ontology(IRI.create("file://KGs/Family/father.owl"))

        male = OWLClass(IRI.create(NS, 'male'))
        female = OWLClass(IRI.create(NS, 'female'))

        reasoner_open = StructuralReasoner(onto, negation_default=False)

        # Should be empty under open world assumption
        self.assertEqual(set(), set(reasoner_open.instances(OWLObjectComplementOf(female))))
        self.assertEqual(set(), set(reasoner_open.instances(OWLObjectComplementOf(male))))

    def test_cardinality_restrictions(self):
        NS = "http://dl-learner.org/mutagenesis#"
        onto = Ontology(IRI.create("file://KGs/Mutagenesis/mutagenesis.owl"))

        hydrogen_3 = OWLClass(IRI.create(NS, 'Hydrogen-3'))
        atom = OWLClass(IRI.create(NS, 'Atom'))
        has_atom = OWLObjectProperty(IRI(NS, 'hasAtom'))

        reasoner = StructuralReasoner(onto, negation_default=True)

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

        all_inds = set(onto.individuals_in_signature())
        inst = frozenset(reasoner.instances(OWLObjectMaxCardinality(cardinality=39,
                                                                    property=has_atom,
                                                                    filler=atom)))
        self.assertEqual(all_inds - target_inst_min, inst)

    def test_data_properties(self):
        NS = "http://dl-learner.org/mutagenesis#"
        onto = Ontology(IRI.create("file://KGs/Mutagenesis/mutagenesis.owl"))

        act = OWLDataProperty(IRI(NS, 'act'))
        fused_rings = OWLDataProperty(IRI(NS, 'hasThreeOrMoreFusedRings'))
        lumo = OWLDataProperty(IRI(NS, 'lumo'))
        logp = OWLDataProperty(IRI(NS, 'logp'))
        charge = OWLDataProperty(IRI(NS, 'charge'))

        reasoner = StructuralReasoner(onto, negation_default=True)

        self.assertEqual([], list(reasoner.sub_data_properties(act, direct=True)))

        # OWLDataHasValue
        inst = frozenset(reasoner.instances(
            OWLObjectIntersectionOf((OWLDataHasValue(property=fused_rings, value=OWLLiteral(True)),
                                     OWLDataHasValue(property=act, value=OWLLiteral(2.11))))))
        target_inst = frozenset({OWLNamedIndividual(IRI(NS, 'd1'))})
        self.assertEqual(inst, target_inst)

        # OWLDatatypeRestriction
        restriction = owl_datatype_min_max_inclusive_restriction(-3.0, -2.8)
        inst = frozenset(reasoner.instances(OWLDataSomeValuesFrom(property=lumo, filler=restriction)))
        target_inst = frozenset({OWLNamedIndividual(IRI(NS, 'd149')),
                                 OWLNamedIndividual(IRI(NS, 'd29')),
                                 OWLNamedIndividual(IRI(NS, 'd49')),
                                 OWLNamedIndividual(IRI(NS, 'd96'))})
        self.assertEqual(inst, target_inst)

        # OWLDataAllValuesFrom
        inst2 = frozenset(reasoner.instances(
            OWLObjectComplementOf(OWLDataAllValuesFrom(property=lumo, filler=OWLDataComplementOf(restriction)))))
        self.assertEqual(inst, inst2)

        # OWLDataComplementOf
        restriction = owl_datatype_min_max_exclusive_restriction(-2.0, 0.88)
        inst = frozenset(reasoner.instances(OWLDataSomeValuesFrom(property=charge,
                                                                  filler=OWLDataComplementOf(restriction))))
        target_inst = frozenset({OWLNamedIndividual(IRI(NS, 'd195_12')),
                                 OWLNamedIndividual(IRI(NS, 'd33_27'))})
        self.assertEqual(inst, target_inst)

        # OWLDataOneOf, OWLDatatype, OWLDataIntersectionOf
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

    def test_data_properties_time(self):
        NS = "http://example.com/father#"
        onto = Ontology(IRI.create("file://KGs/Family/father.owl"))

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
        anna = OWLNamedIndividual(IRI(NS, 'anna'))
        heinz = OWLNamedIndividual(IRI(NS, 'heinz'))
        michelle = OWLNamedIndividual(IRI(NS, 'michelle'))
        martin = OWLNamedIndividual(IRI(NS, 'martin'))

        reasoner = StructuralReasoner(onto)

        restriction = owl_datatype_min_max_exclusive_restriction(date(year=1995, month=6, day=12),
                                                            date(year=1999, month=3, day=2))
        inst = frozenset(reasoner.instances(OWLDataSomeValuesFrom(property=birth_date,
                                                                  filler=restriction)))
        target_inst = frozenset({martin})
        self.assertEqual(inst, target_inst)

        inst = frozenset(reasoner.instances(OWLDataSomeValuesFrom(property=birth_date,
                                                                  filler=OWLDataComplementOf(restriction))))
        target_inst = frozenset({michelle, anna, heinz, markus})
        self.assertEqual(inst, target_inst)

        restriction = owl_datatype_max_inclusive_restriction(datetime(year=1990, month=10, day=2, hour=10,
                                                                  minute=20, second=5))
        inst = frozenset(reasoner.instances(OWLDataSomeValuesFrom(property=birth_date_time,
                                                                  filler=restriction)))
        target_inst = frozenset({markus, heinz})
        self.assertEqual(inst, target_inst)

    def test_sub_property_inclusion(self):
        ns = "http://dl-learner.org/mutagenesis#"
        onto = Ontology(IRI.create("file://KGs/Mutagenesis/mutagenesis.owl"))

        carbon_22 = OWLClass(IRI(ns, 'Carbon-22'))
        compound = OWLClass(IRI(ns, 'Compound'))
        benzene = OWLClass(IRI(ns, 'Benzene'))
        has_structure = OWLObjectProperty(IRI(ns, 'hasStructure'))
        super_has_structure = OWLObjectProperty(IRI(ns, 'superHasStucture'))
        charge = OWLDataProperty(IRI(ns, 'charge'))
        super_charge = OWLDataProperty(IRI.create(ns, 'super_charge'))
        onto.add_axiom(OWLSubObjectPropertyOfAxiom(has_structure, super_has_structure))
        onto.add_axiom(OWLSubDataPropertyOfAxiom(charge, super_charge))

        # sub_property = True
        reasoner = StructuralReasoner(onto, sub_properties=True)
        reasoner._ontology.is_modified = False  # This is done because, for sub_properties to work as expected it needs
                                                # _property_cache of the reasoner to be True which would normally be
                                                # False when the ontology is modified. Info: Cache needs to be reset and
                                                # disabled when ontolgy modification is detected because the
                                                # cached facts may not hold anymore. Hence, setting is_modified to False
                                                # is an excepton to check this test.

        # object property
        ce = OWLObjectIntersectionOf([compound, OWLObjectSomeValuesFrom(super_has_structure, benzene)])
        individuals = frozenset(reasoner.instances(ce))
        self.assertEqual(len(individuals), 222)

        # data property
        ce = OWLObjectIntersectionOf([carbon_22, OWLDataHasValue(super_charge, OWLLiteral(-0.128))])
        individuals = frozenset(reasoner.instances(ce))
        self.assertEqual(len(individuals), 75)

        # sub_property = False
        reasoner = StructuralReasoner(onto, sub_properties=False)

        # object property
        ce = OWLObjectIntersectionOf([compound, OWLObjectSomeValuesFrom(super_has_structure, benzene)])
        individuals = frozenset(reasoner.instances(ce))
        self.assertEqual(len(individuals), 0)

        # data property
        ce = OWLObjectIntersectionOf([carbon_22, OWLDataHasValue(super_charge, OWLLiteral(-0.128))])
        individuals = frozenset(reasoner.instances(ce))
        self.assertEqual(len(individuals), 0)

        onto.remove_axiom(OWLSubObjectPropertyOfAxiom(has_structure, super_has_structure))
        onto.remove_axiom(OWLSubDataPropertyOfAxiom(charge, super_charge))

    def test_inverse(self):
        ns = "http://example.com/father#"
        onto = Ontology(IRI.create("file://KGs/Family/father.owl"))

        has_child = OWLObjectProperty(IRI(ns, 'hasChild'))
        has_child_inverse = OWLObjectProperty(IRI.create(ns, 'hasChild_inverse'))
        onto.add_axiom(OWLInverseObjectPropertiesAxiom(has_child, has_child_inverse))

        parents = {OWLNamedIndividual(IRI.create(ns, 'anna')),
                   OWLNamedIndividual(IRI.create(ns, 'martin')),
                   OWLNamedIndividual(IRI.create(ns, 'stefan')),
                   OWLNamedIndividual(IRI.create(ns, 'markus'))}

        reasoner = StructuralReasoner(onto, sub_properties=False)

        expr = OWLObjectSomeValuesFrom(has_child, OWLThing)
        expr_inverse = OWLObjectSomeValuesFrom(OWLObjectInverseOf(has_child_inverse), OWLThing)
        parents_expr = frozenset(reasoner.instances(expr))
        parents_expr_inverse = frozenset(reasoner.instances(expr_inverse))
        self.assertEqual(parents_expr, parents)
        self.assertEqual(parents_expr_inverse, parents)
        # Removal not needed, just for completeness
        onto.remove_axiom(OWLInverseObjectPropertiesAxiom(has_child, has_child_inverse))

        # test sub properties
        super_has_child = OWLObjectProperty(IRI(ns, 'super_hasChild'))
        onto.add_axiom(OWLSubObjectPropertyOfAxiom(has_child, super_has_child))
        super_has_child_inverse = OWLObjectProperty(IRI(ns, 'super_hasChild_inverse'))
        onto.add_axiom(OWLInverseObjectPropertiesAxiom(super_has_child, super_has_child_inverse))

        # False (sub properties not taken into account)
        expr = OWLObjectSomeValuesFrom(super_has_child, OWLThing)
        expr_inverse = OWLObjectSomeValuesFrom(OWLObjectInverseOf(super_has_child_inverse), OWLThing)
        parents_expr = frozenset(reasoner.instances(expr))
        parents_expr_inverse = frozenset(reasoner.instances(expr_inverse))
        self.assertEqual(parents_expr, frozenset())
        self.assertEqual(parents_expr_inverse, frozenset())

        # True (sub properties taken into account)
        reasoner = StructuralReasoner(onto,  sub_properties=True)
        expr = OWLObjectSomeValuesFrom(super_has_child, OWLThing)
        expr_inverse = OWLObjectSomeValuesFrom(OWLObjectInverseOf(super_has_child_inverse), OWLThing)
        parents_expr = frozenset(reasoner.instances(expr))
        parents_expr_inverse = frozenset(reasoner.instances(expr_inverse))
        self.assertEqual(parents_expr, parents)
        self.assertEqual(parents_expr_inverse, parents)

        onto.remove_axiom(OWLSubObjectPropertyOfAxiom(has_child, super_has_child))
        onto.remove_axiom(OWLInverseObjectPropertiesAxiom(super_has_child, super_has_child_inverse))


if __name__ == '__main__':
    unittest.main()
