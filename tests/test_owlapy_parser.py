import unittest
from datetime import date, datetime, timedelta, timezone

from pandas import Timedelta
from owlapy.model import OWLObjectInverseOf, OWLObjectMinCardinality, OWLObjectSomeValuesFrom, \
    OWLObjectUnionOf, DoubleOWLDatatype, IntegerOWLDatatype, OWLClass, IRI, OWLDataAllValuesFrom, \
    OWLDataIntersectionOf, OWLDataOneOf, OWLDataProperty, OWLDataSomeValuesFrom, OWLDatatypeRestriction,  \
    OWLLiteral, OWLNamedIndividual, OWLObjectAllValuesFrom, OWLObjectComplementOf, OWLObjectExactCardinality, \
    OWLObjectHasSelf, OWLObjectHasValue, OWLObjectIntersectionOf, OWLObjectMaxCardinality, OWLObjectOneOf, \
    OWLObjectProperty, OWLDataComplementOf, OWLDataExactCardinality, OWLDataMaxCardinality, OWLDataUnionOf, \
    OWLDataMinCardinality, OWLDataHasValue, OWLThing, OWLNothing, OWLFacetRestriction

from owlapy.model.providers import OWLDatatypeMinExclusiveRestriction,\
    OWLDatatypeMinMaxExclusiveRestriction, OWLDatatypeMaxExclusiveRestriction
from owlapy.parser import DLSyntaxParser, ManchesterOWLSyntaxParser
from owlapy.vocab import OWLFacet


class ManchesterOWLSyntaxParserTest(unittest.TestCase):

    def setUp(self):
        self.namespace = "http://dl-learner.org/mutagenesis#"
        self.parser = ManchesterOWLSyntaxParser(self.namespace)

        # Classes
        self.atom = OWLClass(IRI(self.namespace, 'Atom'))
        self.bond = OWLClass(IRI(self.namespace, 'Bond'))
        self.compound = OWLClass(IRI(self.namespace, 'Compound'))

        # Object Properties
        self.in_bond = OWLObjectProperty(IRI.create(self.namespace, 'inBond'))
        self.has_bond = OWLObjectProperty(IRI.create(self.namespace, 'hasBond'))

        # Data Properties
        self.charge = OWLDataProperty(IRI.create(self.namespace, 'charge'))
        self.act = OWLDataProperty(IRI.create(self.namespace, 'act'))
        self.has_fife_examples = OWLDataProperty(IRI.create(self.namespace, 'hasFifeExamplesOfAcenthrylenes'))

        # Individuals
        self.bond5225 = OWLNamedIndividual(IRI.create(self.namespace, 'bond5225'))
        self.d91_17 = OWLNamedIndividual(IRI.create(self.namespace, 'd91_17'))
        self.d91_32 = OWLNamedIndividual(IRI.create(self.namespace, 'd91_32'))

    def test_union_intersection(self):
        p = self.parser.parse_expression('Atom or Bond and Compound')
        c = OWLObjectUnionOf((self.atom, OWLObjectIntersectionOf((self.bond, self.compound))))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('(Atom or Bond) and Compound')
        c = OWLObjectIntersectionOf((OWLObjectUnionOf((self.atom, self.bond)), self.compound))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('((Atom or Bond) and Atom) and Compound or Bond')
        c = OWLObjectUnionOf((OWLObjectIntersectionOf((OWLObjectIntersectionOf((
                                                            OWLObjectUnionOf((self.atom, self.bond)),
                                                            self.atom)),
                                                       self.compound)),
                              self.bond))
        self.assertEqual(p, c)

    def test_thing_nothing(self):
        p = self.parser.parse_expression('(hasBond some (Thing and Nothing)) and Nothing or Thing')
        c = OWLObjectUnionOf((
                OWLObjectIntersectionOf((
                    OWLObjectSomeValuesFrom(self.has_bond, OWLObjectIntersectionOf((OWLThing, OWLNothing))),
                    OWLNothing)),
                OWLThing))
        self.assertEqual(p, c)

    def test_object_properties(self):
        p = self.parser.parse_expression('inBond some Bond')
        c = OWLObjectSomeValuesFrom(self.in_bond, self.bond)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('hasBond only Atom')
        c = OWLObjectAllValuesFrom(self.has_bond, self.atom)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('inBond some (hasBond some (Bond and Atom))')
        c = OWLObjectSomeValuesFrom(self.in_bond,
                                    OWLObjectSomeValuesFrom(self.has_bond,
                                                            OWLObjectIntersectionOf((self.bond, self.atom))))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('inBond max 5 Bond')
        c = OWLObjectMaxCardinality(5, self.in_bond, self.bond)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('inBond min 124 Atom')
        c = OWLObjectMinCardinality(124, self.in_bond, self.atom)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('inBond exactly 11 Bond')
        c = OWLObjectExactCardinality(11, self.in_bond, self.bond)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('inBond value d91_32')
        c = OWLObjectHasValue(self.in_bond, self.d91_32)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('inBond Self')
        c = OWLObjectHasSelf(self.in_bond)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('inverse inBond some Atom')
        c = OWLObjectSomeValuesFrom(OWLObjectInverseOf(self.in_bond), self.atom)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('hasBond only {d91_32, d91_17, bond5225}')
        c = OWLObjectAllValuesFrom(self.has_bond, OWLObjectOneOf((self.d91_32, self.d91_17, self.bond5225)))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('(not (Atom or Bond) and Atom) and not Compound '
                                         'or (hasBond some (inBond max 4 Bond))')
        c1 = OWLObjectIntersectionOf((OWLObjectComplementOf(OWLObjectUnionOf((self.atom, self.bond))), self.atom))
        c2 = OWLObjectIntersectionOf((c1, OWLObjectComplementOf(self.compound)))
        c3 = OWLObjectSomeValuesFrom(self.has_bond, OWLObjectMaxCardinality(4, self.in_bond, self.bond))
        c = OWLObjectUnionOf((c2, c3))
        self.assertEqual(p, c)

    def test_data_properties_numeric(self):
        p = self.parser.parse_expression('charge some xsd:integer[> 4]')
        c = OWLDataSomeValuesFrom(self.charge, OWLDatatypeMinExclusiveRestriction(4))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('act only double')
        c = OWLDataAllValuesFrom(self.act, DoubleOWLDatatype)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('charge some <http://www.w3.org/2001/XMLSchema#double>'
                                         '[> "4.4"^^xsd:double, < -32.5]')
        c = OWLDataSomeValuesFrom(self.charge, OWLDatatypeMinMaxExclusiveRestriction(4.4, -32.5))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('charge max 4 not (integer[> +4] and integer or xsd:integer[< "1"^^integer])')
        filler1 = OWLDataIntersectionOf((OWLDatatypeMinExclusiveRestriction(4), IntegerOWLDatatype))
        filler = OWLDataComplementOf(OWLDataUnionOf((filler1, OWLDatatypeMaxExclusiveRestriction(1))))
        c = OWLDataMaxCardinality(4, self.charge, filler)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('charge min 25 (not (xsd:integer[> 9] and '
                                         '(xsd:integer or not xsd:integer[< "6"^^integer])))')
        filler1 = OWLDataUnionOf((IntegerOWLDatatype, OWLDataComplementOf(OWLDatatypeMaxExclusiveRestriction(6))))
        filler = OWLDataComplementOf(OWLDataIntersectionOf((OWLDatatypeMinExclusiveRestriction(9), filler1)))
        c = OWLDataMinCardinality(25, self.charge, filler)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('act exactly 11 xsd:integer[totalDigits "5"^^xsd:integer, > -100]')
        filler = OWLDatatypeRestriction(IntegerOWLDatatype, (OWLFacetRestriction(OWLFacet.TOTAL_DIGITS, 5),
                                                             OWLFacetRestriction(OWLFacet.MIN_EXCLUSIVE, -100)))
        c = OWLDataExactCardinality(11, self.act, filler)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('charge value -11.1e100f')
        c = OWLDataHasValue(self.charge, OWLLiteral(-11.1e100))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('charge only {.10e-001F, 1.1e0010f, 10f, 5}')
        filler = OWLDataOneOf((OWLLiteral(0.10e-001), OWLLiteral(1.1e0010), OWLLiteral(10.0), OWLLiteral(5)))
        c = OWLDataAllValuesFrom(self.charge, filler)
        self.assertEqual(p, c)

    def test_data_properties_boolean(self):
        p = self.parser.parse_expression('hasFifeExamplesOfAcenthrylenes value "true"^^boolean')
        c = OWLDataHasValue(self.has_fife_examples, OWLLiteral(True))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('hasFifeExamplesOfAcenthrylenes value false')
        c = OWLDataHasValue(self.has_fife_examples, OWLLiteral(False))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('hasFifeExamplesOfAcenthrylenes some {true, false, "false"^^xsd:boolean}')
        filler = OWLDataOneOf((OWLLiteral(True), OWLLiteral(False), OWLLiteral(False)))
        c = OWLDataSomeValuesFrom(self.has_fife_examples, filler)
        self.assertEqual(p, c)

    def test_data_properties_string(self):
        p = self.parser.parse_expression('charge value "Test123"^^xsd:string')
        c = OWLDataHasValue(self.charge, OWLLiteral("Test123"))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('charge value "Test\\"123456"')
        c = OWLDataHasValue(self.charge, OWLLiteral("Test\\\"123456"))
        self.assertEqual(p, c)

    def test_data_properties_time(self):
        p = self.parser.parse_expression('charge some <http://www.w3.org/2001/XMLSchema#date>'
                                         '[> 2012-10-09, < "1990-01-31"^^xsd:date]')
        filler = OWLDatatypeMinMaxExclusiveRestriction(date(year=2012, month=10, day=9),
                                                       date(year=1990, month=1, day=31))
        c = OWLDataSomeValuesFrom(self.charge, filler)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('charge exactly 10 dateTime'
                                         '[> 2012-12-31T23:59:59Z, < 2000-01-01 01:01:01.999999]')
        filler = OWLDatatypeMinMaxExclusiveRestriction(datetime(year=2012, month=12, day=31, hour=23,
                                                                minute=59, second=59, tzinfo=timezone.utc),
                                                       datetime(year=2000, month=1, day=1, hour=1, minute=1,
                                                                second=1, microsecond=999999))
        c = OWLDataExactCardinality(10, self.charge, filler)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('charge value "2000-01-01T01:01:01.000001+04:00:59.999899"^^xsd:dateTime')
        literal = OWLLiteral(datetime(year=2000, month=1, day=1, hour=1, minute=1, second=1, microsecond=1,
                                      tzinfo=timezone(timedelta(hours=4, seconds=59, microseconds=999899))))
        c = OWLDataHasValue(self.charge, literal)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('charge only <http://www.w3.org/2001/XMLSchema#duration>'
                                         '[> P10W20DT8H12M10S, < "P10M10.999999S"^^xsd:duration]')
        filler = OWLDatatypeMinMaxExclusiveRestriction(Timedelta(weeks=10, days=20, hours=8, minutes=12, seconds=10),
                                                       Timedelta(minutes=10, seconds=10, microseconds=999999))
        c = OWLDataAllValuesFrom(self.charge, filler)
        self.assertEqual(p, c)

    def test_full_iri(self):
        p = self.parser.parse_expression('<http://dl-learner.org/mutagenesis#hasBond> only '
                                         '<http://dl-learner.org/mutagenesis#Atom>')
        c = OWLObjectAllValuesFrom(self.has_bond, self.atom)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('<http://dl-learner.org/mutagenesis#inBond> some '
                                         '(<http://dl-learner.org/mutagenesis#hasBond> some '
                                         '(<http://dl-learner.org/mutagenesis#Bond> and '
                                         '<http://dl-learner.org/mutagenesis#Atom>))')
        c = OWLObjectSomeValuesFrom(self.in_bond,
                                    OWLObjectSomeValuesFrom(self.has_bond,
                                                            OWLObjectIntersectionOf((self.bond, self.atom))))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('<http://dl-learner.org/mutagenesis#charge> value '
                                         '"Test123"^^<http://www.w3.org/2001/XMLSchema#string>')
        c = OWLDataHasValue(self.charge, OWLLiteral("Test123"))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('<http://dl-learner.org/mutagenesis#charge> max 4 not '
                                         '(<http://www.w3.org/2001/XMLSchema#integer>[> +4] and '
                                         '<http://www.w3.org/2001/XMLSchema#integer> or '
                                         '<http://www.w3.org/2001/XMLSchema#integer>[< '
                                         '"1"^^<http://www.w3.org/2001/XMLSchema#integer>])')
        filler1 = OWLDataIntersectionOf((OWLDatatypeMinExclusiveRestriction(4), IntegerOWLDatatype))
        filler = OWLDataComplementOf(OWLDataUnionOf((filler1, OWLDatatypeMaxExclusiveRestriction(1))))
        c = OWLDataMaxCardinality(4, self.charge, filler)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('<http://dl-learner.org/mutagenesis#hasBond> only '
                                         '{<http://dl-learner.org/mutagenesis#d91_32>, '
                                         '<http://dl-learner.org/mutagenesis#d91_17>, '
                                         '<http://dl-learner.org/mutagenesis#bond5225>}')
        c = OWLObjectAllValuesFrom(self.has_bond, OWLObjectOneOf((self.d91_32, self.d91_17, self.bond5225)))
        self.assertEqual(p, c)

    def test_whitespace(self):
        p = self.parser.parse_expression('    inBond   some    Bond')
        c = OWLObjectSomeValuesFrom(self.in_bond, self.bond)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('( \n Atom or Bond\t)  and\nCompound  ')
        c = OWLObjectIntersectionOf((OWLObjectUnionOf((self.atom, self.bond)), self.compound))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('hasBond only { \n\t d91_32,d91_17  ,    bond5225  }')
        c = OWLObjectAllValuesFrom(self.has_bond, OWLObjectOneOf((self.d91_32, self.d91_17, self.bond5225)))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('act only { \n\t 1.2f  ,    3.2f  }')
        c = OWLDataAllValuesFrom(self.act, OWLDataOneOf((OWLLiteral(1.2), OWLLiteral(3.2))))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('act some (  xsd:double[  > 5f,< 4.2f \n, <  -1.8e10f  ]\t and  integer )')
        f1 = OWLFacetRestriction(OWLFacet.MIN_EXCLUSIVE, OWLLiteral(5.0))
        f2 = OWLFacetRestriction(OWLFacet.MAX_EXCLUSIVE, OWLLiteral(4.2))
        f3 = OWLFacetRestriction(OWLFacet.MAX_EXCLUSIVE, OWLLiteral(-1.8e10))
        c = OWLDataSomeValuesFrom(self.act, OWLDataIntersectionOf(
                                    (OWLDatatypeRestriction(DoubleOWLDatatype, (f1, f2, f3)), IntegerOWLDatatype)))
        self.assertEqual(p, c)


class DLSyntaxParserTest(unittest.TestCase):

    def setUp(self):
        self.namespace = "http://dl-learner.org/mutagenesis#"
        self.parser = DLSyntaxParser(self.namespace)

        # Classes
        self.atom = OWLClass(IRI(self.namespace, 'Atom'))
        self.bond = OWLClass(IRI(self.namespace, 'Bond'))
        self.compound = OWLClass(IRI(self.namespace, 'Compound'))

        # Object Properties
        self.in_bond = OWLObjectProperty(IRI.create(self.namespace, 'inBond'))
        self.has_bond = OWLObjectProperty(IRI.create(self.namespace, 'hasBond'))

        # Data Properties
        self.charge = OWLDataProperty(IRI.create(self.namespace, 'charge'))
        self.act = OWLDataProperty(IRI.create(self.namespace, 'act'))
        self.has_fife_examples = OWLDataProperty(IRI.create(self.namespace, 'hasFifeExamplesOfAcenthrylenes'))

        # Individuals
        self.bond5225 = OWLNamedIndividual(IRI.create(self.namespace, 'bond5225'))
        self.d91_17 = OWLNamedIndividual(IRI.create(self.namespace, 'd91_17'))
        self.d91_32 = OWLNamedIndividual(IRI.create(self.namespace, 'd91_32'))

    def test_union_intersection(self):
        p = self.parser.parse_expression('Atom ⊔ Bond ⊓ Compound')
        c = OWLObjectUnionOf((self.atom, OWLObjectIntersectionOf((self.bond, self.compound))))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('(Atom ⊔ Bond) ⊓ Compound')
        c = OWLObjectIntersectionOf((OWLObjectUnionOf((self.atom, self.bond)), self.compound))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('((Atom ⊔ Bond) ⊓ Atom) ⊓ Compound ⊔ Bond')
        c = OWLObjectUnionOf((OWLObjectIntersectionOf((OWLObjectIntersectionOf((
                                                            OWLObjectUnionOf((self.atom, self.bond)),
                                                            self.atom)),
                                                       self.compound)),
                              self.bond))
        self.assertEqual(p, c)

    def test_top_bottom(self):
        p = self.parser.parse_expression('(∃ hasBond.(⊤ ⊓ ⊥)) ⊓ ⊥ ⊔ ⊤')
        c = OWLObjectUnionOf((
                OWLObjectIntersectionOf((
                    OWLObjectSomeValuesFrom(self.has_bond, OWLObjectIntersectionOf((OWLThing, OWLNothing))),
                    OWLNothing)),
                OWLThing))
        self.assertEqual(p, c)

    def test_object_properties(self):
        p = self.parser.parse_expression('∃ inBond.Bond')
        c = OWLObjectSomeValuesFrom(self.in_bond, self.bond)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∀ hasBond.Atom')
        c = OWLObjectAllValuesFrom(self.has_bond, self.atom)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∃ inBond.(∃ hasBond.(Bond ⊓ Atom))')
        c = OWLObjectSomeValuesFrom(self.in_bond,
                                    OWLObjectSomeValuesFrom(self.has_bond,
                                                            OWLObjectIntersectionOf((self.bond, self.atom))))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('≤ 5 inBond.Bond')
        c = OWLObjectMaxCardinality(5, self.in_bond, self.bond)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('≤ 124 inBond.Atom')
        c = OWLObjectMaxCardinality(124, self.in_bond, self.atom)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('= 11 inBond.Bond')
        c = OWLObjectExactCardinality(11, self.in_bond, self.bond)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∃ inBond.{d91_32}')
        c = OWLObjectHasValue(self.in_bond, self.d91_32)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∃ inBond.Self')
        c = OWLObjectHasSelf(self.in_bond)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∃ inBond⁻.Atom')
        c = OWLObjectSomeValuesFrom(OWLObjectInverseOf(self.in_bond), self.atom)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∀ hasBond.{d91_32 ⊔ d91_17 ⊔ bond5225}')
        c = OWLObjectAllValuesFrom(self.has_bond, OWLObjectOneOf((self.d91_32, self.d91_17, self.bond5225)))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('(¬ (Atom ⊔ Bond) ⊓ Atom) ⊓ ¬Compound '
                                         '⊔ (∃ hasBond.(≤ 4 inBond.Bond))')
        c1 = OWLObjectIntersectionOf((OWLObjectComplementOf(OWLObjectUnionOf((self.atom, self.bond))), self.atom))
        c2 = OWLObjectIntersectionOf((c1, OWLObjectComplementOf(self.compound)))
        c3 = OWLObjectSomeValuesFrom(self.has_bond, OWLObjectMaxCardinality(4, self.in_bond, self.bond))
        c = OWLObjectUnionOf((c2, c3))
        self.assertEqual(p, c)

    def test_data_properties_numeric(self):
        p = self.parser.parse_expression('∃ charge.(xsd:integer[> 4])')
        c = OWLDataSomeValuesFrom(self.charge, OWLDatatypeMinExclusiveRestriction(4))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∀ act.double')
        c = OWLDataAllValuesFrom(self.act, DoubleOWLDatatype)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∃ charge.<http://www.w3.org/2001/XMLSchema#double>'
                                         '[> "4.4"^^xsd:double, < -32.5]')
        c = OWLDataSomeValuesFrom(self.charge, OWLDatatypeMinMaxExclusiveRestriction(4.4, -32.5))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('≤ 4 charge.(¬(integer[> +4] ⊓ integer ⊔ xsd:integer[< "1"^^integer]))')
        filler1 = OWLDataIntersectionOf((OWLDatatypeMinExclusiveRestriction(4), IntegerOWLDatatype))
        filler = OWLDataComplementOf(OWLDataUnionOf((filler1, OWLDatatypeMaxExclusiveRestriction(1))))
        c = OWLDataMaxCardinality(4, self.charge, filler)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('≤ 25 charge.(¬(xsd:integer[> 9] ⊓ '
                                         '(xsd:integer ⊔ ¬xsd:integer[< "6"^^integer])))')
        filler1 = OWLDataUnionOf((IntegerOWLDatatype, OWLDataComplementOf(OWLDatatypeMaxExclusiveRestriction(6))))
        filler = OWLDataComplementOf(OWLDataIntersectionOf((OWLDatatypeMinExclusiveRestriction(9), filler1)))
        c = OWLDataMaxCardinality(25, self.charge, filler)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('= 11 act.xsd:integer[totalDigits "5"^^xsd:integer, > -100]')
        filler = OWLDatatypeRestriction(IntegerOWLDatatype, (OWLFacetRestriction(OWLFacet.TOTAL_DIGITS, 5),
                                                             OWLFacetRestriction(OWLFacet.MIN_EXCLUSIVE, -100)))
        c = OWLDataExactCardinality(11, self.act, filler)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∃ charge.{-11.1e100f}')
        c = OWLDataHasValue(self.charge, OWLLiteral(-11.1e100))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∀ charge.{.10e-001F ⊔ 1.1e0010f ⊔ 10f ⊔ 5}')
        filler = OWLDataOneOf((OWLLiteral(0.10e-001), OWLLiteral(1.1e0010), OWLLiteral(10.0), OWLLiteral(5)))
        c = OWLDataAllValuesFrom(self.charge, filler)
        self.assertEqual(p, c)

    def test_data_properties_boolean(self):
        p = self.parser.parse_expression('∃ hasFifeExamplesOfAcenthrylenes.{"true"^^boolean}')
        c = OWLDataHasValue(self.has_fife_examples, OWLLiteral(True))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∃ hasFifeExamplesOfAcenthrylenes.{false}')
        c = OWLDataHasValue(self.has_fife_examples, OWLLiteral(False))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∃ hasFifeExamplesOfAcenthrylenes.{true ⊔ false ⊔ "false"^^xsd:boolean}')
        filler = OWLDataOneOf((OWLLiteral(True), OWLLiteral(False), OWLLiteral(False)))
        c = OWLDataSomeValuesFrom(self.has_fife_examples, filler)
        self.assertEqual(p, c)

    def test_data_properties_string(self):
        p = self.parser.parse_expression('∃ charge.{"Test123"^^xsd:string}')
        c = OWLDataHasValue(self.charge, OWLLiteral("Test123"))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∃ charge.{"Test\\"123456"}')
        c = OWLDataHasValue(self.charge, OWLLiteral("Test\\\"123456"))
        self.assertEqual(p, c)

    def test_data_properties_time(self):
        p = self.parser.parse_expression('∃ charge.<http://www.w3.org/2001/XMLSchema#date>'
                                         '[> 2012-10-09, < "1990-01-31"^^xsd:date]')
        filler = OWLDatatypeMinMaxExclusiveRestriction(date(year=2012, month=10, day=9),
                                                       date(year=1990, month=1, day=31))
        c = OWLDataSomeValuesFrom(self.charge, filler)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('= 10 charge.dateTime'
                                         '[> 2012-12-31T23:59:59Z, < 2000-01-01 01:01:01.999999]')
        filler = OWLDatatypeMinMaxExclusiveRestriction(datetime(year=2012, month=12, day=31, hour=23,
                                                                minute=59, second=59, tzinfo=timezone.utc),
                                                       datetime(year=2000, month=1, day=1, hour=1, minute=1,
                                                                second=1, microsecond=999999))
        c = OWLDataExactCardinality(10, self.charge, filler)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∃ charge.{"2000-01-01T01:01:01.000001+04:00:59.999899"^^xsd:dateTime}')
        literal = OWLLiteral(datetime(year=2000, month=1, day=1, hour=1, minute=1, second=1, microsecond=1,
                                      tzinfo=timezone(timedelta(hours=4, seconds=59, microseconds=999899))))
        c = OWLDataHasValue(self.charge, literal)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∀ charge.<http://www.w3.org/2001/XMLSchema#duration>'
                                         '[> P10W20DT8H12M10S, < "P10M10.999999S"^^xsd:duration]')
        filler = OWLDatatypeMinMaxExclusiveRestriction(Timedelta(weeks=10, days=20, hours=8, minutes=12, seconds=10),
                                                       Timedelta(minutes=10, seconds=10, microseconds=999999))
        c = OWLDataAllValuesFrom(self.charge, filler)
        self.assertEqual(p, c)

    def test_full_iri(self):
        p = self.parser.parse_expression('∀ <http://dl-learner.org/mutagenesis#hasBond>.'
                                         '<http://dl-learner.org/mutagenesis#Atom>')
        c = OWLObjectAllValuesFrom(self.has_bond, self.atom)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∃ <http://dl-learner.org/mutagenesis#inBond>.'
                                         '(∃ <http://dl-learner.org/mutagenesis#hasBond>.'
                                         '(<http://dl-learner.org/mutagenesis#Bond> ⊓ '
                                         '<http://dl-learner.org/mutagenesis#Atom>))')
        c = OWLObjectSomeValuesFrom(self.in_bond,
                                    OWLObjectSomeValuesFrom(self.has_bond,
                                                            OWLObjectIntersectionOf((self.bond, self.atom))))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∃ <http://dl-learner.org/mutagenesis#charge>.{'
                                         '"Test123"^^<http://www.w3.org/2001/XMLSchema#string>}')
        c = OWLDataHasValue(self.charge, OWLLiteral("Test123"))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('≤ 4 <http://dl-learner.org/mutagenesis#charge>.¬'
                                         '(<http://www.w3.org/2001/XMLSchema#integer>[> +4] ⊓ '
                                         '<http://www.w3.org/2001/XMLSchema#integer> ⊔ '
                                         '<http://www.w3.org/2001/XMLSchema#integer>[< '
                                         '"1"^^<http://www.w3.org/2001/XMLSchema#integer>])')
        filler1 = OWLDataIntersectionOf((OWLDatatypeMinExclusiveRestriction(4), IntegerOWLDatatype))
        filler = OWLDataComplementOf(OWLDataUnionOf((filler1, OWLDatatypeMaxExclusiveRestriction(1))))
        c = OWLDataMaxCardinality(4, self.charge, filler)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∀ <http://dl-learner.org/mutagenesis#hasBond>.'
                                         '{<http://dl-learner.org/mutagenesis#d91_32> ⊔ '
                                         '<http://dl-learner.org/mutagenesis#d91_17> ⊔ '
                                         '<http://dl-learner.org/mutagenesis#bond5225>}')
        c = OWLObjectAllValuesFrom(self.has_bond, OWLObjectOneOf((self.d91_32, self.d91_17, self.bond5225)))
        self.assertEqual(p, c)

    def test_whitespace(self):
        p = self.parser.parse_expression('∃     inBond.Bond')
        c = OWLObjectSomeValuesFrom(self.in_bond, self.bond)
        self.assertEqual(p, c)

        p = self.parser.parse_expression('( \n Atom ⊔ Bond\t)  ⊓\nCompound  ')
        c = OWLObjectIntersectionOf((OWLObjectUnionOf((self.atom, self.bond)), self.compound))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∀ hasBond.{ \n\t d91_32  ⊔ d91_17  ⊔    bond5225  }')
        c = OWLObjectAllValuesFrom(self.has_bond, OWLObjectOneOf((self.d91_32, self.d91_17, self.bond5225)))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∀ act.{ \n\t 1.2f  ⊔    3.2f  }')
        c = OWLDataAllValuesFrom(self.act, OWLDataOneOf((OWLLiteral(1.2), OWLLiteral(3.2))))
        self.assertEqual(p, c)

        p = self.parser.parse_expression('∃ act.(  xsd:double[  > 5f,< 4.2f \n, <  -1.8e10f  ]\t ⊓  integer )')
        f1 = OWLFacetRestriction(OWLFacet.MIN_EXCLUSIVE, OWLLiteral(5.0))
        f2 = OWLFacetRestriction(OWLFacet.MAX_EXCLUSIVE, OWLLiteral(4.2))
        f3 = OWLFacetRestriction(OWLFacet.MAX_EXCLUSIVE, OWLLiteral(-1.8e10))
        c = OWLDataSomeValuesFrom(self.act, OWLDataIntersectionOf(
                                    (OWLDatatypeRestriction(DoubleOWLDatatype, (f1, f2, f3)), IntegerOWLDatatype)))
        self.assertEqual(p, c)
