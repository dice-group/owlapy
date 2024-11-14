# OWLAPY
[![Coverage](https://img.shields.io/badge/coverage-78%25-green)](https://dice-group.github.io/owlapy/usage/further_resources.html#coverage-report)
[![Pypi](https://img.shields.io/badge/pypi-1.3.3-blue)](https://pypi.org/project/owlapy/1.3.3/)
[![Docs](https://img.shields.io/badge/documentation-1.3.3-yellow)](https://dice-group.github.io/owlapy/usage/main.html)

![OWLAPY](docs/_static/images/owlapy_logo.png)

OWLAPY is a Python Framework for creating and manipulating OWL Ontologies.

Have a look at the [Documentation](https://dice-group.github.io/owlapy/).

## Installation

### Installation from Source
``` bash
git clone https://github.com/dice-group/owlapy
conda create -n temp_owlapy python=3.10.13 --no-default-packages && conda activate temp_owlapy && pip3 install -e .
```
or
```bash
pip3 install owlapy
```


```shell
# To download RDF knowledge graphs
wget https://files.dice-research.org/projects/Ontolearn/KGs.zip -O ./KGs.zip && unzip KGs.zip
pytest -p no:warnings -x # Running  147 tests ~ 35 secs
```

## Examples

### Sklearn to OWL Ontology

<details><summary> Click me! </summary>

```python
from owlapy.owl_ontology_manager import SyncOntologyManager
from owlapy.util_owl_static_funcs import csv_to_rdf_kg
import pandas as pd
from sklearn.datasets import load_iris
data = load_iris()
df = pd.DataFrame(data.data, columns=data.feature_names)
df.to_csv("iris_dataset.csv", index=False)
path_kg = "iris_kg.owl"
# Construct an RDF Knowledge Graph from a CSV file
csv_to_rdf_kg(path_csv="iris_dataset.csv", path_kg=path_kg, namespace="http://owlapy.com/iris")
onto = SyncOntologyManager().load_ontology(path_kg)
assert len(onto.get_abox_axioms()) == 750

```

</details>


### Exploring OWL Ontology

<details><summary> Click me! </summary>

```python
from owlapy.owl_ontology_manager import SyncOntologyManager

ontology_path = "KGs/Family/father.owl"
onto = SyncOntologyManager().load_ontology(ontology_path)

print({owl_class.reminder for owl_class in onto.classes_in_signature()}) 
# {'Thing', 'female', 'male', 'person'}

print({individual.reminder for individual in onto.individuals_in_signature()}) 
# {'michelle', 'stefan', 'martin', 'anna', 'heinz', 'markus'}

print({object_property.reminder for object_property in onto.object_properties_in_signature()})
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

### Creating OWL Class Expressions
<details><summary> Click me! </summary>

```python
from owlapy.class_expression import OWLClass, OWLObjectIntersectionOf, OWLObjectSomeValuesFrom
from owlapy.owl_property import OWLObjectProperty
from owlapy import owl_expression_to_sparql, owl_expression_to_dl
from owlapy.owl_ontology_manager import OntologyManager
from owlapy.owl_axiom import OWLDeclarationAxiom, OWLClassAssertionAxiom
from owlapy.owl_individual import OWLNamedIndividual, IRI

# Using owl classes to create a complex class expression
male = OWLClass("http://example.com/society#male")
hasChild = OWLObjectProperty("http://example.com/society#hasChild")
hasChild_male = OWLObjectSomeValuesFrom(hasChild, male)
teacher = OWLClass("http://example.com/society#teacher")
teacher_that_hasChild_male = OWLObjectIntersectionOf([hasChild_male, teacher])

# You can render and print owl class expressions in Description Logics syntax or convert it to SPARQL for example. 
print(owl_expression_to_dl(teacher_that_hasChild_male)) # (∃ hasChild.male) ⊓ teacher
print(owl_expression_to_sparql(teacher_that_hasChild_male)) #  SELECT DISTINCT ?x WHERE {  ?x <http://example.com/society#hasChild> ?s_1 . ?s_1 a <http://example.com/society#male> . ?x a <http://example.com/society#teacher> .  } }

# Create an Ontology, add the axioms and save the Ontology.
manager = OntologyManager()
new_iri = IRI.create("file:/example_ontology.owl")
ontology = manager.create_ontology(new_iri)

john = OWLNamedIndividual("http://example.com/society#john")
male_declaration_axiom = OWLDeclarationAxiom(male)
hasChild_declaration_axiom = OWLDeclarationAxiom(hasChild)
john_declaration_axiom = OWLDeclarationAxiom(john)
john_a_male_assertion_axiom = OWLClassAssertionAxiom(john, male)
ontology.add_axiom([male_declaration_axiom, hasChild_declaration_axiom, john_declaration_axiom, john_a_male_assertion_axiom])
ontology.save()

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

### Logical Inference

<details><summary> Click me! </summary>

```python
from owlapy.owl_ontology_manager import OntologyManager
from owlapy.owl_reasoner import SyncReasoner
from owlapy.static_funcs import stopJVM

ontology_path = "KGs/Family/family-benchmark_rich_background.owl"
# Available OWL Reasoners: 'HermiT', 'Pellet', 'JFact', 'Openllet'
sync_reasoner = SyncReasoner(ontology = ontology_path, reasoner="Pellet")
onto = OntologyManager().load_ontology(ontology_path)
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


Check also the [examples](https://github.com/dice-group/owlapy/tree/develop/examples) and [tests](https://github.com/dice-group/owlapy/tree/develop/tests) folders.

## How to cite
Currently, we are working on our manuscript describing our framework.
