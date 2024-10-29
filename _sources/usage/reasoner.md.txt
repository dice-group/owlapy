# Reasoners

To validate facts about statements in the ontology, the help of a reasoner
component is required.

For this guide we will also consider the 'father' ontology that we slightly described [here](ontologies.md):

```python
from owlapy.iri import IRI
from owlapy.owl_ontology_manager import OntologyManager

manager = OntologyManager()
onto = manager.load_ontology(IRI.create("KGs/Family/father.owl"))
```

In our Owlapy library, we provide several **reasoners** to choose
from:

- [**OntologyReasoner**](owlapy.owl_reasoner.OntologyReasoner)

    Or differently Structural Reasoner, is the base reasoner in Owlapy. The functionalities
  of this reasoner are limited. It does not provide full reasoning in _ALCH_. Furthermore,
  it has no support for instances of complex class expressions, which is covered by the
  other reasoners (SyncReasoner and FIC). This reasoner is used as
  a base reasoner for FIC which overwrites the `instances` method. 
  We recommend using the other reasoners for any reasoning tasks.

    **Initialization:**

   ```python
   from owlapy.owl_reasoner import OntologyReasoner
   
   structural_reasoner = OntologyReasoner(onto)
   ```

    The structural reasoner requires an ontology ([OWLOntology](owlapy.owl_ontology.OWLOntology)).
    


- [**SyncReasoner**](owlapy.owl_reasoner.SyncReasoner)

    Can perform full reasoning in _ALCH_ due to the use of reasoners from 
  owlapi like HermiT, Pellet, etc. and provides support for
  complex class expression instances (when using the method `instances`). 
  SyncReasoner is more useful when your main goal is reasoning over the ontology,
  and you are familiarized with the java reasoners (HermiT, Pellet, ...).

    **Initialization:**

    ```python
    from owlapy.owl_reasoner import SyncReasoner
    
    sync_reasoner = SyncReasoner(ontology_path="KGs/Mutagenesis/mutagenesis.owl", reasoner="HermiT")
    ```
    
    Sync Reasoner is made available by [owlapi mapper](owlapi_adaptor.md) and requires the ontology path
    together with a reasoner name from the possible set of reasoners: `"Hermit"`, `"Pellet"`, `"JFact"`, `"Openllet"`.


- [**FastInstanceCheckerReasoner**](owlapy.owl_reasoner.FastInstanceCheckerReasoner) **(FIC)**

    FIC also provides support for complex class expression but the rest of the methods are the same as in
  the base reasoner.
  It has a cache storing system that allows for faster execution of some reasoning functionalities. Due to this
  feature, FIC is more appropriate to be used in concept learning.

    **Initialization:**

    ```python
    from owlapy.owl_reasoner import FastInstanceCheckerReasoner
    
    fic_reasoner = FastInstanceCheckerReasoner(onto, structural_reasoner, property_cache = True,
                                                   negation_default = True, sub_properties = False)
    ```
    Besides the ontology, FIC requires a base reasoner to delegate any reasoning tasks not covered by it.
  This base reasoner
  can be any other reasoner in Owlapy (usually it's [OntologyReasoner](owlapy.owl_reasoner.OntologyReasoner)).
  `property_cache` specifies whether to cache property values. This
  requires more memory, but it speeds up the reasoning processes. If `negation_default` argument is set
  to `True` the missing facts in the ontology means false. The argument
    `sub_properties` is another boolean argument to specify whether you want to take sub properties in consideration
  for `instances()` method.

## Usage of the Reasoner
All the reasoners available in the Owlapy library inherit from the
class: [OWLReasonerEx](owlapy.owl_reasoner.OWLReasonerEx). This class provides some 
extra convenient methods compared to its base abstract class [OWLReasoner](owlapy.owl_reasoner.OWLReasoner).
Further on, in this guide, we use [FastInstanceCheckerReasoner](owlapy.owl_reasoner.FastInstanceCheckerReasoner)
to show the capabilities of a reasoner in Owlapy.

As mentioned earlier we will use the _father_ dataset to give examples.


## Class Reasoning

Using an [OWLOntology](owlapy.owl_ontology.OWLOntology) you can list all the classes in the signature, 
but a reasoner can give you more than that. You can get the subclasses, superclasses or the 
equivalent classes of a class in the ontology:

<!--pytest-codeblocks:cont-->

```python
from owlapy.class_expression import OWLClass
from owlapy.iri import IRI

namespace = "http://example.com/father#"
male = OWLClass(IRI(namespace, "male"))

male_super_classes = fic_reasoner.super_classes(male)
male_sub_classes = fic_reasoner.sub_classes(male)
male_equivalent_classes = fic_reasoner.equivalent_classes(male)
```

We define the _male_ class by creating an [OWLClass](owlapy.class_expression.owl_class.OWLClass) object. The 
methods `super_classes` and `sub_classes` have 2 more boolean arguments: `direct` and `only_named`. 
If `direct=True` then only the direct classes in the 
hierarchy will be returned, else it will return every class in the hierarchy depending 
on the method(sub_classes or super_classes).
By default, its value is _False_. 
The next argument `only_named` specifies whether you want
to show only named classes or complex classes as well. By default, its value is _True_ which 
means that it will return only the named classes.

>**NOTE**: The extra arguments `direct` and `only_named` are also used in other methods that reason
upon the class, object property, or data property hierarchy.

>**NOTE**: SyncReasoner implements OWLReasoner where we can specify the `only_named` argument
> in some methods but in java reasoners there is no use for such argument and therefore this
> argument is trivial when used in SyncReasoner's methods. 

You can get all the types of a certain individual using `types` method:

<!--pytest-codeblocks:cont-->

```python
anna = list(onto.individuals_in_signature()).pop(0)

anna_types = fic_reasoner.types(anna)
```

We retrieve _anna_ as the first individual on the list of individuals 
of the 'Father' ontology. The `type` method only returns named classes.


## Object Properties and Data Properties Reasoning
Owlapy reasoners offers some convenient methods for working with object properties and 
data properties. Below we show some of them, but you can always check all the methods in the 
[OWLReasoner](owlapy.owl_reasoner.OWLReasoner)
class documentation. 

You can get all the object properties that an individual has by using the 
following method:

<!--pytest-codeblocks:cont-->
```python
anna = individuals[0] 
object_properties = fic_reasoner.ind_object_properties(anna)
```
In this example, `object_properties` contains all the object properties
that _anna_ has, which in our case would only be _hasChild_.
Now we can get the individuals of this object property for _anna_.

<!--pytest-codeblocks:cont-->
```python
for op in object_properties:
    object_properties_values = fic_reasoner.object_property_values(anna, op)
    for individual in object_properties_values:
        print(individual)
```

In this example we iterated over the `object_properties`, assuming that there
are more than 1, and we use the reasoner
to get the values for each object property `op` of the individual `anna`. The values 
are individuals which we store in the variable `object_properties_values` and are 
printed in the end. The method `object_property_values` requires as the
first argument, an [OWLNamedIndividual](owlapy.owl_individual.OWLNamedIndividual) that is the subject of the object property values and 
the second argument an [OWLObjectProperty](owlapy.owl_property.OWLObjectProperty) whose values are to be retrieved for the 
specified individual.  

> **NOTE:** You can as well get all the data properties of an individual in the same way by using 
`ind_data_properties` instead of `ind_object_properties` and `data_property_values` instead of 
`object_property_values`. Keep in mind that `data_property_values` returns literal values 
(type of [OWLLiteral](owlapy.owl_literal.OWLLiteral)).

In the same way as with classes, you can also get the sub object properties or equivalent object properties.

<!--pytest-codeblocks:cont-->

```python
from owlapy.owl_property import OWLObjectProperty

hasChild = OWLObjectProperty(IRI(namespace, "hasChild"))

equivalent_to_hasChild = fic_reasoner.equivalent_object_properties(hasChild)
hasChild_sub_properties = fic_reasoner.sub_object_properties(hasChild)
```

In case you want to get the domains and ranges of an object property use the following:

<!--pytest-codeblocks:cont-->
```python
hasChild_domains = fic_reasoner.object_property_domains(hasChild)
hasChild_ranges = fic_reasoner.object_property_ranges(hasChild)
```

> **NOTE:** Again, you can do the same for data properties but instead of the word 'object' in the 
> method name you should use 'data'.


## Find Instances

The method `instances` is a very convenient method. It takes only 1 argument that is basically
a class expression and returns all the individuals belonging to that class expression. In Owlapy 
we have implemented a Python class for each type of class expression.
The argument is of type [OWLClassExpression](owlapy.class_expression.class_expression.OWLClassExpression).

Let us now show a simple example by finding the instances of the class _male_ and printing them:

<!--pytest-codeblocks:cont-->
```python
male_individuals = fic_reasoner.instances(male)
for ind in male_individuals:
    print(ind)
```

-----------------------------------------------------------------------

In this guide we covered the main functionalities of the reasoners in Owlapy. 
In the next one, we speak about owlapi adaptor and how can make use of owlapi in owlapy.



