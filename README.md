# owlapy
**Version: 0.1.0**

Owlapy is loosely based on owlapi, successfully representing the main
owl objects in python. 

Other than that, Owlapy also offers some extra functionalities:
- `Owl2SparqlConverter` to convert owl class expressions to SPARQL syntax. 
- `DLSyntaxObjectRenderer` to render owl objects to description logics.
- `ManchesterOWLSyntaxParser` to parse strings of manchester syntax to owl class expression.

For more, please feel free to explore the project for yourself which is made
easier due to the well documented code.


## Installation

```shell
pip install owlapy
```

## Usage

```python
from owlapy.render import DLSyntaxObjectRenderer
from owlapy.namespaces import Namespaces
from owlapy.model import IRI, OWLClass, OWLObjectProperty, OWLObjectSomeValuesFrom, \
                         OWLObjectIntersectionOf

# defining the ontology namespace with prefix 'ex'
NS = Namespaces("ex", "http://example.com/society#")

# create the iri referring to 'male' class
male_iri = IRI.create(NS,'male')

# create the male class
male = OWLClass(male_iri)

# create an object property
hasChild = OWLObjectProperty(IRI.create(NS,'hasChild'))

# create an existential restrictions
males_with_children = OWLObjectSomeValuesFrom(hasChild, male)

#let's make it more complex by intersecting with another class
teacher = OWLClass(IRI.create(NS ,'teacher'))
male_teachers_with_children = OWLObjectIntersectionOf([males_with_children, teacher])

# This can be printed in description logics
print(DLSyntaxObjectRenderer().render(male_teachers_with_children))
```
The following will be printed:

```commandline
(∃ hasChild.male) ⊓ teacher
```

Like we showed in this example, you can create more complex class expressions, and there 
are a lot of other OWL objects in owlapy model that you can use.

### Are you looking for more?

The java _owlapi_ library also offers classes for OWL ontology, manager and reasoner. 
We have also implemented those classes in python, but for the time being we are 
not including them in owlapy. You can find all of those classes in
[Ontolearn](https://github.com/dice-group/Ontolearn/tree/develop), which is a 
python library that offers more than just that.

In case you have any question or request please don't hesitate to open an issue.