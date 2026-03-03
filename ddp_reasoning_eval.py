"""
Evaluation of Distributed OWL Reasoning
========================================

Additional dependency: pip install ray

Overview
--------
This script evaluates the BaseShardReasoner from ddp_reasoning.py against
a SyncReasoner ground truth.  It automatically generates OWL class expressions
of increasing complexity (named classes, negations, unions, intersections,
existential / universal restrictions, cardinality restrictions, nominals) and
compares the retrieval results (Jaccard similarity, F1, runtime).

Usage
-----
  # Fully automatic — no terminal setup needed:
  python ddp_reasoning_eval.py --auto_ray --num_shards 16 \\
      --path_kg KGs/Mutagenesis/mutagenesis.owl

  # Subsample classes / properties for faster runs:
  python ddp_reasoning_eval.py --auto_ray --num_shards 16 \\
      --path_kg KGs/Mutagenesis/mutagenesis.owl \\
      --ratio_sample_nc 0.01 --ratio_sample_object_prop 0.01

  # Use a different reasoner backend:
  python ddp_reasoning_eval.py --auto_ray --num_shards 4 \\
      --path_kg KGs/Family/family-benchmark_rich_background.owl \\
      --reasoner HermiT

  # Manual Ray cluster (start Ray head node first in a separate terminal):
  #   ray start --head --port=6379 \\
  #       --resources='{"shard_0":1,"shard_1":1,"shard_2":1,"shard_3":1}'
  python ddp_reasoning_eval.py --path_kg KGs/Mutagenesis/mutagenesis.owl --num_shards 4

CLI Arguments
-------------
  --path_kg       Path to the OWL ontology file
                  (default: KGs/Family/family-benchmark_rich_background.owl).
  --num_shards    Number of shards / Ray workers  (default: 1).
  --reasoner      OWL reasoner backend: Pellet (default) or HermiT.
  --auto_ray      When set, Ray is initialised in-process using all available
                  CPU cores and the required shard custom resources.
                  Shard .owl files are generated automatically if missing.
                  When not set, the script connects to an existing Ray cluster
                  started via `ray start --head ...`.
  --seed          Random seed for reproducibility (default: 1).
  --ratio_sample_nc            Ratio of OWL Classes to sample without replacement
                               (0.0-1.0). None (default) = no sampling.
  --ratio_sample_object_prop   Ratio of OWL Object Properties to sample without
                               replacement (0.0-1.0). None (default) = no sampling.
  --min_jaccard_similarity     Minimum mean Jaccard similarity threshold.
  --num_nominals  Number of OWL named individuals to sample for nominals.
  --path_report   Path to save the evaluation results CSV.
  --no_negations  Exclude negation-based expressions (¬C, ∀r.C) from evaluation.

Distributed Setup (multi-machine)
----------------------------------
Each physical machine runs `ray start` in its own terminal. The head node
registers shard_0; every additional worker registers its own shard resource.
The driver script can then be run from any machine that can reach the head.

  2 machines (1 shard each):
    Machine 1: ray start --head --port=6379 --resources='{"shard_0": 1}'
    Machine 2: ray start --address='<HEAD_IP>:6379' --resources='{"shard_1": 1}'
    Driver:    python ddp_reasoning_eval.py --path_kg KGs/Mutagenesis/mutagenesis.owl --num_shards 2

  4 machines (1 shard each):
    Machine 1: ray start --head --port=6379 --resources='{"shard_0": 1}'
    Machine 2: ray start --address='<HEAD_IP>:6379' --resources='{"shard_1": 1}'
    Machine 3: ray start --address='<HEAD_IP>:6379' --resources='{"shard_2": 1}'
    Machine 4: ray start --address='<HEAD_IP>:6379' --resources='{"shard_3": 1}'
    Driver:    python ddp_reasoning_eval.py --path_kg KGs/Mutagenesis/mutagenesis.owl --num_shards 4

  Multiple shards per machine (declare several resources on one node):
    Machine 1: ray start --head --port=6379 \\
                   --resources='{"shard_0":1,"shard_1":1,"shard_2":1,"shard_3":1}'
    Driver:    python ddp_reasoning_eval.py --path_kg KGs/Mutagenesis/mutagenesis.owl --num_shards 4

Docs: https://docs.ray.io/en/latest/ray-core/configure.html#cluster-resources



Regression Test: Cross-Shard Inference

Regression testing: Any code change should be tested with the following command to ensure that distributed reasoning results remain consistent.  The test runs both reasoners on a complex CE and compares their answers for consistency (OWA vs CWA differences are expected for cardinality).

python ddp_reasoning_eval.py --auto_ray --num_shards 20 --path_kg KGs/Mutagenesis/mutagenesis.owl

======================================================================
EVALUATION SUMMARY
======================================================================

Expression Type Counts:
Type
OWLClass                    17
OWLObjectAllValuesFrom      17
OWLObjectIntersectionOf    152
OWLObjectMaxCardinality     51
OWLObjectMinCardinality     51
OWLObjectSomeValuesFrom    137
OWLObjectUnionOf           152
Name: Type, dtype: int64

Mean Metrics by Type:
                         Jaccard Similarity  F1   Runtime Benefits  Runtime Ground Truth  Runtime Distributed
Type                                                                                                         
OWLClass                 1.0                 1.0  0.000442          0.013348              0.012906           
OWLObjectAllValuesFrom   1.0                 1.0 -0.011999          0.020150              0.032149           
OWLObjectIntersectionOf  1.0                 1.0 -0.009181          0.007764              0.016945           
OWLObjectMaxCardinality  1.0                 1.0 -0.014382          0.017747              0.032129           
OWLObjectMinCardinality  1.0                 1.0  0.448223          0.612016              0.163792           
OWLObjectSomeValuesFrom  1.0                 1.0  0.427984          0.639472              0.211488           
OWLObjectUnionOf         1.0                 1.0 -0.079293          0.029787              0.109080           

----------------------------------------------------------------------
Overall Statistics:
  Total expressions evaluated: 577
  Mean Jaccard Similarity: 1.0000
  Mean F1 Score: 1.0000
  Perfect matches (Jaccard=1.0): 577/577
  Mean Runtime Benefit (GT - Dist): 116.32ms
  Mean Speedup: 1.44x

✓ Correctness check PASSED: Mean Jaccard (1.0000) >= threshold (0.0)


"""

import ray
import time
import random
import itertools
import os
import ast
from pathlib import Path
from typing import Tuple, Set
from argparse import ArgumentParser
from itertools import chain
from tqdm import tqdm
import pandas as pd

from owlapy.owl_reasoner import SyncReasoner
from owlapy.utils import jaccard_similarity, f1_set_similarity
from owlapy.class_expression import (
    OWLObjectUnionOf,
    OWLObjectIntersectionOf,
    OWLObjectSomeValuesFrom,
    OWLObjectAllValuesFrom,
    OWLObjectMinCardinality,
    OWLObjectMaxCardinality,
    OWLObjectOneOf,
)
from owlapy import owl_expression_to_dl

# Import from ddp_reasoning
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ddp_reasoning import ShardReasoner, ShardEnsembleReasoner
from shard_ontology import shard_ontology

# Set pandas options to ensure full output
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.colheader_justify', 'left')
pd.set_option('display.expand_frame_repr', False)


def concept_reducer(concepts, opt):
    """Create all combinations of concepts with the given operator.
    
    Args:
        concepts: Set of concepts
        opt: Operator class (e.g., OWLObjectUnionOf or OWLObjectIntersectionOf)
        
    Returns:
        Set of all combinations of concepts using the operator
    """
    return {opt(operands=frozenset([c1, c2])) for c1 in concepts for c2 in concepts if c1 != c2}


def concept_reducer_properties(concepts, properties, cls, cardinality=None):
    """Create all combinations of concepts with properties and the given class.
    
    Args:
        concepts: Set of concepts
        properties: Set of properties
        cls: Class to use (e.g., OWLObjectSomeValuesFrom)
        cardinality: Optional cardinality for cardinality restrictions
        
    Returns:
        Set of all combinations
    """
    if cardinality is not None:
        return {cls(filler=c, property=p, cardinality=cardinality) for c in concepts for p in properties}
    else:
        return {cls(filler=c, property=p) for c in concepts for p in properties}


def execute(args):
    # (1) Initialize Ray
    if not ray.is_initialized():
        if args.auto_ray:
            num_cpus = os.cpu_count()
            shard_resources = {f"shard_{i}": 1 for i in range(args.num_shards)}
            print(f"[auto_ray] Starting local Ray cluster with {num_cpus} CPUs and resources: {shard_resources}")
            ray.init(num_cpus=num_cpus, resources=shard_resources)
        else:
            print("[manual_ray] Connecting to existing Ray cluster (address='auto') ...")
            ray.init(address='auto')
    
    # (2) Initialize symbolic reasoner (ground truth) - using same reasoner as distributed shards
    assert os.path.isfile(args.path_kg), f"Ontology file not found: {args.path_kg}"
    symbolic_kb = SyncReasoner(ontology=args.path_kg, reasoner=args.reasoner)
    
    # (3) Initialize Distributed Reasoner (shards)
    print(f"\n{'='*60}")
    print(f"Setting up ShardEnsembleReasoner with {args.num_shards} shard(s)")
    print(f"{'='*60}")
    
    # Derive shard filename prefix from the ontology stem
    ontology_stem = Path(args.path_kg).stem
    base_dir = str(Path(args.path_kg).parent)
    
    # Auto-generate shard files if any are missing
    if args.num_shards > 1:
        all_shards_exist = all(
            (Path(base_dir) / f"{ontology_stem}_shard_{i}.owl").exists()
            for i in range(args.num_shards)
        )
        # Also check no extra shards from a previous run with more shards
        extra_shard = (Path(base_dir) / f"{ontology_stem}_shard_{args.num_shards}.owl").exists()
        if not all_shards_exist or extra_shard:
            print(f"  [auto-shard] Shard files not found (or wrong count) — generating {args.num_shards} shards from {args.path_kg}...")
            shard_ontology(args.path_kg, args.num_shards, base_dir)
            print(f"  [auto-shard] Done.")
    
    shards = []
    for i in range(args.num_shards):
        if args.num_shards == 1:
            # Single shard = use complete ontology (fair baseline comparison)
            shard_path = args.path_kg
        else:
            # Multiple shards = use sharded ontology files
            shard_path = str(Path(base_dir) / f"{ontology_stem}_shard_{i}.owl")
            assert os.path.isfile(shard_path), f"Shard file not found: {shard_path}"
        
        # Each shard pinned to its own Ray resource
        shard = ShardReasoner.options(resources={f"shard_{i}": 1}).remote(
            f"Shard-{i}", shard_path, args.reasoner
        )
        shards.append(shard)
    
    # Initialize the distributed reasoner with the created shards.
    distributed_reasoner = ShardEnsembleReasoner(shards, verbose=False)

    # Fix the random seed
    random.seed(args.seed)
    
    ###################################################################
    # GENERATE DL CONCEPTS TO EVALUATE RETRIEVAL PERFORMANCES
    ###################################################################
    
    # (4) Extract object properties
    object_properties = sorted({i for i in symbolic_kb.get_root_ontology().object_properties_in_signature()})
    
    if args.ratio_sample_object_prop and len(object_properties) > 0:
        object_properties = {i for i in random.sample(
            population=list(object_properties),
            k=max(1, int(len(object_properties) * args.ratio_sample_object_prop))
        )}
    
    object_properties = set(object_properties)
    
    # (5) Inverse of object properties
    object_properties_inverse = {i.get_inverse_property() for i in object_properties}
    
    # (6) R*: R UNION R⁻
    object_properties_and_inverse = object_properties.union(object_properties_inverse)
    
    # (7) NC: Named OWL concepts
    nc = sorted({i for i in symbolic_kb.get_root_ontology().classes_in_signature()})
    
    if args.ratio_sample_nc and len(nc) > 0:
        nc = {i for i in random.sample(population=list(nc), k=max(1, int(len(nc) * args.ratio_sample_nc)))}
    
    nc = set(nc)
    
    # (8) NC⁻: Complement of NC (skip if --no_negations)
    if args.no_negations:
        nnc = set()
        nc_star = nc  # Use only named concepts, no negations
    else:
        nnc = {i.get_object_complement_of() for i in nc}
        # (9) NC*: NC UNION NC⁻
        nc_star = nc.union(nnc)
    
    # (10) Retrieve random Nominals
    individuals = list(symbolic_kb.get_root_ontology().individuals_in_signature())
    if len(individuals) > args.num_nominals:
        nominals = set(random.sample(individuals, args.num_nominals))
    else:
        nominals = set(individuals)
    
    # (11) Combinations of 3 for Nominals
    nominal_combinations = set(OWLObjectOneOf(combination) for combination in itertools.combinations(nominals, 3))
    
    # (12) NC UNION NC
    unions = concept_reducer(nc, opt=OWLObjectUnionOf)
    
    # (13) NC INTERSECTION NC
    intersections = concept_reducer(nc, opt=OWLObjectIntersectionOf)
    
    # (14) NC* UNION NC*
    unions_nc_star = concept_reducer(nc_star, opt=OWLObjectUnionOf)
    
    # (15) NC* INTERSECTION NC*
    intersections_nc_star = concept_reducer(nc_star, opt=OWLObjectIntersectionOf)
    
    # (16) ∃ r.C s.t. C ∈ NC* and r ∈ R*
    exist_nc_star = concept_reducer_properties(
        concepts=nc_star,
        properties=object_properties_and_inverse,
        cls=OWLObjectSomeValuesFrom,
    )
    
    # (17) ∀ r.C s.t. C ∈ NC* and r ∈ R* 
    for_all_nc_star = concept_reducer_properties(
            concepts=nc_star,
            properties=object_properties_and_inverse,
            cls=OWLObjectAllValuesFrom,
        )
    
    # (18) Cardinality restrictions
    min_cardinality_nc_star_1, min_cardinality_nc_star_2, min_cardinality_nc_star_3 = (
        concept_reducer_properties(
            concepts=nc_star,
            properties=object_properties_and_inverse,
            cls=OWLObjectMinCardinality,
            cardinality=i,
        )
        for i in [1, 2, 3]
    )
    max_cardinality_nc_star_1, max_cardinality_nc_star_2, max_cardinality_nc_star_3 = (
        concept_reducer_properties(
            concepts=nc_star,
            properties=object_properties_and_inverse,
            cls=OWLObjectMaxCardinality,
            cardinality=i,
        )
        for i in [1, 2, 3]
    )
    
    # (19) ∃ r.Nominal s.t. Nominal ∈ Nominals and r ∈ R*
    exist_nominals = concept_reducer_properties(
        concepts=nominal_combinations,
        properties=object_properties_and_inverse,
        cls=OWLObjectSomeValuesFrom,
    )
    
    ###################################################################
    # EVALUATION
    ###################################################################
    
    def concept_retrieval(retriever_func, c) -> Tuple[Set[str], float]:
        start_time = time.time()
        return {i.str for i in retriever_func.instances(c)}, time.time() - start_time
    
    # Collect concepts for evaluation
    concepts = list(
        chain(
            nc,                           # named concepts (C)
            nnc,                          # negated named concepts (¬C)
            unions_nc_star,               # NC* UNION NC*
            intersections_nc_star,        # NC* INTERSECTION NC*
            exist_nc_star,                # ∃ r.C
            for_all_nc_star,              # ∀ r.C
            min_cardinality_nc_star_1, min_cardinality_nc_star_2, min_cardinality_nc_star_3,
            max_cardinality_nc_star_1, max_cardinality_nc_star_2, max_cardinality_nc_star_3,
            exist_nominals
        )
    )
    
    print("\n")
    print("#" * 50)
    print("Description of generated Concepts")
    print(f"NC denotes the named concepts\t|NC|={len(nc)}")
    print(f"NNC denotes the negated named concepts\t|NNC|={len(nnc)}")
    print(f"|NC UNION NC|={len(unions)}")
    print(f"|NC Intersection NC|={len(intersections)}")
    print(f"NC* denotes the union of named concepts and negated named concepts\t|NC*|={len(nc_star)}")
    print(f"|NC* UNION NC*|={len(unions_nc_star)}")
    print(f"|NC* Intersection NC*|={len(intersections_nc_star)}")
    print(f"|exist R* NC*|={len(exist_nc_star)}")
    print(f"|forall R* NC*|={len(for_all_nc_star)}")
    print(f"|Max Cardinalities|={len(max_cardinality_nc_star_1) + len(max_cardinality_nc_star_2) + len(max_cardinality_nc_star_3)}")
    print(f"|Min Cardinalities|={len(min_cardinality_nc_star_1) + len(min_cardinality_nc_star_2) + len(min_cardinality_nc_star_3)}")
    print(f"|exist R* Nominals|={len(exist_nominals)}")
    print("#" * 50, end="\n\n")
    
    # Shuffle concepts for better progress bar estimation
    concepts.sort(key=lambda c: owl_expression_to_dl(c))
    random.shuffle(concepts)
    
    data = []

    # Iterate over OWL Class Expressions
    for expression in (tqdm_bar := tqdm(concepts, position=0, leave=True)):
        try:
            # Retrieve ground truth results
            retrieval_y, runtime_y = concept_retrieval(symbolic_kb, expression)

            # Retrieve distributed reasoner results
            retrieval_distributed_y, runtime_distributed_y = concept_retrieval(distributed_reasoner, expression)

            # Compute similarity metrics
            jaccard_sim = jaccard_similarity(retrieval_y, retrieval_distributed_y)
            f1_sim = f1_set_similarity(retrieval_y, retrieval_distributed_y)

            data.append({
                "Expression": owl_expression_to_dl(expression),
                "Type": type(expression).__name__,
                "Jaccard Similarity": jaccard_sim,
                "F1": f1_sim,
                "Runtime Benefits": runtime_y - runtime_distributed_y,
                "Runtime Ground Truth": runtime_y,
                "Runtime Distributed": runtime_distributed_y,
                "Ground_Truth_Retrieval": None if jaccard_sim == 1.0 else retrieval_y,
                "Distributed_Retrieval": None if jaccard_sim == 1.0 else retrieval_distributed_y,
                "Match": retrieval_y == retrieval_distributed_y,
            })

            # Update progress bar
            tqdm_bar.set_description_str(
                f"Expression: {owl_expression_to_dl(expression)[:40]}... | Jaccard:{jaccard_sim:.4f} | F1:{f1_sim:.4f} | Speedup:{runtime_y/max(runtime_distributed_y, 1e-6):.2f}x"
            )

        except Exception as e:
            print(f"\nError processing expression {owl_expression_to_dl(expression)}: {e}")
            continue

    # Build dataframe from collected results and write CSV once (avoids header/append race)
    df = pd.DataFrame(data)
    df.to_csv(args.path_report, index=False)
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)
    
    # Group by expression type
    df_g = df.groupby(by="Type")
    
    # Compute mean of numerical columns per group
    numerical_df = df.select_dtypes(include=["number"])
    mean_df = df_g[numerical_df.columns.tolist()].mean()
    
    # Combine counts and mean metrics into a single table
    mean_df.insert(0, "Count", df_g["Type"].count())
    
    print("\nCombined Metrics by Type:")
    print(mean_df)
    
    print("\nLaTeX Table:")
    print("-" * 70)
    
    latex_df = mean_df.rename(columns={
        "Jaccard Similarity": "Jaccard",
        "Runtime Benefits": "RT Benefits"
    })
    latex_df = latex_df.rename(index={
        "OWLObjectAllValuesFrom": "OWLObjAllValuesFrom",
        "OWLObjectComplementOf": "OWLObjComplementOf",
        "OWLObjectIntersectionOf": "OWLObjIntersectionOf",
        "OWLObjectMaxCardinality": "OWLObjMaxCardinality",
        "OWLObjectMinCardinality": "OWLObjMinCardinality",
        "OWLObjectSomeValuesFrom": "OWLObjSomeValuesFrom",
        "OWLObjectUnionOf": "OWLObjUnionOf",
        "OWLObjectOneOf": "OWLObjOneOf",
    })
    
    latex_table_str = []
    latex_table_str.append(r"\begin{table}[htbp]")
    latex_table_str.append(r"\centering")
    latex_table_str.append(r"\small")
    latex_table_str.append(r"\begin{tabular}{l r r r r}")
    latex_table_str.append(r"\toprule")
    latex_table_str.append(r"\textbf{Type} & \textbf{Count} & \textbf{Jaccard} & \textbf{F1} & \textbf{RT Benefits} \\")
    latex_table_str.append(r"\midrule")
    for idx, row in latex_df.iterrows():
        latex_table_str.append(f"{idx:<23} & {int(row['Count']):<3} & {row['Jaccard']:.4f} & {row['F1']:.4f} & {row['RT Benefits']:.4f} \\\\")
    latex_table_str.append(r"\bottomrule")
    latex_table_str.append(r"\end{tabular}")
    latex_table_str.append(r"\caption{Comparison of OWL Runtime Metrics}")
    latex_table_str.append(r"\end{table}")
    
    latex_output = "\n".join(latex_table_str)
    print(latex_output)
    print("-" * 70)
    
    latex_filename = f"{ontology_stem}_{args.num_shards}_shards.txt"
    with open(latex_filename, "w", encoding="utf-8") as f:
        f.write(latex_output)
    print(f"\nLaTeX table saved to {latex_filename}")
    
    # Assert correctness threshold
    mean_jaccard = df["Jaccard Similarity"].mean()
    if mean_jaccard >= args.min_jaccard_similarity:
        print(f"\n✓ Correctness check PASSED: Mean Jaccard ({mean_jaccard:.4f}) >= threshold ({args.min_jaccard_similarity})")
    else:
        print(f"\n✗ Correctness check FAILED: Mean Jaccard ({mean_jaccard:.4f}) < threshold ({args.min_jaccard_similarity})")
    
    return mean_jaccard, df["F1"].mean()


def get_default_arguments():
    parser = ArgumentParser(description="Evaluate BaseShardReasoner against StructuralReasoner ground truth")
    parser.add_argument("--path_kg", type=str, default="KGs/Family/family-benchmark_rich_background.owl",
                        help="Path to the OWL ontology file")
    parser.add_argument("--num_shards", type=int, default=1,
                        help="Number of shards for distributed reasoning (1 = baseline comparison)")
    parser.add_argument("--reasoner", type=str, default="Pellet",
                        help="Reasoner to use in shards (Pellet, HermiT, etc.)")
    parser.add_argument("--seed", type=int, default=1,
                        help="Random seed for reproducibility")
    parser.add_argument("--ratio_sample_nc", type=float, default=None,
                        help="Ratio of OWL Classes to sample without replacement (0.0-1.0). "
                             "None (default) means no sampling — all classes are used.")
    parser.add_argument("--ratio_sample_object_prop", type=float, default=None,
                        help="Ratio of OWL Object Properties to sample without replacement (0.0-1.0). "
                             "None (default) means no sampling — all properties are used.")
    parser.add_argument("--min_jaccard_similarity", type=float, default=0.0,
                        help="Minimum mean Jaccard similarity threshold")
    parser.add_argument("--num_nominals", type=int, default=10,
                        help="Number of OWL named individuals to sample for nominals")
    parser.add_argument("--path_report", type=str, default="DDP_Reasoning_Eval_Results.csv",
                        help="Path to save the evaluation results CSV")
    parser.add_argument("--no_negations", action="store_true",
                        help="Exclude negation-based expressions (¬C, ∀r.C) from evaluation")
    parser.add_argument(
        "--cross_shard", action="store_true", default=False,
        help="Use ShardEnsembleReasoner for open-world distributed reasoning (default: BaseShardReasoner)",
    )
    parser.add_argument("--auto_ray", action="store_true", default=False,
                        help=(
                            "If set, Ray is initialised automatically in-process using all available "
                            "CPU cores and the required shard custom resources. "
                            "Shard .owl files are generated automatically if missing. "
                            "If not set (default), the script connects to an already-running Ray cluster "
                            "that was started manually via 'ray start --head ...'."
                        ))
    return parser.parse_args()


if __name__ == "__main__":
    args = get_default_arguments()
    
    # Ensure deterministic hash/set behavior by setting PYTHONHASHSEED
    if os.environ.get("PYTHONHASHSEED") != str(args.seed):
        print(f"[Info] Setting PYTHONHASHSEED={args.seed} for determinism.")
        os.environ["PYTHONHASHSEED"] = str(args.seed)
        sys.stdout.flush()
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
    execute(args)
