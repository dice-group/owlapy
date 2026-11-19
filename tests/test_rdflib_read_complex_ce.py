"""RDFLibOntology reading axioms with complex class expressions / data ranges (#310, 2.4).

Two oracles: what RDFLibOntology.add_axiom() wrote (round trip, in memory and through a file), and
the OWL API (SyncOntology) reading the same file.
"""

import logging
import os

import pytest

from owlapy.class_expression import OWLDataSomeValuesFrom, OWLObjectOneOf, OWLObjectSomeValuesFrom
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
from owlapy.owl_data_ranges import OWLDataUnionOf
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import IntegerOWLDatatype, OWLLiteral
from owlapy.owl_ontology import RDFLibOntology, SyncOntology
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty
from tests.test_rdflib_write_complex_ce import CLASS_EXPRESSIONS, NS, ONTOLOGY_IRI, A, B, C, a, age, int_range, name, r

CLASS_AXIOMS = (OWLSubClassOfAxiom, OWLEquivalentClassesAxiom, OWLDisjointClassesAxiom)
BIOPAX = "KGs/Biopax/biopax.owl"


def _written(axioms):
    onto = RDFLibOntology(ONTOLOGY_IRI, load=False)
    onto.add_axiom(axioms)
    return onto


def _reloaded(tmp_path, axioms, fmt="rdfxml"):
    path = tmp_path / f"out.{'ttl' if fmt == 'ttl' else 'owl'}"
    _written(axioms).save(path=str(path), document_format=fmt)
    return RDFLibOntology(str(path))


def _from_turtle(tmp_path, body):
    path = tmp_path / "in.ttl"
    path.write_text("@prefix : <" + NS + "> .\n@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
                    "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n"
                    "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
                    "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
                    ":A a owl:Class .\n" + body)
    return RDFLibOntology(str(path))


@pytest.mark.parametrize("ce", CLASS_EXPRESSIONS.values(), ids=CLASS_EXPRESSIONS.keys())
def test_tbox_round_trip_in_memory(ce):
    axioms = [OWLSubClassOfAxiom(A, ce), OWLSubClassOfAxiom(ce, C)]
    assert set(axioms) <= set(_written(axioms).get_tbox_axioms())


@pytest.mark.parametrize("ce", CLASS_EXPRESSIONS.values(), ids=CLASS_EXPRESSIONS.keys())
def test_tbox_round_trip_through_file(tmp_path, ce):
    axioms = [OWLSubClassOfAxiom(A, ce), OWLSubClassOfAxiom(ce, C)]
    assert set(axioms) <= set(_reloaded(tmp_path, axioms).get_tbox_axioms())


@pytest.mark.parametrize("ce", CLASS_EXPRESSIONS.values(), ids=CLASS_EXPRESSIONS.keys())
def test_class_assertion_with_complex_class(tmp_path, ce):
    axiom = OWLClassAssertionAxiom(a, ce)
    assert axiom in _written([axiom]).get_abox_axioms()
    assert axiom in _reloaded(tmp_path, [axiom]).get_abox_axioms()


def test_turtle_round_trip(tmp_path):
    axioms = [OWLSubClassOfAxiom(A, ce) for ce in CLASS_EXPRESSIONS.values()]
    assert set(axioms) <= set(_reloaded(tmp_path, axioms, fmt="ttl").get_tbox_axioms())


def test_equivalent_and_disjoint_classes(tmp_path):
    some, union, inter = CLASS_EXPRESSIONS["some"], CLASS_EXPRESSIONS["union"], CLASS_EXPRESSIONS["intersection"]
    onto = _reloaded(tmp_path, [
        OWLEquivalentClassesAxiom([some, C, inter]),
        OWLEquivalentClassesAxiom([some, union]),
        OWLDisjointClassesAxiom([A, some]),
        OWLDisjointClassesAxiom([A, some, CLASS_EXPRESSIONS["complement"]]),  # owl:AllDisjointClasses
    ])
    tbox = set(onto.get_tbox_axioms())
    assert {OWLEquivalentClassesAxiom([C, some]), OWLEquivalentClassesAxiom([C, inter]),
            OWLEquivalentClassesAxiom([some, union]), OWLDisjointClassesAxiom([A, some]),
            OWLDisjointClassesAxiom([A, some, CLASS_EXPRESSIONS["complement"]])} <= tbox
    assert set(onto.equivalent_classes_axioms(C)) == {OWLEquivalentClassesAxiom([C, some]), OWLEquivalentClassesAxiom([C, inter])}


def test_all_disjoint_classes_between_named_classes(tmp_path):
    onto = _from_turtle(tmp_path, ":B a owl:Class . :C a owl:Class .\n"
                                  "[] a owl:AllDisjointClasses ; owl:members ( :A :B :C ) .\n")
    assert OWLDisjointClassesAxiom([A, B, C]) in onto.get_tbox_axioms()


def test_general_class_axioms_match_owlapi(tmp_path):
    some, union = CLASS_EXPRESSIONS["some"], CLASS_EXPRESSIONS["union"]
    axioms = [OWLSubClassOfAxiom(ce, C) for ce in CLASS_EXPRESSIONS.values()]
    axioms += [OWLSubClassOfAxiom(A, some),  # named subclass: not a general class axiom
               OWLEquivalentClassesAxiom([some, union]), OWLEquivalentClassesAxiom([C, some]),
               OWLDisjointClassesAxiom([some, union]), OWLDisjointClassesAxiom([A, union])]
    path = tmp_path / "gca.owl"
    _written(axioms).save(path=str(path))
    ours = set(RDFLibOntology(str(path)).general_class_axioms())
    assert ours == set(SyncOntology(str(path)).general_class_axioms())
    assert OWLSubClassOfAxiom(some, C) in ours and OWLSubClassOfAxiom(A, some) not in ours


def test_domain_and_range_with_complex_expressions(tmp_path):
    expected = {
        OWLObjectPropertyDomainAxiom(r, CLASS_EXPRESSIONS["union"]),
        OWLObjectPropertyRangeAxiom(r, CLASS_EXPRESSIONS["some"]),
        OWLDataPropertyDomainAxiom(age, CLASS_EXPRESSIONS["intersection"]),
        OWLDataPropertyRangeAxiom(age, int_range),
        OWLDataPropertyRangeAxiom(name, CLASS_EXPRESSIONS["data_one_of"].get_filler()),
    }
    onto = _reloaded(tmp_path, list(expected))
    read = (set(onto.object_property_domain_axioms(r)) | set(onto.object_property_range_axioms(r))
            | set(onto.data_property_domain_axioms(age)) | set(onto.data_property_range_axioms(age))
            | set(onto.data_property_range_axioms(name)))
    assert read == expected


def test_data_restriction_on_undeclared_property_is_told_by_its_filler(tmp_path):
    onto = _from_turtle(tmp_path, ":A rdfs:subClassOf [ a owl:Restriction ; owl:onProperty :undeclared ;\n"
                                  "    owl:someValuesFrom [ a rdfs:Datatype ; owl:unionOf ( xsd:integer xsd:double ) ] ] .\n"
                                  ":A rdfs:subClassOf [ a owl:Restriction ; owl:onProperty :undeclared2 ; owl:someValuesFrom :B ] .\n")
    tbox = set(onto.get_tbox_axioms())
    data_union = OWLDataUnionOf([IntegerOWLDatatype, OWLDatatype("http://www.w3.org/2001/XMLSchema#double")])
    assert OWLSubClassOfAxiom(A, OWLDataSomeValuesFrom(OWLDataProperty(NS + "undeclared"), data_union)) in tbox
    assert OWLSubClassOfAxiom(A, OWLObjectSomeValuesFrom(OWLObjectProperty(NS + "undeclared2"), B)) in tbox


def test_unreadable_expression_is_skipped_with_one_warning(tmp_path, caplog):
    onto = _from_turtle(tmp_path, ":A rdfs:subClassOf [ a owl:Class ; owl:oneOf ( :a _:anon ) ] .\n"
                                  ":A rdfs:subClassOf [ a owl:Class ; owl:oneOf ( _:anon2 ) ] .\n"
                                  ":A rdfs:subClassOf [ a owl:Class ; owl:oneOf ( :a :b ) ] .\n")
    with caplog.at_level(logging.WARNING, logger="owlapy.owl_ontology"):
        tbox = onto.get_tbox_axioms()
    assert OWLSubClassOfAxiom(A, OWLObjectOneOf([a, OWLNamedIndividual(NS + "b")])) in tbox
    assert sum(isinstance(ax, OWLSubClassOfAxiom) for ax in tbox) == 1
    warnings = [rec for rec in caplog.records if "get_tbox_axioms() skipped 2 axiom(s)" in rec.getMessage()]
    assert len(warnings) == 1 and "anonymous individuals" in warnings[0].getMessage()


def test_cyclic_structure_is_skipped_not_recursed_forever(tmp_path):
    onto = _from_turtle(tmp_path, ":A rdfs:subClassOf _:x .\n_:x a owl:Class ; owl:complementOf _:x .\n")
    assert not any(isinstance(ax, OWLSubClassOfAxiom) for ax in onto.get_tbox_axioms())


def test_datatype_definition_is_not_a_class_axiom(tmp_path, caplog):
    onto = _from_turtle(tmp_path, ":adult a rdfs:Datatype ; owl:equivalentClass [ a rdfs:Datatype ; owl:onDatatype xsd:integer ;\n"
                                  "    owl:withRestrictions ( [ xsd:minInclusive 18 ] ) ] .\n")
    with caplog.at_level(logging.WARNING, logger="owlapy.owl_ontology"):
        assert not any(isinstance(ax, CLASS_AXIOMS) for ax in onto.get_tbox_axioms())
        assert not list(onto.general_class_axioms())
    assert not caplog.records


def test_data_has_value_and_cardinality_literals(tmp_path):
    has_value, data_min = CLASS_EXPRESSIONS["data_has_value"], CLASS_EXPRESSIONS["data_min"]
    tbox = set(_reloaded(tmp_path, [OWLSubClassOfAxiom(A, has_value), OWLSubClassOfAxiom(A, data_min)]).get_tbox_axioms())
    assert OWLSubClassOfAxiom(A, has_value) in tbox and has_value.get_filler() == OWLLiteral(42)
    assert OWLSubClassOfAxiom(A, data_min) in tbox


@pytest.mark.skipif(not os.path.isfile(BIOPAX), reason="KGs.zip not downloaded")
def test_biopax_class_axioms_match_owlapi():
    ours = {ax for ax in RDFLibOntology(BIOPAX).get_tbox_axioms() if isinstance(ax, CLASS_AXIOMS)}
    theirs = {ax for ax in SyncOntology(BIOPAX).get_axioms() if isinstance(ax, CLASS_AXIOMS)}
    assert ours == theirs
    # Biopax's complex axioms are restrictions on named classes
    assert sum(isinstance(ax, OWLSubClassOfAxiom) and not ax.get_super_class().is_owl_thing()
               and type(ax.get_super_class()) is not type(A) for ax in ours) > 50

