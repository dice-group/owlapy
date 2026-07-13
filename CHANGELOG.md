# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- The ontology generation pipeline now supports (#219):
  - `rdfs:label` annotations, deterministically computed from entity IRIs
  - `rdfs:comment` annotations, generated via LLM
- Test coverage for `TextChunker` and `DomainExamplesCache` in `agen_kg` (#224)

### Fixed
- Guarded `rdfs:comment` batch generation against LLM call failures, so a single failed batch no longer aborts the whole ontology generation pipeline (#223)
- Fixed an infinite loop in `TextChunker`'s fixed-size chunking strategy that could occur with `overlap > 0` once the cursor reached the end of the text (#224)
- `map_datarange` now degrades gracefully to the top datatype instead of raising `ValueError` on unrecognized data-range fillers (e.g. `owl:Thing` used where a datatype is expected), so a single malformed axiom no longer aborts hierarchy traversal in `super_classes`/`sub_classes`/`object_property_ranges` (#225, #226)

## [1.6.5] - 2026-05-26

### Added
- Timeout support for `SyncReasoner.instances()` method with configurable timeout parameter (default: 1000 seconds)
- Timeout support for `create_axiom_justifications()` method with cooperative cancellation via Java thread interruption
- Timeout support for `create_laconic_axiom_justifications()` method
- Java ExecutorService-based timeout mechanism for proper interruption of Java reasoning tasks
- Comprehensive test suite for timeout functionality in `tests/test_reasoner_timeout.py`
- CHANGELOG.md to track version history
- CONTRIBUTING.md with contributor guidelines
- CODE_OF_CONDUCT.md for community standards
- Pre-commit hooks configuration via .pre-commit-config.yaml
- Type hints support with py.typed marker
- mypy configuration for static type checking

### Changed
- Updated dependency version constraints for better compatibility
- Improved CI/CD pipeline with coverage reporting
- Modernized Python packaging configuration
- Reorganized Copilot agent files under .github/agents/owlapy/
- Refactored reasoning methods to use shared single-threaded Java executor to prevent "ExtensionManager is not reentrant" errors

### Fixed
- Resolved merge conflicts with develop branch maintaining timeout functionality
- Fixed import ordering to comply with ruff linting standards
- Resolved Python version inconsistencies in documentation and setup
- Fixed coverage report generation in CI pipeline
- Prevented concurrent Java thread access issues in HermiT and other reasoners

## [1.6.4] - 2025-05-20

### Added
- Automated ontology generation (AGen-KG) with LLM-powered knowledge extraction
- DomainGraphExtractor and OpenGraphExtractor for scalable KG generation
- Support for chunking and merging strategies for large documents
- Enhanced documentation with comprehensive examples

### Changed
- Updated dependencies to latest stable versions
- Improved class expression simplification algorithms
- Enhanced SPARQL conversion capabilities

### Fixed
- Various bug fixes in ontology reasoning
- Improved error handling in OWLAPI adaptor

## [1.6.3] - Earlier Release

### Added
- Contrastive explanation support
- Justification creation for axioms
- Embedding-based reasoner (EBR)

### Changed
- Performance optimizations for structural reasoner
- Enhanced SWRL rule support

## [1.6.2] - Earlier Release

### Added
- Class expression simplification utilities
- Neural ontology support
- Extended SPARQL conversion features

## [1.6.1] - Earlier Release

### Added
- Support for Python 3.11
- Enhanced synchronization with Java reasoners
- Improved ontology management capabilities

## [1.6.0] - Earlier Release

### Added
- SyncOntology class for thread-safe ontology operations
- Support for multiple OWL reasoners (HermiT, Pellet, JFact, Openllet, ELK)
- CSV to RDF knowledge graph conversion
- Command-line interface for ontology reasoning

### Changed
- Major refactoring of ontology API
- Improved class expression handling

---

## How to Update This Changelog

When making changes:

1. Add entries under `[Unreleased]` section
2. Use categories: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`
3. Before release, move `[Unreleased]` items to new version section with date
4. Follow format: `- Description of change (#PR-number if applicable)`

Example:
```markdown
## [1.6.5] - 2025-06-15

### Added
- New feature X for better ontology handling (#123)

### Fixed
- Bug in reasoner initialization (#124)
```
