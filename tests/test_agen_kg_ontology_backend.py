"""Which ontology AGenKG's extractors build (#310, 1.6).

The default is still an owlready2-backed `Ontology`, with a FutureWarning pointing at the caller;
passing `ontology=` opts in to `RDFLibOntology` (owlapy 2.0's default) now; and without owlready2
installed -- the `agentic` extra doesn't install it -- the extractors fall back to `RDFLibOntology`
instead of failing after every LLM call has been made. Every dspy.Predict is stubbed.
"""
import os
import warnings
from unittest.mock import MagicMock, patch

import pytest
import rdflib

from owlapy.agen_kg import graph_extractor
from owlapy.agen_kg.graph_extracting_models import DomainGraphExtractor, OpenGraphExtractor
from owlapy.class_expression import OWLClass
from owlapy.owl_axiom import OWLClassAssertionAxiom, OWLObjectPropertyAssertionAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import RDFLibOntology
from owlapy.owl_property import OWLObjectProperty

NS = "http://example.com/agen_backend#"
EXTRACTORS = [OpenGraphExtractor, DomainGraphExtractor]
EXAMPLE_KEYS = ("entity_extraction", "triples_extraction", "type_assertion", "type_generation",
                "literal_extraction", "triples_with_numeric_literals_extraction")


def _stubbed(extractor_cls):
    extractor = extractor_cls()
    extractor.plan_decomposer = MagicMock(return_value=MagicMock(
        entity_extraction_task="e", triple_extraction_task="t", type_generation_task="tg", type_assertion_task="ta",
        literal_extraction_task="l", triple_with_literal_extraction_task="spl", fact_checking_task="fc"))
    extractor.entity_extractor = MagicMock(return_value=MagicMock(entities=["Alice", "Bob"]))
    extractor.entity_deduplicator = MagicMock(return_value=MagicMock(filtered_entities=["Alice", "Bob"]))
    extractor.triples_extractor = MagicMock(return_value=MagicMock(triples=[("Alice", "knows", "Bob")]))
    extractor.relation_clusterer = MagicMock(return_value=MagicMock(clusters=[]))
    extractor.type_clusterer = MagicMock(return_value=MagicMock(clusters=[]))
    extractor.coherence_checker = MagicMock(return_value=MagicMock(coherence_scores=[(("Alice", "knows", "Bob"), 5, "ok")]))
    extractor.type_asserter = MagicMock(return_value=MagicMock(pairs=[("Alice", "Person")]))
    extractor.batch_rdfs_comment_generator = MagicMock(return_value=MagicMock(
        entity_comment_pairs=[(NS + "alice", "Alice is a person mentioned in the text.")]))
    if extractor_cls is DomainGraphExtractor:
        extractor.generate_domain_specific_examples = MagicMock(return_value={k: "" for k in EXAMPLE_KEYS})
    return extractor


def _generate(extractor, tmp_path, **kwargs):
    if isinstance(extractor, DomainGraphExtractor):
        kwargs.setdefault("domain", "test")  # skips the domain detector
    return extractor.generate_ontology(text="Alice knows Bob.", ontology_namespace=NS, entity_types=["Person"],
                                       generate_rdfs_annotations=True, save_path=str(tmp_path / "out.owl"), **kwargs)


def _future_warnings(record):
    return [w for w in record if issubclass(w.category, FutureWarning)]


def _assert_content(onto, save_path):
    alice, bob = OWLNamedIndividual(NS + "alice"), OWLNamedIndividual(NS + "bob")
    abox = set(onto.get_abox_axioms())
    assert OWLObjectPropertyAssertionAxiom(alice, OWLObjectProperty(NS + "knows"), bob) in abox
    assert OWLClassAssertionAxiom(alice, OWLClass(NS + "Person")) in abox
    g = rdflib.Graph().parse(save_path)
    assert any(str(v) == "Alice" for v in g.objects(rdflib.URIRef(NS + "alice"), rdflib.RDFS.label))
    assert any("person mentioned" in str(v) for v in g.objects(rdflib.URIRef(NS + "alice"), rdflib.RDFS.comment))


@pytest.mark.parametrize("extractor_cls", EXTRACTORS)
def test_opt_in_fills_the_given_rdflib_ontology_without_warning(tmp_path, extractor_cls):
    given = RDFLibOntology("http://example.com/ontogen", load=False)
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        onto = _generate(_stubbed(extractor_cls), tmp_path, ontology=given)
    assert onto is given
    assert not _future_warnings(record)
    _assert_content(onto, str(tmp_path / "out.owl"))
    # labels/comments are annotations, so they don't turn entities into individuals or data properties
    assert {i.str for i in onto.individuals_in_signature()} == {NS + "alice", NS + "bob"}
    assert not list(onto.data_properties_in_signature())


@pytest.mark.parametrize("extractor_cls", EXTRACTORS)
def test_without_owlready2_falls_back_to_rdflib(tmp_path, extractor_cls):
    with patch.object(graph_extractor, "owlready2_installed", return_value=False), \
            warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        onto = _generate(_stubbed(extractor_cls), tmp_path)
    assert isinstance(onto, RDFLibOntology)
    assert onto.get_ontology_id().get_ontology_iri().str == "http://example.com/ontogen"
    assert not _future_warnings(record)
    _assert_content(onto, str(tmp_path / "out.owl"))


@pytest.mark.requires_owlready2
@pytest.mark.parametrize("extractor_cls", EXTRACTORS)
def test_default_warns_at_the_caller(tmp_path, extractor_cls):
    from owlapy.owl_ontology import Ontology
    with pytest.warns(FutureWarning, match="RDFLibOntology") as record:
        onto = _generate(_stubbed(extractor_cls), tmp_path)
    assert isinstance(onto, Ontology)
    assert _future_warnings(record)[0].filename == __file__
    _assert_content(onto, str(tmp_path / "out.owl"))


@pytest.mark.requires_owlready2
@pytest.mark.parametrize("ontology_type", ["open", "domain"])
def test_default_warning_through_agent_points_at_user_code(tmp_path, ontology_type):
    from owlapy.agen_kg.agent import AGenKG
    with patch("owlapy.agen_kg.agent.dspy.LM"), patch("owlapy.agen_kg.agent.dspy.configure"):
        agent = AGenKG(api_key="fake")
    agent.open_graph_extractor = _stubbed(OpenGraphExtractor)
    agent.domain_graph_extractor = _stubbed(DomainGraphExtractor)
    extra = {"domain": "test"} if ontology_type == "domain" else {}
    with pytest.warns(FutureWarning, match="RDFLibOntology") as record:
        agent.generate_ontology(text="Alice knows Bob.", ontology_type=ontology_type, ontology_namespace=NS,
                                save_path=str(tmp_path / "out.owl"), **extra)
    assert _future_warnings(record)[0].filename == __file__
    assert os.path.isfile(tmp_path / "out.owl")
