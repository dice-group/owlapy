"""Tests for owlapy.owl_reasoner_nir.NIRReasoner.

Helpers and routing logic are covered with a mocked encoder so CI does not need
pretrained weights. Optional Family integration tests run only when the encoder,
OWL file, and embeddings are on disk. Weights are not fetched in GitHub Actions;
download them locally from
https://files.dice-research.org/datasets/CNIR/trained_models.zip
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from owlapy.class_expression import OWLClass, OWLNothing, OWLObjectSomeValuesFrom, OWLThing
from owlapy.iri import IRI
from owlapy.owl_ontology import RDFLibOntology
from owlapy.owl_property import OWLObjectProperty
from owlapy.owl_reasoner_nir import (
    NIRReasoner,
    _load_entity_embeddings,
    _resolve_architecture,
    _short_name,
)

NS = "http://example.org/family#"
_MINI_OWL = """<?xml version="1.0"?>
<rdf:RDF xmlns="http://example.org/family#"
     xml:base="http://example.org/family"
     xmlns:owl="http://www.w3.org/2002/07/owl#"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
    <owl:Ontology rdf:about="http://example.org/family"/>
    <owl:Class rdf:about="http://example.org/family#Person"/>
    <owl:Class rdf:about="http://example.org/family#Female"/>
    <owl:ObjectProperty rdf:about="http://example.org/family#hasChild"/>
    <owl:NamedIndividual rdf:about="http://example.org/family#Alice">
        <rdf:type rdf:resource="http://example.org/family#Female"/>
        <rdf:type rdf:resource="http://example.org/family#Person"/>
    </owl:NamedIndividual>
    <owl:NamedIndividual rdf:about="http://example.org/family#Bob">
        <rdf:type rdf:resource="http://example.org/family#Person"/>
    </owl:NamedIndividual>
</rdf:RDF>
"""

_OWLAPY_ROOT = Path(__file__).resolve().parents[1]
_WORKSPACE = _OWLAPY_ROOT.parent


def _first_existing(*candidates: Path) -> Path:
    for path in candidates:
        if path.is_file() or (path.is_dir() and (path / "config.json").is_file()):
            return path
    return candidates[0]


_FAMILY_OWL = _first_existing(
    _OWLAPY_ROOT / "KGs" / "Family" / "family-benchmark_rich_background.owl",
)
_FAMILY_EMB = _first_existing(
    _WORKSPACE / "trained_models" / "embeddings" / "family" / "DeCaL_entity_embeddings.csv",
    _OWLAPY_ROOT / "trained_models" / "embeddings" / "family" / "DeCaL_entity_embeddings.csv",
)
_FAMILY_MODEL = _first_existing(
    _WORKSPACE / "trained_models" / "nir_pretrained_models" / "NIR_Transformer_family",
    _OWLAPY_ROOT / "trained_models" / "nir_pretrained_models" / "NIR_Transformer_family",
)
_FAMILY_COMPOSITE = _first_existing(
    _WORKSPACE / "trained_models" / "nir_pretrained_models" / "NIR_Composite_family",
    _OWLAPY_ROOT / "trained_models" / "nir_pretrained_models" / "NIR_Composite_family",
)


def _family_assets():
    return _FAMILY_OWL.is_file() and _FAMILY_EMB.is_file() and (_FAMILY_MODEL / "config.json").is_file()


def _family_composite_assets():
    weights = (_FAMILY_COMPOSITE / "model.safetensors").is_file() or (_FAMILY_COMPOSITE / "pytorch_model.bin").is_file()
    return _FAMILY_OWL.is_file() and _FAMILY_EMB.is_file() and (_FAMILY_COMPOSITE / "config.json").is_file() and weights


def test_short_name_from_iri():
    assert _short_name("http://example.org/family#Alice") == "family#Alice"
    assert _short_name("Alice") == "Alice"


def test_resolve_architecture_from_config(tmp_path):
    (tmp_path / "config.json").write_text(json.dumps({"architectures": ["NIRLSTM"]}))
    assert _resolve_architecture(str(tmp_path), None) == "NIRLSTM"
    assert _resolve_architecture(str(tmp_path), "transformer") == "transformer"
    assert _resolve_architecture(str(tmp_path / "missing"), None) == "NIRTransformer"

    (tmp_path / "config.json").write_text(json.dumps({"architectures": ["NIRComposite"]}))
    assert _resolve_architecture(str(tmp_path), None) == "NIRComposite"


def test_load_entity_embeddings_csv_and_directory(tmp_path):
    csv_path = tmp_path / "DeCaL_entity_embeddings.csv"
    pd.DataFrame({"0": [0.1, 0.2], "1": [0.3, 0.4]}, index=["Alice", "http://ex.org#Bob"]).to_csv(csv_path)
    from_file, _ = _load_entity_embeddings(str(csv_path), None)
    assert list(from_file.index) == ["Alice", "ex.org#Bob"]

    nested = tmp_path / "dataset" / "embeddings"
    nested.mkdir(parents=True)
    csv_path.rename(nested / "DeCaL_entity_embeddings.csv")
    from_dir, _ = _load_entity_embeddings(str(tmp_path / "dataset"), None)
    assert "Alice" in from_dir.index


def test_load_entity_embeddings_missing():
    with pytest.raises(FileNotFoundError, match="entity_embeddings"):
        _load_entity_embeddings("/no/such/path", None)


def _write_mini_kb(root: Path):
    owl_path = root / "onto.owl"
    owl_path.write_text(_MINI_OWL)
    emb_path = root / "emb.csv"
    pd.DataFrame({"0": [0.1, 0.5], "1": [0.2, 0.6]}, index=["family#Alice", "family#Bob"]).to_csv(emb_path)
    model_dir = root / "model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text(json.dumps({"architectures": ["NIRTransformer"]}))
    return owl_path, emb_path, model_dir


def _fake_scores(_model, _tokenizer, all_ind_embs, exprs, hidden_size, chunk_size=1024):
    n = all_ind_embs.shape[0]
    scores = np.zeros((1, n), dtype=np.float32)
    # High score only for the first individual in the sorted scored list (Alice).
    scores[0, 0] = 0.9
    return scores


@pytest.fixture
def nir_reasoner(tmp_path):
    pytest.importorskip("torch")
    owl_path, emb_path, model_dir = _write_mini_kb(tmp_path)
    onto = RDFLibOntology(str(owl_path))
    with patch("owlapy.owl_reasoner_nir._register_and_load", return_value=(object(), object())):
        reasoner = NIRReasoner(
            onto,
            model_path=str(model_dir),
            embeddings_path=str(emb_path),
            device="cpu",
            symbolic_max_length=1,
        )
    return reasoner


def test_missing_model_directory_raises(tmp_path):
    pytest.importorskip("torch")
    owl_path, emb_path, _ = _write_mini_kb(tmp_path)
    onto = RDFLibOntology(str(owl_path))
    with pytest.raises(FileNotFoundError, match="NIR model directory"):
        NIRReasoner(onto, model_path=str(tmp_path / "absent"), embeddings_path=str(emb_path), device="cpu")


def test_no_overlapping_individuals_raises(tmp_path):
    pytest.importorskip("torch")
    owl_path, _, model_dir = _write_mini_kb(tmp_path)
    other = tmp_path / "other.csv"
    pd.DataFrame({"0": [0.1], "1": [0.2]}, index=["Nobody"]).to_csv(other)
    onto = RDFLibOntology(str(owl_path))
    with patch("owlapy.owl_reasoner_nir._register_and_load", return_value=(object(), object())):
        with pytest.raises(RuntimeError, match="overlapping individuals"):
            NIRReasoner(onto, model_path=str(model_dir), embeddings_path=str(other), device="cpu")


def test_thing_nothing_and_named_class_use_symbolic_fallback(nir_reasoner):
    person = OWLClass(IRI(NS, "Person"))
    all_inds = {ind.iri.remainder for ind in nir_reasoner.instances(OWLThing)}
    assert all_inds == {"Alice", "Bob"}
    assert set(nir_reasoner.instances(OWLNothing)) == set()

    named = {ind.iri.remainder for ind in nir_reasoner.instances(person)}
    assert "Alice" in named and "Bob" in named
    stats = nir_reasoner.retrieval_stats()
    assert stats["n_symbolic_calls"] >= 1
    assert stats["n_nir_calls"] == 0


def test_complex_expression_uses_nir_scores_and_cache(nir_reasoner):
    has_child = OWLObjectProperty(IRI(NS, "hasChild"))
    person = OWLClass(IRI(NS, "Person"))
    expr = OWLObjectSomeValuesFrom(property=has_child, filler=person)
    with patch("owlapy.owl_reasoner_nir._score_all_inds", side_effect=_fake_scores):
        first = {ind.iri.remainder for ind in nir_reasoner.instances(expr)}
        second = {ind.iri.remainder for ind in nir_reasoner.instances(expr)}
    assert first == {"Alice"}
    assert second == first
    stats = nir_reasoner.retrieval_stats()
    assert stats["n_nir_calls"] == 2
    assert stats["n_cache_hits"] >= 1
    assert stats["max_query_length"] > 1


def test_tbox_is_delegated(nir_reasoner):
    person = OWLClass(IRI(NS, "Person"))
    assert list(nir_reasoner.sub_classes(person)) is not None
    assert "NIRReasoner" in str(nir_reasoner)
    assert nir_reasoner.get_root_ontology() is nir_reasoner.ontology


@pytest.mark.skipif(not _family_assets(), reason="Family OWL / embeddings / NIR Transformer not on disk")
def test_family_pretrained_named_class_is_symbolic():
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    from owlapy.owl_ontology import Ontology

    onto = Ontology(IRI.create("file://" + os.path.abspath(_FAMILY_OWL)))
    reasoner = NIRReasoner(
        onto,
        model_path=str(_FAMILY_MODEL),
        embeddings_path=str(_FAMILY_EMB),
        device="cpu",
        model="transformer",
        symbolic_max_length=1,
    )
    brother = OWLClass(IRI("http://www.benchmark.org/family#", "Brother"))
    retrieved = set(reasoner.instances(brother))
    assert len(retrieved) > 0
    stats = reasoner.retrieval_stats()
    assert stats["n_symbolic_calls"] >= 1
    assert stats["n_nir_calls"] == 0
    has_sibling = OWLObjectProperty(IRI("http://www.benchmark.org/family#", "hasSibling"))
    complex_ce = OWLObjectSomeValuesFrom(property=has_sibling, filler=brother)
    complex_hits = set(reasoner.instances(complex_ce))
    assert isinstance(complex_hits, set)
    assert reasoner.retrieval_stats()["n_nir_calls"] >= 1


@pytest.mark.skipif(not _family_composite_assets(), reason="Family OWL / embeddings / NIR Composite not on disk")
def test_family_pretrained_composite_scores_complex_expression():
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    from owlapy.owl_ontology import Ontology

    onto = Ontology(IRI.create("file://" + os.path.abspath(_FAMILY_OWL)))
    reasoner = NIRReasoner(
        onto,
        model_path=str(_FAMILY_COMPOSITE),
        embeddings_path=str(_FAMILY_EMB),
        device="cpu",
        symbolic_max_length=1,
    )
    assert type(reasoner._encoder).__name__ == "NIRComposite"
    assert reasoner.tokenizer is None
    brother = OWLClass(IRI("http://www.benchmark.org/family#", "Brother"))
    has_sibling = OWLObjectProperty(IRI("http://www.benchmark.org/family#", "hasSibling"))
    complex_ce = OWLObjectSomeValuesFrom(property=has_sibling, filler=brother)
    scores = reasoner.membership_scores(complex_ce)
    assert scores.shape[0] == len(reasoner.all_individuals_arr)
    assert float(scores.min()) >= 0.0
    assert float(scores.max()) <= 1.0
    hits = set(reasoner.instances(complex_ce))
    assert isinstance(hits, set)
    assert reasoner.retrieval_stats()["n_nir_calls"] >= 1
