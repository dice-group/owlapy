from typing import List, Union, Optional, Dict
import os
import dspy
from abc import ABC, abstractmethod
from pathlib import Path

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.ontogen.few_shot_examples import EXAMPLES_FOR_ENTITY_EXTRACTION, EXAMPLES_FOR_TRIPLES_EXTRACTION, \
    EXAMPLES_FOR_TYPE_ASSERTION, EXAMPLES_FOR_TYPE_GENERATION, EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION, \
    EXAMPLES_FOR_LITERAL_EXTRACTION
from owlapy.owl_axiom import OWLObjectPropertyAssertionAxiom, OWLClassAssertionAxiom, OWLDataPropertyAssertionAxiom, \
    OWLSubClassOfAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral, StringOWLDatatype
from owlapy.owl_ontology import Ontology
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty
from owlapy.agen_kg.signatures import Entity, Triple, TypeAssertion, TypeGeneration, Literal, SPLTriples, Domain, DomainSpecificFewShotGenerator, EntityClustering, CoherenceChecker, TypeClustering, RelationClustering
from owlapy.agen_kg.helper import extract_hierarchy_from_dbpedia
from owlapy.agen_kg.text_loader import UniversalTextLoader, TextChunker
from owlapy.agen_kg.domain_examples_cache import DomainExamplesCache, EXAMPLE_TYPE_MAPPING


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

    def __init__(self, enable_logging=False):
        """
        Initialize the graph extractor.

        Args:
            enable_logging: Whether to enable logging.
        """
        super().__init__()
        self.logging = enable_logging
        self.entity_clusterer = dspy.Predict(EntityClustering)
        self.coherence_checker = dspy.Predict(CoherenceChecker)
        self.type_clusterer = dspy.Predict(TypeClustering)
        self.relation_clusterer = dspy.Predict(RelationClustering)
        self.text_loader = UniversalTextLoader(enable_logging=enable_logging)
        # Default text chunker - can be configured via configure_chunking()
        self.text_chunker = TextChunker(
            chunk_size=3000,  # ~750 tokens
            overlap=200,
            strategy="sentence",
            enable_logging=enable_logging
        )
        # Threshold for automatic chunking (in characters)
        self.auto_chunk_threshold = 4000  # ~1000 tokens

    @staticmethod
    def snake_case(text):
        """Convert text to snake_case format."""
        return text.strip().lower().replace(" ", "_")

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
        return self.text_loader.load(source, file_type)
    
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
        auto_chunk_threshold: int = None
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

        Example:
            # Configure for a model with smaller context window
            extractor.configure_chunking(chunk_size=2000, overlap=150, strategy="sentence")

            # Configure for larger context window (e.g., GPT-4-turbo)
            extractor.configure_chunking(chunk_size=8000, overlap=500)
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

        if self.logging:
            print(f"{self.__class__.__name__}: INFO :: Chunking configured - "
                  f"chunk_size={self.text_chunker.chunk_size}, "
                  f"overlap={self.text_chunker.overlap}, "
                  f"strategy={self.text_chunker.strategy}, "
                  f"auto_threshold={self.auto_chunk_threshold}")

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

    def _merge_entity_lists(self, entity_lists: List[List[str]]) -> List[str]:
        """
        Merge entity lists from multiple chunks, removing duplicates.

        Args:
            entity_lists: List of entity lists from each chunk.

        Returns:
            Merged and deduplicated list of entities.
        """
        all_entities = []
        seen = set()
        for entities in entity_lists:
            for entity in entities:
                entity_lower = entity.lower()
                if entity_lower not in seen:
                    seen.add(entity_lower)
                    all_entities.append(entity)
        return all_entities

    def _merge_triple_lists(self, triple_lists: List[List[tuple]]) -> List[tuple]:
        """
        Merge triple lists from multiple chunks, removing duplicates.

        Args:
            triple_lists: List of triple lists from each chunk.

        Returns:
            Merged and deduplicated list of triples.
        """
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

    def _merge_type_assertions(self, assertion_lists: List[List[tuple]]) -> List[tuple]:
        """
        Merge type assertion lists from multiple chunks.

        For duplicate entity-type assignments, keep consistent types.

        Args:
            assertion_lists: List of type assertion lists from each chunk.

        Returns:
            Merged type assertions.
        """
        entity_types = {}  # entity -> type (keep first seen)
        for assertions in assertion_lists:
            for entity, entity_type in assertions:
                entity_lower = entity.lower()
                if entity_lower not in entity_types:
                    entity_types[entity_lower] = (entity, entity_type)
        return list(entity_types.values())

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

    def cluster_entities(self, entities: List[str], text: str) -> dict:
        """
        Cluster entities to identify and merge duplicates.

        Args:
            entities: List of extracted entities.
            text: Original text context.

        Returns:
            Dictionary mapping original entity names to their canonical names.
        """
        if not entities:
            return {}

        result = self.entity_clusterer(entities=entities, text=text)
        entity_mapping = {}

        for cluster, canonical_name in result.clusters:
            for entity in cluster:
                entity_mapping[entity] = canonical_name

        # Add entities that weren't clustered
        for entity in entities:
            if entity not in entity_mapping:
                entity_mapping[entity] = entity

        if self.logging:
            merged_count = len(entities) - len(set(entity_mapping.values()))
            if merged_count > 0:
                print(f"{self.__class__.__name__}: INFO :: Merged {merged_count} duplicate entities")

        return entity_mapping

    def cluster_types(self, types: List[str], text: str) -> dict:
        """
        Cluster entity types to identify and merge duplicates.

        Args:
            types: List of extracted entity types.
            text: Original text context.

        Returns:
            Dictionary mapping original type names to their canonical names.
        """
        if not types:
            return {}

        result = self.type_clusterer(types=types, text=text)
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

    def cluster_relations(self, relations: List[str], text: str) -> dict:
        """
        Cluster relations to identify and merge duplicates.

        Args:
            relations: List of extracted relations.
            text: Original text context.

        Returns:
            Dictionary mapping original relation names to their canonical names.
        """
        if not relations:
            return {}

        result = self.relation_clusterer(relations=relations, text=text)
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

    def check_coherence(self, triples: List[tuple], text: str, batch_size: int = 50,
                       threshold: int = 3) -> List[tuple]:
        """
        Check coherence of extracted triples and filter out low-quality ones.

        Args:
            triples: List of extracted triples.
            text: Original text context.
            batch_size: Number of triples to check per batch.
            threshold: Minimum coherence score (1-5) to keep a triple.

        Returns:
            List of coherent triples that passed the threshold.
        """
        if not triples:
            return []

        coherent_triples = []

        # Process triples in batches
        for i in range(0, len(triples), batch_size):
            batch = triples[i:i+batch_size]
            result = self.coherence_checker(triples=batch, text=text)

            for triple, score, explanation in result.coherence_scores:
                if score >= threshold:
                    coherent_triples.append(triple)
                elif self.logging:
                    print(f"{self.__class__.__name__}: INFO :: Filtered out triple {triple} (score: {score}/5): {explanation}")

        if self.logging:
            filtered_count = len(triples) - len(coherent_triples)
            if filtered_count > 0:
                print(f"{self.__class__.__name__}: INFO :: Filtered out {filtered_count} low-coherence triples")

        return coherent_triples

    def _extract_entities_from_chunks(
        self,
        chunks: List[str],
        examples_for_entity_extraction: str,
        extractor_name: str = None
    ) -> List[str]:
        """
        Extract entities from multiple text chunks and merge results.
        Generic method that works for all extractor subclasses.

        Args:
            chunks: List of text chunks.
            examples_for_entity_extraction: Few-shot examples.
            extractor_name: Name of the extractor (for logging). If None, uses class name.

        Returns:
            Merged list of entities from all chunks.
        """
        if not hasattr(self, 'entity_extractor'):
            raise AttributeError(f"{self.__class__.__name__} must define 'entity_extractor'")

        extractor_name = extractor_name or self.__class__.__name__
        all_entity_lists = []

        for i, chunk in enumerate(chunks):
            if self.logging:
                print(f"{extractor_name}: INFO :: Extracting entities from chunk {i+1}/{len(chunks)}")

            chunk_entities = self.entity_extractor(
                text=chunk,
                few_shot_examples=examples_for_entity_extraction
            ).entities
            all_entity_lists.append(chunk_entities)

            if self.logging:
                print(f"{extractor_name}: INFO :: Found {len(chunk_entities)} entities in chunk {i+1}")

        # Merge entities from all chunks
        merged_entities = self._merge_entity_lists(all_entity_lists)

        if self.logging:
            print(f"{extractor_name}: INFO :: Total merged entities: {len(merged_entities)}")

        return merged_entities

    def _extract_triples_from_chunks(
        self,
        chunks: List[str],
        entities: List[str],
        examples_for_triples_extraction: str,
        extractor_name: str = None
    ) -> List[tuple]:
        """
        Extract triples from multiple text chunks and merge results.
        Generic method that works for all extractor subclasses.

        Args:
            chunks: List of text chunks.
            entities: List of entities to use for extraction.
            examples_for_triples_extraction: Few-shot examples.
            extractor_name: Name of the extractor (for logging). If None, uses class name.

        Returns:
            Merged list of triples from all chunks.
        """
        if not hasattr(self, 'triples_extractor'):
            raise AttributeError(f"{self.__class__.__name__} must define 'triples_extractor'")

        extractor_name = extractor_name or self.__class__.__name__
        all_triple_lists = []

        for i, chunk in enumerate(chunks):
            if self.logging:
                print(f"{extractor_name}: INFO :: Extracting triples from chunk {i+1}/{len(chunks)}")

            chunk_triples = self.triples_extractor(
                text=chunk,
                entities=entities,
                few_shot_examples=examples_for_triples_extraction
            ).triples
            all_triple_lists.append(chunk_triples)

            if self.logging:
                print(f"{extractor_name}: INFO :: Found {len(chunk_triples)} triples in chunk {i+1}")

        # Merge triples from all chunks
        merged_triples = self._merge_triple_lists(all_triple_lists)

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
        extractor_name: str = None
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

        Returns:
            Merged list of type assertions from all chunks.
        """
        if not hasattr(self, 'type_asserter') or not hasattr(self, 'type_generator'):
            raise AttributeError(f"{self.__class__.__name__} must define 'type_asserter' and 'type_generator'")

        extractor_name = extractor_name or self.__class__.__name__
        all_assertion_lists = []

        for i, chunk in enumerate(chunks):
            if self.logging:
                print(f"{extractor_name}: INFO :: Extracting types from chunk {i+1}/{len(chunks)}")

            if entity_types is not None and not generate_types:
                chunk_assertions = self.type_asserter(
                    text=chunk,
                    entities=entities,
                    entity_types=entity_types,
                    few_shot_examples=examples_for_type_assertion
                ).pairs
            else:  # generate_types
                chunk_assertions = self.type_generator(
                    text=chunk,
                    entities=entities,
                    few_shot_examples=examples_for_type_generation
                ).pairs

            all_assertion_lists.append(chunk_assertions)

            if self.logging:
                print(f"{extractor_name}: INFO :: Found {len(chunk_assertions)} type assertions in chunk {i+1}")

        # Merge type assertions from all chunks
        merged_assertions = self._merge_type_assertions(all_assertion_lists)

        if self.logging:
            print(f"{extractor_name}: INFO :: Total merged type assertions: {len(merged_assertions)}")

        return merged_assertions

    def _extract_literals_from_chunks(
        self,
        chunks: List[str],
        examples_for_literal_extraction: str,
        extractor_name: str = None
    ) -> List[str]:
        """
        Extract literals from multiple text chunks and merge results.
        Generic method that works for all extractor subclasses.

        Args:
            chunks: List of text chunks.
            examples_for_literal_extraction: Few-shot examples.
            extractor_name: Name of the extractor (for logging). If None, uses class name.

        Returns:
            Merged list of literals from all chunks.
        """
        if not hasattr(self, 'literal_extractor'):
            raise AttributeError(f"{self.__class__.__name__} must define 'literal_extractor'")

        extractor_name = extractor_name or self.__class__.__name__
        all_literal_lists = []

        for i, chunk in enumerate(chunks):
            if self.logging:
                print(f"{extractor_name}: INFO :: Extracting literals from chunk {i+1}/{len(chunks)}")

            chunk_literals = self.literal_extractor(
                text=chunk,
                few_shot_examples=examples_for_literal_extraction
            ).l_values
            all_literal_lists.append(chunk_literals)

            if self.logging:
                print(f"{extractor_name}: INFO :: Found {len(chunk_literals)} literals in chunk {i+1}")

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
        extractor_name: str = None
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

        Returns:
            Merged list of SPL triples from all chunks.
        """
        if not hasattr(self, 'spl_triples_extractor'):
            raise AttributeError(f"{self.__class__.__name__} must define 'spl_triples_extractor'")

        extractor_name = extractor_name or self.__class__.__name__
        all_triple_lists = []

        for i, chunk in enumerate(chunks):
            if self.logging:
                print(f"{extractor_name}: INFO :: Extracting SPL triples from chunk {i+1}/{len(chunks)}")

            chunk_triples = self.spl_triples_extractor(
                text=chunk,
                entities=entities,
                numeric_literals=literals,
                few_shot_examples=examples_for_spl_triples_extraction
            ).triples
            all_triple_lists.append(chunk_triples)

            if self.logging:
                print(f"{extractor_name}: INFO :: Found {len(chunk_triples)} SPL triples in chunk {i+1}")

        # Merge SPL triples from all chunks
        merged_triples = self._merge_triple_lists(all_triple_lists)

        if self.logging:
            print(f"{extractor_name}: INFO :: Total merged SPL triples: {len(merged_triples)}")

        return merged_triples

    @abstractmethod
    def generate_ontology(self, text: Union[str, Path], ontology_type: str="open", **kwargs) -> Ontology:
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

    @abstractmethod
    def forward(self, text: Union[str, Path], **kwargs) -> Ontology:
        """
        Forward pass for the extractor module.
        Must be implemented by subclasses.

        Args:
            text: Input text or file path to extract ontology from.
                Supports files: .txt, .pdf, .docx, .doc, .rtf, .html, .htm
            **kwargs: Additional arguments specific to the extractor type.

        Returns:
            Generated Ontology object.
        """
        pass


class AGenKG:
    def __init__(self, model="gpt-4o", api_key="<YOUR_GITHUB_PAT>",
                 api_base="https://models.github.ai/inference",
                 temperature=0.1, seed=42, cache=False,
                 enable_logging=False, max_tokens=4000):
        """
                A module to extract an RDF graph from a given text input.
                Supports automatic chunking for large texts that exceed the LLM's context window.

                Args:
                    model: Model name for the LLM.
                    api_key: API key.
                    api_base: API base URL.
                    temperature: The sampling temperature to use when generating responses.
                    seed: Seed for the LLM.
                    cache: Whether to cache the model responses for reuse to improve performance and reduce costs.
                    enable_logging: Whether to enable logging.
                    max_tokens: Maximum tokens for LLM response.
                """
        super().__init__()
        lm = dspy.LM(model=f"openai/{model}", api_key=api_key,
                     api_base=api_base,
                     temperature=temperature, seed=seed, cache=cache, max_tokens=max_tokens)
        dspy.configure(lm=lm)
        self.logging = enable_logging
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.temperature = temperature
        self.seed = seed
        self.cache = cache
        self.enable_logging = enable_logging
        self.max_tokens = max_tokens

        self.open_graph_extractor = OpenGraphExtractor(self.logging)
        self.domain_graph_extractor = DomainGraphExtractor(self.logging)
        self.cross_domain_graph_extractor = CrossDomainGraphExtractor(self.logging)
        self.enterprise_graph_extractor = EnterpriseGraphExtractor(self.logging)

    def configure_chunking(
        self,
        chunk_size: int = None,
        overlap: int = None,
        strategy: str = None,
        auto_chunk_threshold: int = None
    ):
        """
        Configure text chunking settings for all extractors.

        This method allows fine-tuning of how large texts are split into
        manageable pieces for LLM processing.

        Args:
            chunk_size: Maximum characters per chunk (default: 3000, ~750 tokens).
            overlap: Characters to overlap between chunks (default: 200).
            strategy: Chunking strategy - "sentence", "paragraph", or "fixed".
            auto_chunk_threshold: Character threshold for automatic chunking (default: 4000).

        Example:
            # Configure for a model with smaller context window
            agenkg.configure_chunking(chunk_size=2000, overlap=150, strategy="sentence")
        """
        for extractor in [self.open_graph_extractor, self.domain_graph_extractor,
                         self.cross_domain_graph_extractor, self.enterprise_graph_extractor]:
            extractor.configure_chunking(
                chunk_size=chunk_size,
                overlap=overlap,
                strategy=strategy,
                auto_chunk_threshold=auto_chunk_threshold
            )

    def configure_chunking_for_model(
        self,
        max_context_tokens: int,
        prompt_overhead_tokens: int = 1500
    ):
        """
        Automatically configure chunking based on model specifications for all extractors.

        Args:
            max_context_tokens: Maximum context window of your model (e.g., 4096 for GPT-3.5).
            prompt_overhead_tokens: Estimated tokens used by prompts/few-shot examples.

        Example:
            # For GPT-3.5-turbo (4K context)
            agenkg.configure_chunking_for_model(4096, 1000)

            # For GPT-4 (8K context)
            agenkg.configure_chunking_for_model(8192, 1500)
        """
        for extractor in [self.open_graph_extractor, self.domain_graph_extractor,
                         self.cross_domain_graph_extractor, self.enterprise_graph_extractor]:
            extractor.configure_chunking_for_model(
                max_context_tokens=max_context_tokens,
                prompt_overhead_tokens=prompt_overhead_tokens
            )

    def generate_ontology(self, text, ontology_type, **kwargs):

        assert ontology_type in ["domain", "cross-domain", "enterprise", "open"], \
            "ontology_type must be one of 'domain', 'cross-domain', 'enterprise', or 'open'"

        if ontology_type == "open":
            return self.open_graph_extractor(text=text, ontology_type=ontology_type, **kwargs)
        elif ontology_type == "domain":
            return self.domain_graph_extractor(text=text, **kwargs)
        elif ontology_type == "cross-domain":
            return self.cross_domain_graph_extractor(text=text, **kwargs)
        elif ontology_type == "enterprise":
            return self.enterprise_graph_extractor(text=text, **kwargs)
        return None


class OpenGraphExtractor(GraphExtractor):
    def __init__(self, enable_logging=False):
        """
        A module to extract an RDF graph from a given text input.
        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            enable_logging: Whether to enable logging.
        """
        super().__init__(enable_logging)
        self.entity_extractor = dspy.Predict(Entity)
        self.triples_extractor = dspy.Predict(Triple)
        self.type_asserter = dspy.Predict(TypeAssertion)
        self.type_generator = dspy.Predict(TypeGeneration)
        self.literal_extractor = dspy.Predict(Literal)
        self.spl_triples_extractor = dspy.Predict(SPLTriples)

    def generate_ontology(self, text: Union[str, Path], ontology_namespace = "http://example.com/ontogen#",
                entity_types: List[str]=None,
                generate_types=False,
                extract_spl_triples=False,
                create_class_hierarchy=False,
                entity_clustering=True,
                use_chunking: bool = None,
                examples_for_entity_extraction=EXAMPLES_FOR_ENTITY_EXTRACTION,
                examples_for_triples_extraction=EXAMPLES_FOR_TRIPLES_EXTRACTION,
                examples_for_type_assertion=EXAMPLES_FOR_TYPE_ASSERTION,
                examples_for_type_generation=EXAMPLES_FOR_TYPE_GENERATION,
                examples_for_literal_extraction=EXAMPLES_FOR_LITERAL_EXTRACTION,
                examples_for_spl_triples_extraction=EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION,
                save_path="generated_ontology.owl") -> Ontology:
        """
        Generate an ontology from the given text or file.

        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            text: Input text or file path.
            ontology_namespace: Namespace for the ontology.
            entity_types: List of entity types to assign.
            generate_types: Whether to generate types automatically.
            extract_spl_triples: Whether to extract subject-property-literal triples.
            create_class_hierarchy: Whether to create class hierarchy from DBpedia.
            entity_clustering: Whether to perform entity clustering.
            use_chunking: Whether to use text chunking for large documents.
                - None (default): Auto-detect based on text size (uses auto_chunk_threshold).
                - True: Force chunking even for smaller texts.
                - False: Disable chunking (may fail for very large texts).
            examples_for_*: Few-shot examples for various extraction tasks.
            save_path: Path to save the ontology.

        Returns:
            Generated Ontology object.
        """
        # Load text from file if necessary
        if isinstance(text, (str, Path)):
            # Check if it's a file path
            source_path = Path(text) if not isinstance(text, Path) else text
            if source_path.is_file():
                text = self.load_text(text)
            # else: treat as raw text string
        
        # Determine whether to use chunking
        if use_chunking is None:
            use_chunking = self.should_chunk_text(text)

        if use_chunking:
            chunks = self.chunk_text(text)
            if self.logging:
                chunk_info = self.get_chunking_info(text)
                print(f"OpenGraphExtractor: INFO :: Text will be processed in {chunk_info['num_chunks']} chunks")
                print(f"OpenGraphExtractor: INFO :: Total chars: {chunk_info['total_chars']}, "
                      f"Est. tokens: {chunk_info['estimated_tokens']}")
        else:
            chunks = [text]

        if self.logging:
            print("GraphExtractor: INFO  :: In the generated triples, you may see entities or literals that were not"
                  "part of the extracted entities or literals. They are filtered before added to the ontology.")

        # Step 1: Extract entities (from chunks if needed)
        if use_chunking and len(chunks) > 1:
            entities = self._extract_entities_from_chunks(chunks, examples_for_entity_extraction)
        else:
            entities = self.entity_extractor(text=text, few_shot_examples=examples_for_entity_extraction).entities

        if self.logging:
            print(f"GraphExtractor: INFO  :: Generated the following entities: {entities}")

        # Step 2: Cluster entities to identify and merge duplicates
        # For chunked processing, use the full text for better clustering context
        clustering_context = text[:self.auto_chunk_threshold] if len(text) > self.auto_chunk_threshold else text

        if entity_clustering:
            entity_mapping = self.cluster_entities(entities, clustering_context)
            canonical_entities = list(set(entity_mapping.values()))
        else:
            canonical_entities = entities
        if self.logging and len(entities) != len(canonical_entities):
            print(f"GraphExtractor: INFO  :: After clustering: {canonical_entities}")

        # Step 3: Extract triples using canonical entities (from chunks if needed)
        if use_chunking and len(chunks) > 1:
            triples = self._extract_triples_from_chunks(chunks, canonical_entities, examples_for_triples_extraction)
        else:
            triples = self.triples_extractor(text=text, entities=canonical_entities, few_shot_examples=examples_for_triples_extraction).triples

        if self.logging:
            print(f"GraphExtractor: INFO  :: Generated the following triples: {triples}")

        # Step 3.5: Cluster relations (object properties) and update triples programmatically BEFORE coherence check
        relations = list(set([triple[1] for triple in triples]))
        relation_mapping = self.cluster_relations(relations, clustering_context)
        # Update triples with canonical relations
        updated_triples = [(triple[0], relation_mapping.get(triple[1], triple[1]), triple[2]) for triple in triples]
        if self.logging and len(relations) != len(set(relation_mapping.values())):
            print(f"GraphExtractor: INFO  :: After relation clustering: {list(set(relation_mapping.values()))}")

        # Step 4: Check coherence of the relation-normalized triples
        # For chunked text, use a summary for coherence checking
        coherent_triples = self.check_coherence(updated_triples, clustering_context)
        if self.logging:
            print(f"GraphExtractor: INFO  :: After coherence check, kept {len(coherent_triples)} triples")

        # Step 5: Create an ontology and load it with extracted triples
        onto = Ontology(ontology_iri=IRI.create("http://example.com/ontogen") ,load=False)
        for triple in coherent_triples:
            subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
            prop = OWLObjectProperty(ontology_namespace + self.snake_case(triple[1]))
            object = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[2]))
            if triple[0] in canonical_entities and triple[2] in canonical_entities:
                ax = OWLObjectPropertyAssertionAxiom(subject, prop, object)
                onto.add_axiom(ax)

        # If user wants to set types, do so depending on the arguments
        if entity_types is not None or generate_types:
            type_assertions = None

            # Extract types (from chunks if needed)
            if use_chunking and len(chunks) > 1:
                type_assertions = self._extract_types_from_chunks(
                    chunks, canonical_entities, entity_types, generate_types,
                    examples_for_type_assertion, examples_for_type_generation
                )
            else:
                # The user has specified a preset list of types
                if entity_types is not None and not generate_types:
                    type_assertions = self.type_asserter(text=text, entities=canonical_entities, entity_types=entity_types,
                                                         few_shot_examples=examples_for_type_assertion).pairs
                    if self.logging:
                        print(f"GraphExtractor: INFO  :: Assigned types for entities as following: {type_assertions}")
                # The user wishes to leave it to the LLM to generate and assign types
                elif generate_types:
                    type_assertions = self.type_generator(text=text, entities=canonical_entities,
                                                          few_shot_examples=examples_for_type_generation).pairs
                    if self.logging:
                        print(f"GraphExtractor: INFO  :: Finished generating types and assigned them to entities as following: {type_assertions}")

            # Cluster types and update type assertions programmatically
            types = list(set([pair[1] for pair in type_assertions]))
            type_mapping = self.cluster_types(types, clustering_context)
            # Update type assertions with canonical types
            type_assertions = [(pair[0], type_mapping.get(pair[1], pair[1])) for pair in type_assertions]
            if self.logging and len(types) != len(set(type_mapping.values())):
                print(f"GraphExtractor: INFO  :: After type clustering: {list(set(type_mapping.values()))}")

            # Add class assertion axioms
            for pair in type_assertions:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(pair[0]))
                entity_type = OWLClass(ontology_namespace + self.snake_case(pair[1]))
                ax = OWLClassAssertionAxiom(subject, entity_type)
                onto.add_axiom(ax)

        # Extract triples of type s-p-l where l is a numeric literal, including dates.
        if extract_spl_triples:
            # Extract literals (from chunks if needed)
            if use_chunking and len(chunks) > 1:
                literals = self._extract_literals_from_chunks(chunks, examples_for_literal_extraction)
            else:
                literals = self.literal_extractor(text=text, few_shot_examples=examples_for_literal_extraction).l_values

            if self.logging:
                print(f"GraphExtractor: INFO  :: Generated the following numeric literals: {literals}")

            # Extract SPL triples (from chunks if needed)
            if use_chunking and len(chunks) > 1:
                spl_triples = self._extract_spl_triples_from_chunks(
                    chunks, canonical_entities, literals, examples_for_spl_triples_extraction
                )
            else:
                spl_triples = self.spl_triples_extractor(text=text, entities=canonical_entities, numeric_literals=literals,
                                                         few_shot_examples=examples_for_spl_triples_extraction).triples

            if self.logging:
                print(f"GraphExtractor: INFO  :: Generated the following s-p-l triples: {spl_triples}")

            # Cluster relations (data properties) in SPL triples and update programmatically
            spl_relations = list(set([triple[1] for triple in spl_triples]))
            spl_relation_mapping = self.cluster_relations(spl_relations, clustering_context)
            # Update SPL triples with canonical relations
            spl_triples = [(triple[0], spl_relation_mapping.get(triple[1], triple[1]), triple[2])
                          for triple in spl_triples]
            if self.logging and len(spl_relations) != len(set(spl_relation_mapping.values())):
                print(f"GraphExtractor: INFO  :: After SPL relation clustering: {list(set(spl_relation_mapping.values()))}")

            for triple in spl_triples:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
                prop = OWLDataProperty(ontology_namespace + self.snake_case(triple[1]))
                literal = OWLLiteral(str(self.snake_case(triple[2])), type_=StringOWLDatatype) # for now every literal will be represented as a string
                if triple[2] in literals:
                    ax = OWLDataPropertyAssertionAxiom(subject, prop, literal)
                    onto.add_axiom(ax)

        if create_class_hierarchy:
            for cls in onto.classes_in_signature():
                try:
                    superclasses, subclasses = extract_hierarchy_from_dbpedia(cls.remainder)
                except Exception:
                    continue
                if self.logging:
                    print(f"GraphExtractor: INFO  :: For class {cls.remainder} found superclasses: {[IRI.create(s).remainder for s in superclasses]} and subclasses: {[IRI.create(s).remainder for s in subclasses]}")

                for superclass in superclasses:
                    dbpedia_class_remainder = IRI.create(superclass).remainder
                    sup_cls = OWLClass(ontology_namespace + dbpedia_class_remainder)
                    ax = OWLSubClassOfAxiom(cls, sup_cls)
                    onto.add_axiom(ax)
                for subclass in subclasses:
                    dbpedia_class_remainder = IRI.create(subclass).remainder
                    sub_cls = OWLClass(ontology_namespace + dbpedia_class_remainder)
                    ax = OWLSubClassOfAxiom(sub_cls, cls)
                    onto.add_axiom(ax)

        onto.save(path=save_path)
        if self.logging:
            print(f"GraphExtractor: INFO  :: Successfully saved the ontology at {os.path.join(os.getcwd(),save_path)}")

        return onto

    def forward(self, text: Union[str, Path],
                ontology_namespace = "http://example.com/ontogen#",
                entity_types: List[str]=None,
                generate_types=False,
                extract_spl_triples=False,
                create_class_hierarchy=False,
                entity_clustering=True,
                use_chunking: bool = None,
                examples_for_entity_extraction=EXAMPLES_FOR_ENTITY_EXTRACTION,
                examples_for_triples_extraction=EXAMPLES_FOR_TRIPLES_EXTRACTION,
                examples_for_type_assertion=EXAMPLES_FOR_TYPE_ASSERTION,
                examples_for_type_generation=EXAMPLES_FOR_TYPE_GENERATION,
                examples_for_literal_extraction=EXAMPLES_FOR_LITERAL_EXTRACTION,
                examples_for_spl_triples_extraction=EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION,
                save_path="generated_ontology.owl"
                ) -> Ontology:

        """
        Extract an ontology from a given textual input or file.

        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            text (str or Path): Text input or file path from which the ontology will be extracted.
                Supports files: .txt, .pdf, .docx, .doc, .rtf, .html, .htm
            ontology_namespace (str): Namespace to use for the ontology.
            entity_types (List[str]): List of entity types to assign to extracted entities.
                Leave empty if generate_types is True.
            generate_types (bool): Whether to generate types for extracted entities.
            extract_spl_triples (bool): Whether to extract triples of type s-p-l where l is a numeric literal. This
                triples will be represented using data properties and a literal value of type string (although they
                are numeric values).
            create_class_hierarchy (bool): Whether to create a class hierarchy for the extracted entities.
            entity_clustering (bool): Whether to perform entity clustering to merge duplicate entities.
            use_chunking (bool): Whether to use text chunking for large documents.
                - None (default): Auto-detect based on text size (uses auto_chunk_threshold).
                - True: Force chunking even for smaller texts.
                - False: Disable chunking (may fail for very large texts).
            examples_for_entity_extraction (str): Few-shot examples for entity extraction.
            examples_for_triples_extraction (str): Few-shot examples for triple extraction.
            examples_for_type_assertion (str): Few-shot examples for type assertion.
            examples_for_type_generation (str): Few-shot examples for type generation and assertion.
            examples_for_literal_extraction (str): Few-shot examples for literal extraction.
            examples_for_spl_triples_extraction (str): Few-shot examples for s-p-l triples extraction.
            save_path (str): Path to save the generated ontology.

        Returns (Ontology): An ontology object.
        """

        if generate_types:
            assert entity_types is None, ("entity_types argument should be None "
                                          "when you want to generate types (i.e. when generate_types = True)")

        return self.generate_ontology(
            text=text,
            ontology_namespace=ontology_namespace,
            entity_types=entity_types,
            generate_types=generate_types,
            extract_spl_triples=extract_spl_triples,
            create_class_hierarchy=create_class_hierarchy,
            entity_clustering=entity_clustering,
            use_chunking=use_chunking,
            examples_for_entity_extraction=examples_for_entity_extraction,
            examples_for_triples_extraction=examples_for_triples_extraction,
            examples_for_type_assertion=examples_for_type_assertion,
            examples_for_type_generation=examples_for_type_generation,
            examples_for_literal_extraction=examples_for_literal_extraction,
            examples_for_spl_triples_extraction=examples_for_spl_triples_extraction,
            save_path=save_path
        )


class DomainGraphExtractor(GraphExtractor):
    def __init__(self, enable_logging=False, examples_cache_dir: Optional[str] = None):
        """
        A module to extract an RDF graph from domain-specific text input.
        Args:
            enable_logging: Whether to enable logging.
            examples_cache_dir: Directory to cache domain-specific examples. If None, uses current working directory.
        """
        super().__init__(enable_logging)
        self.domain_detector = dspy.Predict(Domain)
        self.few_shot_generator = dspy.Predict(DomainSpecificFewShotGenerator)
        self.entity_extractor = dspy.Predict(Entity)
        self.triples_extractor = dspy.Predict(Triple)
        self.type_asserter = dspy.Predict(TypeAssertion)
        self.type_generator = dspy.Predict(TypeGeneration)
        self.literal_extractor = dspy.Predict(Literal)
        self.spl_triples_extractor = dspy.Predict(SPLTriples)
        # Initialize examples cache manager
        self.examples_cache = DomainExamplesCache(cache_dir=examples_cache_dir)


    def generate_domain_specific_examples(self, domain: str):
        """
        Generate domain-specific few-shot examples for all task types.

        Automatically caches examples to disk for future reuse. If examples have been
        previously generated for the domain, they will be loaded from cache.

        Args:
            domain: The domain for which to generate examples.

        Returns:
            Dictionary containing few-shot examples for each task type, keyed by:
            'entity_extraction', 'triples_extraction', 'type_assertion', 'type_generation',
            'literal_extraction', 'triples_with_numeric_literals_extraction'
        """
        # Check if examples are already cached
        cached_examples = self.examples_cache.load_examples(domain)
        if cached_examples is not None:
            if self.logging:
                cache_file = self.examples_cache.get_cache_file_path(domain)
                print(f"DomainGraphExtractor: INFO :: Loaded cached examples for domain '{domain}' from {cache_file}")
            return cached_examples

        # Generate new examples if not cached
        examples = {}
        task_types = [
            'entity_extraction',
            'triples_extraction',
            'type_assertion',
            'type_generation',
            'literal_extraction',
            'triples_with_numeric_literals_extraction'
        ]

        if self.logging:
            print(f"DomainGraphExtractor: INFO :: Generating domain-specific few-shot examples for domain: {domain}")

        for task_type in task_types:
            result = self.few_shot_generator(
                domain=domain,
                task_type=task_type,
                num_examples=2
            )
            examples[task_type] = result.few_shot_examples
            if self.logging:
                print(f"DomainGraphExtractor: INFO :: Generated examples for {task_type}")

        # Save examples to cache
        if self.examples_cache.save_examples(domain, examples):
            if self.logging:
                cache_file = self.examples_cache.get_cache_file_path(domain)
                print(f"DomainGraphExtractor: INFO :: Cached examples for domain '{domain}' to {cache_file}")
        else:
            if self.logging:
                print(f"DomainGraphExtractor: WARNING :: Failed to cache examples for domain '{domain}'")

        return examples

    def clear_domain_cache(self, domain: str) -> bool:
        """
        Clear the cached examples for a specific domain.

        Args:
            domain: The domain for which to clear cached examples.

        Returns:
            True if the cache was cleared successfully, False otherwise.
        """
        success = self.examples_cache.clear_domain_cache(domain)
        if success and self.logging:
            print(f"DomainGraphExtractor: INFO :: Cleared cache for domain '{domain}'")
        return success

    def clear_all_domain_caches(self) -> bool:
        """
        Clear all cached domain examples.

        Returns:
            True if all caches were cleared successfully, False otherwise.
        """
        success = self.examples_cache.clear_all_caches()
        if success and self.logging:
            print(f"DomainGraphExtractor: INFO :: Cleared all domain example caches")
        return success

    def list_cached_domains(self) -> list:
        """
        List all domains that have cached examples.

        Returns:
            List of domain names with cached examples.
        """
        domains = self.examples_cache.list_cached_domains()
        if self.logging and domains:
            print(f"DomainGraphExtractor: INFO :: Cached domains: {', '.join(domains)}")
        return domains

    def is_domain_cached(self, domain: str) -> bool:
        """
        Check if examples exist for a domain in the cache.

        Args:
            domain: The domain to check.

        Returns:
            True if examples are cached for the domain, False otherwise.
        """
        return self.examples_cache.examples_exist(domain)

    def get_cache_file_path(self, domain: str) -> str:
        """
        Get the full path to the cache file for a domain.

        Args:
            domain: The domain name.

        Returns:
            String path to the cache file.
        """
        return self.examples_cache.get_cache_file_path(domain)

    def generate_ontology(self, text: Union[str, Path],
                          domain: str = None,
                          ontology_namespace = "http://example.com/ontogen#",
                          entity_types: List[str]=None,
                          generate_types=False,
                          extract_spl_triples=False,
                          create_class_hierarchy=False,
                          use_chunking: bool = None,
                          examples_for_entity_extraction=None,
                          examples_for_triples_extraction=None,
                          examples_for_type_assertion=None,
                          examples_for_type_generation=None,
                          examples_for_literal_extraction=None,
                          examples_for_spl_triples_extraction=None,
                          save_path="generated_ontology.owl") -> Ontology:
        """
        Generate a domain-specific ontology from text.

        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            text: Input text or file path to extract ontology from.
                Supports files: .txt, .pdf, .docx, .doc, .rtf, .html, .htm
            domain: The domain of the text. If None, will be detected automatically.
            ontology_namespace: Namespace for the ontology.
            entity_types: List of entity types to assign.
            generate_types: Whether to generate types automatically.
            extract_spl_triples: Whether to extract subject-property-literal triples.
            create_class_hierarchy: Whether to create class hierarchy from DBpedia.
            use_chunking: Whether to use text chunking for large documents.
                - None (default): Auto-detect based on text size (uses auto_chunk_threshold).
                - True: Force chunking even for smaller texts.
                - False: Disable chunking (may fail for very large texts).
            examples_for_*: Custom few-shot examples. If None, domain-specific examples will be generated.
            save_path: Path to save the ontology.

        Returns:
            Generated Ontology object.
        """
        # Load text from file if necessary
        if isinstance(text, (str, Path)):
            # Check if it's a file path
            source_path = Path(text) if not isinstance(text, Path) else text
            if source_path.is_file():
                text = self.load_text(text)
            # else: treat as raw text string
        
        # Determine whether to use chunking
        if use_chunking is None:
            use_chunking = self.should_chunk_text(text)

        if use_chunking:
            chunks = self.chunk_text(text)
            if self.logging:
                chunk_info = self.get_chunking_info(text)
                print(f"DomainGraphExtractor: INFO :: Text will be processed in {chunk_info['num_chunks']} chunks")
                print(f"DomainGraphExtractor: INFO :: Total chars: {chunk_info['total_chars']}, "
                      f"Est. tokens: {chunk_info['estimated_tokens']}")
        else:
            chunks = [text]

        # Use a representative sample for domain detection
        domain_detection_text = text[:self.auto_chunk_threshold] if len(text) > self.auto_chunk_threshold else text

        # Step 1: Detect domain if not provided
        if domain is None:
            domain_result = self.domain_detector(text=domain_detection_text)
            domain = domain_result.domain
            if self.logging:
                print(f"DomainGraphExtractor: INFO :: Detected domain: {domain}")
        else:
            if self.logging:
                print(f"DomainGraphExtractor: INFO :: Using provided domain: {domain}")

        # Step 2: Generate domain-specific few-shot examples if not provided
        use_generated_examples = (
            examples_for_entity_extraction is None or
            examples_for_triples_extraction is None or
            examples_for_type_assertion is None or
            examples_for_type_generation is None or
            examples_for_literal_extraction is None or
            examples_for_spl_triples_extraction is None
        )

        if use_generated_examples:
            generated_examples = self.generate_domain_specific_examples(domain)

            # Use generated examples only if user hasn't provided their own
            examples_for_entity_extraction = examples_for_entity_extraction or generated_examples['entity_extraction']
            examples_for_triples_extraction = examples_for_triples_extraction or generated_examples['triples_extraction']
            examples_for_type_assertion = examples_for_type_assertion or generated_examples['type_assertion']
            examples_for_type_generation = examples_for_type_generation or generated_examples['type_generation']
            examples_for_literal_extraction = examples_for_literal_extraction or generated_examples['literal_extraction']
            examples_for_spl_triples_extraction = examples_for_spl_triples_extraction or generated_examples['triples_with_numeric_literals_extraction']

        # Step 3: Extract entities (from chunks if needed)
        if self.logging:
            print("DomainGraphExtractor: INFO :: In the generated triples, you may see entities or literals that were not "
                  "part of the extracted entities or literals. They are filtered before added to the ontology.")

        if use_chunking and len(chunks) > 1:
            all_entity_lists = []
            for i, chunk in enumerate(chunks):
                if self.logging:
                    print(f"DomainGraphExtractor: INFO :: Extracting entities from chunk {i+1}/{len(chunks)}")
                chunk_entities = self.entity_extractor(text=chunk, few_shot_examples=examples_for_entity_extraction).entities
                all_entity_lists.append(chunk_entities)
            entities = self._merge_entity_lists(all_entity_lists)
        else:
            entities = self.entity_extractor(text=text, few_shot_examples=examples_for_entity_extraction).entities

        if self.logging:
            print(f"DomainGraphExtractor: INFO :: Generated the following entities: {entities}")

        # Step 4: Cluster entities to identify and merge duplicates
        # Use representative sample for clustering context
        clustering_context = text[:self.auto_chunk_threshold] if len(text) > self.auto_chunk_threshold else text

        entity_mapping = self.cluster_entities(entities, clustering_context)
        canonical_entities = list(set(entity_mapping.values()))
        if self.logging and len(entities) != len(canonical_entities):
            print(f"DomainGraphExtractor: INFO :: After clustering: {canonical_entities}")

        # Step 5: Extract triples using canonical entities (from chunks if needed)
        if use_chunking and len(chunks) > 1:
            all_triple_lists = []
            for i, chunk in enumerate(chunks):
                if self.logging:
                    print(f"DomainGraphExtractor: INFO :: Extracting triples from chunk {i+1}/{len(chunks)}")
                chunk_triples = self.triples_extractor(text=chunk, entities=canonical_entities, few_shot_examples=examples_for_triples_extraction).triples
                all_triple_lists.append(chunk_triples)
            triples = self._merge_triple_lists(all_triple_lists)
        else:
            triples = self.triples_extractor(text=text, entities=canonical_entities, few_shot_examples=examples_for_triples_extraction).triples

        if self.logging:
            print(f"DomainGraphExtractor: INFO :: Generated the following triples: {triples}")

        # Step 5.5: Cluster relations (object properties) and update triples programmatically BEFORE coherence check
        relations = list(set([triple[1] for triple in triples]))
        relation_mapping = self.cluster_relations(relations, clustering_context)
        # Update triples with canonical relations
        updated_triples = [(triple[0], relation_mapping.get(triple[1], triple[1]), triple[2]) for triple in triples]
        if self.logging and len(relations) != len(set(relation_mapping.values())):
            print(f"DomainGraphExtractor: INFO :: After relation clustering: {list(set(relation_mapping.values()))}")

        # Step 6: Check coherence of the relation-normalized triples
        coherent_triples = self.check_coherence(updated_triples, clustering_context)
        if self.logging:
            print(f"DomainGraphExtractor: INFO :: After coherence check, kept {len(coherent_triples)} triples")

        # Step 7: Create ontology and add triples
        onto = Ontology(ontology_iri=IRI.create("http://example.com/ontogen"), load=False)
        for triple in coherent_triples:
            subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
            prop = OWLObjectProperty(ontology_namespace + self.snake_case(triple[1]))
            object = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[2]))
            if triple[0] in canonical_entities and triple[2] in canonical_entities:
                ax = OWLObjectPropertyAssertionAxiom(subject, prop, object)
                onto.add_axiom(ax)

        # Step 8: Handle type assertions
        if entity_types is not None or generate_types:
            type_assertions = None

            if use_chunking and len(chunks) > 1:
                # Process types from chunks
                all_assertion_lists = []
                for i, chunk in enumerate(chunks):
                    if self.logging:
                        print(f"DomainGraphExtractor: INFO :: Extracting types from chunk {i+1}/{len(chunks)}")
                    if entity_types is not None and not generate_types:
                        chunk_assertions = self.type_asserter(text=chunk, entities=canonical_entities, entity_types=entity_types,
                                                              few_shot_examples=examples_for_type_assertion).pairs
                    else:
                        chunk_assertions = self.type_generator(text=chunk, entities=canonical_entities,
                                                               few_shot_examples=examples_for_type_generation).pairs
                    all_assertion_lists.append(chunk_assertions)
                type_assertions = self._merge_type_assertions(all_assertion_lists)
            else:
                if entity_types is not None and not generate_types:
                    type_assertions = self.type_asserter(text=text, entities=canonical_entities, entity_types=entity_types,
                                                         few_shot_examples=examples_for_type_assertion).pairs
                    if self.logging:
                        print(f"DomainGraphExtractor: INFO :: Assigned types for entities as following: {type_assertions}")
                elif generate_types:
                    type_assertions = self.type_generator(text=text, entities=canonical_entities,
                                                          few_shot_examples=examples_for_type_generation).pairs
                    if self.logging:
                        print(f"DomainGraphExtractor: INFO :: Finished generating types and assigned them to entities as following: {type_assertions}")

            # Cluster types and update type assertions programmatically
            types = list(set([pair[1] for pair in type_assertions]))
            type_mapping = self.cluster_types(types, clustering_context)
            # Update type assertions with canonical types
            type_assertions = [(pair[0], type_mapping.get(pair[1], pair[1])) for pair in type_assertions]
            if self.logging and len(types) != len(set(type_mapping.values())):
                print(f"DomainGraphExtractor: INFO :: After type clustering: {list(set(type_mapping.values()))}")

            for pair in type_assertions:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(pair[0]))
                entity_type = OWLClass(ontology_namespace + self.snake_case(pair[1]))
                ax = OWLClassAssertionAxiom(subject, entity_type)
                onto.add_axiom(ax)

        # Step 9: Extract SPL triples if requested
        if extract_spl_triples:
            # Extract literals (from chunks if needed)
            if use_chunking and len(chunks) > 1:
                all_literal_lists = []
                for i, chunk in enumerate(chunks):
                    if self.logging:
                        print(f"DomainGraphExtractor: INFO :: Extracting literals from chunk {i+1}/{len(chunks)}")
                    chunk_literals = self.literal_extractor(text=chunk, few_shot_examples=examples_for_literal_extraction).l_values
                    all_literal_lists.append(chunk_literals)
                literals = self._merge_literal_lists(all_literal_lists)
            else:
                literals = self.literal_extractor(text=text, few_shot_examples=examples_for_literal_extraction).l_values

            if self.logging:
                print(f"DomainGraphExtractor: INFO :: Generated the following numeric literals: {literals}")

            # Extract SPL triples (from chunks if needed)
            if use_chunking and len(chunks) > 1:
                all_spl_triple_lists = []
                for i, chunk in enumerate(chunks):
                    if self.logging:
                        print(f"DomainGraphExtractor: INFO :: Extracting SPL triples from chunk {i+1}/{len(chunks)}")
                    chunk_spl_triples = self.spl_triples_extractor(text=chunk, entities=canonical_entities, numeric_literals=literals,
                                                                   few_shot_examples=examples_for_spl_triples_extraction).triples
                    all_spl_triple_lists.append(chunk_spl_triples)
                spl_triples = self._merge_triple_lists(all_spl_triple_lists)
            else:
                spl_triples = self.spl_triples_extractor(text=text, entities=canonical_entities, numeric_literals=literals,
                                                         few_shot_examples=examples_for_spl_triples_extraction).triples

            if self.logging:
                print(f"DomainGraphExtractor: INFO :: Generated the following s-p-l triples: {spl_triples}")

            # Cluster relations (data properties) in SPL triples and update programmatically
            spl_relations = list(set([triple[1] for triple in spl_triples]))
            spl_relation_mapping = self.cluster_relations(spl_relations, clustering_context)
            # Update SPL triples with canonical relations
            spl_triples = [(triple[0], spl_relation_mapping.get(triple[1], triple[1]), triple[2])
                          for triple in spl_triples]
            if self.logging and len(spl_relations) != len(set(spl_relation_mapping.values())):
                print(f"DomainGraphExtractor: INFO :: After SPL relation clustering: {list(set(spl_relation_mapping.values()))}")

            for triple in spl_triples:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
                prop = OWLDataProperty(ontology_namespace + self.snake_case(triple[1]))
                literal = OWLLiteral(str(self.snake_case(triple[2])), type_=StringOWLDatatype)
                if triple[2] in literals:
                    try:
                        ax = OWLDataPropertyAssertionAxiom(subject, prop, literal)
                        onto.add_axiom(ax)
                    except Exception as e:
                        print(e)
                        print(f"Subject: {subject}, Property: {prop}, Literal: {literal}")

        # Step 10: Create class hierarchy if requested
        if create_class_hierarchy:
            for cls in onto.classes_in_signature():
                try:
                    superclasses, subclasses = extract_hierarchy_from_dbpedia(cls.remainder)
                except Exception:
                    continue
                if self.logging:
                    print(f"DomainGraphExtractor: INFO :: For class {cls.remainder} found superclasses: {[IRI.create(s).remainder for s in superclasses]} and subclasses: {[IRI.create(s).remainder for s in subclasses]}")

                for superclass in superclasses:
                    dbpedia_class_remainder = IRI.create(superclass).remainder
                    sup_cls = OWLClass(ontology_namespace + dbpedia_class_remainder)
                    ax = OWLSubClassOfAxiom(cls, sup_cls)
                    onto.add_axiom(ax)
                for subclass in subclasses:
                    dbpedia_class_remainder = IRI.create(subclass).remainder
                    sub_cls = OWLClass(ontology_namespace + dbpedia_class_remainder)
                    ax = OWLSubClassOfAxiom(sub_cls, cls)
                    onto.add_axiom(ax)

        # Step 11: Save ontology
        onto.save(path=save_path)
        if self.logging:
            print(f"DomainGraphExtractor: INFO :: Successfully saved the ontology at {os.path.join(os.getcwd(),save_path)}")

        return onto

    def forward(self, text: Union[str, Path],
                domain: str = None,
                ontology_namespace = "http://example.com/ontogen#",
                entity_types: List[str]=None,
                generate_types=False,
                extract_spl_triples=False,
                create_class_hierarchy=False,
                use_chunking: bool = None,
                examples_for_entity_extraction=None,
                examples_for_triples_extraction=None,
                examples_for_type_assertion=None,
                examples_for_type_generation=None,
                examples_for_literal_extraction=None,
                examples_for_spl_triples_extraction=None,
                save_path="generated_ontology.owl") -> Ontology:
        """
        Extract a domain-specific ontology from a given textual input or file.

        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            text (str or Path): Text input or file path from which the ontology will be extracted.
                Supports files: .txt, .pdf, .docx, .doc, .rtf, .html, .htm
            domain (str): The domain of the text. If None, will be detected automatically.
            ontology_namespace (str): Namespace to use for the ontology.
            entity_types (List[str]): List of entity types to assign to extracted entities.
                Leave empty if generate_types is True.
            generate_types (bool): Whether to generate types for extracted entities.
            extract_spl_triples (bool): Whether to extract triples of type s-p-l where l is a numeric literal.
            create_class_hierarchy (bool): Whether to create a class hierarchy for the extracted entities.
            use_chunking (bool): Whether to use text chunking for large documents.
                - None (default): Auto-detect based on text size (uses auto_chunk_threshold).
                - True: Force chunking even for smaller texts.
                - False: Disable chunking (may fail for very large texts).
            examples_for_entity_extraction (str): Few-shot examples for entity extraction. If None, domain-specific examples will be generated.
            examples_for_triples_extraction (str): Few-shot examples for triple extraction. If None, domain-specific examples will be generated.
            examples_for_type_assertion (str): Few-shot examples for type assertion. If None, domain-specific examples will be generated.
            examples_for_type_generation (str): Few-shot examples for type generation. If None, domain-specific examples will be generated.
            examples_for_literal_extraction (str): Few-shot examples for literal extraction. If None, domain-specific examples will be generated.
            examples_for_spl_triples_extraction (str): Few-shot examples for s-p-l triples extraction. If None, domain-specific examples will be generated.
            save_path (str): Path to save the generated ontology.

        Returns (Ontology): An ontology object.
        """
        if generate_types:
            assert entity_types is None, ("entity_types argument should be None "
                                          "when you want to generate types (i.e. when generate_types = True)")

        return self.generate_ontology(
            text=text,
            domain=domain,
            ontology_namespace=ontology_namespace,
            entity_types=entity_types,
            generate_types=generate_types,
            extract_spl_triples=extract_spl_triples,
            create_class_hierarchy=create_class_hierarchy,
            use_chunking=use_chunking,
            examples_for_entity_extraction=examples_for_entity_extraction,
            examples_for_triples_extraction=examples_for_triples_extraction,
            examples_for_type_assertion=examples_for_type_assertion,
            examples_for_type_generation=examples_for_type_generation,
            examples_for_literal_extraction=examples_for_literal_extraction,
            examples_for_spl_triples_extraction=examples_for_spl_triples_extraction,
            save_path=save_path
        )


class CrossDomainGraphExtractor(GraphExtractor):
    """
    A module to extract cross-domain RDF graphs from text input.
    Handles content that spans multiple related domains.
    Supports automatic chunking for large texts that exceed the LLM's context window.
    """
    def __init__(self, enable_logging=False):
        super().__init__(enable_logging)
        self.domain_detector = dspy.Predict(Domain)
        self.entity_extractor = dspy.Predict(Entity)
        self.triples_extractor = dspy.Predict(Triple)
        self.type_asserter = dspy.Predict(TypeAssertion)
        self.type_generator = dspy.Predict(TypeGeneration)
        self.literal_extractor = dspy.Predict(Literal)
        self.spl_triples_extractor = dspy.Predict(SPLTriples)

    def generate_ontology(self, text: Union[str, Path],
                          ontology_namespace = "http://example.com/ontogen#",
                          entity_types: List[str]=None,
                          generate_types=False,
                          extract_spl_triples=False,
                          create_class_hierarchy=False,
                          entity_clustering=True,
                          use_chunking: bool = None,
                          examples_for_entity_extraction=EXAMPLES_FOR_ENTITY_EXTRACTION,
                          examples_for_triples_extraction=EXAMPLES_FOR_TRIPLES_EXTRACTION,
                          examples_for_type_assertion=EXAMPLES_FOR_TYPE_ASSERTION,
                          examples_for_type_generation=EXAMPLES_FOR_TYPE_GENERATION,
                          examples_for_literal_extraction=EXAMPLES_FOR_LITERAL_EXTRACTION,
                          examples_for_spl_triples_extraction=EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION,
                          save_path="generated_ontology.owl") -> Ontology:
        """
        Generate a cross-domain ontology from text.

        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            text: Input text or file path to extract ontology from.
                Supports files: .txt, .pdf, .docx, .doc, .rtf, .html, .htm
            ontology_namespace: Namespace for the ontology.
            entity_types: List of entity types to assign.
            generate_types: Whether to generate types automatically.
            extract_spl_triples: Whether to extract subject-property-literal triples.
            create_class_hierarchy: Whether to create class hierarchy from DBpedia.
            entity_clustering: Whether to perform entity clustering.
            use_chunking: Whether to use text chunking for large documents.
                - None (default): Auto-detect based on text size (uses auto_chunk_threshold).
                - True: Force chunking even for smaller texts.
                - False: Disable chunking (may fail for very large texts).
            examples_for_*: Few-shot examples for various extraction tasks.
            save_path: Path to save the ontology.

        Returns:
            Generated Ontology object.
        """
        # Load text from file if necessary
        if isinstance(text, (str, Path)):
            source_path = Path(text) if not isinstance(text, Path) else text
            if source_path.is_file():
                text = self.load_text(text)

        # Determine whether to use chunking
        if use_chunking is None:
            use_chunking = self.should_chunk_text(text)

        if use_chunking:
            chunks = self.chunk_text(text)
            if self.logging:
                chunk_info = self.get_chunking_info(text)
                print(f"CrossDomainGraphExtractor: INFO :: Text will be processed in {chunk_info['num_chunks']} chunks")
                print(f"CrossDomainGraphExtractor: INFO :: Total chars: {chunk_info['total_chars']}, "
                      f"Est. tokens: {chunk_info['estimated_tokens']}")
        else:
            chunks = [text]

        if self.logging:
            print("CrossDomainGraphExtractor: INFO :: Extracting cross-domain ontology from text")

        # Use a representative sample for domain detection
        domain_detection_text = text[:self.auto_chunk_threshold] if len(text) > self.auto_chunk_threshold else text

        # Detect domains present in the text
        domain_result = self.domain_detector(text=domain_detection_text)
        if self.logging:
            print(f"CrossDomainGraphExtractor: INFO :: Detected domain(s): {domain_result.domain}")

        # Step 1: Extract entities (from chunks if needed)
        if use_chunking and len(chunks) > 1:
            entities = self._extract_entities_from_chunks(chunks, examples_for_entity_extraction)
        else:
            entities = self.entity_extractor(text=text, few_shot_examples=examples_for_entity_extraction).entities

        if self.logging:
            print(f"CrossDomainGraphExtractor: INFO :: Generated the following entities: {entities}")

        # Step 2: Cluster entities
        clustering_context = text[:self.auto_chunk_threshold] if len(text) > self.auto_chunk_threshold else text

        if entity_clustering:
            entity_mapping = self.cluster_entities(entities, clustering_context)
            canonical_entities = list(set(entity_mapping.values()))
        else:
            canonical_entities = entities

        if self.logging and len(entities) != len(canonical_entities):
            print(f"CrossDomainGraphExtractor: INFO :: After clustering: {canonical_entities}")

        # Step 3: Extract triples (from chunks if needed)
        if use_chunking and len(chunks) > 1:
            triples = self._extract_triples_from_chunks(chunks, canonical_entities, examples_for_triples_extraction)
        else:
            triples = self.triples_extractor(text=text, entities=canonical_entities,
                                            few_shot_examples=examples_for_triples_extraction).triples

        if self.logging:
            print(f"CrossDomainGraphExtractor: INFO :: Generated the following triples: {triples}")

        # Step 3.5: Cluster relations
        relations = list(set([triple[1] for triple in triples]))
        relation_mapping = self.cluster_relations(relations, clustering_context)
        updated_triples = [(triple[0], relation_mapping.get(triple[1], triple[1]), triple[2]) for triple in triples]

        if self.logging and len(relations) != len(set(relation_mapping.values())):
            print(f"CrossDomainGraphExtractor: INFO :: After relation clustering: {list(set(relation_mapping.values()))}")

        # Step 4: Check coherence
        coherent_triples = self.check_coherence(updated_triples, clustering_context)
        if self.logging:
            print(f"CrossDomainGraphExtractor: INFO :: After coherence check, kept {len(coherent_triples)} triples")

        # Step 5: Create ontology
        onto = Ontology(ontology_iri=IRI.create("http://example.com/ontogen"), load=False)
        for triple in coherent_triples:
            subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
            prop = OWLObjectProperty(ontology_namespace + self.snake_case(triple[1]))
            object = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[2]))
            if triple[0] in canonical_entities and triple[2] in canonical_entities:
                ax = OWLObjectPropertyAssertionAxiom(subject, prop, object)
                onto.add_axiom(ax)

        # Step 6: Handle type assertions
        if entity_types is not None or generate_types:
            if use_chunking and len(chunks) > 1:
                type_assertions = self._extract_types_from_chunks(
                    chunks, canonical_entities, entity_types, generate_types,
                    examples_for_type_assertion, examples_for_type_generation
                )
            else:
                if entity_types is not None and not generate_types:
                    type_assertions = self.type_asserter(text=text, entities=canonical_entities,
                                                        entity_types=entity_types,
                                                        few_shot_examples=examples_for_type_assertion).pairs
                else:
                    type_assertions = self.type_generator(text=text, entities=canonical_entities,
                                                         few_shot_examples=examples_for_type_generation).pairs

            # Cluster types
            types = list(set([pair[1] for pair in type_assertions]))
            type_mapping = self.cluster_types(types, clustering_context)
            type_assertions = [(pair[0], type_mapping.get(pair[1], pair[1])) for pair in type_assertions]

            if self.logging and len(types) != len(set(type_mapping.values())):
                print(f"CrossDomainGraphExtractor: INFO :: After type clustering: {list(set(type_mapping.values()))}")

            for pair in type_assertions:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(pair[0]))
                entity_type = OWLClass(ontology_namespace + self.snake_case(pair[1]))
                ax = OWLClassAssertionAxiom(subject, entity_type)
                onto.add_axiom(ax)

        # Step 7: Extract SPL triples if requested
        if extract_spl_triples:
            if use_chunking and len(chunks) > 1:
                literals = self._extract_literals_from_chunks(chunks, examples_for_literal_extraction)
            else:
                literals = self.literal_extractor(text=text, few_shot_examples=examples_for_literal_extraction).l_values

            if self.logging:
                print(f"CrossDomainGraphExtractor: INFO :: Generated the following numeric literals: {literals}")

            if use_chunking and len(chunks) > 1:
                spl_triples = self._extract_spl_triples_from_chunks(
                    chunks, canonical_entities, literals, examples_for_spl_triples_extraction
                )
            else:
                spl_triples = self.spl_triples_extractor(text=text, entities=canonical_entities,
                                                        numeric_literals=literals,
                                                        few_shot_examples=examples_for_spl_triples_extraction).triples

            if self.logging:
                print(f"CrossDomainGraphExtractor: INFO :: Generated the following s-p-l triples: {spl_triples}")

            # Cluster SPL relations
            spl_relations = list(set([triple[1] for triple in spl_triples]))
            spl_relation_mapping = self.cluster_relations(spl_relations, clustering_context)
            spl_triples = [(triple[0], spl_relation_mapping.get(triple[1], triple[1]), triple[2])
                          for triple in spl_triples]

            for triple in spl_triples:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
                prop = OWLDataProperty(ontology_namespace + self.snake_case(triple[1]))
                literal = OWLLiteral(str(self.snake_case(triple[2])), type_=StringOWLDatatype)
                if triple[2] in literals:
                    ax = OWLDataPropertyAssertionAxiom(subject, prop, literal)
                    onto.add_axiom(ax)

        # Step 8: Create class hierarchy if requested
        if create_class_hierarchy:
            for cls in onto.classes_in_signature():
                try:
                    superclasses, subclasses = extract_hierarchy_from_dbpedia(cls.remainder)
                except Exception:
                    continue
                if self.logging:
                    print(f"CrossDomainGraphExtractor: INFO :: For class {cls.remainder} found superclasses: "
                          f"{[IRI.create(s).remainder for s in superclasses]} and subclasses: "
                          f"{[IRI.create(s).remainder for s in subclasses]}")

                for superclass in superclasses:
                    dbpedia_class_remainder = IRI.create(superclass).remainder
                    sup_cls = OWLClass(ontology_namespace + dbpedia_class_remainder)
                    ax = OWLSubClassOfAxiom(cls, sup_cls)
                    onto.add_axiom(ax)
                for subclass in subclasses:
                    dbpedia_class_remainder = IRI.create(subclass).remainder
                    sub_cls = OWLClass(ontology_namespace + dbpedia_class_remainder)
                    ax = OWLSubClassOfAxiom(sub_cls, cls)
                    onto.add_axiom(ax)

        onto.save(path=save_path)
        if self.logging:
            print(f"CrossDomainGraphExtractor: INFO :: Successfully saved the ontology at {os.path.join(os.getcwd(),save_path)}")

        return onto

    def forward(self, text: Union[str, Path],
                ontology_namespace = "http://example.com/ontogen#",
                entity_types: List[str]=None,
                generate_types=False,
                extract_spl_triples=False,
                create_class_hierarchy=False,
                entity_clustering=True,
                use_chunking: bool = None,
                examples_for_entity_extraction=EXAMPLES_FOR_ENTITY_EXTRACTION,
                examples_for_triples_extraction=EXAMPLES_FOR_TRIPLES_EXTRACTION,
                examples_for_type_assertion=EXAMPLES_FOR_TYPE_ASSERTION,
                examples_for_type_generation=EXAMPLES_FOR_TYPE_GENERATION,
                examples_for_literal_extraction=EXAMPLES_FOR_LITERAL_EXTRACTION,
                examples_for_spl_triples_extraction=EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION,
                save_path="generated_ontology.owl") -> Ontology:
        """
        Extract a cross-domain ontology from a given textual input or file.

        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            text (str or Path): Text input or file path from which the ontology will be extracted.
                Supports files: .txt, .pdf, .docx, .doc, .rtf, .html, .htm
            ontology_namespace (str): Namespace to use for the ontology.
            entity_types (List[str]): List of entity types to assign to extracted entities.
                Leave empty if generate_types is True.
            generate_types (bool): Whether to generate types for extracted entities.
            extract_spl_triples (bool): Whether to extract triples of type s-p-l where l is a numeric literal.
            create_class_hierarchy (bool): Whether to create a class hierarchy for the extracted entities.
            entity_clustering (bool): Whether to perform entity clustering to merge duplicate entities.
            use_chunking (bool): Whether to use text chunking for large documents.
                - None (default): Auto-detect based on text size (uses auto_chunk_threshold).
                - True: Force chunking even for smaller texts.
                - False: Disable chunking (may fail for very large texts).
            examples_for_entity_extraction (str): Few-shot examples for entity extraction.
            examples_for_triples_extraction (str): Few-shot examples for triple extraction.
            examples_for_type_assertion (str): Few-shot examples for type assertion.
            examples_for_type_generation (str): Few-shot examples for type generation.
            examples_for_literal_extraction (str): Few-shot examples for literal extraction.
            examples_for_spl_triples_extraction (str): Few-shot examples for s-p-l triples extraction.
            save_path (str): Path to save the generated ontology.

        Returns (Ontology): An ontology object.
        """
        if generate_types:
            assert entity_types is None, ("entity_types argument should be None "
                                          "when you want to generate types (i.e. when generate_types = True)")

        return self.generate_ontology(
            text=text,
            ontology_namespace=ontology_namespace,
            entity_types=entity_types,
            generate_types=generate_types,
            extract_spl_triples=extract_spl_triples,
            create_class_hierarchy=create_class_hierarchy,
            entity_clustering=entity_clustering,
            use_chunking=use_chunking,
            examples_for_entity_extraction=examples_for_entity_extraction,
            examples_for_triples_extraction=examples_for_triples_extraction,
            examples_for_type_assertion=examples_for_type_assertion,
            examples_for_type_generation=examples_for_type_generation,
            examples_for_literal_extraction=examples_for_literal_extraction,
            examples_for_spl_triples_extraction=examples_for_spl_triples_extraction,
            save_path=save_path
        )


class EnterpriseGraphExtractor(GraphExtractor):
    """
    A module to extract enterprise RDF graphs from text input.
    Tailored for organizational knowledge representation.
    Supports automatic chunking for large texts that exceed the LLM's context window.
    """
    def __init__(self, enable_logging=False):
        super().__init__(enable_logging)
        self.entity_extractor = dspy.Predict(Entity)
        self.triples_extractor = dspy.Predict(Triple)
        self.type_asserter = dspy.Predict(TypeAssertion)
        self.type_generator = dspy.Predict(TypeGeneration)
        self.literal_extractor = dspy.Predict(Literal)
        self.spl_triples_extractor = dspy.Predict(SPLTriples)

    def generate_ontology(self, text: Union[str, Path],
                          ontology_namespace = "http://example.com/ontogen#",
                          entity_types: List[str]=None,
                          generate_types=False,
                          extract_spl_triples=False,
                          create_class_hierarchy=False,
                          entity_clustering=True,
                          use_chunking: bool = None,
                          examples_for_entity_extraction=EXAMPLES_FOR_ENTITY_EXTRACTION,
                          examples_for_triples_extraction=EXAMPLES_FOR_TRIPLES_EXTRACTION,
                          examples_for_type_assertion=EXAMPLES_FOR_TYPE_ASSERTION,
                          examples_for_type_generation=EXAMPLES_FOR_TYPE_GENERATION,
                          examples_for_literal_extraction=EXAMPLES_FOR_LITERAL_EXTRACTION,
                          examples_for_spl_triples_extraction=EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION,
                          save_path="generated_ontology.owl") -> Ontology:
        """
        Generate an enterprise ontology from text.

        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            text: Input text or file path to extract ontology from.
                Supports files: .txt, .pdf, .docx, .doc, .rtf, .html, .htm
            ontology_namespace: Namespace for the ontology.
            entity_types: List of entity types to assign (e.g., Department, Employee, Project).
            generate_types: Whether to generate types automatically.
            extract_spl_triples: Whether to extract subject-property-literal triples.
            create_class_hierarchy: Whether to create class hierarchy from DBpedia.
            entity_clustering: Whether to perform entity clustering.
            use_chunking: Whether to use text chunking for large documents.
                - None (default): Auto-detect based on text size (uses auto_chunk_threshold).
                - True: Force chunking even for smaller texts.
                - False: Disable chunking (may fail for very large texts).
            examples_for_*: Few-shot examples for various extraction tasks.
            save_path: Path to save the ontology.

        Returns:
            Generated Ontology object.
        """
        # Load text from file if necessary
        if isinstance(text, (str, Path)):
            source_path = Path(text) if not isinstance(text, Path) else text
            if source_path.is_file():
                text = self.load_text(text)

        # Determine whether to use chunking
        if use_chunking is None:
            use_chunking = self.should_chunk_text(text)

        if use_chunking:
            chunks = self.chunk_text(text)
            if self.logging:
                chunk_info = self.get_chunking_info(text)
                print(f"EnterpriseGraphExtractor: INFO :: Text will be processed in {chunk_info['num_chunks']} chunks")
                print(f"EnterpriseGraphExtractor: INFO :: Total chars: {chunk_info['total_chars']}, "
                      f"Est. tokens: {chunk_info['estimated_tokens']}")
        else:
            chunks = [text]

        if self.logging:
            print("EnterpriseGraphExtractor: INFO :: Extracting enterprise ontology from organizational text")

        # Step 1: Extract entities (from chunks if needed)
        if use_chunking and len(chunks) > 1:
            entities = self._extract_entities_from_chunks(chunks, examples_for_entity_extraction)
        else:
            entities = self.entity_extractor(text=text, few_shot_examples=examples_for_entity_extraction).entities

        if self.logging:
            print(f"EnterpriseGraphExtractor: INFO :: Generated the following entities: {entities}")

        # Step 2: Cluster entities
        clustering_context = text[:self.auto_chunk_threshold] if len(text) > self.auto_chunk_threshold else text

        if entity_clustering:
            entity_mapping = self.cluster_entities(entities, clustering_context)
            canonical_entities = list(set(entity_mapping.values()))
        else:
            canonical_entities = entities

        if self.logging and len(entities) != len(canonical_entities):
            print(f"EnterpriseGraphExtractor: INFO :: After clustering: {canonical_entities}")

        # Step 3: Extract triples (from chunks if needed)
        if use_chunking and len(chunks) > 1:
            triples = self._extract_triples_from_chunks(chunks, canonical_entities, examples_for_triples_extraction)
        else:
            triples = self.triples_extractor(text=text, entities=canonical_entities,
                                            few_shot_examples=examples_for_triples_extraction).triples

        if self.logging:
            print(f"EnterpriseGraphExtractor: INFO :: Generated the following triples: {triples}")

        # Step 3.5: Cluster relations
        relations = list(set([triple[1] for triple in triples]))
        relation_mapping = self.cluster_relations(relations, clustering_context)
        updated_triples = [(triple[0], relation_mapping.get(triple[1], triple[1]), triple[2]) for triple in triples]

        if self.logging and len(relations) != len(set(relation_mapping.values())):
            print(f"EnterpriseGraphExtractor: INFO :: After relation clustering: {list(set(relation_mapping.values()))}")

        # Step 4: Check coherence
        coherent_triples = self.check_coherence(updated_triples, clustering_context)
        if self.logging:
            print(f"EnterpriseGraphExtractor: INFO :: After coherence check, kept {len(coherent_triples)} triples")

        # Step 5: Create ontology
        onto = Ontology(ontology_iri=IRI.create("http://example.com/ontogen"), load=False)
        for triple in coherent_triples:
            subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
            prop = OWLObjectProperty(ontology_namespace + self.snake_case(triple[1]))
            object = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[2]))
            if triple[0] in canonical_entities and triple[2] in canonical_entities:
                ax = OWLObjectPropertyAssertionAxiom(subject, prop, object)
                onto.add_axiom(ax)

        # Step 6: Handle type assertions
        if entity_types is not None or generate_types:
            if use_chunking and len(chunks) > 1:
                type_assertions = self._extract_types_from_chunks(
                    chunks, canonical_entities, entity_types, generate_types,
                    examples_for_type_assertion, examples_for_type_generation
                )
            else:
                if entity_types is not None and not generate_types:
                    type_assertions = self.type_asserter(text=text, entities=canonical_entities,
                                                        entity_types=entity_types,
                                                        few_shot_examples=examples_for_type_assertion).pairs
                    if self.logging:
                        print(f"EnterpriseGraphExtractor: INFO :: Assigned types for entities: {type_assertions}")
                else:
                    type_assertions = self.type_generator(text=text, entities=canonical_entities,
                                                         few_shot_examples=examples_for_type_generation).pairs
                    if self.logging:
                        print(f"EnterpriseGraphExtractor: INFO :: Generated and assigned types: {type_assertions}")

            # Cluster types
            types = list(set([pair[1] for pair in type_assertions]))
            type_mapping = self.cluster_types(types, clustering_context)
            type_assertions = [(pair[0], type_mapping.get(pair[1], pair[1])) for pair in type_assertions]

            if self.logging and len(types) != len(set(type_mapping.values())):
                print(f"EnterpriseGraphExtractor: INFO :: After type clustering: {list(set(type_mapping.values()))}")

            for pair in type_assertions:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(pair[0]))
                entity_type = OWLClass(ontology_namespace + self.snake_case(pair[1]))
                ax = OWLClassAssertionAxiom(subject, entity_type)
                onto.add_axiom(ax)

        # Step 7: Extract SPL triples if requested
        if extract_spl_triples:
            if use_chunking and len(chunks) > 1:
                literals = self._extract_literals_from_chunks(chunks, examples_for_literal_extraction)
            else:
                literals = self.literal_extractor(text=text, few_shot_examples=examples_for_literal_extraction).l_values

            if self.logging:
                print(f"EnterpriseGraphExtractor: INFO :: Generated the following numeric literals: {literals}")

            if use_chunking and len(chunks) > 1:
                spl_triples = self._extract_spl_triples_from_chunks(
                    chunks, canonical_entities, literals, examples_for_spl_triples_extraction
                )
            else:
                spl_triples = self.spl_triples_extractor(text=text, entities=canonical_entities,
                                                        numeric_literals=literals,
                                                        few_shot_examples=examples_for_spl_triples_extraction).triples

            if self.logging:
                print(f"EnterpriseGraphExtractor: INFO :: Generated the following s-p-l triples: {spl_triples}")

            # Cluster SPL relations
            spl_relations = list(set([triple[1] for triple in spl_triples]))
            spl_relation_mapping = self.cluster_relations(spl_relations, clustering_context)
            spl_triples = [(triple[0], spl_relation_mapping.get(triple[1], triple[1]), triple[2])
                          for triple in spl_triples]

            if self.logging and len(spl_relations) != len(set(spl_relation_mapping.values())):
                print(f"EnterpriseGraphExtractor: INFO :: After SPL relation clustering: {list(set(spl_relation_mapping.values()))}")

            for triple in spl_triples:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
                prop = OWLDataProperty(ontology_namespace + self.snake_case(triple[1]))
                literal = OWLLiteral(str(self.snake_case(triple[2])), type_=StringOWLDatatype)
                if triple[2] in literals:
                    ax = OWLDataPropertyAssertionAxiom(subject, prop, literal)
                    onto.add_axiom(ax)

        # Step 8: Create class hierarchy if requested
        if create_class_hierarchy:
            for cls in onto.classes_in_signature():
                try:
                    superclasses, subclasses = extract_hierarchy_from_dbpedia(cls.remainder)
                except Exception:
                    continue
                if self.logging:
                    print(f"EnterpriseGraphExtractor: INFO :: For class {cls.remainder} found superclasses: "
                          f"{[IRI.create(s).remainder for s in superclasses]} and subclasses: "
                          f"{[IRI.create(s).remainder for s in subclasses]}")

                for superclass in superclasses:
                    dbpedia_class_remainder = IRI.create(superclass).remainder
                    sup_cls = OWLClass(ontology_namespace + dbpedia_class_remainder)
                    ax = OWLSubClassOfAxiom(cls, sup_cls)
                    onto.add_axiom(ax)
                for subclass in subclasses:
                    dbpedia_class_remainder = IRI.create(subclass).remainder
                    sub_cls = OWLClass(ontology_namespace + dbpedia_class_remainder)
                    ax = OWLSubClassOfAxiom(sub_cls, cls)
                    onto.add_axiom(ax)

        onto.save(path=save_path)
        if self.logging:
            print(f"EnterpriseGraphExtractor: INFO :: Successfully saved the ontology at {os.path.join(os.getcwd(),save_path)}")

        return onto

    def forward(self, text: Union[str, Path],
                ontology_namespace = "http://example.com/ontogen#",
                entity_types: List[str]=None,
                generate_types=False,
                extract_spl_triples=False,
                create_class_hierarchy=False,
                entity_clustering=True,
                use_chunking: bool = None,
                examples_for_entity_extraction=EXAMPLES_FOR_ENTITY_EXTRACTION,
                examples_for_triples_extraction=EXAMPLES_FOR_TRIPLES_EXTRACTION,
                examples_for_type_assertion=EXAMPLES_FOR_TYPE_ASSERTION,
                examples_for_type_generation=EXAMPLES_FOR_TYPE_GENERATION,
                examples_for_literal_extraction=EXAMPLES_FOR_LITERAL_EXTRACTION,
                examples_for_spl_triples_extraction=EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION,
                save_path="generated_ontology.owl") -> Ontology:
        """
        Extract an enterprise ontology from a given textual input or file.

        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            text (str or Path): Text input or file path from which the ontology will be extracted.
                Supports files: .txt, .pdf, .docx, .doc, .rtf, .html, .htm
            ontology_namespace (str): Namespace to use for the ontology.
            entity_types (List[str]): List of entity types to assign to extracted entities
                (e.g., Department, Employee, Project, Policy).
                Leave empty if generate_types is True.
            generate_types (bool): Whether to generate types for extracted entities.
            extract_spl_triples (bool): Whether to extract triples of type s-p-l where l is a numeric literal.
            create_class_hierarchy (bool): Whether to create a class hierarchy for the extracted entities.
            entity_clustering (bool): Whether to perform entity clustering to merge duplicate entities.
            use_chunking (bool): Whether to use text chunking for large documents.
                - None (default): Auto-detect based on text size (uses auto_chunk_threshold).
                - True: Force chunking even for smaller texts.
                - False: Disable chunking (may fail for very large texts).
            examples_for_entity_extraction (str): Few-shot examples for entity extraction.
            examples_for_triples_extraction (str): Few-shot examples for triple extraction.
            examples_for_type_assertion (str): Few-shot examples for type assertion.
            examples_for_type_generation (str): Few-shot examples for type generation.
            examples_for_literal_extraction (str): Few-shot examples for literal extraction.
            examples_for_spl_triples_extraction (str): Few-shot examples for s-p-l triples extraction.
            save_path (str): Path to save the generated ontology.

        Returns (Ontology): An ontology object.
        """
        if generate_types:
            assert entity_types is None, ("entity_types argument should be None "
                                          "when you want to generate types (i.e. when generate_types = True)")

        return self.generate_ontology(
            text=text,
            ontology_namespace=ontology_namespace,
            entity_types=entity_types,
            generate_types=generate_types,
            extract_spl_triples=extract_spl_triples,
            create_class_hierarchy=create_class_hierarchy,
            entity_clustering=entity_clustering,
            use_chunking=use_chunking,
            examples_for_entity_extraction=examples_for_entity_extraction,
            examples_for_triples_extraction=examples_for_triples_extraction,
            examples_for_type_assertion=examples_for_type_assertion,
            examples_for_type_generation=examples_for_type_generation,
            examples_for_literal_extraction=examples_for_literal_extraction,
            examples_for_spl_triples_extraction=examples_for_spl_triples_extraction,
            save_path=save_path
        )


