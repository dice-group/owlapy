from functools import singledispatchmethod
from typing import Iterable

import jpype.imports

import owlapy.owl_ontology
from owlapy import owl_expression_to_manchester, manchester_to_owl_expression
from owlapy.class_expression import OWLClassExpression, OWLDataOneOf, OWLFacetRestriction, OWLDatatypeRestriction
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLDeclarationAxiom, OWLAnnotation, OWLAnnotationProperty, OWLClassAssertionAxiom, \
    OWLDataPropertyAssertionAxiom, OWLDataPropertyDomainAxiom, OWLDataPropertyRangeAxiom, OWLObjectPropertyDomainAxiom, \
    OWLObjectPropertyRangeAxiom, OWLObjectPropertyAssertionAxiom, OWLEquivalentClassesAxiom, \
    OWLEquivalentDataPropertiesAxiom, OWLEquivalentObjectPropertiesAxiom, OWLDisjointClassesAxiom, \
    OWLDisjointDataPropertiesAxiom, OWLDisjointObjectPropertiesAxiom, OWLHasKeyAxiom, OWLSubDataPropertyOfAxiom, \
    OWLSubClassOfAxiom, OWLSubObjectPropertyOfAxiom, OWLAsymmetricObjectPropertyAxiom, OWLDatatypeDefinitionAxiom, \
    OWLDifferentIndividualsAxiom, OWLDisjointUnionAxiom, OWLFunctionalDataPropertyAxiom, \
    OWLFunctionalObjectPropertyAxiom, OWLInverseFunctionalObjectPropertyAxiom, OWLInverseObjectPropertiesAxiom, \
    OWLIrreflexiveObjectPropertyAxiom, OWLNegativeDataPropertyAssertionAxiom, OWLReflexiveObjectPropertyAxiom, \
    OWLNegativeObjectPropertyAssertionAxiom, OWLSameIndividualAxiom, OWLSymmetricObjectPropertyAxiom, \
    OWLTransitiveObjectPropertyAxiom, OWLAnnotationAssertionAxiom, OWLAnnotationPropertyDomainAxiom, \
    OWLAnnotationPropertyRangeAxiom, OWLSubAnnotationPropertyOfAxiom
from owlapy.owl_data_ranges import OWLDataIntersectionOf, OWLDataComplementOf, OWLDataUnionOf, OWLNaryDataRange
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty
from owlapy.vocab import OWLFacet

if jpype.isJVMStarted():
    from org.semanticweb.owlapi.model import IRI as owlapi_IRI
    from org.semanticweb.owlapi.vocab import OWLFacet as owlapi_OWLFacet
    from org.semanticweb.owlapi.manchestersyntax.parser import ManchesterOWLSyntaxClassExpressionParser
    from org.semanticweb.owlapi.manchestersyntax.renderer import ManchesterOWLSyntaxOWLObjectRendererImpl
    from org.semanticweb.owlapi.util import BidirectionalShortFormProviderAdapter, SimpleShortFormProvider
    from org.semanticweb.owlapi.expression import ShortFormEntityChecker
    from java.util import HashSet, ArrayList, List, Set
    from java.util.stream import Stream
    from uk.ac.manchester.cs.owl.owlapi import (OWLAnonymousClassExpressionImpl, OWLCardinalityRestrictionImpl,
                                                OWLClassExpressionImpl, OWLClassImpl, OWLDataAllValuesFromImpl,
                                                OWLDataCardinalityRestrictionImpl, OWLDataExactCardinalityImpl,
                                                OWLDataHasValueImpl, OWLDataMaxCardinalityImpl, OWLDataUnionOfImpl,
                                                OWLDataMinCardinalityImpl, OWLDataSomeValuesFromImpl,
                                                OWLNaryBooleanClassExpressionImpl, OWLObjectAllValuesFromImpl,
                                                OWLObjectCardinalityRestrictionImpl, OWLObjectComplementOfImpl,
                                                OWLObjectExactCardinalityImpl, OWLObjectHasSelfImpl,
                                                OWLObjectHasValueImpl, OWLObjectIntersectionOfImpl,
                                                OWLObjectMaxCardinalityImpl, OWLObjectMinCardinalityImpl,
                                                OWLObjectOneOfImpl, OWLObjectSomeValuesFromImpl, OWLNaryDataRangeImpl,
                                                OWLObjectUnionOfImpl, OWLQuantifiedDataRestrictionImpl,
                                                OWLQuantifiedObjectRestrictionImpl, OWLQuantifiedRestrictionImpl,
                                                OWLValueRestrictionImpl, OWLLiteralImplBoolean, OWLLiteralImplString,
                                                OWLLiteralImplDouble, OWLLiteralImplFloat, OWLLiteralImplInteger,
                                                OWLDisjointClassesAxiomImpl, OWLDeclarationAxiomImpl, OWLAnnotationImpl,
                                                OWLAnnotationPropertyImpl, OWLClassAssertionAxiomImpl,
                                                OWLDataPropertyAssertionAxiomImpl, OWLDataPropertyDomainAxiomImpl,
                                                OWLDataPropertyRangeAxiomImpl, OWLEquivalentClassesAxiomImpl,
                                                OWLEquivalentDataPropertiesAxiomImpl, OWLDataIntersectionOfImpl,
                                                OWLEquivalentObjectPropertiesAxiomImpl, OWLDataOneOfImpl,
                                                OWLObjectPropertyDomainAxiomImpl, OWLObjectPropertyRangeAxiomImpl,
                                                OWLObjectPropertyAssertionAxiomImpl, OWLDisjointDataPropertiesAxiomImpl,
                                                OWLDisjointObjectPropertiesAxiomImpl, OWLHasKeyAxiomImpl,
                                                OWLSubClassOfAxiomImpl, OWLSubDataPropertyOfAxiomImpl,
                                                OWLSubObjectPropertyOfAxiomImpl, OWLAsymmetricObjectPropertyAxiomImpl,
                                                OWLDatatypeDefinitionAxiomImpl, OWLDatatypeImpl, OWLObjectPropertyImpl,
                                                OWLDataPropertyImpl, OWLNamedIndividualImpl, OWLDisjointUnionAxiomImpl,
                                                OWLDifferentIndividualsAxiomImpl, OWLFunctionalDataPropertyAxiomImpl,
                                                OWLFunctionalObjectPropertyAxiomImpl, OWLSameIndividualAxiomImpl,
                                                OWLInverseFunctionalObjectPropertyAxiomImpl, OWLDataComplementOfImpl,
                                                OWLInverseObjectPropertiesAxiomImpl,OWLReflexiveObjectPropertyAxiomImpl,
                                                OWLIrreflexiveObjectPropertyAxiomImpl, OWLAnnotationAssertionAxiomImpl,
                                                OWLNegativeDataPropertyAssertionAxiomImpl, OWLFacetRestrictionImpl,
                                                OWLNegativeObjectPropertyAssertionAxiomImpl, OWLDatatypeRestrictionImpl,
                                                OWLSymmetricObjectPropertyAxiomImpl,
                                                OWLTransitiveObjectPropertyAxiomImpl,
                                                OWLAnnotationPropertyDomainAxiomImpl,
                                                OWLAnnotationPropertyRangeAxiomImpl,
                                                OWLSubAnnotationPropertyOfAxiomImpl
                                                )

else:
    raise ImportError("Jpype JVM is not started! Tip: Import OWLAPIMapper after JVM has started")


def init(the_class):
    cls_name = the_class.__class__.__name__
    if "Impl" in cls_name:
        return globals().get(cls_name.split(".")[-1].replace("Impl", ""))
    else:
        return globals().get(cls_name + "Impl")


class OWLAPIMapper:

    def __init__(self, ontology=None):
        # TODO: CD: Please use class type of ontology
        # TODO: CD: if ontology is None, then we should throw an exception with a useful information
        # assert isinstance(ontology, OWLAPIMapper)
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
        if isinstance(e, Iterable):
            return self.map_(list(e))

        raise NotImplementedError(f"Not implemented type: {e}")

    @map_.register
    def _(self, e: IRI):
        return owlapi_IRI.create(e.str)

    @map_.register
    def _(self, e: owlapi_IRI):
        return IRI.create(str(e.getIRIString()))

    @map_.register(OWLNamedIndividual)
    @map_.register(OWLDataProperty)
    @map_.register(OWLObjectProperty)
    @map_.register(OWLDatatype)
    @map_.register(OWLAnnotationProperty)
    def _(self, e):
        return init(e)(self.map_(e.iri))

    @map_.register(OWLNamedIndividualImpl)
    @map_.register(OWLDataPropertyImpl)
    @map_.register(OWLObjectPropertyImpl)
    @map_.register(OWLDatatypeImpl)
    @map_.register(OWLAnnotationPropertyImpl)
    def _(self, e):
        return init(e)(self.map_(e.getIRI()))

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
        elif e.is_boolean():
            return OWLLiteralImplBoolean(e.parse_boolean())
        elif e.is_integer():
            return OWLLiteralImplInteger(e.parse_integer())
        elif e.is_double():
            return OWLLiteralImplDouble(e.parse_double())
        else:
            raise NotImplementedError(f"Type of this literal: {e} cannot be mapped!")

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

    @map_.register(OWLDataIntersectionOf)
    @map_.register(OWLDataOneOf)
    @map_.register(OWLDataUnionOf)
    @map_.register(OWLNaryDataRange)
    def _(self, e):
        return init(e)(self.map_(e.operands()))

    @map_.register(OWLDataIntersectionOfImpl)
    @map_.register(OWLDataOneOfImpl)
    @map_.register(OWLDataUnionOfImpl)
    @map_.register(OWLNaryDataRangeImpl)
    def _(self, e):
        return init(e)(self.map_(e.getOperandsAsList()))

    @map_.register(OWLDataComplementOfImpl)
    def _(self, e):
        return OWLDataComplementOf(self.map_(e.getDataRange()))

    @map_.register(OWLDataComplementOf)
    def _(self, e):
        return OWLDataComplementOfImpl(self.map_(e.get_data_range()))

    @map_.register(OWLFacet)
    def _(self, e):
        return owlapi_OWLFacet.getFacetBySymbolicName(e.symbolic_form)

    @map_.register(owlapi_OWLFacet)
    def _(self, e):
        return OWLFacet.from_str(str(e.getSymbolicForm()))

    @map_.register(OWLFacetRestriction)
    def _(self, e):
        return OWLFacetRestrictionImpl(self.map_(e.get_facet()), self.map_(e.get_facet_value()))

    @map_.register(OWLFacetRestrictionImpl)
    def _(self, e):
        return OWLFacetRestriction(self.map_(e.getFacet()), self.map_(e.getFacetValue()))

    @map_.register(OWLDatatypeRestriction)
    def _(self, e):
        return OWLDatatypeRestrictionImpl(self.map_(e.get_datatype()), self.map_(e.get_facet_restrictions()))

    @map_.register(OWLDatatypeRestrictionImpl)
    def _(self, e):
        return OWLDatatypeRestriction(self.map_(e.getDatatype()), self.map_(e.facetRestrictionsAsList()))

    @map_.register
    def _(self, e: OWLAnnotation):
        return OWLAnnotationImpl(self.map_(e.get_property()), self.map_(e.get_value()), Stream.empty())

    @map_.register
    def _(self, e: OWLAnnotationImpl):
        return OWLAnnotation(self.map_(e.getProperty()), self.map_(e.getValue()))

    @map_.register
    def _(self, e: OWLAnnotationAssertionAxiom):
        return OWLAnnotationAssertionAxiomImpl(self.map_(e.get_subject()), self.map_(e.get_property()),
                                               self.map_(e.get_value()), self.map_(e.annotations()))

    @map_.register
    def _(self, e: OWLAnnotationAssertionAxiomImpl):
        return OWLAnnotationAssertionAxiom(self.map_(e.getSubject()),
                                           OWLAnnotation(self.map_(e.getProperty()), self.map_(e.getValue())),
                                           self.map_(e.annotationsAsList()))

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

    @map_.register(OWLObjectPropertyAssertionAxiom)
    @map_.register(OWLDataPropertyAssertionAxiom)
    @map_.register(OWLNegativeDataPropertyAssertionAxiom)
    @map_.register(OWLNegativeObjectPropertyAssertionAxiom)
    def _(self, e):
        return init(e)(self.map_(e.get_subject()), self.map_(e.get_property()), self.map_(e.get_object()),
                       self.map_(e.annotations()))

    @map_.register(OWLObjectPropertyAssertionAxiomImpl)
    @map_.register(OWLDataPropertyAssertionAxiomImpl)
    @map_.register(OWLNegativeDataPropertyAssertionAxiomImpl)
    @map_.register(OWLNegativeObjectPropertyAssertionAxiomImpl)
    def _(self, e):
        return init(e)(self.map_(e.getSubject()), self.map_(e.getProperty()), self.map_(e.getObject()),
                       self.map_(e.annotationsAsList()))

    @map_.register(OWLObjectPropertyDomainAxiom)
    @map_.register(OWLDataPropertyDomainAxiom)
    @map_.register(OWLAnnotationPropertyDomainAxiom)
    @map_.register(OWLAnnotationPropertyRangeAxiom)
    def _(self, e):
        return init(e)(self.map_(e.get_property()), self.map_(e.get_domain()), self.map_(e.annotations()))

    @map_.register(OWLObjectPropertyDomainAxiomImpl)
    @map_.register(OWLDataPropertyDomainAxiomImpl)
    @map_.register(OWLAnnotationPropertyDomainAxiomImpl)
    @map_.register(OWLAnnotationPropertyRangeAxiomImpl)
    def _(self, e):
        return init(e)(self.map_(e.getProperty()), self.map_(e.getDomain()), self.map_(e.annotationsAsList()))

    @map_.register(OWLObjectPropertyRangeAxiom)
    @map_.register(OWLDataPropertyRangeAxiom)
    def _(self, e):
        return init(e)(self.map_(e.get_property()), self.map_(e.get_range()), self.map_(e.annotations()))

    @map_.register(OWLObjectPropertyRangeAxiomImpl)
    @map_.register(OWLDataPropertyRangeAxiomImpl)
    def _(self, e):
        return init(e)(self.map_(e.getProperty()), self.map_(e.getRange()), self.map_(e.annotationsAsList()))

    @map_.register(OWLEquivalentDataPropertiesAxiom)
    @map_.register(OWLEquivalentObjectPropertiesAxiom)
    def _(self, e):
        return init(e)(self.map_(e.properties()), self.map_(e.annotations()))

    @map_.register(OWLEquivalentClassesAxiomImpl)
    @map_.register(OWLEquivalentDataPropertiesAxiomImpl)
    @map_.register(OWLEquivalentObjectPropertiesAxiomImpl)
    def _(self, e):
        return init(e)(self.map_(e.getOperandsAsList()), self.map_(e.annotationsAsList()))

    @map_.register(OWLEquivalentClassesAxiom)
    @map_.register(OWLDisjointClassesAxiom)
    def _(self, e):
        return init(e)(self.map_(e.class_expressions()), self.map_(e.annotations()))

    @map_.register(OWLDisjointDataPropertiesAxiom)
    @map_.register(OWLDisjointObjectPropertiesAxiom)
    def _(self, e):
        return init(e)(self.map_(e.properties()), self.map_(e.annotations()))

    @map_.register(OWLDisjointClassesAxiomImpl)
    @map_.register(OWLDisjointDataPropertiesAxiomImpl)
    @map_.register(OWLDisjointObjectPropertiesAxiomImpl)
    def _(self, e):
        return init(e)(self.map_(e.getOperandsAsList()), self.map_(e.annotationsAsList()))

    @map_.register
    def _(self, e: OWLHasKeyAxiom):
        return OWLHasKeyAxiomImpl(self.map_(e.get_class_expression()), self.map_(e.get_property_expressions()),
                                  self.map_(e.annotations()))

    @map_.register(OWLHasKeyAxiomImpl)
    def _(self, e):
        return OWLHasKeyAxiom(self.map_(e.getClassExpression()), self.map_(e.getOperandsAsList()),
                              self.map_(e.annotationsAsList()))

    @map_.register
    def _(self, e: OWLSubClassOfAxiom):
        return OWLSubClassOfAxiomImpl(self.map_(e.get_sub_class()), self.map_(e.get_super_class()),
                                      self.map_(e.annotations()))

    @map_.register(OWLSubClassOfAxiomImpl)
    def _(self, e):
        return OWLSubClassOfAxiom(self.map_(e.getSubClass()), self.map_(e.getSuperClass()),
                                  self.map_(e.annotationsAsList()))

    @map_.register(OWLSubDataPropertyOfAxiom)
    @map_.register(OWLSubObjectPropertyOfAxiom)
    @map_.register(OWLSubAnnotationPropertyOfAxiom)
    def _(self, e):
        return init(e)(self.map_(e.get_sub_property()), self.map_(e.get_super_property()), self.map_(e.annotations()))

    @map_.register(OWLSubDataPropertyOfAxiomImpl)
    @map_.register(OWLSubObjectPropertyOfAxiomImpl)
    @map_.register(OWLSubAnnotationPropertyOfAxiomImpl)
    def _(self, e):
        return init(e)(self.map_(e.getSubProperty()), self.map_(e.getSuperProperty()),
                       self.map_(e.annotationsAsList()))

    @map_.register(OWLAsymmetricObjectPropertyAxiom)
    @map_.register(OWLFunctionalDataPropertyAxiom)
    @map_.register(OWLFunctionalObjectPropertyAxiom)
    @map_.register(OWLInverseFunctionalObjectPropertyAxiom)
    @map_.register(OWLIrreflexiveObjectPropertyAxiom)
    @map_.register(OWLReflexiveObjectPropertyAxiom)
    @map_.register(OWLSymmetricObjectPropertyAxiom)
    @map_.register(OWLTransitiveObjectPropertyAxiom)
    def _(self, e):
        return init(e)(self.map_(e.get_property()), self.map_(e.annotations()))

    @map_.register(OWLAsymmetricObjectPropertyAxiomImpl)
    @map_.register(OWLFunctionalDataPropertyAxiomImpl)
    @map_.register(OWLFunctionalObjectPropertyAxiomImpl)
    @map_.register(OWLInverseFunctionalObjectPropertyAxiomImpl)
    @map_.register(OWLIrreflexiveObjectPropertyAxiomImpl)
    @map_.register(OWLReflexiveObjectPropertyAxiomImpl)
    @map_.register(OWLSymmetricObjectPropertyAxiomImpl)
    @map_.register(OWLTransitiveObjectPropertyAxiomImpl)
    def _(self, e):
        return init(e)(self.map_(e.getProperty()), self.map_(e.annotationsAsList()))

    @map_.register(OWLDatatypeDefinitionAxiom)
    def _(self, e):
        return OWLDatatypeDefinitionAxiomImpl(self.map_(e.get_datatype()), self.map_(e.get_datarange()),
                                              self.map_(e.annotations()))

    @map_.register(OWLDatatypeDefinitionAxiomImpl)
    def _(self, e):
        return OWLDatatypeDefinitionAxiom(self.map_(e.getDatatype()), self.map_(e.getDataRange()),
                                          self.map_(e.annotationsAsList()))

    @map_.register(OWLDifferentIndividualsAxiom)
    @map_.register(OWLSameIndividualAxiom)
    def _(self, e):
        return OWLDifferentIndividualsAxiomImpl(self.map_(e.individuals()), self.map_(e.annotations()))

    @map_.register(OWLDifferentIndividualsAxiomImpl)
    @map_.register(OWLSameIndividualAxiomImpl)
    def _(self, e):
        return OWLDifferentIndividualsAxiom(self.map_(e.getIndividualsAsList()), self.map_(e.annotationsAsList()))

    @map_.register(OWLDisjointUnionAxiom)
    def _(self, e):
        return OWLDisjointUnionAxiomImpl(self.map_(e.get_owl_class()), self.map_(e.get_class_expressions()).stream(),
                                         self.map_(e.annotations()))

    @map_.register(OWLDisjointUnionAxiomImpl)
    def _(self, e):
        return OWLDisjointUnionAxiom(self.map_(e.getOWLClass()), self.map_(e.getOperandsAsList()),
                                     self.map_(e.annotationsAsList()))

    @map_.register(OWLInverseObjectPropertiesAxiom)
    def _(self, e):
        return OWLInverseObjectPropertiesAxiomImpl(self.map_(e.get_first_property()),
                                                   self.map_(e.get_second_property()), self.map_(e.annotations()))

    @map_.register(OWLInverseObjectPropertiesAxiomImpl)
    def _(self, e):
        return OWLInverseObjectPropertiesAxiom(self.map_(e.getFirstProperty()), self.map_(e.getSecondProperty()),
                                               self.map_(e.annotationsAsList()))

    @map_.register(List)
    @map_.register(Set)
    def _(self, e):
        python_list = list()
        casted_list = list(e)
        if e and len(casted_list) > 0:
            for obj in list(e):
                python_list.append(self.map_(obj))
        return python_list

    @map_.register(list)
    @map_.register(set)
    def _(self, e):
        java_list = ArrayList()
        if e is not None and len(e) > 0:
            for item in e:
                java_list.add(self.map_(item))
        return java_list
