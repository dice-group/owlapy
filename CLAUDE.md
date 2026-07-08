# owlapy

Pure-Python framework for OWL 2 ontology engineering, semantic reasoning, and
LLM-based knowledge graph generation. Developed by the DICE Research Group,
Paderborn University. Current version: see `owlapy/__init__.py`.

Deep API documentation already exists in `markdown_docs/` (core concepts,
ontology management, reasoning, common patterns, API reference) — read the
relevant file there before explaining owlapy APIs at length.

## Environment

Always use the `temp_owlapy` conda environment:

```bash
conda create -n temp_owlapy python=3.11 --no-default-packages
conda activate temp_owlapy
pip install -e '.[dev]'
```

Python 3.11 is required (matches CI and the README install command, not 3.10.x).

## Lint, Test, Build

```bash
# Lint (always run before committing)
ruff check owlapy --line-length=200
ruff check owlapy --line-length=200 --fix --unsafe-fixes

# Tests (download KGs.zip once, see below)
PYTHONPATH=. pytest --ignore=tests/test_z_do_last_ebr_retrieval.py -p no:warnings

# Coverage
coverage run -m pytest --ignore=tests/test_z_do_last_ebr_retrieval.py -p no:warnings -x
coverage report -m
```

- Test KGs (one-time): `wget https://files.dice-research.org/projects/Ontolearn/KGs.zip -O ./KGs.zip && unzip KGs.zip`
- `tests/test_z_do_last_ebr_retrieval.py` is slow and excluded from the default run by convention (runs last, retrains embeddings)
- Test files: `tests/test_*.py`, functions `test_*` (pytest, `pythonpath = ["."]`, configured in `pyproject.toml`)
- mypy config lives in `pyproject.toml` (`check_untyped_defs = true`, `disallow_untyped_defs = false` — gradual typing, tighten over time, don't relax)

## Project Structure

```
owlapy/
├── class_expression/     # OWL class expression types (see .claude/rules/class-expressions.md)
├── entities/, abstracts/ # Entity base types and abstract interfaces
├── agen_kg/               # LLM-based ontology generation, AGenKG (see .claude/rules/kg-generation.md)
├── scripts/               # CLI entry points: `owlapy`, `owlapy-serve`
├── jar_dependencies/      # Bundled Java .jars for HermiT, Pellet, ELK, JFact, Openllet
├── owl_ontology.py         # SyncOntology, Ontology, NeuralOntology
├── owl_reasoner.py         # StructuralReasoner, SyncReasoner
├── owl_reasoner_rdflib.py  # RDFLibReasoner (pure Python)
├── owl_axiom.py             # All OWL axiom types
├── converter.py             # OWL -> SPARQL
├── parser.py                 # DL / Manchester -> OWL
├── render.py                  # OWL -> DL / Manchester
├── swrl.py                     # SWRL rules
├── owlapi_mapper.py, owlapi_dlsyntax.py  # Java OWLAPI bridge
└── utils.py                     # CESimplifier, NNF, similarity metrics
tests/                    # pytest suite, one file per module/feature
examples/                 # Runnable usage scripts (mirrors markdown_docs topics)
markdown_docs/            # LLM-friendly deep-dive docs — check here first for API detail
KGs/                       # Test ontologies (downloaded, not committed)
.github/agents/            # Legacy GitHub Copilot agent specs — superseded by .claude/rules/
```

## Key Design Principles

- Prefer `SyncOntology` over `Ontology` for new code (thread-safe wrapper)
- Never pass raw strings to reasoners — wrap in the appropriate OWL object first; use full IRI strings when constructing entities
- Always call `stopJVM()` (from `owlapy.static_funcs`) after using any Java-backed reasoner (`SyncReasoner`, OWLAPI bridge). `StructuralReasoner` is pure Python and needs no JVM.
- Never guess owlapy import paths — verify against the actual module (see `.claude/rules/` for the domain you're touching)

## Versioning

Version is tracked in **two places** and must stay in sync:
- `owlapy/__init__.py` → `__version__`
- `setup.py` → `version=`

## Dependency Notes

- `dicee` pinned `>=0.3.2,<0.4.0`; `dspy` pinned `>=3.0.3,<4.0.0` (verified against 3.1.3) — do not switch to strict `==` pinning
- Java reasoners require JPype1 + bundled jars in `owlapy/jar_dependencies/`
- `agen_kg` requires `dspy` — install via `pip install owlapy[agentic]`

## Git Workflow

Gitflow: `main` (releases) ← `develop` (integration) ← `feature/*` / `fix/*` / `chore/*`
branches. Open PRs against `develop`, not `main`. Release process (version bump in
both files, CHANGELOG.md update, merge develop → main, tag, build, `twine upload`)
is documented in `.github/copilot-instructions.md` if you're driving a release.

## Rules

Domain-specific API patterns and constraints load automatically from
`.claude/rules/` when you touch matching files (class expressions, ontology
management, reasoning, syntax conversion, SWRL/OWLAPI, KG generation).
