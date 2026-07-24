"""Unit tests for GraphExtractor's single-LLM-call clustering/filtering methods:
filter_entities, cluster_types, cluster_relations, and check_coherence. All four
share the same use_summary auto-detection + direct-vs-summary context branch, so
they're tested together. The relevant dspy.Predict attributes are stubbed --
no real API calls.
"""
import unittest
from unittest.mock import MagicMock

from owlapy.agen_kg.graph_extracting_models.domain_graph_extractor import DomainGraphExtractor


class TestFilterEntities(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()
        self.extractor.text_summarizer = MagicMock(return_value=MagicMock(summary="a summary"))
        self.extractor.entity_deduplicator = MagicMock(
            return_value=MagicMock(filtered_entities=["Alice", "Bob"])
        )
        self.extractor.entity_deduplicator_with_summary = MagicMock(
            return_value=MagicMock(filtered_entities=["Alice"])
        )

    def test_empty_entities_returns_empty(self):
        self.assertEqual(self.extractor.filter_entities([], "some text"), [])

    def test_short_text_uses_direct_deduplicator(self):
        result = self.extractor.filter_entities(["Alice", "Bob", "Alice"], "short text")
        self.assertEqual(result, ["Alice", "Bob"])
        self.extractor.entity_deduplicator.assert_called_once()
        self.extractor.entity_deduplicator_with_summary.assert_not_called()

    def test_long_text_uses_summary_deduplicator(self):
        self.extractor.configure_chunking(summarization_threshold=5)
        result = self.extractor.filter_entities(["Alice", "Bob"], "text longer than five chars")
        self.assertEqual(result, ["Alice"])
        self.extractor.entity_deduplicator_with_summary.assert_called_once()

    def test_use_summary_explicit_true_forces_summary_path(self):
        result = self.extractor.filter_entities(["Alice"], "short", use_summary=True)
        self.assertEqual(result, ["Alice"])
        self.extractor.entity_deduplicator_with_summary.assert_called_once()

    def test_use_summary_explicit_false_forces_direct_path_even_for_long_text(self):
        self.extractor.configure_chunking(summarization_threshold=5, max_summary_length=10)
        result = self.extractor.filter_entities(["Alice", "Bob"], "a text longer than five chars", use_summary=False)
        self.assertEqual(result, ["Alice", "Bob"])
        self.extractor.entity_deduplicator.assert_called_once()

    def test_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.entity_deduplicator = MagicMock(return_value=MagicMock(filtered_entities=["Alice"]))
        extractor.filter_entities(["Alice", "Bob"], "short text")  # should not raise


class TestClusterTypes(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()
        self.extractor.text_summarizer = MagicMock(return_value=MagicMock(summary="a summary"))
        self.extractor.type_clusterer = MagicMock(
            return_value=MagicMock(clusters=[(["Person", "Human"], "Person")])
        )
        self.extractor.type_clusterer_with_summary = MagicMock(
            return_value=MagicMock(clusters=[(["Person", "Human"], "Person")])
        )

    def test_empty_types_returns_empty_dict(self):
        self.assertEqual(self.extractor.cluster_types([], "some text"), {})

    def test_short_text_uses_direct_clusterer(self):
        mapping = self.extractor.cluster_types(["Person", "Human", "Place"], "short text")
        self.assertEqual(mapping["Person"], "Person")
        self.assertEqual(mapping["Human"], "Person")
        # "Place" wasn't in any cluster, so it maps to itself.
        self.assertEqual(mapping["Place"], "Place")
        self.extractor.type_clusterer.assert_called_once()

    def test_long_text_uses_summary_clusterer(self):
        self.extractor.configure_chunking(summarization_threshold=5)
        mapping = self.extractor.cluster_types(["Person"], "text longer than five chars")
        self.assertEqual(mapping["Person"], "Person")
        self.extractor.type_clusterer_with_summary.assert_called_once()

    def test_logs_merge_count_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.type_clusterer = MagicMock(return_value=MagicMock(clusters=[(["Person", "Human"], "Person")]))
        extractor.cluster_types(["Person", "Human"], "short text")  # should not raise


class TestClusterRelations(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()
        self.extractor.text_summarizer = MagicMock(return_value=MagicMock(summary="a summary"))
        self.extractor.relation_clusterer = MagicMock(
            return_value=MagicMock(clusters=[(["knows", "isFriendsWith"], "knows")])
        )
        self.extractor.relation_clusterer_with_summary = MagicMock(
            return_value=MagicMock(clusters=[(["knows", "isFriendsWith"], "knows")])
        )

    def test_empty_relations_returns_empty_dict(self):
        self.assertEqual(self.extractor.cluster_relations([], "some text"), {})

    def test_short_text_uses_direct_clusterer(self):
        mapping = self.extractor.cluster_relations(["knows", "isFriendsWith", "worksAt"], "short text")
        self.assertEqual(mapping["knows"], "knows")
        self.assertEqual(mapping["isFriendsWith"], "knows")
        self.assertEqual(mapping["worksAt"], "worksAt")
        self.extractor.relation_clusterer.assert_called_once()

    def test_long_text_uses_summary_clusterer(self):
        self.extractor.configure_chunking(summarization_threshold=5)
        mapping = self.extractor.cluster_relations(["knows"], "text longer than five chars")
        self.assertEqual(mapping["knows"], "knows")
        self.extractor.relation_clusterer_with_summary.assert_called_once()

    def test_logs_merge_count_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.relation_clusterer = MagicMock(return_value=MagicMock(clusters=[(["knows", "isFriendsWith"], "knows")]))
        extractor.cluster_relations(["knows", "isFriendsWith"], "short text")  # should not raise


class TestCheckCoherence(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()
        self.triples = [("Alice", "knows", "Bob"), ("Bob", "livesIn", "Nowhere")]

    def test_empty_triples_returns_empty(self):
        self.assertEqual(self.extractor.check_coherence([], "some text"), [])

    def test_filters_by_threshold(self):
        self.extractor.coherence_checker = MagicMock(return_value=MagicMock(coherence_scores=[
            (("Alice", "knows", "Bob"), 5, "well supported"),
            (("Bob", "livesIn", "Nowhere"), 1, "not supported by text"),
        ]))
        result = self.extractor.check_coherence(self.triples, "short text", threshold=3)
        self.assertEqual(result, [("Alice", "knows", "Bob")])

    def test_uses_summary_context_for_long_text(self):
        self.extractor.configure_chunking(summarization_threshold=5)
        self.extractor.text_summarizer = MagicMock(return_value=MagicMock(summary="a summary"))
        self.extractor.coherence_checker = MagicMock(return_value=MagicMock(coherence_scores=[
            (("Alice", "knows", "Bob"), 5, "ok"),
        ]))
        result = self.extractor.check_coherence(
            [("Alice", "knows", "Bob")], "text that is longer than five characters"
        )
        self.assertEqual(result, [("Alice", "knows", "Bob")])
        _, call_kwargs = self.extractor.coherence_checker.call_args
        self.assertEqual(call_kwargs["text"], "a summary")

    def test_batches_triples_according_to_batch_size(self):
        self.extractor.coherence_checker = MagicMock(return_value=MagicMock(coherence_scores=[
            (t, 5, "ok") for t in self.triples
        ]))
        # batch_size=1 forces two separate calls for two triples.
        self.extractor.check_coherence(self.triples, "short text", batch_size=1, threshold=3)
        self.assertEqual(self.extractor.coherence_checker.call_count, 2)

    def test_passes_task_instructions_through(self):
        self.extractor.coherence_checker = MagicMock(return_value=MagicMock(coherence_scores=[]))
        self.extractor.check_coherence(self.triples, "short text", task_instructions="be strict")
        _, call_kwargs = self.extractor.coherence_checker.call_args
        self.assertEqual(call_kwargs["task_instructions"], "be strict")

    def test_logs_filtered_triples_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.coherence_checker = MagicMock(return_value=MagicMock(coherence_scores=[
            (("Alice", "knows", "Bob"), 1, "weak"),
        ]))
        result = extractor.check_coherence(self.triples[:1], "short text", threshold=3)
        self.assertEqual(result, [])


if __name__ == '__main__':
    unittest.main()
