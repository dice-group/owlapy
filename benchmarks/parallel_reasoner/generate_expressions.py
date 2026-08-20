"""Generate a reproducible corpus of complex OWL class expressions for a dataset.

Builds N syntactically diverse expressions (intersection, union, complement,
existential/universal restriction, min/max/exact cardinality restriction) nested
up to a bounded depth, drawn only from classes and object properties that actually
appear in the target ontology's signature. Deterministic given the same --seed.

Usage:
    python generate_expressions.py --ontology ../../KGs/Family/family-benchmark_rich_background.owl \
        --out expressions/family.txt --n 100 --seed 42
"""
import argparse
import random

from owlapy.class_expression import (
    OWLClassExpression,
    OWLObjectAllValuesFrom,
    OWLObjectComplementOf,
    OWLObjectExactCardinality,
    OWLObjectIntersectionOf,
    OWLObjectMaxCardinality,
    OWLObjectMinCardinality,
    OWLObjectSomeValuesFrom,
    OWLObjectUnionOf,
)
from owlapy.owl_property import OWLObjectProperty
from owlapy.owl_reasoner_rdflib import RDFLibReasoner
from owlapy.render import owl_expression_to_manchester

MAX_DEPTH = 3
CARDINALITIES = (1, 2, 3)


def _atomic(classes, rng) -> OWLClassExpression:
    return rng.choice(classes)


def _random_concept(classes, properties, rng, depth: int) -> OWLClassExpression:
    if depth >= MAX_DEPTH:
        return _atomic(classes, rng)
    if not properties:
        constructors = ["atomic", "atomic", "intersection", "union", "complement"]
    else:
        constructors = ["atomic", "atomic", "intersection", "union", "complement",
                         "exists", "forall", "min_card", "max_card", "exact_card"]
    choice = rng.choice(constructors)

    if choice == "atomic":
        return _atomic(classes, rng)
    if choice == "intersection":
        return OWLObjectIntersectionOf([_random_concept(classes, properties, rng, depth + 1),
                                         _random_concept(classes, properties, rng, depth + 1)])
    if choice == "union":
        return OWLObjectUnionOf([_random_concept(classes, properties, rng, depth + 1),
                                  _random_concept(classes, properties, rng, depth + 1)])
    if choice == "complement":
        return OWLObjectComplementOf(_random_concept(classes, properties, rng, depth + 1))

    prop = rng.choice(properties)
    filler = _random_concept(classes, properties, rng, depth + 1)
    if choice == "exists":
        return OWLObjectSomeValuesFrom(prop, filler)
    if choice == "forall":
        return OWLObjectAllValuesFrom(prop, filler)
    card = rng.choice(CARDINALITIES)
    if choice == "min_card":
        return OWLObjectMinCardinality(card, prop, filler)
    if choice == "max_card":
        return OWLObjectMaxCardinality(card, prop, filler)
    return OWLObjectExactCardinality(card, prop, filler)


def generate(ontology_path: str, n: int, seed: int) -> list:
    onto = RDFLibReasoner(ontology_path).get_root_ontology()
    classes = [c for c in onto.classes_in_signature() if not isinstance(c, str)]
    properties = [OWLObjectProperty(p.iri) if not isinstance(p, OWLObjectProperty) else p
                  for p in onto.object_properties_in_signature()]
    classes = list({c: None for c in classes})  # de-dup, keep insertion order
    if not classes:
        raise ValueError(f"{ontology_path} has no named classes to build expressions from")

    rng = random.Random(seed)
    seen_manchester = set()
    expressions = []
    attempts = 0
    # top level is always a compound (never a bare atomic class -- those aren't "complex")
    top_level = ["intersection", "union", "complement", "exists", "forall",
                  "min_card", "max_card", "exact_card"]
    while len(expressions) < n and attempts < n * 50:
        attempts += 1
        choice = rng.choice(top_level) if properties else rng.choice(["intersection", "union", "complement"])
        if choice == "intersection":
            ce = OWLObjectIntersectionOf([_random_concept(classes, properties, rng, 1),
                                           _random_concept(classes, properties, rng, 1)])
        elif choice == "union":
            ce = OWLObjectUnionOf([_random_concept(classes, properties, rng, 1),
                                    _random_concept(classes, properties, rng, 1)])
        elif choice == "complement":
            ce = OWLObjectComplementOf(_random_concept(classes, properties, rng, 1))
        else:
            prop = rng.choice(properties)
            filler = _random_concept(classes, properties, rng, 1)
            if choice == "exists":
                ce = OWLObjectSomeValuesFrom(prop, filler)
            elif choice == "forall":
                ce = OWLObjectAllValuesFrom(prop, filler)
            else:
                card = rng.choice(CARDINALITIES)
                cls = {"min_card": OWLObjectMinCardinality, "max_card": OWLObjectMaxCardinality,
                       "exact_card": OWLObjectExactCardinality}[choice]
                ce = cls(card, prop, filler)

        rendered = owl_expression_to_manchester(ce)
        if rendered in seen_manchester:
            continue
        seen_manchester.add(rendered)
        expressions.append(rendered)

    if len(expressions) < n:
        raise RuntimeError(f"Only generated {len(expressions)}/{n} unique expressions for {ontology_path} "
                            f"after {attempts} attempts -- widen the constructor pool or raise attempts budget")
    return expressions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ontology", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    expressions = generate(args.ontology, args.n, args.seed)
    with open(args.out, "w") as f:
        for e in expressions:
            f.write(e + "\n")
    print(f"wrote {len(expressions)} expressions to {args.out}")


if __name__ == "__main__":
    main()
