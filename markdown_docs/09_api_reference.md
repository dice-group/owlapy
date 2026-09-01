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

### `SyncOntology` (Recommended for full OWL 2 support)

```python
from owlapy.owl_ontology import SyncOntology
```

Thread-safe ontology implementation backed by the Java OWL API (requires the JVM via
`startJVM()`/`stopJVM()`).

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
- `save(path: str, document_format: str = None)` - Save ontology (keeps current format if `document_format` is omitted; see the format table in `03_ontology_management.md`)
- `get_dl_expressivity() -> str` - Compute the DL expressivity name of the ontology, e.g. `"ALCHN(D)"`
- `get_prefixes() -> Dict[str, str]` / `set_prefix(prefix: str, namespace: str)` / `remove_prefix(prefix: str)` - Manage prefix -> namespace IRI mappings used by `save()`

**Example:**
```python
onto = SyncOntology("family.owl")
classes = list(onto.classes_in_signature())
onto.add_axiom(OWLSubClassOfAxiom(student, person))
onto.save("updated_family.owl")
```

### `RDFLibOntology` (Recommended for pure-Python use)

```python
from owlapy.owl_ontology import RDFLibOntology
```

Pure Python ontology implementation backed by rdflib. No JVM, no owlready2 -- reads and writes
the RDF graph directly. Supports both loading an existing ontology and creating a blank one.

**Constructor:**
```python
RDFLibOntology(path: str)                       # load an existing ontology from a file
RDFLibOntology(iri: str | IRI, load=False)       # create a blank ontology with the given IRI
```

**Key Methods (read):**
- `classes_in_signature()` / `individuals_in_signature()` / `object_properties_in_signature()` / `data_properties_in_signature()` / `properties_in_signature()`
- `get_tbox_axioms() -> Iterable[OWLAxiom]` - Class declarations, `SubClassOf`, `EquivalentClasses`, `DisjointClasses` between named classes
- `get_abox_axioms() -> Iterable[OWLAxiom]` - Class assertions, object- and data-property assertions
- `get_abox_axioms_between_individuals()` / `get_abox_axioms_between_individuals_and_classes()` - Filtered subsets of the above
- `equivalent_classes_axioms(c: OWLClass) -> Iterable[OWLEquivalentClassesAxiom]`
- `data_property_domain_axioms(pe)` / `data_property_range_axioms(pe)` / `object_property_domain_axioms(pe)` / `object_property_range_axioms(pe)`
- `get_ontology_id() -> OWLOntologyID`

**Key Methods (write):**
- `add_axiom(axiom)` / `remove_axiom(axiom)` - Accepts a single `OWLAxiom` or an iterable. Supports declarations, class/object-property/data-property assertions, `SubClassOf`, `EquivalentClasses`, `DisjointClasses`, sub-property axioms, property domain/range axioms, and the property characteristic axioms (Functional/InverseFunctional/Symmetric/Asymmetric/Transitive/Reflexive/Irreflexive) -- all between/on *named* entities. Adding an axiom auto-declares any entity it references that isn't declared yet, so the axiom is immediately visible to the read API
- `save(path=None, inplace=False, document_format=None)` - Serializes via rdflib (`"rdfxml"` default; also accepts rdflib's own names and OWL-API-style aliases, same vocabulary as `Ontology`/`SyncOntology`)

**Limitation:** axioms involving complex (blank-node) class/property expressions -- e.g. general
class axioms, restriction-based domains/ranges -- aren't representable, on either the read or
write side; only axioms between named entities are. `general_class_axioms()` and
`add_axiom()`/`remove_axiom()` on such an axiom raise `NotImplementedError` to say so explicitly.
A handful of axiom types aren't supported by the write API yet either (e.g. `OWLSameIndividualAxiom`,
`OWLAnnotationAssertionAxiom`, `OWLDisjointUnionAxiom`) -- the error message names what is.

**Example:**
```python
onto = RDFLibOntology("family.owl")
classes = list(onto.classes_in_signature())
tbox = list(onto.get_tbox_axioms())
abox = list(onto.get_abox_axioms())

onto.add_axiom(OWLClassAssertionAxiom(OWLNamedIndividual("family#john"), OWLClass("family#Person")))
onto.save("family_updated.owl")
```

### `Ontology` (Legacy)

owlready2-backed ontology implementation. Being phased out in favor of `RDFLibOntology` (#205);
prefer `SyncOntology` or `RDFLibOntology` for new code. owlready2 is an optional install extra
(`pip install owlapy[owlready2]`) -- constructing an `Ontology` without it installed raises a
clear `ImportError` explaining how to install it.

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
from owlapy.owl_reasoner_rdflib import RDFLibReasoner
```

Pure Python reasoner using SPARQL queries. No circular dependencies, efficient caching.

**Constructor:**
```python
RDFLibReasoner(ontology: AbstractOWLOntology | str)  # accepts a path directly, e.g. RDFLibReasoner("family.owl")
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
- `is_entailed(axiom: OWLAxiom, timeout: int = 1000) -> bool` - Check entailment
- `get_root_ontology() -> AbstractOWLOntology` - Get the underlying ontology
- `create_axiom_justifications(axiom, n_max_justifications=10, timeout=1000, save=False) -> List[Set[OWLAxiom]]` - Explain why an axiom is entailed
- `create_laconic_axiom_justifications(axiom, ...) -> List[Set[OWLAxiom]]` - Same, but each justification is minimized/laconic
- `infer_axioms_and_save(output_path, output_format=None, inference_types=[...])` - Materialize inferred axioms (e.g. `["InferredClassAssertionAxiomGenerator"]`) and save them

### `EBR` (Embedding-Based Reasoner)

Neural, embedding-based reasoner: predicts class membership/relations from a pretrained knowledge
graph embedding model (via `dicee`) instead of applying DL semantics to asserted axioms. Not
DL-complete -- results are probabilistic, score-thresholded predictions. Useful for large, noisy,
or incomplete knowledge graphs. Requires the `dicee` package (`pip install dicee`).

```python
from owlapy.owl_ontology import NeuralOntology
from owlapy.owl_reasoner import EBR

neural_onto = NeuralOntology("path/to/pretrained_kge_model")
reasoner = EBR(ontology=neural_onto)
```

**Key Methods:**
- `instances(ce: OWLClassExpression) -> Iterable[OWLNamedIndividual]` - Predict instances of a (named) class, thresholded by `gamma` (default `0.5`)
- `predict(h=None, r=None, t=None) -> List[Tuple[str, float]]` - Raw `(head, relation, tail)` triple predictions with scores
- `sub_classes(ce)` / `super_classes(ce)` / `types(ind)` / `object_property_values(ind, prop)` / `data_property_domains(pe)` / `object_property_domains(pe)` / `object_property_ranges(pe)`

**Limitations:** no complex class expressions; `equivalent_classes()`, `disjoint_classes()`, `same_individuals()`, `different_individuals()`, `equivalent_object_properties()`, `equivalent_data_properties()`, `disjoint_object_properties()`, `disjoint_data_properties()`, and `data_property_values()` all raise `NotImplementedError`.

### `NIRReasoner` (Neural Instance Retrieval)

Scores complex class expressions with a pretrained NIR encoder against entity embeddings.
Named classes and TBox queries use a symbolic fallback. Requires `torch` and `transformers`.
Pretrained weights: https://files.dice-research.org/datasets/CNIR/trained_models.zip

```python
from owlapy.owl_ontology import Ontology
from owlapy.owl_reasoner import NIRReasoner

onto = Ontology("KGs/Family/family-benchmark_rich_background.owl")
reasoner = NIRReasoner(
    onto,
    model_path="trained_models/nir_pretrained_models/NIR_Transformer_family",
    embeddings_path="trained_models/embeddings/family/DeCaL_entity_embeddings.csv",
)
```

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

#### `OWLObjectMinCardinality(cardinality: int, property, filler)`
Minimum cardinality (≥). `filler` is required -- use `OWLThing` for "any".

```python
at_least_two_children = OWLObjectMinCardinality(2, has_child_prop, OWLThing)  # ≥2 hasChild.⊤
```

#### `OWLObjectMaxCardinality(cardinality: int, property, filler)`
Maximum cardinality (≤). `filler` is required -- use `OWLThing` for "any".

```python
at_most_one_spouse = OWLObjectMaxCardinality(1, has_spouse_prop, OWLThing)  # ≤1 hasSpouse.⊤
```

#### `OWLObjectExactCardinality(cardinality: int, property, filler)`
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

#### `OWLAnonymousIndividual(node_id: str = None)`
Blank-node individual, identified by a local node ID instead of an IRI. Generates a
fresh, unused node ID if none is given.

```python
from owlapy.owl_individual import OWLAnonymousIndividual

anon = OWLAnonymousIndividual()          # auto-generated node id
anon2 = OWLAnonymousIndividual("_:b0")   # explicit node id
```

## Literals

```python
from owlapy.owl_literal import (
    OWLLiteral,
    IntegerOWLDatatype,
    DoubleOWLDatatype,
    BooleanOWLDatatype,
    StringOWLDatatype,
    DateOWLDatatype,
    DateTimeOWLDatatype
)
```

#### `OWLLiteral(value, type_: OWLDatatype = None)`
Literal value. `type_` is inferred from `value`'s Python type if omitted.

```python
age = OWLLiteral(25, IntegerOWLDatatype)
height = OWLLiteral(1.75, DoubleOWLDatatype)
name = OWLLiteral("John Doe", StringOWLDatatype)
is_student = OWLLiteral(True, BooleanOWLDatatype)
```

## Axioms

Every `OWLAxiom` has a `.signature() -> Set[OWLEntity]` method returning the named
classes/object properties/data properties/individuals/datatypes it references (class
expressions and data ranges have the same method). Coverage is limited to declaration,
class/property assertions, sub-class-of, equivalent/disjoint classes, and property
domain/range axioms; other axiom types raise `NotImplementedError` (tracked in #231).

```python
axiom = OWLSubClassOfAxiom(student, person)
axiom.signature()  # {student, person}
```

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

#### `csv_to_rdf_kg(path_csv, path_kg, namespace)`
Convert CSV to RDF knowledge graph. Each row becomes an individual; each column becomes
a data property named after the column header, scoped under `namespace`.

```python
csv_to_rdf_kg(
    path_csv="data.csv",
    path_kg="kg.owl",
    namespace="http://example.com/data#",
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

Requires `dspy` (`pip install owlapy[agentic]`).

```python
from owlapy.agen_kg import AGenKG
```

### `AGenKG`

Generate ontologies from text using LLMs.

**Constructor:**
```python
AGenKG(
    model: str = "gpt-4o",
    api_key: str = "<YOUR_GITHUB_PAT>",
    api_base: str = "https://models.github.ai/inference",
    temperature: float = 0.1,
    seed: int = 42,
    cache: bool = False,
    enable_logging: bool = False,
    max_tokens: int = 4000,
)
```

Any OpenAI-compatible endpoint works (OpenAI, Azure OpenAI, GitHub Models, Ollama, vLLM) -- just swap `api_base`/`model`.

**Methods:**

- `generate_ontology(text, ontology_type: str = "domain", query=None, **kwargs) -> Ontology` -- `save_path` (must end in `.owl`) is a supported `**kwargs` entry

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

### `DomainGraphExtractor` / `OpenGraphExtractor`

Lower-level building blocks that `AGenKG` wraps internally (`ontology_type="domain"` vs
`"open"`) -- construct one directly only if you need to bypass `AGenKG`. They reuse
whichever LLM was last configured via `dspy.configure(lm=...)` (which `AGenKG.__init__`
does for you), rather than taking their own `model`/`api_key`.

```python
from owlapy.agen_kg.graph_extracting_models import DomainGraphExtractor, OpenGraphExtractor

AGenKG(model="gpt-4o", api_key="your-key")  # configures dspy's LM as a side effect

extractor = DomainGraphExtractor(enable_logging=True)
kg = extractor.generate_ontology(text="Medical records...", ontology_type="domain")
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
from owlapy.owl_reasoner_rdflib import RDFLibReasoner
from owlapy.owl_reasoner import StructuralReasoner, SyncReasoner

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
from owlapy.owl_literal import OWLLiteral, IntegerOWLDatatype, DoubleOWLDatatype, StringOWLDatatype

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
