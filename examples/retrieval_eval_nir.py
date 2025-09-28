"""
How to run:
CUDA_VISIBLE_DEVICES=3 python examples/retrieval_eval_nir.py --path_kg KGs/NewFamily/kb/ontology.owl
"""
from owlapy.owl_reasoner import StructuralReasoner, EBR
from owlapy.owl_ontology import Ontology, NeuralOntology
from owlapy.utils import jaccard_similarity, f1_set_similarity
from owlapy.parser import DLSyntaxParser
import json
import time
from typing import Tuple, Set
import pandas as pd
from owlapy import owl_expression_to_dl
from itertools import chain
from argparse import ArgumentParser
import os
from tqdm import tqdm
import ast
# Set pandas options to ensure full output
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.colheader_justify', 'left')
pd.set_option('display.expand_frame_repr', False)
def dataframe_to_latex(df, caption="Table Caption", label="tab:table_label", decimals=3):
    """
    Converts a pandas DataFrame to a LaTeX table.

    Args:
        df (pd.DataFrame): The DataFrame to convert.
        caption (str): The table caption.
        label (str): The table label.
        decimals (int): Number of decimal places to round to.

    Returns:
        str: The LaTeX table string.
    """

    latex_str = "\\begin{table}[htbp]\n"
    latex_str += "\\centering\n"
    latex_str += "\\caption{" + caption + "}\n"
    latex_str += "\\label{" + label + "}\n"
    latex_str += "\\resizebox{\\textwidth}{!}{\\begin{tabular}{" + "c" * (df.shape[1] + 1) + "}\n"  # +1 for the index column
    latex_str += "\\toprule\n"

    # Header row
    header = ["Type"] + list(df.columns)
    latex_str += " & ".join(header) + " \\\\\n"
    latex_str += "\\midrule\n"

    # Data rows
    for index, row in df.iterrows():
        row_str = [index] + [f"{val:.{decimals}f}" if isinstance(val, float) else str(val) for val in row]
        latex_str += " & ".join(row_str) + " \\\\\n"

    latex_str += "\\bottomrule\n"
    latex_str += "\\end{tabular}}\n"
    latex_str += "\\end{table}"

    return latex_str
def make_safe_eval():
    row_counter = {"i": -1}  # mutable dict to hold state

    def safe_eval(x):
        row_counter["i"] += 1
        try:
            return ast.literal_eval(x)
        except Exception:
            print(f"⚠️ Parse failed at row {row_counter['i']}: {x}")
            return None

    return safe_eval
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
    print(symbolic_kb,ontology)
    kb_namespace = list(symbolic_kb._ontology.classes_in_signature())[0].str
    if "#" in kb_namespace:
        kb_namespace = kb_namespace.split("#")[0] + "#"
    elif "/" in kb_namespace:
        kb_namespace = kb_namespace[:kb_namespace.rfind("/")] + "/"
    elif ":" in kb_namespace:
        kb_namespace = kb_namespace[:kb_namespace.rfind(":")] + ":"
    expression_parser = DLSyntaxParser(kb_namespace)
    # (2) Initialize Neural OWL Reasoner
    # Use EBR instead of TripleStoreNeuralReasoner
    if args.path_kge_model:
        neural_ontology = NeuralOntology(path_neural_embedding=args.path_kge_model, batch_size=args.batch_size, device=args.device, gamma=args.gamma)
    else:
        neural_ontology = NeuralOntology(path_neural_embedding=args.path_kg, train_if_not_exists=True, model= args.model, epochs = args.epochs, batch_size=args.batch_size, device=args.device, gamma=args.gamma)
    neural_owl_reasoner = EBR(ontology=neural_ontology)

    # () Iterate over single OWL Class Expressions in ALCQIHO
    # Retrieval Results
    def concept_retrieval(retriever_func, c) -> Tuple[Set[str], float]:
        start_time = time.time()
        return {i.str for i in retriever_func.instances(c)}, time.time() - start_time
    with open(args.dataset_dir + '/data/test_data.json') as f:
        concepts = json.load(f)
        concepts = list(map(expression_parser.parse, concepts))
    rows = []
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
        rows.append({
        "Expression": owl_expression_to_dl(expression),
        "Type": type(expression).__name__,
        "Jaccard Similarity": jaccard_sim,
        "F1": f1_sim,
        "Runtime Benefits": runtime_y - runtime_neural_y,
        "Runtime Neural": runtime_neural_y,
        "Symbolic_Retrieval": retrieval_y,
        "Symbolic_Retrieval_Neural": retrieval_neural_y,})

        # () Update the progress bar.
        tqdm_bar.set_description_str(
            f"Expression: {owl_expression_to_dl(expression)} | Jaccard Similarity:{jaccard_sim:.4f} | F1 :{f1_sim:.4f} | Runtime Benefits:{runtime_y - runtime_neural_y:.3f}"
        )
    df = pd.DataFrame(rows)
    df.to_csv(args.path_report, index=False)
    print("\n\x1b[6;30;42mSuccessfully saved the results!\x1b[0m\n")
    del df
    df = pd.read_csv(
    args.path_report,
    index_col=0,
    converters={
        'Symbolic_Retrieval':  make_safe_eval(),
        'Symbolic_Retrieval_Neural':  make_safe_eval(),
    })
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
    ## Write results as LaTex table
    model_name = args.model.capitalize() if args.model.lower() not in ["lstm",
                                                                       "gru"] else args.model.upper()
    dataset_name = " ".join(list(map(str.capitalize,
                                     [name for name in args.dataset_dir.split("/") if name.strip()][
                                         -1].split("_"))))
    dataset_name_lower = "_".join(list(map(str.lower, dataset_name.split(" "))))
    latex_str = dataframe_to_latex(mean_df, caption=args.caption,
                                   label="tab:" + model_name.lower() + "_" + dataset_name_lower)
    with open(os.path.join(args.output_dir, f"{args.model.lower()}_latex_results.txt"), "w") as f:
        f.write(latex_str)
    return jaccard_sim, f1_sim

def get_default_arguments():
    parser = ArgumentParser()
    parser.add_argument("--model", type=str, default="DeCaL")
    parser.add_argument("--output_dir", type=str, default="KGs/NewFamily/results")
    parser.add_argument("--path_kg", type=str, default="KGs/NewFamily/kb/ontology.owl")
    parser.add_argument("--caption", type=str, default="Retrieval Results")
    parser.add_argument("--path_kge_model", type=str, default=None)
    parser.add_argument("--gamma", type=float, default=0.9)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--ratio_sample_nc", type=float, default=1, help="To sample OWL Classes.")
    parser.add_argument("--ratio_sample_object_prop", type=float, default=1, help="To sample OWL Object Properties.")
    parser.add_argument("--min_jaccard_similarity", type=float, default=0.0, help="Minimum Jaccard similarity to be achieve by the reasoner")
    parser.add_argument("--num_nominals", type=int, default=10, help="Number of OWL named individuals to be sampled.")
    parser.add_argument("--batch_size", type=int, default=256, help="Batch size for the KGE model.")
    parser.add_argument("--epochs", type=int, default=1, help="Number of epochs to train the KGE model if not provided.")
    parser.add_argument("--device", type=str, default="cpu", help="Device to use for the KGE model.")
    parser.add_argument("--dataset_dir", type=str, default="KGs/NewFamily", help="Directory containing test_data.json")
    # H is obtained if the forward chain is applied on KG.
    parser.add_argument("--path_report", type=str, default="ALCQHI_Retrieval_Results.csv")
    return parser.parse_args()

if __name__ == "__main__":
    execute(get_default_arguments())