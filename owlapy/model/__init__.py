# from abc import ABCMeta, abstractmethod
# from typing import Generic, Iterable, Sequence, Set, TypeVar, Union, Final, Optional, Protocol, ClassVar, List
# from datetime import datetime, date
# from pandas import Timedelta
# from owlapy.vocab import OWLRDFVocabulary, XSDVocabulary, OWLFacet
# from owlapy._utils import MOVE
# from owlapy.owlobject import OWLObject, OWLEntity
# from owlapy.owl_annotation import OWLAnnotationObject, OWLAnnotationSubject, OWLAnnotationValue
# from owlapy.iri import IRI
# from owlapy.has import HasIndex
# from owlapy.meta_classes import HasIRI, HasOperands, HasFiller, HasCardinality
# from owlapy.class_expression import OWLClassExpression, OWLNaryBooleanClassExpression, OWLObjectIntersectionOf, \
#     OWLObjectUnionOf, OWLObjectComplementOf
# from owlapy.class_expression import OWLThing, OWLNothing, OWLClass
#
# from owlapy.data_ranges import OWLPropertyRange, OWLDataRange
#
# from owlapy.owl_property import OWLObjectPropertyExpression, OWLProperty, OWLPropertyExpression, \
#     OWLDataPropertyExpression, OWLDataProperty, OWLObjectProperty
# from owlapy.class_expression import (OWLRestriction, OWLObjectAllValuesFrom, OWLObjectSomeValuesFrom,
#                                     OWLQuantifiedRestriction, OWLQuantifiedObjectRestriction,
#                                     OWLObjectRestriction, OWLHasValueRestriction, OWLDataRestriction,
#                                     OWLCardinalityRestriction, OWLObjectMinCardinality, OWLObjectCardinalityRestriction,
#                                     OWLDataAllValuesFrom,
#                                     OWLObjectHasSelf, OWLObjectMaxCardinality, OWLObjectExactCardinality,
#                                     OWLDataExactCardinality, OWLDataMinCardinality,
#                                     OWLDataMaxCardinality, OWLDataSomeValuesFrom, OWLDataHasValue, OWLDataOneOf,
#                                     OWLQuantifiedDataRestriction, OWLDataCardinalityRestriction)
#
# from owlapy.owl_individual import OWLNamedIndividual, OWLIndividual
# from owlapy.owl_axiom import (OWLEquivalentClassesAxiom, OWLClassAxiom,
#                               OWLDataPropertyDomainAxiom, OWLAxiom, OWLDataPropertyRangeAxiom,
#                               OWLObjectPropertyDomainAxiom, OWLObjectPropertyRangeAxiom)
# from owlapy.types import OWLDatatype
# from owlapy.owl_literal import OWLLiteral
#
# MOVE(OWLObject, OWLAnnotationObject, OWLAnnotationSubject, OWLAnnotationValue, HasIRI, IRI)
#
#
#
#
#
# # noinspection PyUnresolvedReferences
# # noinspection PyDunderSlots
#
#
#
#
# """Important constant objects section"""
# # @TODO: Some of them must be removed from here as they are defined under owl literal
#
# #: the built in top object property
# OWLTopObjectProperty: Final = OWLObjectProperty(OWLRDFVocabulary.OWL_TOP_OBJECT_PROPERTY.get_iri())
# #: the built in bottom object property
# OWLBottomObjectProperty: Final = OWLObjectProperty(OWLRDFVocabulary.OWL_BOTTOM_OBJECT_PROPERTY.get_iri())
# #: the built in top data property
# OWLTopDataProperty: Final = OWLDataProperty(OWLRDFVocabulary.OWL_TOP_DATA_PROPERTY.get_iri())
# #: the built in bottom data property
# OWLBottomDataProperty: Final = OWLDataProperty(OWLRDFVocabulary.OWL_BOTTOM_DATA_PROPERTY.get_iri())
#
# DoubleOWLDatatype: Final = OWLDatatype(XSDVocabulary.DOUBLE)  #: An object representing a double datatype.
# IntegerOWLDatatype: Final = OWLDatatype(XSDVocabulary.INTEGER)  #: An object representing an integer datatype.
# BooleanOWLDatatype: Final = OWLDatatype(XSDVocabulary.BOOLEAN)  #: An object representing the boolean datatype.
# StringOWLDatatype: Final = OWLDatatype(XSDVocabulary.STRING)  #: An object representing the string datatype.
# DateOWLDatatype: Final = OWLDatatype(XSDVocabulary.DATE)  #: An object representing the date datatype.
# DateTimeOWLDatatype: Final = OWLDatatype(XSDVocabulary.DATE_TIME)  #: An object representing the dateTime datatype.
# DurationOWLDatatype: Final = OWLDatatype(XSDVocabulary.DURATION)  #: An object representing the duration datatype.
# #: The OWL Datatype corresponding to the top data type
# TopOWLDatatype: Final = OWLDatatype(OWLRDFVocabulary.RDFS_LITERAL)
#
# NUMERIC_DATATYPES: Final[Set[OWLDatatype]] = {DoubleOWLDatatype, IntegerOWLDatatype}
# TIME_DATATYPES: Final[Set[OWLDatatype]] = {DateOWLDatatype, DateTimeOWLDatatype, DurationOWLDatatype}
