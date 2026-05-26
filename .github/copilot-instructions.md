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

## Release Process

### Creating a New Release

Follow this complete workflow to release a new version to PyPI:

#### 1. Create Release Branch

```bash
# Ensure you're on develop and up-to-date
git checkout develop
git pull origin develop

# Create a release branch
git checkout -b feature/release-X.Y.Z
```

#### 2. Update Version Numbers

Update version in **both** files (keep in sync):

```bash
# owlapy/__init__.py
__version__ = 'X.Y.Z'

# setup.py
version="X.Y.Z"
```

#### 3. Update CHANGELOG.md

Add a new version section following [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features and functionality

### Changed
- Updates to existing features

### Fixed
- Bug fixes and corrections
```

#### 4. Add Tests for New Features

- Create test files in `tests/` directory
- Ensure all tests pass: `PYTHONPATH=. pytest --ignore=tests/test_z_do_last_ebr_retrieval.py -p no:warnings`
- Run linter: `ruff check owlapy --line-length=200 --fix --unsafe-fixes`

#### 5. Commit and Push Release Branch

```bash
git add owlapy/__init__.py setup.py CHANGELOG.md tests/
git commit -m "chore: bump version to X.Y.Z and add tests

- Increment version from A.B.C to X.Y.Z
- Add comprehensive test suite
- Update CHANGELOG.md with release notes"

git push -u origin feature/release-X.Y.Z
```

#### 6. Merge to Develop

```bash
git checkout develop
git merge feature/release-X.Y.Z --no-ff -m "Merge feature/release-X.Y.Z into develop

Release version X.Y.Z with [feature description]"

git push origin develop
```

#### 7. Merge to Main

```bash
git checkout main
git pull origin main
git merge develop --no-ff -m "Release vX.Y.Z: Merge develop into main

This release includes:
- [Feature 1]
- [Feature 2]
- Bug fixes and improvements"

git push origin main
```

#### 8. Create Git Tag

```bash
git tag -a vX.Y.Z -m "Release version X.Y.Z

- [Feature 1]
- [Feature 2]
- Bug fixes and documentation improvements"

git push origin vX.Y.Z
```

#### 9. Build and Publish to PyPI

```bash
# Clean old builds
rm -rf build/ dist/ *.egg-info owlapy.egg-info

# Install/upgrade build tools
pip install --upgrade build twine

# Build distributions
python -m build

# Verify build
ls -lh dist/
twine check dist/*

# Upload to PyPI (requires API token in ~/.pypirc)
twine upload dist/*
```

#### 10. Configure PyPI Credentials (One-time Setup)

Create `~/.pypirc` with your API token:

```ini
[pypi]
username = __token__
password = pypi-YOUR_API_TOKEN_HERE
```

Set secure permissions:

```bash
chmod 600 ~/.pypirc
```

### Post-Release Verification

```bash
# Verify package is available on PyPI
pip install --upgrade owlapy

# Check installed version
python -c "import owlapy; print(owlapy.__version__)"

# View package page
# https://pypi.org/project/owlapy/X.Y.Z/
```

### Common Issues

**Twine check fails with metadata errors:**
- Upgrade twine: `pip install --upgrade twine`
- Use `python -m build` instead of `python setup.py bdist_wheel sdist`

**Merge conflicts:**
- When merging branches with conflicts, prefer keeping alphabetized imports while preserving functionality
- Always run `ruff check --fix --unsafe-fixes` after resolving conflicts

**Version mismatch:**
- Ensure version is updated in both `owlapy/__init__.py` AND `setup.py`
- Verify with: `grep -r "version.*=" owlapy/__init__.py setup.py`
