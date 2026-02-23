"""Example: generate a class-discovery SPARQL query using ClassGeneratorConverter.

This example mirrors the Java ``Suggestor.generateClassQuery`` functionality.
The idea is:

  - You have a *context* class expression that contains a special marker
    (:data:`CONTEXT_POSITION_MARKER`) at the position where you want to
    discover OWL classes.
  - You provide positive and (optionally) negative example individuals.
  - The generated query returns every ``?class`` that covers at least one
    positive example inside the given context, together with
    ``?posHits`` / ``?negHits`` counts.

Run with::

    python examples/class_query_example.py
"""

from owlapy.class_expression import (
    OWLClass,
    OWLObjectComplementOf,
    OWLObjectIntersectionOf,
    OWLObjectSomeValuesFrom,
)
from owlapy.class_generator_converter import (
    CONTEXT_POSITION_MARKER,
    owl_expression_to_class_query,
)
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_property import OWLObjectProperty

# ---------------------------------------------------------------------------
# Shared vocabulary
# ---------------------------------------------------------------------------
NS = "http://www.benchmark.org/family#"

Person   = OWLClass(IRI(NS, "Person"))
Male     = OWLClass(IRI(NS, "Male"))
Female   = OWLClass(IRI(NS, "Female"))
hasChild = OWLObjectProperty(IRI(NS, "hasChild"))

# Positive examples (individuals known to belong to the target concept)
positives = [
    OWLNamedIndividual(IRI(NS, "F2F14")),
    OWLNamedIndividual(IRI(NS, "F2F12")),
    OWLNamedIndividual(IRI(NS, "F2F19")),
]

# Negative examples (individuals known NOT to belong to the target concept)
negatives = [
    OWLNamedIndividual(IRI(NS, "F10F200")),
    OWLNamedIndividual(IRI(NS, "F3F48")),
]

# ---------------------------------------------------------------------------
# Example 1 – simplest context: just the marker itself
#
# Context CE:  MARKER
# The marker is the root, so the generated triple pattern is simply:
#     ?pos a ?class .
# The query discovers every class that the positive examples are members of.
# ---------------------------------------------------------------------------
print("=" * 60)
print("Example 1 – marker as root (discover all direct types)")
print("=" * 60)

context1 = CONTEXT_POSITION_MARKER
query1 = owl_expression_to_class_query(
    context=context1,
    positive_examples=positives,
    negative_examples=negatives,
)
print(query1)

exit(1)

# ---------------------------------------------------------------------------
# Example 2 – existential restriction context
#
# Context CE:  ∃hasChild.MARKER
# Find all classes ?class such that the positive examples have at least one
# child that is an instance of ?class.
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("Example 2 – ∃hasChild.MARKER (class of children)")
print("=" * 60)

context2 = OWLObjectSomeValuesFrom(hasChild, CONTEXT_POSITION_MARKER)
query2 = owl_expression_to_class_query(
    context=context2,
    positive_examples=positives,
    negative_examples=negatives,
)
print(query2)

# ---------------------------------------------------------------------------
# Example 3 – intersection context
#
# Context CE:  Person ⊓ MARKER
# The positive examples must be Persons, and the discovered ?class is an
# additional type they share.
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("Example 3 – Person ⊓ MARKER (subclasses of Person shared by positives)")
print("=" * 60)

context3 = OWLObjectIntersectionOf([Person, CONTEXT_POSITION_MARKER])
query3 = owl_expression_to_class_query(
    context=context3,
    positive_examples=positives,
    negative_examples=negatives,
)
print(query3)

# ---------------------------------------------------------------------------
# Example 4 – negated marker
#
# Context CE:  Person ⊓ ¬MARKER
# Find classes that the positive examples are *not* members of (while still
# being Persons).  The marker inside a negation generates:
#     FILTER NOT EXISTS { ?pos a ?class . }
#     ?class a owl:Class .
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("Example 4 – Person ⊓ ¬MARKER (classes positives are NOT a member of)")
print("=" * 60)

context4 = OWLObjectIntersectionOf([Person, OWLObjectComplementOf(CONTEXT_POSITION_MARKER)])
query4 = owl_expression_to_class_query(
    context=context4,
    positive_examples=positives,
    negative_examples=negatives,
)
print(query4)

# ---------------------------------------------------------------------------
# Example 5 – with an extra filter expression
#
# The filter expression is wrapped in FILTER NOT EXISTS on the root variable,
# effectively excluding individuals that also satisfy the filter CE.
# Here we exclude Males from the positive match.
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("Example 5 – MARKER with filter_expression=Male (exclude Males)")
print("=" * 60)

query5 = owl_expression_to_class_query(
    context=CONTEXT_POSITION_MARKER,
    positive_examples=positives,
    negative_examples=negatives,
    filter_expression=Male,
)
print(query5)

