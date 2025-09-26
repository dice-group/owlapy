# OWLAPY
[![Downloads](https://static.pepy.tech/badge/owlapy)](https://pepy.tech/project/owlapy)
[![Downloads](https://img.shields.io/pypi/dm/owlapy)](https://pypi.org/project/owlapy/)
[![Coverage](https://img.shields.io/badge/coverage-78%25-green)](https://dice-group.github.io/owlapy/usage/further_resources.html#coverage-report)
[![Pypi](https://img.shields.io/badge/pypi-1.6.1-blue)](https://pypi.org/project/owlapy/1.6.1/)
[![Docs](https://img.shields.io/badge/documentation-1.6.1-yellow)](https://dice-group.github.io/owlapy/usage/main.html)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/dice-group/owlapy)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/dice-group/owlapy/test.yml)
![GitHub License](https://img.shields.io/github/license/dice-group/owlapy)


![OWLAPY](docs/_static/images/owlapy_logo.png)

OWLAPY is a Python Framework for creating and manipulating OWL Ontologies.

Have a look at the [Documentation](https://dice-group.github.io/owlapy/).

[DeepWiki](https://deepwiki.com/dice-group/owlapy) can also help you get started with owlapy.

## Installation

### Installation from Source
``` bash
git clone https://github.com/dice-group/owlapy
conda create -n temp_owlapy python=3.10.13 --no-default-packages && conda activate temp_owlapy && pip3 install -e .
```

### Installation from PyPI
```bash
pip3 install owlapy
```

### Extra files (optional)

```shell
# To download RDF knowledge graphs
wget https://files.dice-research.org/projects/Ontolearn/KGs.zip -O ./KGs.zip && unzip KGs.zip
pytest -p no:warnings -x # Running  147 tests ~ 35 secs
```

## Examples

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
text using Large Language Models (LLMs).

```python
from owlapy.ontogen.data_extraction import GraphExtractor
from owlapy.owl_ontology import SyncOntology

text_example = """J.P. Morgan & Co. is an American financial institution specialized in investment banking, 
asset management and private banking founded by financier J. P. Morgan in 1871. Through a series of mergers and 
acquisitions, the company is now a subsidiary of JPMorgan Chase, the largest banking institution in the world. 
The company has been historically referred to as the "House of Morgan" or simply Morgan."""

# Extract a graph from text using an LLM
ontogen = GraphExtractor(model="<ENTER_MODELS_NAME> (e.g. 'Qwen/Qwen3-32B-AWQ')",api_key="<ENTER_YOUR_KEY>", api_base="<ENTER_YOUR_API_BASE_URL>",
                         temperature=0.1, seed=42, enable_logging=True)
ontogen.forward(text=text_example, generate_types = True, extract_spl_triples=True)

# Load the generated ontology and print axioms
onto = SyncOntology(path="generated_ontology.owl")
[print(ax) for ax in onto.get_abox_axioms()]
[print(ax) for ax in onto.get_tbox_axioms()]
```

If you just want to give it a quick try, and you don't have access to a paid API token, you can use GitHub Models.
Check out this example [here](https://github.com/dice-group/owlapy/blob/develop/examples/ontogen_example.py) where it shows how to configure `GraphExtractor` with GitHub PAT.


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

## How to cite
Currently, we are working on our manuscript describing our framework.