"""Example: generate property-discovery SPARQL queries using the marker converters.

This example demonstrates both property query variants:

  - **With counts** (``marked_entity_generator_converter``):
    Returns ``?prop`` with ``?posHits`` and ``?negHits`` using a UNION pattern,
    mirroring the Java ``Suggestor.generatePropertyQuery``.

  - **Without counts** (``marked_entity_generator_converter2``):
    Returns only ``DISTINCT ?prop``.

The idea is:
  - You have a *context* class expression containing the special
    :data:`CONTEXT_POSITION_MARKER` at the position where you want to
    discover OWL properties.
  - At the marker position the converter emits ``?pos ?prop [] .``
    (or ``[] ?prop ?pos .`` when inverted) instead of a concrete property.
  - The generated query discovers all properties used by the given examples
    inside the context.

Run with::

    python examples/property_query_example.py
"""

from owlapy.class_expression import (
    OWLClass,
    OWLObjectIntersectionOf,
    OWLObjectSomeValuesFrom,
    OWLObjectUnionOf,
)
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_property import OWLObjectProperty

# Import from both converter variants
from owlapy.marked_entity_generator_converter import (
    CONTEXT_POSITION_MARKER,
    owl_expression_to_property_query as property_query_with_counts,
)

# ---------------------------------------------------------------------------
# Shared vocabulary
# ---------------------------------------------------------------------------
NS = "http://www.benchmark.org/family#"

Person   = OWLClass(IRI(NS, "Person"))
Male     = OWLClass(IRI(NS, "Male"))
Female   = OWLClass(IRI(NS, "Female"))
hasChild = OWLObjectProperty(IRI(NS, "hasChild"))

positives = [
    OWLNamedIndividual(IRI(NS, "F2F14")),
    OWLNamedIndividual(IRI(NS, "F2F12")),
    OWLNamedIndividual(IRI(NS, "F2F19")),
]

negatives = [
    OWLNamedIndividual(IRI(NS, "F2M15")),
    OWLNamedIndividual(IRI(NS, "F2M18")),
]

# ===================================================================
# SECTION B – Property queries WITH counts (converter)
# ===================================================================

# ---------------------------------------------------------------------------
# Example 5 – simplest context with counts (UNION pattern)
#
# Context CE:  MARKER
# Returns ?prop, ?posHits, ?negHits using the UNION pattern from
# Java's generatePropertyQuery.
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("B1 – MARKER as root → discover all properties (with counts)")
print("=" * 70)

query5 = property_query_with_counts(
    context=CONTEXT_POSITION_MARKER,
    positive_examples=positives,
    negative_examples=negatives,
)
print(query5)


# ---------------------------------------------------------------------------
# Example 6 – intersection context with counts
#
# Context CE:  Person ⊓ MARKER
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("B2 – Person ⊓ MARKER → properties of Persons (with counts)")
print("=" * 70)

query6 = property_query_with_counts(
    context=OWLObjectIntersectionOf([Person, CONTEXT_POSITION_MARKER]),
    positive_examples=positives,
    negative_examples=negatives,
)
print(query6)


# ---------------------------------------------------------------------------
# Example 6b – union context with counts
#
# Context CE:  Person ⊔ MARKER
# When the marker appears inside a UNION, the query uses a special structure
# that first binds ?prop independently with ``?anything ?prop [] .`` so that
# it is correctly scoped across both UNION branches.
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("B2b – Person ⊔ MARKER → properties of Person-or-discovered (with counts)")
print("=" * 70)

query6b = property_query_with_counts(
    context=OWLObjectUnionOf([Person, CONTEXT_POSITION_MARKER]),
    positive_examples=positives,
    negative_examples=negatives,
)
print(query6b)


# ---------------------------------------------------------------------------
# Example 7 – inverted with counts
#
# Context CE:  MARKER  (inverted=True)
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("B3 – MARKER inverted → properties where examples are objects (with counts)")
print("=" * 70)

query7 = property_query_with_counts(
    context=CONTEXT_POSITION_MARKER,
    positive_examples=positives,
    negative_examples=negatives,
    inverted=True,
)
print(query7)



