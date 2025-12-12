from typing import List, Union, Optional
import os
import dspy
import uuid
from pathlib import Path

from owlapy.agen_kg.enterprise_examples_cache import EnterpriseExamplesCache
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
from owlapy.agen_kg.signatures import (
    Entity, Triple, TypeAssertion, TypeGeneration, Literal, SPLTriples, Domain,
    DomainSpecificFewShotGenerator, Enterprise, EnterpriseSpecificFewShotGenerator
)
from owlapy.agen_kg.helper import extract_hierarchy_from_dbpedia
from owlapy.agen_kg.domain_examples_cache import DomainExamplesCache
from graph_extractor import GraphExtractor


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
        auto_chunk_threshold: int = None,
        summarization_threshold: int = None,
        max_summary_length: int = None
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
            summarization_threshold: Character threshold for using summarization in clustering
                                    (default: 8000). When text exceeds this, summaries are
                                    generated to provide context for clustering operations.
            max_summary_length: Maximum length of summaries used for clustering context
                               (default: 3000, ~750 tokens).

        Example:
            # Configure for a model with smaller context window
            agenkg.configure_chunking(chunk_size=2000, overlap=150, strategy="sentence")

            # Configure summarization thresholds for large documents
            agenkg.configure_chunking(summarization_threshold=10000, max_summary_length=4000)
        """
        for extractor in [self.open_graph_extractor, self.domain_graph_extractor,
                         self.cross_domain_graph_extractor, self.enterprise_graph_extractor]:
            extractor.configure_chunking(
                chunk_size=chunk_size,
                overlap=overlap,
                strategy=strategy,
                auto_chunk_threshold=auto_chunk_threshold,
                summarization_threshold=summarization_threshold,
                max_summary_length=max_summary_length
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

    def generate_ontology(self, text: Union[str, Path], ontology_namespace = f"http://ontology.local/{uuid.uuid4()}#",
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
        chunk_summaries = None  # Will be populated during chunked extraction
        if use_chunking and len(chunks) > 1:
            entities, chunk_summaries = self._extract_entities_from_chunks(chunks, examples_for_entity_extraction)
        else:
            entities = self.entity_extractor(text=text, few_shot_examples=examples_for_entity_extraction).entities

        if self.logging:
            print(f"GraphExtractor: INFO  :: Generated the following entities: {entities}")

        # Step 2: Cluster entities to identify and merge duplicates
        # For chunked processing, use combined summary or generate clustering context
        if chunk_summaries:
            clustering_context = self.create_combined_summary(chunk_summaries)
        else:
            clustering_context = self.get_clustering_context(text)

        if entity_clustering:
            entity_mapping = self.cluster_entities(entities, clustering_context)
            canonical_entities = list(set(entity_mapping.values()))
        else:
            canonical_entities = entities
        if self.logging and len(entities) != len(canonical_entities):
            print(f"GraphExtractor: INFO  :: After clustering: {canonical_entities}")

        # Step 3: Extract triples using canonical entities (from chunks if needed)
        if use_chunking and len(chunks) > 1:
            triples = self._extract_triples_from_chunks(chunks, canonical_entities, examples_for_triples_extraction, chunk_summaries=chunk_summaries)
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
                    examples_for_type_assertion, examples_for_type_generation,
                    chunk_summaries=chunk_summaries
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
                try:
                    onto.add_axiom(ax)
                except Exception as e:
                    print(e)
                    print(f"Subject: {subject}, Entity Type: {entity_type}")

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
                ontology_namespace = f"http://ontology.local/{uuid.uuid4()}#",
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
        Extract an ontology from a given textual input or file.

        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            text (str or Path): Text input or file path from which the ontology will be extracted.
                Supports files: .txt, .pdf, .docx, .doc, .rtf, .html, .htm
            ontology_namespace (str): Namespace to use for the ontology.
            entity_types (List[str]): List of entity types to assign.
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
            print("DomainGraphExtractor: INFO :: Cleared all domain example caches")
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
                          ontology_namespace = f"http://ontology.local/{uuid.uuid4()}#",
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

        chunk_summaries = None
        if use_chunking and len(chunks) > 1:
            entities, chunk_summaries = self._extract_entities_from_chunks(
                chunks, examples_for_entity_extraction, "DomainGraphExtractor"
            )
        else:
            entities = self.entity_extractor(text=text, few_shot_examples=examples_for_entity_extraction).entities

        if self.logging:
            print(f"DomainGraphExtractor: INFO :: Generated the following entities: {entities}")

        # Step 4: Cluster entities to identify and merge duplicates
        # Use summaries if available from chunked extraction, or create clustering context
        if chunk_summaries:
            clustering_context = self.create_combined_summary(chunk_summaries)
        else:
            clustering_context = self.get_clustering_context(text)

        entity_mapping = self.cluster_entities(entities, clustering_context)
        canonical_entities = list(set(entity_mapping.values()))
        if self.logging and len(entities) != len(canonical_entities):
            print(f"DomainGraphExtractor: INFO :: After clustering: {canonical_entities}")

        # Step 5: Extract triples using canonical entities (from chunks if needed)
        if use_chunking and len(chunks) > 1:
            triples = self._extract_triples_from_chunks(
                chunks, canonical_entities, examples_for_triples_extraction,
                "DomainGraphExtractor", chunk_summaries
            )
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
                type_assertions = self._extract_types_from_chunks(
                    chunks, canonical_entities, entity_types, generate_types,
                    examples_for_type_assertion, examples_for_type_generation,
                    "DomainGraphExtractor", chunk_summaries
                )
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

            # Add class assertion axioms
            for pair in type_assertions:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(pair[0]))
                entity_type = OWLClass(ontology_namespace + self.snake_case(pair[1]))
                ax = OWLClassAssertionAxiom(subject, entity_type)
                try:
                    onto.add_axiom(ax)
                except Exception as e:
                    print(e)
                    print(f"Subject: {subject}, Entity Type: {entity_type}")

        # Step 9: Extract SPL triples if requested
        if extract_spl_triples:
            # Extract literals (from chunks if needed)
            if use_chunking and len(chunks) > 1:
                literals = self._extract_literals_from_chunks(
                    chunks, examples_for_literal_extraction, "DomainGraphExtractor"
                )
            else:
                literals = self.literal_extractor(text=text, few_shot_examples=examples_for_literal_extraction).l_values

            if self.logging:
                print(f"DomainGraphExtractor: INFO :: Generated the following numeric literals: {literals}")

            # Extract SPL triples (from chunks if needed)
            if use_chunking and len(chunks) > 1:
                spl_triples = self._extract_spl_triples_from_chunks(
                    chunks, canonical_entities, literals, examples_for_spl_triples_extraction,
                    "DomainGraphExtractor"
                )
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
                ontology_namespace = f"http://ontology.local/{uuid.uuid4()}#",
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
                          ontology_namespace = f"http://ontology.local/{uuid.uuid4()}#",
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
        chunk_summaries = None
        if use_chunking and len(chunks) > 1:
            entities, chunk_summaries = self._extract_entities_from_chunks(
                chunks, examples_for_entity_extraction, "CrossDomainGraphExtractor"
            )
        else:
            entities = self.entity_extractor(text=text, few_shot_examples=examples_for_entity_extraction).entities

        if self.logging:
            print(f"CrossDomainGraphExtractor: INFO :: Generated the following entities: {entities}")

        # Step 2: Cluster entities
        if chunk_summaries:
            clustering_context = self.create_combined_summary(chunk_summaries)
        else:
            clustering_context = self.get_clustering_context(text)

        if entity_clustering:
            entity_mapping = self.cluster_entities(entities, clustering_context)
            canonical_entities = list(set(entity_mapping.values()))
        else:
            canonical_entities = entities

        if self.logging and len(entities) != len(canonical_entities):
            print(f"CrossDomainGraphExtractor: INFO :: After clustering: {canonical_entities}")

        # Step 3: Extract triples (from chunks if needed)
        if use_chunking and len(chunks) > 1:
            triples = self._extract_triples_from_chunks(
                chunks, canonical_entities, examples_for_triples_extraction,
                "CrossDomainGraphExtractor", chunk_summaries
            )
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
                    examples_for_type_assertion, examples_for_type_generation,
                    "CrossDomainGraphExtractor", chunk_summaries
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
                literals = self._extract_literals_from_chunks(
                    chunks, examples_for_literal_extraction, "CrossDomainGraphExtractor"
                )
            else:
                literals = self.literal_extractor(text=text, few_shot_examples=examples_for_literal_extraction).l_values

            if self.logging:
                print(f"CrossDomainGraphExtractor: INFO :: Generated the following numeric literals: {literals}")

            if use_chunking and len(chunks) > 1:
                spl_triples = self._extract_spl_triples_from_chunks(
                    chunks, canonical_entities, literals, examples_for_spl_triples_extraction,
                    "CrossDomainGraphExtractor"
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
                ontology_namespace = f"http://ontology.local/{uuid.uuid4()}#",
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
    def __init__(self, enable_logging=False, enterprise_context: Optional[str] = None, examples_cache_dir: Optional[str] = None):
        """
        Initialize the EnterpriseGraphExtractor.

        Args:
            enable_logging: Whether to enable logging.
            enterprise_context: Optional enterprise context (e.g., 'Acme Corp', 'healthcare').
                              If not provided, will be automatically detected from text.
            examples_cache_dir: Directory to cache enterprise-specific examples. If None, uses current working directory.
        """
        super().__init__(enable_logging)
        self.enterprise_context = enterprise_context
        self.enterprise_detector = dspy.Predict(Enterprise)
        self.few_shot_generator = dspy.Predict(EnterpriseSpecificFewShotGenerator)
        self.entity_extractor = dspy.Predict(Entity)
        self.triples_extractor = dspy.Predict(Triple)
        self.type_asserter = dspy.Predict(TypeAssertion)
        self.type_generator = dspy.Predict(TypeGeneration)
        self.literal_extractor = dspy.Predict(Literal)
        self.spl_triples_extractor = dspy.Predict(SPLTriples)
        # Initialize examples cache manager
        self.examples_cache = EnterpriseExamplesCache(cache_dir=examples_cache_dir)

    def generate_enterprise_specific_examples(self, enterprise: str):
        """
        Generate enterprise-specific few-shot examples for all task types.

        Automatically caches examples to disk for future reuse. If examples have been
        previously generated for the enterprise, they will be loaded from cache.

        Args:
            enterprise: The enterprise context for which to generate examples.

        Returns:
            Dictionary containing few-shot examples for each task type, keyed by:
            'entity_extraction', 'triples_extraction', 'type_assertion', 'type_generation',
            'literal_extraction', 'triples_with_numeric_literals_extraction'
        """
        # Check if examples are already cached
        cached_examples = self.examples_cache.load_examples(enterprise)
        if cached_examples is not None:
            if self.logging:
                cache_file = self.examples_cache.get_cache_file_path(enterprise)
                print(f"EnterpriseGraphExtractor: INFO :: Loaded cached examples for enterprise '{enterprise}' from {cache_file}")
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
            print(f"EnterpriseGraphExtractor: INFO :: Generating enterprise-specific few-shot examples for enterprise: {enterprise}")

        for task_type in task_types:
            result = self.few_shot_generator(
                enterprise=enterprise,
                task_type=task_type,
                num_examples=2
            )
            examples[task_type] = result.few_shot_examples
            if self.logging:
                print(f"EnterpriseGraphExtractor: INFO :: Generated examples for {task_type}")

        # Save examples to cache
        if self.examples_cache.save_examples(enterprise, examples):
            if self.logging:
                cache_file = self.examples_cache.get_cache_file_path(enterprise)
                print(f"EnterpriseGraphExtractor: INFO :: Cached examples for enterprise '{enterprise}' to {cache_file}")
        else:
            if self.logging:
                print(f"EnterpriseGraphExtractor: WARNING :: Failed to cache examples for enterprise '{enterprise}'")

        return examples

    def clear_enterprise_cache(self, enterprise: str) -> bool:
        """
        Clear the cached examples for a specific enterprise.

        Args:
            enterprise: The enterprise context for which to clear cached examples.

        Returns:
            True if the cache was cleared successfully, False otherwise.
        """
        success = self.examples_cache.clear_enterprise_cache(enterprise)
        if success and self.logging:
            print(f"EnterpriseGraphExtractor: INFO :: Cleared cache for enterprise '{enterprise}'")
        return success

    def clear_all_enterprise_caches(self) -> bool:
        """
        Clear all cached enterprise examples.

        Returns:
            True if all caches were cleared successfully, False otherwise.
        """
        success = self.examples_cache.clear_all_caches()
        if success and self.logging:
            print("EnterpriseGraphExtractor: INFO :: Cleared all enterprise example caches")
        return success

    def list_cached_enterprises(self) -> list:
        """
        List all enterprises that have cached examples.

        Returns:
            List of enterprise context names with cached examples.
        """
        enterprises = self.examples_cache.list_cached_enterprises()
        if self.logging and enterprises:
            print(f"EnterpriseGraphExtractor: INFO :: Cached enterprises: {', '.join(enterprises)}")
        return enterprises

    def is_enterprise_cached(self, enterprise: str) -> bool:
        """
        Check if examples exist for an enterprise in the cache.

        Args:
            enterprise: The enterprise context to check.

        Returns:
            True if examples are cached for the enterprise, False otherwise.
        """
        return self.examples_cache.examples_exist(enterprise)

    def get_cache_file_path(self, enterprise: str) -> str:
        """
        Get the full path to the cache file for an enterprise.

        Args:
            enterprise: The enterprise name.

        Returns:
            String path to the cache file.
        """
        return self.examples_cache.get_cache_file_path(enterprise)

    def generate_ontology(self, text: Union[str, Path],
                          ontology_namespace = f"http://ontology.local/{uuid.uuid4()}#",
                          entity_types: List[str]=None,
                          generate_types=False,
                          extract_spl_triples=False,
                          create_class_hierarchy=False,
                          entity_clustering=True,
                          use_chunking: bool = None,
                          examples_for_entity_extraction=None,
                          examples_for_triples_extraction=None,
                          examples_for_type_assertion=None,
                          examples_for_type_generation=None,
                          examples_for_literal_extraction=None,
                          examples_for_spl_triples_extraction=None,
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
        chunk_summaries = None
        if use_chunking and len(chunks) > 1:
            entities, chunk_summaries = self._extract_entities_from_chunks(
                chunks, examples_for_entity_extraction, "EnterpriseGraphExtractor"
            )
        else:
            entities = self.entity_extractor(text=text, few_shot_examples=examples_for_entity_extraction).entities

        if self.logging:
            print(f"EnterpriseGraphExtractor: INFO :: Generated the following entities: {entities}")

        # Step 2: Cluster entities
        if chunk_summaries:
            clustering_context = self.create_combined_summary(chunk_summaries)
        else:
            clustering_context = self.get_clustering_context(text)

        if entity_clustering:
            entity_mapping = self.cluster_entities(entities, clustering_context)
            canonical_entities = list(set(entity_mapping.values()))
        else:
            canonical_entities = entities

        if self.logging and len(entities) != len(canonical_entities):
            print(f"EnterpriseGraphExtractor: INFO :: After clustering: {canonical_entities}")

        # Step 3: Extract triples (from chunks if needed)
        if use_chunking and len(chunks) > 1:
            triples = self._extract_triples_from_chunks(
                chunks, canonical_entities, examples_for_triples_extraction,
                "EnterpriseGraphExtractor", chunk_summaries
            )
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
                    examples_for_type_assertion, examples_for_type_generation,
                    "EnterpriseGraphExtractor", chunk_summaries
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
                literals = self._extract_literals_from_chunks(
                    chunks, examples_for_literal_extraction, "EnterpriseGraphExtractor"
                )
            else:
                literals = self.literal_extractor(text=text, few_shot_examples=examples_for_literal_extraction).l_values

            if self.logging:
                print(f"EnterpriseGraphExtractor: INFO :: Generated the following numeric literals: {literals}")

            if use_chunking and len(chunks) > 1:
                spl_triples = self._extract_spl_triples_from_chunks(
                    chunks, canonical_entities, literals, examples_for_spl_triples_extraction,
                    "EnterpriseGraphExtractor"
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

        # Step 9: Save ontology
        onto.save(path=save_path)
        if self.logging:
            print(f"EnterpriseGraphExtractor: INFO :: Successfully saved the ontology at {os.path.join(os.getcwd(),save_path)}")

        return onto

    def forward(self, text: Union[str, Path],
                ontology_namespace = f"http://ontology.local/{uuid.uuid4()}#",
                entity_types: List[str]=None,
                generate_types=False,
                extract_spl_triples=False,
                create_class_hierarchy=False,
                entity_clustering=True,
                use_chunking: bool = None,
                examples_for_entity_extraction=None,
                examples_for_triples_extraction=None,
                examples_for_type_assertion=None,
                examples_for_type_generation=None,
                examples_for_literal_extraction=None,
                examples_for_spl_triples_extraction=None,
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


