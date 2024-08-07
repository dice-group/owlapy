from functools import singledispatchmethod

import jpype.imports

from owlapy import owl_expression_to_manchester, manchester_to_owl_expression
from owlapy.class_expression import OWLClassExpression
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLDeclarationAxiom, OWLAnnotation, OWLAnnotationProperty, OWLClassAssertionAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty

if jpype.isJVMStarted():
    from uk.ac.manchester.cs.owl.owlapi import OWLObjectPropertyImpl, OWLDataPropertyImpl, OWLNamedIndividualImpl
    from org.semanticweb.owlapi.model import IRI as owlapi_IRI
    from org.semanticweb.owlapi.manchestersyntax.parser import ManchesterOWLSyntaxClassExpressionParser
    from org.semanticweb.owlapi.manchestersyntax.renderer import ManchesterOWLSyntaxOWLObjectRendererImpl
    from org.semanticweb.owlapi.util import BidirectionalShortFormProviderAdapter, SimpleShortFormProvider
    from org.semanticweb.owlapi.expression import ShortFormEntityChecker
    from java.util import HashSet, ArrayList, List
    from java.util.stream import Stream
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
                                                OWLValueRestrictionImpl, OWLLiteralImplBoolean, OWLLiteralImplString,
                                                OWLLiteralImplDouble, OWLLiteralImplFloat, OWLLiteralImplInteger,
                                                OWLDisjointClassesAxiomImpl, OWLDeclarationAxiomImpl, OWLAnnotationImpl,
                                                OWLAnnotationPropertyImpl, OWLClassAssertionAxiomImpl,
                                                )

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
        raise NotImplementedError(f"Not implemented type: {e}")

    @map_.register
    def _(self, e: IRI):
        return owlapi_IRI.create(e.str)

    @map_.register
    def _(self, e: owlapi_IRI):
        return IRI.create(str(e.getIRIString()))

    @map_.register
    def _(self, e: OWLObjectProperty):
        return OWLObjectPropertyImpl(self.map_(e.iri))

    @map_.register
    def _(self, e: OWLObjectPropertyImpl):
        return OWLObjectProperty(self.map_(e.getIRI()))

    @map_.register
    def _(self, e: OWLDataProperty):
        return OWLDataPropertyImpl(self.map_(e.iri))

    @map_.register
    def _(self, e: OWLDataPropertyImpl):
        return OWLDataProperty(self.map_(e.getIRI()))

    @map_.register
    def _(self, e: OWLNamedIndividual):
        return OWLNamedIndividualImpl(self.map_(e.iri))

    @map_.register
    def _(self, e: OWLNamedIndividualImpl):
        return OWLNamedIndividual(self.map_(e.getIRI()))

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

    @map_.register
    def _(self, e: OWLLiteral):
        if e.is_string():
            return OWLLiteralImplString(e.get_literal())

    @map_.register(OWLLiteralImplBoolean)
    def _(self, e):
        raw_value = str(e.getLiteral())
        if raw_value.lower() == "true":
            return OWLLiteral(True)
        return OWLLiteral(False)

    @map_.register(OWLLiteralImplDouble)
    @map_.register(OWLLiteralImplFloat)
    def _(self, e):
        return OWLLiteral(float(str(e.getLiteral())))

    @map_.register(OWLLiteralImplString)
    def _(self, e):
        return OWLLiteral(str(e.getLiteral()))

    @map_.register
    def _(self, e: OWLLiteralImplInteger):
        return OWLLiteral(int(str(e.getLiteral())))

    @map_.register
    def _(self, e: OWLAnnotation):
        return OWLAnnotationImpl(self.map_(e.get_property()), self.map_(e.get_value()), Stream.empty())

    @map_.register
    def _(self, e: OWLAnnotationImpl):
        return OWLAnnotation(self.map_(e.getProperty()), self.map_(e.getValue()))

    @map_.register
    def _(self, e: OWLAnnotationProperty):
        return OWLAnnotationPropertyImpl(self.map_(e.iri))

    @map_.register
    def _(self, e: OWLAnnotationPropertyImpl):
        return OWLAnnotationProperty(self.map_(e.getIRI()))

    @map_.register(OWLDeclarationAxiom)
    def _(self, e):
        return OWLDeclarationAxiomImpl(self.map_(e.get_entity()), self.map_(e.annotations()))

    @map_.register(OWLDeclarationAxiomImpl)
    def _(self, e):
        return OWLDeclarationAxiom(self.map_(e.getEntity()), self.map_(e.annotationsAsList()))

    @map_.register
    def _(self, e: OWLClassAssertionAxiom):
        return OWLClassAssertionAxiomImpl(self.map_(e.get_individual()), self.map_(e.get_class_expression()),
                                          self.map_(e.annotations()))

    @map_.register(OWLClassAssertionAxiomImpl)
    def _(self, e):
        return OWLClassAssertionAxiom(self.map_(e.getIndividual()), self.map_(e.getClassExpression()),
                                      self.map_(e.annotationsAsList()))

    @map_.register(List)
    def _(self, e):
        python_list = list()
        casted_list = list(e)
        if e and len(casted_list) > 0:
            for obj in list(e):
                python_list.append(self.map_(obj))
        return python_list

    @map_.register
    def _(self, e: list):
        java_list = ArrayList()
        if e is not None and len(e) > 0:
            for item in e:
                java_list.add(self.map_(item))
        return java_list
