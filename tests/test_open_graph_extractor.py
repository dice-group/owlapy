"""Integration-style tests for OpenGraphExtractor.generate_ontology(), the
top-level pipeline that wires together every piece of GraphExtractor already
unit-tested elsewhere (extraction, relation/type clustering, coherence
checking, ontology assembly). Every dspy.Predict-backed attribute involved is
stubbed with a deterministic MagicMock -- no real LLM calls.

Results are verified by parsing the saved RDF/XML file with rdflib rather
than via Ontology.get_abox_axioms()/get_tbox_axioms(), which also happens to
exercise the real onto.save() path end-to-end.
"""
import os
import tempfile
import unittest
from unittest.mock import MagicMock

import rdflib

from owlapy.agen_kg.graph_extracting_models.open_graph_extractor import OpenGraphExtractor

NS = "http://example.com/open_extractor_test#"


def _mock_plan_decomposer():
    return MagicMock(return_value=MagicMock(
        entity_extraction_task="e", triple_extraction_task="t", type_generation_task="tg",
        type_assertion_task="ta", literal_extraction_task="l", triple_with_literal_extraction_task="spl",
        fact_checking_task="fc",
    ))


def _identity_cluster_result():
    """clusters=[] means every item maps to itself (untouched by clustering)."""
    return MagicMock(clusters=[])


def _tmp_save_path():
    return os.path.join(tempfile.mkdtemp(), "out.owl")


class TestOpenGraphExtractorGenerateOntologySimplePath(unittest.TestCase):
    """No chunking (short text), no types, no SPL triples, no hierarchy, no annotations --
    the most direct path through the pipeline."""

    def setUp(self):
        self.extractor = OpenGraphExtractor()
        self.extractor.plan_decomposer = _mock_plan_decomposer()
        self.extractor.entity_extractor = MagicMock(return_value=MagicMock(entities=["Alice", "Bob"]))
        self.extractor.entity_deduplicator = MagicMock(return_value=MagicMock(filtered_entities=["Alice", "Bob"]))
        self.extractor.triples_extractor = MagicMock(
            return_value=MagicMock(triples=[("Alice", "knows", "Bob")])
        )
        self.extractor.relation_clusterer = MagicMock(return_value=_identity_cluster_result())
        self.extractor.coherence_checker = MagicMock(return_value=MagicMock(
            coherence_scores=[(("Alice", "knows", "Bob"), 5, "well supported")]
        ))

    def test_generates_object_property_assertion(self):
        save_path = _tmp_save_path()
        self.extractor.generate_ontology(text="Alice knows Bob.", ontology_namespace=NS, save_path=save_path)

        g = rdflib.Graph().parse(save_path)
        triple = (rdflib.URIRef(NS + "alice"), rdflib.URIRef(NS + "knows"), rdflib.URIRef(NS + "bob"))
        self.assertIn(triple, g)

    def test_skips_triple_when_subject_not_a_canonical_entity(self):
        self.extractor.entity_deduplicator = MagicMock(return_value=MagicMock(filtered_entities=["Bob"]))
        save_path = _tmp_save_path()
        self.extractor.generate_ontology(text="Alice knows Bob.", ontology_namespace=NS, save_path=save_path)

        g = rdflib.Graph().parse(save_path)
        triple = (rdflib.URIRef(NS + "alice"), rdflib.URIRef(NS + "knows"), rdflib.URIRef(NS + "bob"))
        self.assertNotIn(triple, g)

    def test_fact_reassurance_false_skips_coherence_check(self):
        save_path = _tmp_save_path()
        self.extractor.generate_ontology(
            text="Alice knows Bob.", ontology_namespace=NS, save_path=save_path, fact_reassurance=False
        )
        self.extractor.coherence_checker.assert_not_called()

        g = rdflib.Graph().parse(save_path)
        triple = (rdflib.URIRef(NS + "alice"), rdflib.URIRef(NS + "knows"), rdflib.URIRef(NS + "bob"))
        self.assertIn(triple, g)

    def test_low_coherence_triple_is_filtered_out(self):
        self.extractor.coherence_checker = MagicMock(return_value=MagicMock(
            coherence_scores=[(("Alice", "knows", "Bob"), 1, "not supported")]
        ))
        save_path = _tmp_save_path()
        self.extractor.generate_ontology(text="Alice knows Bob.", ontology_namespace=NS, save_path=save_path)

        g = rdflib.Graph().parse(save_path)
        triple = (rdflib.URIRef(NS + "alice"), rdflib.URIRef(NS + "knows"), rdflib.URIRef(NS + "bob"))
        self.assertNotIn(triple, g)

    def test_relation_clustering_remaps_property_name(self):
        self.extractor.relation_clusterer = MagicMock(return_value=MagicMock(
            clusters=[(["knows"], "isAcquaintedWith")]
        ))
        # check_coherence() returns whatever's in coherence_scores verbatim (it doesn't
        # cross-reference against its input triples), so the mock must reflect the
        # relation-clustered triple -- Step 3.5 (relation clustering) runs before Step 4
        # (coherence check) in generate_ontology.
        self.extractor.coherence_checker = MagicMock(return_value=MagicMock(
            coherence_scores=[(("Alice", "isAcquaintedWith", "Bob"), 5, "well supported")]
        ))
        save_path = _tmp_save_path()
        self.extractor.generate_ontology(text="Alice knows Bob.", ontology_namespace=NS, save_path=save_path)

        g = rdflib.Graph().parse(save_path)
        # snake_case() only strips special chars/whitespace and lowercases; it doesn't
        # split camelCase, so "isAcquaintedWith" -> "isacquaintedwith" (no underscores).
        triple = (rdflib.URIRef(NS + "alice"), rdflib.URIRef(NS + "isacquaintedwith"), rdflib.URIRef(NS + "bob"))
        self.assertIn(triple, g)

    def test_logs_when_enabled(self):
        extractor = OpenGraphExtractor(enable_logging=True)
        extractor.plan_decomposer = _mock_plan_decomposer()
        extractor.entity_extractor = MagicMock(return_value=MagicMock(entities=["Alice", "Bob"]))
        extractor.entity_deduplicator = MagicMock(return_value=MagicMock(filtered_entities=["Alice", "Bob"]))
        extractor.triples_extractor = MagicMock(return_value=MagicMock(triples=[("Alice", "knows", "Bob")]))
        extractor.relation_clusterer = MagicMock(return_value=_identity_cluster_result())
        extractor.coherence_checker = MagicMock(return_value=MagicMock(
            coherence_scores=[(("Alice", "knows", "Bob"), 5, "ok")]
        ))
        extractor.generate_ontology(text="Alice knows Bob.", ontology_namespace=NS, save_path=_tmp_save_path())


class TestOpenGraphExtractorGenerateOntologyTypesAndSpl(unittest.TestCase):
    def setUp(self):
        self.extractor = OpenGraphExtractor()
        self.extractor.plan_decomposer = _mock_plan_decomposer()
        self.extractor.entity_extractor = MagicMock(return_value=MagicMock(entities=["Alice"]))
        self.extractor.entity_deduplicator = MagicMock(return_value=MagicMock(filtered_entities=["Alice"]))
        self.extractor.triples_extractor = MagicMock(return_value=MagicMock(triples=[]))
        self.extractor.relation_clusterer = MagicMock(return_value=_identity_cluster_result())
        self.extractor.type_clusterer = MagicMock(return_value=_identity_cluster_result())

    def test_entity_types_uses_type_asserter_and_adds_class_assertion(self):
        self.extractor.type_asserter = MagicMock(return_value=MagicMock(pairs=[("Alice", "Person")]))
        save_path = _tmp_save_path()
        self.extractor.generate_ontology(
            text="Alice is a person.", ontology_namespace=NS, entity_types=["Person"], save_path=save_path
        )
        self.extractor.type_asserter.assert_called_once()

        g = rdflib.Graph().parse(save_path)
        self.assertIn((rdflib.URIRef(NS + "alice"), rdflib.RDF.type, rdflib.URIRef(NS + "Person")), g)

    def test_generate_types_uses_type_generator(self):
        self.extractor.type_generator = MagicMock(return_value=MagicMock(pairs=[("Alice", "Person")]))
        save_path = _tmp_save_path()
        self.extractor.generate_ontology(
            text="Alice is a person.", ontology_namespace=NS, generate_types=True, save_path=save_path
        )
        self.extractor.type_generator.assert_called_once()

        g = rdflib.Graph().parse(save_path)
        self.assertIn((rdflib.URIRef(NS + "alice"), rdflib.RDF.type, rdflib.URIRef(NS + "Person")), g)

    def test_extract_spl_triples_adds_data_property_assertion(self):
        self.extractor.literal_extractor = MagicMock(return_value=MagicMock(l_values=["30"]))
        self.extractor.spl_triples_extractor = MagicMock(
            return_value=MagicMock(triples=[("Alice", "hasAge", "30")])
        )
        save_path = _tmp_save_path()
        self.extractor.generate_ontology(
            text="Alice is 30 years old.", ontology_namespace=NS, extract_spl_triples=True, save_path=save_path
        )

        g = rdflib.Graph().parse(save_path)
        # snake_case("hasAge") -> "hasage" (no camelCase splitting).
        values = list(g.objects(rdflib.URIRef(NS + "alice"), rdflib.URIRef(NS + "hasage")))
        self.assertEqual([int(v) for v in values], [30])

    def test_spl_triple_skipped_when_literal_not_in_extracted_literals(self):
        self.extractor.literal_extractor = MagicMock(return_value=MagicMock(l_values=["30"]))
        self.extractor.spl_triples_extractor = MagicMock(
            return_value=MagicMock(triples=[("Alice", "hasAge", "999")])  # not in l_values
        )
        save_path = _tmp_save_path()
        self.extractor.generate_ontology(
            text="Alice is 30 years old.", ontology_namespace=NS, extract_spl_triples=True, save_path=save_path
        )

        g = rdflib.Graph().parse(save_path)
        values = list(g.objects(rdflib.URIRef(NS + "alice"), rdflib.URIRef(NS + "has_age")))
        self.assertEqual(values, [])


class TestOpenGraphExtractorGenerateOntologyChunkedPath(unittest.TestCase):
    def test_uses_chunk_extraction_when_forced(self):
        extractor = OpenGraphExtractor()
        extractor.plan_decomposer = _mock_plan_decomposer()
        extractor.text_summarizer = MagicMock(return_value=MagicMock(summary="a summary"))
        extractor.entity_extractor = MagicMock(return_value=MagicMock(entities=["Alice"]))
        extractor.entity_deduplicator = MagicMock(return_value=MagicMock(filtered_entities=["Alice"]))
        extractor.entity_deduplicator_with_summary = MagicMock(return_value=MagicMock(filtered_entities=["Alice"]))
        extractor.triples_extractor = MagicMock(return_value=MagicMock(triples=[]))
        extractor.relation_clusterer = MagicMock(return_value=_identity_cluster_result())
        extractor.relation_clusterer_with_summary = MagicMock(return_value=_identity_cluster_result())
        extractor.configure_chunking(chunk_size=20, overlap=0, strategy="fixed")

        save_path = _tmp_save_path()
        extractor.generate_ontology(
            text="a" * 100, ontology_namespace=NS, use_chunking=True, save_path=save_path
        )
        self.assertTrue(extractor.entity_extractor.called)
        self.assertGreater(extractor.entity_extractor.call_count, 1)
        self.assertTrue(os.path.exists(save_path))


class TestOpenGraphExtractorGenerateOntologyRdfsAnnotations(unittest.TestCase):
    def test_generates_label_and_comment_axioms(self):
        extractor = OpenGraphExtractor()
        extractor.plan_decomposer = _mock_plan_decomposer()
        extractor.entity_extractor = MagicMock(return_value=MagicMock(entities=["Alice", "Bob"]))
        extractor.entity_deduplicator = MagicMock(return_value=MagicMock(filtered_entities=["Alice", "Bob"]))
        extractor.triples_extractor = MagicMock(return_value=MagicMock(triples=[("Alice", "knows", "Bob")]))
        extractor.relation_clusterer = MagicMock(return_value=_identity_cluster_result())
        extractor.coherence_checker = MagicMock(return_value=MagicMock(
            coherence_scores=[(("Alice", "knows", "Bob"), 5, "ok")]
        ))
        extractor.batch_rdfs_comment_generator = MagicMock(return_value=MagicMock(
            entity_comment_pairs=[(NS + "alice", "Alice is a person mentioned in the text.")]
        ))

        save_path = _tmp_save_path()
        extractor.generate_ontology(
            text="Alice knows Bob.", ontology_namespace=NS, save_path=save_path, generate_rdfs_annotations=True
        )
        extractor.batch_rdfs_comment_generator.assert_called()

        g = rdflib.Graph().parse(save_path)
        # rdfs:label for the individual (from format_rdfs_label -> "Alice").
        labels = list(g.objects(rdflib.URIRef(NS + "alice"), rdflib.RDFS.label))
        self.assertTrue(any(str(v) == "Alice" for v in labels))
        # rdfs:comment generated via batch_rdfs_comment_generator.
        comments = list(g.objects(rdflib.URIRef(NS + "alice"), rdflib.RDFS.comment))
        self.assertTrue(any("person mentioned in the text" in str(v) for v in comments))


if __name__ == '__main__':
    unittest.main()
