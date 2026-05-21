# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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

### Fixed
- Resolved Python version inconsistencies in documentation and setup
- Fixed coverage report generation in CI pipeline

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
