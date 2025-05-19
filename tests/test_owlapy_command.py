import subprocess
import sys
import unittest

from owlapy.class_expression import OWLClass, OWLNothing
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLSymmetricObjectPropertyAxiom, OWLReflexiveObjectPropertyAxiom
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_property import OWLObjectProperty
from owlapy.owl_reasoner import SyncReasoner


class TestOwlapyCommand(unittest.TestCase):

    def test_owlapy_entry_point(self):
        result = subprocess.run([sys.executable,
                                 '-m',
                                 'owlapy.scripts.run',
                                 '--path_ontology',
                                 'KGs/Family/family-benchmark_rich_background.owl'
                                 ])

        self.assertEqual(result.returncode, 0)

        onto = SyncOntology("inferred_axioms_ontology.owl")

        ops = onto.object_properties_in_signature()
        self.assertCountEqual(list(ops), [OWLObjectProperty(IRI('http://www.benchmark.org/family#', 'hasChild')),
                                     OWLObjectProperty(IRI('http://www.benchmark.org/family#', 'hasParent')),
                                     OWLObjectProperty(IRI('http://www.benchmark.org/family#', 'hasSibling')),
                                     OWLObjectProperty(IRI('http://www.benchmark.org/family#', 'married')),
                                     OWLObjectProperty(IRI('http://www.w3.org/2002/07/owl#', 'topObjectProperty'))])

        reasoner = SyncReasoner(onto)
        mapper = reasoner.mapper
        # noinspection PyUnresolvedReferences
        from org.semanticweb.owlapi.model import AxiomType
        symetrical_axioms = mapper.map_(
            onto.get_owlapi_ontology().getAxioms(AxiomType.SYMMETRIC_OBJECT_PROPERTY).stream())

        reflexive_axioms = mapper.map_(
            onto.get_owlapi_ontology().getAxioms(AxiomType.REFLEXIVE_OBJECT_PROPERTY).stream())

        self.assertEqual(list(symetrical_axioms)[0],
                         OWLSymmetricObjectPropertyAxiom(OWLObjectProperty(IRI('http://www.w3.org/2002/07/owl#',
                                                                               'topObjectProperty')), []))

        self.assertEqual(list(reflexive_axioms)[0],
                         OWLReflexiveObjectPropertyAxiom(OWLObjectProperty(IRI('http://www.w3.org/2002/07/owl#',
                                                                               'topObjectProperty')), []))

        classes = onto.classes_in_signature()
        self.assertCountEqual(list(classes), [OWLClass(IRI('http://www.benchmark.org/family#', 'Brother')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Child')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Daughter')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Father')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Female')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Grandchild')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Granddaughter')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Grandfather')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Grandmother')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Grandparent')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Grandson')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Male')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Mother')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Parent')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Person')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'PersonWithASibling')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Sister')),
                                         OWLClass(IRI('http://www.benchmark.org/family#', 'Son')),
                                         OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing')),
                                         OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing'))])

        disjoint_of_owl_nothing = reasoner.disjoint_classes(OWLNothing)
        self.assertCountEqual(list(disjoint_of_owl_nothing),
                         [OWLClass(IRI('http://www.benchmark.org/family#', 'Grandchild')),
                          OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Person')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Grandparent')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Grandfather')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Male')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Son')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Grandson')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Female')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Granddaughter')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'PersonWithASibling')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Sister')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Grandmother')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Daughter')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Brother')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Mother')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Child')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Father')),
                          OWLClass(IRI('http://www.benchmark.org/family#', 'Parent'))])

        len_inds = len(list(onto.individuals_in_signature()))
        self.assertEqual(len_inds, 202)

