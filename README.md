# OWLAPY
[![Downloads](https://static.pepy.tech/badge/owlapy)](https://pepy.tech/project/owlapy)
[![Downloads](https://img.shields.io/pypi/dm/owlapy)](https://pypi.org/project/owlapy/)
[![Coverage](https://img.shields.io/badge/coverage-82%25-green)](https://dice-group.github.io/owlapy/usage/further_resources.html#coverage-report)
[![Pypi](https://img.shields.io/badge/pypi-1.6.2-blue)](https://pypi.org/project/owlapy/1.6.2/)
[![Docs](https://img.shields.io/badge/documentation-1.6.2-yellow)](https://dice-group.github.io/owlapy/usage/main.html)
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

- **Python-native Reasoners**: Structural Reasoner and Embedding-based Reasoner
- **Optimized Performance**: Benchmarked across complex ontologies (see our [performance data](#reasoners-runtime-benchmark))
- **Synchronization with Java Reasoners**: HermiT, Pellet, JFact, Openllet, ELK, and Structural

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

conda create -n temp_owlapy python=3.10.13 --no-default-packages && conda activate temp_owlapy && pip install -e '.[dev]'
```

#### Extra Files (optional)

```shell
# Download RDF knowledge graphs
wget https://files.dice-research.org/projects/Ontolearn/KGs.zip -O ./KGs.zip && unzip KGs.zip

# Test with pytest
PYTHONPATH=. pytest
```

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
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_reasoner import SyncReasoner
from owlapy.owl_ontology import SyncOntology
from owlapy import manchester_to_owl_expression

individual = OWLNamedIndividual("http://www.benchmark.org/family#F1F2")
manchester_expr_str = "hasChild some Female"

ontology = SyncOntology("../KGs/Family/family-benchmark_rich_background.owl")
reasoner = SyncReasoner(ontology, reasoner="Pellet")
target_class = manchester_to_owl_expression(manchester_expr_str, "http://www.benchmark.org/family#")
justifications = reasoner.create_justifications({individual}, target_class, save=True)
[print(justification) for justification in justifications]
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

Instance retrieval runtime (in seconds) of each reasoner for different class expressions in **Family** dataset:

| Class Expressions                      |  StructuralReasoner |  HermiT |  Pellet |  Openllet |   JFact |     ELK |  Structural |
|----------------------------------------|--------------------:|--------:|--------:|----------:|--------:|--------:|------------:|
| Person                                 |              0.0007 |  0.0251 |  0.0238 |    0.0128 |  0.1726 |  0.1526 |      0.0748 |
| (¬Parent)                              |              0.0005 |  0.3532 |   0.004 |    0.0032 |  0.0046 |  0.0205 |      0.0015 |
| ∀ hasParent.Father                     |              0.0004 |  0.3108 |  0.0043 |    0.0035 |   0.006 |  0.0038 |       0.001 |
| ∃ hasSibling.Daughter                  |              0.0003 |  0.3176 |   0.005 |    0.0057 |   0.011 |  0.0103 |      0.0008 |
| ∃ hasChild.(¬Parent)                   |              0.0005 |  0.3335 |   0.004 |    0.0042 |  0.0102 |  0.0065 |      0.0013 |
| ≥ 1 married.Male                       |              0.0003 |  0.3129 |  0.1711 |     0.143 |  0.0101 |  0.0035 |       0.001 |
| ≤ 3 hasChild.Person                    |              0.0006 |  0.3114 |   0.003 |    0.0038 |  0.0044 |  0.0032 |      0.0008 |
| Brother ⊓ Parent                       |              0.0003 |  0.1445 |  0.0039 |    0.0032 |  0.0028 |  0.0112 |      0.0007 |
| Mother ⊔ Father                        |              0.0003 |  0.0502 |  0.0063 |     0.008 |  0.0071 |  0.0167 |      0.0005 |
| ∃ hasParent.{F9M170 ⊔ F9M147 ⊔ F7M128} |              0.0006 |  0.3107 |  0.0152 |     0.033 |  0.0089 |  0.0063 |      0.0017 |

-----------------------------------------------------------------

Instance retrieval runtime (in seconds) of each reasoner for different class expressions in **Carcinogenesis** dataset:

| Class Expressions                           |  StructuralReasoner |     HermiT |    Pellet |  Openllet |    JFact |     ELK |  Structural |
|:--------------------------------------------|--------------------:|-----------:|----------:|----------:|---------:|--------:|------------:|
| Sulfur                                      |              0.0012 |     0.5098 |    0.3415 |    0.3124 |  30.9185 |  1.0194 |      0.0821 |
| Structure                                   |              0.0004 |     0.0542 |     0.067 |    0.0677 |   0.0571 |  0.1922 |      0.0527 |
| ¬Structure                                  |              0.0004 |   225.7262 |    0.2838 |    0.3073 |   0.3142 |  0.0465 |      0.0027 |
| ∀ hasAtom.Atom                              |              0.0004 |     0.2862 |    0.3253 |    0.3112 |   0.3378 |  0.0063 |      0.0010 |
| ∃ hasStructure.Amino                        |              0.0005 |    20.5614 |    0.0586 |    0.1081 |   0.2986 |  0.0343 |      0.0011 |
| ≥ 2 inBond.⊤                                |              0.0003 |   593.4231 |    0.4509 |    0.4633 |   7.8003 |  0.0055 |      0.0007 |
| ≤ 3 hasAtom.⊤                               |              0.0002 |    21.5695 |    0.3497 |    0.3092 |   0.3407 |  0.0035 |      0.0005 |
| Ring_size_4 ⊓ Sulfur                        |              0.0004 |  2932.3817 |    0.0281 |    0.0163 |   0.0187 |  0.0232 |      0.0008 |
| Bond-7 ⊔ Bond-3                             |              0.0003 |   486.6015 |    0.0838 |    0.0654 |     0.05 |  0.1009 |      0.0007 |
| ∃ hasBond.{bond1838 ⊔ bond1879 ⊔ bond1834}  |              0.0006 |    24.3014 |    1.6182 |    1.2811 |   0.3255 |  0.0391 |      0.0012 |
| ∃ isMutagenic.{True}                        |              0.0233 |    26.6729 |     32.31 |   28.9644 |   0.1972 |   0.012 |      0.0006 |
| ∃ charge.xsd:double[> 0.1]                  |              0.0008 |   626.9762 |   752.119 |  750.1382 |   0.2102 |   0.006 |      0.0008 |
| Compound ⊓ ∃ isMutagenic.{True}             |              0.0009 |    21.8479 |   28.4732 |   29.7676 |   0.1918 |  0.0189 |      0.0007 |
| Carbon ⊓ ∃ charge.xsd:double[> 0.1]         |              0.0005 |   245.4081 |  734.3972 |  747.7481 |   0.0998 |  0.0031 |      0.0007 |

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