"""
Batch Evaluation of Distributed OWL Reasoning
==============================================

Runs ddp_reasoning_eval.py sequentially on every ontology in the KGs/
directory (excluding shard partitions) and collects results into a
timestamped output folder with per-ontology CSVs, logs, and an
aggregated summary table.

Usage
-----
  python run_all_evals.py --num_shards 8 --auto_ray
  python run_all_evals.py --num_shards 16 --auto_ray --reasoner HermiT

Output structure
----------------
  results/YYYY-MM-DD_HH-MM-SS_s8_Pellet_HermiT/
    ├── config.json                          # full run config for reproducibility
    ├── Pellet/
    │   ├── summary.csv                      # aggregated metrics for Pellet
    │   ├── summary.tex                      # LaTeX table for Pellet
    │   ├── Biopax/
    │   │   ├── eval_results.csv
    │   │   ├── eval_results_skipped.csv     # (if any CEs were skipped)
    │   │   └── eval.log
    │   └── ...
    ├── HermiT/
    │   ├── summary.csv
    │   ├── summary.tex
    │   ├── Biopax/
    │   │   └── ...
    │   └── ...
"""

import os
import sys
import glob
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from argparse import ArgumentParser


def discover_ontologies(kg_dir: str) -> list:
    """Find all non-shard .owl files under kg_dir, sorted by file size (ascending)."""
    all_owl = glob.glob(os.path.join(kg_dir, "**", "*.owl"), recursive=True)
    # Exclude shard partitions (files matching *_shard_N.owl)
    import re
    shard_pattern = re.compile(r"_shard_\d+\.owl$")
    ontologies = [p for p in all_owl if not shard_pattern.search(p)]
    # Sort by file size (smallest first) for faster early feedback
    ontologies.sort(key=lambda p: os.path.getsize(p))
    return ontologies


def build_eval_command(owl_path: str, args, output_csv: str) -> list:
    """Build the command line for a single ddp_reasoning_eval.py run."""
    cmd = [
        sys.executable, "ddp_reasoning_eval.py",
        "--path_kg", owl_path,
        "--num_shards", str(args.num_shards),
        "--reasoner", args.reasoner,
        "--seed", str(args.seed),
        "--num_nominals", str(args.num_nominals),
        "--path_report", output_csv,
    ]
    if args.auto_ray:
        cmd.append("--auto_ray")
    if args.no_negations:
        cmd.append("--no_negations")
    if args.no_universal:
        cmd.append("--no_universal")
    if args.ratio_sample_nc is not None:
        cmd.extend(["--ratio_sample_nc", str(args.ratio_sample_nc)])
    if args.ratio_sample_object_prop is not None:
        cmd.extend(["--ratio_sample_object_prop", str(args.ratio_sample_object_prop)])
    if args.verbose:
        cmd.append("--verbose")
    if args.timeout is not None:
        cmd.extend(["--timeout", str(args.timeout)])
    return cmd


def ontology_label(owl_path: str) -> str:
    """Derive a clean label from the ontology path (e.g. 'Family', 'Biopax')."""
    p = Path(owl_path)
    # If the .owl is inside a named subfolder, use the folder name
    if p.parent.name != "KGs":
        return p.parent.name
    # Otherwise use the stem (e.g. UNIV-BENCH-OWL2DL)
    return p.stem


def generate_summary(results: list, output_dir: str, args):
    """Write summary.csv and summary.tex from collected per-ontology results."""
    import pandas as pd

    rows = []
    for r in results:
        if r["status"] != "success" or r["csv_path"] is None:
            rows.append({
                "Ontology": r["label"],
                "Status": r["status"],
                "Num CEs": None,
                "Skipped CEs": r.get("num_skipped", 0),
                "Mean Jaccard": None,
                "Mean F1": None,
                "Mean Speedup": None,
                "Runtime (s)": r["runtime_s"],
            })
            continue

        df = pd.read_csv(r["csv_path"])
        num_ces = len(df)
        mean_jaccard = df["Jaccard Similarity"].mean()
        mean_f1 = df["F1"].mean()
        # Avoid division by zero
        df["Speedup"] = df["Runtime Ground Truth"] / df["Runtime Distributed"].clip(lower=1e-6)
        mean_speedup = df["Speedup"].mean()

        rows.append({
            "Ontology": r["label"],
            "Status": "success",
            "Num CEs": num_ces,
            "Skipped CEs": r.get("num_skipped", 0),
            "Mean Jaccard": round(mean_jaccard, 4),
            "Mean F1": round(mean_f1, 4),
            "Mean Speedup": round(mean_speedup, 2),
            "Runtime (s)": round(r["runtime_s"], 1),
        })

    summary_df = pd.DataFrame(rows)
    summary_csv = os.path.join(output_dir, "summary.csv")
    summary_df.to_csv(summary_csv, index=False)
    print(f"\nSummary saved to {summary_csv}")

    # LaTeX table
    latex_lines = []
    latex_lines.append(r"\begin{table}[htbp]")
    latex_lines.append(r"\centering")
    latex_lines.append(r"\caption{Distributed OWL Reasoning Evaluation (%d shards, %s reasoner)}" % (args.num_shards, args.reasoner))
    latex_lines.append(r"\label{tab:ddp-eval-batch}")
    latex_lines.append(r"\small")
    latex_lines.append(r"\begin{tabular}{l r r r r r r}")
    latex_lines.append(r"\toprule")
    latex_lines.append(r"\textbf{Ontology} & \textbf{\#CEs} & \textbf{Skipped} & \textbf{Jaccard} & \textbf{F1} & \textbf{Speedup} & \textbf{Time (s)} \\")
    latex_lines.append(r"\midrule")
    for _, row in summary_df.iterrows():
        if row["Status"] != "success":
            latex_lines.append(
                r"%s & \multicolumn{6}{c}{\textit{%s}} \\" % (row["Ontology"], row["Status"])
            )
        else:
            latex_lines.append(
                r"%s & %d & %d & %.4f & %.4f & %.2f$\times$ & %.1f \\" % (
                    row["Ontology"],
                    row["Num CEs"],
                    row["Skipped CEs"],
                    row["Mean Jaccard"],
                    row["Mean F1"],
                    row["Mean Speedup"],
                    row["Runtime (s)"],
                )
            )
    latex_lines.append(r"\bottomrule")
    latex_lines.append(r"\end{tabular}")
    latex_lines.append(r"\end{table}")

    latex_str = "\n".join(latex_lines)
    latex_path = os.path.join(output_dir, "summary.tex")
    with open(latex_path, "w", encoding="utf-8") as f:
        f.write(latex_str)
    print(f"LaTeX table saved to {latex_path}")

    # Print summary to stdout
    print("\n" + "=" * 80)
    print("BATCH EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Reasoner: {args.reasoner}  |  Shards: {args.num_shards}  |  Seed: {args.seed}")
    print("-" * 80)
    print(summary_df.to_string(index=False))
    print("=" * 80)

    return summary_df


def run_eval_for_reasoner(ontologies, reasoner, output_dir, args):
    """Run evaluation on all ontologies for a single reasoner."""
    reasoner_dir = os.path.join(output_dir, reasoner)
    os.makedirs(reasoner_dir, exist_ok=True)

    # Override reasoner in args for command building
    args_copy = type(args)()  # shallow namespace copy
    for k, v in vars(args).items():
        setattr(args_copy, k, v)
    args_copy.reasoner = reasoner

    results = []
    for i, owl_path in enumerate(ontologies):
        label = ontology_label(owl_path)
        onto_dir = os.path.join(reasoner_dir, label)
        os.makedirs(onto_dir, exist_ok=True)

        csv_path = os.path.join(onto_dir, "eval_results.csv")
        log_path = os.path.join(onto_dir, "eval.log")

        print(f"\n{'='*80}")
        print(f"[{reasoner}] [{i+1}/{len(ontologies)}] {label}  ({owl_path})")
        print(f"{'='*80}")

        # Skip if results already exist
        if args.skip_existing and os.path.isfile(csv_path):
            print(f"  [SKIP] Results already exist: {csv_path}")
            # Still collect results for the summary
            skipped_csv = csv_path.replace(".csv", "_skipped.csv")
            num_skipped = 0
            if os.path.isfile(skipped_csv):
                import pandas as pd
                num_skipped = len(pd.read_csv(skipped_csv))
            results.append({
                "label": label,
                "owl_path": owl_path,
                "status": "success",
                "runtime_s": 0.0,
                "csv_path": csv_path,
                "log_path": log_path if os.path.isfile(log_path) else None,
                "num_skipped": num_skipped,
            })
            continue

        cmd = build_eval_command(owl_path, args_copy, csv_path)
        print(f"Command: {' '.join(cmd)}")

        start = time.time()
        try:
            with open(log_path, "w") as log_f:
                proc = subprocess.run(
                    cmd,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    timeout=None,  # no timeout — let each ontology run to completion
                )
            elapsed = time.time() - start
            status = "success" if proc.returncode == 0 else f"failed (rc={proc.returncode})"
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            status = "timeout"
        except Exception as e:
            elapsed = time.time() - start
            status = f"error: {e}"

        # Count skipped CEs if the skipped CSV exists
        skipped_csv = csv_path.replace(".csv", "_skipped.csv")
        num_skipped = 0
        if os.path.isfile(skipped_csv):
            import pandas as pd
            num_skipped = len(pd.read_csv(skipped_csv))

        results.append({
            "label": label,
            "owl_path": owl_path,
            "status": status,
            "runtime_s": round(elapsed, 1),
            "csv_path": csv_path if os.path.isfile(csv_path) else None,
            "log_path": log_path,
            "num_skipped": num_skipped,
        })

        print(f"  Status: {status}  |  Runtime: {elapsed:.1f}s  |  Skipped: {num_skipped}")

    # Per-reasoner summary
    args_copy.reasoner = reasoner
    generate_summary(results, reasoner_dir, args_copy)

    return results


def main():
    parser = ArgumentParser(description="Run DDP reasoning eval on all ontologies in KGs/")
    parser.add_argument("--kg_dir", type=str, default="KGs",
                        help="Root directory containing ontology subdirectories")
    parser.add_argument("--output_dir", type=str, default=None,
                        help="Output directory (default: results/<timestamp>)")
    parser.add_argument("--num_shards", type=int, default=8)
    parser.add_argument("--reasoners", type=str, nargs="+", default=["Pellet", "HermiT"],
                        help="Reasoners to evaluate, in order (default: Pellet HermiT)")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--num_nominals", type=int, default=10)
    parser.add_argument("--auto_ray", action="store_true", default=False)
    parser.add_argument("--no_negations", action="store_true")
    parser.add_argument("--no_universal", action="store_true")
    parser.add_argument("--ratio_sample_nc", type=float, default=None)
    parser.add_argument("--ratio_sample_object_prop", type=float, default=None)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--timeout", type=float, default=10,
                        help="Timeout in seconds per CE for the GT reasoner (default: 10)")
    parser.add_argument("--skip_existing", action="store_true",
                        help="Skip ontologies that already have eval_results.csv in the output directory")
    args = parser.parse_args()

    # Discover ontologies
    ontologies = discover_ontologies(args.kg_dir)
    if not ontologies:
        print(f"No .owl files found in {args.kg_dir}")
        sys.exit(1)

    print(f"Found {len(ontologies)} ontologies (sorted by size, ascending):")
    for owl in ontologies:
        size_kb = os.path.getsize(owl) / 1024
        print(f"  - {ontology_label(owl):30s} {size_kb:>8.1f} KB  ({owl})")

    print(f"\nReasoners to evaluate (in order): {args.reasoners}")

    # Create output directory
    if args.output_dir is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        reasoner_tag = "_".join(args.reasoners)
        output_dir = os.path.join("results", f"{timestamp}_s{args.num_shards}_{reasoner_tag}")
    else:
        output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Save run configuration for reproducibility
    config = vars(args).copy()
    config["ontologies"] = ontologies
    config["timestamp"] = datetime.now().isoformat()
    with open(os.path.join(output_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=2)

    # Run evaluations: all ontologies per reasoner, reasoners in order
    all_results = {}
    for reasoner in args.reasoners:
        print(f"\n{'#'*80}")
        print(f"# REASONER: {reasoner}")
        print(f"{'#'*80}")
        all_results[reasoner] = run_eval_for_reasoner(ontologies, reasoner, output_dir, args)

    print(f"\nAll results saved to: {output_dir}/")


if __name__ == "__main__":
    main()
