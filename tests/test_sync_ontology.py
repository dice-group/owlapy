import unittest

from owlapy.class_expression import OWLClass, OWLObjectIntersectionOf, OWLObjectSomeValuesFrom, OWLObjectComplementOf
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLEquivalentClassesAxiom, OWLClassAssertionAxiom, OWLObjectPropertyAssertionAxiom, \
    OWLSubClassOfAxiom, OWLObjectPropertyRangeAxiom, OWLObjectPropertyDomainAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import OWLOntologyID, SyncOntology
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty

NS = "http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#"

# ==== Individuals ====
a = OWLNamedIndividual(IRI(NS, "a"))
b = OWLNamedIndividual(IRI(NS, "b"))
c = OWLNamedIndividual(IRI(NS, "c"))
d = OWLNamedIndividual(IRI(NS, "d"))
e = OWLNamedIndividual(IRI(NS, "e"))
f = OWLNamedIndividual(IRI(NS, "f"))
g = OWLNamedIndividual(IRI(NS, "g"))
h = OWLNamedIndividual(IRI(NS, "h"))
m = OWLNamedIndividual(IRI(NS, "m"))
l = OWLNamedIndividual(IRI(NS, "l"))  # noqa: E741
n = OWLNamedIndividual(IRI(NS, "n"))
o = OWLNamedIndividual(IRI(NS, "o"))
p = OWLNamedIndividual(IRI(NS, "p"))
q = OWLNamedIndividual(IRI(NS, "q"))
r = OWLNamedIndividual(IRI(NS, "r"))
s = OWLNamedIndividual(IRI(NS, "s"))
ind1 = OWLNamedIndividual(IRI(NS, "ind1"))

# ==== Object Properties ====
r1 = OWLObjectProperty(IRI(NS, "r1"))
r2 = OWLObjectProperty(IRI(NS, "r2"))
r3 = OWLObjectProperty(IRI(NS, "r3"))
r4 = OWLObjectProperty(IRI(NS, "r4"))
r5 = OWLObjectProperty(IRI(NS, "r5"))
r6 = OWLObjectProperty(IRI(NS, "r6"))
r7 = OWLObjectProperty(IRI(NS, "r7"))

# ==== Data Properties ====

dp1 = OWLDataProperty(IRI(NS, "dp1"))
dp2 = OWLDataProperty(IRI(NS, "dp2"))
dp3 = OWLDataProperty(IRI(NS, "dp3"))

# ==== Classes ====

A = OWLClass(IRI(NS, 'A'))
B = OWLClass(IRI(NS, 'B'))
C = OWLClass(IRI(NS, 'C'))
AB = OWLClass(IRI(NS, 'AB'))
D = OWLClass(IRI(NS, 'D'))
E = OWLClass(IRI(NS, 'E'))
F = OWLClass(IRI(NS, 'F'))
G = OWLClass(IRI(NS, 'G'))
J = OWLClass(IRI(NS, 'J'))
K = OWLClass(IRI(NS, 'K'))
H = OWLClass(IRI(NS, 'H'))
I = OWLClass(IRI(NS, 'I'))  # noqa: E741
L = OWLClass(IRI(NS, 'L'))
M = OWLClass(IRI(NS, 'M'))
N = OWLClass(IRI(NS, 'N'))
O = OWLClass(IRI(NS, 'O'))  # noqa: E741
P = OWLClass(IRI(NS, 'P'))
Q = OWLClass(IRI(NS, 'Q'))
R = OWLClass(IRI(NS, 'R'))
S = OWLClass(IRI(NS, 'S'))
T = OWLClass(IRI(NS, 'T'))
U = OWLClass(IRI(NS, 'U'))

father_onto_path = "KGs/Family/father.owl"
father_onto = SyncOntology(father_onto_path)


class TestSyncOntology(unittest.TestCase):

    ontology_path = "KGs/Test/test_ontology.owl"
    onto = SyncOntology(ontology_path)

    def test_interface_father_dataset(self):
        ontology_path = "KGs/Family/father.owl"
        onto = SyncOntology(ontology_path)
        assert {owl_class.remainder for owl_class in onto.classes_in_signature()}=={'male', 'female', 'Thing', 'person'}
        assert {individual.remainder for individual in onto.individuals_in_signature()} == {'markus', 'anna', 'martin',
                                                                                           'stefan', 'heinz',
                                                                                           'michelle'}
        assert {object_property.remainder for object_property in onto.object_properties_in_signature()} == {'hasChild'}

    # NOTE AB: The name of "assertCountEqual" may be misleading,but it's essentially an order-insensitive "assertEqual".

    def test_classes_in_signature(self):
        self.assertCountEqual(list(self.onto.classes_in_signature()), [A, AB, B, C, D, E, F, G, H, I, J, K, L, M, N, O,
                                                                       P, Q, R, S, T, U])

    def test_data_properties_in_signature(self):
        self.assertCountEqual(list(self.onto.data_properties_in_signature()), [dp1, dp2, dp3])

    def test_object_properties_in_signature(self):
        self.assertCountEqual(list(self.onto.object_properties_in_signature()), [r1, r2, r3, r4, r5, r6, r7])

    def test_individuals_in_signature(self):
        self.assertCountEqual(list(self.onto.individuals_in_signature()), [a, b, c, d, e, f, g, h, m, l, n, o, p, q, r,
                                                                           s, ind1])

    def test_equivalent_classes_axiom(self):
        eq1 = OWLEquivalentClassesAxiom([Q, N])
        eq2 = OWLEquivalentClassesAxiom([OWLObjectSomeValuesFrom(property=r2, filler=G), F])
        eq3 = OWLEquivalentClassesAxiom([OWLObjectIntersectionOf((B, A)), AB])
        aeq = set()
        for cls in self.onto.classes_in_signature():
            ea = set(self.onto.equivalent_classes_axioms(cls))
            aeq.update(ea)
        self.assertCountEqual(aeq, {eq1, eq2, eq3})

    def test_get_ontology_id(self):
        onto_id = OWLOntologyID(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/', 'untitled-ontology-11'),
                                None)
        self.assertEqual(self.onto.get_ontology_id(), onto_id)

    def test__eq__(self):
        onto2 = SyncOntology(self.ontology_path)
        self.assertTrue(self.onto.__eq__(onto2))

    def test_get_signature(self):
        self.assertCountEqual(father_onto.get_signature(),
                              [OWLClass(IRI('http://example.com/father#', 'female')),
                               OWLClass(IRI('http://example.com/father#', 'male')),
                               OWLClass(IRI('http://example.com/father#', 'person')),
                               OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),
                               OWLObjectProperty(IRI('http://example.com/father#', 'hasChild')),
                               OWLNamedIndividual(IRI('http://example.com/father#', 'anna')),
                               OWLNamedIndividual(IRI('http://example.com/father#', 'heinz')),
                               OWLNamedIndividual(IRI('http://example.com/father#', 'markus')),
                               OWLNamedIndividual(IRI('http://example.com/father#', 'martin')),
                               OWLNamedIndividual(IRI('http://example.com/father#', 'michelle')),
                               OWLNamedIndividual(IRI('http://example.com/father#', 'stefan'))])

    def test_get_abox(self):
        self.assertCountEqual(father_onto.get_abox_axioms(),
                              [OWLClassAssertionAxiom(
                                  individual=OWLNamedIndividual(IRI('http://example.com/father#', 'martin')),
                                  class_expression=OWLClass(IRI('http://example.com/father#', 'male')), annotations=[]),
                               OWLClassAssertionAxiom(
                                   individual=OWLNamedIndividual(IRI('http://example.com/father#', 'markus')),
                                   class_expression=OWLClass(IRI('http://example.com/father#', 'male')),
                                   annotations=[]),
                               OWLClassAssertionAxiom(
                                   individual=OWLNamedIndividual(IRI('http://example.com/father#', 'michelle')),
                                   class_expression=OWLClass(IRI('http://example.com/father#', 'female')),
                                   annotations=[]),
                               OWLClassAssertionAxiom(
                                   individual=OWLNamedIndividual(IRI('http://example.com/father#', 'heinz')),
                                   class_expression=OWLClass(IRI('http://example.com/father#', 'male')),
                                   annotations=[]),
                               OWLClassAssertionAxiom(
                                   individual=OWLNamedIndividual(IRI('http://example.com/father#', 'stefan')),
                                   class_expression=OWLClass(IRI('http://example.com/father#', 'male')),
                                   annotations=[]),
                               OWLClassAssertionAxiom(
                                   individual=OWLNamedIndividual(IRI('http://example.com/father#', 'anna')),
                                   class_expression=OWLClass(IRI('http://example.com/father#', 'female')),
                                   annotations=[]),
                               OWLObjectPropertyAssertionAxiom(
                                   subject=OWLNamedIndividual(IRI('http://example.com/father#', 'anna')),
                                   property_=OWLObjectProperty(IRI('http://example.com/father#', 'hasChild')),
                                   object_=OWLNamedIndividual(IRI('http://example.com/father#', 'heinz')),
                                   annotations=[]),
                               OWLObjectPropertyAssertionAxiom(
                                   subject=OWLNamedIndividual(IRI('http://example.com/father#', 'stefan')),
                                   property_=OWLObjectProperty(IRI('http://example.com/father#', 'hasChild')),
                                   object_=OWLNamedIndividual(IRI('http://example.com/father#', 'markus')),
                                   annotations=[]),
                               OWLObjectPropertyAssertionAxiom(
                                   subject=OWLNamedIndividual(IRI('http://example.com/father#', 'markus')),
                                   property_=OWLObjectProperty(IRI('http://example.com/father#', 'hasChild')),
                                   object_=OWLNamedIndividual(IRI('http://example.com/father#', 'anna')),
                                   annotations=[]),
                               OWLObjectPropertyAssertionAxiom(
                                   subject=OWLNamedIndividual(IRI('http://example.com/father#', 'martin')),
                                   property_=OWLObjectProperty(IRI('http://example.com/father#', 'hasChild')),
                                   object_=OWLNamedIndividual(IRI('http://example.com/father#', 'heinz')),
                                   annotations=[])])

    def test_get_tbox(self):
        print(father_onto.get_tbox_axioms())
        self.assertCountEqual(list(father_onto.get_tbox_axioms()),
                              [OWLObjectPropertyDomainAxiom(
                                  OWLObjectProperty(IRI('http://example.com/father#', 'hasChild')),
                                                            OWLClass(IRI('http://example.com/father#', 'person')),[]),
                               OWLObjectPropertyRangeAxiom(
                                   OWLObjectProperty(IRI('http://example.com/father#', 'hasChild')),
                                                           OWLClass(IRI('http://example.com/father#', 'person')),[]),
                               OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://example.com/father#', 'person')),
                                                  super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),
                                                  annotations=[]),
                               OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://example.com/father#', 'male')),
                                                  super_class=OWLClass(IRI('http://example.com/father#', 'person')),
                                                  annotations=[]),
                               OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://example.com/father#', 'female')),
                                                  super_class=OWLClass(IRI('http://example.com/father#', 'person')),
                                                  annotations=[]),
                               OWLEquivalentClassesAxiom([OWLObjectComplementOf(
                                   OWLClass(IRI('http://example.com/father#', 'female'))),
                                                          OWLClass(IRI('http://example.com/father#', 'male'))],[])])
