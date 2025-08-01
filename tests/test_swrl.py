import unittest

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral, IntegerOWLDatatype
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty
from owlapy.swrl import SWRL, SWRLB, IVariable, DVariable, ClassAtom, ObjectPropertyAtom, DataRangeAtom, \
    Rule, DataPropertyAtom, BuiltInAtom, SameAsAtom, DifferentFromAtom


class TestSWRL(unittest.TestCase):
    x = IVariable(SWRL + "x")
    y = IVariable(SWRL + "y")
    z = IVariable(SWRL + "z")
    a = DVariable(SWRL + "a")
    b = DVariable(SWRL + "b")
    NS = "http://www.benchmark.org/family#"
    ind1 = OWLNamedIndividual(NS + "matthias")
    ind2 = OWLNamedIndividual(NS + "anna")
    grandfather_rule = None

    def test_rule_creation_and_printing(self):
        male = OWLClass(self.NS + "male")
        has_child = OWLObjectProperty(self.NS + "hasChild")
        has_age= OWLDataProperty(self.NS + "hasAge")
        father = OWLClass(self.NS + "Father")
        grandfather = OWLClass(self.NS + "Grandfather")

        atom1 = ClassAtom(male, self.x)
        atom2 = ObjectPropertyAtom(has_child, self.x, self.y)
        atom3 = ClassAtom(father, self.x)

        rule = Rule([atom1, atom2], [atom3])

        self.assertEqual(str(rule), "male(?x) ^ hasChild(?x, ?y) -> Father(?x)")

        atom1 = ClassAtom(male, self.x)
        atom2 = ObjectPropertyAtom(has_child, self.x, self.y)
        atom3= ObjectPropertyAtom(has_child, self.y, self.z)
        atom4 = DataPropertyAtom(has_age, self.x, self.a)
        atom5 = DataRangeAtom(IntegerOWLDatatype, self.a)
        atom6 = BuiltInAtom(IRI.create(SWRLB + "greaterThanOrEqual"), [self.x, OWLLiteral(40)])
        atom7 = ClassAtom(grandfather, self.x)

        rule = Rule([atom1, atom2, atom3, atom4, atom5, atom6], [atom7])

        self.assertEqual(str(rule), "male(?x) ^ hasChild(?x, ?y) ^ hasChild(?y, ?z) ^ hasAge(?x, ?a) ^ integer(?a) ^ greaterThanOrEqual(?x, 40) -> Grandfather(?x)")

    def test_rule_parsing(self):

        rule = Rule.from_string("male(?x) ^ hasChild(?x, ?y) ^ hasChild(?y, ?z) ^ hasAge(?x, ?a) ^ integer(?a) ^ greaterThanOrEqual(?x, 40) -> Grandfather(?x)", namespace=self.NS, dp_predicates=["hasAge"])
        self.assertEqual(rule.__repr__(), """Rule(['ClassAtom(OWLClass(http://www.benchmark.org/family#male), IVariable(http://www.w3.org/2003/11/swrl#x))', 'ObjectPropertyAtom(OWLObjectProperty(http://www.benchmark.org/family#hasChild), IVariable(http://www.w3.org/2003/11/swrl#x), IVariable(http://www.w3.org/2003/11/swrl#y))', 'ObjectPropertyAtom(OWLObjectProperty(http://www.benchmark.org/family#hasChild), IVariable(http://www.w3.org/2003/11/swrl#y), IVariable(http://www.w3.org/2003/11/swrl#z))', 'DataPropertyAtom(OWLDataProperty(http://www.benchmark.org/family#hasAge), IVariable(http://www.w3.org/2003/11/swrl#x), DVariable(http://www.w3.org/2003/11/swrl#a))', 'DataRangeAtom(OWLDatatype(http://www.w3.org/2001/XMLSchema#integer) DVariable(http://www.w3.org/2003/11/swrl#a))', "BuiltInAtom(IRI.create(http://www.w3.org/2003/11/swrlb#greaterThanOrEqual), '40'])"], ['ClassAtom(OWLClass(http://www.benchmark.org/family#Grandfather), IVariable(http://www.w3.org/2003/11/swrl#x))'])""")
