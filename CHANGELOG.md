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
- `OWLAnonymousIndividual` class for representing anonymous (blank-node) individuals, with a `NodeID` helper for node-id generation/normalization, and OWLAPI bridge mapping so anonymous individuals no longer break `get_abox_axioms()`/class/property assertion retrieval (#217)
- `owlapy.marked_entity_generator_converter`: `QueryGenerator` (subclass of `Owl2SparqlConverter`) and `owl_expression_to_class_query`/`owl_expression_to_negated_class_query`/`owl_expression_to_property_query` helpers, which generate SPARQL queries that *discover* classes/properties (with positive/negative hit counts) at a marked position in a class expression, ported from DL-Learner's Java `Suggestor`. Backs PruneCEL's oracle-based refinement operator.
- `axiom.signature()` / `class_expression.signature()`, returning the set of named entities (classes, object/data properties, individuals, datatypes) referenced by an `OWLAxiom`/`OWLClassExpression`/`OWLDataRange`, via the new `owlapy.utils.SignatureExtractor`. Covers all class expression/data range constructs and a core set of axiom types (declaration, class/property assertions, sub-class-of, equivalent/disjoint classes, property domain/range); remaining axiom types raise `NotImplementedError` and are tracked in #231 (#230)
- `SyncOntology.get_prefixes()`/`set_prefix()`/`remove_prefix()` for declaring, modifying and removing prefix -> namespace IRI mappings, honoured by `save()` for both OWL API–backed formats (RDF/XML, OWL/XML, Turtle, Functional Syntax, Manchester Syntax) and rdflib-backed formats (Turtle, N3, TriG, JSON-LD) (#229)
- `DLSyntaxParser`/`ManchesterOWLSyntaxParser` (and `dl_to_owl_expression`/`manchester_to_owl_expression`) now resolve prefixed names (`prefix:localName`), via a `prefixes` argument; `owl:`, `rdf:`, `rdfs:` and `xsd:` are resolved out of the box and an empty prefix (`:localName`) falls back to the parser's default namespace (#229)
- `RDFLibReasoner` now implements the full `AbstractOWLReasoner` interface: `sub/super_object_properties`, `sub/super_data_properties`, `data_property_domains`, `object_property_domains`, `object_property_ranges`, `equivalent_object_properties`, `equivalent_data_properties`, `disjoint_object_properties`, `disjoint_data_properties`, `different_individuals`, and `data_property_values` (previously hard stubs returning `iter([])`), including support for both pairwise and RDF-list-based (`owl:AllDisjointProperties`/`owl:AllDifferent`) axiom forms. Brings it to parity with `StructuralReasoner` without owlready2's punning-related crashes (#242, #205)
- `RDFLibReasoner` constructor gains `negation_default` (open- vs closed-world handling of `OWLObjectComplementOf` in `instances()`) and `sub_properties` (whether `instances()` also matches individuals connected via a sub-property of the property used in a restriction), matching `StructuralReasoner`'s equivalent constructor parameters (#242)
- `owl_expression_to_sparql`/`Owl2SparqlConverter` gain optional `negation_default`, `sub_property_resolver`, `inverse_property_resolver`, and `subclass_resolver` parameters backing `RDFLibReasoner`'s corresponding always-on/opt-in behaviors; default behavior for existing callers is unchanged (#242)
- `owl_expression_to_sparql`/`Owl2SparqlConverter` now translate `OWLDataIntersectionOf`, `OWLDataUnionOf`, and `OWLDataComplementOf` data ranges (previously unimplemented, raising `NotImplementedError`) (#242)

### Changed
- Core library now emits diagnostics through the standard `logging` module instead of `print()`. Progress/status messages log at `INFO`, recoverable issues at `WARNING`, and low-level dumps at `DEBUG`, across `owl_ontology.py`, `owl_reasoner.py`, `render.py`, `utils.py`, and `util_owl_static_funcs.py`. A `NullHandler` is attached to the top-level `owlapy` logger so nothing is printed unless the host application configures logging (opt in via `logging.getLogger("owlapy").setLevel(logging.INFO)`).
- The `agen_kg` LLM pipeline now also logs through the `logging` module instead of `print()`. The existing `enable_logging` flag keeps its meaning: when set, progress messages are emitted via per-module loggers under `owlapy.agen_kg` and a console handler is attached so output stays visible without extra configuration; `except`-block diagnostics now use `logger.exception(...)` and include tracebacks. Host applications that configure logging themselves can control verbosity via the `owlapy` logger hierarchy.
- Added `IMPROVEMENTS.md`, a prioritized plan of readability, performance, documentation, and feature improvements for the library
- Ignored generated/scratch artifacts (`demo.owl`, `inferred_axioms_ontology.owl`, `iris_dataset.csv`, `tests/saved_formats/`) that examples and tests write to the repo root

### Fixed
- `StructuralReasoner.object_property_values()` no longer crashes with `AttributeError: 'Or' object has no attribute 'iri'` on ontologies that illegally pun an entity as multiple property types (e.g. `KGs/Biopax/biopax.owl`, where `glycolysis#DELTA-G` is declared as both `owl:ObjectProperty` and `owl:AnnotationProperty`). owlready2's load-time punning repair can make values of unrelated properties come back as internal class-expression nodes (`owlready2.Or`) instead of individuals; these are now skipped with a warning (emitted once per property) that points at the punning as the root cause, instead of crashing or silently dropping values (#242, supersedes #236)
- `owl_expression_to_sparql` no longer requires individuals to be explicitly asserted `rdf:type owl:Thing` when `OWLThing` is used as a nested filler (e.g. `∃r.⊤`), which previously made such queries wrongly return no results; also fixes `RDFLibReasoner.instances(OWLThing)`, which now returns `individuals_in_signature()` instead of an always-empty SPARQL query (#242)
- `RDFLibReasoner.instances(SomeClass)` (and every named-class membership check inside a larger expression) previously silently returned too few results whenever `SomeClass` had subclasses and individuals were typed only at the leaf level (confirmed on `KGs/Mutagenesis/mutagenesis.owl`'s `Atom` class, 64 subclasses, 0 direct matches). Now expands to the full subclass closure via a bounded SPARQL `VALUES` clause (#242)
- `OWLObjectInverseOf` is now entailed via a declared `owl:inverseOf` axiom even when the inverse property has no physically-asserted triples of its own, in both `RDFLibReasoner.instances()` and `object_property_values()` (#242)
- `OWLObjectMaxCardinality` (and any cardinality restriction with `cardinality=0`) no longer times out on non-trivial ontologies. The `FILTER NOT EXISTS`/`OPTIONAL` pattern needed to detect "zero matching relations" is evaluated by rdflib's SPARQL engine as an expensive per-candidate correlated check; this is now computed set-theoretically in Python using only the fast, uncorrelated `OWLObjectMinCardinality` path (#242)
- Corrupted (mojibake) emoji in the README "Documentation" and "Examples" section headers, and stale version badges (now 1.6.6)
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
