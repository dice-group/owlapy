#!/usr/bin/env python3
"""
Minimal example showing how to use SyncReasoner.get_contrastive_explanation()
"""

from owlapy import manchester_to_owl_expression
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner import SyncReasoner


def make_individual(name: str, base_iri: str) -> OWLNamedIndividual:
    """Create an OWL individual from a short name or full IRI."""
    iri = name if name.startswith("http") else f"{base_iri.rstrip('#/') }#{name}"
    return OWLNamedIndividual(IRI.create(iri))


def main():
    # --- Paths and config ---
    ontology_path = "/home/tiwari/workspace_dice/datasource/family.owl"
    base_iri = "http://www.benchmark.org/family#"
    reasoner_name = "HermiT"

    # --- Load ontology ---
    ontology = SyncOntology(ontology_path)

    # --- Initialize reasoner ---
    reasoner = SyncReasoner(ontology, reasoner=reasoner_name)

    # --- Define class expression and individuals ---
    class_expr = manchester_to_owl_expression(
        "Sister and (hasSibling some (married some (hasChild some Grandchild)))",
        base_iri,
    )

    fact = make_individual("F9F143", base_iri)
    foil = make_individual("F9M161", base_iri)

    # --- Call get_contrastive_explanation ---
    result = reasoner.get_contrastive_explanation(class_expr, fact, foil)

    # --- Print concise results ---
    print("\nContrastive Explanation Results:")
    print("-" * 40)
    print(f"Common ({len(result['common'])}):")
    for ax in result["common"]:
        print(" ", ax)

    print(f"\nDifferent ({len(result['different'])}):")
    for ax in result["different"]:
        print(" ", ax)

    print(f"\nConflict ({len(result['conflict'])}):")
    for ax in result["conflict"]:
        print(" ", ax)

    print("\nFoil Mapping:")
    for k, v in result["foil_mapping"].items():
        print(f"  {k} -> {v}")


if __name__ == "__main__":
    main()
