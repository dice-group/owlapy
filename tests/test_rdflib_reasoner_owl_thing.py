"""RDFLibReasoner treats owl:Thing as the implicit root of the class hierarchy and as the domain/range
of a property without an asserted one, as StructuralReasoner and the OWL API reasoners do (#310, 2.1).

Ontolearn's refinement operator starts from owl:Thing and its KnowledgeBase indexes the first
domain/range, so without this it crashes on RDFLibReasoner.
"""
import pytest

from owlapy.class_expression import OWLClass, OWLThing
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty
from owlapy.owl_reasoner_rdflib import RDFLibReasoner

FAMILY = "KGs/Family/family-benchmark_rich_background.owl"
MUTAGENESIS = "KGs/Mutagenesis/mutagenesis.owl"
CARCINOGENESIS = "KGs/Carcinogenesis/carcinogenesis.owl"
BIOPAX = "KGs/Biopax/biopax.owl"
FAM = "http://www.benchmark.org/family#"
MUT = "http://dl-learner.org/mutagenesis#"


@pytest.fixture(scope="module")
def family():
    return RDFLibReasoner(FAMILY)


@pytest.fixture(scope="module")
def mutagenesis():
    return RDFLibReasoner(MUTAGENESIS)


def test_direct_subclasses_of_thing_are_the_roots(family, mutagenesis):
    assert set(family.sub_classes(OWLThing, direct=True)) == {OWLClass(FAM + "Person")}
    assert set(mutagenesis.sub_classes(OWLThing, direct=True)) == {OWLClass(MUT + c) for c in ("Atom", "Bond", "Compound", "RingStructure")}


def test_all_subclasses_of_thing_are_the_named_classes(family):
    expected = {c for c in family.get_root_ontology().classes_in_signature() if not c.is_owl_thing()}
    assert set(family.sub_classes(OWLThing, direct=False)) == expected
    assert len(expected) == 18


def test_thing_is_a_superclass(family):
    person, brother = OWLClass(FAM + "Person"), OWLClass(FAM + "Brother")
    assert set(family.super_classes(person, direct=True)) == {OWLThing}
    assert set(family.super_classes(person, direct=False)) == {OWLThing}
    assert OWLThing not in set(family.super_classes(brother, direct=True))
    assert OWLThing in set(family.super_classes(brother, direct=False))
    assert not list(family.super_classes(OWLThing, direct=False))


def test_undeclared_domain_and_range_are_thing(family):
    has_child = OWLObjectProperty(FAM + "hasChild")
    assert list(family.object_property_domains(has_child, direct=True)) == [OWLThing]
    assert list(family.object_property_ranges(has_child, direct=True)) == [OWLThing]
    assert list(family.data_property_domains(OWLDataProperty(FAM + "undeclared"), direct=True)) == [OWLThing]


def test_declared_domain_is_not_widened_to_thing(mutagenesis):
    # charge has rdfs:domain Atom
    assert set(mutagenesis.data_property_domains(OWLDataProperty(MUT + "charge"), direct=True)) == {OWLClass(MUT + "Atom")}


def test_declared_complex_range_does_not_fall_back_to_thing():
    # PARTICIPANTS' range is a union (a blank node). RDFLibReasoner returns named classes only,
    # but the range is declared, so it must not be reported as owl:Thing.
    reasoner = RDFLibReasoner(BIOPAX)
    participants = OWLObjectProperty("http://www.biopax.org/examples/glycolysis#PARTICIPANTS")
    assert participants in set(reasoner.get_root_ontology().object_properties_in_signature())
    assert OWLThing not in set(reasoner.object_property_ranges(participants, direct=True))


@pytest.mark.requires_owlready2
@pytest.mark.parametrize("path", [FAMILY, MUTAGENESIS, CARCINOGENESIS])
def test_hierarchy_domains_and_ranges_match_structural_reasoner(path):
    from owlapy.owl_ontology import Ontology
    from owlapy.owl_reasoner import StructuralReasoner
    structural, rdflib_reasoner = StructuralReasoner(Ontology(path)), RDFLibReasoner(path)
    onto = structural.get_root_ontology()
    queries = [(fn, c) for c in [*onto.classes_in_signature(), OWLThing] for fn in ("sub_classes", "super_classes")]
    queries += [(fn, p) for p in onto.object_properties_in_signature() for fn in ("object_property_domains", "object_property_ranges")]
    queries += [("data_property_domains", p) for p in onto.data_properties_in_signature()]
    for fn, entity in queries:
        for direct in (True, False):
            assert set(getattr(rdflib_reasoner, fn)(entity, direct=direct)) == set(getattr(structural, fn)(entity, direct=direct)), \
                (fn, entity, direct)
