# Reasoning in owlapy

## Overview

Reasoning is the process of inferring implicit knowledge from explicit axioms. owlapy provides five reasoner implementations, each with different trade-offs.

## Reasoner Comparison

| Reasoner | Implementation | Completeness | World Assumption | Speed | Dependencies | Use Case |
|----------|---------------|--------------|-------------------|-------|--------------|----------|
| **[RDFLibReasoner](#1-rdflibreasoner-recommended)** | Pure Python (SPARQL) | Structural | Closed-world by default (`negation_default` can opt into open-world handling of `OWLObjectComplementOf`) | Fast | rdflib only | Recommended: general purpose, no circular deps, no owlready2/JVM |
| **[StructuralReasoner](#2-structuralreasoner-legacy) (Legacy)** | Python (owlready2) | Structural | Closed-world | Very fast | owlready2 (optional extra) | Existing owlready2-based code only; being phased out (#205) |
| **[SyncReasoner](#3-syncreasoner-complete-owl-2-dl)** | Java (various) | Complete OWL 2 DL | Open-world (standard OWL DL semantics) | Slower | JPype1 + Java | Full reasoning, complex queries |
| **[EBR](#4-ebr-embedding-based-reasoner)** | Pure Python (neural embeddings via `dicee`) | Probabilistic, not DL-complete | N/A (statistical plausibility, not classical entailment) | Fast (batched inference) | dicee + PyTorch | Large/noisy/incomplete KGs where symbolic reasoning misses implicit facts |
| **[NIRReasoner](#5-nirreasoner-neural-instance-retrieval)** | Pure Python (pretrained NIR encoder) | Probabilistic instance retrieval | N/A (score-thresholded membership) | Fast (batched inference) | torch + transformers | Complex class expressions scored against entity embeddings; TBox stays symbolic |

⚠️ **Choosing between closed- and open-world semantics matters, not just speed.** If your
data is meant to be a complete description of the domain (e.g. a fixed test KG) and you want
fast, predictable "not asserted = false" behavior, use **RDFLibReasoner**. If your data is
known to be incomplete and you need sound entailment under the standard OWL 2 DL open-world
assumption (e.g. "not asserted doesn't mean false, it means unknown"), use **SyncReasoner**
with **HermiT**. `StructuralReasoner` is closed-world like `RDFLibReasoner` but is legacy,
owlready2-backed, and has known correctness issues (circular `sub_classes()`/`super_classes()`
dependency, punning-related crashes worked around in #236/#242) -- prefer `RDFLibReasoner` for
new closed-world code instead.

## 1. RDFLibReasoner (Recommended)

Pure Python reasoner using RDFLib and SPARQL queries. No circular dependencies, efficient caching.

### Basic Usage

```python
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner_rdflib import RDFLibReasoner
from owlapy.class_expression import OWLClass

# Load ontology
onto = SyncOntology("family.owl")

# Create reasoner
reasoner = RDFLibReasoner(onto)

# Query instances
male = OWLClass("http://example.com/family#Male")
males = list(reasoner.instances(male))
print(f"Found {len(males)} males")
```

### Features

✅ **No circular dependencies** between sub_classes() and super_classes()  
✅ **Efficient SPARQL queries** instead of iterating all classes  
✅ **Built-in caching** for 400x+ speedup on repeated queries  
✅ **Pure Python** - no Java required  
✅ **Drop-in replacement** for StructuralReasoner  

### Performance Tips

```python
# Caching is automatic
first_call = list(reasoner.instances(male))   # ~500ms
second_call = list(reasoner.instances(male))  # ~1ms (cached)

# Pre-warm cache for better performance
reasoner.instances(OWLClass("http://example.com/onto#Person"))
```

### Limitations

- Structural reasoning only (no complex inferencing)
- Does not perform consistency checking
- Does not compute property chains
- Best for instance retrieval and hierarchy navigation

## 2. StructuralReasoner (Legacy)

Fast Python reasoner using owlready2. **Legacy:** owlapy is moving away from its owlready2
dependency (#205); `RDFLibReasoner` is the actively-maintained pure-Python replacement and
should be preferred for new code. `StructuralReasoner` also has a known circular dependency
issue (#205) and is kept mainly for existing code that already depends on it. Constructing one
now emits a `DeprecationWarning`. owlready2 itself is an optional install extra as of #205
(`pip install owlapy[owlready2]`) -- constructing a `StructuralReasoner` without it installed
raises a clear `ImportError` explaining how to install it.

### Basic Usage

```python
from owlapy.owl_reasoner import StructuralReasoner

reasoner = StructuralReasoner(onto)
instances = list(reasoner.instances(male))
```

### Known Issues

⚠️ **Circular dependency:** `sub_classes()` calls `super_classes()` and vice versa  
⚠️ **Inefficient:** Iterates over all classes instead of using direct queries  
⚠️ **Possible duplicates:** May return duplicates in hierarchy traversal  

**Recommendation:** Use RDFLibReasoner instead for new code.

## 3. SyncReasoner (Complete OWL 2 DL)

Java-based reasoner with complete OWL 2 DL support. Requires JVM lifecycle management.

### Available Reasoners

- **HermiT** - Complete, handles complex DL, supports SWRL
- **Pellet** - Complete, good performance, supports SWRL
- **JFact** - Complete, fast for large TBoxes
- **ELK** - Incomplete (EL profile only), very fast
- **Openllet** - Fork of Pellet, actively maintained

### Basic Usage

```python
from owlapy.owl_reasoner import SyncReasoner
from owlapy.static_funcs import startJVM, stopJVM

# Start JVM (required before using any Java reasoner)
startJVM()

try:
    # Create reasoner
    reasoner = SyncReasoner(onto, reasoner="HermiT")
    
    # Use reasoner
    instances = list(reasoner.instances(male))
    
    # Check consistency
    is_consistent = reasoner.has_consistent_ontology()
    
finally:
    # Always stop JVM when done
    stopJVM()
```

`instances()` (and `is_entailed()`, `create_axiom_justifications()`) accept a `timeout`
in seconds (default 1000) and cooperatively cancel the underlying Java reasoning task if
it's exceeded, returning whatever partial results were already found rather than hanging:

```python
instances = list(reasoner.instances(male, timeout=30))
```

### Advanced Features

#### Consistency Checking

```python
startJVM()
reasoner = SyncReasoner(onto, "Pellet")

if reasoner.has_consistent_ontology():
    print("Ontology is consistent")
else:
    print("Ontology is inconsistent!")
    
stopJVM()
```

#### Infer and Save New Axioms

`infer_axioms_and_save()` is a method on `SyncReasoner` itself (not a standalone
function) -- it materializes inferred axioms via the OWL API's `InferredOntologyGenerator`
and saves them onto the reasoner's own ontology.

```python
startJVM()

reasoner = SyncReasoner("family.owl", reasoner="HermiT")

# Infer new class assertions and save to a new file
reasoner.infer_axioms_and_save(
    output_path="inferred_family.owl",
    output_format="rdfxml",
    inference_types=["InferredClassAssertionAxiomGenerator"],
)

stopJVM()
```

Other `inference_types` include `"InferredSubClassAxiomGenerator"`,
`"InferredDisjointClassesAxiomGenerator"`, `"InferredEquivalentClassAxiomGenerator"`, and
more -- see the method's docstring for the full list. A shortcut for the most common case:
`reasoner.generate_and_save_inferred_class_assertion_axioms(output="inferred.ttl")`.

#### Get Justifications (Why is this true?)

Justifications are generated directly on the reasoner via `create_axiom_justifications()`
(there is no `get_justifications()` on the ontology):

```python
from owlapy.owl_axiom import OWLSubClassOfAxiom

startJVM()
reasoner = SyncReasoner(onto, reasoner="HermiT")

# Why is Student a subclass of Person? (axiom must actually be entailed)
axiom = OWLSubClassOfAxiom(student, person)
justifications = reasoner.create_axiom_justifications(axiom, n_max_justifications=10)

for i, justification in enumerate(justifications, 1):
    print(f"Justification {i}:")
    for ax in justification:
        print(f"  - {ax}")

stopJVM()
```

`create_laconic_axiom_justifications()` has the same signature but returns minimized
("laconic") justifications. Both accept a `timeout` (seconds, default 1000) for
cooperative cancellation of long-running searches.

### Choosing a Java Reasoner

```python
# For general use
reasoner = SyncReasoner(onto, "HermiT")

# For better performance with large ontologies
reasoner = SyncReasoner(onto, "JFact")

# For SWRL rule support
reasoner = SyncReasoner(onto, "Pellet")

# For very large EL ontologies (incomplete)
reasoner = SyncReasoner(onto, "ELK")
```

## 4. EBR (Embedding-Based Reasoner)

Neural, embedding-based reasoner: instead of applying DL semantics to asserted axioms, it uses a
pretrained knowledge graph embedding model (via [`dicee`](https://github.com/dice-group/dice-embeddings))
to *predict* class membership and relations. Useful for large, noisy, or incomplete knowledge
graphs where symbolic reasoners (RDFLibReasoner/StructuralReasoner/SyncReasoner) either miss
implicit facts or are too slow.

Requires the `dicee` package (`pip install dicee`; not installed by any `owlapy` extra except
`owlapy[all]` -- `NeuralOntology` raises a clear `ImportError` naming the install command if it's
missing).

### Basic Usage

```python
from owlapy.owl_ontology import NeuralOntology
from owlapy.owl_reasoner import EBR
from owlapy.class_expression import OWLClass

# Load a pretrained KGE model (a directory with a `configuration.json`), or train a new one
neural_onto = NeuralOntology("path/to/pretrained_kge_model")
# ... or, to train from a knowledge graph if no pretrained model exists yet:
# neural_onto = NeuralOntology("family.owl", train_if_not_exists=True)

reasoner = EBR(ontology=neural_onto)

# Predict instances of a class via embedding similarity (score threshold = gamma, default 0.5)
male = OWLClass("http://example.com/family#Male")
predicted_males = list(reasoner.instances(male))

# Raw (head, relation, tail) triple predictions with scores
predictions = reasoner.predict(h=["http://example.com/family#john"], r=None, t=None)
```

### Limitations

- Structural navigation only (`sub_classes`/`super_classes`/`types`/property values); no
  equivalence, disjointness, same/different-individuals, or complex class expressions --
  `equivalent_classes()`, `disjoint_classes()`, `same_individuals()`, etc. raise
  `NotImplementedError`
- Prediction quality depends entirely on the underlying embedding model; results are
  probabilistic (score-thresholded by `gamma`), not logically entailed
- No `stopJVM()`/JVM lifecycle to manage (pure Python + `dicee`/PyTorch), but GPU/CPU device
  selection matters for performance -- see `NeuralOntology`'s `device` parameter

## 5. NIRReasoner (Neural Instance Retrieval)

Neural instance retriever for complex OWL class expressions. A pretrained NIR encoder
(Transformer, LSTM, GRU, or Composite, implemented in `owlapy.nir`) scores DL-syntax queries
against DeCaL (or any CSV) entity embeddings. Named / length-1 concepts and all TBox / role
queries go to a symbolic fallback (`StructuralReasoner` or `RDFLibReasoner`). Unlike `EBR`, it
does **not** use `NeuralOntology` / `dicee`.

Requires `torch` and `transformers` (`pip install torch transformers`; imported lazily).

Pretrained encoders and embeddings:

```shell
wget https://files.dice-research.org/datasets/CNIR/trained_models.zip -O ./trained_models.zip && unzip trained_models.zip
```

### Basic Usage

```python
from owlapy.owl_ontology import Ontology
from owlapy.owl_reasoner import NIRReasoner
from owlapy.class_expression import OWLClass, OWLObjectSomeValuesFrom
from owlapy.owl_property import OWLObjectProperty
from owlapy.iri import IRI

onto = Ontology("KGs/Family/family-benchmark_rich_background.owl")
reasoner = NIRReasoner(
    onto,
    model_path="trained_models/nir_pretrained_models/NIR_Transformer_family",
    embeddings_path="trained_models/embeddings/family/DeCaL_entity_embeddings.csv",
    th=0.5,
)

brother = OWLClass(IRI("http://www.benchmark.org/family#", "Brother"))
print(set(reasoner.instances(brother)))  # named class: symbolic fallback

has_sibling = OWLObjectProperty(IRI("http://www.benchmark.org/family#", "hasSibling"))
complex_ce = OWLObjectSomeValuesFrom(property=has_sibling, filler=brother)
print(set(reasoner.instances(complex_ce)))  # longer expression: NIR encoder
```

Architecture is read from the checkpoint `config.json` (`NIRTransformer`, `NIRLSTM`, `NIRGRU`,
`NIRComposite`). Composite also loads a sibling `*relation_embeddings.csv` when present.

### Limitations

- Results are score-thresholded (`th`, default 0.5), not DL-entailed
- Hierarchies and roles are always answered by the symbolic fallback
- Needs a matching pretrained encoder directory plus entity embeddings for the same KG

## Common Reasoning Tasks

### Instance Retrieval

```python
# Get all instances of a class
person = OWLClass("http://example.com/onto#Person")
persons = list(reasoner.instances(person))

# Get instances of complex expression
# Parent ⊓ (∃ hasChild.Male)
complex_expr = OWLObjectIntersectionOf([
    parent,
    OWLObjectSomeValuesFrom(has_child, male)
])
parents_of_males = list(reasoner.instances(complex_expr))
```

### Class Hierarchy Navigation

```python
# Get all subclasses (direct and indirect)
all_subs = list(reasoner.sub_classes(person))

# Get only direct subclasses
direct_subs = list(reasoner.sub_classes(person, direct=True))

# Get all superclasses
all_supers = list(reasoner.super_classes(student))

# Get only direct superclasses
direct_supers = list(reasoner.super_classes(student, direct=True))
```

### Type Retrieval

```python
# Get all types of an individual
john = OWLNamedIndividual("http://example.com/onto#John")
types = list(reasoner.types(john))

# Get only direct types
direct_types = list(reasoner.types(john, direct=True))
```

### Property Value Queries

```python
# Get object property values
has_child = OWLObjectProperty("http://example.com/onto#hasChild")
children = list(reasoner.object_property_values(john, has_child))

# Get data property values
has_age = OWLDataProperty("http://example.com/onto#hasAge")
ages = list(reasoner.data_property_values(john, has_age))
```

### Equivalence and Disjointness

```python
# equivalent_classes()/disjoint_classes() take a single class expression and return
# everything equivalent/disjoint to it -- check membership to answer "are X and Y ...?"
not_female = OWLObjectComplementOf(female)
are_equiv = male in reasoner.equivalent_classes(not_female)

are_disjoint = female in reasoner.disjoint_classes(male)
```

## Performance Optimization

### 1. Use Caching

RDFLibReasoner automatically caches results:

```python
reasoner = RDFLibReasoner(onto)

# First call: ~500ms (builds cache)
males1 = list(reasoner.instances(male))

# Second call: ~1ms (cached)
males2 = list(reasoner.instances(male))
```

### 2. Use Direct Queries

```python
# Faster: only direct subclasses
direct = list(reasoner.sub_classes(person, direct=True))

# Slower: all subclasses (recursive traversal)
all_subs = list(reasoner.sub_classes(person, direct=False))
```

### 3. Batch Queries

```python
classes_to_query = [person, student, teacher, employee]
results = {}

for cls in classes_to_query:
    results[cls] = list(reasoner.instances(cls))
```

### 4. Choose the Right Reasoner

```python
# For quick instance retrieval
reasoner = RDFLibReasoner(onto)  # Fastest

# For complex reasoning
startJVM()
reasoner = SyncReasoner(onto, "HermiT")  # Complete but slower
# ... use reasoner ...
stopJVM()
```

## Complete Examples

### Example 1: Family Reasoning

```python
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner_rdflib import RDFLibReasoner
from owlapy.class_expression import *
from owlapy.owl_property import OWLObjectProperty

# Load ontology
onto = SyncOntology("KGs/Family/family-benchmark_rich_background.owl")
reasoner = RDFLibReasoner(onto)

NS = "http://www.benchmark.org/family#"

# Define classes and properties
male = OWLClass(NS + "Male")
female = OWLClass(NS + "Female")
person = OWLClass(NS + "Person")
has_child = OWLObjectProperty(NS + "hasChild")

# Query 1: All males
males = list(reasoner.instances(male))
print(f"Males: {len(males)}")

# Query 2: Parents with daughters
# Person ⊓ (∃ hasChild.Female)
parents_with_daughters = OWLObjectIntersectionOf([
    person,
    OWLObjectSomeValuesFrom(has_child, female)
])
result = list(reasoner.instances(parents_with_daughters))
print(f"Parents with daughters: {len(result)}")

# Query 3: Class hierarchy
subclasses = list(reasoner.sub_classes(person))
print(f"Subclasses of Person: {[c.str.split('#')[-1] for c in subclasses]}")
```

### Example 2: Performance Comparison

```python
import time

# RDFLibReasoner (fast)
start = time.time()
reasoner_rdf = RDFLibReasoner(onto)
instances_rdf = list(reasoner_rdf.instances(male))
time_rdf = time.time() - start
print(f"RDFLibReasoner: {len(instances_rdf)} instances in {time_rdf:.3f}s")

# Cached query (very fast)
start = time.time()
instances_cached = list(reasoner_rdf.instances(male))
time_cached = time.time() - start
print(f"Cached: {len(instances_cached)} instances in {time_cached:.6f}s")
print(f"Speedup: {time_rdf / time_cached:.0f}x")
```

### Example 3: Complex Reasoning with HermiT

```python
from owlapy.static_funcs import startJVM, stopJVM
from owlapy.owl_axiom import OWLSubClassOfAxiom

startJVM()

try:
    # Create HermiT reasoner
    reasoner = SyncReasoner(onto, "HermiT")
    
    # Check consistency
    if not reasoner.has_consistent_ontology():
        print("Warning: Ontology is inconsistent!")
    
    # Infer new subclass relationships
    teacher = OWLClass(NS + "Teacher")
    researcher = OWLClass(NS + "Researcher")
    
    # Check if all teachers are researchers
    axiom = OWLSubClassOfAxiom(teacher, researcher)
    is_entailed = reasoner.is_entailed(axiom)
    print(f"Teacher ⊑ Researcher: {is_entailed}")
    
    # Get explanation
    if is_entailed:
        justifications = reasoner.get_root_ontology().get_justifications(axiom)
        print(f"Found {len(justifications)} justifications")
        
finally:
    stopJVM()
```

## Troubleshooting

### Issue: JVM Already Started

**Error:** `JPypeException: JVM already started`

**Solution:**
```python
from owlapy.static_funcs import stopJVM, startJVM

# Stop existing JVM
stopJVM()

# Start fresh
startJVM()
```

### Issue: No Instances Found

**Problem:** `reasoner.instances(cls)` returns empty list

**Checklist:**
1. Verify IRI is correct (full namespace + name)
2. Check that individuals exist in ontology
3. Ensure class is not empty
4. For SyncReasoner, verify ontology is consistent

```python
# Debug: print all classes
all_classes = list(onto.classes_in_signature())
print(f"Classes: {[c.str for c in all_classes]}")

# Debug: print all individuals
all_individuals = list(onto.individuals_in_signature())
print(f"Individuals: {[i.str for i in all_individuals]}")
```

### Issue: Slow Performance

**Solutions:**
1. Use RDFLibReasoner instead of StructuralReasoner
2. Use `direct=True` when you only need direct results
3. Pre-warm cache with common queries
4. Consider NeuralOntology for very large ontologies

```python
# Pre-warm cache
reasoner = RDFLibReasoner(onto)
reasoner.instances(OWLClass(NS + "Person"))  # Builds cache
```

## Next Steps

- Learn about [syntax conversion](06_syntax_conversion.md)
- Explore [common patterns](08_common_patterns.md)
- Check [API reference](09_api_reference.md)
