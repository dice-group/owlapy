"""Turn run_benchmark.py's CSV outputs into a markdown summary table.

Usage:
    python analyze_results.py results/*.csv
"""
import csv
import glob
import statistics
import sys
from collections import defaultdict


def load(csv_paths):
    # (dataset, reasoner, mode) -> ...
    times_wall = defaultdict(list)   # ok + timeout (real wall time spent, excludes crashes)
    times_ok = defaultdict(list)     # ok only (clean latency distribution)
    counts = defaultdict(lambda: {"ok": 0, "timeout": 0, "error": 0})
    for path in csv_paths:
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                key = (row["dataset"], row["reasoner"], row["mode"])
                status = row.get("status", "ok" if row.get("timed_out") != "True" else "timeout")
                counts[key][status] += 1
                t = float(row["time_seconds"])
                if status in ("ok", "timeout"):
                    times_wall[key].append(t)
                if status == "ok":
                    times_ok[key].append(t)
    return times_wall, times_ok, counts


def fmt(x):
    return f"{x:.3f}"


def main():
    csv_paths = []
    for arg in sys.argv[1:]:
        csv_paths.extend(sorted(glob.glob(arg)))
    if not csv_paths:
        print("no CSV files given/matched", file=sys.stderr)
        sys.exit(1)

    times_wall, times_ok, counts = load(csv_paths)

    keys = sorted({(d, r) for (d, r, _m) in times_wall} | {(d, r) for (d, r, _m) in times_ok})
    print("| Dataset | Reasoner | N (ok/timeout/error) B \\| P | Baseline total (s) | Parallel total (s) | "
          "Speedup (total) | Baseline mean (s) | Parallel mean (s) | Baseline p95 (s) | Parallel p95 (s) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for dataset, reasoner in keys:
        b_wall = times_wall.get((dataset, reasoner, "baseline"), [])
        p_wall = times_wall.get((dataset, reasoner, "parallel"), [])
        b_ok = times_ok.get((dataset, reasoner, "baseline"), [])
        p_ok = times_ok.get((dataset, reasoner, "parallel"), [])
        if not b_wall or not p_wall:
            continue
        b_total, p_total = sum(b_wall), sum(p_wall)
        speedup = b_total / p_total if p_total > 0 else float("inf")
        b_mean = statistics.mean(b_ok) if b_ok else float("nan")
        p_mean = statistics.mean(p_ok) if p_ok else float("nan")
        b_p95 = (statistics.quantiles(b_ok, n=20)[18] if len(b_ok) >= 20 else max(b_ok)) if b_ok else float("nan")
        p_p95 = (statistics.quantiles(p_ok, n=20)[18] if len(p_ok) >= 20 else max(p_ok)) if p_ok else float("nan")
        bc = counts[(dataset, reasoner, "baseline")]
        pc = counts[(dataset, reasoner, "parallel")]
        n_str = f"{bc['ok']}/{bc['timeout']}/{bc['error']} \\| {pc['ok']}/{pc['timeout']}/{pc['error']}"
        print(f"| {dataset} | {reasoner} | {n_str} | {fmt(b_total)} | {fmt(p_total)} | {speedup:.2f}x | "
              f"{fmt(b_mean)} | {fmt(p_mean)} | {fmt(b_p95)} | {fmt(p_p95)} |")


if __name__ == "__main__":
    main()
