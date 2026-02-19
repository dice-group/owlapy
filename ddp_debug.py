"""
Debug Single Expression — Distributed vs Ground-Truth OWL Reasoning
====================================================================

Additional dependency: pip install ray

This script evaluates a **single** OWL class expression across three
reasoning approaches and prints a detailed diagnostic report:

  1. Ground Truth   — SyncReasoner on the complete (unsharded) ontology
  2. Open-World     — DistributedReasoner (open_world=True): each shard
                      evaluates the full CE independently, results are unioned.

The report shows:
  • Instance counts and runtime for each approach
  • Set comparison (missing / extra individuals)
  • Per-shard breakdowns (which shard contributed what)
  • Jaccard and F1 similarity metrics

Usage
-----
  # Default expression (∃hasAtom.Nitrogen on Mutagenesis):
  python ddp_debug.py --auto_ray --num_shards 4

  # Custom DL expression (parsed automatically):
  python ddp_debug.py --auto_ray --num_shards 4 \\
      --expression "∃hasAtom.Carbon"

  # Custom ontology, namespace, reasoner:
  python ddp_debug.py --auto_ray --num_shards 8 \\
      --path_kg KGs/Family/family-benchmark_rich_background.owl \\
      --ns "http://www.benchmark.org/family#" \\
      --expression "∃hasChild.Female" \\
      --reasoner HermiT

  # Show individual IRIs in the diff (can be large):
  python ddp_debug.py --auto_ray --num_shards 4 --show_individuals

  # Show per-shard breakdown:
  python ddp_debug.py --auto_ray --num_shards 4 --show_shards
"""

import argparse
import os
import sys
import time

import ray
from pathlib import Path

from owlapy.owl_reasoner import SyncReasoner
from owlapy.class_expression import (
    OWLClassExpression, OWLClass,
    OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom,
    OWLObjectUnionOf, OWLObjectIntersectionOf, OWLObjectComplementOf,
    OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality,
    OWLObjectHasValue, OWLObjectOneOf,
)
from owlapy.owl_property import OWLObjectProperty
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.iri import IRI
from owlapy import owl_expression_to_dl
from owlapy.parser import dl_to_owl_expression
from owlapy.utils import jaccard_similarity, f1_set_similarity

from ddp_reasoning import ShardReasoner, DistributedReasoner, CrossShardReasoner
from shard_ontology import shard_ontology


# ── Helpers ──────────────────────────────────────────────────────────

def to_iri_set(individuals):
    """Convert a set of OWLNamedIndividual to a set of IRI strings."""
    return {ind.str for ind in individuals}


def timed_retrieval(reasoner, ce):
    """Return (iri_set, elapsed_seconds)."""
    start = time.perf_counter()
    results = to_iri_set(reasoner.instances(ce))
    elapsed = time.perf_counter() - start
    return results, elapsed


def print_set_diff(label_a, set_a, label_b, set_b, show_individuals):
    """Print a readable diff between two IRI sets."""
    missing = sorted(set_a - set_b)
    extra = sorted(set_b - set_a)
    common = set_a & set_b

    print(f"\n  Common to both: {len(common)}")
    print(f"  In {label_a} but NOT in {label_b} (missing): {len(missing)}")
    print(f"  In {label_b} but NOT in {label_a} (extra):   {len(extra)}")

    if show_individuals:
        if missing:
            print(f"\n  --- Missing from {label_b} ---")
            for iri in missing[:50]:
                print(f"    {iri}")
            if len(missing) > 50:
                print(f"    ... and {len(missing) - 50} more")
        if extra:
            print(f"\n  --- Extra in {label_b} ---")
            for iri in extra[:50]:
                print(f"    {iri}")
            if len(extra) > 50:
                print(f"    ... and {len(extra) - 50} more")


def print_shard_breakdown(shards, ce):
    """Query each shard individually and print per-shard instance counts."""
    print("\n  Per-shard breakdown (open-world, full CE per shard):")
    total = set()
    for i, shard in enumerate(shards):
        shard_iris = ray.get(shard.query_instances.remote(ce, False))
        total |= shard_iris
        print(f"    Shard-{i}: {len(shard_iris):>6} instances")
    print(f"    Union:   {len(total):>6} instances")
    return total


def print_shard_intermediate_breakdown(shards, ce):
    """Query each shard for intermediate results and print per sub-CE counts."""
    print("\n  Per-shard intermediate results:")
    all_shard_results = []
    for i, shard in enumerate(shards):
        res = ray.get(shard.query_instances_with_intermediate.remote(ce, False))
        all_shard_results.append(res)
        print(f"    Shard-{i}:")
        for ce_str, iris in sorted(res.items(), key=lambda x: len(x[0])):
            print(f"      {ce_str[:80]:<80s}  -> {len(iris)} instances")
    return all_shard_results


# ── Predefined expressions (Mutagenesis) ────────────────────────────

def get_predefined_expressions(ns):
    """Return a dict of name -> OWLClassExpression for quick selection."""
    carbon   = OWLClass(IRI(ns, "Carbon"))
    nitrogen = OWLClass(IRI(ns, "Nitrogen"))
    oxygen   = OWLClass(IRI(ns, "Oxygen"))
    hydrogen = OWLClass(IRI(ns, "Hydrogen"))
    atom     = OWLClass(IRI(ns, "Atom"))
    bond     = OWLClass(IRI(ns, "Bond"))
    bond1    = OWLClass(IRI(ns, "Bond-1"))
    bond2    = OWLClass(IRI(ns, "Bond-2"))
    ring     = OWLClass(IRI(ns, "Ring"))

    has_atom      = OWLObjectProperty(IRI(ns, "hasAtom"))
    has_bond      = OWLObjectProperty(IRI(ns, "hasBond"))
    has_structure  = OWLObjectProperty(IRI(ns, "hasStructure"))
    in_bond       = OWLObjectProperty(IRI(ns, "inBond"))

    return {
        "Nitrogen": nitrogen,

        "∃hasAtom.Nitrogen": OWLObjectSomeValuesFrom(
            property=has_atom, filler=nitrogen
        ),

        "∃hasAtom.Carbon": OWLObjectSomeValuesFrom(
            property=has_atom, filler=carbon
        ),

        "∃hasAtom.Carbon ⊔ ∃hasAtom.Nitrogen": OWLObjectUnionOf([
            OWLObjectSomeValuesFrom(property=has_atom, filler=carbon),
            OWLObjectSomeValuesFrom(property=has_atom, filler=nitrogen),
        ]),

        "∃hasAtom.(Carbon ⊓ ∃inBond.Bond)": OWLObjectSomeValuesFrom(
            property=has_atom,
            filler=OWLObjectIntersectionOf([
                carbon,
                OWLObjectSomeValuesFrom(property=in_bond, filler=bond),
            ]),
        ),

        "∃hasAtom.(Carbon ⊓ ∃inBond.Bond-1)": OWLObjectSomeValuesFrom(
            property=has_atom,
            filler=OWLObjectIntersectionOf([
                carbon,
                OWLObjectSomeValuesFrom(property=in_bond, filler=bond1),
            ]),
        ),

        "(∃hasAtom.C ⊓ ∃hasBond.Bond) ⊔ (∃hasAtom.N ⊓ ∃hasBond.Bond)": OWLObjectUnionOf([
            OWLObjectIntersectionOf([
                OWLObjectSomeValuesFrom(property=has_atom, filler=carbon),
                OWLObjectSomeValuesFrom(property=has_bond, filler=bond),
            ]),
            OWLObjectIntersectionOf([
                OWLObjectSomeValuesFrom(property=has_atom, filler=nitrogen),
                OWLObjectSomeValuesFrom(property=has_bond, filler=bond),
            ]),
        ]),

        "∃hasAtom.((Carbon ⊔ Nitrogen) ⊓ ∃inBond.Bond)": OWLObjectSomeValuesFrom(
            property=has_atom,
            filler=OWLObjectIntersectionOf([
                OWLObjectUnionOf([carbon, nitrogen]),
                OWLObjectSomeValuesFrom(property=in_bond, filler=bond),
            ]),
        ),
    }


# ── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Debug a single OWL class expression: Ground Truth vs Distributed Reasoning"
    )
    parser.add_argument(
        "--path_kg", type=str,
        default="KGs/Mutagenesis/mutagenesis.owl",
        help="Path to the OWL ontology file",
    )
    parser.add_argument(
        "--num_shards", type=int, default=4,
        help="Number of shards for distributed reasoning",
    )
    parser.add_argument(
        "--ns", type=str,
        default="http://dl-learner.org/mutagenesis#",
        help="Namespace URI for the ontology",
    )
    parser.add_argument(
        "--reasoner", type=str, default="Pellet",
        help="Reasoner backend (Pellet, HermiT, ...)",
    )
    parser.add_argument(
        "--expression", type=str, default=None,
        help=(
            "DL expression to debug (e.g. '∃hasAtom.Nitrogen'). "
            "If omitted, the default predefined expression is used."
        ),
    )
    parser.add_argument(
        "--list_predefined", action="store_true",
        help="List available predefined expressions and exit.",
    )
    parser.add_argument(
        "--show_individuals", action="store_true",
        help="Print individual IRIs in the set diff (can be large).",
    )
    parser.add_argument(
        "--show_shards", action="store_true",
        help="Print per-shard breakdowns.",
    )
    parser.add_argument(
        "--auto_ray", action="store_true", default=False,
        help="Start Ray in-process automatically (no manual 'ray start' needed).",
    )
    parser.add_argument(
        "--cross_shard", action="store_true", default=False,
        help="Use CrossShardReasoner for open-world distributed reasoning (default: DistributedReasoner)",
    )
    args = parser.parse_args()

    # ── List predefined and exit ─────────────────────────────────────
    if args.list_predefined:
        predefined = get_predefined_expressions(args.ns)
        print("Available predefined expressions:")
        for name in predefined:
            print(f"  {name}")
        return

    # ── Resolve the expression ───────────────────────────────────────
    predefined = get_predefined_expressions(args.ns)

    if args.expression is None:
        # Default expression
        expr_name = "∃hasAtom.Nitrogen"
        ce = predefined[expr_name]
    elif args.expression in predefined:
        expr_name = args.expression
        ce = predefined[expr_name]
    else:
        # Try to parse the DL string
        expr_name = args.expression
        try:
            ce = dl_to_owl_expression(args.expression, args.ns)
        except Exception as e:
            print(f"ERROR: Could not parse expression '{args.expression}': {e}")
            print("Hint: use --list_predefined to see built-in expressions,")
            print("      or provide a valid DL expression string.")
            sys.exit(1)

    dl_str = owl_expression_to_dl(ce)
    print("=" * 80)
    print("DDP DEBUG — Single Expression Evaluation")
    print("=" * 80)
    print(f"  Ontology:    {args.path_kg}")
    print(f"  Namespace:   {args.ns}")
    print(f"  Reasoner:    {args.reasoner}")
    print(f"  Num shards:  {args.num_shards}")
    print(f"  Expression:  {dl_str}")
    print(f"  Python repr: {ce}")
    print("=" * 80)

    # ── Initialize Ray ───────────────────────────────────────────────
    if not ray.is_initialized():
        if args.auto_ray:
            num_cpus = os.cpu_count()
            shard_resources = {f"shard_{i}": 1 for i in range(args.num_shards)}
            print(f"\n[auto_ray] Starting local Ray cluster with {num_cpus} CPUs")
            ray.init(num_cpus=num_cpus, resources=shard_resources)
        else:
            print("\n[manual_ray] Connecting to existing Ray cluster ...")
            ray.init(address="auto")

    # ── Ground-truth reasoner ────────────────────────────────────────
    assert os.path.isfile(args.path_kg), f"Ontology not found: {args.path_kg}"
    print("\n[1/3] Loading ground-truth reasoner (complete ontology) ...")
    gt_reasoner = SyncReasoner(ontology=args.path_kg, reasoner=args.reasoner)

    # ── Shard setup ──────────────────────────────────────────────────
    print(f"[2/3] Setting up {args.num_shards} shard(s) ...")
    ontology_stem = Path(args.path_kg).stem
    base_dir = str(Path(args.path_kg).parent)

    if args.num_shards > 1:
        all_exist = all(
            (Path(base_dir) / f"{ontology_stem}_shard_{i}.owl").exists()
            for i in range(args.num_shards)
        )
        extra = (Path(base_dir) / f"{ontology_stem}_shard_{args.num_shards}.owl").exists()
        if not all_exist or extra:
            print(f"  [auto-shard] Generating {args.num_shards} shards ...")
            shard_ontology(args.path_kg, args.num_shards, base_dir)

    shards = []
    for i in range(args.num_shards):
        shard_path = (
            args.path_kg
            if args.num_shards == 1
            else str(Path(base_dir) / f"{ontology_stem}_shard_{i}.owl")
        )
        shard = ShardReasoner.options(resources={f"shard_{i}": 1}).remote(
            f"Shard-{i}", shard_path, args.reasoner
        )
        shards.append(shard)

    # Setup open-world distributed reasoner
    if args.cross_shard:
        open_world_reasoner = CrossShardReasoner(shards, open_world=True)
    else:
        open_world_reasoner = DistributedReasoner(shards, open_world=True)

    # ── Evaluate ─────────────────────────────────────────────────────
    print(f"\n[3/3] Evaluating expression: {dl_str}")
    print("=" * 80)

    # Ground truth
    print("\n--- Ground Truth (SyncReasoner on complete ontology) ---")
    gt_iris, gt_time = timed_retrieval(gt_reasoner, ce)
    print(f"  Instances: {len(gt_iris)}")
    print(f"  Runtime:   {gt_time * 1000:.1f} ms")

    # Open-world distributed
    print("\n--- Open-World Distributed (union shard results, no decomposition) ---")
    ow_iris, ow_time = timed_retrieval(open_world_reasoner, ce)
    print(f"  Instances: {len(ow_iris)}")
    print(f"  Runtime:   {ow_time * 1000:.1f} ms")

    # ── Comparison ───────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)

    ow_jaccard = jaccard_similarity(gt_iris, ow_iris)
    ow_f1      = f1_set_similarity(gt_iris, ow_iris)
    ow_match   = gt_iris == ow_iris

    hdr = f"{'Approach':<35} {'Count':>7} {'Time(ms)':>10} {'Jaccard':>9} {'F1':>9} {'Match':>7}"
    print(hdr)
    print("-" * len(hdr))
    print(f"{'Ground Truth':<35} {len(gt_iris):>7} {gt_time*1000:>10.1f} {'—':>9} {'—':>9} {'—':>7}")
    print(
        f"{'Open-World Distributed':<35} {len(ow_iris):>7} {ow_time*1000:>10.1f} "
        f"{ow_jaccard:>9.4f} {ow_f1:>9.4f} {'✓' if ow_match else '✗':>7}"
    )

    # ── Set diffs ────────────────────────────────────────────────────
    if not ow_match:
        print("\n--- Open-World vs Ground Truth (diff) ---")
        print_set_diff("GT", gt_iris, "OpenWorld", ow_iris, args.show_individuals)
    else:
        print("\n✓ Open-World distributed matches the ground truth exactly.")

    # ── Per-shard breakdown ──────────────────────────────────────────
    if args.show_shards:
        print("\n" + "=" * 80)
        print("PER-SHARD BREAKDOWN")
        print("=" * 80)
        print_shard_breakdown(shards, ce)
        print_shard_intermediate_breakdown(shards, ce)

    print("\n" + "=" * 80)
    print("DEBUG SESSION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
