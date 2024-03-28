# OWLAPY

## Installation
<details><summary> Click me! </summary>

### Installation from Source
``` bash
git clone https://github.com/dice-group/owlapy
conda create -n temp_owlapy python=3.10.13 --no-default-packages && conda activate temp_owlapy && pip3 install -e .
```
or
```bash
pip3 install owlapy
```
</details>

## Usage
<details><summary> Click me! </summary>

In this example we start with a simple atomic class expression and move to some more complex 
ones and finally render and print the last of them in description logics syntax.

```python
from owlapy.render import DLSyntaxObjectRenderer
from owlapy.model import IRI, OWLClass, OWLObjectProperty, OWLObjectSomeValuesFrom, \
                         OWLObjectIntersectionOf
from owlapy.owl2sparql.converter import owl_expression_to_sparql

# Create an IRI object using the iri as a string for 'male' class.
male_iri = IRI.create('http://example.com/society#male')

# Create the male class
male = OWLClass(male_iri)

# Create an object property using the iri as a string for 'hasChild' property.
hasChild = OWLObjectProperty(IRI.create('http://example.com/society#hasChild'))

# Create an existential restrictions
males_with_children = OWLObjectSomeValuesFrom(hasChild, male)

# Let's make it more complex by intersecting with another class
teacher = OWLClass(IRI.create('http://example.com/society#teacher'))
male_teachers_with_children = OWLObjectIntersectionOf([males_with_children, teacher])

# You can render and print owl class expressions in description logics syntax
print(DLSyntaxObjectRenderer().render(male_teachers_with_children)) 
# (∃ hasChild.male) ⊓ teacher
print(owl_expression_to_sparql("?x", male_teachers_with_children))
#  SELECT DISTINCT ?x WHERE {  ?x <http://example.com/society#hasChild> ?s_1 . ?s_1 a <http://example.com/society#male> . ?x a <http://example.com/society#teacher> .  } }
```
For more, you can check the [API documentation](https://ontolearn-docs-dice-group.netlify.app/autoapi/owlapy/#module-owlapy).


Every OWL object that can be used to classify individuals, is considered a class expression and 
inherits from [OWLClassExpression](https://ontolearn-docs-dice-group.netlify.app/autoapi/owlapy/model/#owlapy.model.OWLClassExpression) 
class. In the above examples we have introduced 3 types of class expressions: 
- [OWLClass](https://ontolearn-docs-dice-group.netlify.app/autoapi/owlapy/model/#owlapy.model.OWLClass), 
- [OWLObjectSomeValuesFrom](https://ontolearn-docs-dice-group.netlify.app/autoapi/owlapy/model/#owlapy.model.OWLObjectSomeValuesFrom)
- [OWLObjectIntersectionOf](https://ontolearn-docs-dice-group.netlify.app/autoapi/owlapy/model/#owlapy.model.OWLObjectIntersectionOf).

Like we showed in this example, you can create all kinds of class expressions using the 
OWL objects in [owlapy model](https://ontolearn-docs-dice-group.netlify.app/autoapi/owlapy/model/#module-owlapy.model).
</details>

## How to cite
Currently, we are working on our manuscript describing our framework.
