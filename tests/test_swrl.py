import unittest

import pytest

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import IntegerOWLDatatype, OWLLiteral
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty
from owlapy.swrl import SWRL, SWRLB, Atom, BuiltInAtom, ClassAtom, DataPropertyAtom, DataRangeAtom, DifferentFromAtom, DVariable, IVariable, ObjectPropertyAtom, Rule, SameAsAtom


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


class TestVariable(unittest.TestCase):
    NS = "http://www.benchmark.org/family#"

    def test_is_i_variable_and_is_d_variable(self):
        x = IVariable(SWRL + "x")
        a = DVariable(SWRL + "a")
        self.assertTrue(x.is_i_variable())
        self.assertFalse(x.is_d_variable())
        self.assertTrue(a.is_d_variable())
        self.assertFalse(a.is_i_variable())

    def test_variable_str_and_repr(self):
        x = IVariable(SWRL + "x")
        self.assertEqual(str(x), "?x")
        self.assertEqual(repr(x), f"IVariable({x.iri})")
        a = DVariable(SWRL + "a")
        self.assertEqual(repr(a), f"DVariable({a.iri})")

    def test_variable_equality_and_hash(self):
        x1 = IVariable(SWRL + "x")
        x2 = IVariable(SWRL + "x")
        a = DVariable(SWRL + "x")
        self.assertEqual(x1, x2)
        self.assertEqual(hash(x1), hash(x2))
        # Different Variable subclass with the same IRI is not equal.
        self.assertNotEqual(x1, a)
        # Different type entirely.
        self.assertNotEqual(x1, "not a variable")

    def test_variable_accepts_string_iri(self):
        x = IVariable(SWRL + "x")
        y = IVariable(str(SWRL + "x"))
        self.assertEqual(x, y)


class TestAtomTypePredicatesAndDunders(unittest.TestCase):
    NS = "http://www.benchmark.org/family#"
    x = IVariable(SWRL + "x")
    y = IVariable(SWRL + "y")
    a = DVariable(SWRL + "a")

    def test_class_atom_predicates_str_hash_eq(self):
        male = OWLClass(self.NS + "male")
        atom = ClassAtom(male, self.x)
        self.assertTrue(atom.is_class_assertion())
        self.assertFalse(atom.is_property_assertion())
        self.assertFalse(atom.is_same_as())
        self.assertFalse(atom.is_different_from())
        self.assertFalse(atom.is_builtin())
        self.assertEqual(str(atom), "male(?x)")
        self.assertEqual(hash(atom), hash(ClassAtom(male, self.x)))
        self.assertEqual(atom, ClassAtom(male, self.x))
        self.assertNotEqual(atom, ClassAtom(OWLClass(self.NS + "female"), self.x))
        self.assertNotEqual(atom, "not an atom")

    def test_data_range_atom_predicates_str_hash_eq(self):
        atom = DataRangeAtom(IntegerOWLDatatype, self.a)
        self.assertTrue(atom.is_class_assertion())
        self.assertFalse(atom.is_property_assertion())
        self.assertFalse(atom.is_same_as())
        self.assertFalse(atom.is_different_from())
        self.assertFalse(atom.is_builtin())
        self.assertEqual(str(atom), "integer(?a)")
        self.assertEqual(hash(atom), hash(DataRangeAtom(IntegerOWLDatatype, self.a)))
        self.assertEqual(atom, DataRangeAtom(IntegerOWLDatatype, self.a))
        self.assertNotEqual(atom, DataRangeAtom(IntegerOWLDatatype, DVariable(SWRL + "b")))

    def test_object_property_atom_predicates_hash_eq(self):
        has_child = OWLObjectProperty(self.NS + "hasChild")
        atom = ObjectPropertyAtom(has_child, self.x, self.y)
        self.assertFalse(atom.is_class_assertion())
        self.assertTrue(atom.is_property_assertion())
        self.assertFalse(atom.is_same_as())
        self.assertFalse(atom.is_different_from())
        self.assertFalse(atom.is_builtin())
        self.assertEqual(hash(atom), hash(ObjectPropertyAtom(has_child, self.x, self.y)))
        self.assertEqual(atom, ObjectPropertyAtom(has_child, self.x, self.y))
        self.assertNotEqual(atom, ObjectPropertyAtom(has_child, self.y, self.x))
        self.assertNotEqual(atom, "not an atom")

    def test_data_property_atom_predicates_hash_eq(self):
        has_age = OWLDataProperty(self.NS + "hasAge")
        atom = DataPropertyAtom(has_age, self.x, self.a)
        self.assertFalse(atom.is_class_assertion())
        self.assertTrue(atom.is_property_assertion())
        self.assertEqual(hash(atom), hash(DataPropertyAtom(has_age, self.x, self.a)))
        self.assertEqual(atom, DataPropertyAtom(has_age, self.x, self.a))
        self.assertNotEqual(atom, DataPropertyAtom(has_age, self.x, DVariable(SWRL + "b")))

    def test_same_as_atom_full(self):
        atom = SameAsAtom(self.x, self.y)
        self.assertFalse(atom.is_class_assertion())
        self.assertFalse(atom.is_property_assertion())
        self.assertTrue(atom.is_same_as())
        self.assertFalse(atom.is_different_from())
        self.assertFalse(atom.is_builtin())
        self.assertEqual(str(atom), "sameAs(?x, ?y)")
        self.assertEqual(repr(atom), f"SameAs(IVariable({self.x.iri.str}), IVariable({self.y.iri.str}))")
        self.assertEqual(hash(atom), hash(SameAsAtom(self.x, self.y)))
        self.assertEqual(atom, SameAsAtom(self.x, self.y))
        self.assertNotEqual(atom, SameAsAtom(self.y, self.x))
        self.assertNotEqual(atom, "not an atom")

    def test_different_from_atom_full(self):
        atom = DifferentFromAtom(self.x, self.y)
        self.assertFalse(atom.is_class_assertion())
        self.assertFalse(atom.is_property_assertion())
        self.assertFalse(atom.is_same_as())
        self.assertTrue(atom.is_different_from())
        self.assertFalse(atom.is_builtin())
        self.assertEqual(str(atom), "differentFrom(?x, ?y)")
        self.assertEqual(repr(atom), f"DifferentFrom(IVariable({self.x.iri.str}), IVariable({self.y.iri.str}))")
        self.assertEqual(hash(atom), hash(DifferentFromAtom(self.x, self.y)))
        self.assertEqual(atom, DifferentFromAtom(self.x, self.y))
        self.assertNotEqual(atom, DifferentFromAtom(self.y, self.x))

    def test_builtin_atom_predicates_str_with_literal_and_variable_args(self):
        atom = BuiltInAtom(IRI.create(SWRLB + "greaterThan"), [self.x, OWLLiteral(40)])
        self.assertFalse(atom.is_class_assertion())
        self.assertFalse(atom.is_property_assertion())
        self.assertFalse(atom.is_same_as())
        self.assertFalse(atom.is_different_from())
        self.assertTrue(atom.is_builtin())
        self.assertEqual(str(atom), "greaterThan(?x, 40)")
        self.assertEqual(hash(atom), hash(BuiltInAtom(IRI.create(SWRLB + "greaterThan"), [self.x, OWLLiteral(40)])))
        self.assertEqual(atom, BuiltInAtom(IRI.create(SWRLB + "greaterThan"), [self.x, OWLLiteral(40)]))
        self.assertNotEqual(atom, BuiltInAtom(IRI.create(SWRLB + "lessThan"), [self.x, OWLLiteral(40)]))


class TestAtomFromString(unittest.TestCase):
    NS = "http://www.benchmark.org/family#"

    def test_single_arg_data_range_atom_with_literal(self):
        atom = Atom.from_string("integer(5)", namespace=self.NS)
        self.assertIsInstance(atom, DataRangeAtom)
        self.assertEqual(atom.argument1, OWLLiteral("5"))

    def test_single_arg_data_range_atom_with_variable(self):
        atom = Atom.from_string("integer(?a)", namespace=self.NS)
        self.assertIsInstance(atom, DataRangeAtom)
        self.assertEqual(atom.argument1, DVariable(SWRL + "a"))

    def test_single_arg_class_atom_with_individual(self):
        atom = Atom.from_string("male(bob)", namespace=self.NS)
        self.assertIsInstance(atom, ClassAtom)
        self.assertEqual(atom.argument1, OWLNamedIndividual(self.NS + "bob"))

    def test_single_arg_class_atom_with_variable(self):
        atom = Atom.from_string("male(?x)", namespace=self.NS)
        self.assertIsInstance(atom, ClassAtom)
        self.assertEqual(atom.argument1, IVariable(SWRL + "x"))

    def test_data_property_atom_with_concrete_individual_and_literal(self):
        # NOTE: unlike the object-property branch, DataPropertyAtom parsing does not
        # prefix argument1 with `namespace` -- it must already be a full IRI string.
        atom = Atom.from_string(
            "hasAge(http://example.com/bob, 30)", namespace=self.NS, dp_predicates=["hasAge"]
        )
        self.assertIsInstance(atom, DataPropertyAtom)
        self.assertEqual(atom.argument1, OWLNamedIndividual("http://example.com/bob"))
        self.assertEqual(atom.argument2, OWLLiteral("30"))

    def test_object_property_atom_with_concrete_individuals(self):
        atom = Atom.from_string("married(bob, alice)", namespace=self.NS)
        self.assertIsInstance(atom, ObjectPropertyAtom)
        self.assertEqual(atom.argument1, OWLNamedIndividual(self.NS + "bob"))
        self.assertEqual(atom.argument2, OWLNamedIndividual(self.NS + "alice"))

    def test_same_as_atom_with_variables(self):
        atom = Atom.from_string("sameAs(?x, ?y)", namespace=self.NS)
        self.assertIsInstance(atom, SameAsAtom)
        self.assertEqual(atom.argument1, IVariable(SWRL + "x"))
        self.assertEqual(atom.argument2, IVariable(SWRL + "y"))

    def test_same_as_atom_with_individuals(self):
        atom = Atom.from_string("sameAs(bob, alice)", namespace=self.NS)
        self.assertIsInstance(atom, SameAsAtom)
        self.assertEqual(atom.argument1, OWLNamedIndividual(self.NS + "bob"))
        self.assertEqual(atom.argument2, OWLNamedIndividual(self.NS + "alice"))

    def test_different_from_atom_with_variables(self):
        atom = Atom.from_string("differentFrom(?x, ?y)", namespace=self.NS)
        self.assertIsInstance(atom, DifferentFromAtom)

    def test_different_from_atom_with_individuals(self):
        atom = Atom.from_string("differentFrom(bob, alice)", namespace=self.NS)
        self.assertIsInstance(atom, DifferentFromAtom)
        self.assertEqual(atom.argument1, OWLNamedIndividual(self.NS + "bob"))
        self.assertEqual(atom.argument2, OWLNamedIndividual(self.NS + "alice"))

    def test_builtin_atom_with_non_variable_first_argument(self):
        atom = Atom.from_string("add(5, 3)", namespace=self.NS)
        self.assertIsInstance(atom, BuiltInAtom)
        self.assertEqual(atom.predicate, IRI.create(SWRLB + "add"))

    def test_invalid_atom_string_raises_value_error(self):
        with pytest.raises(ValueError):
            Atom.from_string("not a valid atom!!!", namespace=self.NS)

    def test_unrecognized_predicate_arity_raises_value_error(self):
        with pytest.raises(ValueError):
            Atom.from_string("foo(?x, ?y, ?z)", namespace=self.NS)


class TestRuleEqualityAndParsing(unittest.TestCase):
    NS = "http://www.benchmark.org/family#"
    x = IVariable(SWRL + "x")

    def test_rule_equality_and_hash(self):
        male = OWLClass(self.NS + "male")
        father = OWLClass(self.NS + "Father")
        atom1 = ClassAtom(male, self.x)
        atom2 = ClassAtom(father, self.x)
        rule_a = Rule([atom1], [atom2])
        rule_b = Rule([atom1], [atom2])
        self.assertEqual(rule_a, rule_b)
        self.assertEqual(hash(rule_a), hash(rule_b))
        self.assertNotEqual(rule_a, Rule([atom2], [atom1]))
        self.assertNotEqual(rule_a, "not a rule")

    def test_rule_from_string_with_same_as_and_different_from(self):
        rule = Rule.from_string(
            "male(?x) ^ sameAs(?x, ?y) ^ differentFrom(?x, ?z) -> male(?y)",
            namespace=self.NS,
        )
        self.assertEqual(len(rule.body), 3)
        self.assertIsInstance(rule.body[1], SameAsAtom)
        self.assertIsInstance(rule.body[2], DifferentFromAtom)
