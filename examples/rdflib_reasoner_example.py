"""
Example: Using RDFLibReasoner as a drop-in replacement for StructuralReasoner.

This example demonstrates how RDFLibReasoner can be used as a pure-Python
alternative to StructuralReasoner for ontology navigation and reasoning.
"""

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_property import OWLObjectProperty
from owlapy.owl_reasoner_rdflib import RDFLibReasoner


def main():
    # Load ontology
    print("Loading Family ontology...")
    onto = SyncOntology("KGs/Family/family-benchmark_rich_background.owl")

    # Initialize RDFLib-based reasoner (drop-in replacement for StructuralReasoner)
    print("Initializing RDFLibReasoner...")
    reasoner = RDFLibReasoner(onto, class_cache=True)

    # Define namespace and classes
    NS = "http://www.benchmark.org/family#"
    male = OWLClass(IRI(NS, "Male"))
    OWLClass(IRI(NS, "Female"))
    person = OWLClass(IRI(NS, "Person"))
    father = OWLClass(IRI(NS, "Father"))
    OWLClass(IRI(NS, "Mother"))

    # Example 1: Get instances of a class
    print("\n" + "="*60)
    print("Example 1: Retrieving instances")
    print("="*60)

    males = list(reasoner.instances(male))
    print(f"Found {len(males)} male individuals:")
    for ind in males[:5]:  # Show first 5
        print(f"  - {ind}")
    if len(males) > 5:
        print(f"  ... and {len(males) - 5} more")

    # Example 2: Get subclasses
    print("\n" + "="*60)
    print("Example 2: Class hierarchy - Direct subclasses")
    print("="*60)

    direct_subs = list(reasoner.sub_classes(person, direct=True))
    print(f"Direct subclasses of Person: {len(direct_subs)}")
    for cls in direct_subs:
        print(f"  - {cls}")

    # Example 3: Get all descendant subclasses
    print("\n" + "="*60)
    print("Example 3: Class hierarchy - All subclasses")
    print("="*60)

    all_subs = list(reasoner.sub_classes(person, direct=False))
    print(f"All descendant subclasses of Person: {len(all_subs)}")
    for cls in all_subs[:10]:  # Show first 10
        print(f"  - {cls}")
    if len(all_subs) > 10:
        print(f"  ... and {len(all_subs) - 10} more")

    # Example 4: Get superclasses
    print("\n" + "="*60)
    print("Example 4: Class hierarchy - Superclasses")
    print("="*60)

    direct_supers = list(reasoner.super_classes(male, direct=True))
    print(f"Direct superclasses of Male: {len(direct_supers)}")
    for cls in direct_supers:
        print(f"  - {cls}")

    all_supers = list(reasoner.super_classes(male, direct=False))
    print(f"All ancestor superclasses of Male: {len(all_supers)}")
    for cls in all_supers:
        print(f"  - {cls}")

    # Example 5: Check equivalent classes
    print("\n" + "="*60)
    print("Example 5: Equivalent classes")
    print("="*60)

    equiv = list(reasoner.equivalent_classes(male))
    if equiv:
        print("Classes equivalent to Male:")
        for cls in equiv:
            print(f"  - {cls}")
    else:
        print("No equivalent classes found for Male")

    # Example 6: Check disjoint classes
    print("\n" + "="*60)
    print("Example 6: Disjoint classes")
    print("="*60)

    disjoint = list(reasoner.disjoint_classes(male))
    if disjoint:
        print("Classes disjoint with Male:")
        for cls in disjoint[:5]:
            print(f"  - {cls}")
        if len(disjoint) > 5:
            print(f"  ... and {len(disjoint) - 5} more")
    else:
        print("No disjoint classes found for Male")

    # Example 7: Object property values
    print("\n" + "="*60)
    print("Example 7: Object property values")
    print("="*60)

    has_child = OWLObjectProperty(IRI(NS, "hasChild"))
    fathers = list(reasoner.instances(father))

    if fathers:
        sample_father = fathers[0]
        print(f"Children of {sample_father}:")

        children = list(reasoner.object_property_values(sample_father, has_child))
        if children:
            for child in children:
                print(f"  - {child}")
        else:
            print("  (none found)")

    # Example 8: Comparison with StructuralReasoner
    print("\n" + "="*60)
    print("Example 8: Comparison with StructuralReasoner")
    print("="*60)

    try:
        from owlapy.owl_reasoner import StructuralReasoner

        structural = StructuralReasoner(onto)

        # Compare instance retrieval
        rdflib_males = set(reasoner.instances(male))
        structural_males = set(structural.instances(male))

        print(f"RDFLibReasoner found {len(rdflib_males)} males")
        print(f"StructuralReasoner found {len(structural_males)} males")

        if rdflib_males == structural_males:
            print("✓ Results are identical!")
        else:
            print("✗ Results differ")
            diff = rdflib_males.symmetric_difference(structural_males)
            print(f"  Difference: {len(diff)} individuals")

        # Compare subclass retrieval
        rdflib_subs = set(reasoner.sub_classes(person, direct=True))
        structural_subs = set(structural.sub_classes(person, direct=True))

        print(f"\nRDFLibReasoner found {len(rdflib_subs)} direct subclasses")
        print(f"StructuralReasoner found {len(structural_subs)} direct subclasses")

        if rdflib_subs == structural_subs:
            print("✓ Subclass results are identical!")
        else:
            print("✗ Subclass results differ")

    except Exception as e:
        print(f"Could not compare with StructuralReasoner: {e}")

    # Example 9: Performance - caching benefits
    print("\n" + "="*60)
    print("Example 9: Cache performance")
    print("="*60)

    import time

    # Create a new reasoner with cache disabled
    reasoner_no_cache = RDFLibReasoner(onto, class_cache=False)

    # Time cached retrieval
    start = time.time()
    _ = list(reasoner.instances(male))
    cached_time = time.time() - start

    # Time non-cached retrieval
    start = time.time()
    _ = list(reasoner_no_cache.instances(male))
    no_cache_time = time.time() - start

    print(f"With cache: {cached_time*1000:.2f}ms")
    print(f"Without cache: {no_cache_time*1000:.2f}ms")
    print(f"Speedup: {no_cache_time/cached_time:.1f}x")

    print("\n" + "="*60)
    print("Benefits of RDFLibReasoner:")
    print("="*60)
    print("✓ Pure Python implementation (no owlready2 quirks)")
    print("✓ No Java dependencies for basic operations")
    print("✓ SPARQL-based querying")
    print("✓ Predictable RDF semantics")
    print("✓ Efficient caching")
    print("✓ Drop-in replacement for StructuralReasoner")
    print("="*60)


if __name__ == "__main__":
    main()
