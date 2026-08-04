# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- README's "Production-Ready Reasoning" bullets and the `markdown_docs`/`.claude/rules` reasoner docs now link out to per-reasoner sections instead of naming reasoners as plain text, and document the previously-undocumented `EBR` (Embedding-Based Reasoner) and its `NeuralOntology` counterpart, which weren't mentioned anywhere outside code docstrings. The README's "Python-native Reasoners" bullet also gained a link to `RDFLibReasoner`, which it previously omitted entirely despite being the recommended pure-Python reasoner.
- `RDFLibOntology` now implements a write API: `add_axiom()`/`remove_axiom()` (accepting a single `OWLAxiom` or an iterable) support declarations, class/object-property/data-property assertions, `SubClassOf`, `EquivalentClasses`, `DisjointClasses`, sub-property axioms, property domain/range axioms, and the property characteristic axioms (Functional/InverseFunctional/Symmetric/Asymmetric/Transitive/Reflexive/Irreflexive) between/on *named* entities -- axiom types or complex (blank-node) expressions it can't represent raise `NotImplementedError` naming what's supported. Adding an axiom auto-declares any entity it references that isn't already declared, so it's immediately visible to the read API. `save()` serializes via rdflib's own writer (`document_format` accepts rdflib's native format names plus the OWL-API-style aliases `Ontology`/`SyncOntology`'s `save()` already use). `RDFLibOntology(iri, load=False)` now creates a blank ontology at the given IRI instead of raising `NotImplementedError` (#205)
- `RDFLibOntology`/`RDFLibReasoner` are now documented and repositioned as the actively-maintained, owlready2/JVM-free path (`markdown_docs/02_core_concepts.md`, `05_reasoning.md`, `09_api_reference.md`, `.claude/rules/reasoning.md`, `.claude/rules/ontology-management.md`), including a previously-missing `RDFLibOntology` entry in the API reference and a correction of `SyncOntology`'s documented backend (Java OWL API, not owlready2). `StructuralReasoner`/`Ontology` (owlready2-backed) are now explicitly marked legacy, pointing at `RDFLibReasoner`/`RDFLibOntology` (#205). Constructing a `StructuralReasoner` now emits a `DeprecationWarning`.
- `RDFLibOntology` now implements its full read API: `classes_in_signature`, `data_properties_in_signature`, `object_properties_in_signature`, `properties_in_signature`, `individuals_in_signature`, `get_abox_axioms_between_individuals`, `get_abox_axioms_between_individuals_and_classes`, `equivalent_classes_axioms`, `data_property_domain_axioms`/`range_axioms`, `object_property_domain_axioms`/`range_axioms`, and `get_ontology_id`, plus `__eq__`/`__hash__`/`__repr__` (previously hard stubs raising `NotImplementedError`). `general_class_axioms()` still raises `NotImplementedError`, since it would require reconstructing complex class expressions from blank-node RDF structures, which this triple-based loader does not support. The write API (`add_axiom`/`remove_axiom`/`save`) remains unimplemented.
- CI step in `.github/workflows/test.yml` that fails the build if `owlapy/__init__.py`'s `__version__` and `setup.py`'s `version=` disagree, enforcing the dual-source-of-truth documented in `CLAUDE.md` (IMPROVEMENTS.md 5.2)
- The ontology generation pipeline now supports (#219):
  - `rdfs:label` annotations, deterministically computed from entity IRIs
  - `rdfs:comment` annotations, generated via LLM
- Test coverage for `TextChunker` and `DomainExamplesCache` in `agen_kg` (#224)
- `OWLAnonymousIndividual` class for representing anonymous (blank-node) individuals, with a `NodeID` helper for node-id generation/normalization, and OWLAPI bridge mapping so anonymous individuals no longer break `get_abox_axioms()`/class/property assertion retrieval (#217)
- `owlapy.marked_entity_generator_converter`: `QueryGenerator` (subclass of `Owl2SparqlConverter`) and `owl_expression_to_class_query`/`owl_expression_to_negated_class_query`/`owl_expression_to_property_query` helpers, which generate SPARQL queries that *discover* classes/properties (with positive/negative hit counts) at a marked position in a class expression, ported from DL-Learner's Java `Suggestor`. Backs PruneCEL's oracle-based refinement operator.
- `axiom.signature()` / `class_expression.signature()`, returning the set of named entities (classes, object/data properties, individuals, datatypes) referenced by an `OWLAxiom`/`OWLClassExpression`/`OWLDataRange`, via the new `owlapy.utils.SignatureExtractor`. Covers all class expression/data range constructs and every `OWLAxiom` subtype, including property characteristics, sub-property/property-chain axioms, has-key, disjoint union, datatype definition, (un)equal individuals, and annotation axioms (#230, #231)
- `SyncOntology.get_prefixes()`/`set_prefix()`/`remove_prefix()` for declaring, modifying and removing prefix -> namespace IRI mappings, honoured by `save()` for both OWL API–backed formats (RDF/XML, OWL/XML, Turtle, Functional Syntax, Manchester Syntax) and rdflib-backed formats (Turtle, N3, TriG, JSON-LD) (#229)
- `DLSyntaxParser`/`ManchesterOWLSyntaxParser` (and `dl_to_owl_expression`/`manchester_to_owl_expression`) now resolve prefixed names (`prefix:localName`), via a `prefixes` argument; `owl:`, `rdf:`, `rdfs:` and `xsd:` are resolved out of the box and an empty prefix (`:localName`) falls back to the parser's default namespace (#229)
- `RDFLibReasoner` now implements the full `AbstractOWLReasoner` interface: `sub/super_object_properties`, `sub/super_data_properties`, `data_property_domains`, `object_property_domains`, `object_property_ranges`, `equivalent_object_properties`, `equivalent_data_properties`, `disjoint_object_properties`, `disjoint_data_properties`, `different_individuals`, and `data_property_values` (previously hard stubs returning `iter([])`), including support for both pairwise and RDF-list-based (`owl:AllDisjointProperties`/`owl:AllDifferent`) axiom forms. Brings it to parity with `StructuralReasoner` without owlready2's punning-related crashes (#242, #205)
- `RDFLibReasoner` constructor gains `negation_default` (open- vs closed-world handling of `OWLObjectComplementOf` in `instances()`) and `sub_properties` (whether `instances()` also matches individuals connected via a sub-property of the property used in a restriction), matching `StructuralReasoner`'s equivalent constructor parameters (#242)
- `owl_expression_to_sparql`/`Owl2SparqlConverter` gain optional `negation_default`, `sub_property_resolver`, `inverse_property_resolver`, and `subclass_resolver` parameters backing `RDFLibReasoner`'s corresponding always-on/opt-in behaviors; default behavior for existing callers is unchanged (#242)
- `owl_expression_to_sparql`/`Owl2SparqlConverter` now translate `OWLDataIntersectionOf`, `OWLDataUnionOf`, and `OWLDataComplementOf` data ranges (previously unimplemented, raising `NotImplementedError`) (#242)
- `Ontology.get_abox_axioms()`, `get_tbox_axioms()`, `get_abox_axioms_between_individuals()`, and `get_abox_axioms_between_individuals_and_classes()` (the owlready2-backed ontology class) are now implemented instead of raising `NotImplementedError("will be implemented in future")`. `get_tbox_axioms()` returns class declarations, `SubClassOf` (including general class axioms), `EquivalentClasses`, and `DisjointClasses` axioms; `get_abox_axioms()` returns class assertions plus object- and data-property assertions (#205)

### Changed
- `owlready2` is now an optional install extra (`pip install owlapy[owlready2]`) rather than a hard dependency of `pip install owlapy` (#205). It backs only the legacy `Ontology`/`StructuralReasoner` classes and a couple of `util_owl_static_funcs` helpers (`make_kb_incomplete`/`make_kb_incomplete_ass`/`make_kb_inconsistent`) -- `owlapy`, `owl_ontology.py`, `owl_reasoner.py`, `owl_reasoner_rdflib.py`, and `util_owl_static_funcs.py` all import fine without it now, via a lazy-loading shim (`owlapy/_lazy_owlready2.py`) that makes `owlready2`-typed annotations/module-level references resolve harmlessly; only actually constructing/calling owlready2-backed functionality without it installed raises a clear `ImportError` pointing at the extra. `RDFLibOntology`/`RDFLibReasoner`/`SyncOntology`/`SyncReasoner` are unaffected either way. `owlready2` remains in the `dev`/`all` extras so the test suite still exercises the owlready2-backed classes.
- `owlready2` dependency in `setup.py` gains an upper bound (`>=0.40,<0.51`), pinned to the version this release's `StructuralReasoner`/`Ontology` code paths and their punning workarounds (#236, #242) were actually verified against, so a future owlready2 release can't silently reintroduce breakage in the legacy owlready2-backed classes before it's been checked.
- `examples/runtime_benchmark_results.py` rewritten: now materializes each reasoner's result (`set(reasoner.instances(ce))`) before recording its runtime -- previously `StructuralReasoner`'s column measured only generator-creation time, not real evaluation, since `StructuralReasoner.instances()`'s underlying `_instances()` is a generator function that was never actually iterated by the benchmark, making its numbers ~10-100x faster than reality (confirmed: 0.0007s unmaterialized vs 0.0067s materialized for the same query). Also adds: a script-level hard timeout (`--timeout_seconds`, default 1000s) enforced via a daemon-thread wrapper independent of each reasoner's own `timeout` support, so no single class expression can block the whole benchmark -- timed-out cells are reported as `TIMEOUT(>Ns)` rather than a misleading elapsed time (note: `StructuralReasoner.instances(timeout=...)` and `RDFLibReasoner.instances(timeout=...)` don't actually enforce anything themselves -- only `SyncReasoner`'s does -- this is why the script-level wrapper exists); `RDFLibReasoner` added as a benchmarked reasoner; removal of a `global sync_reasoners` mutation that silently emptied the reasoner list for later `record_runtime()` calls in the same process after a `single_reasoner="StructuralReasoner"` call; and timestamped progress logging (`[HH:MM:SS] <reasoner>: i/n done (Xs) -- <class expression>`) for each reasoner/class-expression pair, since some individual Carcinogenesis queries (e.g. HermiT) take tens of minutes with no other indication of progress.
- README's "Reasoners Runtime Benchmark" tables refreshed with numbers from the rewritten `examples/runtime_benchmark_results.py`: adds an `RDFLibReasoner` column, corrects `StructuralReasoner` numbers per the materialization fix above, marks timed-out cells as `TIMEOUT(>1000s)` instead of a misleading elapsed time (two Carcinogenesis/HermiT cells and one Carcinogenesis/RDFLibReasoner cell hit this), and adds a note on each reasoner's closed-/open-world semantics linking to `markdown_docs/05_reasoning.md`'s reasoner comparison table.
- `markdown_docs/05_reasoning.md`'s reasoner comparison table now documents each reasoner's world assumption (closed- vs open-world) and adds explicit guidance: use `RDFLibReasoner` for closed-world/complete-data use cases, `SyncReasoner` with `HermiT` for open-world/incomplete-data use cases requiring real OWL 2 DL entailment, and avoid `StructuralReasoner` for new closed-world code in favor of `RDFLibReasoner`.
- `owlapy/utils.py` (1989 LOC) is now the package `owlapy/utils/`, split by concern into `similarity.py`, `length.py`, `ordering.py`, `nnf.py`, `simplify.py`, `signature.py`, and `cache.py`. `owlapy.utils`'s `__init__.py` re-exports every name previously importable from the module, so `from owlapy.utils import ...` is unaffected; no signature changes (IMPROVEMENTS.md 1.2)
- `RDFLibReasoner` ontology ingestion no longer touches `owlready2`/the JVM for its most common inputs: a `str` path is now parsed directly into an `rdflib.Graph` (via `RDFLibOntology`), and an `RDFLibOntology` instance has its `.rdflib_graph` reused directly instead of being round-tripped through `.save()` + reparse. Previously a `str` path was routed through `SyncOntology`, starting the JVM unconditionally. `Ontology`/`SyncOntology` inputs keep the existing save-then-reparse path for back-compat (#205)
- Core library now emits diagnostics through the standard `logging` module instead of `print()`. Progress/status messages log at `INFO`, recoverable issues at `WARNING`, and low-level dumps at `DEBUG`, across `owl_ontology.py`, `owl_reasoner.py`, `render.py`, `utils.py`, and `util_owl_static_funcs.py`. A `NullHandler` is attached to the top-level `owlapy` logger so nothing is printed unless the host application configures logging (opt in via `logging.getLogger("owlapy").setLevel(logging.INFO)`).
- The `agen_kg` LLM pipeline now also logs through the `logging` module instead of `print()`. The existing `enable_logging` flag keeps its meaning: when set, progress messages are emitted via per-module loggers under `owlapy.agen_kg` and a console handler is attached so output stays visible without extra configuration; `except`-block diagnostics now use `logger.exception(...)` and include tracebacks. Host applications that configure logging themselves can control verbosity via the `owlapy` logger hierarchy.
- Added `IMPROVEMENTS.md`, a prioritized plan of readability, performance, documentation, and feature improvements for the library
- Ignored generated/scratch artifacts (`demo.owl`, `inferred_axioms_ontology.owl`, `iris_dataset.csv`, `tests/saved_formats/`) that examples and tests write to the repo root
- `class_expression/restriction.py`'s 10 repeated `# @TODO: CD: property shows the in-built function` comments consolidated into a single module-level docstring note; removed a stray, obsolete `# TODO: XXX` in `owl_axiom.py` whose actual gap is already documented in `signature()`'s docstring (IMPROVEMENTS.md 1.1)

### Fixed
- `StructuralReasoner.instances(ce, timeout=...)` now genuinely enforces its timeout instead of silently never triggering (#260). Two compounding bugs: (1) `_instances()` was a generator function, so `run_with_timeout()` only ever timed how long it took to *create* the generator (near-instant) -- the real work (`_find_instances()`) only ran once the caller iterated the result, outside the timeout-protected region; `_instances()` now returns eagerly. (2) `run_with_timeout()` used `with ThreadPoolExecutor() as executor:`, whose `__exit__` calls `shutdown(wait=True)` unconditionally, so even a caught `TimeoutError` still blocked the caller for the full task duration before returning -- it now calls `shutdown(wait=False)` explicitly. A reasoner that hasn't finished within the timeout now returns an empty result promptly instead of either ignoring the timeout entirely or blocking for the full duration anyway.
- `OWLEquivalentClassesAxiom.contains_owl_nothing()`/`contains_owl_thing()` no longer always raise `TypeError`. `OWLNothing`/`OWLThing` are singleton `OWLClass` *instances*, not types, so `isinstance(ce, OWLNothing)`/`isinstance(ce, OWLThing)` was invalid for any input; both methods now compare via `==` against the singletons (#237)
- `OWLDisjointUnionAxiom.get_owl_equivalent_classes_axiom()` no longer always raises `TypeError`. It called `OWLEquivalentClassesAxiom(self._cls, OWLObjectUnionOf(self._class_expressions))` with two positional args, but `OWLEquivalentClassesAxiom.__init__` expects a single `class_expressions: List[...]`; it now passes `[self._cls, OWLObjectUnionOf(self._class_expressions)]` (#237)
- `RDFLibOntology.get_tbox_axioms()`/`get_abox_axioms()` no longer crash on real-world ontologies: previously any annotation on a class (`rdfs:label`, `rdfs:comment`, ...) raised `NotImplementedError` from `get_tbox_axioms()`, and any individual with an rdf:type target that wasn't independently declared `owl:Class`, or an object-property target that wasn't independently declared `owl:NamedIndividual`, raised `RuntimeError`/`NotImplementedError` from `get_abox_axioms()` — even though neither omission makes the underlying RDF invalid OWL. Both methods now compare rdflib terms directly instead of doing fragile string-matching on `n3()`-serialized predicate IRIs, silently skip predicates that aren't TBox structure, and no longer require independent declarations to represent a class/object-property assertion. `get_tbox_axioms()` also now returns `OWLDisjointClassesAxiom`s (`owl:disjointWith`), which it previously didn't recognize at all. Verified against every ontology under `KGs/` (father, family-benchmark, biopax, carcinogenesis, mutagenesis, lymphography, nctrer) with no exceptions.
- `RDFLibOntology.get_abox_axioms()` no longer raises `NotImplementedError` on individuals with literal-valued (data property) assertions; it now yields a proper `OWLDataPropertyAssertionAxiom` instead.
- `SyncReasoner`'s Java-level timeout helper (`_execute_with_java_timeout`, backing `has_consistent_ontology()`, `is_entailed()`, `is_satisfiable()`, `unsatisfiable_classes()`) waited in **milliseconds** instead of the documented **seconds**, so the default `timeout=1000` only gave the JVM ~1 real second before raising `TimeoutError` — a flaky failure under any CI/machine load. Now correctly waits `timeout` seconds.
- `StructuralReasoner.object_property_values()` no longer crashes with `AttributeError: 'Or' object has no attribute 'iri'` on ontologies that illegally pun an entity as multiple property types (e.g. `KGs/Biopax/biopax.owl`, where `glycolysis#DELTA-G` is declared as both `owl:ObjectProperty` and `owl:AnnotationProperty`). owlready2's load-time punning repair can make values of unrelated properties come back as internal class-expression nodes (`owlready2.Or`) instead of individuals; these are now skipped with a warning (emitted once per property) that points at the punning as the root cause, instead of crashing or silently dropping values (#242, supersedes #236)
- `owl_expression_to_sparql` no longer requires individuals to be explicitly asserted `rdf:type owl:Thing` when `OWLThing` is used as a nested filler (e.g. `∃r.⊤`), which previously made such queries wrongly return no results; also fixes `RDFLibReasoner.instances(OWLThing)`, which now returns `individuals_in_signature()` instead of an always-empty SPARQL query (#242)
- `RDFLibReasoner.instances(SomeClass)` (and every named-class membership check inside a larger expression) previously silently returned too few results whenever `SomeClass` had subclasses and individuals were typed only at the leaf level (confirmed on `KGs/Mutagenesis/mutagenesis.owl`'s `Atom` class, 64 subclasses, 0 direct matches). Now expands to the full subclass closure via a bounded SPARQL `VALUES` clause (#242)
- `OWLObjectInverseOf` is now entailed via a declared `owl:inverseOf` axiom even when the inverse property has no physically-asserted triples of its own, in both `RDFLibReasoner.instances()` and `object_property_values()` (#242)
- `OWLObjectMaxCardinality` (and any cardinality restriction with `cardinality=0`) no longer times out on non-trivial ontologies. The `FILTER NOT EXISTS`/`OPTIONAL` pattern needed to detect "zero matching relations" is evaluated by rdflib's SPARQL engine as an expensive per-candidate correlated check; this is now computed set-theoretically in Python using only the fast, uncorrelated `OWLObjectMinCardinality` path (#242)
- Corrupted (mojibake) emoji in the README "Documentation" and "Examples" section headers, and stale version badges (now 1.6.6)
- Guarded `rdfs:comment` batch generation against LLM call failures, so a single failed batch no longer aborts the whole ontology generation pipeline (#223)
- Fixed an infinite loop in `TextChunker`'s fixed-size chunking strategy that could occur with `overlap > 0` once the cursor reached the end of the text (#224)
- `map_datarange` now degrades gracefully to the top datatype instead of raising `ValueError` on unrecognized data-range fillers (e.g. `owl:Thing` used where a datatype is expected), so a single malformed axiom no longer aborts hierarchy traversal in `super_classes`/`sub_classes`/`object_property_ranges` (#225, #226)
- `OWLLiteral((year, month), GYearMonthOWLDatatype)` / `OWLLiteral((month, day), GMonthDayOWLDatatype)` no longer always raise `ValueError` on tuple input; `_OWLGDatesInterface.__init__` was unconditionally falling through to its string-parsing branch's `else: raise ValueError(...)` for any non-string value, including tuples it had just validated as length-2. Only string input (e.g. `"2020-05"`) worked before this fix. (#237)

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
