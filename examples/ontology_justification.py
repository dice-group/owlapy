import argparse
import os

from owlapy import dl_to_owl_expression, manchester_to_owl_expression
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner import SyncReasoner


def main():
    parser = argparse.ArgumentParser(description="Justification Example for OWL Individual-Class Reasoning")
    parser.add_argument('--ontology_path', type=str, required=True, help='Path to the OWL ontology file.')
    parser.add_argument('--namespace', type=str, required=True, help='Namespace (IRI prefix) of ontology.')
    parser.add_argument('--individual_name', type=str, required=True, help='OWL individual name.')
    parser.add_argument('--class_expression', type=str, required=True, help='Class expression to justify.')
    parser.add_argument('--ce_syntax_choice', type=str, choices=["DL", "Manchester"], default="DL",help='Class expression syntax choice: "DL" or "Manchester". Default is "DL".'
    )

    args = parser.parse_args()

    ontology_path = args.ontology_path
    ns = args.namespace
    individual_name = args.individual_name
    class_expr_str = args.class_expression
    ce_syntax_choice = args.ce_syntax_choice

    print(f"Ontology Path: {ontology_path}")
    print(f"Namespace: {ns}")
    print(f"Individual Name: {individual_name}")
    print(f"Class Expression: {class_expr_str}")
    print(f"ce_syntax_choices: {ce_syntax_choice}")

    def adjust_namespace(ns: str) -> str:
        if ns.endswith(("#", "/", ":")):
            return ns
        else:
            return ns + "#"

    print(f"Loading ontology from: {ontology_path}")
    print("File exists:", os.path.exists(ontology_path))

    ontology = SyncOntology(ontology_path)
    reasoner = SyncReasoner(ontology, reasoner="Pellet")
    print("Reasoner initialized.")

    target_individual = OWLNamedIndividual(IRI.create(adjust_namespace(ns) + individual_name))
    print(f"Target Individual: {target_individual}")

    if ce_syntax_choice == "DL":
        target_class = dl_to_owl_expression(class_expr_str, adjust_namespace(ns))
    elif ce_syntax_choice == "Manchester":
        target_class = manchester_to_owl_expression(class_expr_str, adjust_namespace(ns))
    else:
        raise ValueError(f"Unsupported syntax choice please choose DL or Manchester: {args.ce_syntax_choices}")

    print(f"Target Class Expression: {target_class}")

    justifications = reasoner.create_justifications({target_individual}, target_class)
    print(f"Number of justifications found: {len(justifications)}")

    if not justifications:
        print("No justifications found.")
    else:
        for i, justification in enumerate(justifications, 1):
            print(f"\nJustification {i}:")
            for ax in justification:
                print("  ", ax)

if __name__ == "__main__":
    main()
