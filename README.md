# OWLpy: OWL in Python


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

In this example we start with a simple atomic class expression and move to some more complex 
ones and finally render and print the last of them in description logics syntax.

```python
from owlapy.render import DLSyntaxObjectRenderer
from owlapy.model import IRI, OWLClass, OWLObjectProperty, OWLObjectSomeValuesFrom, \
                         OWLObjectIntersectionOf

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
print(Owl2SparqlConverter().as_query("?x", male_teachers_with_children))
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


### Are you looking for more?

The java _owlapi_ library also offers classes for OWL ontology, manager and reasoner. 
We have also implemented those classes in python, but for the time being we are 
not including them in owlapy. You can find all of those classes in
[Ontolearn](https://github.com/dice-group/Ontolearn/tree/develop), which is a 
python library that offers more than just that.

In case you have any question or request please don't hesitate to open an issue.