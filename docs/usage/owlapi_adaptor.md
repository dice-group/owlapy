# Owlapi Adaptor

As mentioned earlier, owlapy is loosely based in [owlapi](https://github.com/owlcs/owlapi),
a library for ontology modification in java.

We have created [OWLAPIAdaptor](owlapy.owlapi_adaptor.OWLAPIAdaptor), 
an adaptor class that facilitates the conversion of
owl class expressions from owlapy to owlapi and vice-versa. 
This adaptor is still considered experimental, and it's in the 
initial phase of development.

We are able to use owlapi via [Jpype](https://jpype.readthedocs.io/en/latest/),
a python module that provides access to Java via python. To start executing 
Java code via jpype, one needs to start the java virtual machine (JVM).
This is automatically done when initializing a `OWLAPIAdaptor` object.

## Initialization

To use the adaptor you have to start the JVM via jpype, which is done automatically 
when you create an _OWLAPIAdaptor_ object. After you are finished you can stop
the JVM by either using `jpype.shutdownJVM()` or the static method from the 
adaptor `stopJVM()`. This will free the resources used by JPype and the java 
packages.

```python
from owlapy.owlapi_adaptor import OWLAPIAdaptor

adaptor = OWLAPIAdaptor("KGs/Family/father.owl")
#  Use the adaptor
print(f"Is the ontology consistent? {adaptor.has_consistent_ontology()}")

#  Stop the JVM
adaptor.stopJVM()
```

In the above code snipped, we created an adaptor for the father ontology 
by passing the local path of that ontology. Then we print whether 
the ontology is consistent or not.

## Notes

An important note is that when initialising the adaptor you are basically
starting a JVM in the background, and therefore you are able to import and 
use java classes as you would do in python. That means that you can 
play around with owlapi code in python as long as your JVM is started.
Isn't that awesome!

`OWLAPIAdaptor` uses HermiT reasoner by default. You can choose between:
"HermiT", "Pellet", "JFact" and "Openllet".

You can use the reasoning method directly from the adaptor but 
for classes that require an [OWLReasoner](owlapi.owl_reasoner.OWLReasoner)
you can use [SyncReasoner](https://dice-group.github.io/owlapy/autoapi/owlapy/owl_reasoner/index.html#owlapy.owl_reasoner.SyncReasoner).

_**owlapi version**: 5.1.9_

## Examples

You can check a usage example in the [_examples_](https://github.com/dice-group/owlapy/tree/develop/examples) folder.

[Test cases](https://github.com/dice-group/owlapy/tree/develop/tests) for the adaptor can also serve as an example, so you can
check that out as well.
