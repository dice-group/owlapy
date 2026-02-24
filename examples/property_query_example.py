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
)
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_property import OWLObjectProperty

# Import from both converter variants
from owlapy.marked_entity_generator_converter import (
    CONTEXT_POSITION_MARKER,
    owl_expression_to_property_query as property_query_with_counts,
)
from owlapy.marked_entity_generator_converter2 import (
    owl_expression_to_property_query as property_query_no_counts,
    owl_expression_to_class_query as class_query_no_counts,
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
# SECTION A – Property queries WITHOUT counts (converter2)
# ===================================================================

# ---------------------------------------------------------------------------
# Example 1 – simplest context: just the marker itself
#
# Context CE:  MARKER
# At the marker the converter emits:  ?pos ?prop [] .
# The query discovers every property the positive examples participate in.
# ---------------------------------------------------------------------------
print("=" * 70)
print("A1 – MARKER as root → discover all properties (no counts)")
print("=" * 70)

context1 = CONTEXT_POSITION_MARKER
query1 = property_query_no_counts(
    context=context1,
    positive_examples=positives,
)
print(query1)


# ---------------------------------------------------------------------------
# Example 2 – intersection context: Person ⊓ MARKER
#
# Context CE:  Person ⊓ MARKER
# The positives must be Persons; discover what properties they use.
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("A2 – Person ⊓ MARKER → properties of Person individuals (no counts)")
print("=" * 70)

context2 = OWLObjectIntersectionOf([Person, CONTEXT_POSITION_MARKER])
query2 = property_query_no_counts(
    context=context2,
    positive_examples=positives,
)
print(query2)


# ---------------------------------------------------------------------------
# Example 3 – inverted property direction
#
# Context CE:  MARKER  (inverted=True)
# At the marker the converter emits:  [] ?prop ?pos .
# Discovers properties where the positive examples appear as *objects*.
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("A3 – MARKER inverted → properties where positives are objects (no counts)")
print("=" * 70)

query3 = property_query_no_counts(
    context=CONTEXT_POSITION_MARKER,
    positive_examples=positives,
    inverted=True,
)
print(query3)


# ---------------------------------------------------------------------------
# Example 4 – existential restriction context
#
# Context CE:  ∃hasChild.MARKER
# Discover properties that children of the positive examples have.
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("A4 – ∃hasChild.MARKER → properties of children (no counts)")
print("=" * 70)

context4 = OWLObjectSomeValuesFrom(hasChild, CONTEXT_POSITION_MARKER)
query4 = property_query_no_counts(
    context=context4,
    positive_examples=positives,
)
print(query4)


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

exit(1)

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


# ===================================================================
# SECTION C – Class query WITHOUT counts for comparison
# ===================================================================

print("\n" + "=" * 70)
print("C1 – MARKER as root → discover all classes (no counts, for comparison)")
print("=" * 70)

query_class = class_query_no_counts(
    context=CONTEXT_POSITION_MARKER,
    positive_examples=positives,
)
print(query_class)


