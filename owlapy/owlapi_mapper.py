from functools import singledispatchmethod
import jpype.imports

from owlapy import owl_expression_to_manchester, manchester_to_owl_expression
from owlapy.class_expression import OWLClassExpression
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty

if jpype.isJVMStarted():
    from uk.ac.manchester.cs.owl.owlapi import OWLObjectPropertyImpl, OWLDataPropertyImpl, OWLNamedIndividualImpl
    from org.semanticweb.owlapi.model import IRI as owlapi_IRI
    from org.semanticweb.owlapi.manchestersyntax.parser import ManchesterOWLSyntaxClassExpressionParser
    from org.semanticweb.owlapi.manchestersyntax.renderer import ManchesterOWLSyntaxOWLObjectRendererImpl
    from org.semanticweb.owlapi.util import BidirectionalShortFormProviderAdapter, SimpleShortFormProvider
    from org.semanticweb.owlapi.expression import ShortFormEntityChecker
    from java.util import HashSet
    from uk.ac.manchester.cs.owl.owlapi import (OWLAnonymousClassExpressionImpl, OWLCardinalityRestrictionImpl,
                                                OWLClassExpressionImpl, OWLClassImpl, OWLDataAllValuesFromImpl,
                                                OWLDataCardinalityRestrictionImpl, OWLDataExactCardinalityImpl,
                                                OWLDataHasValueImpl, OWLDataMaxCardinalityImpl,
                                                OWLDataMinCardinalityImpl, OWLDataSomeValuesFromImpl,
                                                OWLNaryBooleanClassExpressionImpl, OWLObjectAllValuesFromImpl,
                                                OWLObjectCardinalityRestrictionImpl, OWLObjectComplementOfImpl,
                                                OWLObjectExactCardinalityImpl, OWLObjectHasSelfImpl,
                                                OWLObjectHasValueImpl, OWLObjectIntersectionOfImpl,
                                                OWLObjectMaxCardinalityImpl, OWLObjectMinCardinalityImpl,
                                                OWLObjectOneOfImpl, OWLObjectSomeValuesFromImpl,
                                                OWLObjectUnionOfImpl, OWLQuantifiedDataRestrictionImpl,
                                                OWLQuantifiedObjectRestrictionImpl, OWLQuantifiedRestrictionImpl,
                                                OWLValueRestrictionImpl)
else:
    raise ImportError("Jpype JVM is not started! Tip: Import OWLAPIMapper after JVM has started")


class OWLAPIMapper:

    def __init__(self, ontology):
        self.ontology = ontology
        self.manager = ontology.getOWLOntologyManager()

        # () Get the name space.
        self.namespace = self.ontology.getOntologyID().getOntologyIRI().orElse(None)
        if self.namespace is not None:
            self.namespace = str(self.namespace)
            if self.namespace[-1] not in ["/", "#", ":"]:
                self.namespace += "#"
        else:
            self.namespace = "http://www.anonymous.org/anonymous#"

        # () Create a manchester parser and a renderer.
        ontology_set = HashSet()
        ontology_set.add(self.ontology)
        bidi_provider = BidirectionalShortFormProviderAdapter(self.manager, ontology_set, SimpleShortFormProvider())
        entity_checker = ShortFormEntityChecker(bidi_provider)
        self.parser = ManchesterOWLSyntaxClassExpressionParser(self.manager.getOWLDataFactory(), entity_checker)
        self.renderer = ManchesterOWLSyntaxOWLObjectRendererImpl()

    @singledispatchmethod
    def map_(self, e):
        """ (owlapy <--> owlapi) entity mapping.

        Args:
            e: OWL entity/expression.
        """
        pass

    @map_.register
    def _(self, e: OWLObjectProperty):
        return OWLObjectPropertyImpl(owlapi_IRI.create(e.str))

    @map_.register
    def _(self, e: OWLObjectPropertyImpl):
        return OWLObjectProperty(IRI.create(str(e.getIRI().getIRIString())))

    @map_.register
    def _(self, e: OWLDataProperty):
        return OWLDataPropertyImpl(owlapi_IRI.create(e.str))

    @map_.register
    def _(self, e: OWLDataPropertyImpl):
        return OWLDataProperty(IRI.create(str(e.getIRI().getIRIString())))

    @map_.register
    def _(self, e: OWLNamedIndividual):
        return OWLNamedIndividualImpl(owlapi_IRI.create(e.str))

    @map_.register
    def _(self, e: OWLNamedIndividualImpl):
        return OWLNamedIndividual(IRI.create(str(e.getIRI().getIRIString())))

    @map_.register
    def _(self, e: OWLClassExpression):
        return self.parser.parse(owl_expression_to_manchester(e))

    @map_.register(OWLAnonymousClassExpressionImpl)
    @map_.register(OWLCardinalityRestrictionImpl)
    @map_.register(OWLClassExpressionImpl)
    @map_.register(OWLClassImpl)
    @map_.register(OWLDataAllValuesFromImpl)
    @map_.register(OWLDataCardinalityRestrictionImpl)
    @map_.register(OWLDataExactCardinalityImpl)
    @map_.register(OWLDataHasValueImpl)
    @map_.register(OWLDataMaxCardinalityImpl)
    @map_.register(OWLDataMinCardinalityImpl)
    @map_.register(OWLDataSomeValuesFromImpl)
    @map_.register(OWLNaryBooleanClassExpressionImpl)
    @map_.register(OWLObjectAllValuesFromImpl)
    @map_.register(OWLObjectCardinalityRestrictionImpl)
    @map_.register(OWLObjectComplementOfImpl)
    @map_.register(OWLObjectExactCardinalityImpl)
    @map_.register(OWLObjectHasSelfImpl)
    @map_.register(OWLObjectHasValueImpl)
    @map_.register(OWLObjectIntersectionOfImpl)
    @map_.register(OWLObjectMaxCardinalityImpl)
    @map_.register(OWLObjectMinCardinalityImpl)
    @map_.register(OWLObjectOneOfImpl)
    @map_.register(OWLObjectSomeValuesFromImpl)
    @map_.register(OWLObjectUnionOfImpl)
    @map_.register(OWLQuantifiedDataRestrictionImpl)
    @map_.register(OWLQuantifiedObjectRestrictionImpl)
    @map_.register(OWLQuantifiedRestrictionImpl)
    @map_.register(OWLValueRestrictionImpl)
    def _(self, e):
        # Cant recognize the classes as implementation of org.semanticweb.owlapi.model.OWLClassExpression, so we
        # have to register all possible implementations
        return manchester_to_owl_expression(str(self.renderer.render(e)), self.namespace)
