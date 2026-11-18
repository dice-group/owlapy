"""Behaviour of the rdflib-based make_kb_* helpers (ported from owlready2 in #310)."""
import os

import pytest
from rdflib import RDF, Graph, URIRef

from owlapy.owl_ontology import RDFLibOntology
from owlapy.util_owl_static_funcs import make_kb_incomplete, make_kb_incomplete_ass, make_kb_inconsistent

KB = "KGs/Family/family-benchmark_rich_background.owl"
pytestmark = pytest.mark.skipif(not os.path.isfile(KB), reason="KGs.zip not downloaded")


@pytest.fixture(scope="module")
def kb():
    onto = RDFLibOntology(KB)
    return {
        "graph": onto.rdflib_graph,
        "individuals": {URIRef(i.str) for i in onto.individuals_in_signature()},
        "properties": {URIRef(p.str) for p in onto.object_properties_in_signature()} | {URIRef(p.str) for p in onto.data_properties_in_signature()},
    }


def _load(path):
    return Graph().parse(path, format="xml")


def _assertions(g, kb):
    return {(s, p, o) for s, p, o in g if s in kb["individuals"] and p in kb["properties"]}


def test_make_kb_incomplete_removes_rate_percent_of_individuals_completely(kb, tmp_path):
    out = str(tmp_path / "out.owl")
    removed = make_kb_incomplete(KB, out, 20, seed=1)

    assert len(removed) == int(len(kb["individuals"]) * 0.2) > 0
    assert {URIRef(i) for i in removed} <= kb["individuals"]
    g = _load(out)
    for ind in map(URIRef, removed):
        assert (ind, None, None) not in g and (None, None, ind) not in g
    kept = kb["individuals"] - {URIRef(i) for i in removed}
    assert all((ind, RDF.type, None) in g for ind in kept)


def test_make_kb_incomplete_is_deterministic_per_seed(tmp_path):
    first = make_kb_incomplete(KB, str(tmp_path / "a.owl"), 20, seed=7)
    again = make_kb_incomplete(KB, str(tmp_path / "b.owl"), 20, seed=7)
    other = make_kb_incomplete(KB, str(tmp_path / "c.owl"), 20, seed=8)
    assert first == again != other


def test_make_kb_incomplete_ass_removes_only_property_assertions(kb, tmp_path):
    out = str(tmp_path / "out.owl")
    make_kb_incomplete_ass(KB, out, 30, seed=1)

    g = _load(out)
    before, after = _assertions(kb["graph"], kb), _assertions(g, kb)
    assert after < before
    assert len(before) - len(after) == int(len(before) * 0.3)
    # everything that is not a property assertion of an individual is untouched
    assert set(kb["graph"]) - before == set(g) - after


def test_make_kb_inconsistent_adds_new_statements(kb, tmp_path):
    out = str(tmp_path / "out.owl")
    added = make_kb_inconsistent(KB, out, 1, seed=1)

    assert len(added) == int(len(kb["graph"]) * 0.01) > 0
    g = _load(out)
    assert set(kb["graph"]) < set(g)
    assert len(set(g) - set(kb["graph"])) == len(added)
    assert make_kb_inconsistent(KB, str(tmp_path / "again.owl"), 1, seed=1) == added


def test_zero_rate_changes_nothing(kb, tmp_path):
    for fn in (make_kb_incomplete, make_kb_incomplete_ass, make_kb_inconsistent):
        out = str(tmp_path / f"{fn.__name__}.owl")
        fn(KB, out, 0, 1)
        assert set(_load(out)) == set(kb["graph"]), fn.__name__
