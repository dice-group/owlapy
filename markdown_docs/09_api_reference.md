# API Reference

Quick reference for all major classes and functions in owlapy.

## Top-Level Functions

### Syntax Conversion

```python
from owlapy import (
    owl_expression_to_dl,
    owl_expression_to_manchester,
    owl_expression_to_sparql,
    dl_to_owl_expression,
    manchester_to_owl_expression
)
```

#### `owl_expression_to_dl(expression) -> str`
Convert OWL expression to Description Logic syntax.

```python
expr = OWLObjectSomeValuesFrom(has_child, male)
dl = owl_expression_to_dl(expr)  # "∃ hasChild.Male"
```

#### `owl_expression_to_manchester(expression) -> str`
Convert OWL expression to Manchester syntax.

```python
manchester = owl_expression_to_manchester(expr)  # "hasChild some Male"
```

#### `owl_expression_to_sparql(expression, Named_Individuals=None, count=False) -> str`
Convert OWL expression to SPARQL query.

```python
sparql = owl_expression_to_sparql(expr)
# SELECT DISTINCT ?x WHERE { ... }
```

#### `manchester_to_owl_expression(input_str, namespace=None) -> OWLClassExpression`
Parse Manchester syntax to OWL expression.

```python
expr = manchester_to_owl_expression(
    "Person and (hasChild some Male)",
    namespace="http://example.com/onto#"
)
```

#### `dl_to_owl_expression(input_str, namespace=None) -> OWLClassExpression`
Parse DL syntax to OWL expression.

```python
expr = dl_to_owl_expression(
    "Person ⊓ (∃ hasChild.Male)",
    namespace="http://example.com/onto#"
)
```

## Ontology Classes

### `SyncOntology` (Recommended)

```python
from owlapy.owl_ontology import SyncOntology
```

Thread-safe ontology implementation using owlready2.

**Constructor:**
```python
SyncOntology(path: str)
SyncOntology(iri: IRI)
```

**Key Methods:**
- `classes_in_signature() -> Iterable[OWLClass]` - Get all classes
- `individuals_in_signature() -> Iterable[OWLNamedIndividual]` - Get all individuals
- `object_properties_in_signature() -> Iterable[OWLObjectProperty]` - Get all object properties
- `data_properties_in_signature() -> Iterable[OWLDataProperty]` - Get all data properties
- `add_axiom(axiom: OWLAxiom)` - Add axiom to ontology
- `remove_axiom(axiom: OWLAxiom)` - Remove axiom
- `save(path: str, format: str = 'rdfxml')` - Save ontology

**Example:**
```python
onto = SyncOntology("family.owl")
classes = list(onto.classes_in_signature())
onto.add_axiom(OWLSubClassOfAxiom(student, person))
onto.save("updated_family.owl")
```

### `Ontology`

Alternative lightweight ontology implementation.

```python
from owlapy.owl_ontology import Ontology
onto = Ontology("family.owl")
```

### `NeuralOntology`

Ontology with neural network-backed reasoning.

```python
from owlapy.owl_ontology import NeuralOntology
onto = NeuralOntology("ontology.owl", "embeddings.pkl")
```

## Reasoner Classes

### `RDFLibReasoner` (Recommended)

```python
from owlapy.owl_reasoner import RDFLibReasoner
```

Pure Python reasoner using SPARQL queries. No circular dependencies, efficient caching.

**Constructor:**
```python
RDFLibReasoner(ontology: SyncOntology | Ontology)
```

**Key Methods:**
- `instances(ce: OWLClassExpression, direct: bool = False) -> Iterable[OWLNamedIndividual]`
- `sub_classes(ce: OWLClass, direct: bool = False) -> Iterable[OWLClass]`
- `super_classes(ce: OWLClass, direct: bool = False) -> Iterable[OWLClass]`
- `equivalent_classes(ce: OWLClass) -> Iterable[OWLClass]`
- `disjoint_classes(ce: OWLClass) -> Iterable[OWLClass]`
- `types(ind: OWLNamedIndividual, direct: bool = False) -> Iterable[OWLClass]`
- `object_property_values(ind: OWLNamedIndividual, prop: OWLObjectProperty) -> Iterable[OWLNamedIndividual]`
- `data_property_values(ind: OWLNamedIndividual, prop: OWLDataProperty) -> Iterable[OWLLiteral]`

**Example:**
```python
reasoner = RDFLibReasoner(onto)
males = list(reasoner.instances(OWLClass(NS + "Male")))
subclasses = list(reasoner.sub_classes(person, direct=True))
```

### `StructuralReasoner`

Fast Python reasoner using owlready2. **Warning:** Has circular dependency issue #205.

```python
from owlapy.owl_reasoner import StructuralReasoner
reasoner = StructuralReasoner(onto)
```

### `SyncReasoner`

Complete OWL 2 DL reasoner using Java (HermiT, Pellet, JFact, ELK, Openllet).

```python
from owlapy.owl_reasoner import SyncReasoner
from owlapy.static_funcs import startJVM, stopJVM

startJVM()
reasoner = SyncReasoner(onto, reasoner="HermiT")
# ... use reasoner ...
stopJVM()
```

**Additional Methods:**
- `has_consistent_ontology() -> bool` - Check consistency
- `is_entailed(axiom: OWLAxiom) -> bool` - Check entailment
- `get_root_ontology() -> Ontology` - Get underlying ontology with justification support

## Class Expressions

### Atomic Classes

```python
from owlapy.class_expression import OWLClass, OWLThing, OWLNothing
```

#### `OWLClass(iri: str)`
Named OWL class.

```python
person = OWLClass("http://example.com/onto#Person")
```

#### `OWLThing`
Top class (⊤) - contains everything.

```python
top = OWLThing
```

#### `OWLNothing`
Bottom class (⊥) - contains nothing.

```python
bottom = OWLNothing
```

### Boolean Combinations

```python
from owlapy.class_expression import (
    OWLObjectIntersectionOf,
    OWLObjectUnionOf,
    OWLObjectComplementOf
)
```

#### `OWLObjectIntersectionOf(operands: List[OWLClassExpression])`
Intersection (AND, ⊓).

```python
teacher_researcher = OWLObjectIntersectionOf([teacher, researcher])
```

#### `OWLObjectUnionOf(operands: List[OWLClassExpression])`
Union (OR, ⊔).

```python
student_or_employee = OWLObjectUnionOf([student, employee])
```

#### `OWLObjectComplementOf(operand: OWLClassExpression)`
Complement (NOT, ¬).

```python
not_male = OWLObjectComplementOf(male)
```

### Restrictions

```python
from owlapy.class_expression import (
    OWLObjectSomeValuesFrom,
    OWLObjectAllValuesFrom,
    OWLObjectHasValue
)
```

#### `OWLObjectSomeValuesFrom(property, filler)`
Existential quantification (∃).

```python
has_child = OWLObjectSomeValuesFrom(has_child_prop, male)  # ∃ hasChild.Male
```

#### `OWLObjectAllValuesFrom(property, filler)`
Universal quantification (∀).

```python
only_male_children = OWLObjectAllValuesFrom(has_child_prop, male)  # ∀ hasChild.Male
```

#### `OWLObjectHasValue(property, individual)`
Value restriction.

```python
johns_child = OWLObjectHasValue(has_parent_prop, john)  # ∃ hasParent.{John}
```

### Cardinality Restrictions

```python
from owlapy.class_expression import (
    OWLObjectMinCardinality,
    OWLObjectMaxCardinality,
    OWLObjectExactCardinality
)
```

#### `OWLObjectMinCardinality(cardinality: int, property, filler=None)`
Minimum cardinality (≥).

```python
at_least_two_children = OWLObjectMinCardinality(2, has_child_prop)  # ≥2 hasChild
```

#### `OWLObjectMaxCardinality(cardinality: int, property, filler=None)`
Maximum cardinality (≤).

```python
at_most_one_spouse = OWLObjectMaxCardinality(1, has_spouse_prop)  # ≤1 hasSpouse
```

#### `OWLObjectExactCardinality(cardinality: int, property, filler=None)`
Exact cardinality (=).

```python
exactly_three_sons = OWLObjectExactCardinality(3, has_child_prop, male)  # =3 hasChild.Male
```

### Nominals

```python
from owlapy.class_expression import OWLObjectOneOf
```

#### `OWLObjectOneOf(individuals: List[OWLNamedIndividual])`
Enumeration of individuals.

```python
specific_people = OWLObjectOneOf([john, mary, bob])  # {John, Mary, Bob}
```

### Data Restrictions

```python
from owlapy.class_expression import (
    OWLDataSomeValuesFrom,
    OWLDataAllValuesFrom,
    OWLDataHasValue,
    OWLDataMinCardinality,
    OWLDataMaxCardinality,
    OWLDataExactCardinality
)
```

Similar to object restrictions but for data properties.

## Properties

### Object Properties

```python
from owlapy.owl_property import OWLObjectProperty, OWLObjectInverseOf
```

#### `OWLObjectProperty(iri: str)`
Object property (relates individuals to individuals).

```python
has_parent = OWLObjectProperty("http://example.com/onto#hasParent")
```

#### `OWLObjectInverseOf(property: OWLObjectProperty)`
Inverse property.

```python
has_child = OWLObjectInverseOf(has_parent)  # hasChild ≡ hasParent⁻
```

### Data Properties

```python
from owlapy.owl_property import OWLDataProperty
```

#### `OWLDataProperty(iri: str)`
Data property (relates individuals to literals).

```python
has_age = OWLDataProperty("http://example.com/onto#hasAge")
```

## Individuals

```python
from owlapy.owl_individual import OWLNamedIndividual
```

#### `OWLNamedIndividual(iri: str)`
Named individual (instance).

```python
john = OWLNamedIndividual("http://example.com/onto#John")
```

## Literals

```python
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_datatype import (
    IntegerOWLDatatype,
    DoubleOWLDatatype,
    BooleanOWLDatatype,
    StringOWLDatatype,
    DateOWLDatatype,
    DateTimeOWLDatatype
)
```

#### `OWLLiteral(value, datatype=StringOWLDatatype)`
Literal value.

```python
age = OWLLiteral(25, IntegerOWLDatatype)
height = OWLLiteral(1.75, DoubleOWLDatatype)
name = OWLLiteral("John Doe", StringOWLDatatype)
is_student = OWLLiteral(True, BooleanOWLDatatype)
```

## Axioms

### Class Axioms

```python
from owlapy.owl_axiom import (
    OWLSubClassOfAxiom,
    OWLEquivalentClassesAxiom,
    OWLDisjointClassesAxiom,
    OWLDisjointUnionAxiom
)
```

#### `OWLSubClassOfAxiom(sub_class, super_class)`
Subclass axiom (⊑).

```python
axiom = OWLSubClassOfAxiom(student, person)  # Student ⊑ Person
```

#### `OWLEquivalentClassesAxiom(classes: List[OWLClassExpression])`
Equivalence axiom (≡).

```python
axiom = OWLEquivalentClassesAxiom([male, not_female])  # Male ≡ ¬Female
```

#### `OWLDisjointClassesAxiom(classes: List[OWLClassExpression])`
Disjointness axiom.

```python
axiom = OWLDisjointClassesAxiom([male, female])  # Male ⊥ Female
```

### Individual Axioms

```python
from owlapy.owl_axiom import (
    OWLClassAssertionAxiom,
    OWLObjectPropertyAssertionAxiom,
    OWLDataPropertyAssertionAxiom,
    OWLSameIndividualAxiom,
    OWLDifferentIndividualsAxiom
)
```

#### `OWLClassAssertionAxiom(individual, class_expression)`
Class membership.

```python
axiom = OWLClassAssertionAxiom(john, person)  # John : Person
```

#### `OWLObjectPropertyAssertionAxiom(subject, property, object)`
Object property assertion.

```python
axiom = OWLObjectPropertyAssertionAxiom(john, has_parent, mary)  # John hasParent Mary
```

#### `OWLDataPropertyAssertionAxiom(subject, property, value)`
Data property assertion.

```python
axiom = OWLDataPropertyAssertionAxiom(john, has_age, age_literal)  # John hasAge 25
```

### Property Axioms

```python
from owlapy.owl_axiom import (
    OWLSubObjectPropertyOfAxiom,
    OWLEquivalentObjectPropertiesAxiom,
    OWLInverseObjectPropertiesAxiom,
    OWLTransitiveObjectPropertyAxiom,
    OWLSymmetricObjectPropertyAxiom,
    OWLFunctionalObjectPropertyAxiom
)
```

## Utility Functions

### Static Functions

```python
from owlapy.util_owl_static_funcs import (
    create_ontology,
    csv_to_rdf_kg,
    save_owl_class_expressions
)
```

#### `create_ontology(iri: str) -> SyncOntology`
Create empty ontology.

```python
onto = create_ontology("http://example.com/my-ontology")
```

#### `csv_to_rdf_kg(csv_file, output_file, namespace, class_name, delimiter=',')`
Convert CSV to RDF knowledge graph.

```python
csv_to_rdf_kg(
    csv_file="data.csv",
    output_file="kg.owl",
    namespace="http://example.com/data#",
    class_name="DataPoint"
)
```

#### `save_owl_class_expressions(expressions: List, path: str, namespace: str)`
Save class expressions to OWL file.

```python
save_owl_class_expressions(
    expressions=[expr1, expr2, expr3],
    path="expressions.owl",
    namespace="http://example.com/onto#"
)
```

### JVM Management

```python
from owlapy.static_funcs import startJVM, stopJVM
```

#### `startJVM()`
Start Java Virtual Machine (required for SyncReasoner).

```python
startJVM()
```

#### `stopJVM()`
Stop Java Virtual Machine.

```python
stopJVM()
```

### Class Expression Utilities

```python
from owlapy.utils import CESimplifier, NNF
```

#### `CESimplifier`
Simplify complex class expressions.

```python
simplifier = CESimplifier()
simplified = simplifier.simplify(complex_expression)
```

#### `NNF`
Convert to Negation Normal Form.

```python
nnf = NNF()
normalized = nnf.get_nnf(expression)
```

### Similarity Metrics

```python
from owlapy.utils import jaccard_similarity, f1_set_similarity
```

#### `jaccard_similarity(set1, set2) -> float`
Compute Jaccard similarity.

```python
similarity = jaccard_similarity(instances1, instances2)
```

#### `f1_set_similarity(set1, set2) -> float`
Compute F1 similarity.

```python
similarity = f1_set_similarity(instances1, instances2)
```

## AGenKG (LLM-based Generation)

```python
from owlapy.agen_kg import AGenKG, DomainGraphExtractor, OpenGraphExtractor
```

### `AGenKG`

Generate ontologies from text using LLMs.

**Constructor:**
```python
AGenKG(
    model: str = "gpt-4o",
    api_key: str = None,
    api_base: str = "https://api.openai.com/v1"
)
```

**Methods:**
- `generate_ontology(text: str, ontology_type: str = "domain", save_path: str = None) -> SyncOntology`

**Example:**
```python
agent = AGenKG(
    model="gpt-4o",
    api_key="your-key",
    api_base="https://models.github.ai/inference"
)

ontology = agent.generate_ontology(
    text="path/to/document.txt",
    ontology_type="domain",
    save_path="generated_ontology.owl"
)
```

### `DomainGraphExtractor`

Extract domain-specific knowledge graph.

```python
extractor = DomainGraphExtractor(model="gpt-4o", api_key="key")
kg = extractor.extract(text="Medical records...")
```

### `OpenGraphExtractor`

Extract open-domain knowledge graph.

```python
extractor = OpenGraphExtractor(model="gpt-4o", api_key="key")
kg = extractor.extract(text="General text...")
```

## IRI

```python
from owlapy.iri import IRI
```

#### `IRI.create(iri_string: str) -> IRI`
Create IRI from string.

```python
iri = IRI.create("http://example.com/onto#Person")
```

#### `IRI(namespace: str, remainder: str) -> IRI`
Create IRI from namespace and name.

```python
iri = IRI("http://example.com/onto#", "Person")
```

**Methods:**
- `as_str() -> str` - Get full IRI string
- `get_namespace() -> str` - Get namespace
- `get_short_form() -> str` - Get local name

## SWRL (Semantic Web Rule Language)

```python
from owlapy.swrl import (
    Rule,
    ClassAtom,
    ObjectPropertyAtom,
    DataPropertyAtom,
    IVariable,
    DVariable
)
```

### Rule Construction

```python
# hasParent(?x, ?y) ∧ Male(?y) → hasFather(?x, ?y)
x = IVariable(IRI.create("urn:swrl:var#x"))
y = IVariable(IRI.create("urn:swrl:var#y"))

rule = Rule(
    body=[
        ObjectPropertyAtom(has_parent, x, y),
        ClassAtom(male, y)
    ],
    head=[
        ObjectPropertyAtom(has_father, x, y)
    ]
)
```

## Quick Import Reference

```python
# Ontology
from owlapy.owl_ontology import SyncOntology, Ontology, NeuralOntology

# Reasoners
from owlapy.owl_reasoner import RDFLibReasoner, StructuralReasoner, SyncReasoner

# Class Expressions
from owlapy.class_expression import (
    OWLClass, OWLThing, OWLNothing,
    OWLObjectIntersectionOf, OWLObjectUnionOf, OWLObjectComplementOf,
    OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom, OWLObjectHasValue,
    OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality,
    OWLObjectOneOf
)

# Properties
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty, OWLObjectInverseOf

# Individuals & Literals
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_datatype import IntegerOWLDatatype, DoubleOWLDatatype, StringOWLDatatype

# Axioms
from owlapy.owl_axiom import (
    OWLSubClassOfAxiom, OWLEquivalentClassesAxiom, OWLDisjointClassesAxiom,
    OWLClassAssertionAxiom, OWLObjectPropertyAssertionAxiom, OWLDataPropertyAssertionAxiom
)

# Syntax Conversion
from owlapy import (
    owl_expression_to_dl, owl_expression_to_manchester, owl_expression_to_sparql,
    manchester_to_owl_expression, dl_to_owl_expression
)

# Utilities
from owlapy.util_owl_static_funcs import create_ontology, csv_to_rdf_kg
from owlapy.static_funcs import startJVM, stopJVM
from owlapy.utils import CESimplifier, NNF

# IRI
from owlapy.iri import IRI

# AGenKG
from owlapy.agen_kg import AGenKG
```
