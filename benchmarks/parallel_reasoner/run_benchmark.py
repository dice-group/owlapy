"""Benchmark ParallelReasoner against plain SyncReasoner over a corpus of class
expressions, for one dataset + one Java reasoner backend.

For each expression, in order: run a bulk `SyncReasoner.instances(ce)` call ("baseline")
and a `ParallelReasoner.instances(ce)` call ("parallel") against the same ontology and
the same reused reasoner/pool, and record wall time and the resulting instance set.
Reusing one SyncReasoner / one ParallelReasoner pool across all expressions means only
the *first* call pays JVM startup + TBox classification/loading cost -- this isolates
the steady-state per-query cost, which is what a real workload (e.g. scoring many
candidate concepts) would see.

Writes one row per (expression, mode) to a CSV incrementally (flushed after every row,
so a crash on expression N doesn't lose the timings for 1..N-1), plus a JSON metadata
sidecar written at the end. Some generated expressions can trigger genuine bugs in the
underlying Java reasoners themselves (observed: an ArrayIndexOutOfBoundsException deep in
Pellet/Openllet's realization code on a nested cardinality+complement+union expression on
Mutagenesis) -- those are recorded as status="error" rather than aborting the whole run.

IMPORTANT: per the project's JPype constraint (a JVM cannot be restarted once shut
down in the same process), this script only calls stopJVM() once, at the very end,
after the baseline SyncReasoner (which runs in this process) is done. ParallelReasoner's
workers run in separate spawned processes with their own JVMs and tear those down
independently on worker exit.

Usage:
    python run_benchmark.py --ontology ../../KGs/Family/family-benchmark_rich_background.owl \
        --namespace http://www.benchmark.org/family# \
        --expressions expressions/family.txt --dataset family --reasoner Pellet \
        --out results/family_pellet.csv --timeout 30
"""
import argparse
import csv
import json
import os
import time

from owlapy.owl_reasoner import SyncReasoner
from owlapy.parallel_reasoner import ParallelReasoner
from owlapy.parser import manchester_to_owl_expression
from owlapy.static_funcs import stopJVM

FIELDNAMES = ["dataset", "reasoner", "mode", "expr_index", "expression", "time_seconds", "n_results",
              "status", "error_message"]


def load_expressions(path: str, namespace: str, limit: int = None) -> list:
    with open(path) as f:
        lines = [line.strip() for line in f if line.strip()]
    if limit is not None:
        lines = lines[:limit]
    return [(text, manchester_to_owl_expression(text, namespace)) for text in lines]


def _call(fn, ce, timeout):
    """Run fn(ce, timeout=timeout), classifying the outcome. Never raises."""
    t0 = time.perf_counter()
    try:
        result = frozenset(str(i) for i in fn(ce, timeout=timeout))
        return result, time.perf_counter() - t0, "ok", ""
    except TimeoutError:
        return frozenset(), time.perf_counter() - t0, "timeout", ""
    except Exception as e:  # noqa: BLE001 -- deliberately broad: keep the sweep going on reasoner bugs
        return frozenset(), time.perf_counter() - t0, "error", f"{type(e).__name__}: {e}"[:300]


def run(ontology_path: str, namespace: str, expressions_path: str, dataset: str, reasoner_name: str,
        out_csv: str, timeout: int, per_individual_timeout: int, num_workers: int, limit: int):
    expressions = load_expressions(expressions_path, namespace, limit)
    n_workers = num_workers or os.cpu_count() or 1

    out_f = open(out_csv, "w", newline="")
    writer = csv.DictWriter(out_f, fieldnames=FIELDNAMES)
    writer.writeheader()

    def write_row(mode, idx, text, dt, result, status, err):
        writer.writerow(dict(dataset=dataset, reasoner=reasoner_name, mode=mode, expr_index=idx,
                              expression=text, time_seconds=dt, n_results=len(result),
                              status=status, error_message=err))
        out_f.flush()

    # ---- Baseline: one SyncReasoner, reused across all expressions ----
    baseline_results = {}
    sync_reasoner = SyncReasoner(ontology=ontology_path, reasoner=reasoner_name)
    for idx, (text, ce) in enumerate(expressions):
        result, dt, status, err = _call(sync_reasoner.instances, ce, timeout)
        baseline_results[idx] = (result, status)
        write_row("baseline", idx, text, dt, result, status, err)
        print(f"[{dataset}/{reasoner_name}/baseline] {idx + 1}/{len(expressions)} {dt:.3f}s "
              f"n={len(result)} status={status}")
    sync_reasoner.close()

    # ---- Parallel: one ParallelReasoner pool, reused across all expressions ----
    mismatches = []
    errors = []
    with ParallelReasoner(ontology_path, reasoner=reasoner_name, num_workers=n_workers) as pr:
        for idx, (text, ce) in enumerate(expressions):
            result, dt, status, err = _call(pr.instances, ce, per_individual_timeout)
            write_row("parallel", idx, text, dt, result, status, err)
            print(f"[{dataset}/{reasoner_name}/parallel]  {idx + 1}/{len(expressions)} {dt:.3f}s "
                  f"n={len(result)} status={status}")
            if status == "error":
                errors.append(idx)
            base_result, base_status = baseline_results.get(idx, (None, None))
            if status == "ok" and base_status == "ok" and result != base_result:
                mismatches.append(idx)

    out_f.close()

    meta = dict(dataset=dataset, reasoner=reasoner_name, ontology=ontology_path, n_expressions=len(expressions),
                num_workers=n_workers, timeout=timeout, per_individual_timeout=per_individual_timeout,
                cpu_count=os.cpu_count(), mismatches=mismatches, parallel_errors=errors)
    with open(out_csv.replace(".csv", ".meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\nwrote {2 * len(expressions)} rows to {out_csv}")
    if mismatches:
        print(f"WARNING: {len(mismatches)} expression(s) had baseline != parallel results: {mismatches}")
    else:
        print("all parallel results matched baseline results exactly (among expressions where both succeeded)")

    stopJVM()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ontology", required=True)
    ap.add_argument("--namespace", required=True)
    ap.add_argument("--expressions", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--reasoner", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=int, default=30,
                     help="baseline SyncReasoner.instances() bulk timeout, in seconds. Must be an integer -- "
                          "JPype's Future.get(timeout, TimeUnit.SECONDS) only accepts a Java long, not a float.")
    ap.add_argument("--per-individual-timeout", type=int, default=None,
                     help="ParallelReasoner per-individual is_entailed() timeout, in seconds. This is NOT "
                          "the same budget as --timeout: it bounds a single individual's check, not the whole "
                          "query, so it must be much smaller for large ABoxes -- otherwise several slow "
                          "individuals queuing up sequentially on one worker can multiply the wall-clock cost "
                          "well past --timeout. Defaults to --timeout for small ABoxes where this doesn't matter.")
    ap.add_argument("--num-workers", type=int, default=None)
    ap.add_argument("--limit", type=int, default=None, help="only run the first N expressions")
    args = ap.parse_args()

    per_individual_timeout = args.per_individual_timeout if args.per_individual_timeout is not None else args.timeout
    run(args.ontology, args.namespace, args.expressions, args.dataset, args.reasoner,
        args.out, args.timeout, per_individual_timeout, args.num_workers, args.limit)


if __name__ == "__main__":
    main()
