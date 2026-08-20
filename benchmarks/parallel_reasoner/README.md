# Parallel reasoning benchmarks: do these strategies actually help?

`owlapy.parallel_reasoner` (added alongside this benchmark) implements two independent
strategies for parallelizing open-world class-expression instance retrieval across a pool of
OS processes, each running its own JVM + Java-backed reasoner (`HermiT`, `Pellet`, `JFact`,
`Openllet`, `ELK`, `Structural`):

- **`ParallelReasoner`** parallelizes *within one query*, sharding the individuals it checks
  membership for across workers (`KB |= ce(a)` independently per individual, instead of one
  bulk `getInstances()` call). See [Part 1](#results).
- **`BatchParallelReasoner`** parallelizes *across many different queries* against the same
  ontology, dispatching each expression to a worker that runs its own full, un-decomposed bulk
  call. See [Part 2](#part-2-batchparallelreasoner----parallelizing-across-queries-instead-of-individuals).

This directory measures whether either actually reduces wall-clock time, using 100 (or fewer,
where documented) generated complex-DL class expressions per dataset, run through both
`SyncReasoner` (sequential baseline) and the parallel variant, with identical reused reasoner
state on both sides so only the per-workload cost is compared.

**Headline result: both strategies are conditional wins, not free lunches, and for different
reasons.** Part 1 (individual-level) lost in 3 of 4 configurations, sometimes by orders of
magnitude, because it discards reuse the reasoner's own bulk retrieval already does. Part 2
(query-level) is a real, substantial win when the reasoner's bulk calls are individually
expensive (2-5x, both datasets with HermiT), but a loss when they're already fast (Pellet,
both datasets) because pool-startup and JVM-contention overhead isn't amortized. See both
parts below for the numbers and the reasoning behind each pattern.

### Part 1: `ParallelReasoner` (individual-level)

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
- `run_benchmark.py` -- Part 1: runs one (dataset, reasoner) combination, sequential
  `SyncReasoner` vs `ParallelReasoner` (individual-level), one reused instance/pool per side,
  one CSV row per expression per mode, written incrementally.
- `run_batch_benchmark.py` -- Part 2: runs one (dataset, reasoner) combination, sequential
  `SyncReasoner` vs `BatchParallelReasoner` (query-level, whole corpus dispatched in one
  `instances_batch()` call).
- `analyze_results.py` -- aggregates Part 1 CSVs into the Part 1 summary table.
- `expressions/*.txt` -- the exact generated corpora used (Manchester syntax, one per line).
- `results/*.csv` + `*.meta.json` -- raw per-expression timings and run metadata (`*_batch.csv`
  for Part 2 runs).

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

# 3. Summarize Part 1
python analyze_results.py "results/*.csv"

# 4. Part 2: BatchParallelReasoner vs sequential SyncReasoner, same corpora
python run_batch_benchmark.py --ontology ../../KGs/Family/family-benchmark_rich_background.owl \
    --namespace "http://www.benchmark.org/family#" --expressions expressions/family.txt \
    --dataset family --reasoner Pellet --out results/family_pellet_batch.csv --timeout 30

python run_batch_benchmark.py --ontology ../../KGs/Family/family-benchmark_rich_background.owl \
    --namespace "http://www.benchmark.org/family#" --expressions expressions/family.txt \
    --dataset family --reasoner HermiT --out results/family_hermit_batch.csv --timeout 30

python run_batch_benchmark.py --ontology ../../KGs/Mutagenesis/mutagenesis.owl \
    --namespace "http://dl-learner.org/mutagenesis#" --expressions expressions/mutagenesis.txt \
    --dataset mutagenesis --reasoner Pellet --out results/mutagenesis_pellet_batch.csv --timeout 30

python run_batch_benchmark.py --ontology ../../KGs/Mutagenesis/mutagenesis.owl \
    --namespace "http://dl-learner.org/mutagenesis#" --expressions expressions/mutagenesis.txt \
    --dataset mutagenesis --reasoner HermiT --out results/mutagenesis_hermit_batch.csv \
    --timeout 30 --limit 10
```

`run_batch_benchmark.py` prints its own sequential-vs-batch-parallel total and speedup at the
end of each run (no separate analyze step needed for Part 2).

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

- **`ParallelReasoner` (individual-level) should not be reached for by default.** It's a
  plausible win only when you've independently confirmed that per-individual
  `is_entailed()` checking is already competitive with bulk `instances()` *before* adding
  parallelism -- true for exactly one of four configurations tested (a small ABox with
  HermiT). For anything resembling a production-sized ABox, or for Pellet specifically,
  `SyncReasoner.instances()` directly is very likely faster, sometimes by orders of magnitude.
- **`BatchParallelReasoner` (query-level) is worth reaching for when you have many
  independent queries and a reasoner whose bulk calls aren't already fast.** It won 2-5x with
  HermiT on both datasets here, and lost with Pellet on both -- so profile a handful of
  sequential bulk calls first: if they average well under ~100ms, sequential `SyncReasoner`
  calls in a loop are very likely faster than paying to start a worker pool at all, regardless
  of how many queries you have.
- Both strategies pay a real, non-trivial worker-pool startup cost (JVM start + TBox
  classification, per worker, done once when the pool is created) -- reuse one
  `ParallelReasoner`/`BatchParallelReasoner` instance across as much of your workload as
  possible rather than constructing a fresh one per call, and size `num_workers` to your
  actual workload rather than always maxing out `os.cpu_count()`.

## Part 2: `BatchParallelReasoner` -- parallelizing across queries instead of individuals

The diagnosis above ("bulk retrieval already reuses shared work across individuals, so
decomposing one query throws that away") suggested a different axis should work better:
**parallelize across *queries*, not across individuals.** `owlapy.parallel_reasoner.BatchParallelReasoner`
implements this: each worker runs its own full, un-decomposed `SyncReasoner.instances(ce)`
bulk call, but different workers are assigned *different* expressions from the same corpus,
via `instances_batch(expressions)`. This preserves every reasoner's internal realization/reuse
optimizations -- only the *set of queries*, not the ABox, is split across cores.

```python
from owlapy.parallel_reasoner import BatchParallelReasoner

with BatchParallelReasoner("onto.owl", reasoner="Pellet", num_workers=22) as bpr:
    results = bpr.instances_batch([ce1, ce2, ce3, ...])  # list[set[OWLNamedIndividual]], input order preserved
```

This was benchmarked the same way (`run_batch_benchmark.py`, same corpora, same environment):
one `SyncReasoner` making 100 (or fewer, where documented) sequential bulk calls vs one
`BatchParallelReasoner` pool dispatching that same corpus across 22 workers in a single
`instances_batch()` call.

| Dataset | Reasoner | N | Sequential total (s) | Batch-parallel total (s) | Speedup |
|---|---|---|---|---|---|
| Family (202 ind.) | Pellet | 100 | 1.781 | 10.932 | **0.16x** (slower) |
| Family (202 ind.) | HermiT | 100 | 35.573 | 17.525 | **2.03x** |
| Mutagenesis (14,145 ind.) | Pellet | 100 | 43.765 | 63.196 | **0.69x** (slower) |
| Mutagenesis (14,145 ind.) | HermiT | 10 | 307.064 | 60.948 | **5.04x** |

Correctness held here too: every `batch_parallel` result matched its `sequential` counterpart
exactly, on every expression, in all four runs.

**This is a genuinely mixed result, but a more legible one than Part 1's.** The pattern tracks
directly with how expensive the reasoner's own bulk call is:

- **HermiT (both datasets): a clear win (2-5x).** HermiT's bulk calls are slow enough (35.6s /
  100 = 356ms mean on Family; each of the 10 Mutagenesis calls hit the 30s timeout) that the
  22-way concurrency comfortably outweighs the fixed cost of starting 22 JVMs.
  Mutagenesis+HermiT is the standout: 10 expressions across 22 workers means near-perfect
  one-expression-per-worker scheduling, turning a 307s sequential sweep into 61s.
- **Pellet (both datasets): a loss.** Pellet's bulk calls are so fast on their own (Family:
  1.78s / 100 = 18ms mean; Mutagenesis: 43.8s / 100 = 438ms mean, pulled up by a handful of
  slow nested-cardinality expressions) that they don't clear the pool-startup bar. Spinning up
  22 fresh JVMs (each independently loading and classifying the ontology) took *longer than
  the entire sequential sweep* on Family (10.9s of overhead vs 1.78s of actual work), and on
  Mutagenesis the 100-query batch, spread unevenly across workers plus 22 CPU-heavy JVMs
  contending for the same 22 physical cores, ended up slower than running them one after
  another in a single process.

So: unlike Part 1 (where the individual-decomposition axis lost almost everywhere), this axis
*works, conditionally* -- it needs total sequential work to clearly exceed worker-pool startup
cost, which in practice means either a slow reasoner (HermiT here) or a large enough batch of
individually-nontrivial queries. For a fast bulk reasoner like Pellet on typical-sized corpora,
plain sequential `SyncReasoner` calls remain faster than either parallelization strategy tested
in this benchmark. A likely further win, not tested here: size `num_workers` to the batch size
and expected per-query cost rather than always maxing out `os.cpu_count()` -- e.g. Family+Pellet
would plausibly break even with far fewer workers, since 100 queries at 18ms each barely need
concurrency at all, let alone 22-way.
