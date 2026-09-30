import pytest
from rdflib import OWL, RDF, RDFS, XSD, Graph, Literal, Namespace

from owlapy import RDFLibReasoner, owl_expression_to_sparql
from owlapy.class_expression import (
    OWLClass,
    OWLDataExactCardinality,
    OWLDataMaxCardinality,
    OWLDataMinCardinality,
    OWLDataOneOf,
    OWLObjectExactCardinality,
    OWLObjectMaxCardinality,
    OWLObjectMinCardinality,
    OWLObjectSomeValuesFrom,
    OWLObjectUnionOf,
)
from owlapy.owl_data_ranges import OWLDataUnionOf
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral, StringOWLDatatype
from owlapy.owl_ontology import Ontology
from owlapy.owl_property import OWLDataProperty, OWLObjectInverseOf, OWLObjectProperty
from owlapy.owl_reasoner import StructuralReasoner

EX = Namespace("http://example.org/cardinality#")
SUBJECTS = {"empty", "one", "two", "wrong"}
CASES = [
    ("min", 0, SUBJECTS),
    ("min", 1, {"one", "two"}),
    ("min", 2, {"two"}),
    ("min", 3, set()),
    ("max", 0, {"empty", "wrong"}),
    ("max", 1, {"empty", "one", "wrong"}),
    ("max", 2, SUBJECTS),
    ("exact", 0, {"empty", "wrong"}),
    ("exact", 1, {"one"}),
    ("exact", 2, {"two"}),
]


@pytest.fixture
def graph():
    graph = Graph()
    for name in SUBJECTS | {"target1", "target2", "other"}:
        graph.add((EX[name], RDF.type, OWL.NamedIndividual))
    for cls in (EX.C, EX.D, EX.E):
        graph.add((cls, RDF.type, OWL.Class))
    graph.add((EX.D, RDFS.subClassOf, EX.C))
    graph.add((EX.p, RDF.type, OWL.ObjectProperty))
    graph.add((EX.data, RDF.type, OWL.DatatypeProperty))
    for target in (EX.target1, EX.target2):
        for cls in (EX.C, EX.D):
            graph.add((target, RDF.type, cls))
    graph.add((EX.other, RDF.type, EX.E))
    for subject, target in ((EX.one, EX.target1), (EX.two, EX.target1),
                            (EX.two, EX.target2), (EX.wrong, EX.other)):
        graph.add((subject, EX.p, target))
    for subject, value in ((EX.one, "yes"), (EX.two, "yes"), (EX.two, "also"), (EX.wrong, 7)):
        literal = Literal(value, datatype=XSD.string) if isinstance(value, str) else Literal(value)
        graph.add((subject, EX.data, literal))
    return graph


def retrieve(graph, expression, backend, tmp_path):
    if backend == "converter":
        values = [OWLNamedIndividual(str(EX[name])) for name in SUBJECTS | {"wrapper"}]
        query = owl_expression_to_sparql(
            expression, values=values, named_individuals=True, validate=True,
            subclass_resolver=lambda cls: [OWLClass(str(EX.D))] if cls.str == str(EX.C) else [],
        )
        return {str(row[0]).split("#")[-1] for row in graph.query(query)}
    path = str(tmp_path / "ontology.owl")
    graph.serialize(path, format="xml")
    if backend == "rdflib":
        reasoner = RDFLibReasoner(path)
    else:
        reasoner = StructuralReasoner(Ontology(path), property_cache=backend == "structural_cached")
    return {individual.remainder for individual in reasoner.instances(expression)}


@pytest.mark.parametrize("backend", ["converter", "rdflib"])
@pytest.mark.parametrize("inverse", [False, True])
@pytest.mark.parametrize("kind, cardinality, expected", CASES)
def test_object_cardinality_counts_distinct_targets(graph, tmp_path, backend, inverse, kind, cardinality, expected):
    prop = OWLObjectProperty(str(EX.p))
    if inverse:
        for subject, _, target in list(graph.triples((None, EX.p, None))):
            graph.remove((subject, EX.p, target))
            graph.add((target, EX.p, subject))
        prop = OWLObjectInverseOf(prop)
    filler = OWLObjectUnionOf([OWLClass(str(EX.C)), OWLClass(str(EX.D))])
    restriction = {"min": OWLObjectMinCardinality, "max": OWLObjectMaxCardinality, "exact": OWLObjectExactCardinality}[kind]
    expression = restriction(cardinality, prop, filler)
    assert retrieve(graph, expression, backend, tmp_path) & SUBJECTS == expected


@pytest.mark.parametrize("backend", ["converter", "rdflib", "structural_cached", "structural_uncached"])
@pytest.mark.parametrize("filler", [
    StringOWLDatatype,
    OWLDataOneOf([OWLLiteral("yes"), OWLLiteral("also")]),
    OWLDataUnionOf([StringOWLDatatype, OWLDataOneOf(OWLLiteral("yes"))]),
])
@pytest.mark.parametrize("kind, cardinality, expected", CASES)
def test_data_cardinality_includes_zero_matches(graph, tmp_path, backend, filler, kind, cardinality, expected):
    restriction = {"min": OWLDataMinCardinality, "max": OWLDataMaxCardinality, "exact": OWLDataExactCardinality}[kind]
    expression = restriction(cardinality, OWLDataProperty(str(EX.data)), filler)
    assert retrieve(graph, expression, backend, tmp_path) & SUBJECTS == expected


@pytest.mark.parametrize("backend", ["converter", "rdflib"])
@pytest.mark.parametrize("restriction", [OWLDataMaxCardinality, OWLDataExactCardinality])
def test_nested_zero_cardinality_matches_missing_values(graph, tmp_path, backend, restriction):
    graph.add((EX.wrapper, RDF.type, OWL.NamedIndividual))
    graph.add((EX.wrapper, EX.link, EX.empty))
    expression = OWLObjectSomeValuesFrom(
        OWLObjectProperty(str(EX.link)), restriction(0, OWLDataProperty(str(EX.data)), StringOWLDatatype),
    )
    assert retrieve(graph, expression, backend, tmp_path) == {"wrapper"}
