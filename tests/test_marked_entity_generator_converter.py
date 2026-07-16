"""Test suite for the marked entity generator converters against a live SPARQL endpoint.

This test mirrors the Java ``SparqlBasedSuggestorTest`` from PruneCEL project:
  - We build class expressions with :data:`CONTEXT_POSITION_MARKER`.
  - We generate class-discovery and property-discovery SPARQL queries.
  - We execute those queries against the family ontology hosted on Fuseki.
  - We verify the returned classes / properties and their hit-counts.

Prerequisites:
  - Apache Jena Fuseki running at http://localhost:3030
  - The ``family-benchmark_rich_background.owl`` ontology loaded into the
    ``/family`` dataset.

Run with::

    pytest tests/test_marked_entity_generator_converter.py -v

or::

    python -m pytest tests/test_marked_entity_generator_converter.py -v
"""

from __future__ import annotations

import json
import unittest
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from owlapy.class_expression import (
    OWLClass,
    OWLObjectComplementOf,
    OWLObjectIntersectionOf,
    OWLObjectSomeValuesFrom,
    OWLObjectUnionOf,
)
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_property import OWLObjectProperty

# Converter with counts (UNION / OPTIONAL pattern)
from owlapy.marked_entity_generator_converter import (
    CONTEXT_POSITION_MARKER,
    owl_expression_to_class_query,
    owl_expression_to_negated_class_query,
    owl_expression_to_property_query,
)


# ============================================================================
# Constants
# ============================================================================

FUSEKI_ENDPOINT = "http://localhost:3030/family/sparql"

NS = "http://www.benchmark.org/family#"

# Classes
Person = OWLClass(IRI(NS, "Person"))
Male = OWLClass(IRI(NS, "Male"))
Female = OWLClass(IRI(NS, "Female"))
Father = OWLClass(IRI(NS, "Father"))
Mother = OWLClass(IRI(NS, "Mother"))
Son = OWLClass(IRI(NS, "Son"))
Daughter = OWLClass(IRI(NS, "Daughter"))
Brother = OWLClass(IRI(NS, "Brother"))
Sister = OWLClass(IRI(NS, "Sister"))
Grandfather = OWLClass(IRI(NS, "Grandfather"))
Grandmother = OWLClass(IRI(NS, "Grandmother"))
Grandparent = OWLClass(IRI(NS, "Grandparent"))
Grandchild = OWLClass(IRI(NS, "Grandchild"))
Grandson = OWLClass(IRI(NS, "Grandson"))
Granddaughter = OWLClass(IRI(NS, "Granddaughter"))
PersonWithASibling = OWLClass(IRI(NS, "PersonWithASibling"))
Child = OWLClass(IRI(NS, "Child"))
Parent = OWLClass(IRI(NS, "Parent"))

# Properties
hasChild = OWLObjectProperty(IRI(NS, "hasChild"))
hasParent = OWLObjectProperty(IRI(NS, "hasParent"))
hasSibling = OWLObjectProperty(IRI(NS, "hasSibling"))
married = OWLObjectProperty(IRI(NS, "married"))


def ind(name: str) -> OWLNamedIndividual:
    """Shortcut to create a named individual in the family namespace."""
    return OWLNamedIndividual(IRI(NS, name))


# ============================================================================
# SPARQL query helper
# ============================================================================


def _execute_sparql(query: str) -> List[Dict[str, str]]:
    """Execute a SPARQL SELECT query against Fuseki and return bindings.

    Each binding is a dict mapping variable names (without ``?``) to their
    string values.
    """
    params = urllib.parse.urlencode({"query": query, "output": "json"})
    url = f"{FUSEKI_ENDPOINT}?{params}"
    with urllib.request.urlopen(url) as resp:
        data = json.loads(resp.read())
    results = []
    for binding in data["results"]["bindings"]:
        row = {}
        for var, info in binding.items():
            row[var] = info["value"]
        results.append(row)
    return results


# ============================================================================
# Data classes for expected results
# ============================================================================


@dataclass
class ScoredIRI:
    """Mirrors the Java ``ScoredIRI`` with IRI string and pos/neg counts."""
    iri: str
    pos_count: int
    neg_count: int


# ============================================================================
# Test class
# ============================================================================


class TestMarkedEntityGeneratorConverter(unittest.TestCase):
    """Integration tests that generate class / property queries using the
    marked-entity converters and execute them against the family ontology
    hosted on a live Fuseki SPARQL endpoint.
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @classmethod
    def setUpClass(cls):
        """Verify that the Fuseki endpoint is reachable."""
        try:
            results = _execute_sparql("SELECT (COUNT(*) AS ?c) WHERE { ?s ?p ?o }")
            count = int(results[0]["c"])
            assert count > 0, "The dataset appears to be empty."
        except Exception as exc:
            raise unittest.SkipTest(
                f"Fuseki endpoint not available at {FUSEKI_ENDPOINT}: {exc}"
            ) from exc

    @staticmethod
    def _parse_class_results_with_counts(
        bindings: List[Dict[str, str]],
    ) -> Dict[str, Tuple[int, int]]:
        """Parse bindings from a class query with counts.

        Returns a dict mapping class IRI -> (posHits, negHits).
        """
        result = {}
        for row in bindings:
            cls_iri = row["class"]
            pos = int(row["posHits"])
            neg = int(row["negHits"])
            result[cls_iri] = (pos, neg)
        return result

    @staticmethod
    def _parse_property_results_with_counts(
        bindings: List[Dict[str, str]],
    ) -> Dict[str, Tuple[int, int]]:
        """Parse bindings from a property query with counts.

        Returns a dict mapping property IRI -> (posHits, negHits).
        """
        result = {}
        for row in bindings:
            prop_iri = row["prop"]
            pos = int(row["posHits"])
            neg = int(row["negHits"])
            result[prop_iri] = (pos, neg)
        return result

    @staticmethod
    def _parse_distinct_results(
        bindings: List[Dict[str, str]], var: str
    ) -> Set[str]:
        """Parse bindings from a no-counts query. Returns set of IRIs."""
        return {row[var] for row in bindings}

    # ------------------------------------------------------------------
    # Test 1 – simplest context: MARKER as root (class query)
    #
    # Context:  ⌖
    # Positive: F2M11 (types: Brother, Male, Person, Father, Grandfather, Son)
    # Negative: F2F14 (types: Person, Female)
    #
    # Expected class results (with counts):
    #   Person  -> posHits=1, negHits=1
    #   Male    -> posHits=1, negHits=0
    #   Father  -> posHits=1, negHits=0
    #   Brother -> posHits=1, negHits=0
    #   Son     -> posHits=1, negHits=0
    #   Grandfather -> posHits=1, negHits=0
    #   Female  -> posHits=0, negHits=1
    #   NamedIndividual -> posHits=1, negHits=1 (both are NamedIndividual)
    # ------------------------------------------------------------------

    def test_01_marker_root_class_query_with_counts(self):
        """MARKER as root: discover classes of F2M11 (pos) and F2F14 (neg)."""
        context = CONTEXT_POSITION_MARKER
        positives = [ind("F2M11")]
        negatives = [ind("F2F14")]

        query = owl_expression_to_class_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_class_results_with_counts(bindings)

        # F2M11 is Male, Person, Father, Brother, Son, Grandfather, NamedIndividual
        # F2F14 is Person, Female, NamedIndividual
        self.assertIn(NS + "Person", results)
        self.assertEqual(results[NS + "Person"], (1, 1))

        self.assertIn(NS + "Male", results)
        self.assertEqual(results[NS + "Male"], (1, 0))

        self.assertIn(NS + "Father", results)
        self.assertEqual(results[NS + "Father"], (1, 0))

        # Female: only F2F14 (neg) is Female. Since the class query uses the
        # OPTIONAL pattern (like the Java generateClassQuery), classes that
        # only negatives satisfy do NOT appear in the results – the inner
        # SELECT only returns classes matched by at least one positive.
        self.assertNotIn(NS + "Female", results)


    # ------------------------------------------------------------------
    # Test 2 – simplest context: MARKER as root (property query)
    #
    # Positive: F2M11 (props: hasChild, hasParent, hasSibling, married)
    # Negative: F2F14 (props: married)
    # ------------------------------------------------------------------

    def test_03_marker_root_property_query_with_counts(self):
        """MARKER as root: discover properties of F2M11 (pos) and F2F14 (neg)."""
        context = CONTEXT_POSITION_MARKER
        positives = [ind("F2M11")]
        negatives = [ind("F2F14")]

        query = owl_expression_to_property_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_property_results_with_counts(bindings)

        # F2M11 has hasChild, hasParent, hasSibling, married
        # F2F14 has only married
        self.assertIn(NS + "hasChild", results)
        self.assertEqual(results[NS + "hasChild"][0], 1)  # pos=1
        self.assertEqual(results[NS + "hasChild"][1], 0)  # neg=0

        self.assertIn(NS + "married", results)
        self.assertEqual(results[NS + "married"][0], 1)  # pos=1
        self.assertEqual(results[NS + "married"][1], 1)  # neg=1

        self.assertIn(NS + "hasSibling", results)
        self.assertEqual(results[NS + "hasSibling"][0], 1)  # pos=1
        self.assertEqual(results[NS + "hasSibling"][1], 0)  # neg=0


    # ------------------------------------------------------------------
    # Test 3 – intersection context: Person ⊓ MARKER
    #
    # Positive: F2M11 (Person, Male, Father, Brother, Son, Grandfather)
    #           F2F15 (Person, Daughter, Female, Granddaughter, Mother, Sister)
    # Negative: F2F14 (Person, Female)
    # ------------------------------------------------------------------

    def test_05_intersection_class_query_with_counts(self):
        """Person ⊓ MARKER: discover additional classes shared by positives."""
        context = OWLObjectIntersectionOf([Person, CONTEXT_POSITION_MARKER])
        positives = [ind("F2M11"), ind("F2F15")]
        negatives = [ind("F2F14")]

        query = owl_expression_to_class_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_class_results_with_counts(bindings)

        # Both positives are Person, so Person should have posHits=2, negHits=1
        self.assertIn(NS + "Person", results)
        self.assertEqual(results[NS + "Person"], (2, 1))

        # Male: only F2M11 -> posHits=1, negHits=0
        self.assertIn(NS + "Male", results)
        self.assertEqual(results[NS + "Male"], (1, 0))

        # Female: F2F15 pos + F2F14 neg -> posHits=1, negHits=1
        self.assertIn(NS + "Female", results)
        self.assertEqual(results[NS + "Female"], (1, 1))

    def test_06_intersection_property_query_with_counts(self):
        """Person ⊓ MARKER: discover properties of Person individuals."""
        context = OWLObjectIntersectionOf([Person, CONTEXT_POSITION_MARKER])
        positives = [ind("F2M11"), ind("F2F15")]
        negatives = [ind("F2F14")]

        query = owl_expression_to_property_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_property_results_with_counts(bindings)

        # Both positives have hasChild, hasParent, hasSibling, married
        # F2F14 has only married
        self.assertIn(NS + "hasChild", results)
        self.assertEqual(results[NS + "hasChild"][0], 2)  # both pos have children
        self.assertEqual(results[NS + "hasChild"][1], 0)

        self.assertIn(NS + "married", results)
        self.assertEqual(results[NS + "married"][0], 2)
        self.assertEqual(results[NS + "married"][1], 1)

    # ------------------------------------------------------------------
    # Test 4 – existential context: ∃hasChild.MARKER
    #
    # Find classes of children of the positive examples.
    # Positive: F2M11 (children: F2F15, F2M13)
    # Negative: F2F14 (no children)
    # ------------------------------------------------------------------

    def test_07_existential_class_query_with_counts(self):
        """∃hasChild.MARKER: discover classes of children."""
        context = OWLObjectSomeValuesFrom(hasChild, CONTEXT_POSITION_MARKER)
        positives = [ind("F2M11")]
        negatives = [ind("F2F14")]

        query = owl_expression_to_class_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_class_results_with_counts(bindings)

        # F2M11's children: F2F15 (Person, Daughter, Female, Granddaughter, Mother, Sister)
        #                   F2M13 (Brother, Male, Person, Grandson, Son)
        # F2F14 has no children -> negHits=0 for all classes
        self.assertIn(NS + "Person", results)
        self.assertEqual(results[NS + "Person"][0], 1)  # F2M11 has children who are Person
        self.assertEqual(results[NS + "Person"][1], 0)  # F2F14 has no children

        self.assertIn(NS + "Daughter", results)
        self.assertEqual(results[NS + "Daughter"][0], 1)
        self.assertEqual(results[NS + "Daughter"][1], 0)

        self.assertIn(NS + "Male", results)
        self.assertEqual(results[NS + "Male"][0], 1)
        self.assertEqual(results[NS + "Male"][1], 0)


    def test_09_existential_property_query_with_counts(self):
        """∃hasChild.MARKER: discover properties of children."""
        context = OWLObjectSomeValuesFrom(hasChild, CONTEXT_POSITION_MARKER)
        positives = [ind("F2M11")]
        negatives = [ind("F2F14")]

        query = owl_expression_to_property_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_property_results_with_counts(bindings)

        # Children of F2M11 (F2F15, F2M13) have various properties
        # F2F14 has no children so neg=0
        self.assertIn(NS + "hasParent", results)
        self.assertEqual(results[NS + "hasParent"][0], 1)  # F2M11's children have hasParent
        self.assertEqual(results[NS + "hasParent"][1], 0)

    # ------------------------------------------------------------------
    # Test 5 – inverted property query: MARKER (inverted=True)
    #
    # Discover properties where positive examples appear as OBJECTS.
    # E.g. if F2M13 is pos, we find: hasChild (because F2M11 hasChild F2M13),
    #       hasSibling (because F2F15 hasSibling F2M13),
    #       married (because F2F14 married F2M13)
    # ------------------------------------------------------------------

    def test_10_inverted_property_query_with_counts(self):
        """MARKER inverted: properties where positives are objects."""
        context = CONTEXT_POSITION_MARKER
        positives = [ind("F2M13")]
        negatives = [ind("F2M11")]

        query = owl_expression_to_property_query(
            context, positives, negatives, inverted=True
        )
        bindings = _execute_sparql(query)
        results = self._parse_property_results_with_counts(bindings)

        # F2M13 appears as object of:
        #   hasChild (F2M11 hasChild F2M13)
        #   hasSibling (F2F15 hasSibling F2M13)
        #   married (F2F14 married F2M13)
        self.assertIn(NS + "hasChild", results)
        self.assertGreaterEqual(results[NS + "hasChild"][0], 1)

        self.assertIn(NS + "married", results)
        self.assertGreaterEqual(results[NS + "married"][0], 1)

        self.assertIn(NS + "hasSibling", results)
        self.assertGreaterEqual(results[NS + "hasSibling"][0], 1)


    # ------------------------------------------------------------------
    # Test 6 – multiple positives / negatives with counts
    #
    # Positive: F2M11 (Father, Grandfather, Male, ...)
    #           F2F15 (Mother, Sister, Daughter, Female, ...)
    # Negative: F2F14 (Female, Person – no children)
    #           F2M13 (Male, Person, Brother, Son, Grandson – no children)
    # ------------------------------------------------------------------

    def test_12_multiple_examples_class_query(self):
        """Multiple positives and negatives: verify counts."""
        context = CONTEXT_POSITION_MARKER
        positives = [ind("F2M11"), ind("F2F15")]
        negatives = [ind("F2F14"), ind("F2M13")]

        query = owl_expression_to_class_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_class_results_with_counts(bindings)

        # Person: all four are Person
        self.assertIn(NS + "Person", results)
        self.assertEqual(results[NS + "Person"], (2, 2))

        # Male: F2M11 pos, F2M13 neg
        self.assertIn(NS + "Male", results)
        self.assertEqual(results[NS + "Male"], (1, 1))

        # Female: F2F15 pos, F2F14 neg
        self.assertIn(NS + "Female", results)
        self.assertEqual(results[NS + "Female"], (1, 1))

        # Father: only F2M11 (pos)
        self.assertIn(NS + "Father", results)
        self.assertEqual(results[NS + "Father"], (1, 0))

        # Mother: only F2F15 (pos)
        self.assertIn(NS + "Mother", results)
        self.assertEqual(results[NS + "Mother"], (1, 0))

        # Brother: F2M11 (pos), F2M13 (neg)
        self.assertIn(NS + "Brother", results)
        self.assertEqual(results[NS + "Brother"], (1, 1))

    def test_13_multiple_examples_property_query(self):
        """Multiple positives and negatives: verify property counts."""
        context = CONTEXT_POSITION_MARKER
        positives = [ind("F2M11"), ind("F2F15")]
        negatives = [ind("F2F14"), ind("F2M13")]

        query = owl_expression_to_property_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_property_results_with_counts(bindings)

        # hasChild: F2M11 (pos), F2F15 (pos) have children; F2F14 and F2M13 don't
        self.assertIn(NS + "hasChild", results)
        self.assertEqual(results[NS + "hasChild"][0], 2)
        self.assertEqual(results[NS + "hasChild"][1], 0)

        # married: all four have married
        self.assertIn(NS + "married", results)
        self.assertEqual(results[NS + "married"][0], 2)
        self.assertEqual(results[NS + "married"][1], 2)

        # hasSibling: F2M11 (pos, has siblings), F2F15 (pos, has siblings),
        #             F2M13 (neg, has siblings), F2F14 (neg, no siblings)
        self.assertIn(NS + "hasSibling", results)
        self.assertEqual(results[NS + "hasSibling"][0], 2)
        self.assertEqual(results[NS + "hasSibling"][1], 1)

    # ------------------------------------------------------------------
    # Test 7 – existential + intersection: ∃hasChild.(Person ⊓ MARKER)
    #
    # Discover additional classes of children who are Persons.
    # Positive: F2M11 (children: F2F15, F2M13 – both are Person)
    # Negative: F2F14 (no children)
    # ------------------------------------------------------------------

    def test_14_existential_intersection_class_query(self):
        """∃hasChild.(Person ⊓ MARKER): classes of children who are Persons."""
        context = OWLObjectSomeValuesFrom(
            hasChild,
            OWLObjectIntersectionOf([Person, CONTEXT_POSITION_MARKER]),
        )
        positives = [ind("F2M11")]
        negatives = [ind("F2F14")]

        query = owl_expression_to_class_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_class_results_with_counts(bindings)

        # Same as ∃hasChild.MARKER since all children are Person anyway
        self.assertIn(NS + "Person", results)
        self.assertEqual(results[NS + "Person"][0], 1)
        self.assertEqual(results[NS + "Person"][1], 0)

        # F2F15 is a Mother
        self.assertIn(NS + "Mother", results)
        self.assertEqual(results[NS + "Mother"][0], 1)
        self.assertEqual(results[NS + "Mother"][1], 0)

    # ------------------------------------------------------------------
    # Test 8 – existential + property: ∃hasChild.MARKER (property query)
    #
    # Discover properties used by children.
    # Positive: F2F15 (children: F2F17, F2M18)
    # Negative: F2M13 (no children)
    # ------------------------------------------------------------------

    def test_15_existential_property_query(self):
        """∃hasChild.MARKER (property query): discover properties of children."""
        context = OWLObjectSomeValuesFrom(hasChild, CONTEXT_POSITION_MARKER)
        positives = [ind("F2F15")]
        negatives = [ind("F2M13")]

        query = owl_expression_to_property_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_property_results_with_counts(bindings)

        # Children of F2F15 (F2F17, F2M18) should have hasParent property
        self.assertIn(NS + "hasParent", results)
        self.assertEqual(results[NS + "hasParent"][0], 1)  # F2F15 has children with hasParent
        self.assertEqual(results[NS + "hasParent"][1], 0)  # F2M13 has no children

    # ------------------------------------------------------------------
    # Test 9 – query validation (no execution)
    #
    # Verify that various context shapes produce valid SPARQL that
    # the rdflib parser accepts (parseQuery is called internally).
    # ------------------------------------------------------------------

    def test_16_query_generation_union_context(self):
        """MARKER ⊔ Person: generates valid SPARQL (class query)."""
        context = OWLObjectUnionOf([CONTEXT_POSITION_MARKER, Person])
        positives = [ind("F2M11")]
        negatives = [ind("F2F14")]
        query = owl_expression_to_class_query(context, positives, negatives)
        self.assertIn("UNION", query)
        self.assertIn("?class", query)

    def test_17_query_generation_negated_marker_class(self):
        """Person ⊓ ¬MARKER: generates FILTER NOT EXISTS for class."""
        context = OWLObjectIntersectionOf(
            [Person, OWLObjectComplementOf(CONTEXT_POSITION_MARKER)]
        )
        positives = [ind("F2M11")]
        negatives = [ind("F2F14")]
        query = owl_expression_to_class_query(context, positives, negatives)
        self.assertIn("FILTER NOT EXISTS", query)
        self.assertIn("?class", query)
        self.assertIn("owl#Class", query)

    def test_18_query_generation_negated_marker_property(self):
        """Person ⊓ ¬MARKER: generates FILTER NOT EXISTS for property."""
        context = OWLObjectIntersectionOf(
            [Person, OWLObjectComplementOf(CONTEXT_POSITION_MARKER)]
        )
        positives = [ind("F2M11")]
        negatives = [ind("F2F14")]
        query = owl_expression_to_property_query(context, positives, negatives)
        self.assertIn("FILTER NOT EXISTS", query)
        self.assertIn("?prop", query)
        self.assertIn("rdf-syntax-ns#Property", query)

    # ------------------------------------------------------------------
    # Test 10 – Execute negated marker against Fuseki
    #
    # Person ⊓ ¬MARKER (class): find classes the positive is NOT a member of.
    # Positive: F2F14 (Person, Female – NOT Male, NOT Father, NOT Mother, ...)
    # Negative: F2M11
    # ------------------------------------------------------------------

    def test_19_negated_marker_class_query_execution(self):
        """Person ⊓ ¬MARKER: discover classes F2F14 is NOT a member of."""
        context = OWLObjectIntersectionOf(
            [Person, OWLObjectComplementOf(CONTEXT_POSITION_MARKER)]
        )
        positives = [ind("F2F14")]
        negatives = [ind("F2M11")]

        query = owl_expression_to_class_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_class_results_with_counts(bindings)

        # F2F14 is Person and Female but NOT Male, NOT Father, NOT Mother, etc.
        # So Male should appear with posHits=1 (F2F14 is NOT Male -> hit)
        self.assertIn(NS + "Male", results)
        self.assertGreaterEqual(results[NS + "Male"][0], 1)

        self.assertIn(NS + "Father", results)
        self.assertGreaterEqual(results[NS + "Father"][0], 1)

        self.assertIn(NS + "Mother", results)
        self.assertGreaterEqual(results[NS + "Mother"][0], 1)

    # ------------------------------------------------------------------
    # Test 11 – Consistency: no-count results should be a subset of
    #           with-count results
    # ------------------------------------------------------------------



    # ------------------------------------------------------------------
    # Test 12 – filter_expression parameter
    #
    # MARKER with filter_expression=Male: exclude Males from matching.
    # Positive: F2M11 (Male, should be excluded by filter)
    #           F2F15 (Female, should NOT be excluded)
    # ------------------------------------------------------------------

    def test_22_filter_expression_class_query(self):
        """MARKER with filter_expression=Male: only F2F15 matches."""
        context = CONTEXT_POSITION_MARKER
        positives = [ind("F2M11"), ind("F2F15")]
        negatives = [ind("F2F14")]

        query = owl_expression_to_class_query(
            context, positives, negatives, filter_expression=Male
        )
        bindings = _execute_sparql(query)
        results = self._parse_class_results_with_counts(bindings)

        # F2M11 is Male -> excluded by filter
        # Only F2F15 should contribute to posHits
        # F2F15 is Female -> posHits=1 for Female
        if NS + "Female" in results:
            self.assertEqual(results[NS + "Female"][0], 1)

        # Male should have posHits=0 (F2M11 excluded, F2F15 is not Male)
        if NS + "Male" in results:
            self.assertEqual(results[NS + "Male"][0], 0)

    # ------------------------------------------------------------------
    # Test 13 – Large positive set: verify scalability
    # ------------------------------------------------------------------

    def test_23_large_positive_set(self):
        """Query with many positive examples still produces valid results."""
        context = CONTEXT_POSITION_MARKER
        # Get some Father individuals as positives
        bindings = _execute_sparql(
            f"SELECT ?f WHERE {{ ?f a <{NS}Father> }} LIMIT 10"
        )
        positives = [OWLNamedIndividual(IRI.create(b["f"])) for b in bindings]

        # Get some non-Father individuals as negatives
        bindings_neg = _execute_sparql(
            f"""SELECT ?f WHERE {{
                ?f a <{NS}Female> .
                FILTER NOT EXISTS {{ ?f a <{NS}Mother> }}
            }} LIMIT 5"""
        )
        negatives = [OWLNamedIndividual(IRI.create(b["f"])) for b in bindings_neg]

        if len(positives) < 2 or len(negatives) < 1:
            self.skipTest("Not enough individuals in dataset")

        query = owl_expression_to_class_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_class_results_with_counts(bindings)

        # All fathers are Male, Person, Father
        self.assertIn(NS + "Father", results)
        self.assertEqual(results[NS + "Father"][0], len(positives))

        self.assertIn(NS + "Male", results)
        self.assertEqual(results[NS + "Male"][0], len(positives))

        # Negatives are Female and not Mother.  However, since the class
        # query uses the OPTIONAL pattern (like Java's generateClassQuery),
        # only classes that at least one *positive* belongs to will appear.
        # Positives are all Fathers (Males), so Female won't show up.
        self.assertNotIn(NS + "Female", results)

        # But Person should still show both pos and neg counts
        self.assertIn(NS + "Person", results)
        self.assertEqual(results[NS + "Person"], (len(positives), len(negatives)))

    # ------------------------------------------------------------------
    # Test 14 – Deep nesting: ∃hasChild.(∃hasChild.MARKER)
    #
    # Discover classes of grandchildren.
    # Positive: F2M11 (children: F2F15, F2M13.  F2F15 has children: F2F17, F2M18)
    # ------------------------------------------------------------------

    def test_24_deep_nesting_class_query(self):
        """∃hasChild.(∃hasChild.MARKER): classes of grandchildren."""
        context = OWLObjectSomeValuesFrom(
            hasChild,
            OWLObjectSomeValuesFrom(hasChild, CONTEXT_POSITION_MARKER),
        )
        positives = [ind("F2M11")]
        negatives = [ind("F2F14")]

        query = owl_expression_to_class_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_class_results_with_counts(bindings)

        # F2M11 -> children: F2F15 (has children F2F17, F2M18), F2M13 (no children)
        # So grandchildren are F2F17 and F2M18
        # They should be Person at minimum
        self.assertIn(NS + "Person", results)
        self.assertEqual(results[NS + "Person"][0], 1)  # F2M11 has grandchildren
        self.assertEqual(results[NS + "Person"][1], 0)  # F2F14 has no children

    # ------------------------------------------------------------------
    # Test 15 – Negated class query: MARKER as root
    #
    # Context: ⌖  (with negated_class_marker_mode)
    # At the marker the converter emits:
    #     ?class a owl:Class .
    #     FILTER NOT EXISTS { ?pos a ?class . }
    #
    # This finds classes the individual is NOT a member of.
    #
    # Positive: F2F14 (types: Person, Female, NamedIndividual, Thing)
    #   → NOT member of: Male, Father, Mother, Brother, Sister, Son, Daughter,
    #     Grandfather, Grandmother, Grandparent, Grandchild, Grandson,
    #     Granddaughter, PersonWithASibling, Child, Parent
    # Negative: F2M11 (types: Brother, Male, Person, Father, Grandfather, Son,
    #                   NamedIndividual, Thing)
    #   → NOT member of: Female, Mother, Sister, Daughter, Grandmother,
    #     Grandparent, Grandchild, Grandson, Granddaughter,
    #     PersonWithASibling, Child, Parent
    # ------------------------------------------------------------------

    def test_25_negated_marker_root_class_query(self):
        """Negated MARKER as root: discover classes F2F14 is NOT a member of."""
        context = CONTEXT_POSITION_MARKER
        positives = [ind("F2F14")]
        negatives = [ind("F2M11")]

        query = owl_expression_to_negated_class_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_class_results_with_counts(bindings)

        # F2F14 is NOT Male -> Male should appear with posHits >= 1
        self.assertIn(NS + "Male", results)
        self.assertGreaterEqual(results[NS + "Male"][0], 1)

        # F2F14 is NOT Father -> Father should appear with posHits >= 1
        self.assertIn(NS + "Father", results)
        self.assertGreaterEqual(results[NS + "Father"][0], 1)

        # F2F14 is NOT Mother -> Mother should appear with posHits >= 1
        self.assertIn(NS + "Mother", results)
        self.assertGreaterEqual(results[NS + "Mother"][0], 1)

        # F2F14 IS Person -> Person should NOT appear (or posHits=0)
        if NS + "Person" in results:
            self.assertEqual(results[NS + "Person"][0], 0)

        # F2F14 IS Female -> Female should NOT appear (or posHits=0)
        if NS + "Female" in results:
            self.assertEqual(results[NS + "Female"][0], 0)

        # F2M11 is NOT Female -> negHits for Female >= 1
        self.assertIn(NS + "Female", results)
        self.assertGreaterEqual(results[NS + "Female"][1], 1)

        # F2M11 IS Male -> Male negHits=0
        self.assertEqual(results[NS + "Male"][1], 0)

    def test_26_negated_marker_root_query_structure(self):
        """Verify the negated class query has UNION structure (not OPTIONAL)."""
        context = CONTEXT_POSITION_MARKER
        positives = [ind("F2F14")]
        negatives = [ind("F2M11")]

        query = owl_expression_to_negated_class_query(context, positives, negatives)

        # Should use UNION pattern, not OPTIONAL
        self.assertIn("UNION", query)
        self.assertNotIn("OPTIONAL", query)
        # Should contain FILTER NOT EXISTS { ?pos a ?class . }
        self.assertIn("FILTER NOT EXISTS", query)
        self.assertIn("a ?class", query)
        # Should contain ?class a owl:Class .
        self.assertIn("?class a <http://www.w3.org/2002/07/owl#Class>", query)

    # ------------------------------------------------------------------
    # Test 16 – Negated class query with intersection context
    #
    # Context: Person ⊓ ⌖ (negated)
    # Finds classes that Person-individuals (the positives) are NOT
    # members of.
    # Positive: F2F14 (Person, Female) → NOT: Male, Father, Mother, ...
    # Negative: F2M11 (Person, Male, Father, ...) → NOT: Female, Mother, ...
    # ------------------------------------------------------------------

    def test_27_negated_intersection_class_query(self):
        """Person ⊓ MARKER (negated): classes Person-positives are NOT members of."""
        context = OWLObjectIntersectionOf([Person, CONTEXT_POSITION_MARKER])
        positives = [ind("F2F14")]
        negatives = [ind("F2M11")]

        query = owl_expression_to_negated_class_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_class_results_with_counts(bindings)

        # F2F14 is Person but NOT Male
        self.assertIn(NS + "Male", results)
        self.assertGreaterEqual(results[NS + "Male"][0], 1)

        # F2F14 is Person but NOT Father
        self.assertIn(NS + "Father", results)
        self.assertGreaterEqual(results[NS + "Father"][0], 1)

    # ------------------------------------------------------------------
    # Test 17 – Negated class query with existential context
    #
    # Context: ∃hasChild.⌖ (negated)
    # Finds classes that children of positives are NOT members of.
    # Positive: F2M11 (children: F2F15, F2M13)
    #   F2F15 types: Person, Daughter, Female, Granddaughter, Mother, Sister
    #   F2M13 types: Brother, Male, Person, Grandson, Son
    #   Classes children are NOT: e.g. F2M13 is NOT Female, NOT Mother, etc.
    # Negative: F2F14 (no children)
    # ------------------------------------------------------------------

    def test_28_negated_existential_class_query(self):
        """∃hasChild.MARKER (negated): classes children are NOT members of."""
        context = OWLObjectSomeValuesFrom(hasChild, CONTEXT_POSITION_MARKER)
        positives = [ind("F2M11")]
        negatives = [ind("F2F14")]

        query = owl_expression_to_negated_class_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_class_results_with_counts(bindings)

        # F2M11 has children. F2M13 is NOT Female, NOT Mother, NOT Daughter, etc.
        # So these should appear with posHits >= 1
        # (At least one child of F2M11 is NOT a member of these classes)

        # F2M13 is NOT Female
        self.assertIn(NS + "Female", results)
        self.assertGreaterEqual(results[NS + "Female"][0], 1)

        # F2F14 has no children, so neg doesn't contribute through ∃hasChild
        # -> negHits should be 0 for all classes
        for cls_iri, (pos, neg) in results.items():
            self.assertEqual(neg, 0,
                             f"negHits should be 0 for {cls_iri} since F2F14 has no children")

    # ------------------------------------------------------------------
    # Test 18 – Multiple positives in negated class query
    #
    # Positive: F2M11 (Male, Father, Grandfather, Brother, Son, Person)
    #           F2F14 (Female, Person)
    # Negative: F2M13 (Male, Brother, Grandson, Son, Person)
    # ------------------------------------------------------------------

    def test_29_negated_multiple_positives(self):
        """Negated MARKER with 2 positives: verify counts."""
        context = CONTEXT_POSITION_MARKER
        positives = [ind("F2M11"), ind("F2F14")]
        negatives = [ind("F2M13")]

        query = owl_expression_to_negated_class_query(context, positives, negatives)
        bindings = _execute_sparql(query)
        results = self._parse_class_results_with_counts(bindings)

        # Female: F2M11 is NOT Female (pos=1), F2F14 IS Female (pos doesn't count)
        # F2M13 is NOT Female (neg=1)
        self.assertIn(NS + "Female", results)
        self.assertEqual(results[NS + "Female"][0], 1)  # only F2M11
        self.assertEqual(results[NS + "Female"][1], 1)  # F2M13

        # Male: F2F14 is NOT Male (pos=1), F2M11 IS Male (pos doesn't count)
        # F2M13 IS Male (neg doesn't count for Male)
        self.assertIn(NS + "Male", results)
        self.assertEqual(results[NS + "Male"][0], 1)  # only F2F14
        self.assertEqual(results[NS + "Male"][1], 0)  # F2M13 IS Male

        # Mother: neither F2M11 nor F2F14 is Mother -> pos=2
        # F2M13 is NOT Mother -> neg=1
        self.assertIn(NS + "Mother", results)
        self.assertEqual(results[NS + "Mother"][0], 2)
        self.assertEqual(results[NS + "Mother"][1], 1)


if __name__ == "__main__":
    unittest.main()


