"""owlapy must never let owlready2 fork a child process to parse a large ontology.

owlready2 (0.4x/0.50) parses files >= 8 MB in a forked ``multiprocessing`` child and waits on a queue
without a timeout; forking a process that runs the JVM and other threads intermittently left that child
stuck, hanging CI for hours in ``StructuralReasoner("KGs/Carcinogenesis/carcinogenesis.owl")``.
"""
import multiprocessing
import os
from unittest import mock

import pytest

owlready2 = pytest.importorskip("owlready2")

from owlapy._lazy_owlready2 import load_ontology  # noqa: E402
from owlapy.owl_ontology import Ontology  # noqa: E402

LARGE = "KGs/Carcinogenesis/carcinogenesis.owl"  # 10 MB, above owlready2's 8 MB fork threshold
SMALL = "KGs/Family/family-benchmark_rich_background.owl"

requires_kgs = pytest.mark.skipif(not os.path.isfile(LARGE) or not os.path.isfile(SMALL), reason="KGs.zip not downloaded")


class _ForkAttempted(Exception):
    pass


def _forbid_processes():
    return mock.patch.object(multiprocessing, "Process", side_effect=_ForkAttempted("owlready2 tried to fork a parser process"))


def _triples(onto):
    return sorted(onto.world.as_rdflib_graph().triples((None, None, None)), key=str)


@requires_kgs
def test_plain_owlready2_would_fork_on_large_files():
    """Guards the regression test below against being vacuous: owlready2 itself does fork on LARGE."""
    if os.path.getsize(LARGE) < 8_000_000 or multiprocessing.get_start_method() != "fork":
        pytest.skip("owlready2 only forks for files >= 8 MB with the 'fork' start method")
    with _forbid_processes():
        try:
            owlready2.World().get_ontology(LARGE).load()
        except _ForkAttempted:
            return
    pytest.skip(f"owlready2 {owlready2.VERSION} parses large files in-process anyway")


@requires_kgs
def test_ontology_parses_large_file_in_process():
    with _forbid_processes():
        onto = Ontology(LARGE)
    assert len(list(onto.classes_in_signature())) > 0


@requires_kgs
@pytest.mark.parametrize("path", [SMALL, os.path.abspath(SMALL), "file://" + os.path.abspath(SMALL)])
def test_load_ontology_matches_plain_load(path):
    expected = owlready2.World().get_ontology(path).load()
    loaded = load_ontology(owlready2.World().get_ontology(path))
    assert loaded.loaded
    assert loaded.base_iri == expected.base_iri
    assert _triples(loaded) == _triples(expected)


@requires_kgs
def test_load_ontology_reuses_persistent_world_cache(tmp_path):
    store = tmp_path / "world.sqlite3"
    world = owlready2.World(filename=str(store))
    load_ontology(world.get_ontology(SMALL))
    world.save()
    world.close()
    copy = tmp_path / "copy.sqlite3"
    copy.write_bytes(store.read_bytes())

    plain_world = owlready2.World(filename=str(copy))
    expected = _triples(plain_world.get_ontology(SMALL).load())

    world = owlready2.World(filename=str(store))
    onto = world.get_ontology(SMALL)
    with mock.patch.object(onto.graph, "parse", side_effect=AssertionError("re-parsed a cached ontology")):
        assert _triples(load_ontology(onto)) == expected
    world.close()
    plain_world.close()


def test_load_ontology_keeps_owlready2_error_for_missing_file(tmp_path):
    missing = str(tmp_path / "missing.owl")
    with pytest.raises(Exception) as plain:
        owlready2.World().get_ontology(missing).load()
    with pytest.raises(type(plain.value)):
        load_ontology(owlready2.World().get_ontology(missing))


def test_load_ontology_passes_explicit_arguments_through():
    onto = mock.Mock(loaded=False)
    load_ontology(onto, reload=True)
    onto.load.assert_called_once_with(reload=True)
