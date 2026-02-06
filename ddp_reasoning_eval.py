"""$ python examples/ddp_reasoning_eval.py --path_kg KGs/Family/father.owl --num_shards 1

Evaluates the DistributedReasoner from ddp_reasoning.py against a StructuralReasoner
ground truth, generating OWL class expressions and comparing their retrieval results.

Requires a Ray cluster to be running. Example setup for 1 shard:
  ray start --head --port=6379 --num-cpus=1 --resources='{"shard_0": 1}'
"""

import ray
import time
import random
import itertools
import os
import ast
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
from ddp_reasoning import ShardReasoner, DistributedReasoner

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
    # (1) Initialize Ray and connect to existing cluster
    if not ray.is_initialized():
        ray.init(address='auto')
    
    # (2) Initialize symbolic reasoner (ground truth) - using same reasoner as distributed shards
    assert os.path.isfile(args.path_kg), f"Ontology file not found: {args.path_kg}"
    symbolic_kb = SyncReasoner(ontology=args.path_kg, reasoner=args.reasoner)
    
    # (3) Initialize Distributed Reasoner (shards)
    print(f"\n{'='*60}")
    print(f"Setting up DistributedReasoner with {args.num_shards} shard(s)")
    print(f"{'='*60}")
    
    shards = []
    for i in range(args.num_shards):
        if args.num_shards == 1:
            # Single shard = use complete ontology (fair baseline comparison)
            shard_path = args.path_kg
        else:
            # Multiple shards = use sharded ontology files
            base_path = os.path.splitext(args.path_kg)[0]
            shard_path = f"{base_path}_shard_{i}.owl"
            assert os.path.isfile(shard_path), f"Shard file not found: {shard_path}"
        
        # Each shard pinned to its own Ray resource
        shard = ShardReasoner.options(resources={f"shard_{i}": 1}).remote(
            f"Shard-{i}", shard_path, args.reasoner
        )
        shards.append(shard)
    
    distributed_reasoner = DistributedReasoner(shards)
    
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
    
    # (17) ∀ r.C s.t. C ∈ NC* and r ∈ R* (skip if --no_negations, since ∀r.C ≡ ¬∃r.¬C)
    if args.no_negations:
        for_all_nc_star = set()
    else:
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
    random.shuffle(concepts)
    
    # Check if CSV already exists and delete it
    if os.path.exists(args.path_report):
        os.remove(args.path_report)
    file_exists = False
    
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
            
            # Store the data
            df_row = pd.DataFrame([{
                "Expression": owl_expression_to_dl(expression),
                "Type": type(expression).__name__,
                "Jaccard Similarity": jaccard_sim,
                "F1": f1_sim,
                "Runtime Benefits": runtime_y - runtime_distributed_y,
                "Runtime Ground Truth": runtime_y,
                "Runtime Distributed": runtime_distributed_y,
                "Ground_Truth_Retrieval": retrieval_y,
                "Distributed_Retrieval": retrieval_distributed_y,
                "Match": retrieval_y == retrieval_distributed_y,
            }])
            
            # Append to CSV
            df_row.to_csv(args.path_report, mode='a', header=not file_exists, index=False)
            file_exists = True
            
            # Update progress bar
            tqdm_bar.set_description_str(
                f"Expression: {owl_expression_to_dl(expression)[:40]}... | Jaccard:{jaccard_sim:.4f} | F1:{f1_sim:.4f} | Speedup:{runtime_y/max(runtime_distributed_y, 1e-6):.2f}x"
            )
            
        except Exception as e:
            print(f"\nError processing expression {owl_expression_to_dl(expression)}: {e}")
            continue
    
    # Read and analyze results
    df = pd.read_csv(args.path_report, converters={
        'Ground_Truth_Retrieval': lambda x: ast.literal_eval(x),
        'Distributed_Retrieval': lambda x: ast.literal_eval(x)
    })
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)
    
    # Group by expression type
    df_g = df.groupby(by="Type")
    print("\nExpression Type Counts:")
    print(df_g["Type"].count())
    
    # Compute mean of numerical columns per group
    numerical_df = df.select_dtypes(include=["number"])
    mean_df = df_g[numerical_df.columns.tolist()].mean()
    print("\nMean Metrics by Type:")
    print(mean_df)
    
    # Overall statistics
    print("\n" + "-" * 70)
    print("Overall Statistics:")
    print(f"  Total expressions evaluated: {len(df)}")
    print(f"  Mean Jaccard Similarity: {df['Jaccard Similarity'].mean():.4f}")
    print(f"  Mean F1 Score: {df['F1'].mean():.4f}")
    print(f"  Perfect matches (Jaccard=1.0): {(df['Jaccard Similarity'] == 1.0).sum()}/{len(df)}")
    print(f"  Mean Runtime Benefit (GT - Dist): {df['Runtime Benefits'].mean()*1000:.2f}ms")
    print(f"  Mean Speedup: {(df['Runtime Ground Truth'] / df['Runtime Distributed'].replace(0, 1e-6)).mean():.2f}x")
    
    # Assert correctness threshold
    mean_jaccard = df["Jaccard Similarity"].mean()
    if mean_jaccard >= args.min_jaccard_similarity:
        print(f"\n✓ Correctness check PASSED: Mean Jaccard ({mean_jaccard:.4f}) >= threshold ({args.min_jaccard_similarity})")
    else:
        print(f"\n✗ Correctness check FAILED: Mean Jaccard ({mean_jaccard:.4f}) < threshold ({args.min_jaccard_similarity})")
    
    return mean_jaccard, df["F1"].mean()


def get_default_arguments():
    parser = ArgumentParser(description="Evaluate DistributedReasoner against StructuralReasoner ground truth")
    parser.add_argument("--path_kg", type=str, default="KGs/Family/family-benchmark_rich_background.owl",
                        help="Path to the OWL ontology file")
    parser.add_argument("--num_shards", type=int, default=1,
                        help="Number of shards for distributed reasoning (1 = baseline comparison)")
    parser.add_argument("--reasoner", type=str, default="Pellet",
                        help="Reasoner to use in shards (Pellet, HermiT, etc.)")
    parser.add_argument("--seed", type=int, default=1,
                        help="Random seed for reproducibility")
    parser.add_argument("--ratio_sample_nc", type=float, default=1.0,
                        help="Ratio of OWL Classes to sample (0.0-1.0)")
    parser.add_argument("--ratio_sample_object_prop", type=float, default=1.0,
                        help="Ratio of OWL Object Properties to sample (0.0-1.0)")
    parser.add_argument("--min_jaccard_similarity", type=float, default=0.0,
                        help="Minimum mean Jaccard similarity threshold")
    parser.add_argument("--num_nominals", type=int, default=10,
                        help="Number of OWL named individuals to sample for nominals")
    parser.add_argument("--path_report", type=str, default="DDP_Reasoning_Eval_Results.csv",
                        help="Path to save the evaluation results CSV")
    parser.add_argument("--no_negations", action="store_true",
                        help="Exclude negation-based expressions (¬C, ∀r.C) from evaluation")
    return parser.parse_args()


if __name__ == "__main__":
    execute(get_default_arguments())
