from functools import singledispatchmethod
import jpype.imports

from owlapy.iri import IRI
from owlapy.owl_property import OWLObjectProperty

if jpype.isJVMStarted():
    from uk.ac.manchester.cs.owl.owlapi import OWLObjectPropertyImpl
    from org.semanticweb.owlapi.model import IRI as owlapi_IRI
else:
    raise ImportError("Jpype JVM is not started!")

class OWLAPIMapper():

    def __init__(self):
        self.nothing = "nothing"
    @singledispatchmethod
    def map_(self, expression):
        pass


    @map_.register
    def _(self, expression: OWLObjectProperty):
        return OWLObjectPropertyImpl(owlapi_IRI.create(expression.str))


    @map_.register
    def _(self, expression: OWLObjectPropertyImpl):
        return OWLObjectProperty(IRI.create(str(expression.getIRI().getIRIString())))
