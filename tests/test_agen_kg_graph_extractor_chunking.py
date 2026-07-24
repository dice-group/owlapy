"""Unit tests for the non-LLM chunking/summarization/caching infrastructure of
owlapy.agen_kg.graph_extractor.GraphExtractor (text loading, chunk configuration,
summary caching, and the pure get_corresponding_literal type-detection logic).

GraphExtractor is abstract (generate_ontology), so DomainGraphExtractor is used as
a concrete instance -- constructing it doesn't make any network/LLM calls (dspy.Predict
wraps a signature lazily). Where a method DOES call an LLM (summarize_chunk,
create_combined_summary), the specific dspy.Predict instance attribute is replaced
with a lightweight stub so no real API call happens.
"""
import unittest
import unittest.mock
from datetime import date, datetime
from unittest.mock import MagicMock

from owlapy.agen_kg.chunking_models.simple_chunker import TextChunker
from owlapy.agen_kg.graph_extracting_models.domain_graph_extractor import DomainGraphExtractor
from owlapy.owl_literal import OWLLiteral


class TestLoadTextAndFormats(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()

    def test_load_text_raw_string(self):
        self.assertEqual(self.extractor.load_text("just some raw text"), "just some raw text")

    def test_load_text_nonexistent_path_is_treated_as_raw_text(self):
        # UniversalTextLoader checks Path.is_file() first; a nonexistent path
        # isn't a file, so it falls back to RawTextLoader and returns the
        # string itself rather than raising FileNotFoundError.
        path_str = "/nonexistent/file.txt"
        self.assertEqual(self.extractor.load_text(path_str), path_str)

    def test_load_text_reraises_and_logs_on_unsupported_existing_file(self):
        import os
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            path = f.name
        try:
            extractor = DomainGraphExtractor(enable_logging=True)
            with self.assertRaises(ValueError):
                extractor.load_text(path)
        finally:
            os.remove(path)

    def test_get_supported_formats(self):
        formats = self.extractor.get_supported_formats()
        self.assertIn(".txt", formats)
        self.assertIn(".pdf", formats)


class TestConfigureChunking(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()

    def test_configure_chunking_updates_text_chunker(self):
        self.extractor.configure_chunking(chunk_size=1000, overlap=50, strategy="sentence")
        self.assertEqual(self.extractor.text_chunker.chunk_size, 1000)
        self.assertEqual(self.extractor.text_chunker.overlap, 50)
        self.assertEqual(self.extractor.text_chunker.strategy, "sentence")

    def test_configure_chunking_partial_update_keeps_other_defaults(self):
        original_strategy = self.extractor.text_chunker.strategy
        self.extractor.configure_chunking(chunk_size=1500)
        self.assertEqual(self.extractor.text_chunker.chunk_size, 1500)
        self.assertEqual(self.extractor.text_chunker.strategy, original_strategy)

    def test_configure_chunking_updates_thresholds(self):
        self.extractor.configure_chunking(
            auto_chunk_threshold=5000, summarization_threshold=9000, max_summary_length=4000
        )
        self.assertEqual(self.extractor.auto_chunk_threshold, 5000)
        self.assertEqual(self.extractor.summarization_threshold, 9000)
        self.assertEqual(self.extractor.max_summary_length, 4000)

    def test_configure_chunking_no_args_is_a_noop(self):
        before = (self.extractor.text_chunker.chunk_size, self.extractor.auto_chunk_threshold)
        self.extractor.configure_chunking()
        after = (self.extractor.text_chunker.chunk_size, self.extractor.auto_chunk_threshold)
        self.assertEqual(before, after)

    def test_configure_chunking_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.configure_chunking(chunk_size=1000)  # should not raise

    def test_configure_chunking_for_model_delegates_to_configure_chunking(self):
        expected_chunk_size = TextChunker.calculate_chunk_size_for_model(8192, 1500)
        self.extractor.configure_chunking_for_model(max_context_tokens=8192, prompt_overhead_tokens=1500)
        self.assertEqual(self.extractor.text_chunker.chunk_size, expected_chunk_size)

    def test_configure_chunking_for_model_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.configure_chunking_for_model(max_context_tokens=4096)  # should not raise


class TestChunkingQueries(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()

    def test_should_chunk_text_below_threshold(self):
        self.assertFalse(self.extractor.should_chunk_text("short text"))

    def test_should_chunk_text_above_threshold(self):
        self.extractor.configure_chunking(auto_chunk_threshold=10)
        self.assertTrue(self.extractor.should_chunk_text("this text is definitely longer than ten chars"))

    def test_chunk_text_delegates_to_text_chunker(self):
        self.extractor.configure_chunking(chunk_size=20, overlap=0, strategy="fixed")
        chunks = self.extractor.chunk_text("a" * 100)
        self.assertGreater(len(chunks), 1)

    def test_get_chunking_info_returns_dict(self):
        info = self.extractor.get_chunking_info("some text to analyze")
        self.assertIsInstance(info, dict)

    def test_should_use_summarization_below_threshold(self):
        self.assertFalse(self.extractor.should_use_summarization("short text"))

    def test_should_use_summarization_above_threshold(self):
        self.extractor.configure_chunking(summarization_threshold=10)
        self.assertTrue(self.extractor.should_use_summarization("this text is definitely longer than ten chars"))


class TestSummaryCacheAndConfig(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()
        # Replace the LLM-backed summarizer with a deterministic stub.
        self.extractor.text_summarizer = MagicMock(
            side_effect=lambda text: MagicMock(summary=f"summary-of[{text[:10]}]")
        )
        self.extractor.chunk_summarizer = MagicMock(
            return_value=MagicMock(combined_summary="combined-summary")
        )

    def test_summarize_chunk_calls_summarizer_and_caches(self):
        result1 = self.extractor.summarize_chunk("some chunk text")
        result2 = self.extractor.summarize_chunk("some chunk text")
        self.assertEqual(result1, result2)
        self.extractor.text_summarizer.assert_called_once()  # second call was served from cache

    def test_summarize_chunks_returns_summary_per_chunk(self):
        summaries = self.extractor.summarize_chunks(["chunk one", "chunk two"])
        self.assertEqual(len(summaries), 2)

    def test_summarize_chunk_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.text_summarizer = MagicMock(return_value=MagicMock(summary="s"))
        extractor.summarize_chunk("chunk")  # should not raise

    def test_summarize_chunk_evicts_oldest_entry_when_cache_full(self):
        self.extractor.configure_cache(max_cache_size=1)
        self.extractor.summarize_chunk("first chunk")
        self.assertEqual(len(self.extractor._chunk_summary_cache), 1)
        self.extractor.summarize_chunk("second chunk")
        # Cache size limit is enforced before inserting the new entry, so it
        # stays at 1 with only the newest entry present.
        self.assertEqual(len(self.extractor._chunk_summary_cache), 1)
        self.assertIn(hash("second chunk"), self.extractor._chunk_summary_cache)

    def test_configure_cache_clears_cache_when_shrinking_below_current_size(self):
        self.extractor.summarize_chunk("a")
        self.extractor.summarize_chunk("b")
        self.assertEqual(len(self.extractor._chunk_summary_cache), 2)
        self.extractor.configure_cache(max_cache_size=1)
        self.assertEqual(len(self.extractor._chunk_summary_cache), 0)

    def test_configure_cache_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.configure_cache(max_cache_size=5)  # should not raise

    def test_clear_summary_cache(self):
        self.extractor.summarize_chunk("something")
        self.assertEqual(len(self.extractor._chunk_summary_cache), 1)
        self.extractor.clear_summary_cache()
        self.assertEqual(len(self.extractor._chunk_summary_cache), 0)

    def test_clear_summary_cache_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.clear_summary_cache()  # should not raise

    def test_create_combined_summary_concatenates_when_short(self):
        combined = self.extractor.create_combined_summary(["short one", "short two"])
        self.assertEqual(combined, "short one\n\nshort two")
        self.extractor.chunk_summarizer.assert_not_called()

    def test_create_combined_summary_uses_llm_when_too_long(self):
        self.extractor.configure_chunking(max_summary_length=5)
        combined = self.extractor.create_combined_summary(["a longer summary than five chars"])
        self.assertEqual(combined, "combined-summary"[:5])
        self.extractor.chunk_summarizer.assert_called_once()

    def test_create_combined_summary_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.configure_chunking(max_summary_length=5)
        extractor.chunk_summarizer = MagicMock(return_value=MagicMock(combined_summary="combined-summary"))
        extractor.create_combined_summary(["a longer summary than five chars"])  # should not raise


class TestGetClusteringContext(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()
        self.extractor.text_summarizer = MagicMock(return_value=MagicMock(summary="chunk summary"))
        self.extractor.chunk_summarizer = MagicMock(return_value=MagicMock(combined_summary="final summary"))

    def test_small_text_returned_directly(self):
        context = self.extractor.get_clustering_context("small text")
        self.assertEqual(context, "small text")

    def test_text_below_summarization_threshold_but_above_max_summary_length_is_truncated(self):
        self.extractor.configure_chunking(max_summary_length=5, summarization_threshold=1000)
        context = self.extractor.get_clustering_context("a text longer than five characters")
        self.assertEqual(context, "a tex")

    def test_large_text_triggers_summarization_pipeline(self):
        # max_summary_length is set small so create_combined_summary's own
        # concatenation branch is skipped and it calls chunk_summarizer instead.
        self.extractor.configure_chunking(
            summarization_threshold=10, chunk_size=20, overlap=0, strategy="fixed", max_summary_length=5
        )
        context = self.extractor.get_clustering_context("this text is definitely longer than ten characters")
        self.assertEqual(context, "final")  # "final summary" truncated to max_summary_length=5
        self.extractor.chunk_summarizer.assert_called_once()

    def test_large_text_with_precomputed_chunks_skips_chunking(self):
        self.extractor.configure_chunking(summarization_threshold=5, max_summary_length=5)
        context = self.extractor.get_clustering_context("long enough text", chunks=["precomputed chunk"])
        self.assertEqual(context, "final")

    def test_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.text_summarizer = MagicMock(return_value=MagicMock(summary="s"))
        extractor.chunk_summarizer = MagicMock(return_value=MagicMock(combined_summary="cs"))
        extractor.configure_chunking(summarization_threshold=5)
        extractor.get_clustering_context("long enough text")  # should not raise


class TestGetCorrespondingLiteral(unittest.TestCase):
    def setUp(self):
        self.extractor = DomainGraphExtractor()

    def test_datetime_literal(self):
        literal = self.extractor.get_corresponding_literal("2024-05-17T10:30:00")
        self.assertTrue(literal.is_datetime())
        self.assertEqual(literal.parse_datetime(), datetime(2024, 5, 17, 10, 30, 0))

    def test_date_only_string_is_parsed_as_datetime_on_py311plus(self):
        # NOTE: Python 3.11+ relaxed datetime.fromisoformat() to accept
        # date-only strings (treating the time as midnight), so the DateTime
        # branch (tried first) succeeds for "2024-05-17" and the dedicated
        # Date branch below it is never reached for this input. Use a
        # non-ISO date string to actually exercise the Date branch instead.
        literal = self.extractor.get_corresponding_literal("2024-05-17")
        self.assertTrue(literal.is_datetime())
        self.assertEqual(literal.parse_datetime(), datetime(2024, 5, 17, 0, 0))

    def test_date_literal_via_non_iso_format_string(self):
        with unittest.mock.patch(
            "owlapy.agen_kg.graph_extractor.datetime"
        ) as mock_datetime_cls:
            mock_datetime_cls.fromisoformat.side_effect = ValueError("not iso")
            mock_datetime_cls.strptime.side_effect = datetime.strptime
            literal = self.extractor.get_corresponding_literal("2024-05-17")
        self.assertTrue(literal.is_date())
        self.assertEqual(literal.parse_date(), date(2024, 5, 17))

    def test_boolean_literal_true(self):
        literal = self.extractor.get_corresponding_literal("true")
        self.assertTrue(literal.is_boolean())
        self.assertTrue(literal.parse_boolean())

    def test_boolean_literal_false(self):
        literal = self.extractor.get_corresponding_literal("False")
        self.assertTrue(literal.is_boolean())
        self.assertFalse(literal.parse_boolean())

    def test_integer_literal(self):
        literal = self.extractor.get_corresponding_literal("42")
        self.assertTrue(literal.is_integer())
        self.assertEqual(literal.parse_int(), 42)

    def test_float_literal(self):
        literal = self.extractor.get_corresponding_literal("3.14")
        self.assertTrue(literal.is_double())
        self.assertAlmostEqual(literal.parse_double(), 3.14)

    def test_string_literal_fallback(self):
        literal = self.extractor.get_corresponding_literal("just some text")
        self.assertTrue(literal.is_string())
        self.assertEqual(literal.parse_string(), "just some text")

    def test_returns_owl_literal_instance(self):
        self.assertIsInstance(self.extractor.get_corresponding_literal("42"), OWLLiteral)


if __name__ == '__main__':
    unittest.main()
