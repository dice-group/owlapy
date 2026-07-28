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

### 1.1 Burn down the `TODO`/`FIXME` backlog — 63 markers
- **Where:** e.g. `class_expression/restriction.py` (13 `@TODO: CD:` notes,
  several asking to convert methods to `@property`), `render.py:323/517/544`,
  `owl_hierarchy.py:32/124` (unimplemented equivalence-set handling),
  `owl_ontology.py` (multiple `@TODO: CD:` on ABox/TBox retrieval),
  `parser.py:411/756` (decimal-vs-float shortcut).
- **Why:** Author-initialled `CD:`/`AB:` comments are effectively a hidden issue
  tracker. They hint at real correctness gaps (e.g. `render.py:544` "Can we
  assume equiv size will be 2?", `owl_hierarchy.py` unhandled eq-sets).
- **Approach:** Triage into (a) trivial cleanups (do now), (b) real bugs → file
  GitHub issues, (c) obsolete → delete. Start with `restriction.py`'s repeated
  "property shows the in-built function" notes, which are a single consistent
  design decision that can be documented once instead of 13 times.

### 1.2 Decompose the largest modules
- **Where:** `owl_reasoner.py` (3302 LOC), `owl_ontology.py` (2440),
  `utils.py` (1986), `agen_kg/graph_extractor.py` (1539), `owl_axiom.py` (1426).
- **Why:** Files this size hurt navigation, review, and test isolation.
  `owl_reasoner.py` holds multiple reasoner implementations; `utils.py` is a
  grab-bag (`CESimplifier`, NNF, similarity metrics, an lru_cache adaptation).
- **Approach:** Non-breaking split — move cohesive groups into a subpackage
  (e.g. `owlapy/utils/` with `simplify.py`, `nnf.py`, `similarity.py`) and
  re-export from `utils.py` / `__init__` to preserve the public API. Do this
  behind tests; no signature changes.

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

### 5.2 Enforce version sync in CI
- **Where:** `owlapy/__init__.py` + `setup.py` (CLAUDE.md documents the
  dual-source-of-truth).
- **Approach:** Tiny CI step (or pre-commit hook) asserting the two versions
  match, plus optionally the README badge. Prevents the drift seen in 3.2.

### 5.3 Consider tightening lint/type gates over time
- **Where:** `pyproject.toml` — ruff selects only `E/W/F/I`; mypy has
  `disallow_untyped_defs = false` (gradual typing, by design).
- **Approach:** Incrementally enable ruff `B` (bugbear), `UP` (pyupgrade), and
  `D` (docstrings) on a per-directory basis; ratchet mypy strictness as coverage
  allows. `py.typed` is already shipped (good — PEP 561 compliant).

---

## 6. Suggested Execution Plan

Phased so each phase is independently shippable and low-risk first.

### Phase 0 — Quick wins (hours, no behavior change)
1. Fix README mojibake headers (3.1).
2. Sync version badges + add CI version-sync check (3.2, 5.2).
3. Remove/ignore stray root artifacts (5.1).
4. TODO triage pass: delete obsolete, convert real bugs to issues (1.1 part a).

*Deliverable:* clean tree, accurate metadata, an issue backlog.

### Phase 1 — Logging migration ✅ *shipped* + exception tightening
5. ✅ Per-module loggers now cover the core library and `agen_kg`; recorded in
   `CHANGELOG.md` `[Unreleased]`. `scripts/` keep `print` for CLI output.
6. Narrow/annotate broad `except` blocks in the core modules (1.3) — still open.

### Phase 2 — Documentation & correctness notes (1 day)
8. Document decimal limitation + parser docstrings (3.3, 3.4).
9. Fill TODO-flagged public docstrings; optionally enable ruff `D` on one module.

### Phase 3 — Structural refactor (2–4 days, behind tests)
10. Split `utils.py` into a subpackage with re-exports (1.2).
11. Split reasoner/ontology modules if tests give confidence (1.2).
12. Add context-manager support to JVM reasoners (2.3, 4.3).

### Phase 4 — Performance (data-driven, 2–3 days)
13. Profile Family-KG reasoning; add memoization only to confirmed hot,
    pure functions (2.1); fix any re-materialized generators (2.2).

### Phase 5 — Features (scoped separately)
14. Decimal/typed-literal support (4.1).
15. Equivalence-set handling in `OWLHierarchy` (4.2).

### Cross-cutting rules
- Every change runs `ruff check owlapy --line-length=200` and the pytest suite
  (`PYTHONPATH=. pytest --ignore=tests/test_z_do_last_ebr_retrieval.py -p no:warnings`).
- Public API stays stable through refactors (re-export shims).
- Update `CHANGELOG.md` `[Unreleased]` for any user-facing change (per CLAUDE.md).
- Branch from `develop`; PRs target `develop`.

---

*Generated as a planning document — items marked **(verify)** should be
confirmed against runtime behavior before implementation.*
