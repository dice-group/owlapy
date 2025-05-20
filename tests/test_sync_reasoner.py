import os
import unittest

from owlapy.class_expression import OWLClass, OWLDataSomeValuesFrom, OWLObjectIntersectionOf, OWLNothing, OWLThing, \
    OWLClassExpression, OWLObjectSomeValuesFrom, OWLObjectOneOf
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLDisjointClassesAxiom, OWLDeclarationAxiom, OWLClassAssertionAxiom, OWLSubClassOfAxiom, \
    OWLEquivalentClassesAxiom, OWLSubDataPropertyOfAxiom, OWLSubObjectPropertyOfAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLBottomObjectProperty, OWLTopObjectProperty, OWLBottomDataProperty, OWLTopDataProperty, \
    OWLLiteral
from owlapy.owl_ontology import Ontology
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty
from owlapy.owl_reasoner import SyncReasoner
from owlapy.providers import owl_datatype_min_inclusive_restriction


NS = 'http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#'

a = OWLNamedIndividual(IRI(NS, "a"))
b = OWLNamedIndividual(IRI(NS, "b"))
c = OWLNamedIndividual(IRI(NS, "c"))
d = OWLNamedIndividual(IRI(NS, "d"))
e = OWLNamedIndividual(IRI(NS, "e"))
g = OWLNamedIndividual(IRI(NS, "g"))
m = OWLNamedIndividual(IRI(NS, "m"))
l = OWLNamedIndividual(IRI(NS, "l"))  # noqa: E741
n = OWLNamedIndividual(IRI(NS, "n"))
o = OWLNamedIndividual(IRI(NS, "o"))
p = OWLNamedIndividual(IRI(NS, "p"))
q = OWLNamedIndividual(IRI(NS, "q"))
r = OWLNamedIndividual(IRI(NS, "r"))
s = OWLNamedIndividual(IRI(NS, "s"))
ind1 = OWLNamedIndividual(IRI(NS, "ind1"))

r1 = OWLObjectProperty(IRI(NS, "r1"))
r2 = OWLObjectProperty(IRI(NS, "r2"))
r3 = OWLObjectProperty(IRI(NS, "r3"))
r4 = OWLObjectProperty(IRI(NS, "r4"))
r5 = OWLObjectProperty(IRI(NS, "r5"))
r6 = OWLObjectProperty(IRI(NS, "r6"))
r7 = OWLObjectProperty(IRI(NS, "r7"))

dp1 = OWLDataProperty(IRI(NS, "dp1"))
dp2 = OWLDataProperty(IRI(NS, "dp2"))
dp3 = OWLDataProperty(IRI(NS, "dp3"))

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
reasoner2 = SyncReasoner("KGs/Test/test_ontology.owl")

class TestSyncReasoner(unittest.TestCase):
    ns = "http://dl-learner.org/mutagenesis#"
    ontology_path = "KGs/Mutagenesis/mutagenesis.owl"
    nitrogen38 = OWLClass(IRI.create(ns, "Nitrogen-38"))
    compound = OWLClass(IRI.create(ns, "Compound"))
    atom = OWLClass(IRI.create(ns, "Atom"))
    charge = OWLDataProperty(IRI.create(ns, "charge"))
    hasAtom = OWLObjectProperty(IRI.create(ns, "hasAtom"))
    d100_25 = OWLNamedIndividual(IRI.create(ns, "d100_25"))
    has_charge_more_than_0_85 = OWLDataSomeValuesFrom(charge, owl_datatype_min_inclusive_restriction(0.85))
    ce = OWLObjectIntersectionOf([nitrogen38, has_charge_more_than_0_85])
    reasoner = SyncReasoner(ontology_path)

    def test_father_dataset(self):
        ontology_path = "KGs/Family/father.owl"
        # Available OWL Reasoners: 'HermiT', 'Pellet', 'JFact', 'Openllet'
        owl_reasoners = dict()
        owl_reasoners["HermiT"] = SyncReasoner(ontology=ontology_path, reasoner="HermiT")
        owl_reasoners["Pellet"] = SyncReasoner(ontology=ontology_path, reasoner="Pellet")
        owl_reasoners["JFact"] = SyncReasoner(ontology=ontology_path, reasoner="JFact")
        owl_reasoners["Openllet"] = SyncReasoner(ontology=ontology_path, reasoner="Openllet")

        for k, reasoner in owl_reasoners.items():
            exist_haschild_female = OWLObjectSomeValuesFrom(
                property=OWLObjectProperty('http://example.com/father#hasChild'),
                filler=OWLClass('http://example.com/father#female'))

            exist_haschild_anna = OWLObjectSomeValuesFrom(property=OWLObjectProperty('http://example.com/father#hasChild'),
                                                          filler=OWLObjectOneOf(
                                                              OWLNamedIndividual('http://example.com/father#anna')))
            assert reasoner.instances(ce=exist_haschild_female) == reasoner.instances(ce=exist_haschild_anna) == {
                OWLNamedIndividual('http://example.com/father#markus')}

    def test_consistency_check(self):
        self.assertEqual(self.reasoner.has_consistent_ontology(), True)

    def test_named_concepts(self):

        ontology_path = "KGs/Family/family-benchmark_rich_background.owl"

        # Available OWL Reasoners: 'HermiT', 'Pellet', 'JFact', 'Openllet'
        owl_reasoners = dict()
        owl_reasoners["HermiT"] = SyncReasoner(ontology=ontology_path, reasoner="HermiT")
        owl_reasoners["Pellet"] = SyncReasoner(ontology=ontology_path, reasoner="Pellet")
        owl_reasoners["JFact"] = SyncReasoner(ontology=ontology_path, reasoner="JFact")
        owl_reasoners["Openllet"] = SyncReasoner(ontology=ontology_path, reasoner="Openllet")

        onto = Ontology(ontology_path)

        def compute_agreements(i: OWLClassExpression, verbose=False):
            if verbose:
                print(f"Computing agreements between Reasoners on {i}...")
            retrieval_result = None
            flag = False
            for __, reasoner in owl_reasoners.items():
                if retrieval_result:
                    flag = retrieval_result == {_.str for _ in reasoner.instances(i)}
                else:
                    retrieval_result = {_.str for _ in reasoner.instances(i)}
            return flag

        # Agreement between instances over
        for i in onto.classes_in_signature():
            assert compute_agreements(i, True)

    def test_inconsistency_check(self):
        onto = Ontology(IRI.create(self.ontology_path))

        carbon230 = OWLClass(IRI.create(self.ns, "Carbon-230"))
        axiom = OWLDisjointClassesAxiom([self.nitrogen38, carbon230])
        onto.add_axiom(axiom)
        new_individual = OWLNamedIndividual(IRI.create(self.ns, "testIndividual"))
        onto.add_axiom(OWLDeclarationAxiom(new_individual))
        onto.add_axiom(OWLClassAssertionAxiom(new_individual, self.nitrogen38))
        onto.add_axiom(OWLClassAssertionAxiom(new_individual, carbon230))

        onto.save("test.owl")
        reasoner = SyncReasoner("test.owl")
        self.assertEqual(reasoner.has_consistent_ontology(), False)
        os.remove("test.owl")

    def test_instances_retrieval(self):
        instances = self.reasoner.instances(self.ce)
        expected = [OWLNamedIndividual(IRI('http://dl-learner.org/mutagenesis#', 'd141_10')),
                    OWLNamedIndividual(IRI('http://dl-learner.org/mutagenesis#', 'd195_12')),
                    OWLNamedIndividual(IRI('http://dl-learner.org/mutagenesis#', 'd144_10')),
                    OWLNamedIndividual(IRI('http://dl-learner.org/mutagenesis#', 'd147_11')),
                    OWLNamedIndividual(IRI('http://dl-learner.org/mutagenesis#', 'e18_9')),
                    OWLNamedIndividual(IRI('http://dl-learner.org/mutagenesis#', 'd175_17')),
                    OWLNamedIndividual(IRI('http://dl-learner.org/mutagenesis#', 'e16_9'))]
        # Assert equal without considering the order
        for instance in instances:
            self.assertIn(instance, expected)
        self.assertEqual(len(list(instances)), len(expected))

    def test_equivalent_classes(self):
        self.assertCountEqual(list(reasoner2.equivalent_classes(N)), [N, Q])

    def test_disjoint_classes(self):
        self.assertCountEqual(list(reasoner2.disjoint_classes(L)), [M])

    def test_sub_classes(self):
        self.assertCountEqual(list(reasoner2.sub_classes(P)), [O])

    def test_super_classes(self):
        self.assertCountEqual(list(reasoner2.super_classes(O)), [P, OWLThing])

    def test_object_property_domains(self):
        self.assertCountEqual(list(self.reasoner.object_property_domains(self.hasAtom, False)), [self.compound, OWLThing])
        self.assertCountEqual(list(self.reasoner.object_property_domains(self.hasAtom, True)), [self.compound])

    def test_object_property_ranges(self):
        self.assertCountEqual(list(reasoner2.object_property_ranges(r1, False)), [OWLThing, G])
        self.assertCountEqual(list(reasoner2.object_property_ranges(r1, True)), [G])

    def test_sub_object_properties(self):
        self.assertCountEqual(list(reasoner2.sub_object_properties(r1, False)), [r2])
        self.assertCountEqual(list(reasoner2.sub_object_properties(r1, True)), [r2])

    def test_super_object_properties(self):
        self.assertCountEqual(list(reasoner2.super_object_properties(r2, False)), [r1, OWLTopObjectProperty])
        self.assertCountEqual(list(reasoner2.super_object_properties(r2, True)), [r1])

    def test_sub_data_properties(self):
        self.assertCountEqual(list(reasoner2.sub_data_properties(dp1, False)), [dp2])
        self.assertCountEqual(list(reasoner2.sub_data_properties(dp1, True)), [dp2])

    def test_super_data_properties(self):
        self.assertCountEqual(list(reasoner2.super_data_properties(dp2, False)), [dp1, OWLTopDataProperty])
        self.assertCountEqual(list(reasoner2.super_data_properties(dp2, True)), [dp1])

    def test_different_individuals(self):
        self.assertCountEqual(list(reasoner2.different_individuals(l)), [m])
        self.assertCountEqual(list(reasoner2.different_individuals(m)), [l])

    def test_object_property_values(self):
        self.assertCountEqual(list(reasoner2.object_property_values(n, r3)), [q])
        self.assertCountEqual(list(reasoner2.object_property_values(n, r4)), [l, q])

    def test_data_property_values(self):
        self.assertCountEqual(list(self.reasoner.data_property_values(self.d100_25, self.charge)), [OWLLiteral(0.332)])

    def test_disjoint_object_properties(self):
        self.assertCountEqual(list(reasoner2.disjoint_object_properties(r5)), [r1, r2])
        self.assertCountEqual(list(reasoner2.disjoint_object_properties(r1)), [r5])
        self.assertCountEqual(list(reasoner2.disjoint_object_properties(r2, True)), [r5, OWLBottomObjectProperty])

    def test_disjoint_data_properties(self):
        self.assertCountEqual(list(reasoner2.disjoint_data_properties(dp1)), [dp3])
        self.assertCountEqual(list(reasoner2.disjoint_data_properties(dp3,True)), [dp1,dp2, OWLBottomDataProperty])

    def test_types(self):
        self.assertCountEqual(list(reasoner2.types(c)), [I, J, K, OWLThing])

    def test_infer_axiom(self):
        self.assertCountEqual(list(reasoner2.infer_axioms(["InferredClassAssertionAxiomGenerator", "InferredSubClassAxiomGenerator",
             "InferredDisjointClassesAxiomGenerator", "InferredEquivalentClassAxiomGenerator",
             "InferredEquivalentDataPropertiesAxiomGenerator","InferredEquivalentObjectPropertyAxiomGenerator",
             "InferredInverseObjectPropertiesAxiomGenerator","InferredSubDataPropertyAxiomGenerator",
             "InferredSubObjectPropertyAxiomGenerator","InferredDataPropertyCharacteristicAxiomGenerator",
             "InferredObjectPropertyCharacteristicAxiomGenerator"
             ])),[OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'f')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'l')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'L')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'm')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'M')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'a')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'e')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'C')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 's')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'n')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'p')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'P')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'a')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'AB')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'q')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'Q')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'a')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'B')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'n')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'N')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'c')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'K')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'e')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'A')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'ind1')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'd')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'o')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'O')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'c')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'I')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'r')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'R')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'q')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'l')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 's')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'S')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'f')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'E')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'g')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'b')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'n')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'Q')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'e')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'B')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'a')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'C')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'o')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'o')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'P')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'ind1')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'H')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'a')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'A')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'e')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'ind1')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'F')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 's')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'T')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'r')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'e')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'AB')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'm')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'h')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'd')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'D')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'c')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'J')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'b')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'B')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'c')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'd')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'B')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'p')),class_expression=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'q')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'N')),annotations=[]),
                  OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'g')),class_expression=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'G')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'AB')),super_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'A')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'I')),super_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'K')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'N')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'Q')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'A')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'D')),super_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'B')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'AB')),super_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'C')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'K')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'B')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'G')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'O')),super_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'P')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'L')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'S')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'F')),super_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'H')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'AB')),super_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'B')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'E')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'J')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'U')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'I')),super_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'J')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'T')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'P')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'C')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'H')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'M')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'R')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'D'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'Q'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'J'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'E'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'K'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'L'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'R'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'AB'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'S'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'M'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'F'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'A'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'G'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'T'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'H'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'N'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'U'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'M')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'L'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'I'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'B'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'O'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'P'))],[]),
                  OWLDisjointClassesAxiom([OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'C'))],[]),
                  OWLEquivalentClassesAxiom([OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'Q')), OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'N'))],[]),
                  OWLSubDataPropertyOfAxiom(sub_property=OWLDataProperty(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'dp2')),super_property=OWLDataProperty(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'dp1')),annotations=[]),
                  OWLSubDataPropertyOfAxiom(sub_property=OWLDataProperty(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'dp3')),super_property=OWLDataProperty(IRI('http://www.w3.org/2002/07/owl#', 'topDataProperty')),annotations=[]),
                  OWLSubDataPropertyOfAxiom(sub_property=OWLDataProperty(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'dp1')),super_property=OWLDataProperty(IRI('http://www.w3.org/2002/07/owl#', 'topDataProperty')),annotations=[]),
                  OWLSubObjectPropertyOfAxiom(sub_property=OWLObjectProperty(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'r5')),super_property=OWLObjectProperty(IRI('http://www.w3.org/2002/07/owl#', 'topObjectProperty')),annotations=[]),
                  OWLSubObjectPropertyOfAxiom(sub_property=OWLObjectProperty(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'r2')),super_property=OWLObjectProperty(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'r1')),annotations=[]),
                  OWLSubObjectPropertyOfAxiom(sub_property=OWLObjectProperty(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'r7')),super_property=OWLObjectProperty(IRI('http://www.w3.org/2002/07/owl#', 'topObjectProperty')),annotations=[]),
                  OWLSubObjectPropertyOfAxiom(sub_property=OWLObjectProperty(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'r4')),super_property=OWLObjectProperty(IRI('http://www.w3.org/2002/07/owl#', 'topObjectProperty')),annotations=[]),
                  OWLSubObjectPropertyOfAxiom(sub_property=OWLObjectProperty(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'r1')),super_property=OWLObjectProperty(IRI('http://www.w3.org/2002/07/owl#', 'topObjectProperty')),annotations=[]),
                  OWLSubObjectPropertyOfAxiom(sub_property=OWLObjectProperty(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'r3')),super_property=OWLObjectProperty(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'r4')),annotations=[]),
                  OWLSubObjectPropertyOfAxiom(sub_property=OWLObjectProperty(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'r6')),super_property=OWLObjectProperty(IRI('http://www.w3.org/2002/07/owl#', 'topObjectProperty')),annotations=[])])

    def test_entailment(self):
        self.assertTrue(reasoner2.is_entailed(OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'D')), super_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'B')), annotations=[])))
        self.assertFalse(reasoner2.is_entailed(OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'B')), super_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'D')), annotations=[])))
        self.assertFalse(reasoner2.is_entailed(OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'C')), super_class=OWLClass(IRI('http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#', 'G')), annotations=[])))

    def test_satisfiability(self):
        ST = OWLObjectIntersectionOf([S, T])
        LM = OWLObjectIntersectionOf([L, M])
        r7E = OWLObjectSomeValuesFrom(property=r7, filler=E)
        self.assertTrue(reasoner2.is_satisfiable(ST))
        self.assertTrue(reasoner2.is_satisfiable(r7E))
        self.assertFalse(reasoner2.is_satisfiable(LM))

    def test_unsatisfiability(self):
        self.assertEqual(list(reasoner2.unsatisfiable_classes()), [OWLNothing])
        self.assertNotEqual(list(reasoner2.unsatisfiable_classes()), [OWLThing])
