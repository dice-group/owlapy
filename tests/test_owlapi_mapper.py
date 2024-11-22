import unittest

from jpype import JDouble

from owlapy.class_expression import OWLClass, OWLDataSomeValuesFrom, OWLObjectIntersectionOf, OWLObjectComplementOf, \
    OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality, OWLDataMinCardinality, \
    OWLDataMaxCardinality, OWLDataExactCardinality, OWLObjectHasSelf, OWLObjectHasValue, OWLObjectSomeValuesFrom, \
    OWLObjectAllValuesFrom, OWLDataAllValuesFrom, OWLDataHasValue, OWLObjectUnionOf, OWLObjectOneOf, \
    OWLFacetRestriction, OWLDatatypeRestriction, OWLDataOneOf
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLAnnotationProperty, OWLAnnotation, OWLAnnotationAssertionAxiom
from owlapy.owl_data_ranges import OWLDataIntersectionOf, OWLDataUnionOf, OWLDataComplementOf
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral, IntegerOWLDatatype, BooleanOWLDatatype, DoubleOWLDatatype
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty
from owlapy.owlapi_mapper import OWLAPIMapper
from owlapy.providers import owl_datatype_min_inclusive_restriction
from owlapy.vocab import OWLFacet


class TestOWLAPIMapper(unittest.TestCase):

    mapper = OWLAPIMapper()
    test_ns = "http://test_namespace#"
    i = OWLNamedIndividual(test_ns + "test_i")
    c = OWLClass(test_ns + "test_c")
    dp = OWLDataProperty(test_ns + "test_dp")
    op = OWLObjectProperty(test_ns + "test_op")
    dt = OWLDatatype(IRI.create(test_ns + "test_dt"))
    ap = OWLAnnotationProperty(IRI.create(test_ns + "test_ap"))

    def test_random_complex_ce_mapping(self):

        # construct the class expression in owlapy
        ns = "http://dl-learner.org/mutagenesis#"
        nitrogen38 = OWLClass(IRI.create(ns, "Nitrogen-38"))
        charge = OWLDataProperty(IRI.create(ns, "charge"))
        has_charge_more_than_0_85 = OWLDataSomeValuesFrom(charge, owl_datatype_min_inclusive_restriction(0.85))
        ce = OWLObjectIntersectionOf([nitrogen38, has_charge_more_than_0_85])

        # construct the class expression in owlapi
        from org.semanticweb.owlapi.model import IRI as IRIowlapi
        from org.semanticweb.owlapi.vocab import OWLFacet
        from uk.ac.manchester.cs.owl.owlapi import OWLDataFactoryImpl

        nitrogenIRI = IRIowlapi.create(ns + "Nitrogen-38")
        charge_iri = IRIowlapi.create(ns + "charge")
        data_factory = OWLDataFactoryImpl()
        nitrogen_class = data_factory.getOWLClass(nitrogenIRI)

        charge_property = data_factory.getOWLDataProperty(charge_iri)
        double_datatype = data_factory.getDoubleOWLDatatype()
        facet_restriction = data_factory.getOWLFacetRestriction(OWLFacet.MIN_INCLUSIVE, JDouble(0.85))
        datatype_restriction = data_factory.getOWLDatatypeRestriction(double_datatype, facet_restriction)
        some_values_from = data_factory.getOWLDataSomeValuesFrom(charge_property, datatype_restriction)

        class_expression = data_factory.getOWLObjectIntersectionOf(nitrogen_class, some_values_from)

        # compare them with the mapped expression
        ce_converted = self.mapper.map_(ce)
        self.assertEqual(class_expression, ce_converted)

        # map back to owlapy and check for equality
        ce_1 = self.mapper.map_(class_expression)
        ce_2 = self.mapper.map_(ce_converted)

        self.assertEqual(ce_1, ce_2)
        self.assertEqual(ce_1, ce)
        self.assertEqual(ce_2, ce)

    def test_entity_mapping(self):

        iri = IRI.create(self.test_ns + "test")

        self.assertEqual(iri, self.mapper.map_(self.mapper.map_(iri)))
        self.assertEqual(self.i, self.mapper.map_(self.mapper.map_(self.i)))
        self.assertEqual(self.c, self.mapper.map_(self.mapper.map_(self.c)))
        self.assertEqual(self.dp, self.mapper.map_(self.mapper.map_(self.dp)))
        self.assertEqual(self.op, self.mapper.map_(self.mapper.map_(self.op)))
        self.assertEqual(self.dt, self.mapper.map_(self.mapper.map_(self.dt)))
        self.assertEqual(self.ap, self.mapper.map_(self.mapper.map_(self.ap)))

    def test_ce_mapping(self):

        lit = OWLLiteral(2)

        oco = OWLObjectComplementOf(self.c)
        ominc = OWLObjectMinCardinality(1, self.op, self.c)
        oec = OWLObjectExactCardinality(2, self.op, self.c)
        omaxc = OWLObjectMaxCardinality(3, self.op, self.c)
        dminc = OWLDataMinCardinality(1, self.dp, IntegerOWLDatatype)
        dec = OWLDataExactCardinality(2, self.dp, IntegerOWLDatatype)
        dmaxc = OWLDataMaxCardinality(3, self.dp, IntegerOWLDatatype)
        ohs = OWLObjectHasSelf(self.op)
        ohv = OWLObjectHasValue(self.op, self.i)
        osv = OWLObjectSomeValuesFrom(self.op, self.c)
        oav = OWLObjectAllValuesFrom(self.op, self.c)
        dsv = OWLDataSomeValuesFrom(self.dp, IntegerOWLDatatype)
        dav = OWLDataAllValuesFrom(self.dp, IntegerOWLDatatype)
        dhv = OWLDataHasValue(self.dp, lit)
        ooo = OWLObjectOneOf(self.i)
        ooo2 = OWLObjectOneOf([self.i])
        oio = OWLObjectIntersectionOf([ohs, ohv])
        ouo = OWLObjectUnionOf([oco, ominc])

        self.assertEqual(lit, self.mapper.map_(self.mapper.map_(lit)))
        self.assertEqual(oco, self.mapper.map_(self.mapper.map_(oco)))
        self.assertEqual(ominc, self.mapper.map_(self.mapper.map_(ominc)))
        self.assertEqual(oec, self.mapper.map_(self.mapper.map_(oec)))
        self.assertEqual(omaxc, self.mapper.map_(self.mapper.map_(omaxc)))
        self.assertEqual(dminc, self.mapper.map_(self.mapper.map_(dminc)))
        self.assertEqual(dec, self.mapper.map_(self.mapper.map_(dec)))
        self.assertEqual(dmaxc, self.mapper.map_(self.mapper.map_(dmaxc)))
        self.assertEqual(ohv, self.mapper.map_(self.mapper.map_(ohv)))
        self.assertEqual(osv, self.mapper.map_(self.mapper.map_(osv)))
        self.assertEqual(oav, self.mapper.map_(self.mapper.map_(oav)))
        self.assertEqual(dsv, self.mapper.map_(self.mapper.map_(dsv)))
        self.assertEqual(dav, self.mapper.map_(self.mapper.map_(dav)))
        self.assertEqual(dhv, self.mapper.map_(self.mapper.map_(dhv)))
        self.assertEqual(ooo2, self.mapper.map_(self.mapper.map_(ooo)))
        self.assertEqual(ooo2, self.mapper.map_(self.mapper.map_(ooo2)))
        self.assertEqual(oio, self.mapper.map_(self.mapper.map_(oio)))
        self.assertEqual(ouo, self.mapper.map_(self.mapper.map_(ouo)))

    def test_datarange_mapping(self):

        lit = OWLLiteral(0.1)
        bdt = BooleanOWLDatatype
        f = OWLFacet.MAX_EXCLUSIVE
        fr = OWLFacetRestriction(f, lit)
        dtr = OWLDatatypeRestriction(DoubleOWLDatatype, fr)
        dio = OWLDataIntersectionOf([dtr, bdt])
        doo = OWLDataOneOf([lit, OWLLiteral(True)])
        duo = OWLDataUnionOf([dtr, DoubleOWLDatatype, IntegerOWLDatatype])
        dco = OWLDataComplementOf(dtr)

        self.assertEqual(lit, self.mapper.map_(self.mapper.map_(lit)))
        self.assertEqual(bdt, self.mapper.map_(self.mapper.map_(bdt)))
        self.assertEqual(f, self.mapper.map_(self.mapper.map_(f)))
        self.assertEqual(fr, self.mapper.map_(self.mapper.map_(fr)))
        self.assertEqual(dtr, self.mapper.map_(self.mapper.map_(dtr)))
        self.assertCountEqual(list(dio.operands()), list(self.mapper.map_(self.mapper.map_(dio)).operands()))
        self.assertCountEqual(list(doo.operands()), list(self.mapper.map_(self.mapper.map_(doo)).operands()))
        self.assertCountEqual(list(duo.operands()), list(self.mapper.map_(self.mapper.map_(duo)).operands()))
        self.assertEqual(dco, self.mapper.map_(self.mapper.map_(dco)))

    def test_axiom_mapping(self):

        ap = OWLAnnotationProperty(IRI.create(self.test_ns + "test_annotation"))
        av = OWLLiteral("Value of annotation")
        a = OWLAnnotation(ap, av)
        aa = OWLAnnotationAssertionAxiom(IRI.create(self.test_ns + "test_annotation_subject"), a)


        self.assertEqual(ap, self.mapper.map_(self.mapper.map_(ap)))
        self.assertEqual(av, self.mapper.map_(self.mapper.map_(av)))
        self.assertEqual(a, self.mapper.map_(self.mapper.map_(a)))
        self.assertEqual(aa, self.mapper.map_(self.mapper.map_(aa)))
