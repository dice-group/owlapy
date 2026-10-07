import pytest

from owlapy.owl_data_ranges import OWLDataIntersectionOf, OWLDataUnionOf
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import IntOWLDatatype, OWLLiteral, StringOWLDatatype
from owlapy.owl_property import OWLObjectProperty
from owlapy.class_expression import OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom
from owlapy.converter import owl_expression_to_sparql
from owlapy.render import owl_expression_to_dl
from owlapy.iri import IRI
from owlapy.class_expression import OWLClass, OWLObjectUnionOf, OWLObjectIntersectionOf
from owlapy.class_expression import OWLDataOneOf, OWLObjectOneOf


@pytest.mark.parametrize("factory, operands", [
    (OWLObjectUnionOf, [OWLClass("http://example.org/A"), OWLClass("http://example.org/B")]),
    (OWLObjectIntersectionOf, [OWLClass("http://example.org/A"), OWLClass("http://example.org/B")]),
    (OWLDataUnionOf, [StringOWLDatatype, IntOWLDatatype]),
    (OWLDataIntersectionOf, [StringOWLDatatype, IntOWLDatatype]),
    (OWLDataOneOf, [OWLLiteral("a"), OWLLiteral("b")]),
    (OWLObjectOneOf, [OWLNamedIndividual("http://example.org/a"), OWLNamedIndividual("http://example.org/b")]),
])
def test_reordered_operands_work_in_sets_and_dictionaries(factory, operands):
    left = factory(operands)
    right = factory(reversed(operands))
    assert left == right
    assert hash(left) == hash(right)
    assert len({left, right}) == 1
    assert {left: "cached"}[right] == "cached"


def test_equal_nested_restrictions_share_hashes():
    a, b = OWLClass("http://example.org/A"), OWLClass("http://example.org/B")
    prop = OWLObjectProperty("http://example.org/p")
    left = OWLObjectSomeValuesFrom(prop, OWLObjectIntersectionOf([a, b]))
    right = OWLObjectSomeValuesFrom(prop, OWLObjectIntersectionOf([b, a]))
    assert left == right
    assert {left: "cached"}[right] == "cached"


def test_data_enumeration_duplicates_do_not_change_hash():
    a, b = OWLLiteral("a"), OWLLiteral("b")
    left, right = OWLDataOneOf([a, a, b]), OWLDataOneOf([b, a])
    assert left == right
    assert {left: "cached"}[right] == "cached"


def test_singleton_nominal_accepts_individual_or_iterable():
    individual = OWLNamedIndividual("http://example.org/a")
    left, right = OWLObjectOneOf(individual), OWLObjectOneOf([individual])
    assert left == right
    assert {left: "cached"}[right] == "cached"

class TestHashing:

    def test_el_description_logic_hash(self):
        """
        EL allows complex concepts of the following form:
        C := \top | A | C1 u C2 | \existr.C
        where A is a concept and r a role name.
        For more, refer to https://www.emse.fr/~zimmermann/Teaching/KRR/el.html
        """
        memory = dict()
        # An OWL Class can be used as a key in a dictionary.
        memory[OWLClass("http://example.com/father#A")] = OWLClass("http://example.com/father#A")
        memory[OWLClass("http://example.com/father#B")] = OWLClass("http://example.com/father#B")
        memory[OWLClass("http://example.com/father#C")] = OWLClass("http://example.com/father#C")

        unions = set()
        intersections = set()
        for k, v in memory.items():
            assert k == v
            # An OWLObjectUnionOf over two OWL Classes can be added into a set.
            unions.add(OWLObjectUnionOf((k, v)))
            # Since the order doesn't matter in an OWLObjectUnionOf the following also holds
            assert OWLObjectUnionOf((v, k)) in unions

            # This also works for intersections.
            intersections.add(OWLObjectIntersectionOf((k, v)))
            # Since the order doesn't matter in an OWLObjectUnionOf the following also holds
            assert OWLObjectIntersectionOf((v, k)) in intersections
        # OWLObjectUnionOf and OWLObjectIntersectionOf can also be used as keys
        for i in unions | intersections:
            memory[i]=i
        for k, v in memory.items():
            assert k == v

        atomic_concepts={OWLClass("http://example.com/father#A"),OWLClass("http://example.com/father#B")}
        properties={OWLObjectProperty("http://example.com/society#hasChild")}
        memory = dict()
        for ac in atomic_concepts:
            for op in properties:
                # OWLObjectSomeValuesFrom can be used as a key.
                memory[OWLObjectSomeValuesFrom(property=op, filler=ac)] = OWLObjectSomeValuesFrom(property=op, filler=ac)
                memory[OWLObjectAllValuesFrom(property=op, filler=ac)] = OWLObjectAllValuesFrom(property=op, filler=ac)

        for k, v in memory.items():
            assert k == v