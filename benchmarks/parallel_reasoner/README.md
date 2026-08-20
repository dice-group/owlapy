# ParallelReasoner benchmark: does it actually help?

`owlapy.parallel_reasoner.ParallelReasoner` (added alongside this benchmark) fans out
open-world class-expression instance retrieval across a pool of OS processes, each running
its own JVM + Java-backed reasoner (`HermiT`, `Pellet`, `JFact`, `Openllet`, `ELK`,
`Structural`), by checking `KB |= ce(a)` independently per individual instead of one bulk
`getInstances()` call. This directory measures whether that actually reduces wall-clock time,
using 100 (or fewer, where documented) generated complex-DL class expressions per dataset,
run through both `SyncReasoner` (baseline) and `ParallelReasoner` (parallel), with identical
reused reasoner state on both sides so only the per-query cost is compared.

**Headline result: it depends heavily on the reasoner and the ABox size, and in 3 of the 4
tested configurations it made things *slower*, sometimes drastically.** See
[Results](#results) and [Why](#why-bulk-retrieval-usually-wins) below.

| Dataset (individuals) | Reasoner | Speedup (total wall time, 100→30→10 expressions) |
|---|---|---|
| Family (202) | HermiT | **1.33x faster** |
| Family (202) | Pellet | **25x slower** |
| Mutagenesis (14,145) | Pellet | **670x slower** |
| Mutagenesis (14,145) | HermiT | **0.22x** (both sides timeout-censored -- not a clean comparison, see below) |

Every one of the 240 expression evaluations where neither side hit a timeout produced
**byte-identical results** between `SyncReasoner` and `ParallelReasoner`. Correctness holds;
speed does not, except in one specific corner case.

## Contents

- `generate_expressions.py` -- builds a reproducible corpus of complex DL class expressions
  (intersection, union, complement, existential/universal, min/max/exact cardinality, nested
  up to depth 3) from a dataset's actual classes and object properties.
- `run_benchmark.py` -- runs one (dataset, reasoner) combination: baseline `SyncReasoner`
  then `ParallelReasoner`, one reused instance/pool per side, one CSV row per expression per
  mode, written incrementally.
- `analyze_results.py` -- aggregates CSVs into the summary table above.
- `expressions/*.txt` -- the exact generated corpora used (Manchester syntax, one per line).
- `results/*.csv` + `*.meta.json` -- raw per-expression timings and run metadata.

## Reproducing this

```bash
conda activate temp_owlapy   # see CLAUDE.md
cd benchmarks/parallel_reasoner

# 1. Generate the corpora (deterministic given --seed; already checked in under expressions/)
python generate_expressions.py --ontology ../../KGs/Family/family-benchmark_rich_background.owl \
    --out expressions/family.txt --n 100 --seed 42
python generate_expressions.py --ontology ../../KGs/Mutagenesis/mutagenesis.owl \
    --out expressions/mutagenesis.txt --n 100 --seed 42

# 2. Run each (dataset, reasoner) combination. --timeout bounds the baseline's bulk call;
#    --per-individual-timeout bounds ParallelReasoner's *per-individual* check and MUST be
#    an integer and MUCH smaller for large ABoxes -- see "Two different timeouts" below.
python run_benchmark.py --ontology ../../KGs/Family/family-benchmark_rich_background.owl \
    --namespace "http://www.benchmark.org/family#" --expressions expressions/family.txt \
    --dataset family --reasoner Pellet --out results/family_pellet.csv --timeout 30

python run_benchmark.py --ontology ../../KGs/Family/family-benchmark_rich_background.owl \
    --namespace "http://www.benchmark.org/family#" --expressions expressions/family.txt \
    --dataset family --reasoner HermiT --out results/family_hermit.csv --timeout 30

python run_benchmark.py --ontology ../../KGs/Mutagenesis/mutagenesis.owl \
    --namespace "http://dl-learner.org/mutagenesis#" --expressions expressions/mutagenesis.txt \
    --dataset mutagenesis --reasoner Pellet --out results/mutagenesis_pellet.csv \
    --timeout 30 --per-individual-timeout 1 --limit 30

python run_benchmark.py --ontology ../../KGs/Mutagenesis/mutagenesis.owl \
    --namespace "http://dl-learner.org/mutagenesis#" --expressions expressions/mutagenesis.txt \
    --dataset mutagenesis --reasoner HermiT --out results/mutagenesis_hermit.csv \
    --timeout 30 --per-individual-timeout 1 --limit 10

# 3. Summarize
python analyze_results.py "results/*.csv"
```

`KGs/` is downloaded per the root `CLAUDE.md` instructions (`wget .../KGs.zip`), not
checked into the repo.

## Environment this was measured on

- 22 logical CPUs, 62 GiB RAM (`nproc`, `free -h`)
- Python 3.11.14, `owlapy` 1.6.6, JPype 1.7.1, OpenJDK 17.0.19
- `ParallelReasoner(num_workers=22)` (i.e. `os.cpu_count()`, the library default) throughout
- Wall-clock numbers are single-run, not averaged over repeats -- treat absolute seconds as
  indicative, not lab-grade; the *ratios* and the qualitative pattern (which configurations
  win/lose, and why) are the reliable takeaway.

## Methodology notes

**Reused instance/pool, not cold start.** Both `sync_reasoner` and the `ParallelReasoner`
pool are created once per (dataset, reasoner) combination and reused across all expressions,
matching how a real workload (e.g. scoring many candidate concepts during concept learning)
would use either API. This means the numbers below are *steady-state* per-query cost with
JVM startup and TBox classification amortized away -- they are a **best case** for
`ParallelReasoner`, since its worker-pool startup cost (22 JVMs) is paid once and not charged
against any individual query.

**Two different timeouts.** `SyncReasoner.instances(ce, timeout=T)` bounds the *entire* bulk
call: if the underlying reasoner doesn't finish in `T` seconds, the call returns an empty set
(logged, not raised). `ParallelReasoner.instances(ce, timeout=T)` uses `T` as the budget for
*each individual's* `is_entailed()` check -- it does not bound the query as a whole. On a
14,145-individual ABox split across 22 workers (~643 individuals/worker), if even a modest
fraction of individuals are genuinely slow to resolve, their per-individual timeouts stack
up sequentially within whichever worker happens to process them, and the query's wall time
can become `(slow individuals on the busiest worker) x T` -- far larger than `T` itself. This
is exactly what the Mutagenesis numbers below show, and it is a real, load-bearing limitation
of the per-individual decomposition strategy, not a benchmarking artifact -- see
[Bugs and limitations found](#bugs-and-limitations-found-while-running-this).

**Some generated expressions are genuinely hard, on purpose.** The corpus is intersection /
union / complement / existential / universal / min / max / exact-cardinality restrictions
nested up to depth 3, built from each ontology's real classes and properties (see
`generate_expressions.py`). This is meant to stress both reasoners similarly to how a
concept-learning search (Ontolearn/DRILL-style refinement) would generate candidates, not to
be an easy/friendly corpus.

## Results

Full table (`python analyze_results.py "results/*.csv"`):

| Dataset | Reasoner | N (ok/timeout/error) B \| P | Baseline total (s) | Parallel total (s) | Speedup (total) | Baseline mean (s) | Parallel mean (s) | Baseline p95 (s) | Parallel p95 (s) |
|---|---|---|---|---|---|---|---|---|---|
| family | HermiT | 100/0/0 \| 100/0/0 | 36.719 | 27.660 | **1.33x** | 0.367 | 0.277 | 0.476 | 0.332 |
| family | Pellet | 100/0/0 \| 100/0/0 | 1.013 | 24.945 | **0.04x** | 0.010 | 0.249 | 0.070 | 0.289 |
| mutagenesis | Pellet | 30/0/0 \| 30/0/0 | 3.957 | 2649.156 | **0.00x** | 0.132 | 88.305 | 0.962 | 175.237 |
| mutagenesis | HermiT | 10/0/0 \| 10/0/0 | 300.012 | 1364.141 | **0.22x** | 30.001 | 136.414 | 30.005 | 154.336 |

(`N` = ok/timeout/error counts, Baseline \| Parallel. "error" = the underlying Java reasoner
itself threw, not a `ParallelReasoner` bug -- see below.)

### Family + HermiT: the one configuration where parallelizing wins (1.33x)

HermiT's bulk `getInstances()` on this 202-individual, 18-class ontology is *not* especially
well-optimized relative to doing 202 independent `is_entailed()` checks: a single deep test
expression (3 levels of union/intersection/complement/forall) measured **0.59s bulk vs 0.33s
sequential-per-individual** in isolation (see the log in this PR's history) -- i.e. per-
individual checking was already faster than bulk retrieval *before any parallelism*, on this
dataset+reasoner pair specifically. Spreading that already-favorable sequential workload
across 22 processes turns a modest sequential win into a modest wall-clock win. This is the
one regime the original "shard the individuals across cores" idea actually pays off in.

### Family + Pellet: 25x slower

Pellet's bulk retrieval on Family is already extremely fast (10ms mean). 202 individual
`is_entailed()` calls have real fixed cost per call (JVM method dispatch, `ClassAssertionAxiom`
construction, tableau consistency check from a cold local context) that a mean of 249ms per
*parallel* query can't beat even with 22-way concurrency, because the total work across
individuals is already larger than the entire bulk call, and cross-process dispatch (spawn,
pickling, IPC) adds further constant overhead per query that a 10ms baseline has no chance of
amortizing.

### Mutagenesis + Pellet: 670x slower (0.13s -> 88s mean per query)

This is the more consequential result, since it's the realistic large-ABox case (14,145
individuals). Pellet's bulk `getInstances()` stayed sub-second for every one of the 30
expressions tested (mean 132ms, p95 962ms) -- Pellet's realization algorithm clearly reuses
shared internal structure across individuals far more effectively than 14,145 independent
entailment checks can. Several `ParallelReasoner` queries (nested cardinality restrictions in
particular, e.g. `hasBond exactly 2 (inBond min 3 (Bond-7 or Bond-7))`) took 100-183 *seconds*
each -- direct evidence of the "many individuals each need close to the per-individual
timeout" pileup described above, not an occasional outlier.

### Mutagenesis + HermiT: not a clean comparison

All 10 baseline calls hit the 30s timeout (every single one: mean and p95 both exactly
`30.00x`s). HermiT simply cannot realize these expressions against a 14K-individual ABox
within 30 seconds -- the *true* unconstrained baseline time is unknown and almost certainly
much larger (a standalone probe of one moderately complex expression against this ontology
hit a 60s timeout with zero results). `ParallelReasoner` isn't timeout-capped as a whole, so
it "completed" every query, but at 129-154s each -- worse than the *censored* baseline, and
likely still worse than HermiT's true (uncensored) bulk time would be, though that can't be
measured directly without an impractically long timeout. Treat the `0.22x` figure as "both are
bad, in different ways," not as a real 4.5x factor.

**This combination also produced the experiment's one result mismatch** (expression 0):
baseline returned an empty set (timeout-censored), `ParallelReasoner` returned 167 individuals
(actually resolved, since its budget is distributed per-individual rather than global). This
is a direct, understood consequence of the two systems having structurally different timeout
semantics under time pressure -- not a logic bug. Every non-timeout-affected comparison in this
whole experiment (all of Family x {HermiT, Pellet}, all of Mutagenesis + Pellet) matched
exactly.

## Why bulk retrieval usually wins

The premise behind `ParallelReasoner` (see the design discussion that led to it) was that
`KB |= ce(a)` for different individuals `a` are independent decision problems, so checking
them across processes should be "free" parallelism with no correctness cost. That premise is
true -- correctness holds throughout this experiment -- but it ignored a practical fact about
how real DL reasoners are implemented: **Pellet and HermiT's `getInstances()` do not check
each individual from a cold start.** Realization-based retrieval reuses the classified TBox,
shares completion-graph/model structure across individuals, and short-circuits using the class
hierarchy, so the *marginal* cost of the Nth individual is usually far below the cost of a
fresh, independent consistency check. Decomposing into N separate `is_entailed()` calls
(what `ParallelReasoner` does) throws all of that reuse away and pays a much larger *total*
amount of CPU work -- work that 22-way parallelism did not come close to compensating for in
3 of these 4 configurations. The exception (Family + HermiT) is a case where that reuse
advantage happened to be small enough that decomposition was already a sequential win before
parallelism was even applied.

## Bugs and limitations found while running this

Building this benchmark surfaced two real issues, one of which was a genuine bug in
`ParallelReasoner` (now fixed in this branch), and one a limitation of the reasoners
themselves:

1. **Fixed:** `SyncReasoner.is_entailed()` raises `TimeoutError` on a per-call timeout,
   unlike `SyncReasoner.instances()`, which silently returns an empty set. Since
   `ParallelReasoner._check_individual` called `is_entailed()` per individual without
   catching this, a single slow individual anywhere in a shard would crash the *entire*
   `instances()` call with an uncaught `TimeoutError` propagating out of the worker pool,
   instead of just being excluded like `instances()`'s own timeout handling does. Fixed in
   `owlapy/parallel_reasoner.py` (`_check_individual` now catches `TimeoutError` and treats
   it as "not entailed within budget"), with a regression test
   (`test_per_individual_timeout_excludes_rather_than_raises`).
2. **Not a `ParallelReasoner` bug, but observed here:** one generated Mutagenesis expression
   (`inStructure exactly 1 (hasAtom max 2 (not (hasAtom some (Bromine-94 or Chlorine-93))))`-
   shaped nesting of cardinality + complement + union) triggered
   `java.lang.ArrayIndexOutOfBoundsException: Index 2 out of bounds for length 2` inside
   Pellet/Openllet's own realization code, via the exact same `getInstances()` call the
   baseline uses. `run_benchmark.py` treats this as `status="error"` and continues rather
   than aborting the sweep; it did not recur in the final 30-expression sample used above
   (that specific expression fell outside the `--limit 30` window), but it's a real,
   reproducible Pellet-internal defect independent of this feature.
3. **Design limitation, not a bug:** as described above, `ParallelReasoner`'s per-individual
   timeout does not bound total query time on large ABoxes. There is currently no
   query-level timeout/cutoff in `ParallelReasoner.instances()`.

## Practical guidance

Based on this data, **`ParallelReasoner` should not be reached for by default.** It is a
plausible win only when you have independently confirmed that, for your specific
(ontology, reasoner) pair, per-individual `is_entailed()` checking is already competitive
with bulk `instances()` *before* adding parallelism -- which in this experiment was true for
exactly one of four configurations (a small ABox with HermiT). For anything resembling a
production-sized ABox (thousands of individuals), or for Pellet specifically (whose bulk
realization is clearly well-optimized), `SyncReasoner.instances()` directly is very likely
faster, sometimes by two to three orders of magnitude.

## A more promising direction (not implemented/benchmarked here)

The diagnosis above suggests a different parallelization axis is likely to actually work:
**parallelize across *queries*, not across individuals.** A workload with many different
candidate class expressions to evaluate against the same ontology (e.g. scoring refinement-
operator candidates during concept learning -- squarely Ontolearn/DRILL's use case) is
embarrassingly parallel at the query level without discarding any reasoner-internal reuse:
dispatch each class expression to a different worker process, and have each worker run its
own full, un-decomposed `SyncReasoner.instances(ce)` bulk call. Every worker still benefits
from the reasoner's own realization optimizations; only the *set of queries*, not the ABox, is
split across cores. This wasn't implemented or measured in this round (scope was "benchmark
the existing `ParallelReasoner`"), but given that Family+Pellet's bulk calls average 10ms and
Mutagenesis+Pellet's average 132ms, batching e.g. 100 *different* expressions across 22
processes this way would plausibly deliver a real, close-to-N-fold speedup with none of the
per-individual overhead documented here. Worth a follow-up benchmark.
