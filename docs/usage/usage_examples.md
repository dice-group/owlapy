# Basic Usage

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

print(owl_expression_to_sparql(ce))
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
## More tools

Owlapy also provides some useful tools to work with OWL expressions. For example,
you can use [CESimplifier](owlapy.utils.CESimplifier) which is a syntactic class expression simplifier following the 
Unique Name Assumption (UNA) under Close world Assumption (CWA) to simplify class expressions. 
You can directly call the function `simplify_class_expression` which uses a predefined instance of `CESimplifier`.
For interpretability, we will use concepts in description logic (DL) syntax to show the examples.

```python
from owlapy import dl_to_owl_expression, owl_expression_to_dl
from owlapy.utils import simplify_class_expression

ce_dl = "(A ⊓ B) ⊓ (C ⊓ (B ⊔ (C ⊔ E)))"
ce_owl = dl_to_owl_expression(ce_dl, "http://example_namespace.org/")

ce_owl_simplified = simplify_class_expression(ce_owl)
ce_dl_simplified = owl_expression_to_dl(ce_owl_simplified)
print(ce_dl_simplified) # "A ⊓ B ⊓ C"
```

You can get the top-level Disjunctive Normal Form (DNF) or top-level Conjunctive Normal Form (CNF) as shown below:

```python
from owlapy import dl_to_owl_expression, owl_expression_to_dl
from owlapy.utils import get_top_level_dnf, get_top_level_cnf

ce1_dl = "(A ⊔ B) ⊓ (A ⊔ C)"
ce2_dl = "(A ⊓ B) ⊓ (C ⊓ (B ⊔ (C ⊔ E)))"
ce1_owl = dl_to_owl_expression(ce1_dl, "http://example_namespace.org/")
ce2_owl = dl_to_owl_expression(ce2_dl, "http://example_namespace.org/")

ce1_owl_tl_dnf = get_top_level_dnf(ce1_owl)
ce2_owl_tl_cnf = get_top_level_dnf(ce2_owl)

ce1_dl_tl_dnf = owl_expression_to_dl(ce1_owl_tl_dnf)
ce2_dl_tl_cnf = owl_expression_to_dl(ce2_owl_tl_cnf)

print(ce1_dl_tl_dnf) # A ⊔ (A ⊓ B) ⊔ (A ⊓ C) ⊔ (B ⊓ C)
print(ce2_dl_tl_cnf) # (A ⊓ B ⊓ C) ⊔ (A ⊓ B ⊓ C ⊓ E)
```

Get the negation normal form (NNF) simply by calling `get_nnf()` directly from the class expression:

```python
from owlapy import dl_to_owl_expression, owl_expression_to_dl

ce_dl = "¬(A ⊓ (B ⊔ C))"
ce_owl = dl_to_owl_expression(ce_dl, "http://example_namespace.org/")

ce_owl_nnf = ce_owl.get_nnf()
ce_dl_nnf = owl_expression_to_dl(ce_owl_nnf)

print(ce_dl_nnf) # (¬A) ⊔ ((¬B) ⊓ (¬C))
```

You can also measure the length of a class expression using [OWLClassExpressionLengthMetric](owlapy.utils.OWLClassExpressionLengthMetric).
You can set the weights for different types of constructors. We will continue with the default weights 
so we are going to call directly the function `get_expression_length` which uses a predefined instance of 
`OWLClassExpressionLengthMetric`:

```python
from owlapy import dl_to_owl_expression
from owlapy.utils import get_expression_length

ce_dl = "(∀r_1.⊤) ⊓ (∀r_2.(¬C)) ⊓ (∃r_3.{i1 ⊔ i2 ⊔ i5}) ⊓ A"
ce_owl = dl_to_owl_expression(ce_dl, "http://example_namespace.org/")

length = get_expression_length(ce_owl)

print(length) # 14 
```

------------------------------------------------------------------------------------

In these examples we showed a part of **owlapy**. You can explore the
[api documentation](owlapy) to learn more about all classes in owlapy and check more 
examples in the [examples](https://github.com/dice-group/owlapy/tree/main/examples) or [tests](https://github.com/dice-group/owlapy/tree/main/tests) directory 