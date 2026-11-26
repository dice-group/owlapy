"""RDFLibReasoner.instances(engine="index") returns what engine="sparql" returns (#310, 2.1).

The "index" engine evaluates class expressions with set operations over indexes of the graph; the
"sparql" engine runs owl_expression_to_sparql's query. Every test compares the two engines on the
same reasoner.
"""
import random

import pytest
from rdflib import OWL, URIRef

from owlapy import dl_to_owl_expression
from owlapy.class_expression import (
    OWLClass,
    OWLDataAllValuesFrom,
    OWLDataExactCardinality,
    OWLDataHasValue,
    OWLDataMaxCardinality,
    OWLDataMinCardinality,
    OWLDataSomeValuesFrom,
    OWLNothing,
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
    OWLThing,
)
from owlapy.owl_axiom import (
    OWLClassAssertionAxiom,
    OWLDataPropertyAssertionAxiom,
    OWLDeclarationAxiom,
    OWLObjectPropertyAssertionAxiom,
    OWLSubClassOfAxiom,
    OWLSubObjectPropertyOfAxiom,
)
from owlapy.owl_data_ranges import OWLDataComplementOf, OWLDataUnionOf
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import BooleanOWLDatatype, DoubleOWLDatatype, IntegerOWLDatatype, OWLLiteral, StringOWLDatatype
from owlapy.owl_ontology import RDFLibOntology
from owlapy.owl_property import OWLDataProperty, OWLObjectInverseOf, OWLObjectProperty
from owlapy.owl_reasoner_rdflib import RDFLibReasoner
from owlapy.providers import owl_datatype_max_inclusive_restriction, owl_datatype_min_exclusive_restriction

NS = "http://example.com/engine#"
A, B, C, D = (OWLClass(NS + n) for n in "ABCD")
r, s, sub_r, r_inv, unused = (OWLObjectProperty(NS + n) for n in ("r", "s", "subR", "rInv", "unused"))
age, name = OWLDataProperty(NS + "age"), OWLDataProperty(NS + "name")
a, b, c, d, e, f = (OWLNamedIndividual(NS + n) for n in "abcdef")
CLASSES = [A, B, C, D, OWLThing, OWLNothing]
PROPERTIES = [r, s, sub_r, r_inv, unused]
INDIVIDUALS = [a, b, c, d, e, f]
LITERALS = [OWLLiteral(3), OWLLiteral(7), OWLLiteral(1.5), OWLLiteral("x"), OWLLiteral(True)]


@pytest.fixture(scope="module")
def ontology():
    onto = RDFLibOntology("http://example.com/engine", load=False)
    onto.add_axiom([
        *(OWLDeclarationAxiom(x) for x in [A, B, C, D, *PROPERTIES, age, name, *INDIVIDUALS]),
        OWLSubClassOfAxiom(B, A),  # f is typed only at the subclass B
        OWLSubObjectPropertyOfAxiom(sub_r, r),
        OWLClassAssertionAxiom(a, A), OWLClassAssertionAxiom(b, C), OWLClassAssertionAxiom(c, C),
        OWLClassAssertionAxiom(c, D), OWLClassAssertionAxiom(f, B),
        OWLObjectPropertyAssertionAxiom(a, r, b), OWLObjectPropertyAssertionAxiom(a, r, c),
        OWLObjectPropertyAssertionAxiom(b, sub_r, d),  # r only via the sub-property
        OWLObjectPropertyAssertionAxiom(e, r_inv, a),  # a r e only via the inverse
        OWLObjectPropertyAssertionAxiom(c, s, c),  # self loop
        OWLObjectPropertyAssertionAxiom(d, s, a), OWLObjectPropertyAssertionAxiom(d, s, f),
        OWLDataPropertyAssertionAxiom(a, age, OWLLiteral(3)), OWLDataPropertyAssertionAxiom(a, age, OWLLiteral(7)),
        OWLDataPropertyAssertionAxiom(b, age, OWLLiteral(1.5)), OWLDataPropertyAssertionAxiom(c, name, OWLLiteral("x")),
        OWLDataPropertyAssertionAxiom(d, name, OWLLiteral(True)), OWLDataPropertyAssertionAxiom(e, age, OWLLiteral(7)),
    ])
    # RDFLibOntology.add_axiom() doesn't write OWLInverseObjectPropertiesAxiom yet
    onto.rdflib_graph.add((URIRef(r.str), OWL.inverseOf, URIRef(r_inv.str)))
    return onto


def _random_expression(rng: random.Random, depth: int):
    if depth == 0 or rng.random() < 0.2:
        return rng.choice(CLASSES)

    def prop():
        p = rng.choice(PROPERTIES)
        return OWLObjectInverseOf(p) if rng.random() < 0.3 else p

    def data_range():
        return rng.choice([DoubleOWLDatatype, IntegerOWLDatatype, BooleanOWLDatatype, StringOWLDatatype,
                           owl_datatype_min_exclusive_restriction(rng.choice([2, 5])), owl_datatype_max_inclusive_restriction(3),
                           OWLDataComplementOf(IntegerOWLDatatype), OWLDataUnionOf([BooleanOWLDatatype, StringOWLDatatype])])

    sub = lambda: _random_expression(rng, depth - 1)  # noqa: E731
    dp = rng.choice([age, name])
    return rng.choice([
        lambda: OWLObjectIntersectionOf([sub(), sub()]),
        lambda: OWLObjectUnionOf([sub(), sub()]),
        lambda: OWLObjectComplementOf(sub()),
        lambda: OWLObjectSomeValuesFrom(prop(), sub()),
        lambda: OWLObjectAllValuesFrom(prop(), sub()),
        lambda: rng.choice([OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality])(rng.randrange(3), prop(), sub()),
        lambda: OWLObjectHasValue(prop(), rng.choice(INDIVIDUALS)),
        lambda: OWLObjectOneOf(rng.sample(INDIVIDUALS, rng.randrange(1, 3))),
        lambda: OWLObjectHasSelf(rng.choice(PROPERTIES)),
        lambda: OWLDataSomeValuesFrom(dp, data_range()),
        lambda: OWLDataAllValuesFrom(dp, data_range()),
        lambda: OWLDataHasValue(dp, rng.choice(LITERALS)),
        lambda: rng.choice([OWLDataMinCardinality, OWLDataMaxCardinality, OWLDataExactCardinality])(rng.randrange(3), dp, data_range()),
    ])()


def _assert_same(reasoner, expression):
    index = set(reasoner.instances(expression, engine="index"))
    sparql = set(reasoner.instances(expression, engine="sparql"))
    assert index == sparql, expression


@pytest.mark.parametrize("flags", [{}, {"negation_default": False}, {"sub_properties": True},
                                   {"negation_default": False, "sub_properties": True}],
                         ids=["default", "open_world", "sub_properties", "open_world_sub_properties"])
def test_random_expressions_match_sparql(ontology, flags):
    reasoner = RDFLibReasoner(ontology, **flags)
    rng = random.Random(310)
    for _ in range(300):
        _assert_same(reasoner, _random_expression(rng, rng.choice([1, 2, 3])))


def test_the_ontology_exercises_the_resolvers(ontology):
    reasoner = RDFLibReasoner(ontology, sub_properties=True)
    assert set(reasoner.instances(OWLObjectSomeValuesFrom(r, OWLObjectOneOf([e])))) == {a}  # via rInv
    assert set(reasoner.instances(OWLObjectSomeValuesFrom(r, OWLObjectOneOf([d])))) == {b}  # via subR
    assert set(reasoner.instances(OWLObjectSomeValuesFrom(s, A))) == {d}  # f is an A via B
    assert set(reasoner.instances(OWLObjectHasSelf(s))) == {c}


FAMILY_EXPRESSIONS = ["(¬Parent)", "∀ hasParent.Father", "∃ hasSibling.Daughter", "∃ hasChild.(¬Parent)", "≥ 1 married.Male",
                      "≤ 3 hasChild.Person", "Brother ⊓ Parent", "Mother ⊔ Father", "∃ hasParent.{F9M170 ⊔ F9M147 ⊔ F7M128}",
                      "= 2 hasChild.Female", "∃ hasChild.(∃ hasChild.Parent)", "Female ⊓ (∃ hasSibling.Parent)"]


@pytest.fixture(scope="module")
def family():
    return RDFLibReasoner("KGs/Family/family-benchmark_rich_background.owl")


@pytest.mark.parametrize("dl", FAMILY_EXPRESSIONS)
def test_family_benchmark_expressions_match_sparql(family, dl):
    _assert_same(family, dl_to_owl_expression(dl_expression=dl, namespace="http://www.benchmark.org/family#"))


def test_engine_defaults_to_index_and_is_selectable(ontology):
    expression = OWLObjectSomeValuesFrom(r, C)
    sparql_reasoner = RDFLibReasoner(ontology, engine="sparql")
    assert set(sparql_reasoner.instances(expression)) == {a}
    assert sparql_reasoner._index is None  # the index is never built
    assert set(sparql_reasoner.instances(expression, engine="index")) == {a}
    assert sparql_reasoner._index is not None
    index_reasoner = RDFLibReasoner(ontology)
    assert set(index_reasoner.instances(expression)) == {a}
    assert index_reasoner._index is not None


@pytest.mark.parametrize("engine", ["Index", "owlready2", None])
def test_unknown_engine_raises(ontology, engine):
    if engine is not None:
        with pytest.raises(ValueError, match="engine must be one of"):
            RDFLibReasoner(ontology, engine=engine)
    with pytest.raises(ValueError, match="engine must be one of"):
        RDFLibReasoner(ontology).instances(A, engine=engine or "spaqrl")


def test_index_follows_graph_changes():
    onto = RDFLibOntology("http://example.com/engine-mutation", load=False)
    onto.add_axiom([OWLDeclarationAxiom(x) for x in (A, r, a, b)] + [OWLClassAssertionAxiom(b, A)])
    reasoner = RDFLibReasoner(onto)
    expression = OWLObjectSomeValuesFrom(r, A)
    assert not set(reasoner.instances(expression))
    onto.add_axiom(OWLObjectPropertyAssertionAxiom(a, r, b))  # the graph grew: the index is rebuilt
    assert set(reasoner.instances(expression)) == {a}
    onto.remove_axiom(OWLObjectPropertyAssertionAxiom(a, r, b))
    reasoner.flush()
    assert not set(reasoner.instances(expression))



# The converter used to rely on the root `?x a owl:NamedIndividual` to bind ?x for a top-level data
# allValuesFrom. A UNION branch doesn't see the root's bindings, so FILTER NOT EXISTS ran over an
# unbound ?x and dropped the whole branch. A complement inside a top-level intersection also relies on
# it, but rdflib passes the outer bindings into that branch; the second test guards that case.
@pytest.mark.parametrize("engine", ["index", "sparql"])
def test_union_branch_with_data_all_values_from(ontology, engine):
    reasoner = RDFLibReasoner(ontology)
    all_ints = OWLDataAllValuesFrom(age, IntegerOWLDatatype)
    assert set(reasoner.instances(all_ints, engine=engine)) == {a, c, d, e, f}
    assert set(reasoner.instances(OWLObjectUnionOf([C, all_ints]), engine=engine)) == {a, b, c, d, e, f}


@pytest.mark.parametrize("engine", ["index", "sparql"])
def test_union_branch_with_complements_in_an_intersection(ontology, engine):
    reasoner = RDFLibReasoner(ontology)
    neither = OWLObjectIntersectionOf([OWLObjectComplementOf(A), OWLObjectComplementOf(D)])
    assert set(reasoner.instances(neither, engine=engine)) == {b, d, e}
    assert set(reasoner.instances(OWLObjectUnionOf([neither, OWLObjectOneOf([a])]), engine=engine)) == {a, b, d, e}


@pytest.mark.parametrize("engine", [
    "index",
    pytest.param("sparql", marks=pytest.mark.xfail(strict=True, reason=(
        "rdflib evaluates FILTER NOT EXISTS { { ... } UNION { ... } } as if ?x weren't bound inside the UNION, "
        "so ¬(¬X ⊔ ¬Y) returns every individual (the generated query is correct)"))),
])
def test_complement_of_a_union_of_complements(ontology, engine):
    reasoner = RDFLibReasoner(ontology)
    for x, y, expected in ((C, D, {c}), (A, B, {f}), (A, C, set())):
        ce = OWLObjectComplementOf(OWLObjectUnionOf([OWLObjectComplementOf(x), OWLObjectComplementOf(y)]))
        assert set(reasoner.instances(ce, engine=engine)) == expected


@pytest.mark.parametrize("sub_properties", [False, True])
def test_object_property_values_match_sparql(ontology, sub_properties):
    index = RDFLibReasoner(ontology, sub_properties=sub_properties)
    sparql = RDFLibReasoner(ontology, sub_properties=sub_properties, engine="sparql")
    for individual in INDIVIDUALS:
        for prop in PROPERTIES:
            for pe in (prop, OWLObjectInverseOf(prop)):
                assert set(index.object_property_values(individual, pe)) == set(sparql.object_property_values(individual, pe)), (individual, pe)
    assert set(index.object_property_values(a, r)) == {b, c, e}  # e via rInv; never d via the sub-property subR


# IMPROVEMENTS.md 4.4 listed ∃p.C ≢ ¬∀p.¬C for individuals without p-values as an open gap. It no
# longer reproduces on either engine; these pin the De Morgan equivalence with expected answers.
@pytest.mark.parametrize("engine", ["index", "sparql"])
@pytest.mark.parametrize("data_range, expected", [
    (IntegerOWLDatatype, {a, e}),
    (DoubleOWLDatatype, {b}),
    (OWLDataComplementOf(IntegerOWLDatatype), {b}),
    (OWLDataUnionOf([IntegerOWLDatatype, DoubleOWLDatatype]), {a, b, e}),
    (owl_datatype_max_inclusive_restriction(3), {a}),
], ids=["int", "double", "not-int", "int-or-double", "le-3"])
def test_data_some_values_from_equals_not_all_values_from_not(ontology, engine, data_range, expected):
    reasoner = RDFLibReasoner(ontology, engine=engine)
    some = OWLDataSomeValuesFrom(age, data_range)
    not_all_not = OWLObjectComplementOf(OWLDataAllValuesFrom(age, OWLDataComplementOf(data_range)))
    assert set(reasoner.instances(some)) == expected
    assert set(reasoner.instances(not_all_not)) == expected  # c, d, f have no age value at all


# The SPARQL engine special-cases ≤n only at the top level (_at_most_cardinality_instances); nested
# inside an intersection it goes through the generic query, the index engine through set operations.
@pytest.mark.parametrize("engine", ["index", "sparql"])
@pytest.mark.parametrize("expression, expected", [
    (OWLObjectIntersectionOf([A, OWLObjectMaxCardinality(0, r, OWLThing)]), {f}),
    (OWLObjectIntersectionOf([C, OWLObjectMaxCardinality(0, s, OWLThing)]), {b}),
    (OWLObjectUnionOf([OWLObjectOneOf([a]), OWLObjectExactCardinality(0, r, OWLThing)]), {a, b, c, d, e, f}),
    (OWLObjectIntersectionOf([OWLThing, OWLObjectMaxCardinality(1, s, OWLThing)]), {a, b, c, e, f}),
], ids=["A-and-no-r", "C-and-no-s", "union-with-exactly-0", "at-most-1-s"])
def test_nested_at_most_cardinality(ontology, engine, expression, expected):
    assert set(RDFLibReasoner(ontology, engine=engine).instances(expression)) == expected


@pytest.mark.parametrize("name", ["infer_property_values", "infer_data_property_values"])
@pytest.mark.parametrize("value", [False, True])
def test_unused_inference_flags_are_deprecated(ontology, name, value):
    with pytest.warns(DeprecationWarning, match=name):
        reasoner = RDFLibReasoner(ontology, **{name: value})
    assert set(reasoner.instances(OWLObjectSomeValuesFrom(r, OWLThing))) == {a}  # the flag changes nothing


def test_no_deprecation_warning_by_default(ontology, recwarn):
    RDFLibReasoner(ontology)
    assert not [w for w in recwarn if issubclass(w.category, DeprecationWarning) and "infer_" in str(w.message)]
