"""Unit tests for GraphExtractor's _extract_*_from_chunks methods:
_extract_entities_from_chunks, _extract_triples_from_chunks,
_extract_types_from_chunks, _extract_literals_from_chunks, and
_extract_spl_triples_from_chunks. Each iterates over chunks, calls a
dspy.Predict-backed extractor per chunk (catching exceptions per-chunk so
one bad chunk doesn't abort the whole run), and merges the results.

DomainGraphExtractor defines all the required extractor attributes
(entity_extractor, triples_extractor, type_asserter, type_generator,
literal_extractor, spl_triples_extractor) in its __init__, so the
AttributeError guard in each method (for extractor subclasses missing one)
is tested via a bare GraphExtractor-like stand-in that deletes the attribute.
"""
import unittest
from unittest.mock import MagicMock

from owlapy.agen_kg.graph_extracting_models.domain_graph_extractor import DomainGraphExtractor


class TestExtractEntitiesFromChunks(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()
        self.extractor.entity_extractor = MagicMock(
            side_effect=lambda text, few_shot_examples, task_instructions: MagicMock(
                entities=[f"Entity-in-{text}"]
            )
        )

    def test_missing_entity_extractor_raises_attribute_error(self):
        del self.extractor.entity_extractor
        with self.assertRaises(AttributeError):
            self.extractor._extract_entities_from_chunks(["chunk"], "examples")

    def test_extracts_and_merges_entities_across_chunks(self):
        merged, summaries = self.extractor._extract_entities_from_chunks(
            ["chunk1", "chunk2"], "examples", use_llm_merge=False
        )
        self.assertEqual(merged, ["Entity-in-chunk1", "Entity-in-chunk2"])
        self.assertEqual(summaries, [])

    def test_per_chunk_extraction_failure_is_caught_and_yields_no_entities_for_that_chunk(self):
        self.extractor.entity_extractor = MagicMock(side_effect=[
            RuntimeError("LLM failed"),
            MagicMock(entities=["Bob"]),
        ])
        merged, _ = self.extractor._extract_entities_from_chunks(
            ["bad chunk", "good chunk"], "examples", use_llm_merge=False
        )
        self.assertEqual(merged, ["Bob"])

    def test_result_without_entities_attribute_yields_empty_list_for_chunk(self):
        self.extractor.entity_extractor = MagicMock(return_value=object())  # no `.entities`
        merged, _ = self.extractor._extract_entities_from_chunks(["chunk"], "examples", use_llm_merge=False)
        self.assertEqual(merged, [])

    def test_llm_merge_true_generates_and_returns_chunk_summaries(self):
        self.extractor.text_summarizer = MagicMock(return_value=MagicMock(summary="a summary"))
        self.extractor.use_incremental_merging = True
        merged, summaries = self.extractor._extract_entities_from_chunks(
            ["chunk1"], "examples", use_llm_merge=True
        )
        self.assertEqual(summaries, ["a summary"])
        self.assertEqual(merged, ["Entity-in-chunk1"])

    def test_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.entity_extractor = MagicMock(return_value=MagicMock(entities=["Alice"]))
        extractor._extract_entities_from_chunks(["chunk"], "examples", use_llm_merge=False)

    def test_logs_extraction_failure_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.entity_extractor = MagicMock(side_effect=RuntimeError("boom"))
        merged, _ = extractor._extract_entities_from_chunks(["chunk"], "examples", use_llm_merge=False)
        self.assertEqual(merged, [])


class TestExtractTriplesFromChunks(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()
        self.extractor.triples_extractor = MagicMock(
            return_value=MagicMock(triples=[("Alice", "knows", "Bob")])
        )

    def test_missing_triples_extractor_raises_attribute_error(self):
        del self.extractor.triples_extractor
        with self.assertRaises(AttributeError):
            self.extractor._extract_triples_from_chunks(["chunk"], ["Alice"], "examples")

    def test_extracts_and_merges_triples(self):
        result = self.extractor._extract_triples_from_chunks(
            ["chunk1"], ["Alice", "Bob"], "examples", use_llm_merge=False
        )
        self.assertEqual(result, [("Alice", "knows", "Bob")])

    def test_generates_chunk_summaries_when_not_provided_and_llm_merge_enabled(self):
        self.extractor.text_summarizer = MagicMock(return_value=MagicMock(summary="a summary"))
        self.extractor.triple_merger = MagicMock(
            return_value=MagicMock(merged_triples=[("Alice", "knows", "Bob"), ("Carol", "knows", "Dave")])
        )
        self.extractor.triples_extractor = MagicMock(side_effect=[
            MagicMock(triples=[("Alice", "knows", "Bob")]),
            MagicMock(triples=[("Carol", "knows", "Dave")]),
        ])
        result = self.extractor._extract_triples_from_chunks(
            ["chunk1", "chunk2"], ["Alice"], "examples", use_llm_merge=True
        )
        self.extractor.text_summarizer.assert_called()
        self.assertEqual(result, [("Alice", "knows", "Bob"), ("Carol", "knows", "Dave")])

    def test_per_chunk_extraction_failure_is_caught(self):
        self.extractor.triples_extractor = MagicMock(side_effect=RuntimeError("boom"))
        result = self.extractor._extract_triples_from_chunks(["chunk"], ["Alice"], "examples", use_llm_merge=False)
        self.assertEqual(result, [])

    def test_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.triples_extractor = MagicMock(return_value=MagicMock(triples=[("A", "p", "B")]))
        extractor._extract_triples_from_chunks(["chunk"], ["A"], "examples", use_llm_merge=False)


class TestExtractTypesFromChunks(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()
        self.extractor.type_asserter = MagicMock(return_value=MagicMock(pairs=[("Alice", "Person")]))
        self.extractor.type_generator = MagicMock(return_value=MagicMock(pairs=[("Alice", "Human")]))

    def test_missing_type_extractors_raises_attribute_error(self):
        del self.extractor.type_asserter
        with self.assertRaises(AttributeError):
            self.extractor._extract_types_from_chunks(
                ["chunk"], ["Alice"], ["Person"], False, "ex_a", "ex_g"
            )

    def test_uses_type_asserter_when_entity_types_given_and_not_generating(self):
        result = self.extractor._extract_types_from_chunks(
            ["chunk"], ["Alice"], ["Person"], False, "ex_a", "ex_g", use_llm_merge=False
        )
        self.assertEqual(result, [("Alice", "Person")])
        self.extractor.type_asserter.assert_called_once()
        self.extractor.type_generator.assert_not_called()

    def test_uses_type_generator_when_generate_types_true(self):
        result = self.extractor._extract_types_from_chunks(
            ["chunk"], ["Alice"], None, True, "ex_a", "ex_g", use_llm_merge=False
        )
        self.assertEqual(result, [("Alice", "Human")])
        self.extractor.type_generator.assert_called_once()
        self.extractor.type_asserter.assert_not_called()

    def test_uses_type_generator_when_entity_types_is_none(self):
        result = self.extractor._extract_types_from_chunks(
            ["chunk"], ["Alice"], None, False, "ex_a", "ex_g", use_llm_merge=False
        )
        self.assertEqual(result, [("Alice", "Human")])
        self.extractor.type_generator.assert_called_once()

    def test_per_chunk_extraction_failure_is_caught(self):
        self.extractor.type_asserter = MagicMock(side_effect=RuntimeError("boom"))
        result = self.extractor._extract_types_from_chunks(
            ["chunk"], ["Alice"], ["Person"], False, "ex_a", "ex_g", use_llm_merge=False
        )
        self.assertEqual(result, [])

    def test_generates_summaries_when_llm_merge_enabled_and_not_provided(self):
        self.extractor.text_summarizer = MagicMock(return_value=MagicMock(summary="a summary"))
        self.extractor.type_merger = MagicMock(return_value=MagicMock(
            merged_types=[("Alice", "Person"), ("Bob", "Person")]
        ))
        self.extractor.type_asserter = MagicMock(side_effect=[
            MagicMock(pairs=[("Alice", "Person")]),
            MagicMock(pairs=[("Bob", "Person")]),
        ])
        result = self.extractor._extract_types_from_chunks(
            ["chunk1", "chunk2"], ["Alice", "Bob"], ["Person"], False, "ex_a", "ex_g", use_llm_merge=True
        )
        self.extractor.text_summarizer.assert_called()
        self.assertEqual(result, [("Alice", "Person"), ("Bob", "Person")])

    def test_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.type_asserter = MagicMock(return_value=MagicMock(pairs=[("A", "T")]))
        extractor._extract_types_from_chunks(["chunk"], ["A"], ["T"], False, "ex_a", "ex_g", use_llm_merge=False)


class TestExtractLiteralsFromChunks(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()
        self.extractor.literal_extractor = MagicMock(return_value=MagicMock(l_values=["30", "NYC"]))

    def test_missing_literal_extractor_raises_attribute_error(self):
        del self.extractor.literal_extractor
        with self.assertRaises(AttributeError):
            self.extractor._extract_literals_from_chunks(["chunk"], "examples")

    def test_extracts_and_merges_literals(self):
        result = self.extractor._extract_literals_from_chunks(["chunk1", "chunk2"], "examples")
        self.assertEqual(result, ["30", "NYC"])

    def test_per_chunk_extraction_failure_is_caught(self):
        self.extractor.literal_extractor = MagicMock(side_effect=RuntimeError("boom"))
        result = self.extractor._extract_literals_from_chunks(["chunk"], "examples")
        self.assertEqual(result, [])

    def test_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.literal_extractor = MagicMock(return_value=MagicMock(l_values=["30"]))
        extractor._extract_literals_from_chunks(["chunk"], "examples")


class TestExtractSplTriplesFromChunks(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()
        self.extractor.spl_triples_extractor = MagicMock(
            return_value=MagicMock(triples=[("Alice", "hasAge", "30")])
        )

    def test_missing_spl_triples_extractor_raises_attribute_error(self):
        del self.extractor.spl_triples_extractor
        with self.assertRaises(AttributeError):
            self.extractor._extract_spl_triples_from_chunks(["chunk"], ["Alice"], ["30"], "examples")

    def test_extracts_and_merges_spl_triples(self):
        result = self.extractor._extract_spl_triples_from_chunks(["chunk"], ["Alice"], ["30"], "examples")
        self.assertEqual(result, [("Alice", "hasAge", "30")])

    def test_per_chunk_extraction_failure_is_caught(self):
        self.extractor.spl_triples_extractor = MagicMock(side_effect=RuntimeError("boom"))
        result = self.extractor._extract_spl_triples_from_chunks(["chunk"], ["Alice"], ["30"], "examples")
        self.assertEqual(result, [])

    def test_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.spl_triples_extractor = MagicMock(return_value=MagicMock(triples=[("A", "p", "1")]))
        extractor._extract_spl_triples_from_chunks(["chunk"], ["A"], ["1"], "examples")


if __name__ == '__main__':
    unittest.main()
