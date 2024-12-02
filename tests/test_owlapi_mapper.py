import unittest

from jpype import JDouble

from owlapy.class_expression import OWLClass, OWLDataSomeValuesFrom, OWLObjectIntersectionOf, OWLObjectComplementOf, \
    OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality, OWLDataMinCardinality, \
    OWLDataMaxCardinality, OWLDataExactCardinality, OWLObjectHasSelf, OWLObjectHasValue, OWLObjectSomeValuesFrom, \
    OWLObjectAllValuesFrom, OWLDataAllValuesFrom, OWLDataHasValue, OWLObjectUnionOf, OWLObjectOneOf, \
    OWLFacetRestriction, OWLDatatypeRestriction, OWLDataOneOf, OWLThing
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLAnnotationProperty, OWLAnnotation, OWLAnnotationAssertionAxiom, OWLDeclarationAxiom, \
    OWLClassAssertionAxiom, OWLObjectPropertyAssertionAxiom, OWLDataPropertyAssertionAxiom, \
    OWLNegativeDataPropertyAssertionAxiom, OWLNegativeObjectPropertyAssertionAxiom, OWLObjectPropertyDomainAxiom, \
    OWLDataPropertyDomainAxiom, OWLAnnotationPropertyDomainAxiom, OWLAnnotationPropertyRangeAxiom, \
    OWLObjectPropertyRangeAxiom, OWLDataPropertyRangeAxiom, OWLEquivalentDataPropertiesAxiom, \
    OWLEquivalentObjectPropertiesAxiom, OWLEquivalentClassesAxiom, OWLDisjointClassesAxiom, \
    OWLDisjointDataPropertiesAxiom, OWLDisjointObjectPropertiesAxiom, OWLHasKeyAxiom, OWLSubClassOfAxiom, \
    OWLSubDataPropertyOfAxiom, OWLSubObjectPropertyOfAxiom, OWLSubAnnotationPropertyOfAxiom, \
    OWLAsymmetricObjectPropertyAxiom, OWLFunctionalObjectPropertyAxiom, OWLInverseFunctionalObjectPropertyAxiom, \
    OWLIrreflexiveObjectPropertyAxiom, OWLReflexiveObjectPropertyAxiom, OWLSymmetricObjectPropertyAxiom, \
    OWLTransitiveObjectPropertyAxiom, OWLFunctionalDataPropertyAxiom, OWLDatatypeDefinitionAxiom, \
    OWLDifferentIndividualsAxiom, OWLSameIndividualAxiom, OWLDisjointUnionAxiom, OWLInverseObjectPropertiesAxiom
from owlapy.owl_data_ranges import OWLDataIntersectionOf, OWLDataUnionOf, OWLDataComplementOf
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral, IntegerOWLDatatype, BooleanOWLDatatype, DoubleOWLDatatype
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty, OWLObjectInverseOf
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
        ip = OWLObjectInverseOf(self.op)
        self.assertEqual(ip, self.mapper.map_(self.mapper.map_(ip)))
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
        self.assertEqual(dio, self.mapper.map_(self.mapper.map_(dio)))
        self.assertEqual(doo, self.mapper.map_(self.mapper.map_(doo)))
        self.assertCountEqual(list(duo.operands()), list(self.mapper.map_(self.mapper.map_(duo)).operands()))
        self.assertEqual(dco, self.mapper.map_(self.mapper.map_(dco)))

    def test_axiom_mapping(self):

        ap = OWLAnnotationProperty(IRI.create(self.test_ns + "test_annotation"))
        new_ap = OWLAnnotationProperty(IRI.create(self.test_ns + "new_ap"))
        av = OWLLiteral("Value of annotation")
        test_iri = IRI.create(self.test_ns + "test_iri")
        a = OWLAnnotation(ap, av)
        aa = OWLAnnotationAssertionAxiom(IRI.create(self.test_ns + "test_annotation_subject"), a)
        new_class = OWLClass(self.test_ns + "new_class")
        new_ind = OWLNamedIndividual(self.test_ns + "new_ind")
        new_dp = OWLDataProperty(self.test_ns + "new_dp")
        new_op = OWLObjectProperty(self.test_ns + "new_op")
        dtr = OWLDatatypeRestriction(DoubleOWLDatatype, OWLFacetRestriction(OWLFacet.MAX_EXCLUSIVE, OWLLiteral(0.1)))
        da = OWLDeclarationAxiom(new_class, [a])
        caa = OWLClassAssertionAxiom(self.i, new_class, [a])
        opaa = OWLObjectPropertyAssertionAxiom(self.i, self.op, new_ind, [a])
        dpaa = OWLDataPropertyAssertionAxiom(self.i, self.dp, OWLLiteral(1), [a])
        ndpaa = OWLNegativeDataPropertyAssertionAxiom(self.i, self.dp, OWLLiteral(1), [a])
        nopaa = OWLNegativeObjectPropertyAssertionAxiom(self.i, self.op, new_ind, [a])
        opda = OWLObjectPropertyDomainAxiom(self.op, OWLThing, [a])
        opra = OWLObjectPropertyRangeAxiom(self.op, OWLThing, [a])
        dpda = OWLDataPropertyDomainAxiom(self.dp, OWLThing, [a])
        dpra = OWLDataPropertyRangeAxiom(self.dp, IntegerOWLDatatype, [a])
        apda = OWLAnnotationPropertyDomainAxiom(ap, test_iri, [a])
        apra = OWLAnnotationPropertyRangeAxiom(ap, test_iri, [a])
        edpa = OWLEquivalentDataPropertiesAxiom([self.dp, new_dp], [a])
        eopa = OWLEquivalentObjectPropertiesAxiom([self.op, new_op], [a])
        dopa = OWLDisjointObjectPropertiesAxiom([self.op, new_op], [a])
        ddpa = OWLDisjointDataPropertiesAxiom([self.dp, new_dp], [a])
        eca = OWLEquivalentClassesAxiom([self.c, new_class], [a])
        dca = OWLDisjointClassesAxiom([self.c, new_class], [a])
        hka = OWLHasKeyAxiom(self.c, [self.op, new_op], [a])
        sca = OWLSubClassOfAxiom(self.c, new_class, [a])
        sdpa = OWLSubDataPropertyOfAxiom(self.dp, new_dp, [a])
        sopa = OWLSubObjectPropertyOfAxiom(self.op, new_op, [a])
        sapa = OWLSubAnnotationPropertyOfAxiom(ap, new_ap, [a])
        aopa = OWLAsymmetricObjectPropertyAxiom(self.op, [a])
        fopa = OWLFunctionalObjectPropertyAxiom(self.op, [a])
        ifopa = OWLInverseFunctionalObjectPropertyAxiom(self.op, [a])
        iopa = OWLIrreflexiveObjectPropertyAxiom(self.op, [a])
        ropa = OWLReflexiveObjectPropertyAxiom(self.op, [a])
        smopa = OWLSymmetricObjectPropertyAxiom(self.op, [a])
        topa = OWLTransitiveObjectPropertyAxiom(self.op, [a])
        fdpa = OWLFunctionalDataPropertyAxiom(self.dp, [a])
        dda = OWLDatatypeDefinitionAxiom(DoubleOWLDatatype, dtr, [a])
        dia = OWLDifferentIndividualsAxiom([self.i, new_ind], [a])
        sia = OWLSameIndividualAxiom([self.i, new_ind], [a])
        dua = OWLDisjointUnionAxiom(self.c, [new_class], [a])
        inopa = OWLInverseObjectPropertiesAxiom(self.op, new_op, [a])

        self.assertEqual(ap, self.mapper.map_(self.mapper.map_(ap)))
        self.assertEqual(av, self.mapper.map_(self.mapper.map_(av)))
        self.assertEqual(a, self.mapper.map_(self.mapper.map_(a)))
        self.assertEqual(aa, self.mapper.map_(self.mapper.map_(aa)))
        self.assertEqual(da, self.mapper.map_(self.mapper.map_(da)))
        self.assertEqual(caa, self.mapper.map_(self.mapper.map_(caa)))
        self.assertEqual(opaa, self.mapper.map_(self.mapper.map_(opaa)))
        self.assertEqual(dpaa, self.mapper.map_(self.mapper.map_(dpaa)))
        self.assertEqual(ndpaa, self.mapper.map_(self.mapper.map_(ndpaa)))
        self.assertEqual(nopaa, self.mapper.map_(self.mapper.map_(nopaa)))
        self.assertEqual(opda, self.mapper.map_(self.mapper.map_(opda)))
        self.assertEqual(opra, self.mapper.map_(self.mapper.map_(opra)))
        self.assertEqual(dpda, self.mapper.map_(self.mapper.map_(dpda)))
        self.assertEqual(dpra, self.mapper.map_(self.mapper.map_(dpra)))
        self.assertEqual(apda, self.mapper.map_(self.mapper.map_(apda)))
        self.assertEqual(apra, self.mapper.map_(self.mapper.map_(apra)))
        self.assertEqual(edpa, self.mapper.map_(self.mapper.map_(edpa)))
        self.assertEqual(eopa, self.mapper.map_(self.mapper.map_(eopa)))
        self.assertEqual(dopa, self.mapper.map_(self.mapper.map_(dopa)))
        self.assertEqual(ddpa, self.mapper.map_(self.mapper.map_(ddpa)))
        self.assertEqual(eca, self.mapper.map_(self.mapper.map_(eca)))
        self.assertEqual(dca, self.mapper.map_(self.mapper.map_(dca)))
        self.assertEqual(hka, self.mapper.map_(self.mapper.map_(hka)))
        self.assertEqual(sca, self.mapper.map_(self.mapper.map_(sca)))
        self.assertEqual(sdpa, self.mapper.map_(self.mapper.map_(sdpa)))
        self.assertEqual(sopa, self.mapper.map_(self.mapper.map_(sopa)))
        self.assertEqual(sapa, self.mapper.map_(self.mapper.map_(sapa)))
        self.assertEqual(aopa, self.mapper.map_(self.mapper.map_(aopa)))
        self.assertEqual(fopa, self.mapper.map_(self.mapper.map_(fopa)))
        self.assertEqual(ifopa, self.mapper.map_(self.mapper.map_(ifopa)))
        self.assertEqual(iopa, self.mapper.map_(self.mapper.map_(iopa)))
        self.assertEqual(ropa, self.mapper.map_(self.mapper.map_(ropa)))
        self.assertEqual(smopa, self.mapper.map_(self.mapper.map_(smopa)))
        self.assertEqual(topa, self.mapper.map_(self.mapper.map_(topa)))
        self.assertEqual(fdpa, self.mapper.map_(self.mapper.map_(fdpa)))
        self.assertEqual(dda, self.mapper.map_(self.mapper.map_(dda)))
        self.assertEqual(dia, self.mapper.map_(self.mapper.map_(dia)))
        self.assertEqual(sia, self.mapper.map_(self.mapper.map_(sia)))
        self.assertEqual(dua, self.mapper.map_(self.mapper.map_(dua)))
        self.assertEqual(inopa, self.mapper.map_(self.mapper.map_(inopa)))
