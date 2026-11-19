---
paths:
  - "owlapy/agen_kg/**/*.py"
  - "examples/ag-gen_example.py"
---

# AGen-KG: LLM-Based Knowledge Graph Generation

Requires `dspy` (`pip install owlapy[agentic]`). Pipeline: load text -> extract
entities/relations/types via LLM -> cluster/dedupe relations -> generate class
hierarchy + individuals -> save `.owl`.

```python
from owlapy.agen_kg import AGenKG
from owlapy.owl_ontology import RDFLibOntology

agent = AGenKG(
    model="gpt-4o", api_key="<KEY>", api_base="https://models.github.ai/inference",
    temperature=0.1,     # 0.0-0.2 for factual extraction
    seed=42,              # reproducibility
    max_tokens=6000,      # default 4000; raise for large/complex docs
    enable_logging=True,  # strongly recommended
    cache=True,           # avoid redundant LLM calls during iteration
)
agent.generate_ontology(text="path/or/string", ontology_type="domain", save_path="out.owl",
                        ontology=RDFLibOntology("http://example.com/ontogen", load=False))  # owlready2-free (#310)
```

`ontology_type`: `"domain"` (auto-detects domain, generates domain-specific few-shot
examples — best for structured docs) vs `"open"` (no domain assumption, generic prompts).

## Chunking Large Documents

```python
agent.configure_chunking(chunk_size=3000, overlap=200, strategy="sentence",
                          auto_chunk_threshold=4000, summarization_threshold=8000,
                          max_summary_length=3000)
```

## Internals

`owlapy.agen_kg.graph_extracting_models` has `DomainGraphExtractor` (caches few-shot
examples in `path_hidden/domain_examples_<domain>.json`) and `OpenGraphExtractor`.
`owlapy.agen_kg.chunking_models` implements the chunking strategies.

## Constraints

- `save_path` must end in `.owl` (RDF/XML)
- Always pass `ontology=RDFLibOntology(iri, load=False)` (or a `SyncOntology`) in new code: without it the extractors build a deprecated owlready2 `Ontology` and emit a `FutureWarning` (or fall back to `RDFLibOntology` when owlready2 isn't installed -- the `agentic` extra doesn't install it). The default switches to `RDFLibOntology` in 2.0
- Very short texts (<50 words) yield poor extraction quality
- `temperature=0.1, seed=42` is the recommended reproducible default
- Any OpenAI-compatible endpoint works (OpenAI, Azure OpenAI, GitHub Models, Ollama, vLLM) — just swap `api_base`/`model`
- Wrap `generate_ontology` calls in try/except for `FileNotFoundError`, `UnicodeDecodeError`, `ConnectionError`; validate the output ontology isn't empty before trusting it
