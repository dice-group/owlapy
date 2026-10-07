import pytest
from rdflib import OWL, RDF, XSD, Graph, Literal, Namespace

from owlapy import RDFLibReasoner, owl_expression_to_sparql
from owlapy.class_expression import (
    OWLDataAllValuesFrom,
    OWLDataOneOf,
    OWLDataSomeValuesFrom,
    OWLDatatypeRestriction,
    OWLFacetRestriction,
    OWLObjectComplementOf,
    OWLObjectSomeValuesFrom,
)
from owlapy.owl_data_ranges import OWLDataComplementOf, OWLDataUnionOf
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_literal import IntegerOWLDatatype, OWLLiteral, StringOWLDatatype
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty
from owlapy.vocab import OWLFacet

EX = Namespace("http://example.org/")
P = OWLDataProperty(str(EX.p))


def retrieve(graph, expression, backend, tmp_path):
    if backend == "converter":
        query = owl_expression_to_sparql(expression, named_individuals=True, validate=True)
        return {str(row[0]).removeprefix(str(EX)) for row in graph.query(query)}
    path = tmp_path / "ontology.ttl"
    graph.serialize(path, format="turtle")
    return {individual.remainder for individual in RDFLibReasoner(str(path)).instances(expression)}


@pytest.fixture
def strings():
    graph = Graph()
    for name in ("missing", "empty", "short", "long", "unicode", "number", "mixed"):
        graph.add((EX[name], RDF.type, OWL.NamedIndividual))
    for name, value in (("empty", ""), ("short", "x"), ("long", "abc"), ("unicode", "🙂🙂"), ("mixed", "abc")):
        graph.add((EX[name], EX.p, Literal(value, datatype=XSD.string)))
    for name in ("number", "mixed"):
        graph.add((EX[name], EX.p, Literal(1)))
    return graph


@pytest.mark.parametrize("backend", ["converter", "rdflib"])
@pytest.mark.parametrize("filler, expected", [
    (StringOWLDatatype, {"missing", "empty", "short", "long", "unicode"}),
    (OWLDataComplementOf(StringOWLDatatype), {"missing", "number"}),
    (OWLDataOneOf([OWLLiteral(""), OWLLiteral("abc")]), {"missing", "empty", "long"}),
    (OWLDataUnionOf([StringOWLDatatype, IntegerOWLDatatype]), {"missing", "empty", "short", "long", "unicode", "number", "mixed"}),
])
def test_data_universal_includes_missing_values_and_rejects_any_violation(strings, tmp_path, backend, filler, expected):
    assert retrieve(strings, OWLDataAllValuesFrom(P, filler), backend, tmp_path) == expected


@pytest.mark.parametrize("backend", ["converter", "rdflib"])
def test_data_universal_obeys_de_morgan_with_missing_values(strings, tmp_path, backend):
    expression = OWLObjectComplementOf(OWLDataAllValuesFrom(P, OWLDataComplementOf(StringOWLDatatype)))
    assert retrieve(strings, expression, backend, tmp_path) == {"empty", "short", "long", "unicode", "mixed"}


@pytest.mark.parametrize("backend", ["converter", "rdflib"])
def test_data_universal_works_as_nested_filler(strings, tmp_path, backend):
    strings.add((EX.wrapper, RDF.type, OWL.NamedIndividual))
    strings.add((EX.wrapper, EX.link, EX.missing))
    expression = OWLObjectSomeValuesFrom(OWLObjectProperty(str(EX.link)), OWLDataAllValuesFrom(P, StringOWLDatatype))
    assert retrieve(strings, expression, backend, tmp_path) == {"wrapper"}


@pytest.mark.parametrize("backend", ["converter", "rdflib"])
@pytest.mark.parametrize("facet, bound, expected", [
    (OWLFacet.LENGTH, 0, {"empty"}),
    (OWLFacet.MIN_LENGTH, 3, {"long", "mixed"}),
    (OWLFacet.MAX_LENGTH, 1, {"empty", "short"}),
    (OWLFacet.LENGTH, 2, {"unicode"}),
])
def test_length_facets_constrain_string_values(strings, tmp_path, backend, facet, bound, expected):
    filler = OWLDatatypeRestriction(StringOWLDatatype, OWLFacetRestriction(facet, OWLLiteral(bound)))
    assert retrieve(strings, OWLDataSomeValuesFrom(P, filler), backend, tmp_path) == expected


@pytest.mark.parametrize("backend", ["converter", "rdflib"])
@pytest.mark.parametrize("facet, value", [
    (OWLFacet.PATTERN, "[a-z]+"), (OWLFacet.TOTAL_DIGITS, 3), (OWLFacet.FRACTION_DIGITS, 1),
])
def test_unsupported_facets_raise_instead_of_returning_unfiltered_results(strings, tmp_path, backend, facet, value):
    filler = OWLDatatypeRestriction(StringOWLDatatype, OWLFacetRestriction(facet, OWLLiteral(value)))
    with pytest.raises(NotImplementedError, match=facet.symbolic_form):
        retrieve(strings, OWLDataSomeValuesFrom(P, filler), backend, tmp_path)


@pytest.mark.parametrize("backend", ["converter", "rdflib"])
@pytest.mark.parametrize("datatype, expected", [
    (XSD.integer, {"integer", "int", "decimal_integral", "large"}),
    (XSD.decimal, {"integer", "int", "decimal_integral", "decimal_fraction", "large"}),
    (XSD.int, {"integer", "int", "decimal_integral"}),
])
def test_numeric_restrictions_use_value_spaces_and_exclude_float_types(tmp_path, backend, datatype, expected):
    graph = Graph()
    for name, value, source_type in [
        ("integer", "10", XSD.integer), ("int", "10", XSD.int),
        ("decimal_integral", "10.0", XSD.decimal), ("decimal_fraction", "10.5", XSD.decimal),
        ("double", "10", XSD.double), ("float", "10", XSD.float),
        ("large", str(2**40), XSD.integer), ("small", "1", XSD.integer), ("string", "10", XSD.string),
    ]:
        graph.add((EX[name], RDF.type, OWL.NamedIndividual))
        graph.add((EX[name], EX.p, Literal(value, datatype=source_type)))
    filler = OWLDatatypeRestriction(OWLDatatype(str(datatype)), OWLFacetRestriction(OWLFacet.MIN_INCLUSIVE, OWLLiteral(5)))
    assert retrieve(graph, OWLDataSomeValuesFrom(P, filler), backend, tmp_path) == expected


@pytest.mark.parametrize("backend", ["converter", "rdflib"])
def test_enumerations_keep_float_and_decimal_value_spaces_disjoint(tmp_path, backend):
    graph = Graph()
    for name, datatype in [("integer", XSD.integer), ("int", XSD.int), ("decimal", XSD.decimal), ("double", XSD.double), ("float", XSD.float)]:
        graph.add((EX[name], RDF.type, OWL.NamedIndividual))
        graph.add((EX[name], EX.p, Literal("10", datatype=datatype)))
    expression = OWLDataSomeValuesFrom(P, OWLDataOneOf(OWLLiteral(10)))
    assert retrieve(graph, expression, backend, tmp_path) == {"integer", "int", "decimal"}


@pytest.mark.parametrize("backend", ["converter", "rdflib"])
def test_string_length_restriction_accepts_string_subtypes(tmp_path, backend):
    graph = Graph()
    graph.add((EX.token, RDF.type, OWL.NamedIndividual))
    graph.add((EX.token, EX.p, Literal("abc", datatype=XSD.token)))
    filler = OWLDatatypeRestriction(StringOWLDatatype, OWLFacetRestriction(OWLFacet.LENGTH, OWLLiteral(3)))
    assert retrieve(graph, OWLDataSomeValuesFrom(P, filler), backend, tmp_path) == {"token"}


@pytest.mark.parametrize("backend", ["converter", "rdflib"])
def test_binary_lengths_are_not_evaluated_as_character_counts(strings, tmp_path, backend):
    filler = OWLDatatypeRestriction(OWLDatatype(str(XSD.hexBinary)), OWLFacetRestriction(OWLFacet.LENGTH, OWLLiteral(2)))
    with pytest.raises(NotImplementedError, match="length"):
        retrieve(strings, OWLDataSomeValuesFrom(P, filler), backend, tmp_path)
