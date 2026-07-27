"""Unit tests for the entity/triple/type-assertion/literal merging logic in
owlapy.agen_kg.graph_extractor.GraphExtractor. These four merge families
(_merge_entity_lists, _merge_triple_lists, _merge_type_assertions,
_merge_literal_lists) share near-identical structure: an empty/single-chunk
fast path, a simple-deduplication path (default, or when LLM merge is
disabled/summaries are missing), and an incremental LLM-based merge path with
a fallback to simple merging on empty/invalid LLM output or an exception.

The LLM-backed dspy.Predict attributes (entity_merger, triple_merger,
type_merger) are replaced with MagicMock stubs -- no real API calls.
"""
import unittest
from unittest.mock import MagicMock

from owlapy.agen_kg.graph_extracting_models.domain_graph_extractor import DomainGraphExtractor


class TestMergeEntityLists(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()
        self.extractor.entity_merger = MagicMock()

    def test_empty_list_returns_empty(self):
        self.assertEqual(self.extractor._merge_entity_lists([]), [])

    def test_single_chunk_returned_unchanged(self):
        self.assertEqual(self.extractor._merge_entity_lists([["Alice", "Bob"]]), ["Alice", "Bob"])

    def test_simple_merge_deduplicates_case_insensitively(self):
        result = self.extractor._merge_entity_lists([["Alice", "Bob"], ["alice", "Carol"]])
        self.assertEqual(result, ["Alice", "Bob", "Carol"])
        self.extractor.entity_merger.assert_not_called()

    def test_llm_merge_disabled_by_default_class_setting(self):
        self.extractor.use_incremental_merging = False
        result = self.extractor._merge_entity_lists(
            [["Alice"], ["Bob"]], chunk_summaries=["s1", "s2"]
        )
        self.assertEqual(result, ["Alice", "Bob"])
        self.extractor.entity_merger.assert_not_called()

    def test_mismatched_summaries_length_falls_back_to_simple_merge(self):
        result = self.extractor._merge_entity_lists(
            [["Alice"], ["Bob"]], chunk_summaries=["only one summary"], use_llm_merge=True
        )
        self.assertEqual(result, ["Alice", "Bob"])
        self.extractor.entity_merger.assert_not_called()

    def test_incremental_merge_happy_path_uses_llm_result(self):
        self.extractor.entity_merger.return_value = MagicMock(
            merged_entities=["Alice", "Bob"], entity_mapping=[("Bob ", "Bob")]
        )
        result = self.extractor._merge_entity_lists(
            [["Alice"], ["Bob "]], chunk_summaries=["s1", "s2"], use_llm_merge=True
        )
        self.assertEqual(result, ["Alice", "Bob"])
        self.extractor.entity_merger.assert_called_once()

    def test_incremental_merge_skips_llm_when_current_merged_list_empty(self):
        result = self.extractor._merge_entity_lists(
            [[], ["Bob"]], chunk_summaries=["s1", "s2"], use_llm_merge=True
        )
        self.assertEqual(result, ["Bob"])
        self.extractor.entity_merger.assert_not_called()

    def test_incremental_merge_skips_empty_chunk(self):
        self.extractor.entity_merger.return_value = MagicMock(merged_entities=["Alice"], entity_mapping=[])
        result = self.extractor._merge_entity_lists(
            [["Alice"], []], chunk_summaries=["s1", "s2"], use_llm_merge=True
        )
        self.assertEqual(result, ["Alice"])
        self.extractor.entity_merger.assert_not_called()

    def test_incremental_merge_falls_back_on_empty_llm_result(self):
        self.extractor.entity_merger.return_value = MagicMock(merged_entities=[])
        result = self.extractor._merge_entity_lists(
            [["Alice"], ["Bob"]], chunk_summaries=["s1", "s2"], use_llm_merge=True
        )
        self.assertEqual(result, ["Alice", "Bob"])

    def test_incremental_merge_falls_back_on_llm_exception(self):
        self.extractor.entity_merger.side_effect = RuntimeError("LLM call failed")
        result = self.extractor._merge_entity_lists(
            [["Alice"], ["Bob"]], chunk_summaries=["s1", "s2"], use_llm_merge=True
        )
        self.assertEqual(result, ["Alice", "Bob"])

    def test_incremental_merge_truncates_long_context(self):
        self.extractor.entity_merger.return_value = MagicMock(merged_entities=["Alice", "Bob"], entity_mapping=[])
        long_summary = "x" * 2000
        self.extractor._merge_entity_lists(
            [["Alice"], ["Bob"]], chunk_summaries=[long_summary, long_summary], use_llm_merge=True
        )
        _, call_kwargs = self.extractor.entity_merger.call_args
        self.assertEqual(len(call_kwargs["context_a"]), 1500)
        self.assertEqual(len(call_kwargs["context_b"]), 1500)

    def test_incremental_merge_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.entity_merger = MagicMock(return_value=MagicMock(merged_entities=["Alice", "Bob"], entity_mapping=[("a", "b")]))
        extractor._merge_entity_lists([["Alice"], ["Bob"]], chunk_summaries=["s1", "s2"], use_llm_merge=True)

    def test_incremental_merge_logs_on_fallback_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.entity_merger = MagicMock(side_effect=RuntimeError("boom"))
        result = extractor._merge_entity_lists([["Alice"], ["Bob"]], chunk_summaries=["s1", "s2"], use_llm_merge=True)
        self.assertEqual(result, ["Alice", "Bob"])


class TestMergeTripleLists(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()
        self.extractor.triple_merger = MagicMock()

    def test_empty_list_returns_empty(self):
        self.assertEqual(self.extractor._merge_triple_lists([]), [])

    def test_single_chunk_returned_unchanged(self):
        triples = [("Alice", "knows", "Bob")]
        self.assertEqual(self.extractor._merge_triple_lists([triples]), triples)

    def test_simple_merge_deduplicates_case_insensitively(self):
        result = self.extractor._merge_triple_lists([
            [("Alice", "knows", "Bob")],
            [("alice", "KNOWS", "bob"), ("Carol", "knows", "Dave")],
        ])
        self.assertEqual(result, [("Alice", "knows", "Bob"), ("Carol", "knows", "Dave")])
        self.extractor.triple_merger.assert_not_called()

    def test_incremental_merge_with_two_chunks_uses_llm_result(self):
        merged = [("Alice", "knows", "Bob"), ("Carol", "knows", "Dave")]
        self.extractor.triple_merger.return_value = MagicMock(merged_triples=merged)
        result = self.extractor._merge_triple_lists(
            [[("Alice", "knows", "Bob")], [("Carol", "knows", "Dave")]],
            chunk_summaries=["s1", "s2"], use_llm_merge=True,
        )
        self.assertEqual(result, merged)
        self.extractor.triple_merger.assert_called_once()

    def test_incremental_merge_falls_back_on_empty_llm_result(self):
        self.extractor.triple_merger.return_value = MagicMock(merged_triples=[])
        result = self.extractor._merge_triple_lists(
            [[("Alice", "knows", "Bob")], [("Carol", "knows", "Dave")]],
            chunk_summaries=["s1", "s2"], use_llm_merge=True,
        )
        self.assertEqual(result, [("Alice", "knows", "Bob"), ("Carol", "knows", "Dave")])

    def test_incremental_merge_falls_back_on_llm_exception(self):
        self.extractor.triple_merger.side_effect = RuntimeError("boom")
        result = self.extractor._merge_triple_lists(
            [[("Alice", "knows", "Bob")], [("Carol", "knows", "Dave")]],
            chunk_summaries=["s1", "s2"], use_llm_merge=True,
        )
        self.assertEqual(result, [("Alice", "knows", "Bob"), ("Carol", "knows", "Dave")])


class TestMergeTypeAssertions(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()
        self.extractor.type_merger = MagicMock()

    def test_empty_list_returns_empty(self):
        self.assertEqual(self.extractor._merge_type_assertions([]), [])

    def test_single_chunk_returned_unchanged(self):
        assertions = [("Alice", "Person")]
        self.assertEqual(self.extractor._merge_type_assertions([assertions]), assertions)

    def test_simple_merge_keeps_first_seen_type(self):
        result = self.extractor._merge_type_assertions([
            [("Alice", "Person")],
            [("alice", "Employee"), ("Bob", "Person")],
        ])
        self.assertEqual(result, [("Alice", "Person"), ("Bob", "Person")])
        self.extractor.type_merger.assert_not_called()

    def test_incremental_merge_with_two_chunks_uses_llm_result(self):
        merged = [("Alice", "Person"), ("Bob", "Person")]
        self.extractor.type_merger.return_value = MagicMock(merged_types=merged)
        result = self.extractor._merge_type_assertions(
            [[("Alice", "Person")], [("Bob", "Person")]],
            chunk_summaries=["s1", "s2"], use_llm_merge=True,
        )
        self.assertEqual(result, merged)
        self.extractor.type_merger.assert_called_once()

    def test_incremental_merge_falls_back_on_empty_llm_result(self):
        self.extractor.type_merger.return_value = MagicMock(merged_types=[])
        result = self.extractor._merge_type_assertions(
            [[("Alice", "Person")], [("Bob", "Person")]],
            chunk_summaries=["s1", "s2"], use_llm_merge=True,
        )
        self.assertEqual(result, [("Alice", "Person"), ("Bob", "Person")])

    def test_incremental_merge_falls_back_on_llm_exception(self):
        self.extractor.type_merger.side_effect = RuntimeError("boom")
        result = self.extractor._merge_type_assertions(
            [[("Alice", "Person")], [("Bob", "Person")]],
            chunk_summaries=["s1", "s2"], use_llm_merge=True,
        )
        self.assertEqual(result, [("Alice", "Person"), ("Bob", "Person")])


class TestMergeLiteralLists(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()

    def test_merges_and_deduplicates_preserving_order(self):
        result = self.extractor._merge_literal_lists([["30", "NYC"], ["NYC", "London"]])
        self.assertEqual(result, ["30", "NYC", "London"])

    def test_empty_lists_return_empty(self):
        self.assertEqual(self.extractor._merge_literal_lists([]), [])
        self.assertEqual(self.extractor._merge_literal_lists([[]]), [])


if __name__ == '__main__':
    unittest.main()
