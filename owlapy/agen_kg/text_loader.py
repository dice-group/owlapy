"""
Text loading module for extracting text from various file formats.
Supports: TXT, PDF, DOCX, RTF, HTML, and raw text strings.

Also provides text chunking utilities for handling large documents
that may not fit in an LLM's context window.
"""

import os
import re
from typing import Union, Optional, List
from abc import ABC, abstractmethod
from pathlib import Path


class TextLoader(ABC):
    """Base class for text loaders."""
    
    @abstractmethod
    def load(self, source: Union[str, Path]) -> str:
        """
        Load text from the given source.
        
        Args:
            source: File path or raw text string.
            
        Returns:
            Extracted text content.
            
        Raises:
            ValueError: If the source is invalid or cannot be processed.
        """
        pass


class TXTLoader(TextLoader):
    """Loader for plain text files."""
    
    def load(self, source: Union[str, Path]) -> str:
        """Load text from a .txt file."""
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source}")
        
        try:
            with open(source, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            for encoding in ['latin-1', 'iso-8859-1', 'cp1252']:
                try:
                    with open(source, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise ValueError(f"Could not decode file with standard encodings: {source}")


class PDFLoader(TextLoader):
    """Loader for PDF files."""
    
    def load(self, source: Union[str, Path]) -> str:
        """Load text from a PDF file."""
        try:
            import PyPDF2
        except ImportError:
            raise ImportError(
                "PyPDF2 is required for PDF support. "
                "Install it with: pip install PyPDF2"
            )
        
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source}")
        
        text_content = []
        try:
            with open(source, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_content.append(page.extract_text())
        except Exception as e:
            raise ValueError(f"Error reading PDF file {source}: {str(e)}")
        
        return '\n'.join(text_content)


class DOCXLoader(TextLoader):
    """Loader for DOCX files."""
    
    def load(self, source: Union[str, Path]) -> str:
        """Load text from a DOCX file."""
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "python-docx is required for DOCX support. "
                "Install it with: pip install python-docx"
            )
        
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source}")
        
        try:
            doc = Document(source)
            text_content = []
            for paragraph in doc.paragraphs:
                text_content.append(paragraph.text)
            # Also extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        text_content.append(cell.text)
            return '\n'.join(text_content)
        except Exception as e:
            raise ValueError(f"Error reading DOCX file {source}: {str(e)}")


class RTFLoader(TextLoader):
    """Loader for RTF files."""
    
    def load(self, source: Union[str, Path]) -> str:
        """Load text from an RTF file."""
        try:
            from striprtf.striprtf import rtf_to_text
        except ImportError:
            raise ImportError(
                "striprtf is required for RTF support. "
                "Install it with: pip install striprtf"
            )
        
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source}")
        
        try:
            with open(source, 'r', encoding='utf-8') as f:
                rtf_content = f.read()
            return rtf_to_text(rtf_content)
        except Exception as e:
            raise ValueError(f"Error reading RTF file {source}: {str(e)}")


class HTMLLoader(TextLoader):
    """Loader for HTML files."""
    
    def load(self, source: Union[str, Path]) -> str:
        """Load text from an HTML file."""
        try:
            from html.parser import HTMLParser
            from io import StringIO
        except ImportError:
            raise ImportError("html parser is required for HTML support (built-in module).")
        
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source}")
        
        try:
            with open(source, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Simple HTML parser to extract text
            class MLStripper(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.reset()
                    self.strict = False
                    self.convert_charrefs = True
                    self.text = StringIO()
                
                def handle_data(self, data):
                    self.text.write(data)
                
                def get_data(self):
                    return self.text.getvalue()
            
            stripper = MLStripper()
            stripper.feed(html_content)
            return stripper.get_data()
        except Exception as e:
            raise ValueError(f"Error reading HTML file {source}: {str(e)}")


class RawTextLoader(TextLoader):
    """Loader for raw text strings."""
    
    def load(self, source: Union[str, Path]) -> str:
        """Return the source as-is if it's not a file."""
        if isinstance(source, str):
            return source
        return str(source)


class UniversalTextLoader:
    """
    Universal text loader that automatically detects file type and loads content.
    Handles multiple formats: TXT, PDF, DOCX, RTF, HTML, and raw text strings.
    """
    
    def __init__(self, enable_logging: bool = False):
        """
        Initialize the universal text loader.
        
        Args:
            enable_logging: Whether to enable logging of loaded content info.
        """
        self.logging = enable_logging
        self.loaders = {
            '.txt': TXTLoader(),
            '.pdf': PDFLoader(),
            '.docx': DOCXLoader(),
            '.doc': DOCXLoader(),  # Try DOCX loader for .doc files
            '.rtf': RTFLoader(),
            '.html': HTMLLoader(),
            '.htm': HTMLLoader(),
        }
    
    def load(self, source: Union[str, Path], file_type: Optional[str] = None) -> str:
        """
        Load text from various sources.
        
        Args:
            source: File path (str or Path), or raw text string.
            file_type: Optional file extension (e.g., '.pdf', '.txt'). 
                      If not provided, will be auto-detected from the source.
        
        Returns:
            Extracted text content.
            
        Raises:
            ValueError: If the file type is not supported or content cannot be extracted.
            FileNotFoundError: If the specified file does not exist.
        """
        # Try to detect if source is a file path or raw text
        source_path = Path(source) if not isinstance(source, Path) else source
        
        is_file = source_path.is_file() if isinstance(source_path, Path) else isinstance(source, str) and os.path.isfile(str(source))
        
        if not is_file:
            # Source is raw text, not a file
            if self.logging:
                print("UniversalTextLoader: INFO :: Treating input as raw text string")
            return RawTextLoader().load(source)
        
        # Source is a file path
        source_path = Path(source)
        
        # Determine file type
        if file_type is None:
            file_type = source_path.suffix.lower()
        elif not file_type.startswith('.'):
            file_type = '.' + file_type.lower()
        
        # Get appropriate loader
        if file_type not in self.loaders:
            supported_types = ', '.join(self.loaders.keys())
            raise ValueError(
                f"Unsupported file type: {file_type}. "
                f"Supported types: {supported_types}"
            )
        
        loader = self.loaders[file_type]
        
        if self.logging:
            print(f"UniversalTextLoader: INFO :: Loading text from {file_type} file: {source_path.name}")
        
        try:
            text = loader.load(source_path)
            if self.logging:
                word_count = len(text.split())
                char_count = len(text)
                print(f"UniversalTextLoader: INFO :: Successfully loaded {word_count} words ({char_count} characters)")
            return text
        except Exception as e:
            raise ValueError(f"Error loading text from {source_path}: {str(e)}")
    
    def supports_file_type(self, file_type: str) -> bool:
        """
        Check if a file type is supported.
        
        Args:
            file_type: File extension (e.g., '.pdf', 'pdf').
            
        Returns:
            True if the file type is supported, False otherwise.
        """
        if not file_type.startswith('.'):
            file_type = '.' + file_type.lower()
        return file_type in self.loaders
    
    @property
    def supported_formats(self) -> list:
        """Get list of supported file formats."""
        return list(self.loaders.keys())


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


