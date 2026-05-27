# Getting Started with owlapy

## Installation

### Basic Installation

```bash
pip install owlapy
```

### Installation from Source

```bash
git clone https://github.com/dice-group/owlapy
cd owlapy
conda create -n owlapy_env python=3.11 --no-default-packages
conda activate owlapy_env
pip install -e .
```

### Development Installation

```bash
pip install -e '.[dev]'
```

This includes additional dependencies for:
- Testing (pytest, coverage)
- Linting (ruff)
- Documentation (sphinx)

### Optional Dependencies

**For LLM-based ontology generation (AGenKG):**
```bash
pip install owlapy[agentic]
# or
pip install 'dspy>=3.0.3,<4.0.0'
```

**For Java-based reasoners (HermiT, Pellet, etc.):**
- JPype1 is automatically installed
- Java JRE/JDK 8+ must be installed on your system

## System Requirements

- **Python:** 3.11 or higher
- **Operating System:** Linux, macOS, Windows
- **Memory:** Minimum 4GB RAM (8GB+ recommended for large ontologies)
- **Java (optional):** JRE/JDK 8+ for HermiT, Pellet, JFact, ELK, Openllet reasoners

## Quick Start

### 1. Load an Ontology

```python
from owlapy.owl_ontology import SyncOntology

# Load from file
ontology = SyncOntology("path/to/ontology.owl")

# Or from URL
ontology = SyncOntology("http://example.com/ontology.owl")
```

### 2. Create a Reasoner

```python
from owlapy.owl_reasoner import RDFLibReasoner

# Pure Python reasoner (recommended for most use cases)
reasoner = RDFLibReasoner(ontology)
```

### 3. Query Instances

```python
from owlapy.class_expression import OWLClass

# Define a class
person_class = OWLClass("http://example.com/onto#Person")

# Get all instances
persons = list(reasoner.instances(person_class))
print(f"Found {len(persons)} persons")

for person in persons:
    print(f"  - {person.str}")
```

### 4. Build Class Expressions

```python
from owlapy.class_expression import (
    OWLClass,
    OWLObjectSomeValuesFrom,
    OWLObjectIntersectionOf
)
from owlapy.owl_property import OWLObjectProperty

# Create complex class expression:
# Parent ⊓ (∃ hasChild.Male)
parent_class = OWLClass("http://example.com/onto#Parent")
has_child_prop = OWLObjectProperty("http://example.com/onto#hasChild")
male_class = OWLClass("http://example.com/onto#Male")

parent_with_male_child = OWLObjectIntersectionOf([
    parent_class,
    OWLObjectSomeValuesFrom(has_child_prop, male_class)
])

# Query instances of complex expression
parents = list(reasoner.instances(parent_with_male_child))
print(f"Found {len(parents)} parents with male children")
```

### 5. Convert to Different Syntaxes

```python
from owlapy import owl_expression_to_dl, owl_expression_to_manchester

# Convert to Description Logic syntax
dl_syntax = owl_expression_to_dl(parent_with_male_child)
print(f"DL: {dl_syntax}")
# Output: Parent ⊓ (∃ hasChild.Male)

# Convert to Manchester syntax
manchester = owl_expression_to_manchester(parent_with_male_child)
print(f"Manchester: {manchester}")
# Output: Parent and (hasChild some Male)
```

## Complete Example: Family Ontology

```python
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner import RDFLibReasoner
from owlapy.class_expression import (
    OWLClass,
    OWLObjectSomeValuesFrom,
    OWLObjectIntersectionOf,
    OWLObjectUnionOf
)
from owlapy.owl_property import OWLObjectProperty
from owlapy import owl_expression_to_dl

# 1. Load ontology
onto = SyncOntology("family.owl")

# 2. Create reasoner
reasoner = RDFLibReasoner(onto)

# 3. Define namespace
NS = "http://example.com/family#"

# 4. Define classes and properties
person = OWLClass(NS + "Person")
male = OWLClass(NS + "Male")
female = OWLClass(NS + "Female")
has_child = OWLObjectProperty(NS + "hasChild")

# 5. Query simple classes
all_males = list(reasoner.instances(male))
print(f"Males: {[m.str.split('#')[-1] for m in all_males]}")

# 6. Build complex expression: parents with female children
# Parent ⊓ (∃ hasChild.Female)
parents_with_daughters = OWLObjectIntersectionOf([
    person,
    OWLObjectSomeValuesFrom(has_child, female)
])

# 7. Query complex expression
result = list(reasoner.instances(parents_with_daughters))
print(f"Parents with daughters: {[r.str.split('#')[-1] for r in result]}")
print(f"DL syntax: {owl_expression_to_dl(parents_with_daughters)}")

# 8. Get class hierarchy
all_subclasses = list(reasoner.sub_classes(person))
print(f"Subclasses of Person: {[c.str.split('#')[-1] for c in all_subclasses]}")
```

## Next Steps

- Learn about [core concepts](02_core_concepts.md) in owlapy
- Explore [ontology management](03_ontology_management.md)
- Master [class expressions](04_class_expressions.md)
- Dive into [reasoning](05_reasoning.md) capabilities
- Check [common patterns](08_common_patterns.md) for best practices

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'owlapy'`

**Solution:** 
```bash
pip install owlapy
# Or if installed from source:
pip install -e .
```

### Java Reasoner Errors

**Problem:** `JVMNotFoundException` when using SyncReasoner

**Solution:** Install Java JRE/JDK 8+ and ensure it's in your PATH

### Memory Issues

**Problem:** `MemoryError` when loading large ontologies

**Solution:** 
- Use RDFLibReasoner instead of StructuralReasoner (more memory efficient)
- Increase Python memory limit
- Load only necessary parts of the ontology

### IRI Errors

**Problem:** `ValueError: Invalid IRI`

**Solution:** Always use full IRI strings:
```python
# Correct
OWLClass("http://example.com/onto#Person")

# Incorrect
OWLClass("Person")  # Missing namespace
```
