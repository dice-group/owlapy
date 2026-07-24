"""Unit tests for owlapy.marked_entity_generator_converter that exercise the
SPARQL *string generation* logic directly, without a live Fuseki endpoint.

tests/test_marked_entity_generator_converter.py already covers end-to-end
behaviour against a running Fuseki instance, but every test there is skipped
when Fuseki isn't reachable (the common case for local/CI runs), leaving the
query-building logic itself untested. These tests build class expressions
with CONTEXT_POSITION_MARKER and assert on the shape of the generated SPARQL
string, validating syntax with rdflib's local SPARQL parser instead of
executing anything over the network.
"""
from rdflib.plugins.sparql.parser import parseQuery

from owlapy.class_expression import (
    OWLClass,
    OWLDataAllValuesFrom,
    OWLDataExactCardinality,
    OWLDataHasValue,
    OWLDataMaxCardinality,
    OWLDataMinCardinality,
    OWLDataOneOf,
    OWLDataSomeValuesFrom,
    OWLDatatypeRestriction,
    OWLFacetRestriction,
    OWLObjectAllValuesFrom,
    OWLObjectComplementOf,
    OWLObjectExactCardinality,
    OWLObjectHasSelf,
    OWLObjectHasValue,
    OWLObjectIntersectionOf,
    OWLObjectMaxCardinality,
    OWLObjectMinCardinality,
    OWLObjectOneOf,
    OWLObjectSomeValuesFrom,
    OWLObjectUnionOf,
)
from owlapy.iri import IRI
from owlapy.marked_entity_generator_converter import (
    CONTEXT_POSITION_MARKER,
    QueryGenerator,
    _generate_values_stmt,
    owl_expression_to_class_query,
    owl_expression_to_negated_class_query,
    owl_expression_to_property_query,
)
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import IntegerOWLDatatype, OWLLiteral, TopOWLDatatype
from owlapy.owl_property import OWLDataProperty, OWLObjectInverseOf, OWLObjectProperty
from owlapy.vocab import OWLFacet

NS = "http://example.com/family#"

Person = OWLClass(IRI.create(NS, "Person"))
Male = OWLClass(IRI.create(NS, "Male"))
hasChild = OWLObjectProperty(IRI.create(NS, "hasChild"))
age = OWLDataProperty(IRI.create(NS, "age"))


def ind(name: str) -> OWLNamedIndividual:
    return OWLNamedIndividual(IRI.create(NS, name))


def new_generator() -> QueryGenerator:
    # Each test gets a fresh generator instance so VariablesMapping counters
    # don't leak state between assertions (mirrors how ``generator`` module
    # singleton is used internally, but isolated per-test).
    return QueryGenerator()


# ---------------------------------------------------------------------------
# _generate_values_stmt
# ---------------------------------------------------------------------------

def test_generate_values_stmt_single_individual():
    stmt = _generate_values_stmt("?pos", [ind("a")])
    assert stmt == f"VALUES ?pos {{ <{NS}a> }} . "


def test_generate_values_stmt_multiple_individuals():
    stmt = _generate_values_stmt("?pos", [ind("a"), ind("b")])
    assert f"<{NS}a>" in stmt
    assert f"<{NS}b>" in stmt
    assert stmt.startswith("VALUES ?pos {")


# ---------------------------------------------------------------------------
# _contains_marker / _contains_union_with_marker
# ---------------------------------------------------------------------------

def test_contains_marker_direct():
    assert QueryGenerator._contains_marker(CONTEXT_POSITION_MARKER) is True
    assert QueryGenerator._contains_marker(Person) is False


def test_contains_marker_nested_in_intersection_and_existential():
    ce = OWLObjectSomeValuesFrom(hasChild, OWLObjectIntersectionOf([Person, CONTEXT_POSITION_MARKER]))
    assert QueryGenerator._contains_marker(ce) is True

    ce_no_marker = OWLObjectSomeValuesFrom(hasChild, Person)
    assert QueryGenerator._contains_marker(ce_no_marker) is False


def test_contains_marker_in_complement_and_union():
    assert QueryGenerator._contains_marker(OWLObjectComplementOf(CONTEXT_POSITION_MARKER)) is True
    assert QueryGenerator._contains_marker(OWLObjectUnionOf([Person, CONTEXT_POSITION_MARKER])) is True
    assert QueryGenerator._contains_marker(OWLObjectAllValuesFrom(hasChild, CONTEXT_POSITION_MARKER)) is True


def test_contains_marker_false_for_unrelated_restriction_types():
    # OWLObjectHasValue isn't handled by _contains_marker's isinstance chain,
    # so it should fall through to False even if it structurally "contains" a marker-ish shape.
    assert QueryGenerator._contains_marker(OWLObjectHasSelf(hasChild)) is False


def test_contains_union_with_marker_true_and_false():
    union_ce = OWLObjectUnionOf([Person, CONTEXT_POSITION_MARKER])
    assert QueryGenerator._contains_union_with_marker(union_ce) is True

    plain_union = OWLObjectUnionOf([Person, Male])
    assert QueryGenerator._contains_union_with_marker(plain_union) is False

    assert QueryGenerator._contains_union_with_marker(CONTEXT_POSITION_MARKER) is False

    nested = OWLObjectIntersectionOf([Person, OWLObjectSomeValuesFrom(hasChild, union_ce)])
    assert QueryGenerator._contains_union_with_marker(nested) is True

    complement_wrapped = OWLObjectComplementOf(union_ce)
    assert QueryGenerator._contains_union_with_marker(complement_wrapped) is True


# ---------------------------------------------------------------------------
# convert() marker modes (direct, without going through as_*_query)
# ---------------------------------------------------------------------------

def test_convert_class_marker_mode_root():
    gen = new_generator()
    sparql = "".join(gen.convert("?pos", CONTEXT_POSITION_MARKER, marker_mode=True))
    assert "?pos a ?class ." in sparql


def test_convert_negated_class_marker_mode_root():
    gen = new_generator()
    sparql = "".join(gen.convert("?pos", CONTEXT_POSITION_MARKER, negated_class_marker_mode=True))
    assert "?class a <http://www.w3.org/2002/07/owl#Class>" in sparql
    assert "FILTER NOT EXISTS { ?pos a ?class . }" in sparql


def test_convert_property_marker_mode_not_inverted():
    gen = new_generator()
    sparql = "".join(gen.convert("?pos", CONTEXT_POSITION_MARKER, property_marker_mode=True, inverted=False))
    assert "?pos ?prop [] ." in sparql


def test_convert_property_marker_mode_inverted():
    gen = new_generator()
    sparql = "".join(gen.convert("?pos", CONTEXT_POSITION_MARKER, property_marker_mode=True, inverted=True))
    assert "[] ?prop ?pos ." in sparql


def test_convert_without_marker_mode_falls_back_to_base_class():
    gen = new_generator()
    sparql = "".join(gen.convert("?pos", Person))
    assert "?pos" in sparql
    assert "Person" in sparql


def test_convert_complement_with_marker_adds_class_type_constraint():
    gen = new_generator()
    ce = OWLObjectComplementOf(CONTEXT_POSITION_MARKER)
    sparql = "".join(gen.convert("?pos", ce, marker_mode=True))
    assert "FILTER NOT EXISTS {" in sparql
    assert "?class a <http://www.w3.org/2002/07/owl#Class> ." in sparql


def test_convert_complement_with_property_marker_adds_property_type_constraint():
    gen = new_generator()
    ce = OWLObjectComplementOf(CONTEXT_POSITION_MARKER)
    sparql = "".join(gen.convert("?pos", ce, property_marker_mode=True))
    assert "?prop a <http://www.w3.org/1999/02/22-rdf-syntax-ns#Property> ." in sparql


def test_convert_union_context():
    gen = new_generator()
    ce = OWLObjectUnionOf([Person, Male])
    sparql = "".join(gen.convert("?pos", ce))
    assert "UNION" in sparql


def test_convert_intersection_context():
    gen = new_generator()
    ce = OWLObjectIntersectionOf([Person, Male])
    sparql = "".join(gen.convert("?pos", ce))
    assert "Person" in sparql and "Male" in sparql


def test_convert_object_some_values_from_with_marker():
    gen = new_generator()
    ce = OWLObjectSomeValuesFrom(hasChild, CONTEXT_POSITION_MARKER)
    sparql = "".join(gen.convert("?pos", ce, marker_mode=True))
    assert "?pos" in sparql
    assert "a ?class ." in sparql


def test_convert_object_all_values_from_de_morgan_default():
    gen = new_generator()
    ce = OWLObjectAllValuesFrom(hasChild, Person)
    sparql = "".join(gen.convert("?pos", ce, for_all_de_morgan=True))
    assert "?pos" in sparql


def test_convert_object_all_values_from_without_de_morgan():
    gen = new_generator()
    ce = OWLObjectAllValuesFrom(hasChild, Person)
    sparql = "".join(gen.convert("?pos", ce, for_all_de_morgan=False))
    assert "?pos" in sparql


def test_convert_object_has_value():
    gen = new_generator()
    ce = OWLObjectHasValue(hasChild, ind("bob"))
    sparql = "".join(gen.convert("?pos", ce))
    assert f"<{NS}bob>" in sparql


def test_convert_object_min_max_exact_cardinality():
    for restriction_cls, comparator in (
        (OWLObjectMinCardinality, ">="),
        (OWLObjectMaxCardinality, "<="),
        (OWLObjectExactCardinality, "="),
    ):
        gen = new_generator()
        ce = restriction_cls(2, hasChild, Person)
        sparql = "".join(gen.convert("?pos", ce))
        assert "COUNT" in sparql
        assert comparator in sparql


def test_convert_data_min_max_exact_cardinality():
    for restriction_cls, comparator in (
        (OWLDataMinCardinality, ">="),
        (OWLDataMaxCardinality, "<="),
        (OWLDataExactCardinality, "="),
    ):
        gen = new_generator()
        ce = restriction_cls(1, age, TopOWLDatatype)
        sparql = "".join(gen.convert("?pos", ce))
        assert comparator in sparql


def test_convert_object_has_self():
    gen = new_generator()
    ce = OWLObjectHasSelf(hasChild)
    sparql = "".join(gen.convert("?pos", ce))
    assert "?pos" in sparql


def test_convert_object_one_of():
    gen = new_generator()
    ce = OWLObjectOneOf([ind("a"), ind("b")])
    sparql = "".join(gen.convert("?pos", ce))
    assert "FILTER ( ?pos IN (" in sparql
    assert f"<{NS}a>" in sparql and f"<{NS}b>" in sparql


def test_convert_data_some_values_from():
    gen = new_generator()
    ce = OWLDataSomeValuesFrom(age, TopOWLDatatype)
    sparql = "".join(gen.convert("?pos", ce))
    assert "?pos" in sparql


def test_convert_data_all_values_from():
    gen = new_generator()
    ce = OWLDataAllValuesFrom(age, TopOWLDatatype)
    sparql = "".join(gen.convert("?pos", ce))
    assert "GROUP BY" in sparql
    assert "FILTER(" in sparql


def test_convert_data_has_value():
    gen = new_generator()
    ce = OWLDataHasValue(age, OWLLiteral(42))
    sparql = "".join(gen.convert("?pos", ce))
    assert "?pos" in sparql


def test_convert_datatype_top_vs_concrete():
    gen_top = new_generator()
    sparql_top = "".join(gen_top.convert("?pos", OWLDataSomeValuesFrom(age, TopOWLDatatype)))
    assert "isLiteral" in sparql_top

    gen_concrete = new_generator()
    sparql_concrete = "".join(gen_concrete.convert("?pos", OWLDataSomeValuesFrom(age, IntegerOWLDatatype)))
    assert "DATATYPE" in sparql_concrete
    assert "integer" in sparql_concrete


def test_convert_data_one_of():
    gen = new_generator()
    ce = OWLDataOneOf([OWLLiteral(1), OWLLiteral(2)])
    sparql = "".join(gen.convert("?pos", OWLDataSomeValuesFrom(age, ce)))
    assert "FILTER (" in sparql


def test_convert_data_one_of_as_root_hits_modal_depth_one_branch():
    gen = new_generator()
    ce = OWLDataOneOf([OWLLiteral(1), OWLLiteral(2)])
    sparql = "".join(gen.convert("?pos", ce))
    assert "?pos ?p ?o" in sparql


def test_convert_object_some_values_from_with_inverse_property():
    gen = new_generator()
    ce = OWLObjectSomeValuesFrom(OWLObjectInverseOf(hasChild), Person)
    sparql = "".join(gen.convert("?pos", ce))
    assert "?pos" in sparql


def test_convert_object_has_value_with_inverse_property():
    gen = new_generator()
    ce = OWLObjectHasValue(OWLObjectInverseOf(hasChild), ind("bob"))
    sparql = "".join(gen.convert("?pos", ce))
    assert f"<{NS}bob>" in sparql


def test_convert_object_cardinality_with_inverse_property():
    gen = new_generator()
    ce = OWLObjectMinCardinality(1, OWLObjectInverseOf(hasChild), Person)
    sparql = "".join(gen.convert("?pos", ce))
    assert ">=" in sparql


def test_convert_datatype_restriction_with_facets():
    gen = new_generator()
    restriction = OWLDatatypeRestriction(
        IntegerOWLDatatype,
        [OWLFacetRestriction(OWLFacet.MIN_INCLUSIVE, OWLLiteral(0)),
         OWLFacetRestriction(OWLFacet.MAX_EXCLUSIVE, OWLLiteral(100))],
    )
    sparql = "".join(gen.convert("?pos", OWLDataSomeValuesFrom(age, restriction)))
    assert ">=" in sparql
    assert "<" in sparql


# ---------------------------------------------------------------------------
# as_class_query / as_negated_class_query / as_property_query
# ---------------------------------------------------------------------------

def test_as_class_query_simple_marker_root_is_valid_sparql():
    gen = new_generator()
    query = gen.as_class_query(CONTEXT_POSITION_MARKER, [ind("a")], [ind("b")], validate=True)
    assert "SELECT ?class" in query
    assert "GROUP BY ?class" in query
    parseQuery(query)


def test_as_class_query_with_filter_expression():
    gen = new_generator()
    query = gen.as_class_query(
        CONTEXT_POSITION_MARKER, [ind("a")], [ind("b")], filter_expression=Male, validate=True
    )
    assert "FILTER NOT EXISTS" in query
    parseQuery(query)


def test_as_class_query_with_union_marker_uses_binding_subquery():
    gen = new_generator()
    context = OWLObjectUnionOf([Person, CONTEXT_POSITION_MARKER])
    query = gen.as_class_query(context, [ind("a")], [ind("b")], validate=True)
    assert "SELECT DISTINCT ?class" in query
    parseQuery(query)


def test_as_class_query_with_union_marker_and_filter_expression():
    gen = new_generator()
    context = OWLObjectUnionOf([Person, CONTEXT_POSITION_MARKER])
    query = gen.as_class_query(
        context, [ind("a")], [ind("b")], filter_expression=Male, validate=True
    )
    assert "FILTER NOT EXISTS" in query
    parseQuery(query)


def test_as_class_query_with_union_marker_and_named_individuals():
    gen = new_generator()
    context = OWLObjectUnionOf([Person, CONTEXT_POSITION_MARKER])
    query = gen.as_class_query(
        context, [ind("a")], [ind("b")], named_individuals=True, validate=True
    )
    assert "NamedIndividual" in query
    parseQuery(query)


def test_as_negated_class_query_root_marker():
    gen = new_generator()
    query = gen.as_negated_class_query(CONTEXT_POSITION_MARKER, [ind("a")], [ind("b")], validate=True)
    assert "UNION" in query
    assert "FILTER NOT EXISTS" in query
    parseQuery(query)


def test_as_negated_class_query_with_filter_expression():
    gen = new_generator()
    query = gen.as_negated_class_query(
        CONTEXT_POSITION_MARKER, [ind("a")], [ind("b")], filter_expression=Male, validate=True
    )
    parseQuery(query)


def test_as_property_query_not_inverted():
    gen = new_generator()
    query = gen.as_property_query(CONTEXT_POSITION_MARKER, [ind("a")], [ind("b")], validate=True)
    assert "SELECT ?prop" in query
    parseQuery(query)


def test_as_property_query_inverted():
    gen = new_generator()
    query = gen.as_property_query(CONTEXT_POSITION_MARKER, [ind("a")], [ind("b")], inverted=True, validate=True)
    parseQuery(query)


def test_as_property_query_with_filter_expression():
    gen = new_generator()
    query = gen.as_property_query(
        CONTEXT_POSITION_MARKER, [ind("a")], [ind("b")], filter_expression=Male, validate=True
    )
    assert "FILTER NOT EXISTS" in query
    parseQuery(query)


def test_as_property_query_with_union_marker_uses_binding_subquery():
    gen = new_generator()
    context = OWLObjectUnionOf([Person, CONTEXT_POSITION_MARKER])
    query = gen.as_property_query(context, [ind("a")], [ind("b")], validate=True)
    assert "SELECT DISTINCT ?prop" in query
    parseQuery(query)


def test_as_property_query_with_union_marker_and_filter_expression():
    gen = new_generator()
    context = OWLObjectUnionOf([Person, CONTEXT_POSITION_MARKER])
    query = gen.as_property_query(
        context, [ind("a")], [ind("b")], filter_expression=Male, validate=True
    )
    parseQuery(query)


# ---------------------------------------------------------------------------
# Module-level convenience functions (thin wrappers around the singleton)
# ---------------------------------------------------------------------------

def test_owl_expression_to_class_query_convenience_function():
    query = owl_expression_to_class_query(CONTEXT_POSITION_MARKER, [ind("a")], [ind("b")], validate=True)
    assert "SELECT ?class" in query


def test_owl_expression_to_property_query_convenience_function():
    query = owl_expression_to_property_query(CONTEXT_POSITION_MARKER, [ind("a")], [ind("b")], validate=True)
    assert "SELECT ?prop" in query


def test_owl_expression_to_negated_class_query_convenience_function():
    query = owl_expression_to_negated_class_query(CONTEXT_POSITION_MARKER, [ind("a")], [ind("b")], validate=True)
    assert "SELECT ?class" in query
