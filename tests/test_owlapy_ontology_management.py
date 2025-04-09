from datetime import date, datetime
import unittest

from pandas import Timedelta
from owlapy.owl_reasoner import StructuralReasoner, SyncReasoner
from owlapy.providers import owl_datatype_max_inclusive_restriction, owl_datatype_min_inclusive_restriction, \
                              owl_datatype_min_max_exclusive_restriction, owl_datatype_min_max_inclusive_restriction

import owlready2

from owlapy.class_expression import OWLObjectOneOf, OWLObjectSomeValuesFrom, OWLThing, OWLObjectComplementOf, \
    OWLObjectAllValuesFrom, OWLObjectHasValue, OWLClass, OWLDataAllValuesFrom, OWLDataHasValue, \
    OWLDataOneOf, OWLDataSomeValuesFrom, OWLObjectExactCardinality, OWLObjectMaxCardinality, OWLObjectMinCardinality, \
    OWLObjectIntersectionOf, OWLDataMaxCardinality, OWLDataMinCardinality, OWLObjectUnionOf, \
    OWLDataExactCardinality
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLSubDataPropertyOfAxiom, OWLInverseObjectPropertiesAxiom, OWLSubObjectPropertyOfAxiom, \
    OWLObjectPropertyRangeAxiom, OWLSameIndividualAxiom, OWLClassAssertionAxiom, OWLEquivalentClassesAxiom, \
    OWLDifferentIndividualsAxiom, OWLDisjointClassesAxiom, OWLDisjointDataPropertiesAxiom, \
    OWLDisjointObjectPropertiesAxiom, OWLEquivalentDataPropertiesAxiom, OWLEquivalentObjectPropertiesAxiom, \
    OWLDataPropertyDomainAxiom, OWLDataPropertyRangeAxiom, OWLSubClassOfAxiom, OWLObjectPropertyDomainAxiom, \
    OWLDataPropertyAssertionAxiom, OWLObjectPropertyAssertionAxiom
from owlapy.owl_data_ranges import OWLDataComplementOf, OWLDataIntersectionOf, OWLDataUnionOf
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import DoubleOWLDatatype, OWLLiteral, DurationOWLDatatype, IntegerOWLDatatype, \
    BooleanOWLDatatype, DateTimeOWLDatatype, DateOWLDatatype
from owlapy.owl_property import OWLObjectInverseOf, OWLObjectProperty, OWLDataProperty

from owlapy.owl_ontology import Ontology, ToOwlready2, FromOwlready2


class Owlapy_Owlready2_Test(unittest.TestCase):

    def test_equivalent_classes(self):
        ns = "http://dl-learner.org/mutagenesis#"
        onto = Ontology(IRI.create("file://KGs/Mutagenesis/mutagenesis.owl"))
        reasoner = StructuralReasoner(onto)

        atom = OWLClass(IRI(ns, 'Atom'))
        bond = OWLClass(IRI(ns, 'Bond'))
        ball3 = OWLClass(IRI(ns, 'Ball3'))
        benzene = OWLClass(IRI(ns, 'Benzene'))
        compound = OWLClass(IRI(ns, 'Compound'))
        has_atom = OWLObjectProperty(IRI(ns, 'hasAtom'))

        onto.add_axiom(OWLEquivalentClassesAxiom([OWLObjectUnionOf([atom, bond]), compound, atom, bond]))
        onto.add_axiom(OWLEquivalentClassesAxiom([bond, benzene]))
        onto.add_axiom(OWLEquivalentClassesAxiom([bond, OWLObjectSomeValuesFrom(has_atom, ball3)]))

        classes = frozenset({atom, compound, bond})
        target_classes = frozenset(reasoner.equivalent_classes(benzene, only_named=True))
        self.assertEqual(classes, target_classes)

        classes = frozenset({OWLObjectUnionOf([atom, bond]), atom, compound, bond,
                             OWLObjectSomeValuesFrom(has_atom, ball3)})
        target_classes = frozenset(reasoner.equivalent_classes(benzene, only_named=False))
        self.assertEqual(classes, target_classes)

        classes = frozenset({bond, atom, compound, benzene})
        target_classes = frozenset(reasoner.equivalent_classes(OWLObjectUnionOf([atom, bond]), only_named=True))
        self.assertEqual(classes, target_classes)

        classes = frozenset({atom, compound, bond, benzene, OWLObjectSomeValuesFrom(has_atom, ball3)})
        target_classes = frozenset(reasoner.equivalent_classes(OWLObjectUnionOf([atom, bond]), only_named=False))
        self.assertEqual(classes, target_classes)

        classes = frozenset({bond, atom, compound, benzene})
        target_classes = frozenset(reasoner.equivalent_classes(OWLObjectSomeValuesFrom(has_atom, ball3),
                                                               only_named=True))
        self.assertEqual(classes, target_classes)

        classes = frozenset({atom, compound, bond, benzene, OWLObjectUnionOf([atom, bond])})
        target_classes = frozenset(reasoner.equivalent_classes(OWLObjectSomeValuesFrom(has_atom, ball3),
                                                               only_named=False))
        self.assertEqual(classes, target_classes)

    def test_sub_classes(self):
        ns = "http://dl-learner.org/mutagenesis#"
        onto = Ontology(IRI.create("file://KGs/Mutagenesis/mutagenesis.owl"))
        reasoner = StructuralReasoner(onto)

        bond = OWLClass(IRI(ns, 'Bond'))
        ball3 = OWLClass(IRI(ns, 'Ball3'))
        benzene = OWLClass(IRI(ns, 'Benzene'))
        has_atom = OWLObjectProperty(IRI(ns, 'hasAtom'))

        onto.add_axiom(OWLSubClassOfAxiom(benzene, OWLObjectUnionOf([bond, bond])))
        onto.add_axiom(OWLSubClassOfAxiom(OWLObjectUnionOf([bond, bond]), ball3))
        onto.add_axiom(OWLSubClassOfAxiom(ball3, OWLObjectSomeValuesFrom(has_atom, ball3)))

        # Named class
        # Direct, only named
        classes = frozenset({})
        target_classes = frozenset(reasoner.sub_classes(ball3, direct=True, only_named=True))
        self.assertEqual(classes, target_classes)

        # non Direct, only named
        classes = frozenset({benzene})
        target_classes = frozenset(reasoner.sub_classes(ball3, direct=False, only_named=True))
        self.assertEqual(classes, target_classes)

        # Direct, not only named
        classes = frozenset({OWLObjectUnionOf([bond, bond])})
        target_classes = frozenset(reasoner.sub_classes(ball3, direct=True, only_named=False))
        self.assertEqual(classes, target_classes)

        # non Direct, not only named
        classes = frozenset({OWLObjectUnionOf([bond, bond]), benzene})
        target_classes = frozenset(reasoner.sub_classes(ball3, direct=False, only_named=False))
        self.assertEqual(classes, target_classes)

        # Complex class expression
        # Direct, only named
        classes = frozenset({ball3})
        target_classes = frozenset(reasoner.sub_classes(OWLObjectSomeValuesFrom(has_atom, ball3),
                                                        direct=True, only_named=True))
        self.assertEqual(classes, target_classes)

        # non Direct, only named
        classes = frozenset({ball3, benzene})
        target_classes = frozenset(reasoner.sub_classes(OWLObjectSomeValuesFrom(has_atom, ball3),
                                                        direct=False, only_named=True))
        self.assertEqual(classes, target_classes)

        # Direct, not only named
        classes = frozenset({ball3})
        target_classes = frozenset(reasoner.sub_classes(OWLObjectSomeValuesFrom(has_atom, ball3),
                                                        direct=True, only_named=False))
        self.assertEqual(classes, target_classes)

        # non Direct, not only named
        classes = frozenset({OWLObjectUnionOf([bond, bond]), benzene, ball3})
        target_classes = frozenset(reasoner.sub_classes(OWLObjectSomeValuesFrom(has_atom, ball3),
                                                        direct=False, only_named=False))
        self.assertEqual(classes, target_classes)

    def test_super_classes(self):
        ns = "http://dl-learner.org/mutagenesis#"
        onto = Ontology(IRI.create("file://KGs/Mutagenesis/mutagenesis.owl"))
        reasoner = StructuralReasoner(onto)

        bond = OWLClass(IRI(ns, 'Bond'))
        ball3 = OWLClass(IRI(ns, 'Ball3'))
        benzene = OWLClass(IRI(ns, 'Benzene'))
        ring_structure = OWLClass(IRI(ns, 'RingStructure'))
        has_atom = OWLObjectProperty(IRI(ns, 'hasAtom'))

        onto.add_axiom(OWLSubClassOfAxiom(OWLObjectSomeValuesFrom(has_atom, ball3), benzene))
        onto.add_axiom(OWLSubClassOfAxiom(benzene, OWLObjectUnionOf([bond, bond])))
        onto.add_axiom(OWLSubClassOfAxiom(OWLObjectUnionOf([bond, bond]), ball3))

        # Named class
        # Direct, only named
        classes = frozenset({ring_structure})
        target_classes = frozenset(reasoner.super_classes(benzene, direct=True, only_named=True))
        self.assertEqual(classes, target_classes)

        # non Direct, only named
        classes = frozenset({ring_structure, OWLThing, ball3})
        target_classes = frozenset(reasoner.super_classes(benzene, direct=False, only_named=True))
        self.assertEqual(classes, target_classes)

        # Direct, not only named
        classes = frozenset({OWLObjectUnionOf([bond, bond]), ring_structure})
        target_classes = frozenset(reasoner.super_classes(benzene, direct=True, only_named=False))
        self.assertEqual(classes, target_classes)

        # non Direct, not only named
        classes = frozenset({OWLObjectUnionOf([bond, bond]), ball3, ring_structure, OWLThing})
        target_classes = frozenset(reasoner.super_classes(benzene, direct=False, only_named=False))
        self.assertEqual(classes, target_classes)

        # Complex class expression
        # Direct, only named
        classes = frozenset({benzene})
        target_classes = frozenset(reasoner.super_classes(OWLObjectSomeValuesFrom(has_atom, ball3),
                                                          direct=True, only_named=True))
        self.assertEqual(classes, target_classes)

        # non Direct, only named
        classes = frozenset({ring_structure, OWLThing, benzene, ball3})
        target_classes = frozenset(reasoner.super_classes(OWLObjectSomeValuesFrom(has_atom, ball3),
                                                          direct=False, only_named=True))
        self.assertEqual(classes, target_classes)

        # Direct, not only named
        classes = frozenset({benzene})
        target_classes = frozenset(reasoner.super_classes(OWLObjectSomeValuesFrom(has_atom, ball3),
                                                          direct=True, only_named=False))
        self.assertEqual(classes, target_classes)

        # non Direct, not only named
        classes = frozenset({OWLObjectUnionOf([bond, bond]), ball3, ring_structure, OWLThing, benzene})
        target_classes = frozenset(reasoner.super_classes(OWLObjectSomeValuesFrom(has_atom, ball3),
                                                          direct=False, only_named=False))
        self.assertEqual(classes, target_classes)

    def test_sub_object_properties(self):
        ns = "http://www.biopax.org/examples/glycolysis#"
        onto = Ontology(IRI.create("file://KGs/Biopax/biopax.owl"))
        reasoner = StructuralReasoner(onto)

        participants = OWLObjectProperty(IRI.create(ns, 'PARTICIPANTS'))
        target_props = frozenset({OWLObjectProperty(IRI(ns, 'COFACTOR')),
                                  OWLObjectProperty(IRI(ns, 'CONTROLLED')),
                                  OWLObjectProperty(IRI(ns, 'CONTROLLER')),
                                  OWLObjectProperty(IRI(ns, 'LEFT')),
                                  OWLObjectProperty(IRI(ns, 'RIGHT'))})
        self.assertEqual(frozenset(reasoner.sub_object_properties(participants, direct=True)), target_props)
        self.assertEqual(frozenset(reasoner.sub_object_properties(participants, direct=False)), target_props)

    def test_instances(self):
        ns = "http://example.com/father#"
        onto = Ontology(IRI.create("file://KGs/Family/father.owl"))
        reasoner = StructuralReasoner(onto)

        inst = frozenset(reasoner.instances(OWLThing))
        target_inst = frozenset({OWLNamedIndividual(IRI(ns, 'anna')),
                                 OWLNamedIndividual(IRI(ns, 'heinz')),
                                 OWLNamedIndividual(IRI(ns, 'markus')),
                                 OWLNamedIndividual(IRI(ns, 'martin')),
                                 OWLNamedIndividual(IRI(ns, 'michelle')),
                                 OWLNamedIndividual(IRI(ns, 'stefan'))})
        self.assertEqual(inst, target_inst)

        inst = frozenset(reasoner.instances(OWLClass(IRI.create(ns, "male"))))
        target_inst = frozenset({OWLNamedIndividual(IRI(ns, 'heinz')), OWLNamedIndividual(IRI(ns, 'martin')),
                                 OWLNamedIndividual(IRI(ns, 'markus')), OWLNamedIndividual(IRI(ns, 'stefan'))})
        self.assertEqual(inst, target_inst)

    def test_types(self):
        ns = "http://example.com/father#"
        onto = Ontology(IRI.create("file://KGs/Family/father.owl"))
        reasoner = StructuralReasoner(onto)

        types = frozenset(reasoner.types(OWLNamedIndividual(IRI.create(ns, 'stefan'))))
        target_types = frozenset({OWLThing, OWLClass(IRI(ns, 'male')), OWLClass(IRI(ns, 'person'))})
        self.assertEqual(target_types, types)

    def test_object_values(self):
        ns = "http://example.com/father#"
        onto = Ontology(IRI.create("file://KGs/Family/father.owl"))
        reasoner = StructuralReasoner(onto)

        stefan = OWLNamedIndividual(IRI.create(ns, 'stefan'))
        markus = OWLNamedIndividual(IRI.create(ns, 'markus'))
        heinz = OWLNamedIndividual(IRI(ns, 'heinz'))
        has_child = OWLObjectProperty(IRI.create(ns, 'hasChild'))
        super_has_child = OWLObjectProperty(IRI.create(ns, 'super_hasChild'))
        onto.add_axiom(OWLSubObjectPropertyOfAxiom(has_child, super_has_child))

        kids = frozenset(reasoner.object_property_values(stefan, has_child))
        target_kids = frozenset({markus})
        self.assertEqual(target_kids, kids)

        no_kids = frozenset(reasoner.object_property_values(heinz, has_child))
        self.assertEqual(frozenset(), no_kids)

        # test sub property
        kids = frozenset(reasoner.object_property_values(stefan, super_has_child, direct=True))
        target_kids = frozenset()
        self.assertEqual(target_kids, kids)

        kids = frozenset(reasoner.object_property_values(stefan, super_has_child, direct=False))
        target_kids = frozenset({markus})
        self.assertEqual(target_kids, kids)

        # test inverse
        has_child_inverse = OWLObjectProperty(IRI.create(ns, 'hasChild_inverse'))
        onto.add_axiom(OWLInverseObjectPropertiesAxiom(has_child, has_child_inverse))
        parents = frozenset(reasoner.object_property_values(markus, OWLObjectInverseOf(has_child), direct=True))
        target_parents = frozenset({stefan})
        self.assertEqual(target_parents, parents)
        # Remove again for completeness, would not be necessary
        onto.remove_axiom(OWLInverseObjectPropertiesAxiom(has_child, has_child_inverse))

        # test inverse with sub property
        # Setup:
        # hasChild subPropertyOf super_hasChild
        # hasChild inverseOf hasChild_inverse
        # super_hasChild inverseOf super_hasChild_inverse
        super_has_child_inverse = OWLObjectProperty(IRI.create(ns, 'super_hasChild_inverse'))
        onto.add_axiom(OWLInverseObjectPropertiesAxiom(super_has_child, super_has_child_inverse))

        parents = frozenset(reasoner.object_property_values(stefan,
                                                            OWLObjectInverseOf(super_has_child_inverse),
                                                            direct=True))
        target_parents = frozenset()
        self.assertEqual(target_parents, parents)

        parents = frozenset(reasoner.object_property_values(stefan,
                                                            OWLObjectInverseOf(super_has_child_inverse),
                                                            direct=False))
        target_parents = frozenset({markus})
        self.assertEqual(target_parents, parents)
        onto.remove_axiom(OWLInverseObjectPropertiesAxiom(super_has_child, super_has_child_inverse))
        onto.remove_axiom(OWLSubObjectPropertyOfAxiom(has_child, super_has_child))

    def test_data_values(self):
        ns = "http://dl-learner.org/mutagenesis#"
        onto = Ontology(IRI.create("file://KGs/Mutagenesis/mutagenesis.owl"))
        reasoner = StructuralReasoner(onto)

        d100_1 = OWLNamedIndividual(IRI.create(ns, 'd100_1'))
        charge = OWLDataProperty(IRI.create(ns, 'charge'))
        super_charge = OWLDataProperty(IRI.create(ns, 'super_charge'))
        onto.add_axiom(OWLSubDataPropertyOfAxiom(charge, super_charge))

        values = frozenset(reasoner.data_property_values(d100_1, charge))
        targets = frozenset({OWLLiteral(-0.128)})
        self.assertEqual(targets, values)

        d100 = OWLNamedIndividual(IRI(ns, 'd100'))
        values = frozenset(reasoner.data_property_values(d100, charge))
        self.assertEqual(frozenset(), values)

        # super_charge sub property
        values = frozenset(reasoner.data_property_values(d100_1, super_charge, direct=False))
        targets = frozenset({OWLLiteral(-0.128)})
        self.assertEqual(targets, values)

        values = frozenset(reasoner.data_property_values(d100_1, super_charge, direct=True))
        targets = frozenset()
        self.assertEqual(targets, values)
        onto.remove_axiom(OWLSubDataPropertyOfAxiom(charge, super_charge))

    def test_all_data_values(self):
        ns = "http://dl-learner.org/mutagenesis#"
        onto = Ontology(IRI.create("file://KGs/Mutagenesis/mutagenesis.owl"))
        reasoner = StructuralReasoner(onto)

        charge = OWLDataProperty(IRI.create(ns, 'charge'))
        super_charge = OWLDataProperty(IRI.create(ns, 'super_charge'))
        onto.add_axiom(OWLSubDataPropertyOfAxiom(charge, super_charge))

        values = frozenset(reasoner.all_data_property_values(charge, direct=True))
        self.assertEqual(529, len(values))

        values = frozenset(reasoner.all_data_property_values(super_charge, direct=True))
        self.assertEqual(0, len(values))

        values = frozenset(reasoner.all_data_property_values(super_charge, direct=False))
        self.assertEqual(529, len(values))
        onto.remove_axiom(OWLSubDataPropertyOfAxiom(charge, super_charge))

    def test_ind_object_properties(self):
        ns = "http://example.com/father#"
        onto = Ontology(IRI.create("file://KGs/Family/father.owl"))
        reasoner = StructuralReasoner(onto)

        stefan = OWLNamedIndividual(IRI.create(ns, 'stefan'))
        has_child = OWLObjectProperty(IRI.create(ns, 'hasChild'))
        super_has_child = OWLObjectProperty(IRI.create(ns, 'super_hasChild'))
        onto.add_axiom(OWLSubObjectPropertyOfAxiom(has_child, super_has_child))

        properties = frozenset(reasoner.ind_object_properties(stefan, direct=True))
        target_properties = frozenset({has_child})
        self.assertEqual(target_properties, properties)

        properties = frozenset(reasoner.ind_object_properties(stefan, direct=False))
        target_properties = frozenset({has_child, super_has_child})
        self.assertEqual(target_properties, properties)
        onto.remove_axiom(OWLSubObjectPropertyOfAxiom(has_child, super_has_child))

    def test_ind_data_properties(self):
        ns = "http://dl-learner.org/mutagenesis#"
        onto = Ontology(IRI.create("file://KGs/Mutagenesis/mutagenesis.owl"))
        reasoner = StructuralReasoner(onto)

        d100_1 = OWLNamedIndividual(IRI.create(ns, 'd100_1'))
        charge = OWLDataProperty(IRI.create(ns, 'charge'))
        super_charge = OWLDataProperty(IRI.create(ns, 'super_charge'))
        onto.add_axiom(OWLSubDataPropertyOfAxiom(charge, super_charge))

        properties = frozenset(reasoner.ind_data_properties(d100_1, direct=True))
        target_properties = frozenset({charge})
        self.assertEqual(target_properties, properties)

        properties = frozenset(reasoner.ind_data_properties(d100_1, direct=False))
        target_properties = frozenset({charge, super_charge})
        self.assertEqual(target_properties, properties)
        onto.remove_axiom(OWLSubDataPropertyOfAxiom(charge, super_charge))

    def test_add_remove_axiom(self):
        ns = "http://example.com/father#"
        onto = Ontology(IRI.create("file://KGs/Family/father.owl"))
        reasoner = StructuralReasoner(onto)

        markus = OWLNamedIndividual(IRI.create(ns, 'markus'))
        michelle = OWLNamedIndividual(IRI.create(ns, 'michelle'))
        anna = OWLNamedIndividual(IRI.create(ns, 'anna'))
        marius = OWLNamedIndividual(IRI.create(ns, 'marius'))
        person1 = OWLNamedIndividual(IRI.create(ns, 'person1'))

        has_child = OWLObjectProperty(IRI.create(ns, 'hasChild'))
        has_sibling = OWLObjectProperty(IRI.create(ns, 'has_sibling'))
        age = OWLDataProperty(IRI.create(ns, 'age'))
        test1 = OWLDataProperty(IRI.create(ns, 'test1'))

        male = OWLClass(IRI(ns, 'male'))
        brother = OWLClass(IRI(ns, 'brother'))
        sister = OWLClass(IRI(ns, 'sister'))
        person = OWLClass(IRI(ns, 'person'))
        person_sibling = OWLClass(IRI(ns, 'PersonWithASibling'))
        animal = OWLClass(IRI(ns, 'animal'))
        aerial_animal = OWLClass(IRI(ns, 'aerialAnimal'))

        self.assertNotIn(sister, list(onto.classes_in_signature()))
        onto.add_axiom(OWLClassAssertionAxiom(anna, sister))
        self.assertIn(sister, list(onto.classes_in_signature()))
        self.assertIn(anna, list(reasoner.instances(sister)))
        self.assertIn(sister, list(reasoner.types(anna)))
        onto.remove_axiom(OWLClassAssertionAxiom(anna, sister))
        self.assertNotIn(anna, list(reasoner.instances(sister)))
        self.assertNotIn(sister, list(reasoner.types(anna)))

        self.assertNotIn(michelle, list(reasoner.instances(sister)))
        onto.add_axiom(OWLClassAssertionAxiom(michelle, sister))
        self.assertIn(michelle, list(reasoner.instances(sister)))
        self.assertIn(sister, list(reasoner.types(michelle)))
        onto.remove_axiom(OWLClassAssertionAxiom(michelle, sister))
        self.assertNotIn(michelle, list(reasoner.instances(sister)))
        self.assertNotIn(sister, list(reasoner.types(michelle)))

        self.assertFalse(list(reasoner.object_property_values(michelle, has_child)))
        onto.add_axiom(OWLObjectPropertyAssertionAxiom(michelle, has_child, anna))
        self.assertIn(anna, list(reasoner.object_property_values(michelle, has_child)))
        onto.remove_axiom(OWLObjectPropertyAssertionAxiom(michelle, has_child, anna))
        self.assertNotIn(anna, list(reasoner.object_property_values(michelle, has_child)))
        onto.remove_axiom(OWLObjectPropertyAssertionAxiom(michelle, has_child, anna))

        self.assertNotIn(has_sibling, list(onto.object_properties_in_signature()))
        self.assertNotIn(marius, list(onto.individuals_in_signature()))
        onto.add_axiom(OWLObjectPropertyAssertionAxiom(marius, has_sibling, michelle))
        self.assertIn(has_sibling, list(onto.object_properties_in_signature()))
        self.assertIn(marius, list(onto.individuals_in_signature()))
        self.assertIn(michelle, list(reasoner.object_property_values(marius, has_sibling)))
        onto.remove_axiom(OWLObjectPropertyAssertionAxiom(marius, has_sibling, michelle))
        self.assertNotIn(michelle, list(reasoner.object_property_values(marius, has_sibling)))

        self.assertNotIn(age, list(onto.data_properties_in_signature()))
        onto.add_axiom(OWLDataPropertyAssertionAxiom(markus, age, OWLLiteral(30)))
        self.assertIn(age, list(onto.data_properties_in_signature()))
        self.assertIn(OWLLiteral(30), list(reasoner.data_property_values(markus, age)))
        onto.remove_axiom(OWLDataPropertyAssertionAxiom(markus, age, OWLLiteral(30)))
        self.assertNotIn(OWLLiteral(30), list(reasoner.data_property_values(markus, age)))

        self.assertNotIn(OWLLiteral(31), list(reasoner.data_property_values(anna, age)))
        onto.add_axiom(OWLDataPropertyAssertionAxiom(anna, age, OWLLiteral(31)))
        self.assertIn(OWLLiteral(31), list(reasoner.data_property_values(anna, age)))
        onto.remove_axiom(OWLDataPropertyAssertionAxiom(anna, age, OWLLiteral(31)))
        self.assertNotIn(OWLLiteral(31), list(reasoner.data_property_values(anna, age)))

        self.assertNotIn(brother, list(onto.classes_in_signature()))
        self.assertNotIn(animal, list(onto.classes_in_signature()))
        self.assertNotIn(aerial_animal, list(onto.classes_in_signature()))
        onto.add_axiom(OWLSubClassOfAxiom(brother, male))
        onto.add_axiom(OWLSubClassOfAxiom(aerial_animal, animal))
        self.assertIn(brother, list(reasoner.sub_classes(male)))
        self.assertIn(aerial_animal, list(reasoner.sub_classes(animal)))
        self.assertIn(male, list(reasoner.super_classes(brother)))
        self.assertIn(animal, list(reasoner.super_classes(aerial_animal)))
        onto.remove_axiom(OWLSubClassOfAxiom(brother, male))
        self.assertNotIn(brother, list(reasoner.sub_classes(male)))
        self.assertNotIn(male, list(reasoner.super_classes(brother)))

        self.assertNotIn(has_sibling, list(reasoner.sub_object_properties(has_child)))
        onto.add_axiom(OWLSubObjectPropertyOfAxiom(has_sibling, has_child))
        self.assertIn(has_sibling, list(reasoner.sub_object_properties(has_child)))
        onto.remove_axiom(OWLSubObjectPropertyOfAxiom(has_sibling, has_child))
        self.assertNotIn(has_sibling, list(reasoner.sub_object_properties(has_child)))

        self.assertNotIn(OWLObjectUnionOf([person, person_sibling]),
                         list(reasoner.object_property_domains(has_sibling)))
        onto.add_axiom(OWLObjectPropertyDomainAxiom(has_sibling, OWLObjectUnionOf([person, person_sibling])))
        self.assertIn(OWLObjectUnionOf([person, person_sibling]),
                      list(reasoner.object_property_domains(has_sibling, direct=True)))
        onto.remove_axiom(OWLObjectPropertyDomainAxiom(has_sibling, OWLObjectUnionOf([person, person_sibling])))
        self.assertNotIn(OWLObjectUnionOf([person, person_sibling]),
                         list(reasoner.object_property_domains(has_sibling, direct=True)))

        self.assertNotIn(sister, list(reasoner.object_property_ranges(has_sibling, direct=True)))
        onto.add_axiom(OWLObjectPropertyRangeAxiom(has_sibling, sister))
        self.assertIn(sister, list(reasoner.object_property_ranges(has_sibling)))
        onto.remove_axiom(OWLObjectPropertyRangeAxiom(has_sibling, sister))
        self.assertNotIn(sister, list(reasoner.object_property_ranges(has_sibling, direct=True)))

        self.assertNotIn(person, list(reasoner.data_property_domains(age, True)))
        onto.add_axiom(OWLDataPropertyDomainAxiom(age, person))
        self.assertIn(person, list(reasoner.data_property_domains(age, True)))
        onto.remove_axiom(OWLDataPropertyDomainAxiom(age, person))
        self.assertNotIn(person, list(reasoner.data_property_domains(age, True)))

        self.assertFalse(list(reasoner.data_property_ranges(age)))
        onto.add_axiom(OWLDataPropertyRangeAxiom(age, OWLDataUnionOf([IntegerOWLDatatype, DateOWLDatatype])))
        self.assertIn(OWLDataUnionOf([IntegerOWLDatatype, DateOWLDatatype]), list(reasoner.data_property_ranges(age)))
        onto.remove_axiom(OWLDataPropertyRangeAxiom(age, OWLDataUnionOf([IntegerOWLDatatype, DateOWLDatatype])))
        self.assertNotIn(OWLDataUnionOf([IntegerOWLDatatype, DateOWLDatatype]),
                         list(reasoner.data_property_ranges(age)))

        self.assertFalse(list(reasoner.equivalent_classes(brother)))
        onto.add_axiom(OWLEquivalentClassesAxiom([brother, male]))
        self.assertIn(male, list(reasoner.equivalent_classes(brother)))
        onto.remove_axiom(OWLEquivalentClassesAxiom([brother, male]))
        self.assertNotIn(male, list(reasoner.equivalent_classes(brother)))

        self.assertFalse(list(reasoner.equivalent_object_properties(has_child)))
        onto.add_axiom(OWLEquivalentObjectPropertiesAxiom([has_child, has_sibling]))
        self.assertIn(has_sibling, list(reasoner.equivalent_object_properties(has_child)))
        onto.remove_axiom(OWLEquivalentObjectPropertiesAxiom([has_child, has_sibling]))
        self.assertNotIn(has_sibling, list(reasoner.equivalent_object_properties(has_child)))

        self.assertFalse(list(reasoner.equivalent_data_properties(age)))
        onto.add_axiom(OWLEquivalentDataPropertiesAxiom([age, test1]))
        self.assertIn(test1, list(reasoner.equivalent_data_properties(age)))
        onto.remove_axiom(OWLEquivalentDataPropertiesAxiom([age, test1]))
        self.assertNotIn(test1, list(reasoner.equivalent_data_properties(age)))

        self.assertFalse(list(reasoner.same_individuals(markus)))
        onto.add_axiom(OWLSameIndividualAxiom([markus, anna, person1]))
        self.assertEqual({anna, person1}, set(reasoner.same_individuals(markus)))
        onto.remove_axiom(OWLSameIndividualAxiom([markus, anna, person1]))
        self.assertFalse(set(reasoner.same_individuals(markus)))

        self.assertFalse(list(reasoner.disjoint_classes(brother)))
        self.assertFalse(list(reasoner.disjoint_classes(person)))
        onto.add_axiom(OWLDisjointClassesAxiom([brother, sister, aerial_animal]))
        self.assertEqual({sister, aerial_animal}, set(reasoner.disjoint_classes(brother)))
        onto.remove_axiom(OWLDisjointClassesAxiom([brother, sister, aerial_animal]))
        self.assertFalse(set(reasoner.disjoint_classes(brother)))
        onto.add_axiom(OWLDisjointClassesAxiom([person, animal]))
        self.assertEqual({animal, aerial_animal}, set(reasoner.disjoint_classes(person)))
        onto.remove_axiom(OWLDisjointClassesAxiom([person, animal]))
        self.assertFalse(set(reasoner.disjoint_classes(person)))

        self.assertFalse(list(reasoner.disjoint_object_properties(has_sibling)))
        self.assertFalse(list(reasoner.disjoint_object_properties(has_child)))
        onto.add_axiom(OWLDisjointObjectPropertiesAxiom([has_child, has_sibling]))
        self.assertIn(has_sibling, set(reasoner.disjoint_object_properties(has_child)))
        self.assertIn(has_child, set(reasoner.disjoint_object_properties(has_sibling)))
        onto.remove_axiom(OWLDisjointObjectPropertiesAxiom([has_child, has_sibling]))
        self.assertNotIn(has_sibling, set(reasoner.disjoint_object_properties(has_child)))
        self.assertNotIn(has_child, set(reasoner.disjoint_object_properties(has_sibling)))

        self.assertFalse(list(reasoner.disjoint_data_properties(age)))
        self.assertFalse(list(reasoner.disjoint_data_properties(test1)))
        onto.add_axiom(OWLDisjointDataPropertiesAxiom([age, test1]))
        self.assertIn(test1, set(reasoner.disjoint_data_properties(age)))
        self.assertIn(age, set(reasoner.disjoint_data_properties(test1)))
        onto.remove_axiom(OWLDisjointDataPropertiesAxiom([age, test1]))
        self.assertNotIn(test1, set(reasoner.disjoint_data_properties(age)))
        self.assertNotIn(age, set(reasoner.disjoint_data_properties(test1)))

        self.assertFalse(list(reasoner.different_individuals(markus)))
        self.assertFalse(list(reasoner.different_individuals(michelle)))
        onto.add_axiom(OWLDifferentIndividualsAxiom([markus, michelle]))
        onto.add_axiom(OWLDifferentIndividualsAxiom([markus, anna, marius]))
        self.assertEqual({michelle, anna, marius}, set(reasoner.different_individuals(markus)))
        self.assertEqual({markus}, set(reasoner.different_individuals(michelle)))
        onto.remove_axiom(OWLDifferentIndividualsAxiom([markus, michelle]))
        onto.remove_axiom(OWLDifferentIndividualsAxiom([markus, anna, marius]))
        self.assertFalse(set(reasoner.different_individuals(markus)))
        self.assertFalse(set(reasoner.different_individuals(michelle)))

    def test_mapping(self):
        ns = "http://example.com/father#"
        onto = Ontology(IRI.create("file://KGs/Family/father.owl"))

        male = OWLClass(IRI.create(ns, 'male'))
        female = OWLClass(IRI.create(ns, 'female'))
        has_child = OWLObjectProperty(IRI(ns, 'hasChild'))

        to_owlready = ToOwlready2(world=onto._world)

        ce = male
        owlready_ce = onto._onto.male
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        ce = OWLObjectUnionOf((male, female))
        owlready_ce = onto._onto.male | onto._onto.female
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        ce = OWLObjectIntersectionOf((male, female))
        owlready_ce = onto._onto.male & onto._onto.female
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        ce = OWLObjectSomeValuesFrom(has_child, OWLThing)
        owlready_ce = onto._onto.hasChild.some(owlready2.owl.Thing)
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        ce = OWLObjectAllValuesFrom(has_child, male)
        owlready_ce = onto._onto.hasChild.only(onto._onto.male)
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        ce = male.get_object_complement_of()
        owlready_ce = owlready2.Not(onto._onto.male)
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        ce = OWLObjectOneOf([OWLNamedIndividual(IRI.create(ns, 'martin')),
                             OWLNamedIndividual(IRI.create(ns, 'michelle'))])
        owlready_ce = owlready2.OneOf([onto._onto.martin, onto._onto.michelle])
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        ce = OWLObjectMinCardinality(2, has_child, male)
        owlready_ce = onto._onto.hasChild.min(2, onto._onto.male)
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        ce = OWLObjectMaxCardinality(5, has_child, female)
        owlready_ce = onto._onto.hasChild.max(5, onto._onto.female)
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        ce = OWLObjectExactCardinality(3, has_child, OWLThing)
        owlready_ce = onto._onto.hasChild.exactly(3, owlready2.owl.Thing)
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        ce = OWLObjectHasValue(has_child, OWLNamedIndividual(IRI.create(ns, 'markus')))
        owlready_ce = onto._onto.hasChild.value(onto._onto.markus)
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

    def test_mapping_data_properties(self):
        ns = "http://dl-learner.org/mutagenesis#"
        onto = Ontology(IRI.create("file://KGs/Mutagenesis/mutagenesis.owl"))

        act = OWLDataProperty(IRI(ns, 'act'))
        charge = OWLDataProperty(IRI(ns, 'charge'))

        to_owlready = ToOwlready2(world=onto._world)

        # owlready2 defines no equal or hash method for ConstrainedDatatype, just using the __dict__ attribute
        # should be sufficient for the purpose of these tests
        def constraint_datatype_eq(self, other):
            return isinstance(other, owlready2.ConstrainedDatatype) and self.__dict__ == other.__dict__
        setattr(owlready2.ConstrainedDatatype, '__eq__', constraint_datatype_eq)
        setattr(owlready2.ConstrainedDatatype, '__hash__', lambda self: hash(frozenset(self.__dict__.items())))

        ce = OWLDataSomeValuesFrom(act, DateOWLDatatype)
        owlready_ce = onto._onto.act.some(date)
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        res = owl_datatype_min_inclusive_restriction(20)
        ce = OWLDataAllValuesFrom(charge, OWLDataComplementOf(res))
        owlready_ce = onto._onto.charge.only(owlready2.Not(owlready2.ConstrainedDatatype(int, min_inclusive=20)))
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        res_both = owl_datatype_min_max_exclusive_restriction(0.5, 1)
        ce = OWLDataAllValuesFrom(charge, OWLDataUnionOf([res, res_both]))
        owlready_ce = onto._onto.charge.only(
            owlready2.Or([owlready2.ConstrainedDatatype(int, min_inclusive=20),
                          owlready2.ConstrainedDatatype(float, min_exclusive=0.5, max_exclusive=1.0)]))
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        res = owl_datatype_max_inclusive_restriction(1.2)
        oneof = OWLDataOneOf([OWLLiteral(2.3), OWLLiteral(5.9), OWLLiteral(7.2)])
        ce = OWLDataAllValuesFrom(charge, OWLDataIntersectionOf([res, oneof]))
        owlready_ce = onto._onto.charge.only(owlready2.ConstrainedDatatype(float, max_inclusive=1.2) &
                                             owlready2.OneOf([2.3, 5.9, 7.2]))
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        ce = OWLDataSomeValuesFrom(charge, OWLDataIntersectionOf([res, BooleanOWLDatatype]))
        owlready_ce = onto._onto.charge.some(
            owlready2.And([owlready2.ConstrainedDatatype(float, max_inclusive=1.2), bool]))
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        ce = OWLDataMinCardinality(2, act, res)
        owlready_ce = onto._onto.act.min(2, owlready2.ConstrainedDatatype(float, max_inclusive=1.2))
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        ce = OWLDataMaxCardinality(4, charge, DurationOWLDatatype)
        owlready_ce = onto._onto.charge.max(4, Timedelta)
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

        ce = OWLDataExactCardinality(3, charge, OWLDataComplementOf(IntegerOWLDatatype))
        owlready_ce = onto._onto.charge.exactly(3, owlready2.Not(int))
        self.assertEqual(owlready_ce, to_owlready.map_concept(ce))

    def test_mapping_rev(self):
        ns = "http://example.com/father#"
        onto = Ontology(IRI.create("file://KGs/Family/father.owl"))

        male = onto._onto.male
        female = onto._onto.female
        has_child = onto._onto.hasChild

        from_owlready = FromOwlready2()

        ce = male | female
        owl_ce = OWLObjectUnionOf((OWLClass(IRI.create(ns, 'male')), OWLClass(IRI.create(ns, 'female'))))
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = male & female
        owl_ce = OWLObjectIntersectionOf((OWLClass(IRI.create(ns, 'male')), OWLClass(IRI.create(ns, 'female'))))
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = has_child.some(owlready2.owl.Thing)
        owl_ce = OWLObjectSomeValuesFrom(OWLObjectProperty(IRI(ns, 'hasChild')), OWLThing)
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = has_child.only(male)
        owl_ce = OWLObjectAllValuesFrom(OWLObjectProperty(IRI(ns, 'hasChild')), OWLClass(IRI.create(ns, 'male')))
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = owlready2.Not(male)
        owl_ce = OWLObjectComplementOf(OWLClass(IRI(ns, 'male')))
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = owlready2.OneOf([onto._onto.markus, onto._onto.anna])
        owl_ce = OWLObjectOneOf([OWLNamedIndividual(IRI.create(ns, 'markus')),
                                 OWLNamedIndividual(IRI.create(ns, 'anna'))])
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = onto._onto.hasChild.min(2, onto._onto.male)
        owl_ce = OWLObjectMinCardinality(2, OWLObjectProperty(IRI(ns, 'hasChild')), OWLClass(IRI(ns, 'male')))
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = onto._onto.hasChild.max(5, onto._onto.female)
        owl_ce = OWLObjectMaxCardinality(5, OWLObjectProperty(IRI(ns, 'hasChild')), OWLClass(IRI(ns, 'female')))
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = onto._onto.hasChild.exactly(3, owlready2.owl.Thing)
        owl_ce = OWLObjectExactCardinality(3, OWLObjectProperty(IRI(ns, 'hasChild')), OWLThing)
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = has_child.value(onto._onto.markus)
        owl_ce = OWLObjectHasValue(OWLObjectProperty(IRI(ns, 'hasChild')), OWLNamedIndividual(IRI.create(ns, 'markus')))
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

    def test_mapping_rev_data_properties(self):
        ns = "http://dl-learner.org/mutagenesis#"
        onto = Ontology(IRI.create("file://KGs/Mutagenesis/mutagenesis.owl"))

        act = onto._onto.act
        charge = onto._onto.charge

        from_owlready = FromOwlready2()

        ce = act.some(float)
        owl_ce = OWLDataSomeValuesFrom(OWLDataProperty(IRI(ns, 'act')), DoubleOWLDatatype)
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = charge.only(owlready2.Not(owlready2.ConstrainedDatatype(int, max_inclusive=2)))
        res = owl_datatype_max_inclusive_restriction(2)
        owl_ce = OWLDataAllValuesFrom(OWLDataProperty(IRI(ns, 'charge')), OWLDataComplementOf(res))
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = charge.some(owlready2.Not(owlready2.ConstrainedDatatype(int, max_inclusive=2)) |
                         owlready2.ConstrainedDatatype(float, min_inclusive=2.1, max_inclusive=2.2))
        res = owl_datatype_max_inclusive_restriction(2)
        res2 = owl_datatype_min_max_inclusive_restriction(2.1, 2.2)
        owl_ce = OWLDataSomeValuesFrom(OWLDataProperty(IRI(ns, 'charge')),
                                       OWLDataUnionOf([OWLDataComplementOf(res), res2]))
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = act.only(owlready2.Not(owlready2.ConstrainedDatatype(int, max_inclusive=2)) & datetime)
        owl_ce = OWLDataAllValuesFrom(OWLDataProperty(IRI(ns, 'act')),
                                      OWLDataIntersectionOf([OWLDataComplementOf(res), DateTimeOWLDatatype]))
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = act.some(owlready2.Not(owlready2.OneOf([1, 2, 3])) & Timedelta)
        values = OWLDataOneOf([OWLLiteral(1), OWLLiteral(2), OWLLiteral(3)])
        owl_ce = OWLDataSomeValuesFrom(OWLDataProperty(IRI(ns, 'act')),
                                       OWLDataIntersectionOf([OWLDataComplementOf(values), DurationOWLDatatype]))
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = onto._onto.act.value(19.5)
        owl_ce = OWLDataHasValue(OWLDataProperty(IRI(ns, 'act')), OWLLiteral(19.5))
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = onto._onto.act.min(2, owlready2.ConstrainedDatatype(int, max_inclusive=2))
        owl_ce = OWLDataMinCardinality(2, OWLDataProperty(IRI(ns, 'act')), res)
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = onto._onto.charge.max(5, date)
        owl_ce = OWLDataMaxCardinality(5, OWLDataProperty(IRI(ns, 'charge')), DateOWLDatatype)
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))

        ce = onto._onto.charge.exactly(3, owlready2.Not(float))
        owl_ce = OWLDataExactCardinality(3, OWLDataProperty(IRI(ns, 'charge')), OWLDataComplementOf(DoubleOWLDatatype))
        self.assertEqual(owl_ce, from_owlready.map_concept(ce))


class Owlapy_Owlready2_SyncReasoner(unittest.TestCase):
    # noinspection DuplicatedCode
    def test_instances(self):
        ns = "http://example.com/father#"

        male = OWLClass(IRI.create(ns, 'male'))
        female = OWLClass(IRI.create(ns, 'female'))
        has_child = OWLObjectProperty(IRI(ns, 'hasChild'))

        reasoner = SyncReasoner("KGs/Family/father.owl")

        inst = frozenset(reasoner.instances(female))
        target_inst = frozenset({OWLNamedIndividual(IRI(ns, 'anna')),
                                 OWLNamedIndividual(IRI(ns, 'michelle'))})
        self.assertEqual(inst, target_inst)

        inst = frozenset(reasoner.instances(
            OWLObjectIntersectionOf((male, OWLObjectSomeValuesFrom(property=has_child, filler=female)))))
        target_inst = frozenset({OWLNamedIndividual(IRI(ns, 'markus'))})
        self.assertEqual(inst, target_inst)

        inst = frozenset(reasoner.instances(
            OWLObjectIntersectionOf((female, OWLObjectSomeValuesFrom(property=has_child, filler=OWLThing)))))
        target_inst = frozenset({OWLNamedIndividual(IRI(ns, 'anna'))})
        self.assertEqual(inst, target_inst)


if __name__ == '__main__':
    unittest.main()
