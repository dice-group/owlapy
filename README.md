# owlapy
**Owlapy is loosely based on _owlapi_ - the java counterpart, successfully representing the main
owl objects in python.** 

Other than that, Owlapy also offers some extra functionalities:
- `Owl2SparqlConverter` to convert owl class expressions to SPARQL syntax. 
- `DLSyntaxObjectRenderer` to render owl objects to description logics.
- `ManchesterOWLSyntaxParser` to parse strings of manchester syntax to owl class expression.

For more, you can check the [API documentation](https://ontolearn-docs-dice-group.netlify.app/autoapi/owlapy/#module-owlapy).


## Installation

```shell
pip install owlapy
```

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
```
The following will be printed:

```commandline
(∃ hasChild.male) ⊓ teacher
```

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