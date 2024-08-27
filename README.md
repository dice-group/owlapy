# OWLAPY
[![Coverage](https://img.shields.io/badge/coverage-78%25-green)](https://dice-group.github.io/owlapy/usage/further_resources.html#coverage-report)
[![Pypi](https://img.shields.io/badge/pypi-1.2.0-blue)](https://pypi.org/project/owlapy/1.2.0/)
[![Docs](https://img.shields.io/badge/documentation-1.2.0-yellow)](https://dice-group.github.io/owlapy/usage/main.html)

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
pytest -p no:warnings -x # Running  102 tests takes ~ 1 min
```

## Usage


### Creating OWL Class Expressions
<details><summary> Click me! </summary>

```python
from owlapy.class_expression import OWLClass, OWLObjectIntersectionOf, OWLObjectSomeValuesFrom
from owlapy.owl_property import OWLObjectProperty
from owlapy import owl_expression_to_sparql, owl_expression_to_dl

# Create the male class
male = OWLClass("http://example.com/society#male")
# Create an object property using the iri as a string for 'hasChild' property.
hasChild = OWLObjectProperty("http://example.com/society#hasChild")
# Create an existential restrictions
hasChild_male = OWLObjectSomeValuesFrom(hasChild, male)
# Let's make it more complex by intersecting with another class
teacher = OWLClass("http://example.com/society#teacher")
teacher_that_hasChild_male = OWLObjectIntersectionOf([hasChild_male, teacher])
# You can render and print owl class expressions in description logics syntax (and vice-versa)
print(owl_expression_to_dl(teacher_that_hasChild_male))
# (∃ hasChild.male) ⊓ teacher
print(owl_expression_to_sparql(teacher_that_hasChild_male))
#  SELECT DISTINCT ?x WHERE {  ?x <http://example.com/society#hasChild> ?s_1 . ?s_1 a <http://example.com/society#male> . ?x a <http://example.com/society#teacher> .  } }
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
from owlapy.owlapi_adaptor import OWLAPIAdaptor

ontology_path = "KGs/Family/family-benchmark_rich_background.owl"
# Available OWL Reasoners: 'HermiT', 'Pellet', 'JFact', 'Openllet'
owlapi_adaptor = OWLAPIAdaptor(path=ontology_path, name_reasoner="Pellet")
onto = OntologyManager().load_ontology(ontology_path)
# Iterate over defined owl Classes in the signature
for i in onto.classes_in_signature():
    # Performing type inference with Pellet
    instances=owlapi_adaptor.instances(i,direct=False)
    print(f"Class:{i}\t Num instances:{len(instances)}")
owlapi_adaptor.stopJVM()
```

</details>

### Ontology Enrichment

<details><summary> Click me! </summary>

An Ontology can be enriched by inferring many different axioms.
```python
from owlapy.owlapi_adaptor import OWLAPIAdaptor

adaptor = OWLAPIAdaptor(path="KGs/Family/family-benchmark_rich_background.owl", name_reasoner="Pellet")
# Infer missing class assertions
adaptor.infer_axioms_and_save(output_path="KGs/Family/inferred_family-benchmark_rich_background.ttl",
                       output_format="ttl",
                       inference_types=[
                           "InferredClassAssertionAxiomGenerator",
                           "InferredEquivalentClassAxiomGenerator",
                           "InferredDisjointClassesAxiomGenerator",
                                        "InferredSubClassAxiomGenerator",
                                        "InferredInverseObjectPropertiesAxiomGenerator",
                                        "InferredEquivalentClassAxiomGenerator"])
adaptor.stopJVM()
```

</details>


Check also the [examples](https://github.com/dice-group/owlapy/tree/develop/examples) and [tests](https://github.com/dice-group/owlapy/tree/develop/tests) folders.

## How to cite
Currently, we are working on our manuscript describing our framework.
