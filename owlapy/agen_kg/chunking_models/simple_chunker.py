import re
from typing import List


class TextChunker:
    """
    Utility class for splitting large texts into smaller chunks that fit within
    an LLM's context window. Supports multiple chunking strategies.

    This is essential for handling large documents (e.g., long PDFs, books,
    extensive reports) when using LLMs with limited context windows.
    """

    # Approximate token/character ratios for different models
    # These are conservative estimates (1 token ≈ 4 characters for English text)
    DEFAULT_CHARS_PER_TOKEN = 4

    def __init__(
        self,
        chunk_size: int = 3000,
        overlap: int = 200,
        strategy: str = "sentence",
        enable_logging: bool = False
    ):
        """
        Initialize the text chunker.

        Args:
            chunk_size: Maximum number of characters per chunk (default: 3000, ~750 tokens).
                       Set based on your model's context window and prompt overhead.
            overlap: Number of characters to overlap between consecutive chunks (default: 200).
                    This helps preserve context at chunk boundaries.
            strategy: Chunking strategy to use:
                - "sentence": Split on sentence boundaries (default, recommended)
                - "paragraph": Split on paragraph boundaries
                - "fixed": Split at fixed character positions (may break mid-word/sentence)
            enable_logging: Whether to log chunking information.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.strategy = strategy
        self.logging = enable_logging

        # Sentence boundary patterns
        self._sentence_end_pattern = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
        # Paragraph boundary pattern (two or more newlines)
        self._paragraph_pattern = re.compile(r'\n\s*\n')

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks based on the configured strategy.

        Args:
            text: The text to split into chunks.

        Returns:
            List of text chunks.
        """
        if not text or len(text) <= self.chunk_size:
            return [text] if text else []

        if self.strategy == "sentence":
            chunks = self._chunk_by_sentences(text)
        elif self.strategy == "paragraph":
            chunks = self._chunk_by_paragraphs(text)
        elif self.strategy == "fixed":
            chunks = self._chunk_fixed(text)
        else:
            raise ValueError(f"Unknown chunking strategy: {self.strategy}. "
                           f"Use 'sentence', 'paragraph', or 'fixed'.")

        if self.logging:
            print(f"TextChunker: INFO :: Split text ({len(text)} chars) into {len(chunks)} chunks")
            for i, chunk in enumerate(chunks):
                print(f"  Chunk {i+1}: {len(chunk)} chars")

        return chunks

    def _chunk_by_sentences(self, text: str) -> List[str]:
        """Split text into chunks at sentence boundaries."""
        # Split text into sentences
        sentences = self._sentence_end_pattern.split(text)

        # If no sentence boundaries found, fall back to paragraph chunking
        if len(sentences) <= 1:
            return self._chunk_by_paragraphs(text)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_length = len(sentence)

            # If single sentence is too long, split it further
            if sentence_length > self.chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                # Split long sentence by paragraphs or fixed chunks
                long_sentence_chunks = self._chunk_fixed(sentence)
                chunks.extend(long_sentence_chunks)
                continue

            # Check if adding this sentence would exceed chunk size
            if current_length + sentence_length + 1 > self.chunk_size:
                # Save current chunk
                chunks.append(' '.join(current_chunk))

                # Start new chunk with overlap
                if self.overlap > 0 and current_chunk:
                    # Include last sentences up to overlap size
                    overlap_text = []
                    overlap_length = 0
                    for prev_sentence in reversed(current_chunk):
                        if overlap_length + len(prev_sentence) + 1 <= self.overlap:
                            overlap_text.insert(0, prev_sentence)
                            overlap_length += len(prev_sentence) + 1
                        else:
                            break
                    current_chunk = overlap_text
                    current_length = overlap_length
                else:
                    current_chunk = []
                    current_length = 0

            current_chunk.append(sentence)
            current_length += sentence_length + 1

        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def _chunk_by_paragraphs(self, text: str) -> List[str]:
        """Split text into chunks at paragraph boundaries."""
        # Split text into paragraphs
        paragraphs = self._paragraph_pattern.split(text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # If no paragraph boundaries found, fall back to fixed chunking
        if len(paragraphs) <= 1:
            return self._chunk_fixed(text)

        chunks = []
        current_chunk = []
        current_length = 0

        for para in paragraphs:
            para_length = len(para)

            # If single paragraph is too long, split it by sentences
            if para_length > self.chunk_size:
                # Save current chunk if exists
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                # Split long paragraph by sentences
                long_para_chunks = self._chunk_by_sentences(para)
                chunks.extend(long_para_chunks)
                continue

            # Check if adding this paragraph would exceed chunk size
            if current_length + para_length + 2 > self.chunk_size:
                # Save current chunk
                chunks.append('\n\n'.join(current_chunk))

                # Start new chunk with overlap (take last paragraph if fits)
                if self.overlap > 0 and current_chunk:
                    last_para = current_chunk[-1]
                    if len(last_para) <= self.overlap:
                        current_chunk = [last_para]
                        current_length = len(last_para)
                    else:
                        current_chunk = []
                        current_length = 0
                else:
                    current_chunk = []
                    current_length = 0

            current_chunk.append(para)
            current_length += para_length + 2

        # Add final chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def _chunk_fixed(self, text: str) -> List[str]:
        """Split text at fixed character positions with overlap."""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)

            # Try to break at word boundary
            if end < text_length:
                # Look for last space within the chunk
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space

            chunks.append(text[start:end].strip())

            # Move start position with overlap
            start = end - self.overlap if self.overlap > 0 else end

            # Ensure we're making progress
            if start >= text_length:
                break

        return chunks

    def estimate_tokens(self, text: str, chars_per_token: int = None) -> int:
        """
        Estimate the number of tokens in a text.

        Args:
            text: The text to estimate tokens for.
            chars_per_token: Character to token ratio (default: 4 for English).

        Returns:
            Estimated number of tokens.
        """
        if chars_per_token is None:
            chars_per_token = self.DEFAULT_CHARS_PER_TOKEN
        return len(text) // chars_per_token

    def get_chunk_info(self, text: str) -> dict:
        """
        Get information about how a text would be chunked.

        Args:
            text: The text to analyze.

        Returns:
            Dictionary with chunking information.
        """
        chunks = self.chunk_text(text)
        return {
            "total_chars": len(text),
            "estimated_tokens": self.estimate_tokens(text),
            "num_chunks": len(chunks),
            "chunk_sizes": [len(c) for c in chunks],
            "avg_chunk_size": sum(len(c) for c in chunks) / len(chunks) if chunks else 0,
            "strategy": self.strategy,
            "configured_chunk_size": self.chunk_size,
            "configured_overlap": self.overlap
        }

    @staticmethod
    def calculate_chunk_size_for_model(
        max_context_tokens: int,
        prompt_overhead_tokens: int = 1000,
        chars_per_token: int = 4
    ) -> int:
        """
        Calculate an appropriate chunk size based on model parameters.

        Args:
            max_context_tokens: Maximum context window size of the model.
            prompt_overhead_tokens: Estimated tokens used by prompts, few-shot examples, etc.
            chars_per_token: Character to token ratio (default: 4 for English).

        Returns:
            Recommended chunk size in characters.

        Example:
            # For GPT-4 with 8K context window
            chunk_size = TextChunker.calculate_chunk_size_for_model(8000, 2000)
        """
        available_tokens = max_context_tokens - prompt_overhead_tokens
        # Leave some buffer (use 80% of available space)
        safe_tokens = int(available_tokens * 0.8)
        return safe_tokens * chars_per_token
