# owlapy — Improvement Plan

A prioritized catalogue of concrete, actionable improvements for the owlapy
library (v1.6.5), grouped by **code readability**, **performance**,
**documentation**, **missing features**, and **project housekeeping**.

Each item lists *what*, *where* (file references), *why it matters*, and a
*suggested approach*. The final section proposes an execution plan with phases,
effort estimates, and sequencing.

> Scope note: findings come from a static survey of the codebase (module sizes,
> `TODO`/`FIXME` markers, error-handling patterns, `print` usage, packaging
> config, README, and docs). Items marked **(verify)** need a quick confirmation
> before acting.

---

## 1. Code Readability

> Completed items are removed from this plan once they ship; see
> `CHANGELOG.md` for the record (e.g. the print-to-logging migration, done for
> the core library and `agen_kg` in the 1.6.6 cycle).

### 1.1 Burn down the `TODO`/`FIXME` backlog — 52 markers remaining (was 63)
- **Status:** First triage pass done. `class_expression/restriction.py`'s 10
  repeated "property shows the in-built function" notes were consolidated into
  a single module-level docstring note (the design decision — `property` as a
  parameter name intentionally shadows the builtin — only needs stating once).
  One truly obsolete marker (`owl_axiom.py`'s trailing `# TODO: XXX` after
  `signature()`, whose actual gap is already documented in that method's
  docstring with a link to #231) was deleted. The remaining ~52 markers were
  reviewed and are legitimate — either real, non-trivial correctness/design
  questions (`render.py:325/519/546`, `owl_hierarchy.py:32/124`,
  `owl_class.py:56-57`, `nary_boolean_expression.py:19`,
  `owl_ontology.py`'s ABox/TBox `NotImplementedError` stubs and owlready2
  bug notes) or already tracked elsewhere in this plan (4.1, 4.2).
- **Where:** e.g. `owl_ontology.py` (multiple `@TODO: CD:` on ABox/TBox
  retrieval), `parser.py:411/756` (decimal-vs-float shortcut, tracked in 3.3).
- **Why:** Author-initialled `CD:`/`AB:` comments are effectively a hidden issue
  tracker. They hint at real correctness gaps (e.g. `render.py:546` "Can we
  assume equiv size will be 2?", `owl_hierarchy.py` unhandled eq-sets).
- **Approach:** Remaining work is (b) real bugs → file GitHub issues where
  worth tracking independently, most are small enough to stay as in-code
  markers for now.

### 1.2 Decompose the largest modules
- **Where:** `owl_reasoner.py` (3302 LOC, holds both `StructuralReasoner` and
  `SyncReasoner`) plus the sibling `owl_reasoner_rdflib.py` (841 LOC,
  `RDFLibReasoner`), `owl_ontology.py` (2440), `agen_kg/graph_extractor.py`
  (1539), `owl_axiom.py` (1426).
  ~~`utils.py` (1986)~~ — done: split into `owlapy/utils/` (`similarity.py`,
  `length.py`, `ordering.py`, `nnf.py`, `simplify.py`, `signature.py`,
  `cache.py`), re-exported unchanged from `owlapy/utils/__init__.py`.
- **Why:** Files this size hurt navigation, review, and test isolation.
  `owl_reasoner.py` holds multiple reasoner implementations, and
  `RDFLibReasoner` living in a separate top-level module while conceptually
  being a third reasoner backend is inconsistent.
- **Approach:** Non-breaking split — for the reasoners specifically, turn
  `owl_reasoner.py` into a package `owlapy/owl_reasoner/` with
  `structural.py` (`StructuralReasoner`), `sync.py` (`SyncReasoner`), and
  `rdflib_reasoner.py` (`RDFLibReasoner`, moved in from
  `owl_reasoner_rdflib.py`), all re-exported from
  `owlapy/owl_reasoner/__init__.py`.
  **Caveat:** `owlapy.owl_reasoner` is a public import path with at least one
  known external consumer (Ontolearn — see the traceback in owlapy#242, which
  reaches directly into `owl_reasoner.py`). The new package's `__init__.py`
  must re-export every symbol currently importable from the module (not just
  the 3 main classes), and it may be safer to keep `owl_reasoner.py` itself as
  a thin re-export shim rather than deleting it, so nothing downstream breaks
  silently. Do this as its own PR, separate from functional changes, behind
  the existing test suite; no signature changes.

### 1.3 Tighten broad exception handling
- **Where (in-scope core):** `owl_reasoner.py` (~4 `except Exception`),
  `owl_ontology.py` (~2), `owl_reasoner_rdflib.py` (~1). The bulk of the
  remaining broad catches live in `agen_kg/` — the formerly-printing ones now
  use `logger.exception(...)`, but several silent `except Exception: pass`
  sites remain there.
- **Why:** Broad catches hide root causes and can swallow logic errors.
- **Approach:** Narrow to specific exception types where known; where a broad
  catch is intentional, log with `logger.exception(...)` and add a comment
  stating why it's broad. **(verify)** each site.

---

## 2. Performance

### 2.1 Add caching to hot, pure computations
- **Where:** `utils.py` already hand-rolls an lru_cache adaptation (line ~1878);
  reasoner uses `cached_property`. Hierarchy traversal (`owl_hierarchy.py`) and
  class-expression normalization (`utils.py` `CESimplifier`, NNF) are called
  repeatedly on immutable inputs.
- **Why:** OWL entities are hashable/immutable — ideal for memoization. Repeated
  sub/super-class walks and NNF conversions during reasoning are recomputed.
- **Approach:** Profile a representative reasoning workload (Family KG) to find
  the real hot spots *before* adding caches, then apply `functools.lru_cache`/
  `cached_property` to confirmed-pure hot functions. Measure, don't guess.

### 2.2 Audit repeated `list(...)`/`set(...)` materialization
- **Where:** Generator-returning APIs (`get_tbox_axioms()`, signature walks)
  are frequently wrapped in `list(...)`/`set(...)` by callers and internally.
- **Why:** Re-materializing generators inside loops is a common O(n²) trap.
- **Approach:** **(verify)** with a profiler; where a collection is iterated
  multiple times, compute it once. Keep generator APIs lazy at the boundary.

### 2.3 JVM lifecycle cost
- **Where:** Java-backed reasoners (`SyncReasoner`, `owlapi_mapper.py`) require
  `startJVM`/`stopJVM`.
- **Why:** JVM startup dominates short-lived scripts; the mandatory
  `stopJVM()` teardown means a process can't cheaply reuse it.
- **Approach:** Document the cost clearly and consider a context-manager
  (`with SyncReasoner(...) as r:`) that guarantees teardown, reducing the
  boilerplate that CLAUDE.md currently warns about manually.

---

## 3. Documentation

### 3.1 Fix corrupted README headers — *quick win*
- **Where:** `README.md:84` `## � Documentation` and `README.md:104`
  `## �📋 Examples` contain a U+FFFD replacement character (mojibake) where an
  emoji was intended.
- **Why:** Renders as a broken glyph on PyPI and GitHub — the project's first
  impression.
- **Approach:** Replace with the intended emoji (e.g. `📚`, `📋`) and re-check
  the file is valid UTF-8.

### 3.2 Version-badge / metadata drift — *quick win*
- **Where:** `README.md` badges show **1.6.4** (`pypi-1.6.4`,
  `documentation-1.6.4`) while `owlapy/__init__.py` and `setup.py` are **1.6.5**.
- **Why:** Stale badges mislead users about the current release.
- **Approach:** Update badges as part of the release checklist. Better: derive
  the badge version dynamically (shields.io PyPI endpoint) so it never drifts,
  and add a CI check asserting `__version__ == setup.py version` (CLAUDE.md
  already flags that these two must stay in sync — enforce it).

### 3.3 Document the `TODO`-flagged decimal limitation
- **Where:** `parser.py:411,756` "Just use float for now, decimal not supported
  in owlapy yet."
- **Why:** A silent precision downgrade (`xsd:decimal` → float) is a correctness
  surprise users should know about.
- **Approach:** Note the limitation in `markdown_docs/` and the parser docstring;
  file a tracking issue for real `Decimal` support.

### 3.4 Docstring coverage for public API
- **Where:** Several public methods carry `@TODO` notes asking for docstrings
  (e.g. `restriction.py:705` "should add it into docstring",
  `owl_ontology.py:990` "Unsure it is working").
- **Why:** owlapy positions itself as a documented framework (`markdown_docs/`);
  in-code docstrings should match.
- **Approach:** Fill docstrings for public methods flagged by TODOs; consider a
  `pydocstyle`/ruff `D` rule (currently only `E/W/F/I` are enabled in
  `pyproject.toml`) to prevent regressions.

### 3.5 JPype/JVM dependency-boundary reference table — *from TGDK review*
- **Where:** `markdown_docs/05_reasoning.md` (already has a reasoner
  comparison table with closed/open-world semantics), README "Why OWLAPY?"
  section.
- **Why:** TGDK Reviewer 1 flagged that the JVM/JPype dependency's *scope*
  (which components need Java, which don't) isn't characterized anywhere in
  one place — reviewers had to infer it from scattered prose. A precise,
  greppable table is the single cheapest change that answers "what do I lose
  if I can't run a JVM?" for both reviewers and adopters evaluating the
  library for JVM-averse deployments.
- **Approach:** Add one table — component × JVM required? × semantics —
  covering `RDFLibReasoner`/`RDFLibOntology` (no), legacy `StructuralReasoner`
  (no), `NeuralOntology`/EBR (no), `SyncReasoner` + the OWLAPI mapper (yes).
  Keep it next to the existing reasoner comparison table since the set of
  components changes rarely; link it from the README's dependency section.

### 3.6 OWLAPI ↔ OWLAPY feature-coverage matrix — *from TGDK review*
- **Where:** `owlapy_mapper.py`, `markdown_docs/09_api_reference.md`.
- **Why:** TGDK Reviewer 1 asked which OWLAPI features OWLAPY covers;
  Reviewer 2 characterized the resource as an incremental mirror of OWLAPI
  with no evidence either way. A coverage matrix turns a vague claim into a
  checkable list, and documents known mapper gaps (literal-type mapping
  raises `NotImplementedError` for unmapped datatypes at
  `owlapi_mapper.py:198,301`) in one place instead of scattered exceptions
  discovered only at runtime.
- **Approach:** Enumerate OWLAPI axiom/class-expression/entity types and
  cross-reference against owlapy's mapper; produce a checked-in Markdown
  table. Consider a test asserting every `OWLAxiom` subtype has a mapper
  round-trip test, so the table can't silently drift out of date as new
  axiom types are added.

---

## 4. Missing Features / Enhancements

### 4.1 First-class decimal / typed-literal support
- **Why:** See 3.3 — `xsd:decimal` is currently coerced to float.
- **Approach:** Add an `OWLLiteral` path backed by `decimal.Decimal`; medium
  effort, touches `owl_literal.py`, `parser.py`, `render.py`.

### 4.2 Equivalence-set handling in `OWLHierarchy`
- **Why:** `owl_hierarchy.py:32,124` explicitly defers eq-set handling
  (`_eq_set` commented out, "TODO handling of eq_sets").
- **Approach:** Implement equivalent-entity grouping so hierarchy queries return
  equivalence classes correctly. **(verify)** current behavior with a test on an
  ontology containing `EquivalentClasses` axioms first.

### 4.3 Context-manager ergonomics for JVM reasoners
- **Why:** See 2.3 — reduces the easy-to-forget `stopJVM()` footgun.
- **Approach:** Add `__enter__`/`__exit__` to `SyncReasoner` / the OWLAPI adaptor.

### 4.4 `RDFLibReasoner` / `owl_expression_to_sparql`: remaining gaps found during owlapy#242 parity work
- **Where:** `owlapy/converter.py`, `owlapy/owl_reasoner_rdflib.py`,
  `tests/test_rdflib_reasoner_structural_parity.py` (module docstring documents
  these live, in-code — this entry is the durable backlog pointer to them).
- **Known remaining gap (correctness):** `OWLObjectComplementOf(OWLDataAllValuesFrom(p,
  OWLDataComplementOf(C)))` does not agree with `OWLDataSomeValuesFrom(p, C)` — the De
  Morgan equivalence `∃p.C ≡ ¬∀p.¬C` — for individuals with *zero* `p`-values. Root
  cause is an interaction between the new `OWLDataComplementOf` handler and the
  existing, untouched counting-based `OWLDataAllValuesFrom` implementation (which
  treats "no values" as vacuously satisfying ∀, but the complement-of-complement
  chain doesn't currently unwind that correctly). Needs its own investigation into
  `OWLDataAllValuesFrom`'s counting logic, not just `OWLDataComplementOf`.
- **Known remaining gap (scope):** the `_at_most_cardinality_instances` performance
  fix (Python set-arithmetic instead of a correlated SPARQL `FILTER NOT
  EXISTS`/`OPTIONAL`) only triggers when `OWLObjectMaxCardinality`/`cardinality==0`
  is the *top-level* expression passed to `instances()`. The same restriction
  *nested* inside a larger expression (e.g. an intersection) still goes through the
  slow, generic SPARQL path and could time out on a large enough ontology. Extending
  the special-casing to nested occurrences would need it to live in the shared
  `Owl2SparqlConverter` rather than only in `RDFLibReasoner.instances()`.
- **Cleanup:** `RDFLibReasoner.__init__`'s `infer_property_values`/
  `infer_data_property_values` parameters have been dead code (stored, never read)
  since before this session; their stated intent ("infer property values from
  sub-properties") now fully overlaps with the real, working `sub_properties`
  parameter added this session. Worth removing the two dead parameters in a
  follow-up (a public API change, however trivial, so do it deliberately rather than
  bundled with unrelated work).
- **Gotchas for future SPARQL work in `converter.py`** (both confirmed by direct
  testing against rdflib, not documented anywhere else): (1) a bare
  `FILTER(false)`/`FILTER(0)` is silently ineffective in rdflib's SPARQL engine —
  use a comparison like `FILTER(1=0)` instead; (2) a `UNION` branch containing
  *exactly one* bare `FILTER` and no triples fails to correlate with
  already-bound outer variables — add a leading no-op `FILTER(BOUND(?var))` to any
  such branch (two or more filters in the group works fine).

### 4.5 Ontology-generation quality evaluation harness (`agen_kg`) — *from TGDK review*
- **Where:** `owlapy/agen_kg/`, new `examples/agen_kg_eval.py` (or similar).
- **Why:** TGDK Reviewer 3 pointed out that the GraphRAG-style
  text-to-ontology pipeline is described but never evaluated — "not clear
  ... if the generated ontologies can have good quality." This is currently
  the single biggest evidence gap for that feature and the most likely
  paper-rejection risk; it's also a real product gap since users have no way
  to sanity-check pipeline output against a baseline today.
- **Approach:** Run the pipeline over 1–2 small public gold-standard
  KGs/texts, then report precision/recall/F1 of extracted entities/triples/
  types against the gold ABox/TBox. Wire it into `examples/` as a runnable
  script producing a table, so both the paper and README can cite real
  numbers instead of a narrative claim.

### 4.6 Multi-provider LLM example + test for `agen_kg` — *from TGDK review*
- **Where:** `owlapy/agen_kg/agent.py` (`model="gpt-4o"` default,
  `dspy.LM(model=f"openai/{model}", ...)`), `owlapy/agen_kg/helper.py`
  (`configure_dspy` hardcodes `"openai/gpt-4o"`), `examples/`.
- **Why:** TGDK Reviewer 2 read the pipeline as tied to one LLM vendor. In
  reality `dspy.LM` is provider-agnostic, but every example and default
  hardcodes an OpenAI model string, so the provider-agnostic claim is
  currently unverified by anything runnable.
- **Approach:** Add one example configuration plus an integration test
  (skipped by default / requires an API key) that runs `agen_kg` against a
  non-OpenAI `dspy.LM` backend (e.g. a local Ollama-hosted model or another
  vendor supported by `litellm`), and document the swap in `markdown_docs/`.

### 4.7 `NeuralOntology` (EBR) runtime/hardware benchmark — *from TGDK review*
- **Where:** `examples/runtime_benchmark_results.py` (already benchmarks
  `SyncReasoner`/`StructuralReasoner`/`RDFLibReasoner`), `owl_ontology.py`
  `NeuralOntology`.
- **Why:** TGDK Reviewer 2 asked for the hardware specification needed to
  run the embedding-based reasoning path. There is currently no runtime or
  hardware data for `NeuralOntology` anywhere, unlike the symbolic reasoners
  which already have a published benchmark table.
- **Approach:** Extend the existing benchmark script to include
  `NeuralOntology` inference latency at a couple of embedding
  dimensions/dataset sizes, on CPU and GPU (`device="cpu"`/`"gpu"`), and
  report the numbers in the README/paper next to the existing reasoner
  table.

### 4.8 Close or document remaining ELK query-method gaps — *from TGDK review*
- **Where:** `owl_reasoner.py` — `getDisjointClasses`,
  `getDataPropertyDomains`, `getObjectPropertyDomains`/`Ranges`,
  `getSubDataProperties`/`getSuperDataProperties`,
  `getDifferentIndividuals`, `equivalentDataProperties` all raise
  `NotImplementedError` when `reasoner_name == "ELK"`.
- **Why:** These currently read as blanket owlapy gaps (raised during the
  TGDK response's R1.2 answer), but some are genuine OWL EL profile
  limitations that ELK itself cannot support by design (e.g. EL has no
  disjointness), while others may be closable with a structural fallback.
  Distinguishing the two turns a vague "not implemented" list into either a
  documented, principled reasoner-profile limitation, or a real backlog item
  — both are defensible in the paper, an unexplained gap list isn't.
- **Approach:** Audit each `NotImplementedError` against the OWL EL profile
  spec. For anything EL doesn't support, reword the message from "not yet
  implemented" to an explicit "unsupported by the EL profile" and add it to
  the reasoner comparison table in `markdown_docs/05_reasoning.md`. For
  anything closable, implement it via a structural fallback.

---

## 5. Project Housekeeping

### 5.1 Remove stray artifacts from the repo root — *quick win*
- **Where (untracked, per `git status`):** `dummy.py`, `demo.owl`,
  `inferred_axioms_ontology.owl`, `iris_dataset.csv`, and root-level
  `iris_kg.owl`, `owl_class_expressions.owl` (already gitignored), plus
  `tests/saved_formats/`.
- **Why:** `dummy.py` is clearly a scratch script; generated `.owl`/`.csv`
  outputs clutter the working tree and risk accidental commits.
- **Approach:** Delete scratch files or move examples into `examples/`; extend
  `.gitignore` to cover `demo.owl`, `inferred_axioms_ontology.owl`,
  `iris_dataset.csv`, and any test-generated `tests/saved_formats/` output. Point
  test fixtures at the scratchpad/`tmp` rather than the repo root.

### 5.2 Enforce version sync in CI — ✅ *done*
- **Status:** `.github/workflows/test.yml` now has a "Check version sync" step
  (runs before dependency install, so it fails fast) that parses
  `owlapy/__init__.py`'s `__version__` and `setup.py`'s `version=` and fails
  the build if they disagree. The README badge is not covered — it's static
  text, not worth a CI check on its own.
- **Where:** `owlapy/__init__.py` + `setup.py` (CLAUDE.md documents the
  dual-source-of-truth).

### 5.3 Consider tightening lint/type gates over time
- **Where:** `pyproject.toml` — ruff selects only `E/W/F/I`; mypy has
  `disallow_untyped_defs = false` (gradual typing, by design).
- **Approach:** Incrementally enable ruff `B` (bugbear), `UP` (pyupgrade), and
  `D` (docstrings) on a per-directory basis; ratchet mypy strictness as coverage
  allows. `py.typed` is already shipped (good — PEP 561 compliant).

### 5.4 Independent-adoption tracking — *from TGDK review*
- **Where:** README.md "Why OWLAPY?" section / new `markdown_docs/` page.
- **Why:** TGDK Reviewers 1 and 2 both flagged that documented real-world
  usage is currently limited to DICE-group-originated projects (Ontolearn,
  DRILL, EvoLearner, CLIP). Citing genuinely independent adopters is the
  single most effective lever for the paper's Impact score, and it's cheap
  to start collecting now rather than scrambling right before a resubmission
  deadline.
- **Approach:** Check PyPI/GitHub's "Used by"/dependents graph and Google
  Scholar citations of the owlapy paper/repo for usage outside
  `dice-group`-owned repos. If none are found, consider lightweight outreach
  (e.g. a GitHub Discussions "who's using owlapy?" thread, or a request in
  the release notes) to surface adopters before the revision deadline.

---

## 6. Suggested Execution Plan

Phased so each phase is independently shippable and low-risk first.

### Phase 0 — Quick wins ✅ *shipped*
1. ✅ Fix README mojibake headers (3.1).
2. ✅ Sync version badges + add CI version-sync check (3.2, 5.2).
3. ✅ Remove/ignore stray root artifacts (5.1).
4. ✅ TODO triage pass: consolidated `restriction.py`'s repeated notes, deleted
   the one obsolete marker found, reviewed the rest (1.1) — see 1.1 for what's
   left open (real, non-trivial items, not quick wins).

*Deliverable:* clean tree, accurate metadata, reviewed TODO backlog.

### Phase 1 — Logging migration ✅ *shipped* + exception tightening
5. ✅ Per-module loggers now cover the core library and `agen_kg`; recorded in
   `CHANGELOG.md` `[Unreleased]`. `scripts/` keep `print` for CLI output.
6. Narrow/annotate broad `except` blocks in the core modules (1.3) — still open.

### Phase 2 — Documentation & correctness notes (1 day)
8. Document decimal limitation + parser docstrings (3.3, 3.4).
9. Fill TODO-flagged public docstrings; optionally enable ruff `D` on one module.

### Phase 3 — Structural refactor (2–4 days, behind tests)
10. ✅ `utils.py` split into a subpackage with re-exports (1.2).
11. Split reasoner/ontology modules if tests give confidence (1.2).
12. Add context-manager support to JVM reasoners (2.3, 4.3).

### Phase 4 — Performance (data-driven, 2–3 days)
13. Profile Family-KG reasoning; add memoization only to confirmed hot,
    pure functions (2.1); fix any re-materialized generators (2.2).

### Phase 5 — Features (scoped separately)
14. Decimal/typed-literal support (4.1).
15. Equivalence-set handling in `OWLHierarchy` (4.2).

### Phase 6 — TGDK resubmission support (paper-driven, prioritize by revision deadline)
16. JPype/JVM dependency-boundary table + OWLAPI feature-coverage matrix
    (3.5, 3.6) — cheapest, highest-leverage for reviewer concerns; do first.
17. Independent-adoption search/outreach (5.4) — start immediately, it's the
    slowest-turnaround item (depends on external response).
18. `agen_kg` evaluation harness (4.5) — addresses the most substantive
    quality gap raised (R3).
19. `NeuralOntology` CPU/GPU benchmark (4.7) and multi-provider LLM example
    (4.6) — answers R2's "missing technical detail" points with runnable
    evidence rather than prose.
20. ELK gap audit (4.8) — smaller, do if time allows before the deadline.

### Cross-cutting rules
- Every change runs `ruff check owlapy --line-length=200` and the pytest suite
  (`PYTHONPATH=. pytest --ignore=tests/test_z_do_last_ebr_retrieval.py -p no:warnings`).
- Public API stays stable through refactors (re-export shims).
- Update `CHANGELOG.md` `[Unreleased]` for any user-facing change (per CLAUDE.md).
- Branch from `develop`; PRs target `develop`.

---

*Generated as a planning document — items marked **(verify)** should be
confirmed against runtime behavior before implementation.*
