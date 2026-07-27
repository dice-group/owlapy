# Ontology Management

## Creating Ontologies

### Create Empty Ontology

```python
from owlapy.util_owl_static_funcs import create_ontology
from owlapy.iri import IRI

# Create with IRI string
onto = create_ontology("http://example.com/my-ontology")

# Or create with IRI object
iri = IRI.create("http://example.com/my-ontology")
onto = create_ontology(iri)
```

### Create Ontology with Initial Content

```python
from owlapy.owl_ontology import SyncOntology
from owlapy.iri import IRI
from owlapy.class_expression import OWLClass
from owlapy.owl_axiom import OWLSubClassOfAxiom

# Create ontology
iri = IRI.create("http://example.com/university")
onto = SyncOntology(iri)

# Define namespace
NS = "http://example.com/university#"

# Add classes
person = OWLClass(NS + "Person")
student = OWLClass(NS + "Student")
professor = OWLClass(NS + "Professor")

# Add axioms
onto.add_axiom(OWLSubClassOfAxiom(student, person))
onto.add_axiom(OWLSubClassOfAxiom(professor, person))

# Save
onto.save("university.owl")
```

## Loading Ontologies

### Load from File

```python
from owlapy.owl_ontology import SyncOntology

# Load OWL/RDF file
onto = SyncOntology("path/to/ontology.owl")

# Supported formats: .owl, .rdf, .ttl, .n3, .nt
onto = SyncOntology("ontology.ttl")
```

### Load from URL

```python
# Load directly from web
onto = SyncOntology("http://example.com/ontology.owl")

# Load from GitHub
onto = SyncOntology("https://raw.githubusercontent.com/user/repo/main/onto.owl")
```

### Load with Error Handling

```python
import os

def safe_load_ontology(path: str) -> SyncOntology:
    """Safely load ontology with validation."""
    # Check file exists
    if not os.path.exists(path):
        raise FileNotFoundError(f"Ontology not found: {path}")
    
    # Check file extension
    if not path.endswith(('.owl', '.rdf', '.ttl', '.n3', '.nt')):
        raise ValueError(f"Unsupported format: {path}")
    
    try:
        onto = SyncOntology(path)
        print(f"✓ Loaded ontology: {path}")
        print(f"  Classes: {len(list(onto.classes_in_signature()))}")
        print(f"  Individuals: {len(list(onto.individuals_in_signature()))}")
        return onto
    except Exception as e:
        raise RuntimeError(f"Failed to load ontology: {e}")

# Usage
onto = safe_load_ontology("family.owl")
```

## Saving Ontologies

### Save in Different Formats

```python
# RDF/XML format (default)
onto.save("output.owl")
onto.save("output.owl", document_format="rdfxml")

# Turtle format (OWL API writer)
onto.save("output.ttl", document_format="turtle")

# N-Triples format (rdflib writer)
onto.save("output.nt", document_format="ntriples")

# N3 format (rdflib writer)
onto.save("output.n3", document_format="n3")
```

`document_format` accepts many more values (`"owlxml"`, `"functional"`, `"manchester"`,
`"trig"`, `"json-ld"`, ...) — see `SyncOntology.save()`'s docstring for the full table.

### Save with Compression

```python
import gzip

# Save and compress
onto.save("ontology.owl")
with open("ontology.owl", "rb") as f_in:
    with gzip.open("ontology.owl.gz", "wb") as f_out:
        f_out.writelines(f_in)
```

### Prefix Management (`SyncOntology` only)

By default, entities from namespaces owlapy doesn't already know about (`owl:`, `rdf:`,
`rdfs:`, `xsd:`, and the ontology's own IRI) serialize as full IRIs instead of a short
`prefix:name`. Declare a prefix to get the abbreviated form back:

```python
onto.set_prefix("foaf", "http://xmlns.com/foaf/0.1/")

onto.get_prefixes()
# {"owl": "...", "rdf": "...", "rdfs": "...", "xsd": "...", "foaf": "http://xmlns.com/foaf/0.1/"}

onto.remove_prefix("foaf")  # back to full IRIs on the next save()
```

Prefixes are honoured by `save()` for both the OWL API–backed formats that support them
(RDF/XML, OWL/XML, Turtle, Functional Syntax, Manchester Syntax) and the rdflib-backed
formats (`turtle2`, `n3`, `trig`, `json-ld`). `set_prefix`/`remove_prefix` raise
`ValueError` if the ontology's current document format doesn't support prefixes at all
(LaTeX, DL Syntax, KRSS2, OBO).

## Inspecting Ontologies

### Get All Entities

```python
# Get all classes
classes = list(onto.classes_in_signature())
print(f"Classes ({len(classes)}):")
for cls in classes[:10]:  # First 10
    print(f"  - {cls.str}")

# Get all individuals
individuals = list(onto.individuals_in_signature())
print(f"Individuals: {len(individuals)}")

# Get all object properties
obj_props = list(onto.object_properties_in_signature())
print(f"Object properties: {len(obj_props)}")

# Get all data properties
data_props = list(onto.data_properties_in_signature())
print(f"Data properties: {len(data_props)}")
```

### Get Ontology IRI

```python
ontology_iri = onto.get_ontology_id().get_ontology_iri()
print(f"Ontology IRI: {ontology_iri.as_str()}")
```

### Count Axioms

```python
# Get all axioms (expensive!)
axioms = list(onto.get_tbox_axioms()) + list(onto.get_abox_axioms())
print(f"Total axioms: {len(axioms)}")

# Get TBox axioms (class definitions)
tbox = list(onto.get_tbox_axioms())
print(f"TBox axioms: {len(tbox)}")

# Get ABox axioms (individual assertions)
abox = list(onto.get_abox_axioms())
print(f"ABox axioms: {len(abox)}")
```

## Modifying Ontologies

### Add Axioms

```python
from owlapy.owl_axiom import (
    OWLSubClassOfAxiom,
    OWLClassAssertionAxiom,
    OWLObjectPropertyAssertionAxiom
)
from owlapy.owl_individual import OWLNamedIndividual

NS = "http://example.com/onto#"

# Add class hierarchy
student = OWLClass(NS + "Student")
person = OWLClass(NS + "Person")
onto.add_axiom(OWLSubClassOfAxiom(student, person))

# Add individual
john = OWLNamedIndividual(NS + "John")
onto.add_axiom(OWLClassAssertionAxiom(john, student))

# Add property assertion
mary = OWLNamedIndividual(NS + "Mary")
has_friend = OWLObjectProperty(NS + "hasFriend")
onto.add_axiom(OWLObjectPropertyAssertionAxiom(john, has_friend, mary))
```

### Remove Axioms

```python
# Create axiom to remove
axiom = OWLSubClassOfAxiom(student, person)

# Remove it
onto.remove_axiom(axiom)
```

### Batch Add Axioms

```python
# Prepare axioms
axioms = [
    OWLSubClassOfAxiom(student, person),
    OWLSubClassOfAxiom(professor, person),
    OWLClassAssertionAxiom(john, student),
    OWLClassAssertionAxiom(mary, professor),
]

# Add all at once
for axiom in axioms:
    onto.add_axiom(axiom)

print(f"Added {len(axioms)} axioms")
```

## Merging Ontologies

### Simple Merge

```python
# Load two ontologies
onto1 = SyncOntology("ontology1.owl")
onto2 = SyncOntology("ontology2.owl")

# Get all axioms from onto2
axioms2 = list(onto2.get_tbox_axioms()) + list(onto2.get_abox_axioms())

# Add to onto1
for axiom in axioms2:
    onto1.add_axiom(axiom)

# Save merged ontology
onto1.save("merged_ontology.owl")
```

### Merge with Namespace Mapping

```python
def merge_ontologies(target_onto, source_onto, namespace_map=None):
    """Merge source ontology into target with optional namespace mapping."""
    axioms = list(source_onto.get_tbox_axioms()) + list(source_onto.get_abox_axioms())
    
    for axiom in axioms:
        # Apply namespace mapping if provided
        if namespace_map:
            # ... implement namespace remapping logic ...
            pass
        target_onto.add_axiom(axiom)
    
    return target_onto

# Usage
merged = merge_ontologies(onto1, onto2)
```

## Filtering and Extraction

### Extract Subontology by Classes

```python
def extract_classes(onto, class_iris: list):
    """Extract subontology containing only specified classes."""
    from owlapy.util_owl_static_funcs import create_ontology
    
    # Create new ontology (with_owlapi=True: add_axiom/get_tbox_axioms need the OWLAPI-backed ontology)
    new_onto = create_ontology("http://example.com/extracted", with_owlapi=True)
    
    # Get relevant axioms
    for cls_iri in class_iris:
        cls = OWLClass(cls_iri)
        
        # Get axioms referencing this class
        for axiom in onto.get_tbox_axioms():
            # Check if axiom involves this class
            if cls in axiom.signature():
                new_onto.add_axiom(axiom)
    
    return new_onto

# Usage
selected_classes = [
    "http://example.com/onto#Person",
    "http://example.com/onto#Student"
]
subontology = extract_classes(onto, selected_classes)
```

### Filter Individuals by Class

```python
def get_individuals_of_class(onto, cls: OWLClass):
    """Get all individuals asserted to be of given class."""
    from owlapy.owl_axiom import OWLClassAssertionAxiom
    
    individuals = []
    for axiom in onto.get_abox_axioms():
        if isinstance(axiom, OWLClassAssertionAxiom):
            if axiom.get_class_expression() == cls:
                individuals.append(axiom.get_individual())
    
    return individuals

# Usage
students = get_individuals_of_class(onto, OWLClass(NS + "Student"))
print(f"Found {len(students)} students")
```

## CSV to RDF Conversion

### Basic CSV to RDF

```python
from owlapy.util_owl_static_funcs import csv_to_rdf_kg

# Convert CSV file to RDF knowledge graph.
# Each row becomes an individual; each column becomes a data property named after
# the column header, scoped under the given namespace.
csv_to_rdf_kg(
    path_csv="data.csv",
    path_kg="knowledge_graph.owl",
    namespace="http://example.com/data#",
)
```

### CSV to RDF with Custom Mapping

CSV file (`students.csv`):
```csv
id,name,age,major
s001,John Doe,20,Computer Science
s002,Jane Smith,22,Mathematics
```

Code:
```python
import csv
from owlapy.owl_ontology import SyncOntology
from owlapy.iri import IRI
from owlapy.class_expression import OWLClass
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_property import OWLDataProperty
from owlapy.owl_axiom import OWLClassAssertionAxiom, OWLDataPropertyAssertionAxiom
from owlapy.owl_literal import OWLLiteral, IntegerOWLDatatype, StringOWLDatatype

NS = "http://example.com/university#"

# Create ontology
onto = SyncOntology(IRI.create(NS[:-1]))

# Define classes and properties
student_class = OWLClass(NS + "Student")
has_id = OWLDataProperty(NS + "hasID")
has_name = OWLDataProperty(NS + "hasName")
has_age = OWLDataProperty(NS + "hasAge")
has_major = OWLDataProperty(NS + "hasMajor")

# Read CSV and create individuals
with open("students.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Create individual
        student = OWLNamedIndividual(NS + row["id"])
        onto.add_axiom(OWLClassAssertionAxiom(student, student_class))
        
        # Add properties
        onto.add_axiom(OWLDataPropertyAssertionAxiom(
            student, has_id, OWLLiteral(row["id"], StringOWLDatatype)
        ))
        onto.add_axiom(OWLDataPropertyAssertionAxiom(
            student, has_name, OWLLiteral(row["name"], StringOWLDatatype)
        ))
        onto.add_axiom(OWLDataPropertyAssertionAxiom(
            student, has_age, OWLLiteral(int(row["age"]), IntegerOWLDatatype)
        ))
        onto.add_axiom(OWLDataPropertyAssertionAxiom(
            student, has_major, OWLLiteral(row["major"], StringOWLDatatype)
        ))

# Save
onto.save("students_kg.owl")
```

## Ontology Statistics

### Get Comprehensive Statistics

```python
def ontology_statistics(onto):
    """Get detailed statistics about an ontology."""
    stats = {
        "classes": len(list(onto.classes_in_signature())),
        "individuals": len(list(onto.individuals_in_signature())),
        "object_properties": len(list(onto.object_properties_in_signature())),
        "data_properties": len(list(onto.data_properties_in_signature())),
        "tbox_axioms": len(list(onto.get_tbox_axioms())),
        "abox_axioms": len(list(onto.get_abox_axioms())),
    }
    
    print("Ontology Statistics:")
    print("=" * 50)
    for key, value in stats.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    return stats

# Usage
stats = ontology_statistics(onto)
```

## Ontology Validation

### Check for Empty Classes

```python
from owlapy.owl_reasoner_rdflib import RDFLibReasoner

def find_empty_classes(onto):
    """Find classes with no instances."""
    reasoner = RDFLibReasoner(onto)
    empty_classes = []
    
    for cls in onto.classes_in_signature():
        instances = list(reasoner.instances(cls))
        if len(instances) == 0:
            empty_classes.append(cls)
    
    print(f"Found {len(empty_classes)} empty classes")
    return empty_classes

# Usage
empty = find_empty_classes(onto)
```

### Validate IRI Consistency

```python
def validate_iris(onto, expected_namespace: str):
    """Check if all entities use expected namespace."""
    issues = []
    
    # Check classes
    for cls in onto.classes_in_signature():
        if not cls.str.startswith(expected_namespace):
            issues.append(f"Class with wrong namespace: {cls.str}")
    
    # Check individuals
    for ind in onto.individuals_in_signature():
        if not ind.str.startswith(expected_namespace):
            issues.append(f"Individual with wrong namespace: {ind.str}")
    
    if issues:
        print(f"Found {len(issues)} IRI issues:")
        for issue in issues[:10]:
            print(f"  - {issue}")
    else:
        print("✓ All IRIs use correct namespace")
    
    return issues

# Usage
validate_iris(onto, "http://example.com/onto#")
```

## Best Practices

### ✅ DO:
- Use `SyncOntology` for thread safety
- Save regularly when making many changes
- Validate IRIs before adding entities
- Use consistent namespaces
- Back up ontologies before major modifications

### ❌ DON'T:
- Mix multiple namespaces unnecessarily
- Add axioms without validation
- Load very large ontologies entirely into memory
- Forget to save after modifications

## Next Steps

- Learn about [class expressions](04_class_expressions.md)
- Explore [reasoning](05_reasoning.md)
- Check [common patterns](08_common_patterns.md)
