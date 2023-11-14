#  This file is part of the OWL API.
#  * The contents of this file are subject to the LGPL License, Version 3.0.
#  * Copyright 2014, The University of Manchester
#
# * This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
# later version. * This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details. * You should have received a copy of the GNU General Public License along with this
# program.  If not, see http://www.gnu.org/licenses/.
#
# * Alternatively, the contents of this file may be used under the terms of the Apache License, Version 2.0 in which
# case, the provisions of the Apache License Version 2.0 are applicable instead of those above. * Licensed under the
# Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You
# may obtain a copy of the License at * http://www.apache.org/licenses/LICENSE-2.0 * Unless required by applicable
# law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
#
# package: org.semanticweb.owlapi.api.test.axioms
#
#  * @author Matthew Horridge, The University of Manchester, Information Management Group
#  * @since 3.0.0
#
import unittest

from owlapy.model import OWLObjectProperty, OWLNamedIndividual, OWLObjectComplementOf, \
    OWLObjectAllValuesFrom, OWLObjectSomeValuesFrom, OWLObjectIntersectionOf, OWLObjectUnionOf, \
    OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectHasValue, OWLObjectOneOf, OWLClassExpression, IRI, \
    BooleanOWLDatatype, DoubleOWLDatatype, IntegerOWLDatatype, OWLClass, OWLDataAllValuesFrom, OWLDataComplementOf, \
    OWLDataIntersectionOf, OWLDataProperty, OWLDataSomeValuesFrom, OWLDataUnionOf, \
    OWLDataHasValue, OWLDataMaxCardinality, OWLDataMinCardinality, OWLDataOneOf, OWLLiteral
from owlapy.model.providers import OWLDatatypeMinMaxExclusiveRestriction
from owlapy.util import NNF


def iri(suffix):
    NS = "http://example.org/"
    return IRI.create(NS, suffix)


class Owlapy_NNF_Test(unittest.TestCase):
    """ generated source for class NNFTestCase """
    clsA = OWLClass(iri("A"))
    clsB = OWLClass(iri("B"))
    clsC = OWLClass(iri("C"))
    clsD = OWLClass(iri("D"))
    propP = OWLObjectProperty(iri("p"))
    indA = OWLNamedIndividual(iri("a"))

    def get_nnf(self, ce: OWLClassExpression):
        return NNF().get_class_nnf(ce)

    def testPosOWLClass(self):
        """ generated source for method testPosOWLClass """
        cls = OWLClass(iri("A"))
        self.assertEqual(cls.get_nnf(), cls)

    def testNegOWLClass(self):
        """ generated source for method testNegOWLClass """
        cls = OWLObjectComplementOf(OWLClass(iri("A")))
        self.assertEqual(cls.get_nnf(), cls)

    def testPosAllValuesFrom(self):
        """ generated source for method testPosAllValuesFrom """
        cls = OWLObjectAllValuesFrom(OWLObjectProperty(iri("p")), OWLClass(iri("A")))
        self.assertEqual(cls.get_nnf(), cls)

    def testNegAllValuesFrom(self):
        """ generated source for method testNegAllValuesFrom """
        property = OWLObjectProperty(iri("p"))
        filler = OWLClass(iri("A"))
        all_values_from = OWLObjectAllValuesFrom(property, filler)
        cls = all_values_from.get_object_complement_of()
        nnf = OWLObjectSomeValuesFrom(property, filler.get_object_complement_of())
        self.assertEqual(cls.get_nnf(), nnf)

    def testPosSomeValuesFrom(self):
        """ generated source for method testPosSomeValuesFrom """
        cls = OWLObjectSomeValuesFrom(OWLObjectProperty(iri("p")), OWLClass(iri("A")))
        self.assertEqual(cls.get_nnf(), cls)

    def testNegSomeValuesFrom(self):
        """ generated source for method testNegSomeValuesFrom """
        property = OWLObjectProperty(iri("p"))
        filler = OWLClass(iri("A"))
        some_values_from = OWLObjectSomeValuesFrom(property, filler)
        cls = OWLObjectComplementOf(some_values_from)
        nnf = OWLObjectAllValuesFrom(property, OWLObjectComplementOf(filler))
        self.assertEqual(cls.get_nnf(), nnf)

    def testPosObjectIntersectionOf(self):
        """ generated source for method testPosObjectIntersectionOf """
        cls = OWLObjectIntersectionOf((OWLClass(iri("A")), OWLClass(iri("B")), OWLClass(iri("C"))))
        self.assertEqual(cls.get_nnf(), cls)

    def testNegObjectIntersectionOf(self):
        """ generated source for method testNegObjectIntersectionOf """
        cls = OWLObjectComplementOf(OWLObjectIntersectionOf(
            (OWLClass(iri("A")), OWLClass(iri("B")), OWLClass(iri("C")))))
        nnf = OWLObjectUnionOf(
            (OWLObjectComplementOf(OWLClass(iri("A"))),
             OWLObjectComplementOf(OWLClass(iri("B"))),
             OWLObjectComplementOf(OWLClass(iri("C")))))
        self.assertEqual(cls.get_nnf(), nnf)

    def testPosObjectUnionOf(self):
        """ generated source for method testPosObjectUnionOf """
        cls = OWLObjectUnionOf((OWLClass(iri("A")), OWLClass(iri("B")), OWLClass(iri("C"))))
        self.assertEqual(cls.get_nnf(), cls)

    def testNegObjectUnionOf(self):
        """ generated source for method testNegObjectUnionOf """
        cls = OWLObjectComplementOf(OWLObjectUnionOf((OWLClass(iri("A")), OWLClass(iri("B")), OWLClass(iri("C")))))
        nnf = OWLObjectIntersectionOf(
            (OWLObjectComplementOf(OWLClass(iri("A"))),
             OWLObjectComplementOf(OWLClass(iri("B"))),
             OWLObjectComplementOf(OWLClass(iri("C")))))
        self.assertEqual(cls.get_nnf(), nnf)

    def testPosObjectMinCardinality(self):
        """ generated source for method testPosObjectMinCardinality """
        prop = OWLObjectProperty(iri("p"))
        filler = OWLClass(iri("A"))
        cls = OWLObjectMinCardinality(cardinality=3, property=prop, filler=filler)
        self.assertEqual(cls.get_nnf(), cls)

    def testNegObjectMinCardinality(self):
        """ generated source for method testNegObjectMinCardinality """
        prop = OWLObjectProperty(iri("p"))
        filler = OWLClass(iri("A"))
        cls = OWLObjectMinCardinality(cardinality=3, property=prop, filler=filler).get_object_complement_of()
        nnf = OWLObjectMaxCardinality(cardinality=2, property=prop, filler=filler)
        self.assertEqual(cls.get_nnf(), nnf)

    def testPosObjectMaxCardinality(self):
        """ generated source for method testPosObjectMaxCardinality """
        prop = OWLObjectProperty(iri("p"))
        filler = OWLClass(iri("A"))
        cls = OWLObjectMaxCardinality(cardinality=3, property=prop, filler=filler)
        self.assertEqual(cls.get_nnf(), cls)

    def testNegObjectMaxCardinality(self):
        """ generated source for method testNegObjectMaxCardinality """
        prop = OWLObjectProperty(iri("p"))
        filler = OWLClass(iri("A"))
        cls = OWLObjectMaxCardinality(cardinality=3, property=prop, filler=filler).get_object_complement_of()
        nnf = OWLObjectMinCardinality(cardinality=4, property=prop, filler=filler)
        self.assertEqual(cls.get_nnf(), nnf)

    def testNamedClass(self):
        """ generated source for method testNamedClass """
        desc = self.clsA
        nnf = self.clsA
        comp = self.get_nnf(desc)
        self.assertEqual(nnf, comp)

    def testObjectIntersectionOf(self):
        """ generated source for method testObjectIntersectionOf """
        desc = OWLObjectIntersectionOf((self.clsA, self.clsB))
        neg = OWLObjectComplementOf(desc)
        nnf = OWLObjectUnionOf((OWLObjectComplementOf(self.clsA), OWLObjectComplementOf(self.clsB)))
        comp = self.get_nnf(neg)
        self.assertEqual(nnf, comp)

    def testObjectUnionOf(self):
        """ generated source for method testObjectUnionOf """
        desc = OWLObjectUnionOf((self.clsA, self.clsB))
        neg = OWLObjectComplementOf(desc)
        nnf = OWLObjectIntersectionOf((OWLObjectComplementOf(self.clsA), OWLObjectComplementOf(self.clsB)))
        comp = self.get_nnf(neg)
        self.assertEqual(nnf, comp)

    def testDoubleNegation(self):
        """ generated source for method testDoubleNegation """
        desc = OWLObjectComplementOf(self.clsA)
        neg = OWLObjectComplementOf(desc)
        nnf = self.clsA
        comp = self.get_nnf(neg)
        self.assertEqual(nnf, comp)

    def testTripleNegation(self):
        """ generated source for method testTripleNegation """
        desc = OWLObjectComplementOf(OWLObjectComplementOf(self.clsA))
        neg = OWLObjectComplementOf(desc)
        nnf = OWLObjectComplementOf(self.clsA)
        comp = self.get_nnf(neg)
        self.assertEqual(nnf, comp)

    def testObjectSome(self):
        """ generated source for method testObjectSome """
        desc = OWLObjectSomeValuesFrom(self.propP, self.clsA)
        neg = OWLObjectComplementOf(desc)
        nnf = OWLObjectAllValuesFrom(self.propP, OWLObjectComplementOf(self.clsA))
        comp = self.get_nnf(neg)
        self.assertEqual(nnf, comp)

    def testObjectAll(self):
        """ generated source for method testObjectAll """
        desc = OWLObjectAllValuesFrom(self.propP, self.clsA)
        neg = OWLObjectComplementOf(desc)
        nnf = OWLObjectSomeValuesFrom(self.propP, OWLObjectComplementOf(self.clsA))
        comp = self.get_nnf(neg)
        self.assertEqual(nnf, comp)

    def testObjectHasValue(self):
        """ generated source for method testObjectHasValue """
        desc = OWLObjectHasValue(self.propP, self.indA)
        neg = OWLObjectComplementOf(desc)
        nnf = OWLObjectAllValuesFrom(self.propP, OWLObjectComplementOf(OWLObjectOneOf(self.indA)))
        comp = self.get_nnf(neg)
        self.assertEqual(nnf, comp)

    def testObjectMin(self):
        """ generated source for method testObjectMin """
        desc = OWLObjectMinCardinality(cardinality=3, property=self.propP, filler=self.clsA)
        neg = OWLObjectComplementOf(desc)
        nnf = OWLObjectMaxCardinality(cardinality=2, property=self.propP, filler=self.clsA)
        comp = self.get_nnf(neg)
        self.assertEqual(nnf, comp)

    def testObjectMax(self):
        """ generated source for method testObjectMax """
        desc = OWLObjectMaxCardinality(cardinality=3, property=self.propP, filler=self.clsA)
        neg = OWLObjectComplementOf(desc)
        nnf = OWLObjectMinCardinality(cardinality=4, property=self.propP, filler=self.clsA)
        comp = self.get_nnf(neg)
        self.assertEqual(nnf, comp)

    def testNestedA(self):
        """ generated source for method testNestedA """
        filler_a = OWLObjectUnionOf((self.clsA, self.clsB))
        op_a = OWLObjectSomeValuesFrom(self.propP, filler_a)
        op_b = self.clsB
        desc = OWLObjectUnionOf((op_a, op_b))
        nnf = OWLObjectIntersectionOf(
            (OWLObjectComplementOf(self.clsB),
             OWLObjectAllValuesFrom(self.propP,
                                    OWLObjectIntersectionOf((OWLObjectComplementOf(self.clsA),
                                                             OWLObjectComplementOf(self.clsB))))))
        neg = OWLObjectComplementOf(desc)
        comp = self.get_nnf(neg)
        self.assertEqual(comp, nnf)

    def testNestedB(self):
        """ generated source for method testNestedB """
        desc = OWLObjectIntersectionOf(
            (OWLObjectIntersectionOf((self.clsA, self.clsB)),
             OWLObjectComplementOf(OWLObjectUnionOf((self.clsC, self.clsD)))))
        neg = OWLObjectComplementOf(desc)
        nnf = OWLObjectUnionOf(
            (OWLObjectUnionOf((OWLObjectComplementOf(self.clsA),
                               OWLObjectComplementOf(self.clsB))),
             OWLObjectUnionOf((self.clsC, self.clsD))))
        comp = self.get_nnf(neg)
        self.assertEqual(comp, nnf)

    def testPosDataAllValuesFrom(self):
        cls = OWLDataAllValuesFrom(OWLDataProperty(iri("p")), IntegerOWLDatatype)
        self.assertEqual(cls.get_nnf(), cls)

    def testNegDataAllValuesFrom(self):
        property = OWLDataProperty(iri("p"))
        all_values_from = OWLDataAllValuesFrom(property, IntegerOWLDatatype)
        cls = all_values_from.get_object_complement_of()
        nnf = OWLDataSomeValuesFrom(property, OWLDataComplementOf(IntegerOWLDatatype))
        self.assertEqual(cls.get_nnf(), nnf)

    def testPosDataSomeValuesFrom(self):
        cls = OWLDataSomeValuesFrom(OWLDataProperty(iri("p")), IntegerOWLDatatype)
        self.assertEqual(cls.get_nnf(), cls)

    def testNegDataSomeValuesFrom(self):
        property = OWLDataProperty(iri("p"))
        some_values_from = OWLDataSomeValuesFrom(property, IntegerOWLDatatype)
        cls = OWLDataComplementOf(some_values_from)
        nnf = OWLDataAllValuesFrom(property, OWLDataComplementOf(IntegerOWLDatatype))
        self.assertEqual(self.get_nnf(cls), nnf)

    def testPosDataIntersectionOf(self):
        cls = OWLDataIntersectionOf((BooleanOWLDatatype, DoubleOWLDatatype, IntegerOWLDatatype))
        self.assertEqual(self.get_nnf(cls), cls)

    def testNegDataIntersectionOf(self):
        cls = OWLDataComplementOf(OWLDataIntersectionOf(
            (BooleanOWLDatatype, DoubleOWLDatatype, IntegerOWLDatatype)))
        nnf = OWLDataUnionOf(
            (OWLDataComplementOf(BooleanOWLDatatype),
             OWLDataComplementOf(DoubleOWLDatatype),
             OWLDataComplementOf(IntegerOWLDatatype)))
        self.assertEqual(self.get_nnf(cls), nnf)

    def testPosDataUnionOf(self):
        cls = OWLDataUnionOf((BooleanOWLDatatype, DoubleOWLDatatype, IntegerOWLDatatype))
        self.assertEqual(self.get_nnf(cls), cls)

    def testNegDataUnionOf(self):
        cls = OWLDataComplementOf(OWLDataUnionOf((BooleanOWLDatatype, DoubleOWLDatatype, IntegerOWLDatatype)))
        nnf = OWLDataIntersectionOf(
            (OWLDataComplementOf(BooleanOWLDatatype),
             OWLDataComplementOf(DoubleOWLDatatype),
             OWLDataComplementOf(IntegerOWLDatatype)))
        self.assertEqual(self.get_nnf(cls), nnf)

    def testPosDataMinCardinality(self):
        prop = OWLDataProperty(iri("p"))
        cls = OWLDataMinCardinality(cardinality=3, property=prop, filler=IntegerOWLDatatype)
        self.assertEqual(cls.get_nnf(), cls)

    def testNegDataMinCardinality(self):
        prop = OWLDataProperty(iri("p"))
        filler = IntegerOWLDatatype
        cls = OWLDataMinCardinality(cardinality=3, property=prop, filler=filler).get_object_complement_of()
        nnf = OWLDataMaxCardinality(cardinality=2, property=prop, filler=filler)
        self.assertEqual(cls.get_nnf(), nnf)

    def testPosDataMaxCardinality(self):
        prop = OWLDataProperty(iri("p"))
        cls = OWLDataMaxCardinality(cardinality=3, property=prop, filler=IntegerOWLDatatype)
        self.assertEqual(cls.get_nnf(), cls)

    def testNegDataMaxCardinality(self):
        prop = OWLDataProperty(iri("p"))
        filler = IntegerOWLDatatype
        cls = OWLDataMaxCardinality(cardinality=3, property=prop, filler=filler).get_object_complement_of()
        nnf = OWLDataMinCardinality(cardinality=4, property=prop, filler=filler)
        self.assertEqual(cls.get_nnf(), nnf)

    def testDatatype(self):
        desc = IntegerOWLDatatype
        nnf = IntegerOWLDatatype
        comp = self.get_nnf(desc)
        self.assertEqual(nnf, comp)

    def testDataDoubleNegation(self):
        desc = OWLDataComplementOf(IntegerOWLDatatype)
        neg = OWLDataComplementOf(desc)
        nnf = IntegerOWLDatatype
        comp = self.get_nnf(neg)
        self.assertEqual(nnf, comp)

    def testDataTripleNegation(self):
        desc = OWLDataComplementOf(OWLDataComplementOf(IntegerOWLDatatype))
        neg = OWLDataComplementOf(desc)
        nnf = OWLDataComplementOf(IntegerOWLDatatype)
        comp = self.get_nnf(neg)
        self.assertEqual(nnf, comp)

    def testDataHasValue(self):
        prop = OWLDataProperty(iri("p"))
        literal = OWLLiteral(5)
        desc = OWLDataHasValue(prop, literal)
        neg = OWLDataComplementOf(desc)
        nnf = OWLDataAllValuesFrom(prop, OWLDataComplementOf(OWLDataOneOf(literal)))
        comp = self.get_nnf(neg)
        self.assertEqual(nnf, comp)

    def testDataNestedA(self):
        restriction = OWLDatatypeMinMaxExclusiveRestriction(5, 6)
        prop = OWLDataProperty(iri("p"))
        filler_a = OWLDataUnionOf((IntegerOWLDatatype, DoubleOWLDatatype))
        op_a = OWLDataSomeValuesFrom(prop, filler_a)
        op_b = OWLDataIntersectionOf((restriction, IntegerOWLDatatype))
        desc = OWLDataUnionOf((op_a, op_b))
        nnf = OWLDataIntersectionOf(
                (OWLDataAllValuesFrom(prop, OWLDataIntersectionOf((OWLDataComplementOf(DoubleOWLDatatype),
                                                                   OWLDataComplementOf(IntegerOWLDatatype)))),
                 OWLDataUnionOf((OWLDataComplementOf(IntegerOWLDatatype), OWLDataComplementOf(restriction)))))
        neg = OWLDataComplementOf(desc)
        comp = self.get_nnf(neg)
        self.assertEqual(comp, nnf)

    def testDataNestedB(self):
        desc = OWLDataIntersectionOf(
            (OWLDataIntersectionOf((IntegerOWLDatatype, DoubleOWLDatatype)),
             OWLDataComplementOf(OWLDataUnionOf((BooleanOWLDatatype, OWLDataOneOf(OWLLiteral(True)))))))
        neg = OWLDataComplementOf(desc)
        nnf = OWLDataUnionOf(
            (OWLDataUnionOf((BooleanOWLDatatype, OWLDataOneOf(OWLLiteral(True)))),
             OWLDataUnionOf((OWLDataComplementOf(DoubleOWLDatatype),
                             OWLDataComplementOf(IntegerOWLDatatype)))))
        comp = self.get_nnf(neg)
        self.assertEqual(comp, nnf)
