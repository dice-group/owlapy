# Reasoners

To validate or infer facts from statements in the ontology, the help of a reasoner
component is required.

For this guide we will also consider the 'father' ontology that we slightly described [here](ontologies.md):

```python
from owlapy.iri import IRI
from owlapy.owl_ontology import Ontology

onto = Ontology(IRI.create("KGs/Family/father.owl"))
```

In Owlapy, we provide two main reasoner classes:


- [**StructuralReasoner**](owlapy.owl_reasoner.StructuralReasoner) (What used to be FastInstanceCheckerReasoner )

    Structural Reasoner is the base reasoner in Owlapy. This reasoner works 
   under CWA/PCWA and the base library used for it is _owlready2_. The functionalities
  of this reasoner are limited and may be incomplete. It does not provide full reasoning in _ALCH_. 
  It provides support for finding instance of complex class expression.
  It has a cache storing system that allows for faster execution of some reasoning functionalities.

    **Initialization:**

    ```python
    from owlapy.owl_reasoner import StructuralReasoner
    
    structural_reasoner = StructuralReasoner(onto, property_cache = True, negation_default = True, sub_properties = False)
    ```
  The structural reasoner requires an ontology ([AbstractOWLOntology](owlapy.abstracts.AbstractOWLOntology)).
  `property_cache` specifies whether to cache property values. This
  requires more memory, but it speeds up the reasoning processes. If `negation_default` argument is set
  to `True` the missing facts in the ontology means false. The argument
    `sub_properties` is another boolean argument to specify whether you want to take sub properties in consideration
  for `instances()` method.


- [**SyncReasoner**](owlapy.owl_reasoner.SyncReasoner)
  
  SyncReasoner is a class that serves as a 'syncing' class 
  between our framework and reasoners in _owlapi_. It
  can perform full reasoning in _ALCH_ due to the use of well-known reasoners such as HermiT, Pellet, ELK etc. 
  SyncReasoner is more useful when your main goal is reasoning over the ontology,
  and you are familiarized with the java reasoners (HermiT, Pellet, ELK, JFact, ...).

    **Initialization:**

    ```python
    from owlapy.owl_reasoner import SyncReasoner
    
    sync_reasoner = SyncReasoner(ontology="KGs/Mutagenesis/mutagenesis.owl", reasoner="HermiT")
    ```
    
    SyncReasoner is made available by [OWLAPI mapper](owlapi_synchronization.md) and requires the ontology path or an
    object of type [SyncOntology](owlapy.owl_ontology.SyncOntology),
    together with a reasoner name from the possible set of reasoners: `"Hermit"`, `"Pellet"`, `"ELK"`, `"JFact"`, 
   `"Openllet"`, `"Structural"` specified as a string value.

   **Note that SyncReasoner with `reasoner` argument set to `"Structural"` is referring to 
   _StructuralReasoner_ implemented in OWLAPI. That is different from our StructuralReasoner.**

  **Also is worth mentioning that some java reasoners like ELK do not implement all methods that a reasoner 
  can perform. You will get a `NotImplementedError` if you try to use them. Note that we use these reasoners via jar
  distributions, and we do not consider updating them. But in such cases we keep an eye open for new releases 
  that may address these limitations.**

- [**EBR**](owlapy.owl_reasoner.EBR)
  
  Embedding-based reasoner (EBR) is a native Python model that leverages knowledge graph embeddings for inference, 
  which instead of strict logical deduction, uses the model's scoring function to approximate reasoning tasks, such 
  as retrieving instances of class expressions. For example, to find instances of a class C, EBR identifies 
  individuals x for which the triple `(x, rdf:type, C)` receives a score above a given **threshold**. 
  This approach extends compositionally to handle arbitaray complex expression in SROIQ by combining the instances 
  retrieved for their constituent parts. 

    **Initialization:**
  
  ```python
  from owlapy.owl_reasoner import EBR
  from owlapy.owl_ontology import NeuralOntology
  
  onto = NeuralOntology(path_neural_embedding="KGs/Family/trained_model")
  sync_reasoner = EBR(ontology=onto)
  ```
    EBR requires only 1 argument to initialize and that is a `NeuralOntology`. 
  
## Usage of the Reasoner
All the reasoners available in Owlapy inherit from the
class: [AbstractOWLReasoner](owlapy.abstracts.AbstractOWLReasoner).
Further on, in this guide, we use [StructuralReasoner](owlapy.owl_reasoner.StructuralReasoner)
to show the capabilities of a reasoner in Owlapy.

We will proceed to use the _father_ dataset to give examples.


## Class Reasoning

Using an [AbstractOWLOntology](owlapy.abstracts.AbstractOWLOntology) you can list all the classes in the signature, 
but a reasoner can give you more than that. You can get the subclasses, superclasses or the 
equivalent classes of a class in the ontology:

<!--pytest-codeblocks:cont-->

```python
from owlapy.class_expression import OWLClass
from owlapy.iri import IRI

namespace = "http://example.com/father#"
male = OWLClass(IRI(namespace, "male"))

male_super_classes = structural_reasoner.super_classes(male)
male_sub_classes = structural_reasoner.sub_classes(male)
male_equivalent_classes = structural_reasoner.equivalent_classes(male)
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

>**NOTE**: In SyncReasoner, there is no use for the argument `only_named` as this is not
> supported by methods in the java library OWLAPI. 

You can get all the types of a certain individual using `types` method:

<!--pytest-codeblocks:cont-->

```python
anna = list(onto.individuals_in_signature()).pop(0)

anna_types = structural_reasoner.types(anna)
```

We retrieve _anna_ as the first individual on the list of individuals 
of the 'Father' ontology. The `type` method only returns named classes.


## Object Properties and Data Properties Reasoning
Owlapy reasoners offers some convenient methods for working with object properties and 
data properties. Below we show some of them, but you can always check all the methods in the 
[AbstractOWLReasoner](owlapy.abstracts.AbstractOWLReasoner)
class documentation. 

You can get all the object properties that an individual has by using the 
following method:

<!--pytest-codeblocks:cont-->
```python
anna = individuals[0] 
object_properties = structural_reasoner.ind_object_properties(anna)
```
In this example, `object_properties` contains all the object properties
that _anna_ has, which in our case would only be _hasChild_.
Now we can get the individuals of this object property for _anna_.

<!--pytest-codeblocks:cont-->
```python
for op in object_properties:
    object_properties_values = structural_reasoner.object_property_values(anna, op)
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

equivalent_to_hasChild = structural_reasoner.equivalent_object_properties(hasChild)
hasChild_sub_properties = structural_reasoner.sub_object_properties(hasChild)
```

In case you want to get the domains and ranges of an object property use the following:

<!--pytest-codeblocks:cont-->
```python
hasChild_domains = structural_reasoner.object_property_domains(hasChild)
hasChild_ranges = structural_reasoner.object_property_ranges(hasChild)
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
male_individuals = structural_reasoner.instances(male)
for ind in male_individuals:
    print(ind)
```

## Infer and validate facts

With **SyncReasoner** you can also infer missing facts from the ontology by using the method `infer_axioms`, check for
consistency of the ontology (`has_consistent_ontology`), check satisfiability of a class expression (`is_satisfiable`)
and more. See [SyncReasoner API](owlapy.owl_reasoner.SyncReasoner) for more detail.

## Serve SyncReasoner
Using the CLI command `owlapy-serve` you can start a server hosting Owlapy API via FastAPI to use such 
functionalities offered by SyncReasoner:

```shell
owlapy-serve --path_kb KGs/Family/family-benchmark_rich_background.owl --reasoner HermiT
```

Optionally, you provide custom host and port for the FastAPI server:

```shell
owlapy-serve --path_kb KGs/Family/family-benchmark_rich_background.owl --reasoner HermiT --host 0.0.0.0 --port 8000
```

-----------------------------------------------------------------------

In this guide we covered the main functionalities of the reasoners in Owlapy. 
In the next one, we speak about OWLAPI synchronization and how can make use of OWLAPI in Owlapy.



