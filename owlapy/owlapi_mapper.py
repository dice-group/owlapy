from functools import singledispatchmethod
from typing import Iterable, TypeVar
import jpype.imports

from owlapy.class_expression import OWLDataOneOf, OWLFacetRestriction, OWLDatatypeRestriction, \
    OWLClass, OWLObjectComplementOf, OWLObjectUnionOf, OWLObjectIntersectionOf, \
    OWLObjectHasSelf, OWLObjectHasValue, OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom, OWLObjectMinCardinality, \
    OWLObjectMaxCardinality, OWLObjectExactCardinality, OWLDataSomeValuesFrom, OWLDataAllValuesFrom, OWLDataHasValue, \
    OWLDataMinCardinality, OWLDataMaxCardinality, OWLDataExactCardinality, OWLObjectOneOf
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
from owlapy.owl_ontology import OWLOntologyID
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty, OWLObjectInverseOf
from owlapy.static_funcs import startJVM
from owlapy.vocab import OWLFacet

if not jpype.isJVMStarted():
    startJVM()
from org.semanticweb.owlapi.model import IRI as owlapi_IRI, OWLOntologyID as owlapi_OWLOntologyID
from org.semanticweb.owlapi.vocab import OWLFacet as owlapi_OWLFacet
from java.util import ArrayList, List, Set, LinkedHashSet, Optional, Collections
from java.util.stream import Stream
from uk.ac.manchester.cs.owl.owlapi import (OWLClassImpl, OWLDataAllValuesFromImpl, OWL2DatatypeImpl,
                                            OWLDataExactCardinalityImpl,OWLDataHasValueImpl, OWLObjectInverseOfImpl,
                                            OWLDataMaxCardinalityImpl, OWLDataUnionOfImpl,
                                            OWLDataMinCardinalityImpl, OWLDataSomeValuesFromImpl,
                                            OWLObjectAllValuesFromImpl, OWLObjectComplementOfImpl,
                                            OWLObjectExactCardinalityImpl, OWLObjectHasSelfImpl,
                                            OWLObjectHasValueImpl, OWLObjectIntersectionOfImpl,
                                            OWLObjectMaxCardinalityImpl, OWLObjectMinCardinalityImpl,
                                            OWLObjectOneOfImpl, OWLObjectSomeValuesFromImpl, OWLNaryDataRangeImpl,
                                            OWLObjectUnionOfImpl,OWLLiteralImplBoolean, OWLLiteralImplString,
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


def init(the_class):
    """Since classes names in owlapi and owlapy are pretty much similar with the small difference that in owlapi they
    usually have the 'Impl' part then we can create the mapping class name dynamically reducing the amount of code
    significantly. That's what this method does."""
    cls_name = the_class.__class__.__name__
    if "Impl" in cls_name:
        return globals().get(cls_name.split(".")[-1].replace("Impl", ""))
    else:
        return globals().get(cls_name + "Impl")


_SO = TypeVar('_SO', bound='SyncOntology')  # noqa: F821


class OWLAPIMapper:
    """A bridge between owlapy and owlapi owl-related classes."""

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
    @map_.register(OWLClass)
    def _(self, e):
        return init(e)(self.map_(e.iri))

    @map_.register(OWLNamedIndividualImpl)
    @map_.register(OWLDataPropertyImpl)
    @map_.register(OWLObjectPropertyImpl)
    @map_.register(OWLDatatypeImpl)
    @map_.register(OWLAnnotationPropertyImpl)
    @map_.register(OWLClassImpl)
    def _(self, e):
        return init(e)(self.map_(e.getIRI()))

    @map_.register(OWL2DatatypeImpl)
    def _(self, e):
        return OWLDatatype(self.map_(e.getIRI()))

    @map_.register
    def _(self, e: OWLObjectComplementOf):
        return init(e)(self.map_(e.get_operand()))

    @map_.register
    def _(self, e: OWLObjectComplementOfImpl):
        return init(e)(self.map_(e.getOperand()))

    @map_.register(OWLObjectMinCardinality)
    @map_.register(OWLObjectMaxCardinality)
    @map_.register(OWLObjectExactCardinality)
    @map_.register(OWLDataMinCardinality)
    @map_.register(OWLDataMaxCardinality)
    @map_.register(OWLDataExactCardinality)
    def _(self, e):
        return init(e)(self.map_(e.get_property()), e.get_cardinality(), self.map_(e.get_filler()))

    @map_.register(OWLObjectMinCardinalityImpl)
    @map_.register(OWLObjectMaxCardinalityImpl)
    @map_.register(OWLObjectExactCardinalityImpl)
    @map_.register(OWLDataMinCardinalityImpl)
    @map_.register(OWLDataMaxCardinalityImpl)
    @map_.register(OWLDataExactCardinalityImpl)
    def _(self, e):
        return init(e)(e.getCardinality(), self.map_(e.getProperty()), self.map_(e.getFiller()))

    @map_.register(OWLObjectHasSelf)
    def _(self, e):
        return init(e)(self.map_(e.get_property()))

    @map_.register(OWLObjectHasSelfImpl)
    def _(self, e):
        return init(e)(self.map_(e.getProperty()))

    @map_.register(OWLObjectHasValue)
    @map_.register(OWLObjectSomeValuesFrom)
    @map_.register(OWLObjectAllValuesFrom)
    @map_.register(OWLDataSomeValuesFrom)
    @map_.register(OWLDataAllValuesFrom)
    @map_.register(OWLDataHasValue)
    def _(self, e):
        return init(e)(self.map_(e.get_property()), self.map_(e.get_filler()))

    @map_.register(OWLObjectHasValueImpl)
    @map_.register(OWLObjectSomeValuesFromImpl)
    @map_.register(OWLObjectAllValuesFromImpl)
    @map_.register(OWLDataSomeValuesFromImpl)
    @map_.register(OWLDataAllValuesFromImpl)
    @map_.register(OWLDataHasValueImpl)
    def _(self, e):
        return init(e)(self.map_(e.getProperty()), self.map_(e.getFiller()))

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

    @map_.register
    def _(self, e: OWLObjectInverseOf):
        return init(e)(self.map_(e.get_named_property()))

    @map_.register
    def _(self, e: OWLObjectInverseOfImpl):
        return init(e)(self.map_(e.getNamedProperty()))

    @map_.register(OWLDataIntersectionOf)
    @map_.register(OWLDataOneOf)
    @map_.register(OWLDataUnionOf)
    @map_.register(OWLNaryDataRange)
    @map_.register(OWLObjectIntersectionOf)
    @map_.register(OWLObjectUnionOf)
    def _(self, e):
        return init(e)(self.map_(e.operands()))

    @map_.register(OWLDataIntersectionOfImpl)
    @map_.register(OWLDataOneOfImpl)
    @map_.register(OWLDataUnionOfImpl)
    @map_.register(OWLNaryDataRangeImpl)
    @map_.register(OWLObjectIntersectionOfImpl)
    @map_.register(OWLObjectUnionOfImpl)
    @map_.register(OWLObjectOneOfImpl)
    def _(self, e):
        return init(e)(self.map_(e.getOperandsAsList()))

    @map_.register(OWLObjectOneOf)
    def _(self, e):
        return init(e)(self.map_(e.operands()).stream())

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
    def _(self, e):
        return init(e)(self.map_(e.get_property()), self.map_(e.get_domain()), self.map_(e.annotations()))

    @map_.register(OWLObjectPropertyDomainAxiomImpl)
    @map_.register(OWLDataPropertyDomainAxiomImpl)
    @map_.register(OWLAnnotationPropertyDomainAxiomImpl)
    def _(self, e):
        return init(e)(self.map_(e.getProperty()), self.map_(e.getDomain()), self.map_(e.annotationsAsList()))

    @map_.register(OWLObjectPropertyRangeAxiom)
    @map_.register(OWLDataPropertyRangeAxiom)
    @map_.register(OWLAnnotationPropertyRangeAxiom)
    def _(self, e):
        return init(e)(self.map_(e.get_property()), self.map_(e.get_range()), self.map_(e.annotations()))

    @map_.register(OWLObjectPropertyRangeAxiomImpl)
    @map_.register(OWLDataPropertyRangeAxiomImpl)
    @map_.register(OWLAnnotationPropertyRangeAxiomImpl)
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
        return init(e)(self.map_(e.individuals()), self.map_(e.annotations()))

    @map_.register(OWLDifferentIndividualsAxiomImpl)
    @map_.register(OWLSameIndividualAxiomImpl)
    def _(self, e):
        return init(e)(self.map_(e.getIndividualsAsList()), self.map_(e.annotationsAsList()))

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

    @map_.register(OWLOntologyID)
    def _(self, e):
        if e.get_ontology_iri():
            i1 = self.map_(e.get_ontology_iri())
        else:
            i1 = None
        if e.get_version_iri():
            i2 = self.map_(e.get_version_iri())
        else:
            i2 = None
        return owlapi_OWLOntologyID(i1, i2)

    @map_.register(owlapi_OWLOntologyID)
    def _(self, e):
        return OWLOntologyID(self.map_(e.getOntologyIRI()), self.map_(e.getVersionIRI()))

    @map_.register(Optional)
    def _(self, e):
        if bool(e.isPresent()):
            return self.map_(e.get())
        else:
            return None

    @map_.register(List)
    @map_.register(Set)
    @map_.register(LinkedHashSet)
    def _(self, e):
        python_list = list()
        casted_list = list(e)
        if e and len(casted_list) > 0:
            for obj in list(e):
                python_list.append(self.map_(obj))
            # reverse to have the same order as the mapped iterable object
            python_list.reverse()
        return python_list

    @map_.register(list)
    @map_.register(set)
    @map_.register(frozenset)
    def _(self, e):
        java_list = ArrayList()
        if e is not None and len(e) > 0:
            for item in e:
                java_list.add(self.map_(item))
            # reverse to have the same order as the mapped iterable object
            Collections.reverse(java_list)
        return java_list

    @map_.register(Stream)
    def _(self, e):
        for en in self.to_list(e):
            yield self.map_(en)

    @staticmethod
    def to_list(stream_obj):
        """Converts Java Stream object to Python list"""
        return stream_obj.collect(jpype.JClass("java.util.stream.Collectors").toList())
