"""
Shard an OWL ontology: Keep TBox intact, split ABox across shards.

Usage:
    python shard_ontology.py <ontology_path> <num_shards> [output_dir]

Example:
    python shard_ontology.py KGs/Family/family-benchmark_rich_background.owl 2
"""

import sys
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
    
    print(f"Loading ontology: {source}")
    onto = SyncOntology(str(source))
    
    # Get TBox and ABox axioms directly
    tbox_axioms = list(onto.get_tbox_axioms())
    abox_axioms = list(onto.get_abox_axioms())
    
    print(f"TBox axioms: {len(tbox_axioms)}")
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
        
        # Add all TBox axioms
        for axiom in tbox_axioms:
            shard_onto.add_axiom(axiom)
        
        # Add this shard's ABox axioms
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
