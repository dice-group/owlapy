import pytest
from rdflib import XSD, Graph, Literal, Namespace

from owlapy import owl_expression_to_sparql
from owlapy.class_expression import OWLDataHasValue, OWLDataOneOf, OWLDataSomeValuesFrom
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_property import OWLDataProperty


@pytest.mark.parametrize("value", [
    'say "hello"', "line\nbreak", "carriage\rreturn", "tab\there", r"path\name",
    'three """ quotes', '" } UNION { ?x ?p ?o } #',
])
@pytest.mark.parametrize("enumeration", [False, True])
def test_literal_values_survive_sparql_conversion(value, enumeration):
    ex = Namespace("http://example.org/")
    graph = Graph()
    graph.add((ex.alice, ex.value, Literal(value, datatype=XSD.string)))
    graph.add((ex.bob, ex.value, Literal("different", datatype=XSD.string)))
    prop = OWLDataProperty(str(ex.value))
    literal = OWLLiteral(value)
    expression = OWLDataSomeValuesFrom(prop, OWLDataOneOf(literal)) if enumeration else OWLDataHasValue(prop, literal)
    query = owl_expression_to_sparql(expression, validate=True)
    assert {row[0] for row in graph.query(query)} == {ex.alice}
