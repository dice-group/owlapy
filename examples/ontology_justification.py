import argparse
import os

from owlapy import dl_to_owl_expression, manchester_to_owl_expression
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner import SyncReasoner


def adjust_namespace(ns: str) -> str:
    """Ensure the namespace ends with a separator character."""
    return ns if ns.endswith(("#", "/", ":")) else ns + "#"


def main():
    parser = argparse.ArgumentParser(description="Justification Example for OWL Individual-Class Reasoning")
    parser.add_argument('--ontology_path', type=str, required=True, help='Path to the OWL ontology file.')
    parser.add_argument('--namespace', type=str, required=True, help='Namespace (IRI prefix) of ontology.')
    parser.add_argument('--individual_name', type=str, required=True, help='OWL individual name.')
    parser.add_argument('--class_expression', type=str, required=True, help='Class expression to justify.')
    parser.add_argument('--ce_syntax_choice', type=str, choices=["DL", "Manchester"], default="DL",
                        help='Class expression syntax choice: "DL" or "Manchester". Default is "DL".')

    args = parser.parse_args()

    ontology_path = args.ontology_path
    ns = adjust_namespace(args.namespace)
    individual_name = args.individual_name
    class_expr_str = args.class_expression
    ce_syntax_choice = args.ce_syntax_choice

    print(f"Ontology Path: {ontology_path}")
    print(f"Namespace: {ns}")
    print(f"Individual Name: {individual_name}")
    print(f"Class Expression: {class_expr_str}")
    print(f"Class Expression Syntax: {ce_syntax_choice}")

    if not os.path.exists(ontology_path):
        raise FileNotFoundError(f"Ontology file does not exist at: {ontology_path}")

    print("Loading ontology...")
    ontology = SyncOntology(ontology_path)

    print("Initializing reasoner...")
    reasoner = SyncReasoner(ontology, reasoner="Pellet")

    target_individual = OWLNamedIndividual(IRI.create(ns + individual_name))
    print(f"Target Individual: {target_individual}")

    if ce_syntax_choice == "DL":
        target_class = dl_to_owl_expression(class_expr_str, ns)
    elif ce_syntax_choice == "Manchester":
        target_class = manchester_to_owl_expression(class_expr_str, ns)
    else:
        raise ValueError("Invalid syntax choice. Use 'DL' or 'Manchester'.")

    print(f"Parsed Class Expression: {target_class}")

    # --- Call your updated justification method (no save) ---
    justifications = reasoner.create_justifications({target_individual}, target_class, save=False)
    # --- Call your updated justification method (with save) ---
    # justifications = reasoner.create_justifications({target_individual}, target_class, save=True)

    print(f"\nNumber of justifications found: {len(justifications)}")

    if not justifications:
        print("No justifications found.")
    else:
        for i, justification in enumerate(justifications, 1):
            print(f"\nJustification {i}:")
            for ax in justification:
                print("  ", ax)


if __name__ == "__main__":
    main()
