"""The goal of this script is to perform retrieval task on inconsistent or incomplete KB. 
   Given and input KB, we first generate a number of subgraphs that are either incomplete 
   or inconsistent. Each subgraph is then evaluated by running a retrieval task, using
   using a neural method or different symbolic reasoners (HermiT, Pellet, JFact, and Openllet).
   for each subgraph, the script computes and records Jaccard similarity scores between 
   the retrieval results of each reasoner and the expected goal, as well as their runtime. 
   The result is then save as a csv file for further investigation.
   
   To run the script: python examples/retrieval_eval_under_incomplete.py"""

from argparse import ArgumentParser
# Replace ontolearn dependencies with owlapy components
from owlapy.owl_reasoner import StructuralReasoner
from owlapy.owl_ontology import Ontology
from owlapy.util_owl_static_funcs import make_kb_incomplete, make_kb_inconsistent
from owlapy.utils import jaccard_similarity
import pandas as pd
from typing import Set
import time
import os
import subprocess
from owlapy.class_expression import *
from owlapy.parser import DLSyntaxParser
import ast
from owlapy.owl_reasoner import SyncReasoner
from owlapy.static_funcs import stopJVM

# Create incomplete/noisy KGs
def generate_subgraphs(kb_path: str, directory: str, n: int, ratio: float, operation: str) -> Set[str]:

    """
    Generates a specified number of paths of subgraphs (incomplete or noisy knowledge graphs)
    by applying either the "incomplete" or "inconsistent" operation from the functions make_kb_incomplete and
    make_kb_inconsistent to the given KB.

    Inputs:
    ---------------

        kb_path (str): The path to the input KB file.
        directory (str): The directory where the generated subgraphs will be stored.
        n (int): The number of subgraphs to generate.
        ratio (float): The ratio of elements to modify within the KB (as a percentage).
        operation (str): The type of operation to perform on the KB. Expected values are
                        "incomplete" or "inconsistent", which define the type of subgraph to generate.

    Output:
    ---------------

        Set[str]: A set containing the file paths of all the generated subgraphs.
    """

    name = kb_path.split('/')[-1].split('.')[0]
    rate = int(ratio * 100)

    os.makedirs(directory, exist_ok=True)

    file_paths = set()

    for i in range(1, n + 1):

        
        if "incomplete" in operation:

            # output path for the incomplete KGs
            output_path = f'{directory}/{operation}_{name}_ratio_{rate}_number_{i}.owl'

                # Check if the file already exists
            if not os.path.exists(output_path):
                # If file does not exist, generate it
                make_kb_incomplete(kb_path, output_path, rate, seed=i)

        else:
            output_path = f'{directory}/{operation}_{name}_ratio_{rate}_number_{i}.owl'

                # Check if the file already exists
            if not os.path.exists(output_path):
                # If file does not exist, generate it
                make_kb_inconsistent(kb_path, output_path, rate, seed=i)

        # Add the output path to the set
        file_paths.add(output_path)

    return file_paths


def execute(args):
    # Initialize symbolic reasoner using owlapy components
    ontology = Ontology(ontology_iri=args.path_kg)
    symbolic_kb = StructuralReasoner(ontology)
    namespace = list(symbolic_kb.get_root_ontology().classes_in_signature())[0].iri.get_namespace()
    parser = DLSyntaxParser(namespace)
    name_KG = args.path_kg.split('/')[-1].split('.')[0]
    ratio_str = str(args.ratio).replace('.', '_')
    directory = f"{args.operation}_{name_KG}_{ratio_str}"
    paths_of_subgraphs = generate_subgraphs(
        kb_path=args.path_kg, 
        directory=directory,
        n=args.number_of_subgraphs, 
        ratio=args.ratio,
        operation=args.operation
    )
    path_report = f"{directory}/ALCQHI_Retrieval_Results.csv"

    expressions = None
    all_results = []

    for path in paths_of_subgraphs:

        list_jaccard_neural = []
        data = []

        if args.sample == "Yes":
            subprocess.run(['python', 'examples/retrieval_eval.py', "--path_kg", path, "--ratio_sample_nc","0.1", "--ratio_sample_object_prop", "0.2", "--path_report", path_report])
        else:
            subprocess.run(['python', 'examples/retrieval_eval.py', "--path_kg", path, "--path_report", path_report])
        

        df = pd.read_csv(f"{directory}/ALCQHI_Retrieval_Results.csv")

        # Extract expressions
        expressions = df["Expression"].tolist()
        
        ontology_path = path
        reasoners = ['HermiT', 'Pellet', 'JFact', 'Openllet']
        reasoner_jaccards = {reasoner: [] for reasoner in reasoners}
        reasoner_times = {reasoner: [] for reasoner in reasoners}  # To store running times


        hermit_reasoner = SyncReasoner(ontology=ontology_path, reasoner='HermiT')

        if hermit_reasoner.has_consistent_ontology():

            for expression in expressions:
                print("-" * 100)
                print("Expression:", expression)
                try:
                    target_concept = parser.parse_expression(expression)
                except Exception as e:
                    print(f"Failed to parse expression: {expression}")
                    print(e)
                    continue
                goal_retrieval = {i.str for i in symbolic_kb.instances(target_concept)}
                result_neural_symbolic = df[df["Expression"] == expression]["Symbolic_Retrieval_Neural"].apply(ast.literal_eval).iloc[0]
                jaccard_sim_neural = jaccard_similarity(result_neural_symbolic, goal_retrieval)
                list_jaccard_neural.append(jaccard_sim_neural)
                
                result_row = {
                    "Incomplete_KG": path.split('/')[-1],
                    "Expression": expression,
                    "Type": type(parser.parse_expression(expression)).__name__,
                    "Jaccard_EBR": jaccard_sim_neural,
                    "Runtime_EBR": df[df["Expression"] == expression]["Runtime Neural"].iloc[0]
                }


                for reasoner in reasoners:

                    cur_reasoner = SyncReasoner(ontology=ontology_path, reasoner=reasoner)

                    print(f"...Reasoner {reasoner} starts")

                    start_time = time.time()  # Start timing

                    result_symbolic = {i.str for i in (cur_reasoner.instances(target_concept, direct=False))}
                    end_time = time.time()  # End timing
                    
                    elapsed_time = end_time - start_time  # Calculate elapsed time
                    jaccard_sim_symbolic = jaccard_similarity(result_symbolic, goal_retrieval)
                    reasoner_jaccards[reasoner].append(jaccard_sim_symbolic)
                    reasoner_times[reasoner].append(elapsed_time)  # Store running time
                    
                    result_row[f"Jaccard_{reasoner}"] = jaccard_sim_symbolic
                    result_row[f"Runtime_{reasoner}"] = elapsed_time

                

                data.append(result_row)

            all_results.extend(data)

        
            avg_jaccard_neural = sum(list_jaccard_neural) / len(list_jaccard_neural)
            avg_jaccard_reasoners = {reasoner: sum(reasoner_jaccards[reasoner]) / len(reasoner_jaccards[reasoner]) for reasoner in reasoners}
            avg_time_reasoners = {reasoner: sum(reasoner_times[reasoner]) / len(reasoner_times[reasoner]) for reasoner in reasoners}

            print(f"Average Jaccard neural ({path}):", avg_jaccard_neural)
            for reasoner, avg_jaccard in avg_jaccard_reasoners.items():
                print(f"Average Jaccard {reasoner} ({path}):", avg_jaccard)
                print(f"Average Runtime {reasoner} ({path}):", avg_time_reasoners[reasoner])

        else:

            for expression in expressions:

                print("-"*100)
                print("Expression:", expression)
                
                target_concept = parser.parse_expression(expression)
                goal_retrieval = {i.str for i in symbolic_kb.instances(target_concept)}
                result_neural_symbolic = df[df["Expression"] == expression]["Symbolic_Retrieval_Neural"].apply(ast.literal_eval).iloc[0]
                jaccard_sim_neural = jaccard_similarity(result_neural_symbolic, goal_retrieval)
                list_jaccard_neural.append(jaccard_sim_neural)
                
                result_row = {
                    "Subgraphs": path.split('/')[-1],
                    "Expression": expression,
                    "Type": type(parser.parse_expression(expression)).__name__,
                    "Jaccard_EBR": jaccard_sim_neural,
                    "Runtime_EBR": df[df["Expression"] == expression]["Runtime Neural"].iloc[0]
                }
                

                data.append(result_row)

            all_results.extend(data)
            print("The Knowledge base is not consistent, hence other reasoners will fail")

    # Create a final DataFrame from all results and write to a CSV file
    final_df = pd.DataFrame(all_results)
    final_csv_path = f"{directory}/comparison_results.csv"
    final_df.to_csv(final_csv_path, index=False)

    print(final_df.head())
    print(f"Results have been saved to {final_csv_path}")
    # stopJVM()
    return avg_jaccard_reasoners
   



def get_default_arguments():
    parser = ArgumentParser()
    parser.add_argument("--path_kg", type=str, default="KGs/Family/family-benchmark_rich_background.owl")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--ratio_sample_nc", type=float, default=None, help="To sample OWL Classes.")
    parser.add_argument("--ratio_sample_object_prop", type=float, default=None, help="To sample OWL Object Properties.")
    parser.add_argument("--path_report", type=str, default="ALCQHI_Retrieval_Incomplete_Results.csv")
    parser.add_argument("--number_of_subgraphs", type=int, default=1)
    parser.add_argument("--ratio", type=float, default=0.1, \
                        help="Percentage of incompleteness or inconsistency from the original KG between 0 and 1")
    parser.add_argument("--operation", type=str, default="incomplete", choices=["incomplete", "inconsistent"],\
                        help = "Choose to make the KB incomplete or inconsistent")
    parser.add_argument("--sample", type=str, default="No", choices=["No", "Yes"], help = "Sample if needed")
    return parser.parse_args()


if __name__ == "__main__":
    execute(get_default_arguments())
