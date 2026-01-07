import dspy
from owlapy.agen_kg.graph_extracting_models import (OpenGraphExtractor, DomainGraphExtractor)

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
        for extractor in [self.open_graph_extractor, self.domain_graph_extractor]:
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
        for extractor in [self.open_graph_extractor, self.domain_graph_extractor]:
            extractor.configure_chunking_for_model(
                max_context_tokens=max_context_tokens,
                prompt_overhead_tokens=prompt_overhead_tokens
            )

    def generate_ontology(self, text, ontology_type, query, **kwargs):

        assert ontology_type in ["domain", "open"], "ontology_type must be one of 'domain' or 'open'"
        if ontology_type == "open":
            return self.open_graph_extractor.generate_ontology(text=text, query=query, **kwargs)
        elif ontology_type == "domain":
            return self.domain_graph_extractor.generate_ontology(text=text,query=query, **kwargs)
        return None
