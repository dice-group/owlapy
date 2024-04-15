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
from owlapy.iri import IRI
from owlapy.class_expression import OWLClass, OWLObjectIntersectionOf, OWLObjectSomeValuesFrom
from owlapy.owl_property import OWLObjectProperty
from owlapy.converter import owl_expression_to_sparql
from owlapy.render import owl_expression_to_dl

# Create the male class
male = OWLClass("http://example.com/society#male")

# Create an object property using the iri as a string for 'hasChild' property.
hasChild = OWLObjectProperty("http://example.com/society#hasChild")

# Create an existential restrictions
males_with_children = OWLObjectSomeValuesFrom(hasChild, male)

# Let's make it more complex by intersecting with another class
teacher = OWLClass("http://example.com/society#teacher")
male_teachers_with_children = OWLObjectIntersectionOf([males_with_children, teacher])

# You can render and print owl class expressions in description logics syntax (and vice-versa)
print(owl_expression_to_dl(male_teachers_with_children))
# (∃ hasChild.male) ⊓ teacher
print(owl_expression_to_sparql("?x", male_teachers_with_children))
#  SELECT DISTINCT ?x WHERE {  ?x <http://example.com/society#hasChild> ?s_1 . ?s_1 a <http://example.com/society#male> . ?x a <http://example.com/society#teacher> .  } }
```
For more, you can check the [API documentation](https://dice-group.github.io/owlapy/autoapi/owlapy/index.html).


Every OWL object that can be used to classify individuals, is considered a class expression and 
inherits from [OWLClassExpression](https://dice-group.github.io/owlapy/autoapi/owlapy/class_expression/class_expression/index.html#owlapy.class_expression.class_expression.OWLClassExpression) 
class. In the above examples we have introduced 3 types of class expressions: 
- [OWLClass](https://dice-group.github.io/owlapy/autoapi/owlapy/class_expression/owl_class/index.html#owlapy.class_expression.owl_class.OWLClass), 
- [OWLObjectSomeValuesFrom](https://dice-group.github.io/owlapy/autoapi/owlapy/class_expression/restriction/index.html#owlapy.class_expression.restriction.OWLObjectSomeValuesFrom)
- [OWLObjectIntersectionOf](https://dice-group.github.io/owlapy/autoapi/owlapy/class_expression/nary_boolean_expression/index.html#owlapy.class_expression.nary_boolean_expression.OWLObjectIntersectionOf).

Like we showed in this example, you can create all kinds of class expressions using the 
OWL objects in [owlapy api](https://dice-group.github.io/owlapy/autoapi/owlapy/index.html).
</details>

## How to cite
Currently, we are working on our manuscript describing our framework.
