import os
import unittest

from jpype import JDouble

from owlapy.class_expression import OWLClass, OWLDataSomeValuesFrom, OWLObjectIntersectionOf
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLDisjointClassesAxiom, OWLDeclarationAxiom, OWLClassAssertionAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology_manager import OntologyManager
from owlapy.owl_property import OWLDataProperty
from owlapy.owlapi_adaptor import OWLAPIAdaptor
from owlapy.providers import owl_datatype_min_inclusive_restriction


class TestOwlapiAdaptor(unittest.TestCase):
    ns = "http://dl-learner.org/mutagenesis#"
    ontology_path = "KGs/Mutagenesis/mutagenesis.owl"
    nitrogen38 = OWLClass(IRI.create(ns, "Nitrogen-38"))
    charge = OWLDataProperty(IRI.create(ns, "charge"))
    has_charge_more_than_0_85 = OWLDataSomeValuesFrom(charge, owl_datatype_min_inclusive_restriction(0.85))
    ce = OWLObjectIntersectionOf([nitrogen38, has_charge_more_than_0_85])
    adaptor = OWLAPIAdaptor(ontology_path)

    def test_consistency_check(self):
        self.assertEqual(self.adaptor.has_consistent_ontology(), True)

    def test_inconsistency_check(self):
        manager = OntologyManager()
        onto = manager.load_ontology(IRI.create(self.ontology_path))

        carbon230 = OWLClass(IRI.create(self.ns, "Carbon-230"))
        axiom = OWLDisjointClassesAxiom([self.nitrogen38, carbon230])
        manager.add_axiom(onto, axiom)
        new_individual = OWLNamedIndividual(IRI.create(self.ns, "testIndividual"))
        manager.add_axiom(onto, OWLDeclarationAxiom(new_individual))
        manager.add_axiom(onto, OWLClassAssertionAxiom(new_individual, self.nitrogen38))
        manager.add_axiom(onto, OWLClassAssertionAxiom(new_individual, carbon230))

        manager.save_ontology(onto, IRI.create("file:/test.owl"))
        adaptor1 = OWLAPIAdaptor("test.owl")
        self.assertEqual(adaptor1.has_consistent_ontology(), False)
        os.remove("test.owl")

    def test_instances_retrieval(self):
        instances = self.adaptor.instances(self.ce)
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

    def test_conversion(self):
        # construct the class expression in owlapi
        from org.semanticweb.owlapi.model import IRI as IRIowlapi, OWLClass, OWLObjectProperty
        from org.semanticweb.owlapi.vocab import OWLFacet

        nitrogenIRI = IRIowlapi.create(self.ns + "Nitrogen-38")
        charge_iri = IRIowlapi.create(self.ns + "charge")

        data_factory = self.adaptor.manager.getOWLDataFactory()
        nitrogen_class = data_factory.getOWLClass(nitrogenIRI)

        charge_property = data_factory.getOWLDataProperty(charge_iri)
        double_datatype = data_factory.getDoubleOWLDatatype()
        facet_restriction = data_factory.getOWLFacetRestriction(OWLFacet.MIN_INCLUSIVE, JDouble(0.85))
        datatype_restriction = data_factory.getOWLDatatypeRestriction(double_datatype, facet_restriction)
        some_values_from = data_factory.getOWLDataSomeValuesFrom(charge_property, datatype_restriction)

        class_expression = data_factory.getOWLObjectIntersectionOf(nitrogen_class, some_values_from)

        # compare them with the adaptor converted expression
        ce_converted = self.adaptor.convert_to_owlapi(self.ce)
        print(ce_converted)
        print(class_expression)
        self.assertEqual(class_expression, ce_converted)

        # convert back to owlapy and check for equality
        ce_1 = self.adaptor.convert_from_owlapi(class_expression)
        ce_2 = self.adaptor.convert_from_owlapi(ce_converted)

        self.assertEqual(ce_1, ce_2)
        self.assertEqual(ce_1, self.ce)
        self.assertEqual(ce_2, self.ce)
