# Core Concepts

## Overview

owlapy is built on the Web Ontology Language (OWL) 2 specification. Understanding these core concepts is essential for effective use of the framework.

## Key Concepts

### 1. Ontologies

An **ontology** is a formal representation of knowledge as a set of concepts and relationships. In OWL, an ontology consists of:

- **TBox (Terminological Box):** Class definitions and hierarchies
- **ABox (Assertional Box):** Individual instances and their property values
- **RBox (Role Box):** Property definitions and hierarchies

#### Ontology Classes in owlapy

```python
# SyncOntology - Recommended when you need full OWL 2 support / Java-backed reasoning
from owlapy.owl_ontology import SyncOntology
onto = SyncOntology("path/to/ontology.owl")

# RDFLibOntology - pure Python (rdflib-backed), no JVM or owlready2 dependency
from owlapy.owl_ontology import RDFLibOntology
onto = RDFLibOntology("path/to/ontology.owl")

# Ontology - owlready2-backed; legacy, being phased out in favor of RDFLibOntology (#205)
from owlapy.owl_ontology import Ontology
onto = Ontology("path/to/ontology.owl")

# NeuralOntology - For neural network-backed reasoning
from owlapy.owl_ontology import NeuralOntology
neural_onto = NeuralOntology("ontology.owl", "embeddings.pkl")
```

**Key differences:** `SyncOntology` is thread-safe and backed by the Java OWL API (requires the
JVM via `startJVM()`/`stopJVM()`, but gives complete OWL 2 support). `RDFLibOntology` is a
pure-Python, rdflib-backed alternative with no JVM or owlready2 dependency -- prefer it when you
don't need Java-backed reasoning; it supports both inspection (signature queries, TBox/ABox axiom
retrieval) and mutation (`add_axiom`/`remove_axiom`/`save`), limited to axioms between *named*
entities (no complex/blank-node class expressions). `Ontology` is the original owlready2-backed
implementation; treat it as legacy.

### 2. OWL Entities

#### Classes

Classes represent concepts in your domain.

```python
from owlapy.class_expression import OWLClass

# Always use full IRI
person = OWLClass("http://example.com/onto#Person")
student = OWLClass("http://example.com/onto#Student")
```

#### Individuals

Individuals are instances of classes.

```python
from owlapy.owl_individual import OWLNamedIndividual

john = OWLNamedIndividual("http://example.com/onto#John")
mary = OWLNamedIndividual("http://example.com/onto#Mary")
```

#### Properties

Properties define relationships between individuals.

```python
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty

# Object properties (relate individuals to individuals)
has_parent = OWLObjectProperty("http://example.com/onto#hasParent")
knows = OWLObjectProperty("http://example.com/onto#knows")

# Data properties (relate individuals to literal values)
has_age = OWLDataProperty("http://example.com/onto#hasAge")
has_name = OWLDataProperty("http://example.com/onto#hasName")
```

#### Literals

Literals are data values (strings, numbers, dates, etc.).

```python
from owlapy.owl_literal import OWLLiteral, IntegerOWLDatatype, DoubleOWLDatatype, StringOWLDatatype

age = OWLLiteral(25, IntegerOWLDatatype)
height = OWLLiteral(1.75, DoubleOWLDatatype)
name = OWLLiteral("John", StringOWLDatatype)
```

### 3. Class Expressions

Class expressions are complex class descriptions built from atomic classes and logical operators.

#### Atomic Classes

```python
from owlapy.class_expression import OWLClass, OWLThing, OWLNothing

# Named class
person = OWLClass("http://example.com/onto#Person")

# Top class (everything)
everything = OWLThing

# Bottom class (nothing)
nothing = OWLNothing
```

#### Boolean Combinations

```python
from owlapy.class_expression import (
    OWLObjectIntersectionOf,
    OWLObjectUnionOf,
    OWLObjectComplementOf
)

# Intersection (AND): Teacher ⊓ Researcher
teacher_researcher = OWLObjectIntersectionOf([teacher, researcher])

# Union (OR): Student ⊔ Employee
student_or_employee = OWLObjectUnionOf([student, employee])

# Complement (NOT): ¬Male
not_male = OWLObjectComplementOf(male)
```

#### Existential Restrictions

```python
from owlapy.class_expression import OWLObjectSomeValuesFrom

# ∃ hasChild.Male (has at least one male child)
has_male_child = OWLObjectSomeValuesFrom(has_child, male)

# ∃ hasParent.⊤ (has at least one parent)
has_parent = OWLObjectSomeValuesFrom(has_parent_prop, OWLThing)
```

#### Universal Restrictions

```python
from owlapy.class_expression import OWLObjectAllValuesFrom

# ∀ hasChild.Male (all children are male)
only_male_children = OWLObjectAllValuesFrom(has_child, male)
```

#### Cardinality Restrictions

```python
from owlapy.class_expression import (
    OWLObjectMinCardinality,
    OWLObjectMaxCardinality,
    OWLObjectExactCardinality
)

# ≥2 hasChild.⊤ (at least 2 children) -- filler is required, OWLThing for "any"
at_least_two_children = OWLObjectMinCardinality(2, has_child, OWLThing)

# ≤1 hasSpouse.⊤ (at most 1 spouse)
at_most_one_spouse = OWLObjectMaxCardinality(1, has_spouse, OWLThing)

# =3 hasChild.Male (exactly 3 male children)
exactly_three_sons = OWLObjectExactCardinality(3, has_child, male)
```

#### Value Restrictions

```python
from owlapy.class_expression import OWLObjectHasValue

# ∃ hasParent.{John} (has John as parent)
johns_child = OWLObjectHasValue(has_parent, john)
```

#### Nominals (Enumeration)

```python
from owlapy.class_expression import OWLObjectOneOf

# {John, Mary, Bob} (exactly these three individuals)
specific_people = OWLObjectOneOf([john, mary, bob])
```

### 4. Axioms

Axioms are statements that define the structure and constraints of your ontology.

#### Class Axioms

```python
from owlapy.owl_axiom import OWLSubClassOfAxiom, OWLEquivalentClassesAxiom

# Student ⊑ Person (Student is subclass of Person)
subclass_axiom = OWLSubClassOfAxiom(student, person)

# Male ≡ Person ⊓ ¬Female
male_definition = OWLEquivalentClassesAxiom([
    male,
    OWLObjectIntersectionOf([person, OWLObjectComplementOf(female)])
])
```

#### Individual Axioms

```python
from owlapy.owl_axiom import (
    OWLClassAssertionAxiom,
    OWLObjectPropertyAssertionAxiom,
    OWLDataPropertyAssertionAxiom
)

# John is a Person
class_assertion = OWLClassAssertionAxiom(john, person)

# John hasParent Mary
object_prop_assertion = OWLObjectPropertyAssertionAxiom(john, has_parent, mary)

# John hasAge 25
data_prop_assertion = OWLDataPropertyAssertionAxiom(john, has_age, age_literal)
```

#### Property Axioms

```python
from owlapy.owl_axiom import (
    OWLSubObjectPropertyOfAxiom,
    OWLInverseObjectPropertiesAxiom,
    OWLTransitiveObjectPropertyAxiom
)

# hasParent ⊑ hasAncestor
subproperty_axiom = OWLSubObjectPropertyOfAxiom(has_parent, has_ancestor)

# hasChild ≡ hasParent⁻
inverse_axiom = OWLInverseObjectPropertiesAxiom(has_child, has_parent)

# hasAncestor is transitive
transitive_axiom = OWLTransitiveObjectPropertyAxiom(has_ancestor)
```

### 5. Reasoners

Reasoners infer implicit knowledge from explicit axioms.

#### Types of Reasoners in owlapy

```python
# RDFLibReasoner (Recommended) - Pure Python, SPARQL-based, no circular deps, no owlready2/JVM
from owlapy.owl_reasoner_rdflib import RDFLibReasoner
reasoner = RDFLibReasoner(ontology)

# StructuralReasoner (Legacy) - Fast, incomplete, owlready2-based; being phased out (#205)
from owlapy.owl_reasoner import StructuralReasoner
reasoner = StructuralReasoner(ontology)

# SyncReasoner - Complete OWL 2 DL reasoning, Java-based
from owlapy.owl_reasoner import SyncReasoner
from owlapy.static_funcs import startJVM, stopJVM

startJVM()
reasoner = SyncReasoner(ontology, reasoner="HermiT")
# ... use reasoner ...
stopJVM()
```

#### Reasoner Capabilities

```python
# Instance retrieval
instances = list(reasoner.instances(person))

# Subclass queries
subclasses = list(reasoner.sub_classes(person))
superclasses = list(reasoner.super_classes(student))

# Property value queries
children = list(reasoner.object_property_values(john, has_child))
age_values = list(reasoner.data_property_values(john, has_age))

# Type queries
types = list(reasoner.types(john))
```

### 6. IRIs (Internationalized Resource Identifiers)

All OWL entities are identified by IRIs.

```python
from owlapy.iri import IRI

# Create IRI
person_iri = IRI("http://example.com/onto#", "Person")
# or
person_iri = IRI.create("http://example.com/onto#Person")

# Get IRI string
iri_string = person_iri.as_str()  # "http://example.com/onto#Person"

# Extract namespace and name
namespace = person_iri.get_namespace()  # "http://example.com/onto#"
name = person_iri.get_short_form()      # "Person"
```

**Best Practice:** Always use full IRI strings in owlapy constructors:

```python
# Correct
OWLClass("http://example.com/onto#Person")

# Incorrect
OWLClass("Person")  # Missing namespace
```

## OWL Profiles

owlapy supports different OWL 2 profiles with varying expressivity:

### OWL 2 DL (Description Logic)
- Full OWL 2 expressivity
- Decidable reasoning
- Supported by: SyncReasoner (HermiT, Pellet, JFact)

### OWL 2 EL (Existential Logic)
- Limited to existential quantification
- Polynomial-time reasoning
- Supported by: SyncReasoner (ELK)

### OWL 2 QL (Query Logic)
- Optimized for query answering
- Log-space reasoning
- Partially supported

### OWL 2 RL (Rule Logic)
- Rule-based reasoning
- Can be implemented with rules engines
- Partially supported

## Design Patterns

### Pattern 1: Defined Classes

```python
# Define "Parent" as anyone who has at least one child
parent_definition = OWLEquivalentClassesAxiom([
    parent,
    OWLObjectSomeValuesFrom(has_child, OWLThing)
])
ontology.add_axiom(parent_definition)
```

### Pattern 2: Disjoint Classes

```python
from owlapy.owl_axiom import OWLDisjointClassesAxiom

# Male and Female are disjoint
disjoint = OWLDisjointClassesAxiom([male, female])
ontology.add_axiom(disjoint)
```

### Pattern 3: Property Chains

```python
from owlapy.owl_axiom import OWLSubPropertyChainAxiom

# hasParent ∘ hasParent ⊑ hasGrandparent
chain = OWLSubPropertyChainAxiom([has_parent, has_parent], has_grandparent)
ontology.add_axiom(chain)
```

## Common Namespaces

```python
# Standard OWL namespaces
OWL = "http://www.w3.org/2002/07/owl#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
XSD = "http://www.w3.org/2001/XMLSchema#"

# Your custom namespace
NS = "http://example.com/myontology#"
```

## Next Steps

- Explore [ontology management](03_ontology_management.md)
- Master [class expressions](04_class_expressions.md)
- Learn about [reasoning](05_reasoning.md)
