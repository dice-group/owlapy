"""FutureWarnings on code paths that hand an owlready2-backed object to the user (#310, 1.3).

Each of these defaults changes in owlapy 2.0; passing an RDFLibOntology/SyncOntology yourself
opts in to the new behaviour now and must not warn.
"""

import os
import warnings

import pytest

from owlapy.owl_ontology import Ontology, RDFLibOntology
from owlapy.util_owl_static_funcs import create_ontology

FAMILY = "KGs/Family/family-benchmark_rich_background.owl"
needs_family = pytest.mark.skipif(not os.path.isfile(FAMILY), reason="KGs.zip not downloaded")


def _future_warnings(record):
    return [w for w in record if issubclass(w.category, FutureWarning)]


@pytest.mark.requires_owlready2
def test_create_ontology_default_warns_and_points_to_rdflib():
    with pytest.warns(FutureWarning, match="RDFLibOntology") as record:
        onto = create_ontology("http://example.com/fw")
    assert isinstance(onto, Ontology)
    # stacklevel points at the caller, not at owlapy internals
    assert _future_warnings(record)[0].filename == __file__


def test_create_ontology_with_owlapi_does_not_warn():
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        create_ontology("http://example.com/fw", with_owlapi=True)
    assert not _future_warnings(record)


@needs_family
@pytest.mark.requires_owlready2
def test_structural_reasoner_from_path_warns():
    from owlapy.owl_reasoner import StructuralReasoner
    with pytest.warns(FutureWarning, match="RDFLibReasoner") as record:
        StructuralReasoner(FAMILY)
    assert _future_warnings(record)[0].filename == __file__


@needs_family
@pytest.mark.requires_owlready2
def test_structural_reasoner_from_ontology_has_no_future_warning():
    from owlapy.owl_reasoner import StructuralReasoner
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        StructuralReasoner(Ontology(FAMILY))
    assert not _future_warnings(record)


@needs_family
@pytest.mark.requires_owlready2
def test_nir_reasoner_from_path_warns(tmp_path):
    pytest.importorskip("torch")
    from owlapy.owl_reasoner_nir import NIRReasoner
    # The missing model directory makes construction fail right after the ontology is built.
    with pytest.warns(FutureWarning, match="RDFLibOntology") as record, pytest.raises(FileNotFoundError):
        NIRReasoner(FAMILY, model_path=str(tmp_path / "absent"))
    assert _future_warnings(record)[0].filename == __file__


@needs_family
def test_nir_reasoner_from_rdflib_ontology_has_no_future_warning(tmp_path):
    pytest.importorskip("torch")
    from owlapy.owl_reasoner_nir import NIRReasoner
    with warnings.catch_warnings(record=True) as record, pytest.raises(FileNotFoundError):
        warnings.simplefilter("always")
        NIRReasoner(RDFLibOntology(FAMILY), model_path=str(tmp_path / "absent"))
    assert not _future_warnings(record)
