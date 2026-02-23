"""
Counterexample: CrossShardReasoner is incomplete for property chains under OWA.

Ontology (TBox + ABox):
    PropertyChain: r o s -> t  (If x has r to y, and y has s to z, then x has t to z)
    (a, r, b)
    (b, s, c)
    c : C

Query: ∃ t.C

Ground truth (single Pellet):  {a}
    a -> r -> b -> s -> c implies a -> t -> c. Since c:C, a ∈ ∃ t.C ✓

CrossShardReasoner (3 shards):  {}
    Shard-0 has (a, r, b)   (but misses b -> s -> c)
    Shard-1 has (b, s, c)   (but misses a -> r -> b)
    Shard-2 has c : C
    → Coordinator evaluates C -> {c}.
    → Coordinator asks all shards for subjects with 't' edges to 'c'.
    → Shard-0 cannot infer (a, t, c) because it doesn't know (b, s, c).
    → Shard-1 doesn't have 'a' as a subject.
    → Result is empty ✗
"""

import argparse, os, ray
from pathlib import Path
from owlapy.owl_reasoner import SyncReasoner
from owlapy.class_expression import OWLClass, OWLObjectSomeValuesFrom
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
    <owl:ObjectProperty rdf:about="http://example.org/test#s"/>
    <owl:ObjectProperty rdf:about="http://example.org/test#t">
        <owl:propertyChainAxiom rdf:parseType="Collection">
            <rdf:Description rdf:about="http://example.org/test#r"/>
            <rdf:Description rdf:about="http://example.org/test#s"/>
        </owl:propertyChainAxiom>
    </owl:ObjectProperty>
    
    <owl:NamedIndividual rdf:about="http://example.org/test#a">
        <test:r rdf:resource="http://example.org/test#b"/>
    </owl:NamedIndividual>
    
    <owl:NamedIndividual rdf:about="http://example.org/test#b">
        <test:s rdf:resource="http://example.org/test#c"/>
    </owl:NamedIndividual>
    
    <owl:NamedIndividual rdf:about="http://example.org/test#c">
        <rdf:type rdf:resource="http://example.org/test#C"/>
    </owl:NamedIndividual>
</rdf:RDF>
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto_ray", action="store_true")
    # Using 3 shards to split 'a', 'b', and 'c' into separate partitions
    parser.add_argument("--num_shards", type=int, default=3)
    args = parser.parse_args()

    out = os.path.join(os.path.dirname(__file__), "debug_chain_test")
    os.makedirs(out, exist_ok=True)
    owl_path = os.path.join(out, "chain_test.owl")
    with open(owl_path, "w") as f:
        f.write(ONTOLOGY_OWL)

    # Shard the ontology
    shard_ontology(owl_path, args.num_shards, out)

    # Define Query: ∃ t.C
    C = OWLClass(IRI(NS, "C"))
    t = OWLObjectProperty(IRI(NS, "t"))
    exists_t_C = OWLObjectSomeValuesFrom(property=t, filler=C)

    # Ground truth (Full Ontology)
    # NOTE: SyncReasoner must be created BEFORE ray.init() to avoid a
    # SIGSEGV caused by JPype/Ray JVM conflicts in the driver process.
    print("Computing Ground Truth...")
    gt = SyncReasoner(ontology=owl_path, reasoner="Pellet")
    gt_exists = {i.str for i in gt.instances(exists_t_C)}

    # Initialize Ray (after ground-truth JVM is running)
    if args.auto_ray:
        ray.init(num_cpus=os.cpu_count(),
                 resources={f"shard_{i}": 1 for i in range(args.num_shards)})
    else:
        ray.init(address="auto")

    # Distributed Reasoning
    print("Computing Distributed Results...")
    stem = Path(owl_path).stem
    shards = [
        ShardReasoner.options(resources={f"shard_{i}": 1})
            .remote(f"Shard-{i}", os.path.join(out, f"{stem}_shard_{i}.owl"), "Pellet", verbose=False)
        for i in range(args.num_shards)
    ]
    dist = CrossShardReasoner(shards, open_world=True, verbose=False)
    dist_exists = {i.str for i in dist.instances(exists_t_C)}

    # Report
    print("\n" + "=" * 65)
    for name, g, d in [("∃ t.C", gt_exists, dist_exists)]:
        ok = "✓" if g == d else "✗"
        print(f"  {ok} {name}   GT={g}   Dist={d}")
        if g - d:
            print(f"       MISSING: {g - d} (Due to fractured property chain path)")
    print("=" * 65)

if __name__ == "__main__":
    main()