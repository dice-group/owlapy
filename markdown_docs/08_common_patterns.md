# Common Patterns and Best Practices

## Ontology Loading and Management

### Pattern: Load Ontology Safely

```python
from owlapy.owl_ontology import SyncOntology
import os

def load_ontology_safe(path: str):
    """Load ontology with error handling."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Ontology not found: {path}")
    
    try:
        onto = SyncOntology(path)
        print(f"Loaded {len(list(onto.classes_in_signature()))} classes")
        return onto
    except Exception as e:
        raise RuntimeError(f"Failed to load ontology: {e}")

# Usage
onto = load_ontology_safe("family.owl")
```

### Pattern: Create Ontology from Scratch

```python
from owlapy.owl_ontology import SyncOntology
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLSubClassOfAxiom, OWLClassAssertionAxiom
from owlapy.class_expression import OWLClass
from owlapy.owl_individual import OWLNamedIndividual

# Create empty ontology
onto_iri = IRI.create("http://example.com/my-ontology")
onto = SyncOntology(onto_iri)

# Define namespace
NS = "http://example.com/my-ontology#"

# Add classes
person = OWLClass(NS + "Person")
student = OWLClass(NS + "Student")

# Add subclass axiom: Student ⊑ Person
onto.add_axiom(OWLSubClassOfAxiom(student, person))

# Add individual
john = OWLNamedIndividual(NS + "John")
onto.add_axiom(OWLClassAssertionAxiom(john, student))

# Save
onto.save("my-ontology.owl")
```

### Pattern: Bulk Add Axioms

```python
from owlapy.owl_axiom import OWLClassAssertionAxiom

individuals = [
    OWLNamedIndividual(NS + "John"),
    OWLNamedIndividual(NS + "Mary"),
    OWLNamedIndividual(NS + "Bob"),
]

# Add all individuals as instances of Person
axioms = [OWLClassAssertionAxiom(ind, person) for ind in individuals]
for axiom in axioms:
    onto.add_axiom(axiom)
```

## Class Expression Construction

### Pattern: Build Complex Expressions

```python
from owlapy.class_expression import *
from owlapy.owl_property import OWLObjectProperty

NS = "http://example.com/onto#"

# Helper function for namespace
def cls(name: str) -> OWLClass:
    return OWLClass(NS + name)

def prop(name: str) -> OWLObjectProperty:
    return OWLObjectProperty(NS + name)

# Build: Teacher ⊓ (∃ teaches.Graduate) ⊓ (≥2 hasPublication)
expression = OWLObjectIntersectionOf([
    cls("Teacher"),
    OWLObjectSomeValuesFrom(prop("teaches"), cls("Graduate")),
    OWLObjectMinCardinality(2, prop("hasPublication"))
])
```

### Pattern: Expression Builder Class

```python
class ExpressionBuilder:
    """Fluent API for building class expressions."""
    
    def __init__(self, namespace: str):
        self.ns = namespace
        self._expr = None
    
    def cls(self, name: str) -> 'ExpressionBuilder':
        self._expr = OWLClass(self.ns + name)
        return self
    
    def and_(self, *exprs) -> 'ExpressionBuilder':
        all_exprs = [self._expr] + list(exprs)
        self._expr = OWLObjectIntersectionOf(all_exprs)
        return self
    
    def or_(self, *exprs) -> 'ExpressionBuilder':
        all_exprs = [self._expr] + list(exprs)
        self._expr = OWLObjectUnionOf(all_exprs)
        return self
    
    def not_(self) -> 'ExpressionBuilder':
        self._expr = OWLObjectComplementOf(self._expr)
        return self
    
    def some(self, prop_name: str, filler) -> 'ExpressionBuilder':
        prop = OWLObjectProperty(self.ns + prop_name)
        if isinstance(filler, str):
            filler = OWLClass(self.ns + filler)
        self._expr = OWLObjectSomeValuesFrom(prop, filler)
        return self
    
    def build(self):
        return self._expr

# Usage
builder = ExpressionBuilder("http://example.com/onto#")
expr = builder.cls("Teacher").and_(
    builder.some("teaches", "Graduate").build()
).build()
```

### Pattern: Simplify Complex Expressions

```python
from owlapy.utils import CESimplifier

# Complex expression with redundancies
complex_expr = OWLObjectIntersectionOf([
    person,
    person,  # duplicate
    OWLObjectUnionOf([person, OWLThing]),  # person ⊔ ⊤ = ⊤
])

# Simplify
simplifier = CESimplifier()
simplified = simplifier.simplify(complex_expr)
```

## Reasoning Patterns

### Pattern: Reasoner Factory

```python
from owlapy.owl_reasoner import RDFLibReasoner, StructuralReasoner, SyncReasoner
from owlapy.static_funcs import startJVM, stopJVM

class ReasonerFactory:
    """Factory for creating reasoners with proper lifecycle."""
    
    @staticmethod
    def create(onto, reasoner_type="rdflib", **kwargs):
        """Create reasoner of specified type."""
        if reasoner_type == "rdflib":
            return RDFLibReasoner(onto)
        
        elif reasoner_type == "structural":
            return StructuralReasoner(onto)
        
        elif reasoner_type in ["hermit", "pellet", "jfact", "elk", "openllet"]:
            startJVM()
            return SyncReasoner(onto, reasoner=reasoner_type.capitalize())
        
        else:
            raise ValueError(f"Unknown reasoner type: {reasoner_type}")
    
    @staticmethod
    def cleanup(reasoner_type: str):
        """Clean up resources."""
        if reasoner_type in ["hermit", "pellet", "jfact", "elk", "openllet"]:
            stopJVM()

# Usage
reasoner = ReasonerFactory.create(onto, "rdflib")
instances = list(reasoner.instances(person))
# No cleanup needed for RDFLibReasoner

# Or with Java reasoner
reasoner = ReasonerFactory.create(onto, "hermit")
instances = list(reasoner.instances(person))
ReasonerFactory.cleanup("hermit")
```

### Pattern: Query with Timeout

```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds):
    """Context manager for timeout."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds}s")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

# Usage
try:
    with timeout(10):
        instances = list(reasoner.instances(complex_expression))
        print(f"Found {len(instances)} instances")
except TimeoutError:
    print("Query timed out, expression may be too complex")
```

### Pattern: Cache Results

```python
from functools import lru_cache

class CachedReasoner:
    """Wrapper with LRU caching."""
    
    def __init__(self, reasoner):
        self.reasoner = reasoner
    
    @lru_cache(maxsize=1000)
    def instances(self, class_expr: OWLClass):
        """Cached instance retrieval."""
        # Convert to tuple for hashability
        return tuple(self.reasoner.instances(class_expr))
    
    def clear_cache(self):
        """Clear all caches."""
        self.instances.cache_clear()

# Usage
cached = CachedReasoner(reasoner)
instances1 = cached.instances(person)  # Computed
instances2 = cached.instances(person)  # Cached
```

## Syntax Conversion Patterns

### Pattern: Convert and Display

```python
from owlapy import (
    owl_expression_to_dl,
    owl_expression_to_manchester,
    owl_expression_to_sparql
)

def display_expression(expr, show_sparql=False):
    """Display expression in multiple formats."""
    print("DL Syntax:", owl_expression_to_dl(expr))
    print("Manchester:", owl_expression_to_manchester(expr))
    if show_sparql:
        print("SPARQL:\n", owl_expression_to_sparql(expr))

# Usage
expr = OWLObjectIntersectionOf([
    person,
    OWLObjectSomeValuesFrom(has_child, male)
])
display_expression(expr, show_sparql=True)
```

### Pattern: Parse User Input

```python
from owlapy import manchester_to_owl_expression, dl_to_owl_expression

def parse_expression(input_str: str, namespace: str, syntax="manchester"):
    """Parse user input to OWL expression."""
    try:
        if syntax == "manchester":
            return manchester_to_owl_expression(input_str, namespace)
        elif syntax == "dl":
            return dl_to_owl_expression(input_str, namespace)
        else:
            raise ValueError(f"Unknown syntax: {syntax}")
    except Exception as e:
        print(f"Parse error: {e}")
        return None

# Usage
user_input = "Person and (hasChild some Male)"
expr = parse_expression(user_input, "http://example.com/onto#")
```

## Data Integration Patterns

### Pattern: CSV to RDF Knowledge Graph

```python
from owlapy.util_owl_static_funcs import csv_to_rdf_kg

# Convert CSV to RDF
csv_to_rdf_kg(
    csv_file="data.csv",
    output_file="knowledge_graph.owl",
    namespace="http://example.com/data#",
    class_name="DataPoint",
    delimiter=","
)
```

### Pattern: Add Individuals from Dictionary

```python
from owlapy.owl_axiom import (
    OWLClassAssertionAxiom,
    OWLObjectPropertyAssertionAxiom,
    OWLDataPropertyAssertionAxiom
)
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_datatype import IntegerOWLDatatype

def add_individual_from_dict(onto, ind_data: dict, namespace: str):
    """Add individual with properties from dictionary."""
    # Create individual
    ind = OWLNamedIndividual(namespace + ind_data["id"])
    
    # Add class assertion
    cls = OWLClass(namespace + ind_data["type"])
    onto.add_axiom(OWLClassAssertionAxiom(ind, cls))
    
    # Add object properties
    for prop_name, target_id in ind_data.get("object_props", {}).items():
        prop = OWLObjectProperty(namespace + prop_name)
        target = OWLNamedIndividual(namespace + target_id)
        onto.add_axiom(OWLObjectPropertyAssertionAxiom(ind, prop, target))
    
    # Add data properties
    for prop_name, value in ind_data.get("data_props", {}).items():
        prop = OWLDataProperty(namespace + prop_name)
        if isinstance(value, int):
            literal = OWLLiteral(value, IntegerOWLDatatype)
        else:
            literal = OWLLiteral(str(value))
        onto.add_axiom(OWLDataPropertyAssertionAxiom(ind, prop, literal))

# Usage
person_data = {
    "id": "John",
    "type": "Person",
    "object_props": {"hasParent": "Mary"},
    "data_props": {"age": 25, "name": "John Doe"}
}
add_individual_from_dict(onto, person_data, NS)
```

## Performance Patterns

### Pattern: Batch Instance Retrieval

```python
def batch_retrieve_instances(reasoner, classes: list):
    """Retrieve instances for multiple classes efficiently."""
    results = {}
    for cls in classes:
        results[cls.str] = list(reasoner.instances(cls))
    return results

# Usage
classes = [person, student, teacher, employee]
all_instances = batch_retrieve_instances(reasoner, classes)

for cls_iri, instances in all_instances.items():
    print(f"{cls_iri.split('#')[-1]}: {len(instances)} instances")
```

### Pattern: Progressive Loading

```python
def load_ontology_progressive(path: str, max_axioms=None):
    """Load ontology with progress reporting."""
    print("Loading ontology...")
    onto = SyncOntology(path)
    
    classes = list(onto.classes_in_signature())
    individuals = list(onto.individuals_in_signature())
    properties = list(onto.object_properties_in_signature())
    
    print(f"Loaded: {len(classes)} classes, {len(individuals)} individuals")
    print(f"        {len(properties)} properties")
    
    return onto
```

## Error Handling Patterns

### Pattern: Robust Reasoner Usage

```python
def safe_reason(onto, expr, reasoner_type="rdflib"):
    """Perform reasoning with comprehensive error handling."""
    reasoner = None
    try:
        # Create reasoner
        reasoner = ReasonerFactory.create(onto, reasoner_type)
        
        # Query instances
        instances = list(reasoner.instances(expr))
        
        return instances
    
    except TimeoutError:
        print("Reasoning timed out")
        return []
    
    except Exception as e:
        print(f"Reasoning error: {e}")
        return []
    
    finally:
        # Cleanup
        if reasoner_type in ["hermit", "pellet", "jfact", "elk"]:
            ReasonerFactory.cleanup(reasoner_type)
```

### Pattern: Validate IRI

```python
def validate_iri(iri_str: str) -> bool:
    """Validate IRI format."""
    from owlapy.iri import IRI
    try:
        IRI.create(iri_str)
        return True
    except:
        return False

def safe_create_class(iri_str: str):
    """Create OWL class with validation."""
    if not validate_iri(iri_str):
        raise ValueError(f"Invalid IRI: {iri_str}")
    return OWLClass(iri_str)
```

## Anti-Patterns (What NOT to Do)

### ❌ Anti-Pattern: Using String Names Instead of IRIs

```python
# WRONG
person = OWLClass("Person")  # Missing namespace!

# CORRECT
person = OWLClass("http://example.com/onto#Person")
```

### ❌ Anti-Pattern: Not Stopping JVM

```python
# WRONG
from owlapy.static_funcs import startJVM
from owlapy.owl_reasoner import SyncReasoner

startJVM()
reasoner = SyncReasoner(onto, "HermiT")
instances = list(reasoner.instances(person))
# JVM left running! Memory leak!

# CORRECT
from owlapy.static_funcs import startJVM, stopJVM

startJVM()
try:
    reasoner = SyncReasoner(onto, "HermiT")
    instances = list(reasoner.instances(person))
finally:
    stopJVM()
```

### ❌ Anti-Pattern: Not Caching Repeated Queries

```python
# WRONG - repeated queries without caching
for i in range(100):
    instances = list(reasoner.instances(person))  # Recomputed each time!

# CORRECT - cache result
instances = list(reasoner.instances(person))
for i in range(100):
    # Use cached result
    process(instances)
```

### ❌ Anti-Pattern: Building Expressions Inefficiently

```python
# WRONG - verbose and error-prone
expr = OWLObjectIntersectionOf([
    OWLClass("http://example.com/onto#Teacher"),
    OWLObjectSomeValuesFrom(
        OWLObjectProperty("http://example.com/onto#teaches"),
        OWLClass("http://example.com/onto#Graduate")
    )
])

# CORRECT - use helper functions
NS = "http://example.com/onto#"

def cls(name): return OWLClass(NS + name)
def prop(name): return OWLObjectProperty(NS + name)

expr = OWLObjectIntersectionOf([
    cls("Teacher"),
    OWLObjectSomeValuesFrom(prop("teaches"), cls("Graduate"))
])
```

### ❌ Anti-Pattern: Ignoring Errors

```python
# WRONG
try:
    onto = SyncOntology("ontology.owl")
except:
    pass  # Silent failure!

# CORRECT
try:
    onto = SyncOntology("ontology.owl")
except FileNotFoundError:
    print("Ontology file not found")
    raise
except Exception as e:
    print(f"Failed to load ontology: {e}")
    raise
```

## Best Practices Summary

### ✅ DO:
- Always use full IRIs for OWL entities
- Stop JVM when done with Java reasoners
- Cache results of expensive queries
- Use RDFLibReasoner for general-purpose reasoning
- Validate inputs and handle errors
- Use helper functions for namespace management
- Profile code to identify bottlenecks

### ❌ DON'T:
- Use bare class names without namespaces
- Leave JVM running after reasoning
- Repeat expensive queries without caching
- Ignore parse/reasoning errors
- Use StructuralReasoner for new code (circular dependency issue #205)
- Build complex expressions inline without helpers

## Next Steps

- Review [API reference](09_api_reference.md)
- Check [migration guide](10_migration_guide.md)
- Explore [examples directory](../../examples/) for more patterns
