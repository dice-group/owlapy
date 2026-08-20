"""Benchmark BatchParallelReasoner against sequential SyncReasoner calls over a corpus of
class expressions, for one dataset + one Java reasoner backend.

Unlike run_benchmark.py (which parallelizes *within* one query, by individual), this
parallelizes *across* the whole expression corpus: each worker runs its own full, un-
decomposed SyncReasoner.instances(ce) bulk call per expression it's assigned.

Writes one row per expression per mode ("sequential" | "batch_parallel") to a CSV,
incrementally, plus a JSON metadata sidecar.

Usage:
    python run_batch_benchmark.py --ontology ../../KGs/Family/family-benchmark_rich_background.owl \
        --namespace http://www.benchmark.org/family# \
        --expressions expressions/family.txt --dataset family --reasoner Pellet \
        --out results/family_pellet_batch.csv --timeout 30
"""
import argparse
import csv
import json
import os
import time

from owlapy.owl_reasoner import SyncReasoner
from owlapy.parallel_reasoner import BatchParallelReasoner
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


def run(ontology_path: str, namespace: str, expressions_path: str, dataset: str, reasoner_name: str,
        out_csv: str, timeout: int, num_workers: int, limit: int):
    expressions = load_expressions(expressions_path, namespace, limit)
    n_workers = num_workers or os.cpu_count() or 1

    out_f = open(out_csv, "w", newline="")
    writer = csv.DictWriter(out_f, fieldnames=FIELDNAMES)
    writer.writeheader()

    def write_row(mode, idx, text, dt, n_results, status="ok", err=""):
        writer.writerow(dict(dataset=dataset, reasoner=reasoner_name, mode=mode, expr_index=idx,
                              expression=text, time_seconds=dt, n_results=n_results, status=status,
                              error_message=err))
        out_f.flush()

    # ---- Sequential: one SyncReasoner, one bulk call per expression, timed individually ----
    # Some generated expressions can trigger genuine bugs in the underlying Java reasoner
    # itself (observed: an ArrayIndexOutOfBoundsException deep in Pellet/Openllet's
    # realization code) -- caught and recorded as status="error" rather than aborting.
    sequential_results = {}
    t_seq_start = time.perf_counter()
    sync_reasoner = SyncReasoner(ontology=ontology_path, reasoner=reasoner_name)
    for idx, (text, ce) in enumerate(expressions):
        t0 = time.perf_counter()
        try:
            result = frozenset(str(i) for i in sync_reasoner.instances(ce, timeout=timeout))
            dt = time.perf_counter() - t0
            sequential_results[idx] = result
            write_row("sequential", idx, text, dt, len(result))
            print(f"[{dataset}/{reasoner_name}/sequential] {idx + 1}/{len(expressions)} {dt:.3f}s n={len(result)}")
        except Exception as e:  # noqa: BLE001 -- keep the sweep going on reasoner bugs
            dt = time.perf_counter() - t0
            write_row("sequential", idx, text, dt, 0, status="error", err=f"{type(e).__name__}: {e}"[:300])
            print(f"[{dataset}/{reasoner_name}/sequential] {idx + 1}/{len(expressions)} {dt:.3f}s ERROR")
    sync_reasoner.close()
    t_seq_total_wall = time.perf_counter() - t_seq_start

    # ---- Batch parallel: the whole corpus is dispatched in ONE instances_batch() call --
    #      that's the point, N workers picking up different expressions concurrently -- so
    #      there is only one wall-clock number for the entire batch, not one per expression.
    mismatches = []
    t_par_start = time.perf_counter()
    with BatchParallelReasoner(ontology_path, reasoner=reasoner_name, num_workers=n_workers) as bpr:
        results = bpr.instances_batch([ce for _text, ce in expressions], timeout=timeout)
    t_par_total_wall = time.perf_counter() - t_par_start
    # instances_batch dispatches the whole corpus in one go (that's the point -- N workers
    # picking up N different expressions concurrently), so we only have one wall-clock
    # number for the entire batch, not one per expression. Record it as a single row plus
    # per-expression result-size rows (time_seconds=0 for those, so totals aren't double
    # counted) so analyze_results.py's per-expression correctness check still works.
    write_row("batch_parallel_TOTAL", -1, "<whole corpus>", t_par_total_wall, sum(len(r) for r in results))
    for idx, ((text, _ce), result) in enumerate(zip(expressions, results)):
        result_iris = frozenset(str(i) for i in result)
        write_row("batch_parallel", idx, text, 0.0, len(result_iris))
        if idx in sequential_results and result_iris != sequential_results[idx]:
            mismatches.append(idx)

    out_f.close()

    meta = dict(dataset=dataset, reasoner=reasoner_name, ontology=ontology_path, n_expressions=len(expressions),
                num_workers=n_workers, timeout=timeout, cpu_count=os.cpu_count(),
                sequential_total_wall_seconds=t_seq_total_wall, batch_parallel_total_wall_seconds=t_par_total_wall,
                speedup=(t_seq_total_wall / t_par_total_wall) if t_par_total_wall > 0 else None,
                mismatches=mismatches)
    with open(out_csv.replace(".csv", ".meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\nsequential total wall time: {t_seq_total_wall:.3f}s")
    print(f"batch_parallel total wall time: {t_par_total_wall:.3f}s")
    print(f"speedup: {meta['speedup']:.2f}x" if meta["speedup"] else "speedup: n/a")
    if mismatches:
        print(f"WARNING: {len(mismatches)} expression(s) had sequential != batch_parallel results: {mismatches}")
    else:
        print("all batch_parallel results matched sequential results exactly")

    stopJVM()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ontology", required=True)
    ap.add_argument("--namespace", required=True)
    ap.add_argument("--expressions", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--reasoner", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=int, default=30, help="per-expression bulk-call timeout, in seconds")
    ap.add_argument("--num-workers", type=int, default=None)
    ap.add_argument("--limit", type=int, default=None, help="only run the first N expressions")
    args = ap.parse_args()

    run(args.ontology, args.namespace, args.expressions, args.dataset, args.reasoner,
        args.out, args.timeout, args.num_workers, args.limit)


if __name__ == "__main__":
    main()
