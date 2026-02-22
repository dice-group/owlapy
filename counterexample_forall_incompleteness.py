"""
Counterexample: CrossShardReasoner is incomplete for ∀ r.C under OWA.

Ontology (TBox + ABox):
    FunctionalObjectProperty(r)
    (a, r, b)
    b : C

Query: ∀ r.C

Ground truth (single Pellet):  {a}
    r is functional → b is a's only filler → b : C → a ∈ ∀ r.C  ✓

CrossShardReasoner (2 shards):  {}
    Shard-0 has b : C       (but no a)
    Shard-1 has (a, r, b)   (but no b : C)
    → Shard-1 Pellet cannot confirm b ∈ C → misses a  ✗

Usage:  python counterexample_forall_incompleteness.py --auto_ray
"""

import argparse, os, ray
from pathlib import Path
from owlapy.owl_reasoner import SyncReasoner
from owlapy.class_expression import OWLClass, OWLObjectAllValuesFrom, OWLObjectSomeValuesFrom
from owlapy.owl_property import OWLObjectProperty
from owlapy.iri import IRI
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
    <owl:ObjectProperty rdf:about="http://example.org/test#r">
        <rdf:type rdf:resource="http://www.w3.org/2002/07/owl#FunctionalProperty"/>
    </owl:ObjectProperty>
    <owl:NamedIndividual rdf:about="http://example.org/test#a">
        <test:r rdf:resource="http://example.org/test#b"/>
    </owl:NamedIndividual>
    <owl:NamedIndividual rdf:about="http://example.org/test#b">
        <rdf:type rdf:resource="http://example.org/test#C"/>
    </owl:NamedIndividual>
</rdf:RDF>
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto_ray", action="store_true")
    parser.add_argument("--num_shards", type=int, default=2)
    args = parser.parse_args()

    out = os.path.join(os.path.dirname(__file__), "debug_forall_test")
    os.makedirs(out, exist_ok=True)
    owl_path = os.path.join(out, "forall_test.owl")
    with open(owl_path, "w") as f:
        f.write(ONTOLOGY_OWL)

    # Shard
    shard_ontology(owl_path, args.num_shards, out)

    # Ray
    if args.auto_ray:
        ray.init(num_cpus=os.cpu_count(),
                 resources={f"shard_{i}": 1 for i in range(args.num_shards)})
    else:
        ray.init(address="auto")

    # Queries
    C = OWLClass(IRI(NS, "C"))
    r = OWLObjectProperty(IRI(NS, "r"))
    forall_r_C = OWLObjectAllValuesFrom(property=r, filler=C)
    exists_r_C = OWLObjectSomeValuesFrom(property=r, filler=C)

    # Ground truth
    gt = SyncReasoner(ontology=owl_path, reasoner="Pellet")
    gt_forall = {i.str for i in gt.instances(forall_r_C)}
    gt_exists = {i.str for i in gt.instances(exists_r_C)}

    # Distributed
    stem = Path(owl_path).stem
    shards = [
        ShardReasoner.options(resources={f"shard_{i}": 1})
            .remote(f"Shard-{i}", os.path.join(out, f"{stem}_shard_{i}.owl"), "Pellet")
        for i in range(args.num_shards)
    ]
    dist = CrossShardReasoner(shards, open_world=True, verbose=False)
    dist_forall = {i.str for i in dist.instances(forall_r_C)}
    dist_exists = {i.str for i in dist.instances(exists_r_C)}

    # Report
    print("\n" + "=" * 60)
    for name, g, d in [("∀ r.C", gt_forall, dist_forall),
                        ("∃ r.C", gt_exists, dist_exists)]:
        ok = "✓" if g == d else "✗"
        print(f"  {ok} {name}   GT={g}   Dist={d}")
        if g - d:
            print(f"       MISSING: {g - d}")
    print("=" * 60)

if __name__ == "__main__":
    main()
