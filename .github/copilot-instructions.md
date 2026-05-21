# OWLAPY Developer Guidelines

## Development Environment

**Always use the `temp_owlapy` conda environment when working on this project:**

```bash
conda create -n temp_owlapy python=3.11 --no-default-packages
conda activate temp_owlapy
pip install -e '.[dev]'
```

> The README install command uses `python=3.11` — not `3.10.13`. The CI also targets `3.11`.

## Running the Linter (ruff)

**Always run ruff before committing:**

```bash
# Check for issues
ruff check owlapy --line-length=200

# Auto-fix all issues (includes trailing whitespace W291/W293)
ruff check owlapy --line-length=200 --fix --unsafe-fixes
```

**Important ruff notes:**
- `--output-format=text` is **invalid**. Use `concise`, `full`, `json`, `json-lines`, `junit`, `grouped`, `github`, `gitlab`, `pylint`, `rdjson`, `azure`, or `sarif`
- For a summary of violations, use JSON output piped to python3:

```bash
ruff check owlapy --line-length=200 --output-format=json 2>&1 | python3 -c "
import json, sys
from collections import Counter
data = json.load(sys.stdin)
print(f'Total violations: {len(data)}')
for code, n in Counter(v['code'] for v in data).most_common():
    print(f'  {code}: {n}')
"
```

## Running Tests

```bash
# Download test KGs first (one-time)
wget https://files.dice-research.org/projects/Ontolearn/KGs.zip -O ./KGs.zip && unzip KGs.zip

# Run all tests (excluding slow EBR test)
PYTHONPATH=. pytest --ignore=tests/test_z_do_last_ebr_retrieval.py -p no:warnings

# Run with coverage
coverage run -m pytest --ignore=tests/test_z_do_last_ebr_retrieval.py -p no:warnings -x
coverage report -m
```

## Project Structure

```
owlapy/
├── class_expression/       # OWL class expression types
├── abstracts/              # Abstract base classes
├── agen_kg/                # AGen-KG: LLM-based ontology generation
├── scripts/                # CLI entry points (owlapy, owlapy-serve)
├── jar_dependencies/       # Java .jar files for HermiT, Pellet, etc.
├── owl_ontology.py         # SyncOntology, Ontology, NeuralOntology
├── owl_reasoner.py         # StructuralReasoner, SyncReasoner
├── owl_axiom.py            # All OWL axiom types
├── converter.py            # OWL → SPARQL conversion
├── parser.py               # DL / Manchester → OWL parsing
├── render.py               # OWL → DL / Manchester rendering
└── utils.py                # CESimplifier, NNF, similarity metrics
tests/                      # pytest test suite
examples/                   # Runnable usage examples
KGs/                        # Test ontology knowledge graphs (downloaded separately)
.github/
├── agents/                 # GitHub Copilot custom agents
└── workflows/test.yml      # CI pipeline
```

## Versioning

Current version is tracked in **two places** — keep them in sync:
- `owlapy/__init__.py` → `__version__ = 'X.Y.Z'`
- `setup.py` → `version="X.Y.Z"`

## Dependency Notes

- `dicee` is pinned to `>=0.3.2,<0.4.0` — do not use strict `==` pinning
- `dspy` is pinned to `>=3.0.3,<4.0.0` — last verified compatible version is 3.1.3
- Java reasoners (HermiT, Pellet, ELK, JFact, Openllet) require JPype1 and the bundled JARs in `owlapy/jar_dependencies/`
- `agen_kg` module requires `dspy` — install with `pip install owlapy[agentic]`

## Key Design Principles

- Always use `SyncOntology` (not `Ontology`) for new code
- Always call `stopJVM()` after using any Java-backed `SyncReasoner`
- Use full IRI strings when constructing OWL entities
- Never pass raw strings to reasoners — wrap them in the appropriate OWL object first
