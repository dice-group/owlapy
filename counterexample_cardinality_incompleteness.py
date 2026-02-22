"""
Counterexample: CrossShardReasoner is incomplete for ≥ 2 r.C under OWA.

Ontology (TBox + ABox):
    AllDifferent(o1, o2)
    (a, r, o1)
    (a, r, o2)
    o1 : C
    o2 : C

Query: ≥ 2 r.C

Ground truth (single Pellet):  {a}
    a has two distinct r-fillers (o1, o2) that are both of type C → a ∈ ≥ 2 r.C ✓

CrossShardReasoner (3 shards):  {}
    Shard-0 has (a, r, o1) and (a, r, o2)  (but misses o1:C and o2:C)
    Shard-1 has o1:C                       (but misses a)
    Shard-2 has o2:C                       (but misses a)
    → Shard-0 Pellet cannot confirm fillers are of type C → local count fails.
    → Coordinator merely unions the empty sets → misses a ✗
"""

import argparse, os, ray
from pathlib import Path
from owlapy.owl_reasoner import SyncReasoner
from owlapy.class_expression import OWLClass, OWLObjectSomeValuesFrom, OWLObjectMinCardinality
from owlapy.owl_property import OWLObjectProperty
from owlapy.iri import IRI

# Assumes shard_ontology.py and ddp_reasoning.py are in the same directory
from shard_ontology import shard_ontology
from ddp_reasoning import ShardReasoner, CrossShardReasoner

NS = "http://example.org/test#"
ONTOLOGY_OWL = """\
<?xml version="1.0"?>
<rdf:RDF xmlns="http://example.org/test#"
     xml:base="http://example.org/test"
     xmlns:owl="http://www.w3.org/2002/07/owl#"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:xml="http://www.w3.org/XML/1998/namespace"
     xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
     xmlns:test="http://example.org/test#">
    
    <owl:Ontology rdf:about="http://example.org/test"/>
    <owl:Class rdf:about="http://example.org/test#C"/>
    <owl:ObjectProperty rdf:about="http://example.org/test#r"/>
    
    <owl:NamedIndividual rdf:about="http://example.org/test#a">
        <test:r rdf:resource="http://example.org/test#o1"/>
        <test:r rdf:resource="http://example.org/test#o2"/>
    </owl:NamedIndividual>
    
    <owl:NamedIndividual rdf:about="http://example.org/test#o1">
        <rdf:type rdf:resource="http://example.org/test#C"/>
    </owl:NamedIndividual>
    <owl:NamedIndividual rdf:about="http://example.org/test#o2">
        <rdf:type rdf:resource="http://example.org/test#C"/>
    </owl:NamedIndividual>
    
    <rdf:Description>
        <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#AllDifferent"/>
        <owl:distinctMembers rdf:parseType="Collection">
            <rdf:Description rdf:about="http://example.org/test#o1"/>
            <rdf:Description rdf:about="http://example.org/test#o2"/>
        </owl:distinctMembers>
    </rdf:Description>
</rdf:RDF>
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto_ray", action="store_true")
    # Using 3 shards guarantees 'a', 'o1', and 'o2' are spread apart
    parser.add_argument("--num_shards", type=int, default=3)
    args = parser.parse_args()

    out = os.path.join(os.path.dirname(__file__), "debug_cardinality_test")
    os.makedirs(out, exist_ok=True)
    owl_path = os.path.join(out, "cardinality_test.owl")
    with open(owl_path, "w") as f:
        f.write(ONTOLOGY_OWL)

    # Shard the ontology
    shard_ontology(owl_path, args.num_shards, out)

    # Initialize Ray
    if args.auto_ray:
        ray.init(num_cpus=os.cpu_count(),
                 resources={f"shard_{i}": 1 for i in range(args.num_shards)})
    else:
        ray.init(address="auto")

    # Define Queries
    C = OWLClass(IRI(NS, "C"))
    r = OWLObjectProperty(IRI(NS, "r"))
    
    # Query 1: ≥ 2 r.C (This will fail under cross-shard logic)
    min_2_r_C = OWLObjectMinCardinality(2, r, C)
    
    # Query 2: ∃ r.C (This will pass because of your cross-shard join logic!)
    exists_r_C = OWLObjectSomeValuesFrom(property=r, filler=C)

    # Ground truth (Full Ontology)
    print("Computing Ground Truth...")
    gt = SyncReasoner(ontology=owl_path, reasoner="Pellet")
    gt_min = {i.str for i in gt.instances(min_2_r_C)}
    gt_exists = {i.str for i in gt.instances(exists_r_C)}

    # Distributed Reasoning
    print("Computing Distributed Results...")
    stem = Path(owl_path).stem
    shards = [
        ShardReasoner.options(resources={f"shard_{i}": 1})
            .remote(f"Shard-{i}", os.path.join(out, f"{stem}_shard_{i}.owl"), "Pellet")
        for i in range(args.num_shards)
    ]
    dist = CrossShardReasoner(shards, open_world=True, verbose=False)
    dist_min = {i.str for i in dist.instances(min_2_r_C)}
    dist_exists = {i.str for i in dist.instances(exists_r_C)}

    # Report
    print("\n" + "=" * 65)
    for name, g, d in [("≥ 2 r.C", gt_min, dist_min),
                       ("∃ r.C  ", gt_exists, dist_exists)]:
        ok = "✓" if g == d else "✗"
        print(f"  {ok} {name}   GT={g}   Dist={d}")
        if g - d:
            print(f"       MISSING: {g - d} (Due to fractured ABox visibility)")
    print("=" * 65)

if __name__ == "__main__":
    main()