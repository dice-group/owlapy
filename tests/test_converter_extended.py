"""Extended test cases for converter module to increase coverage."""
import unittest
from owlapy.converter import Owl2SparqlConverter, VariablesMapping, peek
from owlapy.class_expression import (
    OWLClass, OWLObjectIntersectionOf, OWLObjectUnionOf,
    OWLObjectComplementOf, OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom,
    OWLObjectHasValue, OWLObjectMinCardinality, OWLObjectMaxCardinality,
    OWLObjectExactCardinality, OWLObjectHasSelf, OWLObjectOneOf,
    OWLDataSomeValuesFrom, OWLDataAllValuesFrom, OWLDataHasValue,
    OWLDataMinCardinality, OWLDataMaxCardinality, OWLDataExactCardinality,
    OWLDataOneOf, OWLDatatypeRestriction, OWLFacetRestriction
)
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty, OWLObjectInverseOf
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_datatype import OWLDatatype
from owlapy.iri import IRI
from owlapy.vocab import OWLFacet, XSDVocabulary


class TestPeekFunction(unittest.TestCase):
    """Test peek helper function."""

    def test_peek_basic(self):
        """Test peek function with list."""
        arr = [1, 2, 3, 4, 5]
        self.assertEqual(peek(arr), 5)

    def test_peek_single_element(self):
        """Test peek with single element."""
        arr = ["only"]
        self.assertEqual(peek(arr), "only")

    def test_peek_strings(self):
        """Test peek with string elements."""
        arr = ["a", "b", "c"]
        self.assertEqual(peek(arr), "c")


class TestVariablesMapping(unittest.TestCase):
    """Test VariablesMapping class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mapping = VariablesMapping()
        self.ns = "http://example.com/test#"

    def test_get_variable_class(self):
        """Test getting variable for OWLClass."""
        cls = OWLClass(IRI.create(self.ns, "Person"))
        var = self.mapping.get_variable(cls)

        self.assertTrue(var.startswith("?cls_"))
        self.assertEqual(self.mapping.class_cnt, 1)

    def test_get_variable_object_property(self):
        """Test getting variable for OWLObjectProperty."""
        prop = OWLObjectProperty(IRI.create(self.ns, "knows"))
        var = self.mapping.get_variable(prop)

        self.assertTrue(var.startswith("?p_"))
        self.assertEqual(self.mapping.prop_cnt, 1)

    def test_get_variable_data_property(self):
        """Test getting variable for OWLDataProperty."""
        prop = OWLDataProperty(IRI.create(self.ns, "hasAge"))
        var = self.mapping.get_variable(prop)

        self.assertTrue(var.startswith("?p_"))
        self.assertEqual(self.mapping.prop_cnt, 1)

    def test_get_variable_individual(self):
        """Test getting variable for OWLNamedIndividual."""
        ind = OWLNamedIndividual(IRI.create(self.ns, "Alice"))
        var = self.mapping.get_variable(ind)

        self.assertTrue(var.startswith("?ind_"))
        self.assertEqual(self.mapping.ind_cnt, 1)

    def test_get_variable_caching(self):
        """Test that getting variable for same entity returns cached value."""
        cls = OWLClass(IRI.create(self.ns, "Person"))
        var1 = self.mapping.get_variable(cls)
        var2 = self.mapping.get_variable(cls)

        self.assertEqual(var1, var2)
        self.assertEqual(self.mapping.class_cnt, 1)  # Counter should not increase

    def test_new_individual_variable(self):
        """Test creating new individual variable."""
        var1 = self.mapping.new_individual_variable()
        var2 = self.mapping.new_individual_variable()

        self.assertTrue(var1.startswith("?s_"))
        self.assertTrue(var2.startswith("?s_"))
        self.assertNotEqual(var1, var2)

    def test_new_property_variable(self):
        """Test creating new property variable."""
        var1 = self.mapping.new_property_variable()
        var2 = self.mapping.new_property_variable()

        self.assertTrue(var1.startswith("?p_"))
        self.assertTrue(var2.startswith("?p_"))
        self.assertNotEqual(var1, var2)

    def test_contains(self):
        """Test __contains__ method."""
        cls = OWLClass(IRI.create(self.ns, "Person"))
        self.assertNotIn(cls, self.mapping)

        self.mapping.get_variable(cls)
        self.assertIn(cls, self.mapping)

    def test_getitem(self):
        """Test __getitem__ method."""
        cls = OWLClass(IRI.create(self.ns, "Person"))
        var = self.mapping.get_variable(cls)

        self.assertEqual(self.mapping[cls], var)


class TestOwl2SparqlConverter(unittest.TestCase):
    """Test Owl2SparqlConverter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.converter = Owl2SparqlConverter()
        self.ns = "http://example.com/test#"

    def test_convert_simple_class(self):
        """Test converting simple class."""
        person = OWLClass(IRI.create(self.ns, "Person"))

        result = self.converter.convert("?x", person)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_convert_intersection(self):
        """Test converting intersection."""
        male = OWLClass(IRI.create(self.ns, "Male"))
        teacher = OWLClass(IRI.create(self.ns, "Teacher"))

        intersection = OWLObjectIntersectionOf([male, teacher])
        result = self.converter.convert("?x", intersection)

        self.assertIsInstance(result, list)

    def test_convert_union(self):
        """Test converting union."""
        male = OWLClass(IRI.create(self.ns, "Male"))
        female = OWLClass(IRI.create(self.ns, "Female"))

        union = OWLObjectUnionOf([male, female])
        result = self.converter.convert("?x", union)

        self.assertIsInstance(result, list)
        sparql_str = "".join(result)
        self.assertIn("UNION", sparql_str)

    def test_convert_complement(self):
        """Test converting complement."""
        person = OWLClass(IRI.create(self.ns, "Person"))
        complement = OWLObjectComplementOf(person)

        result = self.converter.convert("?x", complement)

        self.assertIsInstance(result, list)
        sparql_str = "".join(result)
        self.assertIn("FILTER NOT EXISTS", sparql_str)

    def test_convert_object_some_values_from(self):
        """Test converting existential restriction."""
        has_child = OWLObjectProperty(IRI.create(self.ns, "hasChild"))
        male = OWLClass(IRI.create(self.ns, "Male"))

        exists = OWLObjectSomeValuesFrom(has_child, male)
        result = self.converter.convert("?x", exists)

        self.assertIsInstance(result, list)

    def test_convert_object_all_values_from(self):
        """Test converting universal restriction."""
        has_child = OWLObjectProperty(IRI.create(self.ns, "hasChild"))
        male = OWLClass(IRI.create(self.ns, "Male"))

        forall = OWLObjectAllValuesFrom(has_child, male)
        result = self.converter.convert("?x", forall)

        self.assertIsInstance(result, list)

    def test_convert_object_all_values_from_de_morgan(self):
        """Test converting universal restriction with de Morgan."""
        has_child = OWLObjectProperty(IRI.create(self.ns, "hasChild"))
        male = OWLClass(IRI.create(self.ns, "Male"))

        forall = OWLObjectAllValuesFrom(has_child, male)
        result = self.converter.convert("?x", forall, for_all_de_morgan=True)

        self.assertIsInstance(result, list)
        sparql_str = "".join(result)
        self.assertIn("FILTER NOT EXISTS", sparql_str)

    def test_convert_object_all_values_from_no_de_morgan(self):
        """Test converting universal restriction without de Morgan."""
        has_child = OWLObjectProperty(IRI.create(self.ns, "hasChild"))
        male = OWLClass(IRI.create(self.ns, "Male"))

        forall = OWLObjectAllValuesFrom(has_child, male)
        result = self.converter.convert("?x", forall, for_all_de_morgan=False)

        self.assertIsInstance(result, list)

    def test_convert_object_has_value(self):
        """Test converting hasValue restriction."""
        has_child = OWLObjectProperty(IRI.create(self.ns, "hasChild"))
        john = OWLNamedIndividual(IRI.create(self.ns, "John"))

        has_value = OWLObjectHasValue(has_child, john)
        result = self.converter.convert("?x", has_value)

        self.assertIsInstance(result, list)

    def test_convert_object_min_cardinality(self):
        """Test converting min cardinality restriction."""
        has_child = OWLObjectProperty(IRI.create(self.ns, "hasChild"))
        person = OWLClass(IRI.create(self.ns, "Person"))

        min_card = OWLObjectMinCardinality(2, has_child, person)
        result = self.converter.convert("?x", min_card)

        self.assertIsInstance(result, list)
        sparql_str = "".join(result)
        self.assertIn(">=", sparql_str)

    def test_convert_object_max_cardinality(self):
        """Test converting max cardinality restriction."""
        has_child = OWLObjectProperty(IRI.create(self.ns, "hasChild"))
        person = OWLClass(IRI.create(self.ns, "Person"))

        max_card = OWLObjectMaxCardinality(3, has_child, person)
        result = self.converter.convert("?x", max_card)

        self.assertIsInstance(result, list)
        sparql_str = "".join(result)
        self.assertIn("<=", sparql_str)

    def test_convert_object_exact_cardinality(self):
        """Test converting exact cardinality restriction."""
        has_child = OWLObjectProperty(IRI.create(self.ns, "hasChild"))
        person = OWLClass(IRI.create(self.ns, "Person"))

        exact_card = OWLObjectExactCardinality(2, has_child, person)
        result = self.converter.convert("?x", exact_card)

        self.assertIsInstance(result, list)

    def test_convert_object_has_self(self):
        """Test converting hasSelf restriction."""
        knows = OWLObjectProperty(IRI.create(self.ns, "knows"))

        has_self = OWLObjectHasSelf(knows)
        result = self.converter.convert("?x", has_self)

        self.assertIsInstance(result, list)

    def test_convert_object_one_of(self):
        """Test converting oneOf."""
        alice = OWLNamedIndividual(IRI.create(self.ns, "Alice"))
        bob = OWLNamedIndividual(IRI.create(self.ns, "Bob"))

        one_of = OWLObjectOneOf([alice, bob])
        result = self.converter.convert("?x", one_of)

        self.assertIsInstance(result, list)
        sparql_str = "".join(result)
        self.assertIn("IN", sparql_str)

    def test_convert_data_some_values_from(self):
        """Test converting data existential restriction."""
        has_age = OWLDataProperty(IRI.create(self.ns, "hasAge"))
        int_datatype = OWLDatatype(XSDVocabulary.INTEGER)

        exists = OWLDataSomeValuesFrom(has_age, int_datatype)
        result = self.converter.convert("?x", exists)

        self.assertIsInstance(result, list)

    def test_convert_data_all_values_from(self):
        """Test converting data universal restriction."""
        has_age = OWLDataProperty(IRI.create(self.ns, "hasAge"))
        int_datatype = OWLDatatype(XSDVocabulary.INTEGER)

        forall = OWLDataAllValuesFrom(has_age, int_datatype)
        result = self.converter.convert("?x", forall)

        self.assertIsInstance(result, list)

    def test_convert_data_has_value(self):
        """Test converting data hasValue restriction."""
        has_age = OWLDataProperty(IRI.create(self.ns, "hasAge"))
        literal = OWLLiteral(30)

        has_value = OWLDataHasValue(has_age, literal)
        result = self.converter.convert("?x", has_value)

        self.assertIsInstance(result, list)

    def test_convert_data_min_cardinality(self):
        """Test converting data min cardinality restriction."""
        has_name = OWLDataProperty(IRI.create(self.ns, "hasName"))
        string_datatype = OWLDatatype(XSDVocabulary.STRING)

        min_card = OWLDataMinCardinality(1, has_name, string_datatype)
        result = self.converter.convert("?x", min_card)

        self.assertIsInstance(result, list)

    def test_convert_data_max_cardinality(self):
        """Test converting data max cardinality restriction."""
        has_name = OWLDataProperty(IRI.create(self.ns, "hasName"))
        string_datatype = OWLDatatype(XSDVocabulary.STRING)

        max_card = OWLDataMaxCardinality(1, has_name, string_datatype)
        result = self.converter.convert("?x", max_card)

        self.assertIsInstance(result, list)

    def test_convert_data_exact_cardinality(self):
        """Test converting data exact cardinality restriction."""
        has_name = OWLDataProperty(IRI.create(self.ns, "hasName"))
        string_datatype = OWLDatatype(XSDVocabulary.STRING)

        exact_card = OWLDataExactCardinality(1, has_name, string_datatype)
        result = self.converter.convert("?x", exact_card)

        self.assertIsInstance(result, list)

    def test_convert_data_one_of(self):
        """Test converting data oneOf."""
        lit1 = OWLLiteral(10)
        lit2 = OWLLiteral(20)

        one_of = OWLDataOneOf([lit1, lit2])
        result = self.converter.convert("?x", one_of)

        self.assertIsInstance(result, list)
        sparql_str = "".join(result)
        self.assertIn("IN", sparql_str)

    def test_convert_datatype_restriction(self):
        """Test converting datatype restriction."""
        int_datatype = OWLDatatype(XSDVocabulary.INTEGER)
        lit_min = OWLLiteral(18)
        lit_max = OWLLiteral(65)

        facet_restrictions = [
            OWLFacetRestriction(OWLFacet.MIN_INCLUSIVE, lit_min),
            OWLFacetRestriction(OWLFacet.MAX_INCLUSIVE, lit_max)
        ]

        restriction = OWLDatatypeRestriction(int_datatype, facet_restrictions)
        result = self.converter.convert("?x", restriction)

        self.assertIsInstance(result, list)

    def test_as_query_basic(self):
        """Test as_query method."""
        person = OWLClass(IRI.create(self.ns, "Person"))

        query = self.converter.as_query("?x", person)

        self.assertIsInstance(query, str)
        self.assertIn("SELECT", query)
        self.assertIn("WHERE", query)

    def test_as_query_with_count(self):
        """Test as_query with count."""
        person = OWLClass(IRI.create(self.ns, "Person"))

        query = self.converter.as_query("?x", person, count=True)

        self.assertIsInstance(query, str)
        self.assertIn("COUNT", query)

    def test_as_query_with_values(self):
        """Test as_query with values."""
        person = OWLClass(IRI.create(self.ns, "Person"))
        alice = OWLNamedIndividual(IRI.create(self.ns, "Alice"))
        bob = OWLNamedIndividual(IRI.create(self.ns, "Bob"))

        query = self.converter.as_query("?x", person, values=[alice, bob])

        self.assertIsInstance(query, str)
        self.assertIn("VALUES", query)

    def test_as_query_named_individuals(self):
        """Test as_query with named_individuals flag."""
        person = OWLClass(IRI.create(self.ns, "Person"))

        query = self.converter.as_query("?x", person, named_individuals=True)

        self.assertIsInstance(query, str)

    def test_convert_inverse_property(self):
        """Test converting with inverse property."""
        has_parent = OWLObjectProperty(IRI.create(self.ns, "hasParent"))
        inverse_prop = OWLObjectInverseOf(has_parent)
        person = OWLClass(IRI.create(self.ns, "Person"))

        exists = OWLObjectSomeValuesFrom(inverse_prop, person)
        result = self.converter.convert("?x", exists)

        self.assertIsInstance(result, list)

    def test_convert_object_has_value_inverse(self):
        """Test converting hasValue with inverse property."""
        has_parent = OWLObjectProperty(IRI.create(self.ns, "hasParent"))
        inverse_prop = OWLObjectInverseOf(has_parent)
        john = OWLNamedIndividual(IRI.create(self.ns, "John"))

        has_value = OWLObjectHasValue(inverse_prop, john)
        result = self.converter.convert("?x", has_value)

        self.assertIsInstance(result, list)

    def test_convert_complex_nested(self):
        """Test converting complex nested expression."""
        male = OWLClass(IRI.create(self.ns, "Male"))
        teacher = OWLClass(IRI.create(self.ns, "Teacher"))
        has_child = OWLObjectProperty(IRI.create(self.ns, "hasChild"))
        female = OWLClass(IRI.create(self.ns, "Female"))

        # Male ⊓ Teacher ⊓ ∃hasChild.Female
        complex_expr = OWLObjectIntersectionOf([
            male,
            teacher,
            OWLObjectSomeValuesFrom(has_child, female)
        ])

        result = self.converter.convert("?x", complex_expr)

        self.assertIsInstance(result, list)

    def test_convert_complement_with_named_individuals(self):
        """Test converting complement with named_individuals flag."""
        person = OWLClass(IRI.create(self.ns, "Person"))
        complement = OWLObjectComplementOf(person)

        result = self.converter.convert("?x", complement, named_individuals=True)

        self.assertIsInstance(result, list)
        sparql_str = "".join(result)
        self.assertIn("NamedIndividual", sparql_str)

    def test_modal_depth(self):
        """Test modal_depth property."""
        person = OWLClass(IRI.create(self.ns, "Person"))

        self.converter.convert("?x", person)

        # After conversion, check modal depth tracking
        self.assertIsInstance(self.converter.modal_depth, int)

    def test_new_count_var(self):
        """Test new_count_var method - needs convert to be called first."""
        person = OWLClass(IRI.create(self.ns, "Person"))
        # Initialize converter properly by calling convert first
        self.converter.convert("?x", person)

        var1 = self.converter.new_count_var()
        var2 = self.converter.new_count_var()

        self.assertTrue(var1.startswith("?cnt_"))
        self.assertTrue(var2.startswith("?cnt_"))
        self.assertNotEqual(var1, var2)

    def test_render_literal(self):
        """Test render method with OWLLiteral."""
        # Initialize converter first
        person = OWLClass(IRI.create(self.ns, "Person"))
        self.converter.convert("?x", person)

        lit = OWLLiteral(42)
        rendered = self.converter.render(lit)

        self.assertIsInstance(rendered, str)
        self.assertIn("42", rendered)

    def test_render_entity(self):
        """Test render method with OWLEntity - needs convert to be called first."""
        person = OWLClass(IRI.create(self.ns, "Person"))
        # Initialize converter properly by calling convert first
        self.converter.convert("?x", person)

        another_person = OWLClass(IRI.create(self.ns, "AnotherPerson"))
        rendered = self.converter.render(another_person)

        self.assertIsInstance(rendered, str)


class TestOwl2SparqlConverterEdgeCases(unittest.TestCase):
    """Test edge cases for Owl2SparqlConverter."""

    def setUp(self):
        """Set up test fixtures."""
        self.converter = Owl2SparqlConverter()
        self.ns = "http://example.com/test#"

    def test_convert_cardinality_zero(self):
        """Test converting cardinality with zero."""
        has_child = OWLObjectProperty(IRI.create(self.ns, "hasChild"))
        person = OWLClass(IRI.create(self.ns, "Person"))

        # Exactly 0 children
        exact_zero = OWLObjectExactCardinality(0, has_child, person)
        result = self.converter.convert("?x", exact_zero)

        self.assertIsInstance(result, list)
        sparql_str = "".join(result)
        self.assertIn("UNION", sparql_str)

    def test_convert_max_cardinality_with_union(self):
        """Test max cardinality generates union pattern."""
        has_child = OWLObjectProperty(IRI.create(self.ns, "hasChild"))
        person = OWLClass(IRI.create(self.ns, "Person"))

        max_card = OWLObjectMaxCardinality(2, has_child, person)
        result = self.converter.convert("?x", max_card)

        sparql_str = "".join(result)
        self.assertIn("UNION", sparql_str)

    def test_multiple_unions(self):
        """Test multiple union operands."""
        male = OWLClass(IRI.create(self.ns, "Male"))
        female = OWLClass(IRI.create(self.ns, "Female"))
        child = OWLClass(IRI.create(self.ns, "Child"))

        union = OWLObjectUnionOf([male, female, child])
        result = self.converter.convert("?x", union)

        sparql_str = "".join(result)
        # Should have 2 UNION keywords for 3 operands
        self.assertEqual(sparql_str.count("UNION"), 2)

    def test_nested_complement(self):
        """Test nested complement."""
        person = OWLClass(IRI.create(self.ns, "Person"))
        complement1 = OWLObjectComplementOf(person)
        complement2 = OWLObjectComplementOf(complement1)

        result = self.converter.convert("?x", complement2)

        self.assertIsInstance(result, list)


if __name__ == '__main__':
    unittest.main()
