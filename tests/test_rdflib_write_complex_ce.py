"""RDFLibOntology.add_axiom() writing complex class expressions / data ranges (#310, 1.2b).

The OWL API is the test oracle: every axiom is written with RDFLibOntology, saved, and read back
through SyncOntology, which must report exactly the axiom we wrote.
"""

import pytest
from rdflib import OWL, RDF, BNode, URIRef

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
    OWLThing,
)
from owlapy.owl_axiom import (
    OWLClassAssertionAxiom,
    OWLDataPropertyDomainAxiom,
    OWLDataPropertyRangeAxiom,
    OWLDisjointClassesAxiom,
    OWLEquivalentClassesAxiom,
    OWLObjectPropertyDomainAxiom,
    OWLObjectPropertyRangeAxiom,
    OWLSubClassOfAxiom,
)
from owlapy.owl_data_ranges import OWLDataComplementOf, OWLDataIntersectionOf, OWLDataUnionOf
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import DoubleOWLDatatype, IntegerOWLDatatype, OWLLiteral, StringOWLDatatype, TopOWLDatatype
from owlapy.owl_ontology import RDFLibOntology, SyncOntology
from owlapy.owl_property import OWLDataProperty, OWLObjectInverseOf, OWLObjectProperty
from owlapy.vocab import OWLFacet

NS = "http://example.com/complex#"
ONTOLOGY_IRI = "http://example.com/complex"

A, B, C = OWLClass(NS + "A"), OWLClass(NS + "B"), OWLClass(NS + "C")
r, s = OWLObjectProperty(NS + "r"), OWLObjectProperty(NS + "s")
age, name = OWLDataProperty(NS + "age"), OWLDataProperty(NS + "name")
a, b = OWLNamedIndividual(NS + "a"), OWLNamedIndividual(NS + "b")

# One facet only: OWLDatatypeRestriction equality is order-sensitive and the OWL API does not keep
# facet order (see test_datatype_restriction_with_several_facets).
int_range = OWLDatatypeRestriction(IntegerOWLDatatype, OWLFacetRestriction(OWLFacet.MIN_INCLUSIVE, 18))

CLASS_EXPRESSIONS = {
    "intersection": OWLObjectIntersectionOf([A, B]),
    "union": OWLObjectUnionOf([A, B, C]),
    "complement": OWLObjectComplementOf(A),
    "nominal": OWLObjectOneOf([a, b]),
    "some": OWLObjectSomeValuesFrom(r, B),
    "all": OWLObjectAllValuesFrom(r, OWLObjectUnionOf([B, C])),
    "has_value": OWLObjectHasValue(r, b),
    "has_self": OWLObjectHasSelf(r),
    "inverse": OWLObjectSomeValuesFrom(OWLObjectInverseOf(r), A),
    "min_qualified": OWLObjectMinCardinality(2, r, B),
    "max_qualified": OWLObjectMaxCardinality(3, r, OWLObjectComplementOf(B)),
    "exact_qualified": OWLObjectExactCardinality(1, s, C),
    "min_unqualified": OWLObjectMinCardinality(1, r, OWLThing),
    "exact_unqualified": OWLObjectExactCardinality(2, s, OWLThing),
    "nested": OWLObjectIntersectionOf([A, OWLObjectSomeValuesFrom(r, OWLObjectAllValuesFrom(s, OWLObjectComplementOf(C)))]),
    "data_some": OWLDataSomeValuesFrom(age, int_range),
    "data_all": OWLDataAllValuesFrom(name, StringOWLDatatype),
    "data_has_value": OWLDataHasValue(age, OWLLiteral(42)),
    "data_min": OWLDataMinCardinality(1, age, IntegerOWLDatatype),
    "data_max_unqualified": OWLDataMaxCardinality(1, age, TopOWLDatatype),
    "data_exact": OWLDataExactCardinality(1, name, StringOWLDatatype),
    "data_one_of": OWLDataSomeValuesFrom(name, OWLDataOneOf([OWLLiteral("x"), OWLLiteral("y")])),
    "data_union": OWLDataSomeValuesFrom(age, OWLDataUnionOf([IntegerOWLDatatype, DoubleOWLDatatype])),
    "data_intersection": OWLDataSomeValuesFrom(age, OWLDataIntersectionOf([IntegerOWLDatatype, int_range])),
    "data_complement": OWLDataSomeValuesFrom(age, OWLDataComplementOf(IntegerOWLDatatype)),
}


def _round_trip(tmp_path, axioms, fmt="rdfxml"):
    onto = RDFLibOntology(ONTOLOGY_IRI, load=False)
    onto.add_axiom(axioms)
    path = tmp_path / f"out.{'ttl' if fmt == 'ttl' else 'owl'}"
    onto.save(path=str(path), document_format=fmt)
    return set(SyncOntology(str(path)).get_axioms())


@pytest.mark.parametrize("ce", CLASS_EXPRESSIONS.values(), ids=CLASS_EXPRESSIONS.keys())
def test_sub_class_of_complex_super_class(tmp_path, ce):
    axiom = OWLSubClassOfAxiom(A, ce)
    assert axiom in _round_trip(tmp_path, [axiom])


@pytest.mark.parametrize("ce", CLASS_EXPRESSIONS.values(), ids=CLASS_EXPRESSIONS.keys())
def test_general_class_axiom(tmp_path, ce):
    axiom = OWLSubClassOfAxiom(ce, C)
    assert axiom in _round_trip(tmp_path, [axiom])


@pytest.mark.parametrize("ce", CLASS_EXPRESSIONS.values(), ids=CLASS_EXPRESSIONS.keys())
def test_class_assertion_with_complex_class(tmp_path, ce):
    axiom = OWLClassAssertionAxiom(a, ce)
    assert axiom in _round_trip(tmp_path, [axiom])


def test_turtle_round_trip(tmp_path):
    axioms = [OWLSubClassOfAxiom(A, ce) for ce in CLASS_EXPRESSIONS.values()]
    assert set(axioms) <= _round_trip(tmp_path, axioms, fmt="ttl")


def test_many_axioms_in_one_ontology(tmp_path):
    axioms = [OWLSubClassOfAxiom(A, ce) for ce in CLASS_EXPRESSIONS.values()]
    axioms += [OWLClassAssertionAxiom(b, ce) for ce in CLASS_EXPRESSIONS.values()]
    assert set(axioms) <= _round_trip(tmp_path, axioms)


def test_equivalent_classes_with_named_anchor(tmp_path):
    some, inter = CLASS_EXPRESSIONS["some"], CLASS_EXPRESSIONS["intersection"]
    read = _round_trip(tmp_path, [OWLEquivalentClassesAxiom([some, C, inter])])
    assert OWLEquivalentClassesAxiom([C, some]) in read
    assert OWLEquivalentClassesAxiom([C, inter]) in read


def test_equivalent_classes_all_complex(tmp_path):
    axiom = OWLEquivalentClassesAxiom([CLASS_EXPRESSIONS["some"], CLASS_EXPRESSIONS["union"]])
    assert axiom in _round_trip(tmp_path, [axiom])


def test_disjoint_classes_two_complex(tmp_path):
    axiom = OWLDisjointClassesAxiom([A, CLASS_EXPRESSIONS["some"]])
    assert axiom in _round_trip(tmp_path, [axiom])


def test_disjoint_classes_many_complex_uses_all_disjoint_classes(tmp_path):
    axiom = OWLDisjointClassesAxiom([A, CLASS_EXPRESSIONS["some"], CLASS_EXPRESSIONS["complement"]])
    assert axiom in _round_trip(tmp_path, [axiom])


def test_domain_and_range_with_complex_expressions(tmp_path):
    axioms = [
        OWLObjectPropertyDomainAxiom(r, CLASS_EXPRESSIONS["union"]),
        OWLObjectPropertyRangeAxiom(r, CLASS_EXPRESSIONS["some"]),
        OWLDataPropertyDomainAxiom(age, CLASS_EXPRESSIONS["intersection"]),
        OWLDataPropertyRangeAxiom(age, int_range),
        OWLDataPropertyRangeAxiom(name, OWLDataOneOf([OWLLiteral("x"), OWLLiteral("y")])),
    ]
    assert set(axioms) <= _round_trip(tmp_path, axioms)


def test_datatype_restriction_with_several_facets(tmp_path):
    facets = [OWLFacetRestriction(OWLFacet.MIN_INCLUSIVE, 18), OWLFacetRestriction(OWLFacet.MAX_EXCLUSIVE, 65)]
    axiom = OWLDataPropertyRangeAxiom(age, OWLDatatypeRestriction(IntegerOWLDatatype, facets))
    read = [ax for ax in _round_trip(tmp_path, [axiom]) if isinstance(ax, OWLDataPropertyRangeAxiom)]
    assert len(read) == 1
    restriction = read[0].get_range()
    assert restriction.get_datatype() == IntegerOWLDatatype
    assert set(restriction.get_facet_restrictions()) == set(facets)


def test_signature_entities_are_declared():
    onto = RDFLibOntology(ONTOLOGY_IRI, load=False)
    onto.add_axiom(OWLSubClassOfAxiom(A, CLASS_EXPRESSIONS["nested"]))
    onto.add_axiom(OWLSubClassOfAxiom(A, CLASS_EXPRESSIONS["has_value"]))
    onto.add_axiom(OWLSubClassOfAxiom(A, CLASS_EXPRESSIONS["data_some"]))
    assert {c.str for c in onto.classes_in_signature()} == {A.str, C.str}
    assert {p.str for p in onto.object_properties_in_signature()} == {r.str, s.str}
    assert {p.str for p in onto.data_properties_in_signature()} == {age.str}
    assert {i.str for i in onto.individuals_in_signature()} == {b.str}
    # owl:Thing is never declared as a local class
    onto.add_axiom(OWLSubClassOfAxiom(A, CLASS_EXPRESSIONS["min_unqualified"]))
    assert (URIRef(OWLThing.str), RDF.type, OWL.Class) not in onto.rdflib_graph


def test_each_occurrence_gets_its_own_blank_node():
    onto = RDFLibOntology(ONTOLOGY_IRI, load=False)
    some = CLASS_EXPRESSIONS["some"]
    onto.add_axiom([OWLSubClassOfAxiom(A, some), OWLSubClassOfAxiom(C, some)])
    supers = [o for o in onto.rdflib_graph.objects(None, URIRef("http://www.w3.org/2000/01/rdf-schema#subClassOf"))]
    assert len(supers) == 2 and all(isinstance(o, BNode) for o in supers) and supers[0] != supers[1]


def test_named_only_axioms_keep_their_plain_triples():
    onto = RDFLibOntology(ONTOLOGY_IRI, load=False)
    onto.add_axiom([OWLSubClassOfAxiom(A, B), OWLClassAssertionAxiom(a, A)])
    assert OWLSubClassOfAxiom(A, B) in onto.get_tbox_axioms()
    assert OWLClassAssertionAxiom(a, A) in onto.get_abox_axioms()


def test_complex_axioms_are_not_removable_yet():
    onto = RDFLibOntology(ONTOLOGY_IRI, load=False)
    axiom = OWLSubClassOfAxiom(A, CLASS_EXPRESSIONS["some"])
    onto.add_axiom(axiom)
    with pytest.raises(NotImplementedError):
        onto.remove_axiom(axiom)
