"""$ python examples/retrieval_eval.py --path_kg KGs/Family/father.owl

##################################################
Description of generated Concepts
NC denotes the named concepts   |NC|=3
NNC denotes the negated named concepts  |NNC|=3
|NC UNION NC|=9
|NC Intersection NC|=9
NC* denotes the union of named concepts and negated named concepts      |NC*|=6
|NC* UNION NC*|=36
|NC* Intersection NC*|=36
|exist R* NC*|=12
|forall R* NC*|=12
|Max Cardinalities|=36
|Min Cardinalities|=36
|exist R* Nominals|=40
##################################################

Expression: ∃ hasChild⁻.{heinz , stefan , martin} | Jaccard Similarity:1.0000 | F1 :1.0000 | Runtime Benefits:-0.003:   0%|                                                                                 | 0/232 [00:00<?, ?it/s]Invalid IRI detected: Nec8a193431bd4ba6a57485770b54e72b, error: string index out of range
Expression: male ⊔ (¬female) | Jaccard Similarity:1.0000 | F1 :1.0000 | Runtime Benefits:-0.002: 100%|███████████████████████████████████████████████████████████████████████████████████████████| 232/232 [00:00<00:00, 285.35it/s]
Type
OWLClass                    3
OWLObjectAllValuesFrom     12
OWLObjectComplementOf       3
OWLObjectIntersectionOf    45
OWLObjectMaxCardinality    36
OWLObjectMinCardinality    36
OWLObjectSomeValuesFrom    52
OWLObjectUnionOf           45
Name: Type, dtype: int64
                         Jaccard Similarity   F1  Runtime Benefits
Type
OWLClass                                1.0  1.0         -0.001484
OWLObjectAllValuesFrom                  1.0  1.0         -0.004071
OWLObjectComplementOf                   1.0  1.0         -0.001592
OWLObjectIntersectionOf                 1.0  1.0         -0.002914
OWLObjectMaxCardinality                 1.0  1.0          0.000511
OWLObjectMinCardinality                 1.0  1.0         -0.002798
OWLObjectSomeValuesFrom                 1.0  1.0         -0.001701
OWLObjectUnionOf                        1.0  1.0         -0.002939

"""
# Replace ontolearn dependencies with owlapy components
from owlapy.owl_reasoner import StructuralReasoner
from owlapy.embedding_based_reasoner import EBR
from owlapy.owl_ontology import Ontology
from owlapy.neural_ontology import NeuralOntology
from owlapy.class_expression import (
    OWLObjectUnionOf,
    OWLObjectIntersectionOf,
    OWLObjectSomeValuesFrom,
    OWLObjectAllValuesFrom,
    OWLObjectMinCardinality,
    OWLObjectMaxCardinality,
    OWLObjectOneOf,
)
import time
from typing import Tuple, Set
import pandas as pd
from owlapy import owl_expression_to_dl
from itertools import chain
from argparse import ArgumentParser
import os
from tqdm import tqdm
import random
import itertools
import ast
# Set pandas options to ensure full output
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.colheader_justify', 'left')
pd.set_option('display.expand_frame_repr', False)

# Define utility functions that were previously imported from ontolearn
def jaccard_similarity(set1, set2):
    """Calculate the Jaccard similarity between two sets.
    
    Args:
        set1: First set
        set2: Second set
        
    Returns:
        Jaccard similarity: intersection(set1, set2) / union(set1, set2)
    """
    if len(set1) == 0 and len(set2) == 0:
        return 1.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union

def f1_set_similarity(set1, set2):
    """Calculate the F1 score between two sets.
    
    Args:
        set1: First set (treated as ground truth)
        set2: Second set (treated as prediction)
        
    Returns:
        F1 score
    """
    if len(set1) == 0 and len(set2) == 0:
        return 1.0
    
    if len(set2) == 0:
        return 0.0
    
    true_positives = len(set1.intersection(set2))
    precision = true_positives / len(set2) if len(set2) > 0 else 0
    recall = true_positives / len(set1) if len(set1) > 0 else 0
    
    if precision + recall == 0:
        return 0.0
    
    return 2 * (precision * recall) / (precision + recall)

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
    # (1) Initialize symbolic reasoner
    assert os.path.isfile(args.path_kg)
    # Use StructuralReasoner instead of KnowledgeBase
    ontology = Ontology(ontology_iri=args.path_kg)
    symbolic_kb = StructuralReasoner(ontology)
    
    # (2) Initialize Neural OWL Reasoner
    # Use EBR instead of TripleStoreNeuralReasoner
    if args.path_kge_model:
        neural_ontology = NeuralOntology(path_neural_embedding=args.path_kge_model)
    else:
        neural_ontology = NeuralOntology(path_neural_embedding=args.path_kg, train_if_not_exists=True)
    neural_owl_reasoner = EBR(ontology=neural_ontology, gamma=args.gamma)
    
    # Fix the random seed.
    random.seed(args.seed)
    ###################################################################
    # GENERATE DL CONCEPTS TO EVALUATE RETRIEVAL PERFORMANCES
    # (3) R: Extract object properties.
    object_properties = sorted({i for i in symbolic_kb.get_root_ontology().object_properties_in_signature()})
    
    # (3.1) Subsample if required.
    if args.ratio_sample_object_prop and len(object_properties) > 0:
        object_properties = {i for i in random.sample(population=list(object_properties),
                                                      k=max(1, int(len(object_properties) * args.ratio_sample_object_prop)))}

    object_properties = set(object_properties)    
    
    # (4) R⁻: Inverse of object properties.
    object_properties_inverse = {i.get_inverse_property() for i in object_properties}

    # (5) R*: R UNION R⁻.
    object_properties_and_inverse = object_properties.union(object_properties_inverse)
    # (6) NC: Named owl concepts.
    nc = sorted({i for i in symbolic_kb.get_root_ontology().classes_in_signature()})
   
    if args.ratio_sample_nc and len(nc) > 0:
        # (6.1) Subsample if required.
        nc = {i for i in random.sample(population=list(nc), k=max(1, int(len(nc) * args.ratio_sample_nc)))}

    nc = set(nc) # return to a set
    # (7) NC⁻: Complement of NC.
    nnc = {i.get_object_complement_of() for i in nc}

    # (8) NC*: NC UNION NC⁻.
    nc_star = nc.union(nnc)
    # (9) Retrieve 10 random Nominals.
    individuals = list(symbolic_kb.get_root_ontology().individuals_in_signature())
    if len(individuals) > args.num_nominals:
        nominals = set(random.sample(individuals, args.num_nominals))
    else:
        nominals = set(individuals)
    # (10) All combinations of 3 for Nominals, e.g. {martin, heinz, markus}
    nominal_combinations = set(OWLObjectOneOf(combination) for combination in itertools.combinations(nominals, 3))

    # (11) NC UNION NC.
    unions = concept_reducer(nc, opt=OWLObjectUnionOf)
    # (12) NC INTERSECTION NC.
    intersections = concept_reducer(nc, opt=OWLObjectIntersectionOf)
    # (13) NC* UNION NC*.
    unions_nc_star = concept_reducer(nc_star, opt=OWLObjectUnionOf)
    # (14) NC* INTERACTION NC*.
    intersections_nc_star = concept_reducer(nc_star, opt=OWLObjectIntersectionOf)
    # (15) \exist r. C s.t. C \in NC* and r \in R* .
    exist_nc_star = concept_reducer_properties(
        concepts=nc_star,
        properties=object_properties_and_inverse,
        cls=OWLObjectSomeValuesFrom,
    )
    # (16) \forall r. C s.t. C \in NC* and r \in R* .
    for_all_nc_star = concept_reducer_properties(
        concepts=nc_star,
        properties=object_properties_and_inverse,
        cls=OWLObjectAllValuesFrom,
    )
    # (17) >= n r. C  and =< n r. C, s.t. C \in NC* and r \in R* .
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
    # (18) \exist r. Nominal s.t. Nominal \in Nominals and r \in R* .
    exist_nominals = concept_reducer_properties(
        concepts=nominal_combinations,
        properties=object_properties_and_inverse,
        cls=OWLObjectSomeValuesFrom,
    )

    ###################################################################

    # Retrieval Results
    def concept_retrieval(retriever_func, c) -> Tuple[Set[str], float]:
        start_time = time.time()
        return {i.str for i in retriever_func.instances(c)}, time.time() - start_time

    # () Collect the data.
    data = []
    # () Converted to list so that the progress bar works.
    concepts = list(
        chain(
            nc,           # named concepts          (C)
            nnc,                   # negated named concepts  (\neg C)
            unions_nc_star,        # A set of Union of named concepts and negat
            intersections_nc_star, #
            exist_nc_star,
            for_all_nc_star,
            min_cardinality_nc_star_1, min_cardinality_nc_star_1, min_cardinality_nc_star_3,
            max_cardinality_nc_star_1, max_cardinality_nc_star_2, max_cardinality_nc_star_3,
            exist_nominals))
    print("\n")
    print("#"*50)
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

    print(f"|Max Cardinalities|={len(max_cardinality_nc_star_1) + len(max_cardinality_nc_star_2)+ len(max_cardinality_nc_star_3)}")
    print(f"|Min Cardinalities|={len(min_cardinality_nc_star_1) + len(min_cardinality_nc_star_1)+ len(min_cardinality_nc_star_3)}")
    print(f"|exist R* Nominals|={len(exist_nominals)}")
    print("#" * 50,end="\n\n")


    # () Shuffled the data so that the progress bar is not influenced by the order of concepts.

    random.shuffle(concepts)
    # check if csv arleady exists and delete it cause we want to override it
    if os.path.exists(args.path_report):
        os.remove(args.path_report)
    file_exists = False
    # () Iterate over single OWL Class Expressions in ALCQIHO
    for expression in (tqdm_bar := tqdm(concepts, position=0, leave=True)):
        retrieval_y: Set[str]
        runtime_y: Set[str]
        # () Retrieve the true set of individuals and elapsed runtime.
        retrieval_y, runtime_y = concept_retrieval(symbolic_kb, expression)
        # () Retrieve a set of inferred individuals and elapsed runtime.
        retrieval_neural_y, runtime_neural_y = concept_retrieval(neural_owl_reasoner, expression)
        # () Compute the Jaccard similarity.
        jaccard_sim = jaccard_similarity(retrieval_y, retrieval_neural_y)
        # () Compute the F1-score.
        f1_sim = f1_set_similarity(retrieval_y, retrieval_neural_y)
        # () Store the data.
        df_row = pd.DataFrame(
            [{
                "Expression": owl_expression_to_dl(expression),
                "Type": type(expression).__name__,
                "Jaccard Similarity": jaccard_sim,
                "F1": f1_sim,
                "Runtime Benefits": runtime_y - runtime_neural_y,
                "Runtime Neural": runtime_neural_y,
                "Symbolic_Retrieval": retrieval_y,
                "Symbolic_Retrieval_Neural": retrieval_neural_y,
            }])
        # Append the row to the CSV file
        df_row.to_csv(args.path_report, mode='a', header=not file_exists, index=False)
        file_exists = True
        # () Update the progress bar.
        tqdm_bar.set_description_str(
            f"Expression: {owl_expression_to_dl(expression)} | Jaccard Similarity:{jaccard_sim:.4f} | F1 :{f1_sim:.4f} | Runtime Benefits:{runtime_y - runtime_neural_y:.3f}"
        )
    # () Read the data into pandas dataframe
    df = pd.read_csv(args.path_report, index_col=0, converters={'Symbolic_Retrieval': lambda x: ast.literal_eval(x),
                                                                'Symbolic_Retrieval_Neural': lambda x: ast.literal_eval(x)})
    # () Assert that the mean Jaccard Similarity meets the threshold
    assert df["Jaccard Similarity"].mean() >= args.min_jaccard_similarity

    # () Ensure 'Symbolic_Retrieval_Neural' contains sets
    x = df["Symbolic_Retrieval_Neural"].iloc[0]
    assert isinstance(x, set)

    # () Extract numerical features
    numerical_df = df.select_dtypes(include=["number"])

    # () Group by the type of OWL concepts
    df_g = df.groupby(by="Type")
    print(df_g["Type"].count())

    # () Compute mean of numerical columns per group
    mean_df = df_g[numerical_df.columns].mean()
    print(mean_df)
    return jaccard_sim, f1_sim

def get_default_arguments():
    parser = ArgumentParser()
    parser.add_argument("--path_kg", type=str, default="KGs/Family/father.owl")
    parser.add_argument("--path_kge_model", type=str, default=None)
    parser.add_argument("--gamma", type=float, default=0.9)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--ratio_sample_nc", type=float, default=1, help="To sample OWL Classes.")
    parser.add_argument("--ratio_sample_object_prop", type=float, default=1, help="To sample OWL Object Properties.")
    parser.add_argument("--min_jaccard_similarity", type=float, default=0.0, help="Minimum Jaccard similarity to be achieve by the reasoner")
    parser.add_argument("--num_nominals", type=int, default=10, help="Number of OWL named individuals to be sampled.")

    # H is obtained if the forward chain is applied on KG.
    parser.add_argument("--path_report", type=str, default="ALCQHI_Retrieval_Results.csv")
    return parser.parse_args()

if __name__ == "__main__":
    execute(get_default_arguments())