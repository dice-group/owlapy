# OWLAPY

OWLAPY is a Python Framework that serves as a base structure for creating and manipulating 
OWL Ontologies. 

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


## Usage

In this example we start with a simple atomic class expression and move to some more complex 
ones and finally render and print the last of them in description logics syntax.

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

## How to cite
Currently, we are working on our manuscript describing our framework.
