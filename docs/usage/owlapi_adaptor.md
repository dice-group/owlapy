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

To use the adaptor you have to initialize using the `with` statement in python.
This way you will know where the JVM session starts and when it closes:

```python
from owlapy.owlapi_adaptor import OWLAPIAdaptor

with OWLAPIAdaptor("KGs/Family/father.owl") as adaptor:
    #  Use the adaptor
    print(f"Is the ontology consistent? {adaptor.has_consistent_ontology()}")

#  The JVM will shut down when the thread is no longer used.
```

In the above code snipped, we created an adaptor for the father ontology 
by passing the local path of that ontology. Then we print whether 
the ontology is consistent or not.

## Notes

An important note is that when initialising the adaptor you are basically
starting a JVM in the background, and therefore you are able to import and 
use java classes as you would do in python. That means that you can 
play around with owlapi code in python. Isn't that awesome!

`OWLAPIAdaptor` uses HermiT reasoner for methods that require reasoning,
such as `instances`, which returns all individuals belonging to a class
expression.

## Examples

You can check a usage example in the [_examples_](https://github.com/dice-group/owlapy/tree/develop/examples) folder.

[Test cases](https://github.com/dice-group/owlapy/tree/develop/tests) for the adaptor can also serve as an example, so you can
check that out as well.
