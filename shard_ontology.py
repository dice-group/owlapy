"""
Shard an OWL ontology: Keep TBox intact, split ABox across shards.

Usage:
    python shard_ontology.py <ontology_path> <num_shards> [output_dir]

Example:
    python shard_ontology.py KGs/Family/family-benchmark_rich_background.owl 2
"""

import sys
import glob
import os
from pathlib import Path
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_axiom import (
    OWLClassAssertionAxiom, OWLObjectPropertyAssertionAxiom, 
    OWLDataPropertyAssertionAxiom, OWLSameIndividualAxiom,
    OWLDifferentIndividualsAxiom, OWLNegativeObjectPropertyAssertionAxiom,
    OWLNegativeDataPropertyAssertionAxiom
)


def shard_ontology(ontology_path: str, num_shards: int, output_dir: str = None):
    """
    Split an ontology into shards: TBox stays complete, ABox is partitioned.
    
    Args:
        ontology_path: Path to the source ontology
        num_shards: Number of shards to create
        output_dir: Output directory (default: same as source)
    """
    source = Path(ontology_path)
    output_dir = Path(output_dir) if output_dir else source.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean up any old shard files before generating new ones
    old_shards = glob.glob(str(output_dir / f"{source.stem}_shard_*.owl"))
    for old in old_shards:
        os.remove(old)
    
    print(f"Loading ontology: {source}")
    onto = SyncOntology(str(source))
    
    # Get all axioms via OWLAPI and classify into ABox vs rest.
    # We bypass the owlapy mapper here because it cannot represent every axiom
    # type (e.g. OWLSubPropertyChainOfAxiom / RBox axioms are unsupported), so
    # calling onto.get_tbox_axioms() silently drops them.
    j_onto_api = onto.get_owlapi_ontology()
    j_manager_src = onto.owlapi_manager
    from org.semanticweb.owlapi.model.parameters import Imports
    j_abox_set = set(j_onto_api.getABoxAxioms(Imports.INCLUDED))
    # Non-ABox axioms: TBox + RBox + Declarations (everything that is not ABox)
    j_non_abox_axioms = [ax for ax in j_onto_api.getAxioms() if ax not in j_abox_set]

    # ABox partitioning at the Python/owlapy level (works fine for all ABox types)
    tbox_axioms = list(onto.get_tbox_axioms())
    abox_axioms = list(onto.get_abox_axioms())
    
    print(f"TBox axioms: {len(tbox_axioms)} (owlapy-mapped); Non-ABox OWLAPI axioms (copied to all shards): {len(j_non_abox_axioms)}")
    print(f"ABox axioms: {len(abox_axioms)}")
    
    # Get all individuals and partition them
    individuals = list(onto.individuals_in_signature())
    print(f"Total individuals: {len(individuals)}")
    
    # Create individual -> shard mapping (round-robin)
    ind_to_shard = {ind: i % num_shards for i, ind in enumerate(individuals)}
    
    # Partition ABox axioms based on the "main" individual
    shard_abox = [[] for _ in range(num_shards)]
    
    for axiom in abox_axioms:
        if isinstance(axiom, OWLClassAssertionAxiom):
            ind = axiom.get_individual()
        elif isinstance(axiom, (OWLObjectPropertyAssertionAxiom, OWLDataPropertyAssertionAxiom,
                                OWLNegativeObjectPropertyAssertionAxiom, OWLNegativeDataPropertyAssertionAxiom)):
            ind = axiom.get_subject()
        elif isinstance(axiom, (OWLSameIndividualAxiom, OWLDifferentIndividualsAxiom)):
            # Put with the first individual
            ind = list(axiom.individuals())[0]
        else:
            ind = None
        
        if ind and ind in ind_to_shard:
            shard_abox[ind_to_shard[ind]].append(axiom)
    
    # Create shard ontologies - handle anonymous ontologies
    ont_iri = onto.get_ontology_id().get_ontology_iri()
    if ont_iri is not None:
        base_iri = ont_iri.as_str()
    else:
        # Fallback for anonymous ontologies
        base_iri = f"http://example.org/{source.stem}"
        print(f"Warning: Ontology has no IRI, using fallback: {base_iri}")
    
    for i in range(num_shards):
        shard_name = f"{source.stem}_shard_{i}{source.suffix}"
        shard_path = output_dir / shard_name
        
        # Create new ontology with shard IRI
        from owlapy.iri import IRI
        shard_iri = IRI.create(f"{base_iri}/shard/{i}")
        shard_onto = SyncOntology(shard_iri, load=False)
        j_shard_ont = shard_onto.get_owlapi_ontology()
        j_shard_manager = shard_onto.owlapi_manager

        # Add all non-ABox axioms (TBox + RBox + Declarations) directly via
        # OWLAPI to avoid axiom-type gaps in the owlapy mapper (e.g. property
        # chain axioms are in the RBox and are not mapped by owlapy).
        for j_ax in j_non_abox_axioms:
            j_shard_manager.addAxiom(j_shard_ont, j_ax)

        # Add this shard's ABox axioms (owlapy mapper handles these fine)
        for axiom in shard_abox[i]:
            shard_onto.add_axiom(axiom)
        
        shard_onto.save(str(shard_path))
        print(f"Shard {i}: {len(shard_abox[i])} ABox axioms → {shard_path}")
    
    print(f"\nCreated {num_shards} shards in {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    ontology_path = sys.argv[1]
    num_shards = int(sys.argv[2])
    output_dir = sys.argv[3] if len(sys.argv) > 3 else None
    
    shard_ontology(ontology_path, num_shards, output_dir)
