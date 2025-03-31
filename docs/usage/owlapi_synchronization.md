# Owlapi Synchronization

As mentioned earlier, _owlapy_ is loosely based in [_OWLAPI_](https://github.com/owlcs/owlapi),
a library for ontology modification in java.

We have created [OWLAPIMapper](owlapy.owlapi_mapper.OWLAPIMapper), 
a mapping class that makes possible the conversion of the most
important classes from _owlapy_ to _owlapi_ and vice-versa. 


We are able to use OWLAPI via [Jpype](https://jpype.readthedocs.io/en/latest/),
a python module that provides access to Java in python. To start executing 
Java code via Jpype, one needs to start the java virtual machine (JVM).
You don't have to worry about it, because if a class is going to use
`OWLAPIMapper` the JVM will start automatically. However, there is the 
function `startJVM` of the `static_functions.py` module if you ever need
to start it manually.

## "Sync" Classes

With the addition of the `OWLAPIMapper`, we introduce two new classes:
- [SyncOntology](owlapy.owl_ontology.SyncOntology)
- [SyncReasoner](owlapy.owl_reasoner.SyncReasoner)

The logic of both these classes is handled by _OWLAPI_ through the
mapper. They inherit from abstract classes already present in owlapy 
(`AbstractOWLOntology` and `AbstractOWLReasoner` respectively) so
the usage is the same as other implementors of these abstract classes.
Additionally, SyncReasoner provides some supplementary methods, such as `infer_axioms` in, 
which infers and returns missing axioms from a given ontology.
For a comprehensive overview of all available methods, refer to the [API](owlapy.owl_reasoner.SyncReasoner) documentation.

To make this guide self-contained, we will go through a simple example
showing how to use the aforementioned classes:

```python
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_axiom import OWLDeclarationAxiom
from owlapy.class_expression import OWLClass
from owlapy.owl_reasoner import SyncReasoner
from owlapy.static_funcs import stopJVM

# (.) Load the 'father' ontology into a SyncOntology object
ontology = SyncOntology("KGs/Family/father.owl")

# (.) Use your ontology as you usually do
# (..) Add a new class
ontology.add_axiom(OWLDeclarationAxiom(OWLClass("http://example.com/father#some_new_class")))
# (..) Print classes in signature
[print(cls) for cls in ontology.classes_in_signature()]

# (.) Create a reasoner and perform some reasoning 
reasoner = SyncReasoner(ontology)

# (..) Check ontology consistency
print(f"Is the ontology consistent? Answer: {reasoner.has_consistent_ontology()}")

# (..) Print all male individuals
[print(ind) for ind in reasoner.instances(OWLClass("http://example.com/father#male"))]

# (.) Stop the JVM if you no longer intend to use "Sync" classes
stopJVM()


```
This was a simple example using the '_father_' ontology to show
just a small part of what you can do with "Sync" classes. 

Notice that after we are done using them we can stop 
the JVM by either using `jpype.shutdownJVM()` or the static function from the 
`static_functions.py` module `stopJVM()`. This will free the resources used by JPype and the java 
packages. Once you stop the JVM it cannot be restarted so make sure you do that
when you are done with the OWLAPI related classes. Stopping the JVM is not
strictly necessary. The resources will be freed once the execution is over, but
in case your code is somehow longer and the "Sync" classes only make up a part of your execution
then you can stop the JVM after it not being needed anymore.


## Notes

An important thing to keep in mind is that when starting the JVM
you are able to import and use java classes as you would do in python (thanks to Jpype). 
That means that you can play around with OWLAPI code in python as long 
as your JVM is started. Isn't that awesome! 

`SyncReasoner` uses HermiT reasoner by default. You can choose between:
"HermiT", "Pellet", "ELK", "JFact" and "Openllet" and "StructuralReasoner". Although no significant 
difference has been noticed between these reasoners, they surely differentiate 
in specific scenarios. You can check OWLAPI's [Wiki](https://github.com/owlcs/owlapi/wiki) for more details.

_**owlapi version**: 5.1.9_

## Examples

You can see usage examples in the [_examples_](https://github.com/dice-group/owlapy/tree/develop/examples) folder.

[Test cases](https://github.com/dice-group/owlapy/tree/develop/tests) can also serve as an example, so you can check them out as well.
