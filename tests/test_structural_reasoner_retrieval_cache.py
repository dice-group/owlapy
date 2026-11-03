"""StructuralReasoner retrieval caches: the all-individuals set and the per-expression memo.

The memo is keyed by class-expression equality, so the main risk is a wrong answer from a cache hit. Most tests
therefore compare a memoising reasoner with one that has the memo turned off (``expression_cache_size=0``) over many
nested expressions, on three ontologies: Family (object properties), a small generated ontology whose data property
values only differ by datatype (``1``, ``1.0``, ``"1"``, ``true``) and Mutagenesis (real numeric data).

Caches are only active on unmodified ontologies, so the generated ontology is saved to disk and reloaded.
"""
import itertools
import random
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

pytest.importorskip("owlready2")

from owlapy.class_expression import (  # noqa: E402
    OWLClass,
    OWLDataAllValuesFrom,
    OWLDataExactCardinality,
    OWLDataHasValue,
    OWLDataMaxCardinality,
    OWLDataMinCardinality,
    OWLDataOneOf,
    OWLDataSomeValuesFrom,
    OWLObjectAllValuesFrom,
    OWLObjectComplementOf,
    OWLObjectExactCardinality,
    OWLObjectHasValue,
    OWLObjectIntersectionOf,
    OWLObjectMaxCardinality,
    OWLObjectMinCardinality,
    OWLObjectOneOf,
    OWLObjectSomeValuesFrom,
    OWLObjectUnionOf,
    OWLThing,
)
from owlapy.iri import IRI  # noqa: E402
from owlapy.owl_axiom import (  # noqa: E402
    OWLClassAssertionAxiom,
    OWLDataPropertyAssertionAxiom,
    OWLDeclarationAxiom,
    OWLObjectPropertyAssertionAxiom,
)
from owlapy.owl_data_ranges import OWLDataComplementOf, OWLDataIntersectionOf, OWLDataUnionOf  # noqa: E402
from owlapy.owl_individual import OWLNamedIndividual  # noqa: E402
from owlapy.owl_literal import (  # noqa: E402
    BooleanOWLDatatype,
    DoubleOWLDatatype,
    IntegerOWLDatatype,
    OWLLiteral,
    StringOWLDatatype,
)
from owlapy.owl_ontology import Ontology  # noqa: E402
from owlapy.owl_property import OWLDataProperty, OWLObjectInverseOf, OWLObjectProperty  # noqa: E402
from owlapy.owl_reasoner import StructuralReasoner  # noqa: E402
from owlapy.providers import (  # noqa: E402
    owl_datatype_max_inclusive_restriction,
    owl_datatype_min_inclusive_restriction,
    owl_datatype_min_max_inclusive_restriction,
)

KGS = Path(__file__).resolve().parents[1] / "KGs"
FATHER = KGS / "Family" / "father.owl"
MUTAGENESIS = KGS / "Mutagenesis" / "mutagenesis.owl"

NS = "http://example.com/father#"
MALE, FEMALE, PERSON = OWLClass(IRI(NS, "male")), OWLClass(IRI(NS, "female")), OWLClass(IRI(NS, "person"))
HAS_CHILD = OWLObjectProperty(IRI(NS, "hasChild"))
ANNA, MARKUS = OWLNamedIndividual(IRI(NS, "anna")), OWLNamedIndividual(IRI(NS, "markus"))


def _load(path: Path) -> Ontology:
    if not path.exists():
        raise unittest.SkipTest(f"{path} not found (download KGs.zip, see CLAUDE.md)")
    return Ontology(IRI.create(path.as_uri()))


def _reasoner(onto: Ontology, **kwargs) -> StructuralReasoner:
    with pytest.warns(DeprecationWarning):
        return StructuralReasoner(onto, **kwargs)


def _assert_memo_matches_uncached(test: unittest.TestCase, onto: Ontology, expressions, repeat: int = 2):
    """Answer `expressions` (each `repeat` times) with one memoising reasoner and compare every answer with a
    reasoner whose memo is off. Retrieval errors must match too."""
    memoising, uncached = _reasoner(onto), _reasoner(onto, expression_cache_size=0)
    for ce in list(expressions) * repeat:
        with test.subTest(ce=ce):
            try:
                expected = frozenset(uncached.instances(ce))
            except Exception as exc:  # unsupported expressions must fail the same way with the memo on
                with test.assertRaises(type(exc)):
                    memoising.instances(ce)
                continue
            result = memoising.instances(ce)
            test.assertIsInstance(result, frozenset)
            test.assertEqual(result, expected)
    return memoising


def _assert_equal_keys_mean_equal_answers(test: unittest.TestCase, onto: Ontology, expressions):
    """The memo returns the answer of any key that compares equal: equal expressions must hash equally and have the
    same instances."""
    uncached = _reasoner(onto, expression_cache_size=0)
    for a, b in itertools.combinations(expressions, 2):
        if a == b:
            with test.subTest(a=a, b=b):
                test.assertEqual(hash(a), hash(b))
                test.assertEqual(frozenset(uncached.instances(a)), frozenset(uncached.instances(b)))


# ---------------------------------------------------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------------------------------------------------

def _family_expressions():
    """Nested object-property expressions of every kind the memo and the all-individuals set are used for."""
    atoms = [MALE, FEMALE, PERSON, OWLThing]
    inverse = OWLObjectInverseOf(HAS_CHILD)
    level1 = atoms + [OWLObjectComplementOf(MALE), OWLObjectOneOf([ANNA, MARKUS]), OWLObjectHasValue(HAS_CHILD, ANNA)]
    for filler in atoms:
        level1 += [OWLObjectSomeValuesFrom(HAS_CHILD, filler), OWLObjectAllValuesFrom(HAS_CHILD, filler),
                   OWLObjectSomeValuesFrom(inverse, filler), OWLObjectMinCardinality(2, HAS_CHILD, filler),
                   OWLObjectMaxCardinality(1, HAS_CHILD, filler), OWLObjectExactCardinality(1, HAS_CHILD, filler)]
    level2 = []
    for a, b in itertools.combinations(level1, 2):
        level2 += [OWLObjectIntersectionOf([a, b]), OWLObjectUnionOf([a, b])]
    level3 = [OWLObjectSomeValuesFrom(HAS_CHILD, e) for e in level2[::7]]
    level3 += [OWLObjectComplementOf(e) for e in level2[::11]]
    level3 += [OWLObjectAllValuesFrom(HAS_CHILD, e) for e in level2[::13]]
    return level1 + level2 + level3


TNS = "http://example.com/memo-data#"
THING_A = OWLClass(IRI(TNS, "A"))
LINK = OWLObjectProperty(IRI(TNS, "link"))
VALUE, AGE, SCORE, NAME, FLAG = (OWLDataProperty(IRI(TNS, n)) for n in ("value", "age", "score", "code", "flag"))
DATA_PROPERTIES = [VALUE, AGE, SCORE, NAME, FLAG]

# Literals that are equal as Python values (1 == 1.0 == True) but not as OWL literals, plus spelled-out duplicates.
LITERALS = [
    OWLLiteral(1), OWLLiteral(1.0), OWLLiteral("1"), OWLLiteral(True), OWLLiteral(2), OWLLiteral(2.5),
    OWLLiteral("a"), OWLLiteral(False), OWLLiteral(0), OWLLiteral(0.0),
    OWLLiteral("1", IntegerOWLDatatype), OWLLiteral("1.0", DoubleOWLDatatype), OWLLiteral("true", BooleanOWLDatatype),
]


def _data_ranges():
    return [
        IntegerOWLDatatype, DoubleOWLDatatype, StringOWLDatatype, BooleanOWLDatatype,
        owl_datatype_min_inclusive_restriction(1), owl_datatype_min_inclusive_restriction(1.0),
        owl_datatype_max_inclusive_restriction(1), owl_datatype_max_inclusive_restriction(1.0),
        owl_datatype_min_max_inclusive_restriction(1, 2), owl_datatype_min_max_inclusive_restriction(1.0, 2.0),
        OWLDataOneOf([OWLLiteral(1)]), OWLDataOneOf([OWLLiteral(1.0)]), OWLDataOneOf([OWLLiteral("1")]),
        OWLDataOneOf([OWLLiteral(1), OWLLiteral(1.0)]), OWLDataOneOf([OWLLiteral(1.0), OWLLiteral(1)]),
        OWLDataComplementOf(IntegerOWLDatatype), OWLDataUnionOf([IntegerOWLDatatype, StringOWLDatatype]),
        OWLDataIntersectionOf([DoubleOWLDatatype, owl_datatype_min_inclusive_restriction(1.0)]),
    ]


def _data_expressions():
    level1 = [OWLDataHasValue(p, lit) for p in DATA_PROPERTIES for lit in LITERALS]
    for p in DATA_PROPERTIES:
        for r in _data_ranges():
            level1 += [OWLDataSomeValuesFrom(p, r), OWLDataAllValuesFrom(p, r), OWLDataMinCardinality(1, p, r),
                       OWLDataMinCardinality(2, p, r), OWLDataMaxCardinality(1, p, r), OWLDataExactCardinality(1, p, r)]
    rng = random.Random(0)
    nested = []
    for _ in range(150):
        a, b = rng.sample(level1, 2)
        nested += [OWLObjectIntersectionOf([a, b]), OWLObjectUnionOf([a, b]), OWLObjectComplementOf(a),
                   OWLObjectSomeValuesFrom(LINK, a), OWLObjectIntersectionOf([THING_A, OWLObjectAllValuesFrom(LINK, b)])]
    return level1 + nested


def _write_data_ontology(path: Path) -> None:
    """Individuals whose values for one property differ only by datatype, plus typed properties and a link."""
    onto = Ontology(IRI.create(TNS.rstrip("#")), load=False)
    individuals = {n: OWLNamedIndividual(IRI(TNS, n)) for n in ("i_int", "i_dbl", "i_str", "i_bool", "i_two", "i_none")}
    axioms = [OWLDeclarationAxiom(THING_A), OWLDeclarationAxiom(LINK)]
    axioms += [OWLDeclarationAxiom(p) for p in DATA_PROPERTIES]
    axioms += [OWLDeclarationAxiom(i) for i in individuals.values()]
    values = {"i_int": [OWLLiteral(1)], "i_dbl": [OWLLiteral(1.0)], "i_str": [OWLLiteral("1")],
              "i_bool": [OWLLiteral(True)], "i_two": [OWLLiteral(2), OWLLiteral(2.5)]}
    for name, literals in values.items():
        axioms += [OWLDataPropertyAssertionAxiom(individuals[name], VALUE, lit) for lit in literals]
    typed = [("i_int", AGE, OWLLiteral(1)), ("i_two", AGE, OWLLiteral(2)), ("i_two", AGE, OWLLiteral(0)),
             ("i_dbl", SCORE, OWLLiteral(1.0)), ("i_two", SCORE, OWLLiteral(2.5)), ("i_str", NAME, OWLLiteral("1")),
             ("i_none", NAME, OWLLiteral("a")), ("i_bool", FLAG, OWLLiteral(True)), ("i_int", FLAG, OWLLiteral(False))]
    axioms += [OWLDataPropertyAssertionAxiom(individuals[s], p, lit) for s, p, lit in typed]
    axioms += [OWLClassAssertionAxiom(individuals[n], THING_A) for n in ("i_int", "i_str", "i_none")]
    axioms += [OWLObjectPropertyAssertionAxiom(individuals[s], LINK, individuals[o])
               for s, o in [("i_int", "i_dbl"), ("i_dbl", "i_str"), ("i_none", "i_bool"), ("i_none", "i_two")]]
    onto.add_axiom(axioms)
    onto.save(path=str(path))


# ---------------------------------------------------------------------------------------------------------------------
# Correctness of cache hits
# ---------------------------------------------------------------------------------------------------------------------

class TestMemoisedResultsAreCorrect(unittest.TestCase):
    def test_family_object_property_expressions(self):
        onto = _load(FATHER)
        _assert_memo_matches_uncached(self, onto, _family_expressions())
        _assert_equal_keys_mean_equal_answers(self, onto, _family_expressions())

    def test_literals_that_differ_only_by_datatype(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "memo_data.owl"
            _write_data_ontology(path)
            onto = Ontology(IRI.create(path.as_uri()))
            # Sanity check of the fixture: the four `value` literals equal to 1 in Python have different instances.
            uncached = _reasoner(onto, expression_cache_size=0)
            answers = [frozenset(uncached.instances(OWLDataHasValue(VALUE, lit))) for lit in LITERALS[:4]]
            self.assertEqual(len(set(answers)), 4, answers)

            _assert_memo_matches_uncached(self, onto, _data_expressions())
            _assert_equal_keys_mean_equal_answers(self, onto, _data_expressions())

    def test_mutagenesis_data_restrictions(self):
        onto = _load(MUTAGENESIS)
        mns = "http://dl-learner.org/mutagenesis#"
        charge, lumo, act = (OWLDataProperty(IRI(mns, n)) for n in ("charge", "lumo", "act"))
        has_atom, has_bond = OWLObjectProperty(IRI(mns, "hasAtom")), OWLObjectProperty(IRI(mns, "hasBond"))
        compound, carbon = OWLClass(IRI(mns, "Compound")), OWLClass(IRI(mns, "Carbon"))
        ranges = [DoubleOWLDatatype, owl_datatype_min_inclusive_restriction(0.0),
                  owl_datatype_max_inclusive_restriction(-0.1), owl_datatype_min_max_inclusive_restriction(-1.0, 1.0)]
        level1 = [compound, carbon]
        for p in (charge, lumo, act):
            for r in ranges:
                level1 += [OWLDataSomeValuesFrom(p, r), OWLDataMinCardinality(1, p, r), OWLDataMaxCardinality(0, p, r)]
        rng = random.Random(1)
        nested = []
        for _ in range(25):
            a, b = rng.sample(level1, 2)
            nested += [OWLObjectSomeValuesFrom(has_atom, OWLObjectIntersectionOf([a, b])),
                       OWLObjectIntersectionOf([compound, OWLObjectComplementOf(a)]), OWLObjectUnionOf([a, b])]
        nested += [OWLObjectSomeValuesFrom(has_bond, OWLThing), OWLObjectAllValuesFrom(has_atom, carbon)]
        _assert_memo_matches_uncached(self, onto, level1 + nested)


# ---------------------------------------------------------------------------------------------------------------------
# Cache behaviour
# ---------------------------------------------------------------------------------------------------------------------

class TestCacheBehaviour(unittest.TestCase):
    def setUp(self):
        self.onto = _load(FATHER)

    def test_all_individuals_are_read_from_the_ontology_once(self):
        reasoner = _reasoner(self.onto)
        with patch.object(Ontology, "individuals_in_signature", autospec=True,
                          side_effect=Ontology.individuals_in_signature) as walk:
            first = reasoner.instances(OWLObjectComplementOf(MALE))
            reasoner.instances(OWLObjectAllValuesFrom(HAS_CHILD, FEMALE))
            reasoner.instances(OWLObjectMaxCardinality(1, HAS_CHILD, PERSON))
        self.assertEqual(walk.call_count, 1)
        self.assertEqual(first, frozenset(_reasoner(self.onto, class_cache=False).instances(OWLObjectComplementOf(MALE))))

    def test_memo_is_bounded_and_skips_named_classes(self):
        reasoner = _reasoner(self.onto, expression_cache_size=5)
        for ce in _family_expressions()[:40]:
            reasoner.instances(ce)
            self.assertLessEqual(len(reasoner._ce_to_ind), 5)
            self.assertFalse(any(isinstance(key.ce, OWLClass) for key in reasoner._ce_to_ind))

    def test_size_zero_turns_the_memo_off(self):
        reasoner = _reasoner(self.onto, expression_cache_size=0)
        for ce in _family_expressions()[:20]:
            reasoner.instances(ce)
        self.assertEqual(len(reasoner._ce_to_ind), 0)
        with self.assertRaises(ValueError):
            StructuralReasoner(self.onto, expression_cache_size=-1)

    def test_disabled_class_cache_still_retrieves_correctly(self):
        uncached = _reasoner(self.onto, class_cache=False)
        cached = _reasoner(self.onto)
        for ce in _family_expressions()[:60]:
            with self.subTest(ce=ce):
                self.assertEqual(frozenset(uncached.instances(ce)), cached.instances(ce))
        self.assertEqual(len(uncached._ce_to_ind), 0)

    def test_results_are_identical_across_reset_and_after_disabling(self):
        reasoner = _reasoner(self.onto)
        expressions = _family_expressions()[:80]
        before = [reasoner.instances(ce) for ce in expressions]

        reasoner.reset()
        self.assertEqual(len(reasoner._ce_to_ind), 0)
        self.assertIsNone(reasoner._all_inds)
        self.assertTrue(reasoner.class_cache)
        self.assertEqual([reasoner.instances(ce) for ce in expressions], before)
        self.assertGreater(len(reasoner._ce_to_ind), 0)

        reasoner.reset_and_disable_cache()
        self.assertEqual(len(reasoner._ce_to_ind), 0)
        self.assertIsNone(reasoner._all_inds)
        self.assertEqual([frozenset(reasoner.instances(ce)) for ce in expressions], before)
        self.assertEqual(len(reasoner._ce_to_ind), 0)
        self.assertIsNone(reasoner._all_inds)

    def test_modifying_the_ontology_invalidates_cached_results(self):
        reasoner = _reasoner(self.onto)
        some_male_child = OWLObjectSomeValuesFrom(HAS_CHILD, MALE)
        not_male = OWLObjectComplementOf(MALE)
        before_some, before_not = reasoner.instances(some_male_child), reasoner.instances(not_male)

        newcomer = OWLNamedIndividual(IRI(NS, "newcomer"))
        self.assertIn(ANNA, before_not)
        self.onto.add_axiom(OWLClassAssertionAxiom(ANNA, MALE))
        self.onto.add_axiom(OWLClassAssertionAxiom(newcomer, PERSON))

        after_not = reasoner.instances(not_male)
        self.assertNotIn(ANNA, after_not)
        self.assertIn(newcomer, after_not)
        # Caches are cleared and disabled after a modification, as for the existing class and property caches, and
        # nested results are recomputed from the modified ontology.
        self.assertFalse(reasoner.class_cache)
        self.assertEqual(len(reasoner._ce_to_ind), 0)
        self.assertIsNone(reasoner._all_inds)
        after_some = frozenset(reasoner.instances(some_male_child))
        self.assertEqual(after_some, frozenset(_reasoner(self.onto).instances(some_male_child)))
        self.assertTrue(before_some <= after_some)

    def test_direct_owlready2_edits_need_reset(self):
        # Edits through owlready2 objects bypass add_axiom, so is_modified stays False and cached results are kept
        # (documented limitation, as for the named-class cache). reset() makes the reasoner see them.
        reasoner = _reasoner(self.onto)
        not_male = OWLObjectComplementOf(MALE)
        self.assertIn(ANNA, reasoner.instances(not_male))

        world = self.onto._world
        world[ANNA.str].is_a.append(world[MALE.str])
        self.assertFalse(self.onto.is_modified)
        self.assertIn(ANNA, reasoner.instances(not_male))

        reasoner.reset()
        self.assertNotIn(ANNA, reasoner.instances(not_male))


# ---------------------------------------------------------------------------------------------------------------------
# Concurrent use
# ---------------------------------------------------------------------------------------------------------------------

class TestConcurrentUse(unittest.TestCase):
    def setUp(self):
        self.onto = _load(FATHER)

    def test_threads_sharing_the_memo_get_correct_results(self):
        # Exercises the memo's own locking: a small memo forces evictions while other threads read and insert.
        # owlready2's SQLite backend is not safe for concurrent queries, so retrieval itself is replaced by a lookup of
        # answers computed beforehand; every call still goes through the memo.
        expressions = _family_expressions()
        expected = {ce: frozenset(_reasoner(self.onto, expression_cache_size=0).instances(ce)) for ce in expressions}
        shared = _reasoner(self.onto, expression_cache_size=8)
        calls = []

        def compute(ce):
            calls.append(ce)
            time.sleep(0)  # let other threads interleave between lookup and insert
            return expected[ce]

        patcher = patch.object(shared, "_compute_instances", side_effect=compute)
        patcher.start()
        self.addCleanup(patcher.stop)
        errors = []

        def work(seed):
            order = list(expressions)
            random.Random(seed).shuffle(order)
            try:
                for ce in order:
                    if shared.instances(ce) != expected[ce]:
                        errors.append(ce)
            except Exception as exc:  # pragma: no cover - reported below
                errors.append(exc)

        threads = [threading.Thread(target=work, args=(seed,)) for seed in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        self.assertLessEqual(len(shared._ce_to_ind), 8)
        self.assertGreater(len(calls), len(expressions))  # evictions caused recomputation

    def _finish_after_reset(self, reset):
        """Start a retrieval that blocks, call `reset` meanwhile, then let it finish (like a timed-out retrieval that
        keeps running in its worker thread)."""
        reasoner = _reasoner(self.onto)
        ce = OWLObjectSomeValuesFrom(HAS_CHILD, MALE)
        started, release = threading.Event(), threading.Event()
        compute = reasoner._compute_instances

        def slow_compute(expression):
            if expression == ce:
                started.set()
                release.wait(5)
            return compute(expression)

        results = []
        with patch.object(reasoner, "_compute_instances", side_effect=slow_compute):
            worker = threading.Thread(target=lambda: results.append(reasoner._find_instances(ce)))
            worker.start()
            self.assertTrue(started.wait(5))
            reset(reasoner)
            release.set()
            worker.join(5)
        self.assertEqual(results, [frozenset(_reasoner(self.onto).instances(ce))])
        return reasoner, ce

    def test_result_computed_before_a_reset_is_not_inserted(self):
        reasoner, ce = self._finish_after_reset(StructuralReasoner.reset)
        self.assertNotIn(ce, reasoner._ce_to_ind)
        self.assertTrue(reasoner.class_cache)

    def test_result_computed_before_disabling_is_not_inserted(self):
        reasoner, ce = self._finish_after_reset(StructuralReasoner.reset_and_disable_cache)
        self.assertEqual(len(reasoner._ce_to_ind), 0)

    def test_all_individuals_read_before_a_reset_are_not_kept(self):
        reasoner = _reasoner(self.onto)
        started, release = threading.Event(), threading.Event()
        read = Ontology.individuals_in_signature

        def slow_read(onto):
            started.set()
            release.wait(5)
            return read(onto)

        with patch.object(Ontology, "individuals_in_signature", autospec=True, side_effect=slow_read):
            worker = threading.Thread(target=reasoner._all_individuals)
            worker.start()
            self.assertTrue(started.wait(5))
            reasoner.reset()
            release.set()
            worker.join(5)
        self.assertIsNone(reasoner._all_inds)


if __name__ == "__main__":
    unittest.main()
