# Reasoners

To validate facts about statements in the ontology, the help of a reasoner
component is required.

For this guide we will also consider the 'father' ontology that we slightly described [here](ontologies.md):

```python
from owlapy.owl_ontology_manager import OntologyManager

manager = OntologyManager()
onto = manager.load_ontology(IRI.create("KGs/Family/father.owl"))
```

In our Owlapy library, we provide several **reasoners** to choose
from. Currently, there are the following reasoners available: 

- [**OntologyReasoner**](owlapy.owl_reasoner.OntologyReasoner)

    Or differently Structural Reasoner, is the base reasoner in Owlapy. The functionalities
  of this reasoner are limited. It does not provide full reasoning in _ALCH_. Furthermore,
  it has no support for instances of complex class expressions, which is covered by the
  other reasoners (SyncReasoner and FIC). We recommend to use the other reasoners for any heavy reasoning tasks.

    **Initialization:**

   ```python
   from owlapy.owl_reasoner import OntologyReasoner
   
   structural_reasoner = OntologyReasoner(onto)
   ```

    The structural reasoner requires an ontology ([OWLOntology](owlapy.owl_ontology.OWLOntology)).
  The second argument is `isolate` argument which isolates the world (therefore the ontology) where the reasoner is
  performing the reasoning. More on that on _[Reasoning Details](reasoning_details.md#isolated-world)_.
    


- [**SyncReasoner**](owlapy.owl_reasoner.SyncReasoner)

    Can perform full reasoning in _ALCH_ due to the use of HermiT/Pellet and provides support for
  complex class expression instances (when using the method `instances`). SyncReasoner is more useful when
  your main goal is reasoning over the ontology.

    **Initialization:**

    ```python
    from owlapy.owl_reasoner import SyncReasoner, BaseReasoner
    
    sync_reasoner = SyncReasoner(onto, BaseReasoner.HERMIT, infer_property_values = True)
    ```
    
    Sync Reasoner requires an ontology and a base reasoner of type [BaseReasoner](owlapy.owl_reasoner.BaseReasoner)
    which is just an enumeration with two possible values: `BaseReasoner.HERMIT` and `BaseReasoner.PELLET`.
  You can set the `infer_property_values` argument to `True` if you want the reasoner to infer
  property values. `infer_data_property_values` is an additional argument when the base reasoner is set to 
    `BaseReasoner.PELLET`. The argument `isolated` is inherited from the base class


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
  can be any other reasoner in Owlapy. `property_cache` specifies whether to cache property values. This
  requires more memory, but it speeds up the reasoning processes. If `negation_default` argument is set
  to `True` the missing facts in the ontology means false. The argument
    `sub_properties` is another boolean argument to specify whether you want to take sub properties in consideration
  for `instances()` method.

## Usage of the Reasoner
All the reasoners available in the Owlapy library inherit from the
class: [OWLReasonerEx](owlapy.owl_reasoner.OWLReasonerEx). This class provides some 
extra convenient methods compared to its base class [OWLReasoner](owlapy.owl_reasoner.OWLReasoner), which is an 
abstract class.
Further on, in this guide, we use 
[SyncReasoner](owlapy.owl_reasoner.SyncReasoner).
to show the capabilities of a reasoner in Owlapy.

To give examples we consider the _father_ dataset. 
If you are not already familiar with this small dataset,
you can find an overview of it [here](ontologies.md).


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

male_super_classes = sync_reasoner.super_classes(male)
male_sub_classes = sync_reasoner.sub_classes(male)
male_equivalent_classes = sync_reasoner.equivalent_classes(male)
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

You can get all the types of a certain individual using `types` method:

<!--pytest-codeblocks:cont-->

```python
anna = list(onto.individuals_in_signature()).pop()

anna_types = sync_reasoner.types(anna)
```

We retrieve _anna_ as the first individual on the list of individuals 
of the 'Father' ontology. The `type` method only returns named classes.


## Object Properties and Data Properties Reasoning
Owlapy reasoners offers some convenient methods for working with object properties and 
data properties. Below we show some of them, but you can always check all the methods in the 
[SyncReasoner](owlapy.owl_reasoner.SyncReasoner)
class documentation. 

You can get all the object properties that an individual has by using the 
following method:

<!--pytest-codeblocks:cont-->
```python
anna = individuals[0] 
object_properties = sync_reasoner.ind_object_properties(anna)
```
In this example, `object_properties` contains all the object properties
that _anna_ has, which in our case would only be _hasChild_.
Now we can get the individuals of this object property for _anna_.

<!--pytest-codeblocks:cont-->
```python
for op in object_properties:
    object_properties_values = sync_reasoner.object_property_values(anna, op)
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

equivalent_to_hasChild = sync_reasoner.equivalent_object_properties(hasChild)
hasChild_sub_properties = sync_reasoner.sub_object_properties(hasChild)
```

In case you want to get the domains and ranges of an object property use the following:

<!--pytest-codeblocks:cont-->
```python
hasChild_domains = sync_reasoner.object_property_domains(hasChild)
hasChild_ranges = sync_reasoner.object_property_ranges(hasChild)
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
male_individuals = sync_reasoner.instances(male)
for ind in male_individuals:
    print(ind)
```

-----------------------------------------------------------------------

In this guide we covered the main functionalities of the reasoners in Owlapy. More
details are provided in the next guide.



