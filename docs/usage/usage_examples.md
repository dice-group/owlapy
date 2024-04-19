# Usage

The main usage for owlapy is to use it for class expression construction. Class 
expression learning algorithms require such basic structure to work upon. Let's walk 
through an example of constructing some class expressions. 

In this example we will be using the _family_ ontology,
a simple ontology with namespace: `http://example.com/family#`.
Here is a hierarchical diagram that shows the classes and their relationship:

             Thing
               |
            person
           /   |   
       male  female

It contains only one object property which is `hasChild` and in total there 
are six persons (individuals), of which four are males and two are females.

## Atomic Classes

To represent the classes `male`, `female`, and `person` we can simply use the 
class [OWLClass](https://dice-group.github.io/owlapy/autoapi/owlapy/class_expression/owl_class/index.html#owlapy.class_expression.owl_class.OWLClass):

```python
from owlapy.class_expression import OWLClass
from owlapy.iri import IRI

namespace = "http://example.com/family#"

male = OWLClass(IRI(namespace, "male"))
female = OWLClass(IRI(namespace, "female"))
person = OWLClass(IRI(namespace, "person"))

```

Notice that we created an `IRI` object for every class. [IRI](https://dice-group.github.io/owlapy/autoapi/owlapy/iri/index.html#owlapy.iri.IRI)
is used to represent an _IRI_. Every named entity requires an IRI, whereas Anonymous entities does not. 
However, in owlapy you can create an _OWLClass_ by passing the _IRI_ directly as a string, like so:

```python
male = OWLClass("http://example.com/family#male")
```

## Object Property

To represent the object property `hasChild` we can use the class 
[OWLObjectProperty](https://dice-group.github.io/owlapy/autoapi/owlapy/owl_property/index.html#owlapy.owl_property.OWLObjectProperty):

```python
from owlapy.owl_property import OWLObjectProperty

hasChild = OWLObjectProperty("http://example.com/family#hasChild")
```

> **Tip:** In owlapy the naming of the classes is made in accordance with the notations from
> OWL 2 specification but with the word _"OWL"_ in the beginning. Example: _"OWLObjectProperty"_
> represents the notation _"ObjectProperty"_.

## Complex class expressions

Now that we have these atomic entities, we can construct more complex class 
expressions. Let's say we want to represent all individuals which are `male` 
and have at least 1 child.

We already have the concept of `male`. We need to find the appropriate class
for the second part: _"have at least 1 child"_. In OWL 2 specification that would be
[ObjectMinCardinality](https://www.w3.org/TR/owl2-syntax/#Minimum_Cardinality). In owlapy,
as we said, we simply add the word _"OWL"_ upfront to find the correct class:

```python
from owlapy.class_expression import OWLObjectMinCardinality

has_at_least_one_child = OWLObjectMinCardinality(
    cardinality = 1, 
    property = hasChild,
    filler = person
)
```
As you can see, to create an object of class [OWLObjectMinCardinality](https://dice-group.github.io/owlapy/autoapi/owlapy/class_expression/restriction/index.html#owlapy.class_expression.restriction.OWLObjectMinCardinality)
is as easy as that. You specify the cardinality which in this case is `1`, the object property where we apply this 
cardinality restriction and the filler class in case you want to restrict the domain of the class expression. In this
case we used `person`.

Now let's merge both class expressions together using [OWLObjectIntersectionOf](https://dice-group.github.io/owlapy/autoapi/owlapy/class_expression/nary_boolean_expression/index.html#owlapy.class_expression.nary_boolean_expression.OWLObjectIntersectionOf):

```python
from owlapy.class_expression import OWLObjectIntersectionOf

ce = OWLObjectIntersectionOf([male, has_at_least_one_child])
```

## Convert to SPARQL, DL or Manchester syntax

Owlapy is not just a library to represent OWL entities, you can also
use it to convert owl expressions into other formats:

```python
from owlapy import owl_expression_to_sparql, owl_expression_to_dl, owl_expression_to_manchester

print(owl_expression_to_dl(ce))
# Result: male ⊓ (≥ 1 hasChild.person)

print(owl_expression_to_sparql(expression=ce))
# Result: SELECT DISTINCT ?x WHERE { ?x a <http://example.com/family#male> . { SELECT ?x WHERE { ?x <http://example.com/family#hasChild> ?s_1 . ?s_1 a <http://example.com/family#person> .  } GROUP BY ?x HAVING ( COUNT ( ?s_1 ) >= 1 ) } }

print(owl_expression_to_manchester(ce))
# Result: male and (hasChild min 1 person)
```

To parse a DL or Manchester expression to owl expression you can use the 
following convenient methods:

```python
from owlapy import dl_to_owl_expression, manchester_to_owl_expression

print(dl_to_owl_expression("∃ hasChild.male", namespace))
# Result: OWLObjectSomeValuesFrom(property=OWLObjectProperty(IRI('http://example.com/family#','hasChild')),filler=OWLClass(IRI('http://example.com/family#','male')))

print(manchester_to_owl_expression("female and (hasChild max 2 person)", namespace))
# Result: OWLObjectIntersectionOf((OWLClass(IRI('http://example.com/family#','female')), OWLObjectMaxCardinality(property=OWLObjectProperty(IRI('http://example.com/family#','hasChild')),2,filler=OWLClass(IRI('http://example.com/family#','person')))))

```

In these examples we showed a fraction of **owlapy**. You can explore the
[api documentation](owlapy) to learn more about all classes in owlapy.