# OWLAPY
[![Downloads](https://static.pepy.tech/badge/owlapy)](https://pepy.tech/project/owlapy)
[![Downloads](https://img.shields.io/pypi/dm/owlapy)](https://pypi.org/project/owlapy/)
[![Coverage](https://img.shields.io/badge/coverage-88%25-green)](https://dice-group.github.io/owlapy/usage/further_resources.html#coverage-report)
[![Pypi](https://img.shields.io/badge/pypi-1.6.6-blue)](https://pypi.org/project/owlapy/1.6.6/)
[![Docs](https://img.shields.io/badge/documentation-1.6.6-yellow)](https://dice-group.github.io/owlapy/usage/main.html)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/dice-group/owlapy)
![GitHub License](https://img.shields.io/github/license/dice-group/owlapy)


![OWLAPY](docs/_static/images/owlapy_logo.png)

**The Python Framework for Modern Ontology Engineering and Knowledge Graph Development**

OWLAPY brings the power of OWL ontologies to Python's rich data science and AI ecosystem. Built for researchers, data scientists, and knowledge engineers who want to leverage semantic web technologies without leaving Python.

## 🚀 Why OWLAPY?

### Native Python Integration

- **Pythonic API**: Work with ontologies using intuitive Python syntax, not verbose Java-style code
- **Perfect for Machine Learning**: Atomic structure makes it easy to integrate with ML pipelines and data science workflows
- **LLM-Powered Knowledge Extraction**: Fully automatic, scalable, agentic ontology (KG) generation from unstructured text using
LLMs

### Production-Ready Reasoning

- **Python-native Reasoners**: [RDFLibReasoner](markdown_docs/05_reasoning.md#1-rdflibreasoner-recommended) (recommended, pure Python, no JVM/owlready2), [Structural Reasoner](markdown_docs/05_reasoning.md#2-structuralreasoner-legacy) (legacy), and an [Embedding-Based Reasoner](markdown_docs/05_reasoning.md#4-ebr-embedding-based-reasoner) for neural knowledge graph completion
- **Optimized Performance**: Benchmarked across complex ontologies (see our [performance data](#reasoners-runtime-benchmark))
- **Synchronization with Java Reasoners**: [HermiT, Pellet, JFact, Openllet, ELK, and Structural](markdown_docs/05_reasoning.md#3-syncreasoner-complete-owl-2-dl)

### Cutting-Edge Features

- 🆕 **Automated Ontology Generation**: Extract knowledge graphs from text using LLMs with zero manual annotation through our 
    agentic pipeline AGen-KG (scalable to large documents).
- **Class Expression Simplification**: Automatically simplify complex logical expressions
- **Syntax Conversion**: Convert between Manchester, DL, and SPARQL syntaxes effortlessly


### Other Functionalities

- **Synchronization with OWLAPI**: Access to [OWLAPI](https://github.com/owlcs/owlapi)'s features via a Pythonic interface
- **Support for SWRL Rules**: Create and manipulate SWRL rules in Python

### Research-Backed

OWLAPY is actively developed by the DICE research group of Paderborn University. 
Our framework powers cutting-edge research in knowledge graph engineering, concept learning, and semantic reasoning.

[Documentation](https://dice-group.github.io/owlapy/usage/main.html) | [DeepWiki Assistant](https://deepwiki.com/dice-group/owlapy)

### 🎯 What Can You Build?

- **Knowledge Graph Pipelines**: Transform raw data into rich, queryable knowledge graphs
- **AI-Enhanced Ontologies**: Leverage LLMs to extract structured knowledge from documents
- **Semantic Search Systems**: Build intelligent search with logical reasoning
- **Data Integration**: Unify heterogeneous data sources with formal semantics
- **Explainable AI**: Add logical reasoning and justifications to ML pipelines

## Installation

### ⚡ Quick Start using PyPI
```bash
pip3 install owlapy
```

### 🌱 Installation from Source
``` bash
git clone https://github.com/dice-group/owlapy && cd owlapy

conda create -n temp_owlapy python=3.11 --no-default-packages && conda activate temp_owlapy && pip install -e '.[dev]'
```

#### Extra Files (optional)

```shell
# Download RDF knowledge graphs
wget https://files.dice-research.org/projects/Ontolearn/KGs.zip -O ./KGs.zip && unzip KGs.zip

# Test with pytest
PYTHONPATH=. pytest
```

## 📚 Documentation

### LLM-Friendly Documentation

For comprehensive, LLM-optimized documentation, check out the [`markdown_docs/`](markdown_docs/) directory:

- **[Getting Started](markdown_docs/01_getting_started.md)** - Installation, setup, and quick start guide
- **[Core Concepts](markdown_docs/02_core_concepts.md)** - OWL fundamentals, ontologies, reasoners, and class expressions
- **[Ontology Management](markdown_docs/03_ontology_management.md)** - Creating, loading, saving, and modifying ontologies
- **[Reasoning](markdown_docs/05_reasoning.md)** - Complete guide to RDFLibReasoner, StructuralReasoner, SyncReasoner, and the Embedding-Based Reasoner (EBR)
- **[Common Patterns](markdown_docs/08_common_patterns.md)** - Best practices, patterns, and anti-patterns
- **[API Reference](markdown_docs/09_api_reference.md)** - Complete API documentation

These docs are specifically formatted for LLM consumption and provide detailed examples, type information, and troubleshooting guidance.

### Official Documentation

- **[Online Documentation](https://dice-group.github.io/owlapy/usage/main.html)** - Complete API reference and tutorials
- **[DeepWiki Assistant](https://deepwiki.com/dice-group/owlapy)** - AI-powered documentation assistant

## 📋 Examples

### Exploring OWL Ontology

<details><summary> Click me! </summary>

```python
from owlapy.owl_ontology import SyncOntology

ontology_path = "KGs/Family/father.owl"
onto = SyncOntology(ontology_path)

print({owl_class.remainder for owl_class in onto.classes_in_signature()}) 
# {'Thing', 'female', 'male', 'person'}

print({individual.remainder for individual in onto.individuals_in_signature()}) 
# {'michelle', 'stefan', 'martin', 'anna', 'heinz', 'markus'}

print({object_property.remainder for object_property in onto.object_properties_in_signature()})
# {'hasChild'}

for owl_subclass_of_axiom in onto.get_tbox_axioms():
    print(owl_subclass_of_axiom)

# OWLEquivalentClassesAxiom([OWLClass(IRI('http://example.com/father#', 'male')), OWLObjectComplementOf(OWLClass(IRI('http://example.com/father#', 'female')))],[])
# OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://example.com/father#', 'female')),super_class=OWLClass(IRI('http://example.com/father#', 'person')),annotations=[])
# OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://example.com/father#', 'male')),super_class=OWLClass(IRI('http://example.com/father#', 'person')),annotations=[])
# OWLSubClassOfAxiom(sub_class=OWLClass(IRI('http://example.com/father#', 'person')),super_class=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')),annotations=[])
# OWLObjectPropertyRangeAxiom(OWLObjectProperty(IRI('http://example.com/father#', 'hasChild')),OWLClass(IRI('http://example.com/father#', 'person')),[])
# OWLObjectPropertyDomainAxiom(OWLObjectProperty(IRI('http://example.com/father#', 'hasChild')),OWLClass(IRI('http://example.com/father#', 'person')),[])


for axiom in onto.get_abox_axioms():
    print(axiom)
    
# OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://example.com/father#', 'anna')),class_expression=OWLClass(IRI('http://example.com/father#', 'female')),annotations=[])
# OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://example.com/father#', 'michelle')),class_expression=OWLClass(IRI('http://example.com/father#', 'female')),annotations=[])
# OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://example.com/father#', 'martin')),class_expression=OWLClass(IRI('http://example.com/father#', 'male')),annotations=[])
# OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://example.com/father#', 'markus')),class_expression=OWLClass(IRI('http://example.com/father#', 'male')),annotations=[])
# OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://example.com/father#', 'heinz')),class_expression=OWLClass(IRI('http://example.com/father#', 'male')),annotations=[])
# OWLClassAssertionAxiom(individual=OWLNamedIndividual(IRI('http://example.com/father#', 'stefan')),class_expression=OWLClass(IRI('http://example.com/father#', 'male')),annotations=[])
# OWLObjectPropertyAssertionAxiom(subject=OWLNamedIndividual(IRI('http://example.com/father#', 'markus')),property_=OWLObjectProperty(IRI('http://example.com/father#', 'hasChild')),object_=OWLNamedIndividual(IRI('http://example.com/father#', 'anna')),annotations=[])
# OWLObjectPropertyAssertionAxiom(subject=OWLNamedIndividual(IRI('http://example.com/father#', 'martin')),property_=OWLObjectProperty(IRI('http://example.com/father#', 'hasChild')),object_=OWLNamedIndividual(IRI('http://example.com/father#', 'heinz')),annotations=[])
# OWLObjectPropertyAssertionAxiom(subject=OWLNamedIndividual(IRI('http://example.com/father#', 'stefan')),property_=OWLObjectProperty(IRI('http://example.com/father#', 'hasChild')),object_=OWLNamedIndividual(IRI('http://example.com/father#', 'markus')),annotations=[])
# OWLObjectPropertyAssertionAxiom(subject=OWLNamedIndividual(IRI('http://example.com/father#', 'anna')),property_=OWLObjectProperty(IRI('http://example.com/father#', 'hasChild')),object_=OWLNamedIndividual(IRI('http://example.com/father#', 'heinz')),annotations=[])

```

</details>

### OWL Knowledge Engineering

<details><summary> Click me! </summary>

```python
from owlapy.class_expression import OWLClass, OWLObjectIntersectionOf, OWLObjectSomeValuesFrom
from owlapy.owl_property import OWLObjectProperty
from owlapy import owl_expression_to_sparql, owl_expression_to_dl
from owlapy.owl_axiom import OWLDeclarationAxiom, OWLClassAssertionAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.util_owl_static_funcs import create_ontology
# Using owl classes to create a complex class expression
male = OWLClass("http://example.com/society#male")
hasChild = OWLObjectProperty("http://example.com/society#hasChild")
hasChild_male = OWLObjectSomeValuesFrom(hasChild, male)
teacher = OWLClass("http://example.com/society#teacher")
teacher_that_hasChild_male = OWLObjectIntersectionOf([hasChild_male, teacher])

# You can render and print owl class expressions in Description Logics syntax or convert it to SPARQL for example.
print(owl_expression_to_dl(teacher_that_hasChild_male)) # (∃ hasChild.male) ⊓ teacher
print(owl_expression_to_sparql(teacher_that_hasChild_male)) #  SELECT DISTINCT ?x WHERE {  ?x <http://example.com/society#hasChild> ?s_1 . ?s_1 a <http://example.com/society#male> . ?x a <http://example.com/society#teacher> .  } }

# Create an ontology
ontology = create_ontology("file:/example_ontology.owl",with_owlapi=False)
john = OWLNamedIndividual("http://example.com/society#john")
male_declaration_axiom = OWLDeclarationAxiom(male)
hasChild_declaration_axiom = OWLDeclarationAxiom(hasChild)
john_declaration_axiom = OWLDeclarationAxiom(john)
john_a_male_assertion_axiom = OWLClassAssertionAxiom(john, male)
ontology.add_axiom([male_declaration_axiom, hasChild_declaration_axiom, john_declaration_axiom, john_a_male_assertion_axiom])
ontology.save(inplace=True)
```

Every OWL object that can be used to classify individuals, is considered a class expression and 
inherits from [OWLClassExpression](https://dice-group.github.io/owlapy/autoapi/owlapy/class_expression/class_expression/index.html#owlapy.class_expression.class_expression.OWLClassExpression) 
class. In the above examples we have introduced 3 types of class expressions: 
- [OWLClass](https://dice-group.github.io/owlapy/autoapi/owlapy/class_expression/owl_class/index.html#owlapy.class_expression.owl_class.OWLClass), 
- [OWLObjectSomeValuesFrom](https://dice-group.github.io/owlapy/autoapi/owlapy/class_expression/restriction/index.html#owlapy.class_expression.restriction.OWLObjectSomeValuesFrom)
- [OWLObjectIntersectionOf](https://dice-group.github.io/owlapy/autoapi/owlapy/class_expression/nary_boolean_expression/index.html#owlapy.class_expression.nary_boolean_expression.OWLObjectIntersectionOf).

Like we showed in this example, you can create all kinds of class expressions using the 
OWL objects in [owlapy api](https://dice-group.github.io/owlapy/autoapi/owlapy/index.html).

</details>


### Ontology Generation

<details><summary> Click me! </summary>

Our latest feature employees a combination of state-of-the-art approaches to extract knowledge graphs from unstructured
text using Large Language Models (LLMs). The algorithm consist of an agentic pipeline called AGen-KG (stands for agent-generated KG)
which can scale to large documents through chunking and merging strategies.

#### Installation

Before using this feature, install the required extra dependencies for LLM-based 
ontology generation:

```shell
pip install owlapy[agentic]  # or: pip install owlapy[all]
```

If you already have the minimum version of OWLAPY installed, you can install DSPy directly:

```shell
pip install dspy
```

> **Note:** DSPy is updated frequently and compatibility with the latest versions is not guaranteed. The last verified compatible version is **3.1.3**.


#### Example

```python
from owlapy.agen_kg import AGenKG
from owlapy.owl_ontology import SyncOntology


filep = "examples/doctors_notes.txt" # make sure the path is pointing correctly

# This example is set up to use GitHub's Models by providing your 
# GitHub Personal Access Token (PAT) because it's for free (subject to change),
# but of course, you can use any model & API base of your choice.
agent = AGenKG(model="gpt-4o", api_key="<YOUR_GITHUB_PAT>",
             api_base="https://models.github.ai/inference",
             temperature=0.1, seed=42, max_tokens=6000, enable_logging=True)
agent.generate_ontology(text=filep,
                        ontology_type="domain",
                        query="I want the resulting graph to represent medical information "
                              "about each patient from the provided doctors' notes.",
                        generate_types=True,
                        extract_spl_triples=True,
                        create_class_hierarchy=False,
                        fact_reassurance=False,
                        save_path="patients.owl")

# === Logs ===
# DomainGraphExtractor: INFO :: Decomposed the query into specific instructions
# UniversalTextLoader: INFO :: Loading text from .txt file: doctors_notes.txt
# UniversalTextLoader: INFO :: Successfully loaded 564 words (4257 characters)
# DomainGraphExtractor: INFO :: Text will be processed in 1 chunks
# DomainGraphExtractor: INFO :: Total chars: 4257, Est. tokens: 1064
# DomainGraphExtractor: INFO :: Detected domain: medicine
# DomainGraphExtractor: INFO :: Generating domain-specific few-shot examples for domain: medicine
# DomainGraphExtractor: INFO :: Generated examples for entity_extraction
# DomainGraphExtractor: INFO :: Generated examples for triples_extraction
# DomainGraphExtractor: INFO :: Generated examples for type_assertion
# DomainGraphExtractor: INFO :: Generated examples for type_generation
# DomainGraphExtractor: INFO :: Generated examples for literal_extraction
# DomainGraphExtractor: INFO :: Generated examples for triples_with_numeric_literals_extraction
# DomainGraphExtractor: INFO :: Cached examples for domain 'medicine' to path_hidden/domain_examples_medicine.json
# DomainGraphExtractor: INFO :: Generated the following entities: ['P001', 'EARLY HYPERTENSION', 'ACE INHIBITORS', 'P002', 'TYPE 2 DIABETES', 'METFORMIN', 'P003', 'SEASONAL FLU', 'ANTIVIRALS', 'P004', 'MECHANICAL BACK PAIN', 'NSAIDS', 'PHYSIOTHERAPY', 'P005', 'MIGRAINES', 'TRIPTANS', 'P006', 'OSTEOARTHRITIS', 'PAIN MANAGEMENT PLAN', 'P007', 'GERD', 'PPIs', 'P008', 'ANXIETY DISORDER', 'CBT', 'SSRIs', 'P009', 'HYPERLIPIDEMIA', 'STATINS', 'P010', 'ASTHMA', 'INHALED BRONCHODILATOR', 'P011', 'COPD', 'BRONCHODILATORS', 'P012', 'IRON DEFICIENCY ANEMIA', 'IRON SUPPLEMENTS', 'P013', 'DEPRESSION', 'ANTIDEPRESSANTS', 'P014', 'IBS', 'DIETARY MODIFICATIONS', 'P015', 'CATARACTS', 'SURGICAL EVALUATION', 'P016', 'HYPOTHYROIDISM', 'LEVOTHYROXINE', 'P017', 'ACUTE PHARYNGITIS', 'ANTIBIOTICS', 'P018', 'RHEUMATOID ARTHRITIS', 'DMARDs', 'P019', 'KIDNEY STONES', 'PAIN RELIEF', 'HYDRATION', 'P020', 'LOW VITAMIN D LEVELS', 'SUPPLEMENTS']
# DomainGraphExtractor: INFO :: Generated the following triples: [('P001', 'HAS', 'EARLY HYPERTENSION'), ('EARLY HYPERTENSION', 'TREATED WITH', 'ACE INHIBITORS'), ('P001', 'PRESCRIBED', 'ACE INHIBITORS'), ('P002', 'HAS', 'TYPE 2 DIABETES'), ('TYPE 2 DIABETES', 'TREATED WITH', 'METFORMIN'), ('P002', 'PRESCRIBED', 'METFORMIN'), ('P003', 'HAS', 'SEASONAL FLU'), ('SEASONAL FLU', 'TREATED WITH', 'ANTIVIRALS'), ('P003', 'PRESCRIBED', 'ANTIVIRALS'), ('P004', 'HAS', 'MECHANICAL BACK PAIN'), ('MECHANICAL BACK PAIN', 'TREATED WITH', 'NSAIDS'), ('P004', 'PRESCRIBED', 'NSAIDS'), ('P004', 'REFERRED TO', 'PHYSIOTHERAPY'), ('P005', 'HAS', 'MIGRAINES'), ('MIGRAINES', 'TREATED WITH', 'TRIPTANS'), ('P005', 'PRESCRIBED', 'TRIPTANS'), ('P006', 'HAS', 'OSTEOARTHRITIS'), ('OSTEOARTHRITIS', 'TREATED WITH', 'PAIN MANAGEMENT PLAN'), ('P007', 'HAS', 'GERD'), ('GERD', 'TREATED WITH', 'PPIs'), ('P007', 'PRESCRIBED', 'PPIs'), ('P008', 'HAS', 'ANXIETY DISORDER'), ('ANXIETY DISORDER', 'TREATED WITH', 'CBT'), ('ANXIETY DISORDER', 'TREATED WITH', 'SSRIs'), ('P008', 'PRESCRIBED', 'SSRIs'), ('P009', 'HAS', 'HYPERLIPIDEMIA'), ('HYPERLIPIDEMIA', 'TREATED WITH', 'STATINS'), ('P009', 'PRESCRIBED', 'STATINS'), ('P010', 'HAS', 'ASTHMA'), ('ASTHMA', 'TREATED WITH', 'INHALED BRONCHODILATOR'), ('P010', 'PRESCRIBED', 'INHALED BRONCHODILATOR'), ('P011', 'HAS', 'COPD'), ('COPD', 'TREATED WITH', 'BRONCHODILATORS'), ('P011', 'PRESCRIBED', 'BRONCHODILATORS'), ('P012', 'HAS', 'IRON DEFICIENCY ANEMIA'), ('IRON DEFICIENCY ANEMIA', 'TREATED WITH', 'IRON SUPPLEMENTS'), ('P012', 'PRESCRIBED', 'IRON SUPPLEMENTS'), ('P013', 'HAS', 'DEPRESSION'), ('DEPRESSION', 'TREATED WITH', 'ANTIDEPRESSANTS'), ('P013', 'PRESCRIBED', 'ANTIDEPRESSANTS'), ('P014', 'HAS', 'IBS'), ('IBS', 'TREATED WITH', 'DIETARY MODIFICATIONS'), ('P015', 'HAS', 'CATARACTS'), ('CATARACTS', 'TREATED WITH', 'SURGICAL EVALUATION'), ('P016', 'HAS', 'HYPOTHYROIDISM'), ('HYPOTHYROIDISM', 'TREATED WITH', 'LEVOTHYROXINE'), ('P016', 'PRESCRIBED', 'LEVOTHYROXINE'), ('P017', 'HAS', 'ACUTE PHARYNGITIS'), ('ACUTE PHARYNGITIS', 'TREATED WITH', 'ANTIBIOTICS'), ('P017', 'PRESCRIBED', 'ANTIBIOTICS'), ('P018', 'HAS', 'RHEUMATOID ARTHRITIS'), ('RHEUMATOID ARTHRITIS', 'TREATED WITH', 'DMARDs'), ('P018', 'PRESCRIBED', 'DMARDs'), ('P019', 'HAS', 'KIDNEY STONES'), ('KIDNEY STONES', 'TREATED WITH', 'PAIN RELIEF'), ('KIDNEY STONES', 'TREATED WITH', 'HYDRATION'), ('P020', 'HAS', 'LOW VITAMIN D LEVELS'), ('LOW VITAMIN D LEVELS', 'TREATED WITH', 'SUPPLEMENTS')]
# DomainGraphExtractor: INFO :: Using summary (3000 chars) for relation clustering
# DomainGraphExtractor: INFO :: Merged 1 duplicate relations
# DomainGraphExtractor: INFO :: After relation clustering: ['TREATED WITH', 'HAS', 'REFERRED TO']
# DomainGraphExtractor: INFO :: Skipped coherence check, using all 58 triples
# DomainGraphExtractor: INFO :: Finished generating types and assigned them to entities as following: [('P001', 'Patient'), ('EARLY HYPERTENSION', 'MedicalCondition'), ('ACE INHIBITORS', 'Medication'), ('P002', 'Patient'), ('TYPE 2 DIABETES', 'MedicalCondition'), ('METFORMIN', 'Medication'), ('P003', 'Patient'), ('SEASONAL FLU', 'MedicalCondition'), ('ANTIVIRALS', 'Medication'), ('P004', 'Patient'), ('MECHANICAL BACK PAIN', 'MedicalCondition'), ('NSAIDS', 'Medication'), ('PHYSIOTHERAPY', 'Procedure'), ('P005', 'Patient'), ('MIGRAINES', 'MedicalCondition'), ('TRIPTANS', 'Medication'), ('P006', 'Patient'), ('OSTEOARTHRITIS', 'MedicalCondition'), ('PAIN MANAGEMENT PLAN', 'Procedure'), ('P007', 'Patient'), ('GERD', 'MedicalCondition'), ('PPIs', 'Medication'), ('P008', 'Patient'), ('ANXIETY DISORDER', 'MedicalCondition'), ('CBT', 'Procedure'), ('SSRIs', 'Medication'), ('P009', 'Patient'), ('HYPERLIPIDEMIA', 'MedicalCondition'), ('STATINS', 'Medication'), ('P010', 'Patient'), ('ASTHMA', 'MedicalCondition'), ('INHALED BRONCHODILATOR', 'Medication'), ('P011', 'Patient'), ('COPD', 'MedicalCondition'), ('BRONCHODILATORS', 'Medication'), ('P012', 'Patient'), ('IRON DEFICIENCY ANEMIA', 'MedicalCondition'), ('IRON SUPPLEMENTS', 'Medication'), ('P013', 'Patient'), ('DEPRESSION', 'MedicalCondition'), ('ANTIDEPRESSANTS', 'Medication'), ('P014', 'Patient'), ('IBS', 'MedicalCondition'), ('DIETARY MODIFICATIONS', 'Procedure'), ('P015', 'Patient'), ('CATARACTS', 'MedicalCondition'), ('SURGICAL EVALUATION', 'Procedure'), ('P016', 'Patient'), ('HYPOTHYROIDISM', 'MedicalCondition'), ('LEVOTHYROXINE', 'Medication'), ('P017', 'Patient'), ('ACUTE PHARYNGITIS', 'MedicalCondition'), ('ANTIBIOTICS', 'Medication'), ('P018', 'Patient'), ('RHEUMATOID ARTHRITIS', 'MedicalCondition'), ('DMARDs', 'Medication'), ('P019', 'Patient'), ('KIDNEY STONES', 'MedicalCondition'), ('PAIN RELIEF', 'Procedure'), ('HYDRATION', 'Procedure'), ('P020', 'Patient'), ('LOW VITAMIN D LEVELS', 'LabResult'), ('SUPPLEMENTS', 'Medication')]
# DomainGraphExtractor: INFO :: Generated the following numeric literals: ['34', '58', '22', '45', '29', '67', '41', '36', '50', '19', '62', '27', '48', '33', '71', '39', '24', '55', '46', '31', '1']
# DomainGraphExtractor: INFO :: Generated the following s-p-l triples: [('P001', 'AGE', '34'), ('P002', 'AGE', '58'), ('P003', 'AGE', '22'), ('P004', 'AGE', '45'), ('P005', 'AGE', '29'), ('P006', 'AGE', '67'), ('P007', 'AGE', '41'), ('P008', 'AGE', '36'), ('P009', 'AGE', '50'), ('P010', 'AGE', '19'), ('P011', 'AGE', '62'), ('P012', 'AGE', '27'), ('P013', 'AGE', '48'), ('P014', 'AGE', '33'), ('P015', 'AGE', '71'), ('P016', 'AGE', '39'), ('P017', 'AGE', '24'), ('P018', 'AGE', '55'), ('P019', 'AGE', '46'), ('P020', 'AGE', '31')]
# Saving patients.owl..


# You can load the generated ontology and work with it as normally
onto = SyncOntology(path="patients.owl")
[print(ax) for ax in onto.get_abox_axioms()]
[print(ax) for ax in onto.get_tbox_axioms()]
```

You can find this example [here](https://github.com/dice-group/owlapy/blob/develop/examples/ag-gen_example.py).


</details>

### OWL Reasoning from Command line

<details><summary> Click me! </summary>

```shell
owlapy --path_ontology "KGs/Family/family-benchmark_rich_background.owl" --inference_types "all" --out_ontology "enriched_family.owl"
```

```--inference_types``` can be specified by selecting one from 

``` 
["InferredClassAssertionAxiomGenerator",
"InferredSubClassAxiomGenerator",
"InferredDisjointClassesAxiomGenerator",
"InferredEquivalentClassAxiomGenerator",
"InferredEquivalentDataPropertiesAxiomGenerator",
"InferredEquivalentObjectPropertyAxiomGenerator",
"InferredInverseObjectPropertiesAxiomGenerator",
"InferredSubDataPropertyAxiomGenerator",
"InferredSubObjectPropertyAxiomGenerator",
"InferredDataPropertyCharacteristicAxiomGenerator",
"InferredObjectPropertyCharacteristicAxiomGenerator"]
```

</details>

### Logical Inference

<details><summary> Click me! </summary>

```python
from owlapy.owl_reasoner import SyncReasoner
from owlapy.static_funcs import stopJVM
from owlapy.owl_ontology import Ontology

ontology_path = "KGs/Family/family-benchmark_rich_background.owl"
# Available OWL Reasoners: 'HermiT', 'Pellet', 'JFact', 'Openllet', 'ELK', 'Structural'
sync_reasoner = SyncReasoner(ontology = ontology_path, reasoner="Pellet")
onto = Ontology(ontology_path)
# Iterate over defined owl Classes in the signature
for i in onto.classes_in_signature():
    # Performing type inference with Pellet
    instances=sync_reasoner.instances(i,direct=False)
    print(f"Class:{i}\t Num instances:{len(instances)}")
stopJVM()
```

</details>

### Ontology Enrichment

<details><summary> Click me! </summary>

An Ontology can be enriched by inferring many different axioms.
```python
from owlapy.owl_reasoner import SyncReasoner
from owlapy.static_funcs import stopJVM

sync_reasoner = SyncReasoner(ontology="KGs/Family/family-benchmark_rich_background.owl", reasoner="Pellet")
# Infer missing class assertions
sync_reasoner.infer_axioms_and_save(output_path="KGs/Family/inferred_family-benchmark_rich_background.ttl",
                       output_format="ttl",
                       inference_types=[
                           "InferredClassAssertionAxiomGenerator",
                           "InferredEquivalentClassAxiomGenerator",
                           "InferredDisjointClassesAxiomGenerator",
                                        "InferredSubClassAxiomGenerator",
                                        "InferredInverseObjectPropertiesAxiomGenerator",
                                        "InferredEquivalentClassAxiomGenerator"])
stopJVM()
```

</details>


### Sklearn to OWL Ontology

<details><summary> Click me! </summary>

```python
from owlapy.owl_ontology import SyncOntology
from owlapy.util_owl_static_funcs import csv_to_rdf_kg
import pandas as pd
from sklearn.datasets import load_iris
data = load_iris()
df = pd.DataFrame(data.data, columns=data.feature_names)
df.to_csv("iris_dataset.csv", index=False)
path_kg = "iris_kg.owl"
# Construct an RDF Knowledge Graph from a CSV file
csv_to_rdf_kg(path_csv="iris_dataset.csv", path_kg=path_kg, namespace="http://owlapy.com/iris")
onto = SyncOntology(path_kg)
print(len(onto.get_abox_axioms()))

```

</details>


### Create Justifications

<details><summary> Click me!</summary>

```python
from owlapy.owl_axiom import OWLClassAssertionAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_reasoner import SyncReasoner
from owlapy.owl_ontology import SyncOntology
from owlapy import manchester_to_owl_expression

individual = OWLNamedIndividual("http://www.benchmark.org/family#F1F2")
manchester_expr_str = "hasChild some Female"

ontology = SyncOntology("../KGs/Family/family-benchmark_rich_background.owl")
reasoner = SyncReasoner(ontology, reasoner="Pellet")
target_class = manchester_to_owl_expression(manchester_expr_str, "http://www.benchmark.org/family#")
axiom = OWLClassAssertionAxiom(individual, target_class)
justifications = reasoner.create_axiom_justifications(axiom)
[print(justification) for justification in justifications]
```
</details>


### Get Contrastive Explanations

<details><summary> Click me!</summary>

```python
from owlapy import manchester_to_owl_expression
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner import SyncReasoner

# --- Load ontology and reasoner ---
ontology = SyncOntology("../KGs/Family/family.owl")
reasoner = SyncReasoner(ontology, reasoner="HermiT")

# --- Define class expression ---
class_expr = manchester_to_owl_expression(
    "Sister and (hasSibling some (married some (hasChild some Grandchild)))",
    "http://www.benchmark.org/family#"
)

# --- Define individuals ---
fact = OWLNamedIndividual(IRI.create("http://www.benchmark.org/family#F9F143"))
foil = OWLNamedIndividual(IRI.create("http://www.benchmark.org/family#F9M161"))

# --- Get contrastive explanation ---
result = reasoner.get_contrastive_explanation(class_expr, fact, foil)

# --- Print results ---
for k in ["common", "different", "conflict"]:
    print(f"{k.capitalize()} axioms: {result[k]}")
```
</details>


### Class expression simplification

<details><summary> Click me!</summary>

Syntactic simplification of class expressions using `owlapy.utils.CESimplifier` class or directly by using
`owlapy.utils.simplify_class_expression` function.

```python
from owlapy import dl_to_owl_expression, owl_expression_to_dl
from owlapy.utils import simplify_class_expression, get_expression_length

ce_dl = "((((((((((¬Father) ⊓ (¬(∃ hasChild.Grandfather))) ⊓ (¬(∃ hasParent.{F1F2}))) ⊓ (¬(∃ hasSibling.Granddaughter))) \
⊓ Grandson) ⊓ (¬(∃ hasParent.{F8M136}))) ⊔ ((((((¬Father) ⊓ (¬(∃ hasChild.Grandfather))) ⊓ (¬(∃ hasParent.{F1F2}))) ⊓ \
(¬(∃ hasSibling.Granddaughter))) ⊓ (¬Grandson)) ⊓ (∃ married.{F10F179}))) ⊔ (((((¬Father) ⊓ (¬(∃ hasChild.Grandfather))) \
⊓ (¬(∃ hasParent.{F1F2}))) ⊓ (∃ hasSibling.Granddaughter)) ⊓ (¬Grandson))) ⊔ ((¬Father) ⊓ (∃ hasChild.Grandfather))) ⊔ \
(((¬Father) ⊓ (¬(∃ hasChild.Grandfather))) ⊓ (∃ hasParent.{F1F2}))) ⊔ (((Father ⊓ (¬(∃ hasSibling.Grandson))) ⊓ \
(¬(∃ hasChild.{F5M64}))) ⊓ (¬(∃ married.{F2F15})))"
ce_owl = dl_to_owl_expression(ce_dl, "http://www.benchmark.org/family#")
simplified_ce = simplify_class_expression(ce_owl)
print(owl_expression_to_dl(simplified_ce))
print(f"Original CE length: {get_expression_length(ce_owl)} \nSimplified CE length: {get_expression_length(simplified_ce)}")
```
</details>

### Reasoners Runtime Benchmark

<details><summary> Click me! </summary>

To generate and print the following tables:

```shell
wget https://files.dice-research.org/projects/Ontolearn/KGs.zip -O ./KGs.zip && unzip KGs.zip

cd examples && python runtime_benchmark_results.py --pretty_print
```

`StructuralReasoner` and `RDFLibReasoner` are **closed-world** (structural, no formal entailment);
`HermiT`/`Pellet`/`Openllet`/`JFact`/`Structural` (via `SyncReasoner`) are **open-world**, standard
OWL 2 DL semantics; `ELK` is open-world but incomplete (EL profile only). See
[Reasoner Comparison](markdown_docs/05_reasoning.md#reasoner-comparison) for what that means for
your use case.

Each reasoner is given a hard upper bound of 1000 seconds per class expression
(`--timeout_seconds`, script-enforced -- see `HARD_TIMEOUT_SECONDS` in
`examples/runtime_benchmark_results.py`); a reasoner that hasn't returned by then is reported as
`TIMEOUT(>1000s)` instead of being waited on further, so a single pathological query can't block
the whole benchmark.

Instance retrieval runtime (in seconds) of each reasoner for different class expressions in **Family** dataset:

| Class Expressions                      | StructuralReasoner | RDFLibReasoner |  HermiT |  Pellet | Openllet |   JFact |     ELK | Structural |
|-----------------------------------------|--------------------:|---------------:|--------:|--------:|---------:|--------:|--------:|-----------:|
| Person                                 |              0.0730 |          0.1763 |  0.0335 |  0.0624 |   0.0507 |  0.2219 |  0.1705 |     0.0147 |
| (¬Parent)                              |              0.0024 |          0.5766 |  0.4232 |  0.0036 |   0.0014 |  0.0027 |  0.0240 |     0.0011 |
| ∀ hasParent.Father                     |              0.0052 |          0.5231 |  0.4135 |  0.0028 |   0.0011 |  0.0040 |  0.0044 |     0.0008 |
| ∃ hasSibling.Daughter                  |              0.0021 |          0.0360 |  0.3775 |  0.0033 |   0.0023 |  0.0112 |  0.0107 |     0.0007 |
| ∃ hasChild.(¬Parent)                   |              0.0026 |          0.9000 |  0.3764 |  0.0025 |   0.0017 |  0.0066 |  0.0056 |     0.0008 |
| ≥ 1 married.Male                       |              0.0035 |          0.1074 |  0.3598 |  0.1690 |   0.1088 |  0.0075 |  0.0028 |     0.0006 |
| ≤ 3 hasChild.Person                    |              0.0015 |          0.4348 |  0.3743 |  0.0020 |   0.0016 |  0.0028 |  0.0028 |     0.0007 |
| Brother ⊓ Parent                       |              0.0006 |          0.0942 |  0.1620 |  0.0025 |   0.0012 |  0.0025 |  0.0083 |     0.0007 |
| Mother ⊔ Father                        |              0.0007 |          0.0830 |  0.0521 |  0.0036 |   0.0050 |  0.0031 |  0.0141 |     0.0006 |
| ∃ hasParent.{F9M170 ⊔ F9M147 ⊔ F7M128} |              0.0003 |          0.0198 |  0.3837 |  0.0175 |   0.0102 |  0.0061 |  0.0041 |     0.0012 |

-----------------------------------------------------------------

Instance retrieval runtime (in seconds) of each reasoner for different class expressions in **Carcinogenesis** dataset (`TIMEOUT(>1000s)` = hit the hard upper bound described above; result was incomplete/empty, not a completion time):

| Class Expressions                           | StructuralReasoner |  RDFLibReasoner |      HermiT |    Pellet |  Openllet |    JFact |     ELK | Structural |
|:---------------------------------------------|--------------------:|-----------------:|-------------:|----------:|----------:|---------:|--------:|-----------:|
| Sulfur                                      |              0.0048 |           2.4729 |       0.4402 |    0.2408 |    0.1411 |  34.5881 |  0.8854 |     0.0087 |
| Structure                                   |              0.0551 |           8.7157 |       0.0508 |    0.0616 |    0.0505 |   0.0497 |  0.1807 |     0.0451 |
| ¬Structure                                  |              0.4901 |          71.7221 |     280.8219 |    0.3205 |    0.2755 |   0.4435 |  0.0358 |     0.0010 |
| ∀ hasAtom.Atom                              |              0.3513 | TIMEOUT(>1000s) |       0.2997 |    0.3297 |    0.3249 |   0.3228 |  0.0028 |     0.0004 |
| ∃ hasStructure.Amino                        |              0.0320 |           0.8363 |      26.3037 |    0.0350 |    0.0456 |   0.2756 |  0.0228 |     0.0004 |
| ≥ 2 inBond.⊤                                |              0.2937 |           3.7918 |     762.5192 |    0.4647 |    0.2423 |   8.6851 |  0.0022 |     0.0003 |
| ≤ 3 hasAtom.⊤                               |              0.0912 |          74.6104 |      28.7288 |    0.3333 |    0.3355 |   0.3411 |  0.0019 |     0.0003 |
| Ring_size_4 ⊓ Sulfur                        |              0.0011 |           3.7009 | TIMEOUT(>1000s) |    0.0195 |    0.0167 |   0.0121 |  0.0116 |     0.0004 |
| Bond-7 ⊔ Bond-3                             |              0.0109 |          97.0338 | TIMEOUT(>1000s) |    0.0673 |    0.0602 |   0.0435 |  0.0654 |     0.0005 |
| ∃ hasBond.{bond1838 ⊔ bond1879 ⊔ bond1834}  |              0.0770 |           0.9832 |     381.2848 |    1.3793 |    1.3290 |   0.3337 |  0.0161 |     0.0007 |
| ∃ isMutagenic.{True}                        |              0.0046 |           0.0241 |      25.7430 |   28.3317 |   30.6846 |   0.2114 |  0.0055 |     0.0003 |
| ∃ charge.xsd:double[> 0.1]                  |              0.0845 |           1.1228 |     721.7161 |  709.7448 |  780.8275 |   0.2004 |  0.0022 |     0.0004 |
| Compound ⊓ ∃ isMutagenic.{True}             |              0.0035 |           2.4838 |      26.6295 |   27.5774 |   29.9838 |   0.4790 |  0.0219 |     0.0004 |
| Carbon ⊓ ∃ charge.xsd:double[> 0.1]         |              0.0260 |          83.8693 |     273.3282 |  699.4585 |  778.6429 |   0.0960 |  0.0037 |     0.0004 |

</details>

Check also the [examples](https://github.com/dice-group/owlapy/tree/develop/examples) and [tests](https://github.com/dice-group/owlapy/tree/develop/tests) directories for more examples.

## 🌐 Try It Online
Explore OWLAPY through [OntoSource](https://github.com/dice-group/OntoSource) - a web-based interface for ontology engineering, no installation required.


## 📄 How to Cite
If you use OWLAPY in your research, please cite our work:

```
# OWLAPY
@misc{baci2025owlapypythonicframeworkowl,
      title={OWLAPY: A Pythonic Framework for OWL Ontology Engineering}, 
      author={Alkid Baci and Luke Friedrichs and Caglar Demir and Axel-Cyrille Ngonga Ngomo},
      year={2025},
      eprint={2511.08232},
      archivePrefix={arXiv},
      primaryClass={cs.SE},
      url={https://arxiv.org/abs/2511.08232}, 
}


# EBR
@misc{teyou2025neuralreasoningrobustinstance,
      title={Neural Reasoning for Robust Instance Retrieval in $\mathcal{SHOIQ}$}, 
      author={Louis Mozart Kamdem Teyou and Luke Friedrichs and N'Dah Jean Kouagou and Caglar Demir and Yasir Mahmood and Stefan Heindorf and Axel-Cyrille Ngonga Ngomo},
      year={2025},
      eprint={2510.20457},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2510.20457}, 
}
```

Built by the DICE Research Group | [dice-research.org](https://dice-research.org/) | [UPB homepage](https://en.cs.uni-paderborn.de/ds)