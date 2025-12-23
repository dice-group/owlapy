import re
from typing import List, Union, Optional
import dspy
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime

from owlapy.owl_literal import OWLLiteral
from owlapy.owl_ontology import Ontology
from owlapy.agen_kg.signatures import (EntityDeduplication, CoherenceChecker, TypeClustering,
                                       RelationClustering, TextSummarizer, ChunkSummarizer,
                                       EntityDeduplicationWithSummary,
                                       TypeClusteringWithSummary, RelationClusteringWithSummary,
                                       IncrementalEntityMerger,
                                       IncrementalTripleMerger, IncrementalTypeMerger, PlanDecomposer
                                       )
from owlapy.agen_kg.text_loader import UniversalTextLoader, TextChunker

# A compatible metaclass that combines dspy.Module's metaclass with ABCMeta
class GraphExtractorMeta(type(dspy.Module), type(ABC)):
    """Metaclass that resolves conflicts between dspy.Module and ABC."""
    pass


class GraphExtractor(dspy.Module, ABC, metaclass=GraphExtractorMeta):
    """
    Base class for all graph extractors.
    Provides common functionality for entity clustering, coherence checking,
    text chunking for large documents, and utility methods shared across all extractor types.
    """

    def __init__(self, enable_logging=False, use_incremental_merging=True):
        """
        Initialize the graph extractor.

        Args:
            enable_logging: Whether to enable logging.
            use_incremental_merging: Whether to use incremental LLM-based merging for entities, triples,
                and type assertions. If False, uses simple direct merging without LLM calls (default: True).
        """
        super().__init__()
        self.fact_checking_instructions = None
        self.triple_with_literal_extraction_instructions = None
        self.literal_extraction_instructions = None
        self.type_assertion_instructions = None
        self.type_generation_instructions = None
        self.triple_extraction_instructions = None
        self.entity_extraction_instructions = None
        self.logging = enable_logging
        self.use_incremental_merging = use_incremental_merging
        self.plan_decomposer = dspy.ChainOfThought(PlanDecomposer)
        self.entity_deduplicator = dspy.Predict(EntityDeduplication)
        self.coherence_checker = dspy.Predict(CoherenceChecker)
        self.type_clusterer = dspy.Predict(TypeClustering)
        self.relation_clusterer = dspy.Predict(RelationClustering)
        # Summarization-based clustering (for large texts)
        self.entity_deduplicator_with_summary = dspy.Predict(EntityDeduplicationWithSummary)
        self.type_clusterer_with_summary = dspy.Predict(TypeClusteringWithSummary)
        self.relation_clusterer_with_summary = dspy.Predict(RelationClusteringWithSummary)
        # Summarization modules
        self.text_summarizer = dspy.Predict(TextSummarizer)
        self.chunk_summarizer = dspy.Predict(ChunkSummarizer)
        # Incremental merging modules
        self.entity_merger = dspy.Predict(IncrementalEntityMerger)
        self.triple_merger = dspy.Predict(IncrementalTripleMerger)
        self.type_merger = dspy.Predict(IncrementalTypeMerger)

        self.text_loader = UniversalTextLoader(enable_logging=enable_logging)
        # Default text chunker - can be configured via configure_chunking()
        self.text_chunker = TextChunker(
            chunk_size=6000,  # ~1500 tokens
            overlap=300,
            strategy="paragraph",
            enable_logging=enable_logging
        )
        # Threshold for automatic chunking (in characters)
        self.auto_chunk_threshold = 4000  # ~1000 tokens
        # Threshold for using summarization in clustering (in characters)
        # When text exceeds this, use summarization-based clustering
        self.summarization_threshold = 8000  # ~2000 tokens
        # Maximum summary length (in characters) for clustering context
        self.max_summary_length = 3000  # ~750 tokens
        # Cache for chunk summaries (chunk_text_hash -> summary)
        self._chunk_summary_cache = {}
        # Maximum cache size to prevent memory leaks
        self._max_cache_size = 1000

    @staticmethod
    def snake_case(text):
        # Normalize whitespace and special chars
        text = re.sub(r'[^\w\s]', '', text)  # Remove special chars
        text = re.sub(r'\s+', '_', text.strip())  # Multiple spaces -> single underscore
        return text.lower()

    @staticmethod
    def format_type_name(text):
        """
        Format a type name to start with capital letter and rest lowercase.
        E.g., 'PERSON' -> 'Person', 'person' -> 'Person', 'PERSON_TYPE' -> 'Person_type'

        Args:
            text: The type name to format.

        Returns:
            Formatted type name with capital first letter and lowercase rest.
        """
        # Normalize whitespace and special chars
        text = re.sub(r'[^\w\s]', '', text)  # Remove special chars
        text = re.sub(r'\s+', '_', text.strip())  # Multiple spaces -> single underscore
        # Convert to lowercase first, then capitalize first letter
        text = text.lower()
        if text:
            text = text[0].upper() + text[1:]
        return text


    def plan_decompose(self, query: str):
        if query is None:
            query = "Extract knowledge graph relevant information from the provided text."

        results = self.plan_decomposer(user_request=query)

        self.entity_extraction_instructions = results.entity_extraction_task
        self.triple_extraction_instructions = results.triple_extraction_task
        self.type_generation_instructions = results.type_generation_task
        self.type_assertion_instructions = results.type_assertion_task
        self.literal_extraction_instructions = results.literal_extraction_task
        self.triple_with_literal_extraction_instructions = results.triple_with_literal_extraction_task
        self.fact_checking_instructions = results.fact_checking_task

        print(f"{self.__class__.__name__}: INFO :: Decomposed the query into specific instructions")

    def load_text(self, source: Union[str, Path], file_type: Optional[str] = None) -> str:
        """
        Load text from various sources (files or raw text).

        Supports multiple file formats:
        - Plain text: .txt
        - PDF: .pdf
        - Word documents: .docx, .doc
        - Rich Text: .rtf
        - HTML: .html, .htm
        - Raw text strings

        Args:
            source: File path (str or Path) or raw text string.
            file_type: Optional file extension (e.g., '.pdf', '.txt').
                      If not provided, will be auto-detected from the source.

        Returns:
            Extracted text content as a string.

        Raises:
            ValueError: If the file type is not supported or content cannot be extracted.
            FileNotFoundError: If the specified file does not exist.

        Examples:
            # Load from file
            text = extractor.load_text('document.pdf')
            text = extractor.load_text('/path/to/file.docx')

            # Load from raw text
            text = extractor.load_text('This is raw text input')

            # Specify file type explicitly
            text = extractor.load_text('file.txt', file_type='.txt')
        """
        try:
            return self.text_loader.load(source, file_type)
        except Exception as e:
            if self.logging:
                print(f"{self.__class__.__name__}: ERROR :: Failed to load text from source: {e}")
            raise

    def get_supported_formats(self) -> list:
        """
        Get list of supported file formats.

        Returns:
            List of supported file extensions (e.g., ['.txt', '.pdf', '.docx', ...])
        """
        return self.text_loader.supported_formats

    def configure_chunking(
            self,
            chunk_size: int = None,
            overlap: int = None,
            strategy: str = None,
            auto_chunk_threshold: int = None,
            summarization_threshold: int = None,
            max_summary_length: int = None
    ):
        """
        Configure text chunking settings for handling large documents.

        This method allows fine-tuning of how large texts are split into
        manageable pieces for LLM processing.

        Args:
            chunk_size: Maximum characters per chunk (default: 3000, ~750 tokens).
            overlap: Characters to overlap between chunks (default: 200).
            strategy: Chunking strategy - "sentence", "paragraph", or "fixed".
            auto_chunk_threshold: Character threshold for automatic chunking (default: 4000).
                                 Texts larger than this will be automatically chunked.
            summarization_threshold: Character threshold for using summarization in clustering
                                    (default: 8000). When text exceeds this, summaries are
                                    generated to provide context for clustering operations.
            max_summary_length: Maximum length of summaries used for clustering context
                               (default: 3000, ~750 tokens).

        Example:
            # Configure for a model with smaller context window
            extractor.configure_chunking(chunk_size=2000, overlap=150, strategy="sentence")

            # Configure for larger context window (e.g., GPT-4-turbo)
            extractor.configure_chunking(chunk_size=8000, overlap=500)

            # Configure summarization thresholds
            extractor.configure_chunking(summarization_threshold=10000, max_summary_length=4000)
        """
        if chunk_size is not None or overlap is not None or strategy is not None:
            self.text_chunker = TextChunker(
                chunk_size=chunk_size or self.text_chunker.chunk_size,
                overlap=overlap if overlap is not None else self.text_chunker.overlap,
                strategy=strategy or self.text_chunker.strategy,
                enable_logging=self.logging
            )

        if auto_chunk_threshold is not None:
            self.auto_chunk_threshold = auto_chunk_threshold

        if summarization_threshold is not None:
            self.summarization_threshold = summarization_threshold

        if max_summary_length is not None:
            self.max_summary_length = max_summary_length

        if self.logging:
            print(f"{self.__class__.__name__}: INFO :: Chunking configured - "
                  f"chunk_size={self.text_chunker.chunk_size}, "
                  f"overlap={self.text_chunker.overlap}, "
                  f"strategy={self.text_chunker.strategy}, "
                  f"auto_threshold={self.auto_chunk_threshold}, "
                  f"summarization_threshold={self.summarization_threshold}, "
                  f"max_summary_length={self.max_summary_length}")

    def configure_chunking_for_model(
            self,
            max_context_tokens: int,
            prompt_overhead_tokens: int = 1500
    ):
        """
        Automatically configure chunking based on model specifications.

        This is a convenience method that calculates optimal chunk size
        based on your model's context window.

        Args:
            max_context_tokens: Maximum context window of your model (e.g., 4096 for GPT-3.5).
            prompt_overhead_tokens: Estimated tokens used by prompts/few-shot examples.

        Example:
            # For GPT-3.5-turbo (4K context)
            extractor.configure_chunking_for_model(4096, 1000)

            # For GPT-4 (8K context)
            extractor.configure_chunking_for_model(8192, 1500)

            # For GPT-4-turbo (128K context)
            extractor.configure_chunking_for_model(128000, 2000)
        """
        chunk_size = TextChunker.calculate_chunk_size_for_model(
            max_context_tokens,
            prompt_overhead_tokens
        )
        self.configure_chunking(chunk_size=chunk_size)

        if self.logging:
            print(f"{self.__class__.__name__}: INFO :: Configured for model with "
                  f"{max_context_tokens} token context window, "
                  f"chunk_size={chunk_size} chars")

    def should_chunk_text(self, text: str) -> bool:
        """
        Determine if text should be chunked based on its size.

        Args:
            text: The text to check.

        Returns:
            True if text exceeds the auto_chunk_threshold.
        """
        return len(text) > self.auto_chunk_threshold

    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks for processing.

        Args:
            text: The text to chunk.

        Returns:
            List of text chunks.
        """
        return self.text_chunker.chunk_text(text)

    def get_chunking_info(self, text: str) -> dict:
        """
        Get information about how a text would be chunked.

        Args:
            text: The text to analyze.

        Returns:
            Dictionary with chunking information including number of chunks,
            chunk sizes, etc.
        """
        return self.text_chunker.get_chunk_info(text)

    def should_use_summarization(self, text: str) -> bool:
        """
        Determine if text is large enough to require summarization for clustering.

        Args:
            text: The text to check.

        Returns:
            True if text exceeds the summarization_threshold.
        """
        return len(text) > self.summarization_threshold

    def summarize_chunk(self, chunk: str) -> str:
        """
        Generate a summary of a text chunk that preserves key entities and relationships.

        Args:
            chunk: Text chunk to summarize.

        Returns:
            Summary of the chunk.
        """
        # Check cache first
        chunk_hash = hash(chunk)
        if chunk_hash in self._chunk_summary_cache:
            return self._chunk_summary_cache[chunk_hash]

        result = self.text_summarizer(text=chunk)
        summary = result.summary

        # Cache the summary with size limit
        if len(self._chunk_summary_cache) >= self._max_cache_size:
            # Remove oldest entry (first key) to prevent unbounded growth
            first_key = next(iter(self._chunk_summary_cache))
            del self._chunk_summary_cache[first_key]
            if self.logging:
                print(f"{self.__class__.__name__}: INFO :: Cache limit reached, evicted oldest entry")

        self._chunk_summary_cache[chunk_hash] = summary

        if self.logging:
            print(f"{self.__class__.__name__}: INFO :: Summarized chunk from {len(chunk)} to {len(summary)} chars")

        return summary

    def summarize_chunks(self, chunks: List[str]) -> List[str]:
        """
        Generate summaries for multiple text chunks.

        Args:
            chunks: List of text chunks.

        Returns:
            List of chunk summaries.
        """
        summaries = []
        for i, chunk in enumerate(chunks):
            summary = self.summarize_chunk(chunk)
            summaries.append(summary)
            if self.logging:
                print(f"{self.__class__.__name__}: INFO :: Generated summary for chunk {i + 1}/{len(chunks)}")
        return summaries

    def create_combined_summary(self, chunk_summaries: List[str]) -> str:
        """
        Combine multiple chunk summaries into a unified summary for clustering context.

        Args:
            chunk_summaries: List of summaries from individual chunks.

        Returns:
            A combined summary suitable for clustering operations.
        """
        # If summaries are small enough, just concatenate them
        total_length = sum(len(s) for s in chunk_summaries)
        if total_length <= self.max_summary_length:
            return "\n\n".join(chunk_summaries)

        # Otherwise, use LLM to combine them
        result = self.chunk_summarizer(chunk_summaries=chunk_summaries)
        combined = result.combined_summary

        # Truncate if still too long
        if len(combined) > self.max_summary_length:
            combined = combined[:self.max_summary_length]

        if self.logging:
            print(
                f"{self.__class__.__name__}: INFO :: Combined {len(chunk_summaries)} summaries into {len(combined)} chars")

        return combined

    def get_clustering_context(self, text: str, chunks: List[str] = None) -> str:
        """
        Get appropriate context for clustering operations based on text size.

        For small texts, returns the text directly (possibly truncated).
        For large texts, generates a summary to use as clustering context.

        Args:
            text: The full text.
            chunks: Optional pre-computed chunks of the text.

        Returns:
            Context string suitable for clustering operations.
        """
        # For small texts, use the text directly
        if not self.should_use_summarization(text):
            if len(text) > self.max_summary_length:
                return text[:self.max_summary_length]
            return text

        # For large texts, generate summary
        if self.logging:
            print(
                f"{self.__class__.__name__}: INFO :: Text exceeds summarization threshold, generating summary for clustering")

        # Use provided chunks or create new ones
        if chunks is None:
            chunks = self.chunk_text(text)

        # Generate summaries for each chunk
        chunk_summaries = self.summarize_chunks(chunks)

        # Combine summaries
        combined_summary = self.create_combined_summary(chunk_summaries)

        return combined_summary

    def clear_summary_cache(self):
        """Clear the chunk summary cache."""
        self._chunk_summary_cache.clear()
        if self.logging:
            print(f"{self.__class__.__name__}: INFO :: Cleared summary cache")

    def configure_cache(self, max_cache_size: int = None):
        """
        Configure summary cache settings.

        Args:
            max_cache_size: Maximum number of summaries to cache (default: 1000).
                           Set to 0 to disable caching.

        Example:
            # Increase cache size for large batch processing
            extractor.configure_cache(max_cache_size=5000)

            # Disable caching to minimize memory usage
            extractor.configure_cache(max_cache_size=0)
        """
        if max_cache_size is not None:
            self._max_cache_size = max(0, max_cache_size)
            if self.logging:
                print(f"{self.__class__.__name__}: INFO :: Cache size limit set to {self._max_cache_size}")

            # Clear cache if new size is smaller than current cache size
            if len(self._chunk_summary_cache) > self._max_cache_size:
                self.clear_summary_cache()

    def _merge_entity_lists(self, entity_lists: List[List[str]], chunk_summaries: List[str] = None,
                            use_llm_merge: bool = None) -> List[str]:
        """
        Merge entity lists from multiple chunks, removing duplicates.

        Supports both simple deduplication and LLM-based semantic merging.

        Args:
            entity_lists: List of entity lists from each chunk.
            chunk_summaries: Optional list of chunk summaries for context-aware merging.
            use_llm_merge: Whether to use LLM for semantic entity merging. If None, uses
                self.use_incremental_merging (default: None).

        Returns:
            Merged and deduplicated list of entities.
        """
        if not entity_lists:
            return []

        # Simple case: only one chunk
        if len(entity_lists) == 1:
            return entity_lists[0]

        # Use class-level setting if not explicitly specified
        if use_llm_merge is None:
            use_llm_merge = self.use_incremental_merging

        # If no summaries provided or LLM merge disabled, use simple deduplication
        if not use_llm_merge or chunk_summaries is None or len(chunk_summaries) != len(entity_lists):
            return self._simple_merge_entities(entity_lists)

        # Use incremental LLM-based merging for better quality
        return self._incremental_merge_entities(entity_lists, chunk_summaries)

    def _simple_merge_entities(self, entity_lists: List[List[str]]) -> List[str]:
        """Simple deduplication-based entity merging."""
        all_entities = []
        seen = set()
        for entities in entity_lists:
            for entity in entities:
                entity_lower = entity.lower()
                if entity_lower not in seen:
                    seen.add(entity_lower)
                    all_entities.append(entity)
        return all_entities

    def _incremental_merge_entities(self, entity_lists: List[List[str]], chunk_summaries: List[str]) -> List[str]:
        """
        Incrementally merge entities using LLM for semantic deduplication.

        Uses a divide-and-conquer approach to merge entities pairwise,
        ensuring cross-chunk duplicates are properly identified.
        """
        if len(entity_lists) == 0:
            return []
        if len(entity_lists) == 1:
            return entity_lists[0]

        # Start with first chunk
        merged_entities = entity_lists[0].copy() if entity_lists[0] else []
        merged_context = chunk_summaries[0]

        # Global mapping to track all entity transformations
        global_mapping = {}

        for i in range(1, len(entity_lists)):
            # Skip empty entity lists
            if not entity_lists[i]:
                continue

            if self.logging:
                print(f"{self.__class__.__name__}: INFO :: Merging entity list {i + 1}/{len(entity_lists)}")

            # Skip LLM merge if current merged list is empty
            if not merged_entities:
                merged_entities = entity_lists[i].copy()
                merged_context = chunk_summaries[i]
                continue

            try:
                result = self.entity_merger(
                    entities_a=merged_entities,
                    entities_b=entity_lists[i],
                    context_a=merged_context[:1500] if len(merged_context) > 1500 else merged_context,
                    context_b=chunk_summaries[i][:1500] if len(chunk_summaries[i]) > 1500 else chunk_summaries[i],
                )

                # Validate result
                if not hasattr(result, 'merged_entities') or not result.merged_entities:
                    if self.logging:
                        print(f"{self.__class__.__name__}: WARNING :: LLM returned empty result, using simple merge")
                    raise ValueError("Empty result from LLM")

                merged_entities = result.merged_entities

                # Update global mapping with new mappings
                if hasattr(result, 'entity_mapping') and result.entity_mapping:
                    for original, canonical in result.entity_mapping:
                        global_mapping[original] = canonical

                # Update context (combine summaries, keeping it bounded)
                if len(merged_context) + len(chunk_summaries[i]) < self.max_summary_length:
                    merged_context = merged_context + "\n" + chunk_summaries[i]
                else:
                    # Keep most recent context
                    merged_context = chunk_summaries[i]

            except Exception as e:
                if self.logging:
                    print(f"{self.__class__.__name__}: WARNING :: LLM merge failed, falling back to simple merge: {e}")
                # Fallback to simple merge for this iteration
                seen = set(e.lower() for e in merged_entities)
                for entity in entity_lists[i]:
                    if entity.lower() not in seen:
                        seen.add(entity.lower())
                        merged_entities.append(entity)

        if self.logging and global_mapping:
            print(f"{self.__class__.__name__}: INFO :: Entity merge mappings: {global_mapping}")

        return merged_entities

    def _merge_triple_lists(self, triple_lists: List[List[tuple]], chunk_summaries: List[str] = None,
                            use_llm_merge: bool = None) -> List[tuple]:
        """
        Merge triple lists from multiple chunks, removing duplicates.

        Supports both simple deduplication and LLM-based semantic merging.

        Args:
            triple_lists: List of triple lists from each chunk.
            chunk_summaries: Optional list of chunk summaries for context-aware merging.
            use_llm_merge: Whether to use LLM for semantic triple merging. If None, uses
                self.use_incremental_merging (default: None).

        Returns:
            Merged and deduplicated list of triples.
        """
        if not triple_lists:
            return []

        if len(triple_lists) == 1:
            return triple_lists[0]

        # Use class-level setting if not explicitly specified
        if use_llm_merge is None:
            use_llm_merge = self.use_incremental_merging

        # If no summaries provided or LLM merge disabled, use simple deduplication
        if not use_llm_merge or chunk_summaries is None or len(chunk_summaries) != len(triple_lists):
            return self._simple_merge_triples(triple_lists)

        return self._incremental_merge_triples(triple_lists, chunk_summaries)

    def _simple_merge_triples(self, triple_lists: List[List[tuple]]) -> List[tuple]:
        """Simple deduplication-based triple merging."""
        all_triples = []
        seen = set()
        for triples in triple_lists:
            for triple in triples:
                # Normalize for comparison
                triple_key = (triple[0].lower(), triple[1].lower(), triple[2].lower())
                if triple_key not in seen:
                    seen.add(triple_key)
                    all_triples.append(triple)
        return all_triples

    def _incremental_merge_triples(self, triple_lists: List[List[tuple]], chunk_summaries: List[str]) -> List[tuple]:
        """
        Incrementally merge triples using LLM for semantic deduplication.
        """
        if len(triple_lists) == 0:
            return []
        if len(triple_lists) == 1:
            return triple_lists[0]

        merged_triples = list(triple_lists[0]) if triple_lists[0] else []
        merged_context = chunk_summaries[0]

        for i in range(1, len(triple_lists)):
            # Skip empty triple lists
            if not triple_lists[i]:
                continue

            if self.logging:
                print(f"{self.__class__.__name__}: INFO :: Merging triple list {i + 1}/{len(triple_lists)}")

            # Skip LLM merge if current merged list is empty
            if not merged_triples:
                merged_triples = list(triple_lists[i])
                merged_context = chunk_summaries[i]
                continue

            try:
                result = self.triple_merger(
                    triples_a=merged_triples,
                    triples_b=triple_lists[i],
                    context_a=merged_context[:1500] if len(merged_context) > 1500 else merged_context,
                    context_b=chunk_summaries[i][:1500] if len(chunk_summaries[i]) > 1500 else chunk_summaries[i],
                )

                # Validate result
                if not hasattr(result, 'merged_triples') or not result.merged_triples:
                    if self.logging:
                        print(f"{self.__class__.__name__}: WARNING :: LLM returned empty result, using simple merge")
                    raise ValueError("Empty result from LLM")

                merged_triples = result.merged_triples

                # Update context
                if len(merged_context) + len(chunk_summaries[i]) < self.max_summary_length:
                    merged_context = merged_context + "\n" + chunk_summaries[i]
                else:
                    merged_context = chunk_summaries[i]

            except Exception as e:
                if self.logging:
                    print(
                        f"{self.__class__.__name__}: WARNING :: LLM triple merge failed, falling back to simple merge: {e}")
                # Fallback to simple merge
                seen = set((t[0].lower(), t[1].lower(), t[2].lower()) for t in merged_triples)
                for triple in triple_lists[i]:
                    triple_key = (triple[0].lower(), triple[1].lower(), triple[2].lower())
                    if triple_key not in seen:
                        seen.add(triple_key)
                        merged_triples.append(triple)

        return merged_triples

    def _merge_type_assertions(self, assertion_lists: List[List[tuple]], chunk_summaries: List[str] = None,
                               use_llm_merge: bool = None) -> List[tuple]:
        """
        Merge type assertion lists from multiple chunks.

        For duplicate entity-type assignments, resolves conflicts intelligently.

        Args:
            assertion_lists: List of type assertion lists from each chunk.
            chunk_summaries: Optional list of chunk summaries for context-aware merging.
            use_llm_merge: Whether to use LLM for semantic type merging. If None, uses
                self.use_incremental_merging (default: None).

        Returns:
            Merged type assertions.
        """
        if not assertion_lists:
            return []

        if len(assertion_lists) == 1:
            return assertion_lists[0]

        # Use class-level setting if not explicitly specified
        if use_llm_merge is None:
            use_llm_merge = self.use_incremental_merging

        # If no summaries provided or LLM merge disabled, use simple merging
        if not use_llm_merge or chunk_summaries is None or len(chunk_summaries) != len(assertion_lists):
            return self._simple_merge_type_assertions(assertion_lists)

        return self._incremental_merge_type_assertions(assertion_lists, chunk_summaries)

    def _simple_merge_type_assertions(self, assertion_lists: List[List[tuple]]) -> List[tuple]:
        """Simple type assertion merging that keeps first seen type for each entity."""
        entity_types = {}  # entity -> type (keep first seen)
        for assertions in assertion_lists:
            for entity, entity_type in assertions:
                entity_lower = entity.lower()
                if entity_lower not in entity_types:
                    entity_types[entity_lower] = (entity, entity_type)
        return list(entity_types.values())

    def _incremental_merge_type_assertions(self, assertion_lists: List[List[tuple]], chunk_summaries: List[str]) -> \
    List[tuple]:
        """
        Incrementally merge type assertions using LLM to resolve conflicts.
        """
        if len(assertion_lists) == 0:
            return []
        if len(assertion_lists) == 1:
            return assertion_lists[0]

        merged_types = list(assertion_lists[0]) if assertion_lists[0] else []
        merged_context = chunk_summaries[0]

        for i in range(1, len(assertion_lists)):
            # Skip empty assertion lists
            if not assertion_lists[i]:
                continue

            if self.logging:
                print(f"{self.__class__.__name__}: INFO :: Merging type assertions {i + 1}/{len(assertion_lists)}")

            # Skip LLM merge if current merged list is empty
            if not merged_types:
                merged_types = list(assertion_lists[i])
                merged_context = chunk_summaries[i]
                continue

            try:
                result = self.type_merger(
                    types_a=merged_types,
                    types_b=assertion_lists[i],
                    context_a=merged_context[:1500] if len(merged_context) > 1500 else merged_context,
                    context_b=chunk_summaries[i][:1500] if len(chunk_summaries[i]) > 1500 else chunk_summaries[i],
                )

                # Validate result
                if not hasattr(result, 'merged_types') or not result.merged_types:
                    if self.logging:
                        print(f"{self.__class__.__name__}: WARNING :: LLM returned empty result, using simple merge")
                    raise ValueError("Empty result from LLM")

                merged_types = result.merged_types

                # Update context
                if len(merged_context) + len(chunk_summaries[i]) < self.max_summary_length:
                    merged_context = merged_context + "\n" + chunk_summaries[i]
                else:
                    merged_context = chunk_summaries[i]

            except Exception as e:
                if self.logging:
                    print(
                        f"{self.__class__.__name__}: WARNING :: LLM type merge failed, falling back to simple merge: {e}")
                # Fallback to simple merge
                existing_entities = set(t[0].lower() for t in merged_types)
                for entity, entity_type in assertion_lists[i]:
                    if entity.lower() not in existing_entities:
                        existing_entities.add(entity.lower())
                        merged_types.append((entity, entity_type))

        return merged_types

    def _merge_literal_lists(self, literal_lists: List[List[str]]) -> List[str]:
        """
        Merge literal value lists from multiple chunks, removing duplicates.

        Args:
            literal_lists: List of literal lists from each chunk.

        Returns:
            Merged and deduplicated list of literals.
        """
        all_literals = []
        seen = set()
        for literals in literal_lists:
            for literal in literals:
                if literal not in seen:
                    seen.add(literal)
                    all_literals.append(literal)
        return all_literals

    def filter_entities(self, entities: List[str], text: str, use_summary: bool = None) -> list:
        """
        Deduplicate entities by removing redundant near-duplicates.

        For large texts, automatically uses summarization to provide context
        that fits within token limits.

        Args:
            entities: List of extracted entities.
            text: Original text context (or pre-computed summary).
            use_summary: Whether to use summary-based deduplication.
                - None (default): Auto-detect based on text size.
                - True: Force summary-based deduplication.
                - False: Use direct text (may fail for large texts).

        Returns:
            Dictionary mapping original entity names to their canonical names.
        """
        if not entities:
            return []

        # Determine whether to use summarization
        if use_summary is None:
            use_summary = self.should_use_summarization(text)

        if use_summary:
            # Get or create summary for deduplication context
            clustering_context = self.get_clustering_context(text)
            if self.logging:
                print(
                    f"{self.__class__.__name__}: INFO :: Using summary ({len(clustering_context)} chars) for entity deduplication")
            result = self.entity_deduplicator_with_summary(entities=entities, summary=clustering_context)
        else:
            # Use direct text (truncated if necessary)
            context = text[:self.max_summary_length] if len(text) > self.max_summary_length else text
            result = self.entity_deduplicator(entities=entities, text=context)

        # Get the filtered entities list
        filtered_entities = result.filtered_entities

        if self.logging:
            merged_count = len(entities) - len(filtered_entities)
            if merged_count > 0:
                print(f"{self.__class__.__name__}: INFO :: Filtered out {merged_count} redundant entities")

        return filtered_entities

    def cluster_types(self, types: List[str], text: str, use_summary: bool = None) -> dict:
        """
        Cluster entity types to identify and merge duplicates.

        For large texts, automatically uses summarization to provide context
        that fits within token limits.

        Args:
            types: List of extracted entity types.
            text: Original text context (or pre-computed summary).
            use_summary: Whether to use summary-based clustering.
                - None (default): Auto-detect based on text size.
                - True: Force summary-based clustering.
                - False: Use direct text (may fail for large texts).

        Returns:
            Dictionary mapping original type names to their canonical names.
        """
        if not types:
            return {}

        # Determine whether to use summarization
        if use_summary is None:
            use_summary = self.should_use_summarization(text)

        if use_summary:
            clustering_context = self.get_clustering_context(text)
            if self.logging:
                print(
                    f"{self.__class__.__name__}: INFO :: Using summary ({len(clustering_context)} chars) for type clustering")
            result = self.type_clusterer_with_summary(types=types, summary=clustering_context)
        else:
            context = text[:self.max_summary_length] if len(text) > self.max_summary_length else text
            result = self.type_clusterer(types=types, text=context)

        type_mapping = {}

        for cluster, canonical_name in result.clusters:
            for type_name in cluster:
                type_mapping[type_name] = canonical_name

        # Add types that weren't clustered
        for type_name in types:
            if type_name not in type_mapping:
                type_mapping[type_name] = type_name

        if self.logging:
            merged_count = len(types) - len(set(type_mapping.values()))
            if merged_count > 0:
                print(f"{self.__class__.__name__}: INFO :: Merged {merged_count} duplicate types")

        return type_mapping

    def cluster_relations(self, relations: List[str], text: str, use_summary: bool = None) -> dict:
        """
        Cluster relations to identify and merge duplicates.

        For large texts, automatically uses summarization to provide context
        that fits within token limits.

        Args:
            relations: List of extracted relations.
            text: Original text context (or pre-computed summary).
            use_summary: Whether to use summary-based clustering.
                - None (default): Auto-detect based on text size.
                - True: Force summary-based clustering.
                - False: Use direct text (may fail for large texts).

        Returns:
            Dictionary mapping original relation names to their canonical names.
        """
        if not relations:
            return {}

        # Determine whether to use summarization
        if use_summary is None:
            use_summary = self.should_use_summarization(text)

        if use_summary:
            clustering_context = self.get_clustering_context(text)
            if self.logging:
                print(
                    f"{self.__class__.__name__}: INFO :: Using summary ({len(clustering_context)} chars) for relation clustering")
            result = self.relation_clusterer_with_summary(relations=relations, summary=clustering_context)
        else:
            context = text[:self.max_summary_length] if len(text) > self.max_summary_length else text
            result = self.relation_clusterer(relations=relations, text=context)

        relation_mapping = {}

        for cluster, canonical_name in result.clusters:
            for relation in cluster:
                relation_mapping[relation] = canonical_name

        # Add relations that weren't clustered
        for relation in relations:
            if relation not in relation_mapping:
                relation_mapping[relation] = relation

        if self.logging:
            merged_count = len(relations) - len(set(relation_mapping.values()))
            if merged_count > 0:
                print(f"{self.__class__.__name__}: INFO :: Merged {merged_count} duplicate relations")

        return relation_mapping

    def check_coherence(self, triples: List[tuple], text: str, task_instructions: str = None, batch_size: int = 50,
                        threshold: int = 3, use_summary: bool = None) -> List[tuple]:
        """
        Check coherence of extracted triples and filter out low-quality ones.

        For large texts, automatically uses summarization to provide context
        that fits within token limits.

        Args:
            triples: List of extracted triples.
            text: Original text context (or pre-computed summary).
            task_instructions: Optional instructions to guide coherence checking.
            batch_size: Number of triples to check per batch.
            threshold: Minimum coherence score (1-5) to keep a triple.
            use_summary: Whether to use summary for coherence checking.
                - None (default): Auto-detect based on text size.
                - True: Force summary-based checking.
                - False: Use direct text (may fail for large texts).

        Returns:
            List of coherent triples that passed the threshold.
        """
        if not triples:
            return []

        # Determine context to use
        if use_summary is None:
            use_summary = self.should_use_summarization(text)

        if use_summary:
            context = self.get_clustering_context(text)
            if self.logging:
                print(f"{self.__class__.__name__}: INFO :: Using summary ({len(context)} chars) for coherence checking")
        else:
            context = text[:self.max_summary_length] if len(text) > self.max_summary_length else text

        coherent_triples = []

        # Process triples in batches
        for i in range(0, len(triples), batch_size):
            batch = triples[i:i + batch_size]
            result = self.coherence_checker(triples=batch, text=context, task_instructions=task_instructions)

            for triple, score, explanation in result.coherence_scores:
                if score >= threshold:
                    coherent_triples.append(triple)
                elif self.logging:
                    print(
                        f"{self.__class__.__name__}: INFO :: Filtered out triple {triple} (score: {score}/5): {explanation}")

        if self.logging:
            filtered_count = len(triples) - len(coherent_triples)
            if filtered_count > 0:
                print(f"{self.__class__.__name__}: INFO :: Filtered out {filtered_count} low-coherence triples")

        return coherent_triples

    def _extract_entities_from_chunks(
            self,
            chunks: List[str],
            examples_for_entity_extraction: str,
            extractor_name: str = None,
            use_llm_merge: bool = None,
            task_instructions: str = None
    ) -> tuple:
        """
        Extract entities from multiple text chunks and merge results.
        Generic method that works for all extractor subclasses.

        Args:
            chunks: List of text chunks.
            examples_for_entity_extraction: Few-shot examples.
            extractor_name: Name of the extractor (for logging). If None, uses class name.
            use_llm_merge: Whether to use LLM-based merging for better quality. If None, uses
                self.use_incremental_merging (default: None).
            task_instructions: Further instructions in accordance with the user's query.

        Returns:
            Tuple of (merged_entities, chunk_summaries) where chunk_summaries can be used
            for subsequent operations.
        """
        if not hasattr(self, 'entity_extractor'):
            raise AttributeError(f"{self.__class__.__name__} must define 'entity_extractor'")

        extractor_name = extractor_name or self.__class__.__name__
        all_entity_lists = []
        chunk_summaries = []

        # Use class-level setting if not explicitly specified
        if use_llm_merge is None:
            use_llm_merge = self.use_incremental_merging

        for i, chunk in enumerate(chunks):
            if self.logging:
                print(f"{extractor_name}: INFO :: Extracting entities from chunk {i + 1}/{len(chunks)}")

            try:
                result = self.entity_extractor(
                    text=chunk,
                    few_shot_examples=examples_for_entity_extraction,
                    task_instructions=task_instructions
                )
                chunk_entities = result.entities if hasattr(result, 'entities') and result.entities else []
            except Exception as e:
                if self.logging:
                    print(f"{extractor_name}: WARNING :: Failed to extract entities from chunk {i + 1}: {e}")
                chunk_entities = []

            all_entity_lists.append(chunk_entities)

            # Generate summary for this chunk (for later use in merging/clustering)
            if use_llm_merge:
                summary = self.summarize_chunk(chunk)
                chunk_summaries.append(summary)

            if self.logging:
                print(f"{extractor_name}: INFO :: Found {len(chunk_entities)} entities in chunk {i + 1}")

        # Merge entities from all chunks
        merged_entities = self._merge_entity_lists(all_entity_lists, chunk_summaries, use_llm_merge=use_llm_merge)
        if not use_llm_merge:
            chunk_summaries = []  # Return empty if not generated

        if self.logging:
            print(f"{extractor_name}: INFO :: Total merged entities: {len(merged_entities)}")

        return merged_entities, chunk_summaries

    def _extract_triples_from_chunks(
            self,
            chunks: List[str],
            entities: List[str],
            examples_for_triples_extraction: str,
            extractor_name: str = None,
            chunk_summaries: List[str] = None,
            use_llm_merge: bool = None,
            task_instructions: str = None
    ) -> List[tuple]:
        """
        Extract triples from multiple text chunks and merge results.
        Generic method that works for all extractor subclasses.

        Args:
            chunks: List of text chunks.
            entities: List of entities to use for extraction.
            examples_for_triples_extraction: Few-shot examples.
            extractor_name: Name of the extractor (for logging). If None, uses class name.
            chunk_summaries: Optional pre-computed chunk summaries for merging context.
            use_llm_merge: Whether to use LLM-based merging for better quality. If None, uses
                self.use_incremental_merging (default: None).
            task_instructions: Further instructions in accordance with the user's query.

        Returns:
            Merged list of triples from all chunks.
        """
        if not hasattr(self, 'triples_extractor'):
            raise AttributeError(f"{self.__class__.__name__} must define 'triples_extractor'")

        extractor_name = extractor_name or self.__class__.__name__
        all_triple_lists = []

        # Use class-level setting if not explicitly specified
        if use_llm_merge is None:
            use_llm_merge = self.use_incremental_merging

        # Generate summaries if not provided and LLM merge is enabled
        if use_llm_merge and chunk_summaries is None:
            chunk_summaries = self.summarize_chunks(chunks)

        for i, chunk in enumerate(chunks):
            if self.logging:
                print(f"{extractor_name}: INFO :: Extracting triples from chunk {i + 1}/{len(chunks)}")

            try:
                result = self.triples_extractor(
                    text=chunk,
                    entities=entities,
                    few_shot_examples=examples_for_triples_extraction,
                    task_instructions=task_instructions
                )
                chunk_triples = result.triples if hasattr(result, 'triples') and result.triples else []
            except Exception as e:
                if self.logging:
                    print(f"{extractor_name}: WARNING :: Failed to extract triples from chunk {i + 1}: {e}")
                chunk_triples = []

            all_triple_lists.append(chunk_triples)

            if self.logging:
                print(f"{extractor_name}: INFO :: Found {len(chunk_triples)} triples in chunk {i + 1}")

        # Merge triples from all chunks
        merged_triples = self._merge_triple_lists(all_triple_lists, chunk_summaries, use_llm_merge=use_llm_merge)

        if self.logging:
            print(f"{extractor_name}: INFO :: Total merged triples: {len(merged_triples)}")

        return merged_triples

    def _extract_types_from_chunks(
            self,
            chunks: List[str],
            entities: List[str],
            entity_types: List[str],
            generate_types: bool,
            examples_for_type_assertion: str,
            examples_for_type_generation: str,
            extractor_name: str = None,
            chunk_summaries: List[str] = None,
            use_llm_merge: bool = None,
            task_instructions_assertion: str = None,
            task_instructions_generation: str = None
    ) -> List[tuple]:
        """
        Extract type assertions from multiple text chunks and merge results.
        Generic method that works for all extractor subclasses.

        Args:
            chunks: List of text chunks.
            entities: List of entities.
            entity_types: List of predefined types (if not generating).
            generate_types: Whether to generate types.
            examples_for_type_assertion: Few-shot examples for assertion.
            examples_for_type_generation: Few-shot examples for generation.
            extractor_name: Name of the extractor (for logging). If None, uses class name.
            chunk_summaries: Optional pre-computed chunk summaries for merging context.
            use_llm_merge: Whether to use LLM-based merging for better quality. If None, uses
                self.use_incremental_merging (default: None).
            task_instructions_assertion: Further type assertion instructions in accordance with the user's query.
            task_instructions_generation: Further type generation instructions in accordance with the user's query.

        Returns:
            Merged list of type assertions from all chunks.
        """
        if not hasattr(self, 'type_asserter') or not hasattr(self, 'type_generator'):
            raise AttributeError(f"{self.__class__.__name__} must define 'type_asserter' and 'type_generator'")

        extractor_name = extractor_name or self.__class__.__name__
        all_assertion_lists = []

        # Use class-level setting if not explicitly specified
        if use_llm_merge is None:
            use_llm_merge = self.use_incremental_merging

        # Generate summaries if not provided and LLM merge is enabled
        if use_llm_merge and chunk_summaries is None:
            chunk_summaries = self.summarize_chunks(chunks)

        for i, chunk in enumerate(chunks):
            if self.logging:
                print(f"{extractor_name}: INFO :: Extracting types from chunk {i + 1}/{len(chunks)}")

            try:
                if entity_types is not None and not generate_types:
                    result = self.type_asserter(
                        text=chunk,
                        entities=entities,
                        entity_types=entity_types,
                        task_instructions = task_instructions_assertion,
                        few_shot_examples=examples_for_type_assertion
                    )
                    chunk_assertions = result.pairs if hasattr(result, 'pairs') and result.pairs else []
                else:  # generate_types
                    result = self.type_generator(
                        text=chunk,
                        entities=entities,
                        task_instructions = task_instructions_generation,
                        few_shot_examples=examples_for_type_generation
                    )
                    chunk_assertions = result.pairs if hasattr(result, 'pairs') and result.pairs else []
            except Exception as e:
                if self.logging:
                    print(f"{extractor_name}: WARNING :: Failed to extract types from chunk {i + 1}: {e}")
                chunk_assertions = []

            all_assertion_lists.append(chunk_assertions)

            if self.logging:
                print(f"{extractor_name}: INFO :: Found {len(chunk_assertions)} type assertions in chunk {i + 1}")

        # Merge type assertions from all chunks
        merged_assertions = self._merge_type_assertions(all_assertion_lists, chunk_summaries, use_llm_merge=use_llm_merge)

        if self.logging:
            print(f"{extractor_name}: INFO :: Total merged type assertions: {len(merged_assertions)}")

        return merged_assertions

    def _extract_literals_from_chunks(
            self,
            chunks: List[str],
            examples_for_literal_extraction: str,
            extractor_name: str = None,
            task_instructions: str = None
    ) -> List[str]:
        """
        Extract literals from multiple text chunks and merge results.
        Generic method that works for all extractor subclasses.

        Args:
            chunks: List of text chunks.
            examples_for_literal_extraction: Few-shot examples.
            extractor_name: Name of the extractor (for logging). If None, uses class name.
            task_instructions: Further instructions in accordance with the user's query.

        Returns:
            Merged list of literals from all chunks.
        """
        if not hasattr(self, 'literal_extractor'):
            raise AttributeError(f"{self.__class__.__name__} must define 'literal_extractor'")

        extractor_name = extractor_name or self.__class__.__name__
        all_literal_lists = []

        for i, chunk in enumerate(chunks):
            if self.logging:
                print(f"{extractor_name}: INFO :: Extracting literals from chunk {i + 1}/{len(chunks)}")

            try:
                result = self.literal_extractor(
                    text=chunk,
                    task_instructions=task_instructions,
                    few_shot_examples=examples_for_literal_extraction
                )
                chunk_literals = result.l_values if hasattr(result, 'l_values') and result.l_values else []
            except Exception as e:
                if self.logging:
                    print(f"{extractor_name}: WARNING :: Failed to extract literals from chunk {i + 1}: {e}")
                chunk_literals = []

            all_literal_lists.append(chunk_literals)

            if self.logging:
                print(f"{extractor_name}: INFO :: Found {len(chunk_literals)} literals in chunk {i + 1}")

        # Merge literals from all chunks
        merged_literals = self._merge_literal_lists(all_literal_lists)

        if self.logging:
            print(f"{extractor_name}: INFO :: Total merged literals: {len(merged_literals)}")

        return merged_literals

    def _extract_spl_triples_from_chunks(
            self,
            chunks: List[str],
            entities: List[str],
            literals: List[str],
            examples_for_spl_triples_extraction: str,
            extractor_name: str = None,
            task_instructions: str = None
    ) -> List[tuple]:
        """
        Extract SPL triples from multiple text chunks and merge results.
        Generic method that works for all extractor subclasses.

        Args:
            chunks: List of text chunks.
            entities: List of entities.
            literals: List of numeric literals.
            examples_for_spl_triples_extraction: Few-shot examples.
            extractor_name: Name of the extractor (for logging). If None, uses class name.
            task_instructions: Further instructions in accordance with the user's query.

        Returns:
            Merged list of SPL triples from all chunks.
        """
        if not hasattr(self, 'spl_triples_extractor'):
            raise AttributeError(f"{self.__class__.__name__} must define 'spl_triples_extractor'")

        extractor_name = extractor_name or self.__class__.__name__
        all_triple_lists = []

        for i, chunk in enumerate(chunks):
            if self.logging:
                print(f"{extractor_name}: INFO :: Extracting SPL triples from chunk {i + 1}/{len(chunks)}")

            try:
                result = self.spl_triples_extractor(
                    text=chunk,
                    entities=entities,
                    numeric_literals=literals,
                    task_instructions= task_instructions,
                    few_shot_examples=examples_for_spl_triples_extraction
                )
                chunk_triples = result.triples if hasattr(result, 'triples') and result.triples else []
            except Exception as e:
                if self.logging:
                    print(f"{extractor_name}: WARNING :: Failed to extract SPL triples from chunk {i + 1}: {e}")
                chunk_triples = []

            all_triple_lists.append(chunk_triples)

            if self.logging:
                print(f"{extractor_name}: INFO :: Found {len(chunk_triples)} SPL triples in chunk {i + 1}")

        # Merge SPL triples from all chunks
        merged_triples = self._merge_triple_lists(all_triple_lists)

        if self.logging:
            print(f"{extractor_name}: INFO :: Total merged SPL triples: {len(merged_triples)}")

        return merged_triples

    def get_corresponding_literal(self, literal_value: str) -> OWLLiteral:
        """
        Convert a string literal value to an OWLLiteral with the appropriate datatype."""

        value = literal_value
        literal = None

        # Try DateTime first (most specific date type)
        try:
            parsed_datetime = datetime.fromisoformat(str(value))
            literal = OWLLiteral(parsed_datetime)  # OWLLiteral will auto-detect datetime type
        except (ValueError, TypeError, AttributeError):
            pass

        # Try Date (without time)
        if literal is None:
            try:
                # Check if it looks like a date format (YYYY-MM-DD)
                parsed_date = datetime.strptime(str(value), "%Y-%m-%d").date()
                literal = OWLLiteral(parsed_date)  # OWLLiteral will auto-detect date type
            except (ValueError, TypeError, AttributeError):
                pass

        # Try Boolean
        if literal is None:
            try:
                str_value = str(value).lower().strip()
                if str_value in ('true', 'false'):
                    bool_value = str_value == 'true'
                    literal = OWLLiteral(bool_value)  # OWLLiteral will auto-detect bool type
            except (ValueError, TypeError, AttributeError):
                pass

        # Try Integer
        if literal is None:
            try:
                # Check if it's an integer (no decimal point or is x.0)
                float_value = float(value)
                if float_value.is_integer():
                    int_value = int(float_value)
                    literal = OWLLiteral(int_value)  # OWLLiteral will auto-detect int type
                else:
                    # It's a float with decimal places
                    literal = OWLLiteral(float_value)  # OWLLiteral will auto-detect float type
            except (ValueError, TypeError, AttributeError):
                pass

        # Default to String
        if literal is None:
            literal = OWLLiteral(str(value))  # OWLLiteral will auto-detect string type

        return literal

    @abstractmethod
    def generate_ontology(self, text: Union[str, Path], ontology_type: str = "open", **kwargs) -> Ontology:
        """
        Generate an ontology from the given text or file.
        Must be implemented by subclasses.

        Args:
            text: Input text or file path to extract ontology from.
                Supports files: .txt, .pdf, .docx, .doc, .rtf, .html, .htm
            ontology_type (str): The ontology type to use. Options are:
                    1. 'domain': Focused on a specific domain (e.g., healthcare, finance),
                    2. 'cross-domain': Spans multiple related domains,
                    3. 'enterprise': Tailored for organizational knowledge representation,
                    4. 'open': General-purpose ontology covering a wide range of topics, similar to Wikidata.
            **kwargs: Additional arguments specific to the extractor type.

        Returns:
            Generated Ontology object.
        """
        pass
