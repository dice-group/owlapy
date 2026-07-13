import unittest

from owlapy.agen_kg.chunking_models.simple_chunker import TextChunker


class TestChunkTextBasics(unittest.TestCase):
    """Test the top-level chunk_text dispatch and edge cases."""

    def test_empty_text_returns_empty_list(self):
        chunker = TextChunker()
        self.assertEqual(chunker.chunk_text(""), [])

    def test_text_shorter_than_chunk_size_returned_as_single_chunk(self):
        chunker = TextChunker(chunk_size=1000)
        text = "This is a short piece of text."
        self.assertEqual(chunker.chunk_text(text), [text])

    def test_unknown_strategy_raises_value_error(self):
        chunker = TextChunker(strategy="unknown")
        with self.assertRaises(ValueError):
            chunker.chunk_text("x" * 10000)

    def test_logging_enabled_does_not_raise(self):
        chunker = TextChunker(chunk_size=50, overlap=0, strategy="fixed", enable_logging=True)
        text = "word " * 50
        chunks = chunker.chunk_text(text)
        self.assertGreater(len(chunks), 1)


class TestChunkBySentences(unittest.TestCase):
    def test_splits_multiple_sentences_into_chunks(self):
        chunker = TextChunker(chunk_size=60, overlap=0, strategy="sentence")
        text = ("Sentence one is here. Sentence two follows now. "
                "Sentence three comes next. Sentence four ends it.")
        chunks = chunker.chunk_text(text)
        self.assertGreater(len(chunks), 1)
        # No chunk should exceed the configured size by a large margin
        for chunk in chunks:
            self.assertLessEqual(len(chunk), chunker.chunk_size + 20)

    def test_no_sentence_boundaries_falls_back_to_paragraphs(self):
        chunker = TextChunker(chunk_size=20, overlap=0, strategy="sentence")
        text = "onelongwordwithoutandpunctuationatallxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        chunks = chunker.chunk_text(text)
        self.assertGreater(len(chunks), 0)
        self.assertEqual("".join(c.replace(" ", "") for c in chunks).replace(" ", ""),
                          text.replace(" ", ""))

    def test_overlap_included_between_chunks(self):
        chunker = TextChunker(chunk_size=40, overlap=15, strategy="sentence")
        text = ("Alpha sentence is short. Beta sentence is short too. "
                "Gamma sentence follows here. Delta sentence ends the text.")
        chunks = chunker.chunk_text(text)
        self.assertGreater(len(chunks), 1)

    def test_oversized_single_sentence_is_split_further(self):
        chunker = TextChunker(chunk_size=30, overlap=0, strategy="sentence")
        long_sentence = "Word " * 30 + "."
        text = f"Short one. {long_sentence} Short two."
        chunks = chunker.chunk_text(text)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), chunker.chunk_size + 5)


class TestChunkByParagraphs(unittest.TestCase):
    def test_splits_multiple_paragraphs_into_chunks(self):
        chunker = TextChunker(chunk_size=50, overlap=0, strategy="paragraph")
        text = "Para one text here.\n\nPara two text here.\n\nPara three text here."
        chunks = chunker.chunk_text(text)
        self.assertGreater(len(chunks), 1)

    def test_no_paragraph_boundaries_falls_back_to_fixed(self):
        chunker = TextChunker(chunk_size=20, overlap=0, strategy="paragraph")
        text = "a" * 100
        chunks = chunker.chunk_text(text)
        self.assertGreater(len(chunks), 1)

    def test_overlap_keeps_last_paragraph_when_it_fits(self):
        chunker = TextChunker(chunk_size=40, overlap=25, strategy="paragraph")
        text = "Short para A.\n\nShort para B.\n\nShort para C.\n\nShort para D."
        chunks = chunker.chunk_text(text)
        self.assertGreater(len(chunks), 1)

    def test_oversized_single_paragraph_is_split_by_sentences(self):
        chunker = TextChunker(chunk_size=30, overlap=0, strategy="paragraph")
        long_para = "This is sentence one. This is sentence two. This is sentence three."
        text = f"Short para.\n\n{long_para}"
        chunks = chunker.chunk_text(text)
        self.assertGreater(len(chunks), 1)


class TestChunkFixed(unittest.TestCase):
    def test_fixed_strategy_splits_at_word_boundaries(self):
        chunker = TextChunker(chunk_size=20, overlap=0, strategy="fixed")
        text = "one two three four five six seven eight nine ten"
        chunks = chunker.chunk_text(text)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 20)

    def test_fixed_strategy_with_overlap_progresses(self):
        chunker = TextChunker(chunk_size=20, overlap=5, strategy="fixed")
        text = "word " * 20
        chunks = chunker.chunk_text(text)
        self.assertGreater(len(chunks), 1)

    def test_fixed_strategy_terminates_when_final_chunk_reaches_end_of_text(self):
        # Regression test: with overlap > 0, once the cursor's fixed-size window
        # reaches the end of the text, start = end - overlap must not loop forever
        # re-emitting the same trailing slice. See _chunk_fixed.
        chunker = TextChunker(chunk_size=3000, overlap=200, strategy="fixed")
        text = "x" * 50000
        chunks = chunker.chunk_text(text)
        self.assertGreater(len(chunks), 1)
        self.assertLess(len(chunks), 100)

    def test_fixed_strategy_terminates_with_overlap_close_to_chunk_size(self):
        chunker = TextChunker(chunk_size=20, overlap=19, strategy="fixed")
        text = "word " * 50
        chunks = chunker.chunk_text(text)
        self.assertGreater(len(chunks), 1)
        self.assertLess(len(chunks), 500)

    def test_fixed_strategy_no_space_breaks_at_chunk_size(self):
        chunker = TextChunker(chunk_size=10, overlap=0, strategy="fixed")
        text = "a" * 35
        chunks = chunker.chunk_text(text)
        self.assertTrue(all(len(c) <= 10 for c in chunks))
        self.assertEqual("".join(chunks), text)


class TestEstimateTokens(unittest.TestCase):
    def test_default_ratio(self):
        chunker = TextChunker()
        self.assertEqual(chunker.estimate_tokens("a" * 40), 10)

    def test_custom_ratio(self):
        chunker = TextChunker()
        self.assertEqual(chunker.estimate_tokens("a" * 40, chars_per_token=2), 20)


class TestGetChunkInfo(unittest.TestCase):
    def test_info_fields_for_short_text(self):
        chunker = TextChunker(chunk_size=1000)
        text = "A short bit of text."
        info = chunker.get_chunk_info(text)
        self.assertEqual(info["total_chars"], len(text))
        self.assertEqual(info["num_chunks"], 1)
        self.assertEqual(info["chunk_sizes"], [len(text)])
        self.assertEqual(info["avg_chunk_size"], len(text))
        self.assertEqual(info["strategy"], "sentence")
        self.assertEqual(info["configured_chunk_size"], 1000)
        self.assertEqual(info["configured_overlap"], 200)

    def test_info_for_empty_text_has_zero_avg(self):
        chunker = TextChunker()
        info = chunker.get_chunk_info("")
        self.assertEqual(info["num_chunks"], 0)
        self.assertEqual(info["avg_chunk_size"], 0)


class TestCalculateChunkSizeForModel(unittest.TestCase):
    def test_default_parameters(self):
        size = TextChunker.calculate_chunk_size_for_model(8000, 2000)
        # (8000 - 2000) * 0.8 * 4
        self.assertEqual(size, 19200)

    def test_custom_chars_per_token(self):
        size = TextChunker.calculate_chunk_size_for_model(4000, 1000, chars_per_token=3)
        # (4000 - 1000) * 0.8 * 3
        self.assertEqual(size, 7200)


if __name__ == "__main__":
    unittest.main()
