"""OWL Ontology"""
from functools import singledispatchmethod, singledispatch
from itertools import chain, islice, combinations
import types
from types import MappingProxyType
from typing import Final, cast, Iterable, List, Optional, Tuple, Union, Dict, Any
import logging

import jpype
import owlready2
import rdflib
from pandas import Timedelta
from owlapy import namespaces
from owlapy.abstracts.abstract_owl_ontology import _OI, AbstractOWLOntology
from owlapy.owl_data_ranges import OWLDataRange, OWLDataComplementOf, OWLDataUnionOf, OWLDataIntersectionOf
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_individual import OWLNamedIndividual, OWLIndividual
from owlapy.owl_literal import IntegerOWLDatatype, DoubleOWLDatatype, BooleanOWLDatatype, StringOWLDatatype, \
    DateOWLDatatype, DateTimeOWLDatatype, DurationOWLDatatype, OWLLiteral
from owlapy.owl_object import OWLObject
from owlapy.iri import IRI
from owlapy.class_expression import OWLClass, OWLThing, OWLClassExpression, OWLObjectComplementOf, OWLObjectUnionOf, \
    OWLObjectIntersectionOf, OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom, OWLObjectExactCardinality, \
    OWLObjectMaxCardinality, OWLObjectMinCardinality, OWLObjectHasValue, OWLDataSomeValuesFrom, OWLDataAllValuesFrom, \
    OWLDataExactCardinality, OWLDataMaxCardinality, OWLDataMinCardinality, OWLDataHasValue, OWLDataOneOf, \
    OWLDatatypeRestriction, OWLRestriction, OWLObjectRestriction, OWLDataRestriction, OWLFacetRestriction, \
    OWLNaryBooleanClassExpression, OWLQuantifiedObjectRestriction, OWLQuantifiedDataRestriction, OWLObjectOneOf
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty, OWLPropertyExpression, OWLObjectInverseOf, \
    OWLObjectPropertyExpression, OWLDataPropertyExpression, OWLProperty
from datetime import date, datetime
from owlready2 import destroy_entity, AllDisjoint, AllDifferent, GeneralClassAxiom
from owlapy.owl_axiom import OWLObjectPropertyRangeAxiom, OWLAxiom, OWLSubClassOfAxiom, OWLEquivalentClassesAxiom, \
    OWLDisjointUnionAxiom, OWLAnnotationAssertionAxiom, OWLAnnotationProperty, OWLSubPropertyAxiom, \
    OWLPropertyRangeAxiom, OWLClassAssertionAxiom, OWLDeclarationAxiom, OWLObjectPropertyAssertionAxiom, \
    OWLSymmetricObjectPropertyAxiom, OWLTransitiveObjectPropertyAxiom, OWLPropertyDomainAxiom, \
    OWLAsymmetricObjectPropertyAxiom, OWLDataPropertyCharacteristicAxiom, OWLFunctionalDataPropertyAxiom, \
    OWLReflexiveObjectPropertyAxiom, OWLDataPropertyAssertionAxiom, OWLFunctionalObjectPropertyAxiom, \
    OWLObjectPropertyCharacteristicAxiom, OWLIrreflexiveObjectPropertyAxiom, OWLInverseFunctionalObjectPropertyAxiom, \
    OWLDisjointDataPropertiesAxiom, OWLDisjointObjectPropertiesAxiom, OWLEquivalentDataPropertiesAxiom, \
    OWLEquivalentObjectPropertiesAxiom, OWLInverseObjectPropertiesAxiom, OWLNaryPropertyAxiom, OWLNaryIndividualAxiom, \
    OWLDifferentIndividualsAxiom, OWLDisjointClassesAxiom, OWLSameIndividualAxiom, OWLClassAxiom, \
    OWLDataPropertyDomainAxiom, OWLDataPropertyRangeAxiom, OWLObjectPropertyDomainAxiom
from owlapy.static_funcs import startJVM
from owlapy.vocab import OWLFacet
import os
from pathlib import Path
from dicee.knowledge_graph_embeddings import KGE
from dicee.executer import Execute
from dicee.config import Namespace
import torch

logger = logging.getLogger(__name__)

_Datatype_map: Final = MappingProxyType({
    int: IntegerOWLDatatype,
    float: DoubleOWLDatatype,
    bool: BooleanOWLDatatype,
    str: StringOWLDatatype,
    date: DateOWLDatatype,
    datetime: DateTimeOWLDatatype,
    Timedelta: DurationOWLDatatype,
})


_VERSION_IRI: Final = IRI.create(namespaces.OWL, "versionIRI")


class OWLOntologyID:
    """An object that identifies an ontology. Since OWL 2, ontologies do not have to have an ontology IRI, or if they
    have an ontology IRI then they can optionally also have a version IRI. Instances of this OWLOntologyID class bundle
    identifying information of an ontology together. If an ontology doesn't have an ontology IRI then we say that it is
    "anonymous".
    """
    __slots__ = '_ontology_iri', '_version_iri'

    _ontology_iri: Optional[IRI]
    _version_iri: Optional[IRI]

    def __init__(self, ontology_iri: Optional[IRI] = None, version_iri: Optional[IRI] = None):
        """Constructs an ontology identifier specifying the ontology IRI and version IRI.

        Args:
            ontology_iri: The ontology IRI (optional).
            version_iri: The version IRI (must be None if no ontology_iri is provided).
        """
        self._ontology_iri = ontology_iri
        self._version_iri = version_iri

    def get_ontology_iri(self) -> Optional[IRI]:
        """Gets the ontology IRI.

        Returns:
            Ontology IRI. If the ontology is anonymous, it will return None.
        """
        return self._ontology_iri

    def get_version_iri(self) -> Optional[IRI]:
        """Gets the version IRI.

        Returns:
            Version IRI or None.
        """
        return self._version_iri

    def get_default_document_iri(self) -> Optional[IRI]:
        """Gets the IRI which is used as a default for the document that contain a representation of an ontology with
        this ID. This will be the version IRI if there is an ontology IRI and version IRI, else it will be the ontology
        IRI if there is an ontology IRI but no version IRI, else it will be None if there is no ontology IRI. See
        Ontology Documents in the OWL 2 Structural Specification.

        Returns:
            the IRI that can be used as a default for an ontology document, or None.
        """
        if self._ontology_iri is not None:
            if self._version_iri is not None:
                return self._version_iri
        return self._ontology_iri

    def is_anonymous(self) -> bool:
        return self._ontology_iri is None

    def __repr__(self):
        return f"OWLOntologyID({repr(self._ontology_iri)}, {repr(self._version_iri)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._ontology_iri == other._ontology_iri and self._version_iri == other._version_iri
        return NotImplemented


def _check_expression(expr: OWLObject, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    """
    Creates all entities (individuals, classes, properties) that appear in the given (complex) class expression
    and do not exist in the given ontology yet

    """
    if isinstance(expr, (OWLClass, OWLProperty, OWLNamedIndividual,)):
        _add_axiom(OWLDeclarationAxiom(expr), ontology, world)
    elif isinstance(expr, (OWLNaryBooleanClassExpression, OWLObjectComplementOf, OWLObjectOneOf,)):
        for op in expr.operands():
            _check_expression(op, ontology, world)
    elif isinstance(expr, (OWLQuantifiedObjectRestriction, OWLObjectHasValue,)):
        _check_expression(expr.get_property(), ontology, world)
        _check_expression(expr.get_filler(), ontology, world)
    elif isinstance(expr, OWLObjectInverseOf):
        _check_expression(expr.get_named_property(), ontology, world)
        _check_expression(expr.get_inverse_property(), ontology, world)
    elif isinstance(expr, (OWLQuantifiedDataRestriction, OWLDataHasValue,)):
        _check_expression(expr.get_property(), ontology, world)
    elif not isinstance(expr, OWLObject):
        raise ValueError(f'({expr}) is not an OWLObject.')


@singledispatch
def _add_axiom(axiom: OWLAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    raise NotImplementedError(f'Axiom type {axiom} is not implemented yet.')


@_add_axiom.register
def _(axiom: OWLDeclarationAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    entity = axiom.get_entity()
    with ont_x:
        entity_x = world[entity.to_string_id()]
        # Entity already exists
        if entity_x is not None:
            return

        thing_x: owlready2.entity.ThingClass = conv.map_concept(OWLThing)
        if isinstance(entity, OWLClass):
            if entity.is_owl_thing() or entity.is_owl_nothing():
                return
            entity_x = types.new_class(name=entity.iri.get_remainder(), bases=(thing_x,))
        elif isinstance(entity, OWLIndividual):
            entity_x = thing_x(entity.iri.get_remainder())
        elif isinstance(entity, OWLObjectProperty):
            entity_x = types.new_class(name=entity.iri.get_remainder(), bases=(owlready2.ObjectProperty,))
        elif isinstance(entity, OWLDataProperty):
            entity_x = types.new_class(name=entity.iri.get_remainder(), bases=(owlready2.DatatypeProperty,))
        elif isinstance(entity, OWLAnnotationProperty):
            entity_x = types.new_class(name=entity.iri.get_remainder(), bases=(owlready2.AnnotationProperty,))
        else:
            raise ValueError(f'Cannot add ({entity}). Not an atomic class, property, or individual.')
        entity_x.namespace = ont_x.get_namespace(entity.iri.get_namespace())
        entity_x.namespace.world._refactor(entity_x.storid, entity_x.iri)


@_add_axiom.register
def _(axiom: OWLClassAssertionAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    individual = axiom.get_individual()
    cls_ = axiom.get_class_expression()
    _check_expression(cls_, ontology, world)
    _add_axiom(OWLDeclarationAxiom(individual), ontology, world)
    with ont_x:
        cls_x = conv.map_concept(cls_)
        ind_x = conv._to_owlready2_individual(individual)
        thing_x = conv.map_concept(OWLThing)
        if thing_x in ind_x.is_a:
            ind_x.is_a.remove(thing_x)
        ind_x.is_a.append(cls_x)


@_add_axiom.register
def _(axiom: OWLObjectPropertyAssertionAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    subject = axiom.get_subject()
    property_ = axiom.get_property()
    object_ = axiom.get_object()
    _add_axiom(OWLDeclarationAxiom(subject), ontology, world)
    _add_axiom(OWLDeclarationAxiom(property_), ontology, world)
    _add_axiom(OWLDeclarationAxiom(object_), ontology, world)
    with ont_x:
        subject_x = conv._to_owlready2_individual(subject)
        property_x = conv._to_owlready2_property(property_)
        object_x = conv._to_owlready2_individual(object_)
        property_x[subject_x].append(object_x)


@_add_axiom.register
def _(axiom: OWLDataPropertyAssertionAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    subject = axiom.get_subject()
    property_ = axiom.get_property()
    _add_axiom(OWLDeclarationAxiom(subject), ontology, world)
    _add_axiom(OWLDeclarationAxiom(property_), ontology, world)
    with ont_x:
        subject_x = conv._to_owlready2_individual(subject)
        property_x = conv._to_owlready2_property(property_)
        property_x[subject_x].append(axiom.get_object().to_python())


@_add_axiom.register
def _(axiom: OWLSubClassOfAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    sub_class = axiom.get_sub_class()
    super_class = axiom.get_super_class()

    _check_expression(sub_class, ontology, world)
    _check_expression(super_class, ontology, world)
    with ont_x:
        thing_x = conv.map_concept(OWLThing)
        sub_class_x = conv.map_concept(sub_class)
        super_class_x = conv.map_concept(super_class)
        if isinstance(sub_class, OWLClass):
            if thing_x in sub_class_x.is_a:
                sub_class_x.is_a.remove(thing_x)
        else:
            # Currently owlready2 seems to expect that we make a new GeneralClassAxiom object each time.
            # Another option would be to check whether a GeneralClassAxiom with the sub_class_x already exists and just
            # add the super_class_x to its is_a attribute
            sub_class_x = GeneralClassAxiom(sub_class_x)
        sub_class_x.is_a.append(super_class_x)


# TODO: Update as soon as owlready2 adds support for EquivalentClasses general class axioms
@_add_axiom.register
def _(axiom: OWLEquivalentClassesAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x = conv.map_object(ontology)

    assert axiom.contains_named_equivalent_class(), 'Owlready2 does not support general' \
                                                    'class axioms for equivalent classes.'
    for ce in axiom.class_expressions():
        _check_expression(ce, ontology, world)
    with ont_x:
        for ce_1, ce_2 in combinations(axiom.class_expressions(), 2):
            assert ce_1 is not None, f"ce_1 cannot be None: {ce_1}, {type(ce_1)}"
            assert ce_2 is not None, f"ce_2_x cannot be None: {ce_2}, {type(ce_2)}"

            ce_1_x = conv.map_concept(ce_1)
            ce_2_x = conv.map_concept(ce_2)
            try:
                assert ce_1_x is not None, f"ce_1_x cannot be None: {ce_1_x}, {type(ce_1_x)}"
                assert ce_2_x is not None, f"ce_2_x cannot be None: {ce_2_x}, {type(ce_2_x)}"
            except AssertionError:
                print("function of ToOwlready2.map_concept() returns None")
                print(ce_1, ce_1_x)
                print(ce_2, ce_2_x)
                print("Axiom:", axiom)
                print("Temporary solution is reinitializing ce_1_x=ce_2_x\n\n")
                ce_1_x=ce_2_x

            if isinstance(ce_1_x, owlready2.ThingClass):
                ce_1_x.equivalent_to.append(ce_2_x)
            if isinstance(ce_2_x, owlready2.ThingClass):
                ce_2_x.equivalent_to.append(ce_1_x)


@_add_axiom.register
def _(axiom: OWLDisjointClassesAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    for cls_ in axiom.class_expressions():
        _check_expression(cls_, ontology, world)
    with ont_x:
        # TODO: If the first element in the list is a complex class expression owlready2 is bugged
        # and creates an AllDifferent axiom
        AllDisjoint(list(map(conv.map_concept, axiom.class_expressions())))


@_add_axiom.register
def _(axiom: OWLDisjointUnionAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    assert isinstance(axiom.get_owl_class(), OWLClass), f'({axiom.get_owl_class()}) is not a named class.'
    _add_axiom(OWLDeclarationAxiom(axiom.get_owl_class()), ontology, world)
    for cls_ in axiom.get_class_expressions():
        _check_expression(cls_, ontology, world)
    with ont_x:
        cls_x = conv.map_concept(axiom.get_owl_class())
        cls_x.disjoint_unions.append(list(map(conv.map_concept, axiom.get_class_expressions())))


@_add_axiom.register
def _(axiom: OWLAnnotationAssertionAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    prop_x = conv.map_object(axiom.get_property())
    if prop_x is None:
        with ont_x:
            prop_x: owlready2.annotation.AnnotationPropertyClass = cast(
                owlready2.AnnotationProperty,
                types.new_class(
                    name=axiom.get_property().iri.get_remainder(),
                    bases=(owlready2.AnnotationProperty,)))
            prop_x.namespace = ont_x.get_namespace(axiom.get_property().iri.get_namespace())
    sub_x = world[axiom.get_subject().as_iri().as_str()]
    assert sub_x is not None, f'{axiom.get_subject} not found in {ontology}'
    with ont_x:
        if axiom.get_value().is_literal():
            literal = axiom.get_value().as_literal()
            setattr(sub_x, prop_x.python_name, literal.to_python())
        else:
            o_x = world[axiom.get_value().as_iri().as_str()]
            assert o_x is not None, f'{axiom.get_value()} not found in {ontology}'
            setattr(sub_x, prop_x.python_name, o_x)


@_add_axiom.register
def _(axiom: OWLNaryIndividualAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    for ind in axiom.individuals():
        _add_axiom(OWLDeclarationAxiom(ind), ontology, world)
    with ont_x:
        if isinstance(axiom, OWLSameIndividualAxiom):
            for idx, ind in enumerate(axiom.individuals()):
                ind_x = conv._to_owlready2_individual(ind)
                for ind_2 in islice(axiom.individuals(), idx + 1, None):
                    ind_2_x = conv._to_owlready2_individual(ind_2)
                    ind_x.equivalent_to.append(ind_2_x)
        elif isinstance(axiom, OWLDifferentIndividualsAxiom):
            AllDifferent(list(map(conv._to_owlready2_individual, axiom.individuals())))
        else:
            raise ValueError(f'OWLNaryIndividualAxiom ({axiom}) is not defined.')


@_add_axiom.register
def _(axiom: OWLSubPropertyAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    sub_property = axiom.get_sub_property()
    super_property = axiom.get_super_property()
    _add_axiom(OWLDeclarationAxiom(sub_property), ontology, world)
    _add_axiom(OWLDeclarationAxiom(super_property), ontology, world)
    with ont_x:
        sub_property_x = conv._to_owlready2_property(sub_property)
        super_property_x = conv._to_owlready2_property(super_property)
        sub_property_x.is_a.append(super_property_x)


@_add_axiom.register
def _(axiom: OWLPropertyDomainAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    property_ = axiom.get_property()
    domain = axiom.get_domain()
    _add_axiom(OWLDeclarationAxiom(property_), ontology, world)
    _check_expression(domain, ontology, world)
    with ont_x:
        property_x = conv._to_owlready2_property(property_)
        domain_x = conv.map_concept(domain)
        property_x.domain.append(domain_x)


@_add_axiom.register
def _(axiom: OWLPropertyRangeAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    property_ = axiom.get_property()
    range_ = axiom.get_range()
    _add_axiom(OWLDeclarationAxiom(property_), ontology, world)
    if isinstance(axiom, OWLObjectPropertyRangeAxiom):
        _check_expression(range_, ontology, world)
    with ont_x:
        property_x = conv._to_owlready2_property(property_)
        range_x = conv.map_concept(range_) if isinstance(axiom, OWLObjectPropertyRangeAxiom) \
            else conv.map_datarange(range_)
        property_x.range.append(range_x)


@_add_axiom.register
def _(axiom: OWLNaryPropertyAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    for property_ in axiom.properties():
        _add_axiom(OWLDeclarationAxiom(property_), ontology, world)
    with ont_x:
        if isinstance(axiom, (OWLEquivalentObjectPropertiesAxiom, OWLEquivalentDataPropertiesAxiom,)):
            for idx, property_ in enumerate(axiom.properties()):
                property_x = conv._to_owlready2_property(property_)
                for property_2 in islice(axiom.properties(), idx + 1, None):
                    property_2_x = conv._to_owlready2_property(property_2)
                    property_x.equivalent_to.append(property_2_x)
        elif isinstance(axiom, (OWLDisjointObjectPropertiesAxiom, OWLDisjointDataPropertiesAxiom,)):
            AllDisjoint(list(map(conv._to_owlready2_property, axiom.properties())))
        elif isinstance(axiom, OWLInverseObjectPropertiesAxiom):
            property_first_x = conv._to_owlready2_property(axiom.get_first_property())
            property_second_x = conv._to_owlready2_property(axiom.get_second_property())
            if property_second_x.inverse_property is not None:
                property_second_x.inverse_property = None
            property_first_x.inverse_property = property_second_x
        else:
            raise ValueError(f'OWLNaryPropertyAxiom ({axiom}) is not defined.')


@_add_axiom.register
def _(axiom: OWLObjectPropertyCharacteristicAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    property_ = axiom.get_property()
    _add_axiom(OWLDeclarationAxiom(property_), ontology, world)
    with ont_x:
        property_x = conv._to_owlready2_property(property_)
        if isinstance(axiom, OWLFunctionalObjectPropertyAxiom):
            property_x.is_a.append(owlready2.FunctionalProperty)
        elif isinstance(axiom, OWLAsymmetricObjectPropertyAxiom):
            property_x.is_a.append(owlready2.AsymmetricProperty)
        elif isinstance(axiom, OWLInverseFunctionalObjectPropertyAxiom):
            property_x.is_a.append(owlready2.InverseFunctionalProperty)
        elif isinstance(axiom, OWLIrreflexiveObjectPropertyAxiom):
            property_x.is_a.append(owlready2.IrreflexiveProperty)
        elif isinstance(axiom, OWLReflexiveObjectPropertyAxiom):
            property_x.is_a.append(owlready2.ReflexiveProperty)
        elif isinstance(axiom, OWLSymmetricObjectPropertyAxiom):
            property_x.is_a.append(owlready2.SymmetricProperty)
        elif isinstance(axiom, OWLTransitiveObjectPropertyAxiom):
            property_x.is_a.append(owlready2.TransitiveProperty)
        else:
            raise ValueError(f'ObjectPropertyCharacteristicAxiom ({axiom}) is not defined.')


@_add_axiom.register
def _(axiom: OWLDataPropertyCharacteristicAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    property_ = axiom.get_property()
    _add_axiom(OWLDeclarationAxiom(property_), ontology, world)
    with ont_x:
        property_x = conv._to_owlready2_property(property_)
        if isinstance(axiom, OWLFunctionalDataPropertyAxiom):
            property_x.is_a.append(owlready2.FunctionalProperty)
        else:
            raise ValueError(f'DataPropertyCharacteristicAxiom ({axiom}) is not defined.')


@singledispatch
def _remove_axiom(axiom: OWLAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    raise NotImplementedError(f'Axiom type {axiom} is not implemented yet.')


@_remove_axiom.register
def _(axiom: OWLDeclarationAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)
    with ont_x:
        entity_x = world[axiom.get_entity().to_string_id()]
        if entity_x is not None:
            # TODO: owlready2 seems to be bugged for properties here
            destroy_entity(entity_x)


@_remove_axiom.register
def _(axiom: OWLClassAssertionAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    with ont_x:
        cls_x = conv.map_concept(axiom.get_class_expression())
        ind_x = conv._to_owlready2_individual(axiom.get_individual())
        if cls_x is None or ind_x is None:
            return
        if cls_x in ind_x.is_a:
            ind_x.is_a.remove(cls_x)
        elif isinstance(axiom.get_class_expression(), OWLClass):
            ont_x._del_obj_triple_spo(ind_x.storid, owlready2.rdf_type, cls_x.storid)


@_remove_axiom.register
def _(axiom: OWLObjectPropertyAssertionAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    with ont_x:
        subject_x = conv._to_owlready2_individual(axiom.get_subject())
        property_x = conv._to_owlready2_property(axiom.get_property())
        object_x = conv._to_owlready2_individual(axiom.get_object())
        if all([subject_x, property_x, object_x]) and object_x in property_x[subject_x]:
            property_x[subject_x].remove(object_x)


@_remove_axiom.register
def _(axiom: OWLDataPropertyAssertionAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    with ont_x:
        subject_x = conv._to_owlready2_individual(axiom.get_subject())
        property_x = conv._to_owlready2_property(axiom.get_property())
        object_ = axiom.get_object().to_python()
        if subject_x is not None and property_x is not None and object_ in property_x[subject_x]:
            property_x[subject_x].remove(object_)


@_remove_axiom.register
def _(axiom: OWLSubClassOfAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)
    sub_class = axiom.get_sub_class()
    super_class = axiom.get_super_class()

    with ont_x:
        sub_class_x = conv.map_concept(sub_class)
        super_class_x = conv.map_concept(super_class)
        if sub_class_x is None or super_class_x is None:
            return

        if isinstance(sub_class, OWLClass):
            if super_class_x in sub_class_x.is_a:
                sub_class_x.is_a.remove(super_class_x)
            elif isinstance(axiom.get_sub_class(), OWLClass) and isinstance(axiom.get_super_class(), OWLClass):
                ont_x._del_obj_triple_spo(sub_class_x.storid, owlready2.rdfs_subclassof, super_class_x.storid)
        else:
            for ca in ont_x.general_class_axioms():
                if ca.left_side == sub_class_x and super_class_x in ca.is_a:
                    ca.is_a.remove(super_class_x)


# TODO: Update as soons as owlready2 adds support for EquivalentClasses general class axioms
@_remove_axiom.register
def _(axiom: OWLEquivalentClassesAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x = conv.map_object(ontology)

    if not axiom.contains_named_equivalent_class():
        return

    with ont_x:
        ces_x = list(map(conv.map_concept, axiom.class_expressions()))
        if len(ces_x) < 2 or not all(ces_x):
            return

        for ce_1_x, ce_2_x in combinations(ces_x, 2):
            if isinstance(ce_2_x, owlready2.ThingClass) and ce_1_x in ce_2_x.equivalent_to:
                ce_2_x.equivalent_to.remove(ce_1_x)
            if isinstance(ce_1_x, owlready2.ThingClass) and ce_2_x in ce_1_x.equivalent_to:
                ce_1_x.equivalent_to.remove(ce_2_x)


@_remove_axiom.register
def _(axiom: OWLDisjointClassesAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    with ont_x:
        class_expressions_x = set(map(conv.map_concept, axiom.class_expressions()))
        if len(class_expressions_x) < 2 or not all(class_expressions_x):
            return
        for disjoints_x in ont_x.disjoint_classes():
            if set(disjoints_x.entities) == class_expressions_x:
                del disjoints_x.entities[:-1]
                break


@_remove_axiom.register
def _(axiom: OWLDisjointUnionAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)
    assert isinstance(axiom.get_owl_class(), OWLClass), f'({axiom.get_owl_class()}) is not a named class.'

    with ont_x:
        cls_x = conv.map_concept(axiom.get_owl_class())
        union_expressions_x = set(map(conv.map_concept, axiom.get_class_expressions()))
        if cls_x is not None and all(union_expressions_x):
            for union_x in cls_x.disjoint_unions:
                if union_expressions_x == set(union_x):
                    cls_x.disjoint_unions.remove(union_x)
                    break


@_remove_axiom.register
def _(axiom: OWLAnnotationAssertionAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    sub_x = world[axiom.get_subject().as_iri().as_str()]
    if sub_x is None:
        return
    name = axiom.get_property().iri.get_remainder()
    with ont_x:
        if axiom.get_value().is_literal():
            o_x = axiom.get_value().as_literal().to_python()
        else:
            o_x = world[axiom.get_value().as_iri().as_str()]

        value = getattr(sub_x, name, None)
        if value is not None and o_x in value:
            value.remove(o_x)


@_remove_axiom.register
def _(axiom: OWLNaryIndividualAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    with ont_x:
        individuals_x = list(map(conv._to_owlready2_individual, axiom.individuals()))
        if len(individuals_x) < 2 or not all(individuals_x):
            return
        if isinstance(axiom, OWLSameIndividualAxiom):
            if set(individuals_x[1:-1]) <= set(individuals_x[0].INDIRECT_equivalent_to):
                for individual_1_x, individual_2_x in combinations(individuals_x, 2):
                    if individual_1_x in individual_2_x.equivalent_to:
                        individual_2_x.equivalent_to.remove(individual_1_x)
                    if individual_2_x in individual_1_x.equivalent_to:
                        individual_1_x.equivalent_to.remove(individual_2_x)
        elif isinstance(axiom, OWLDifferentIndividualsAxiom):
            individuals_x = set(individuals_x)
            for different_x in ont_x.different_individuals():
                if set(different_x.entities) == individuals_x:
                    del different_x.entities[:-1]
                    break
        else:
            raise ValueError(f'OWLNaryIndividualAxiom ({axiom}) is not defined.')


@_remove_axiom.register
def _(axiom: OWLSubPropertyAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    with ont_x:
        sub_property_x = conv._to_owlready2_property(axiom.get_sub_property())
        super_property_x = conv._to_owlready2_property(axiom.get_super_property())
        if sub_property_x is None or super_property_x is None:
            return
        if super_property_x in sub_property_x.is_a:
            sub_property_x.is_a.remove(super_property_x)
        else:
            ont_x._del_obj_triple_spo(sub_property_x.storid, owlready2.rdfs_subpropertyof, super_property_x.storid)


@_remove_axiom.register
def _(axiom: OWLPropertyDomainAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    with ont_x:
        property_x = conv._to_owlready2_property(axiom.get_property())
        domain_x = conv.map_concept(axiom.get_domain())
        if domain_x is not None and property_x is not None and domain_x in property_x.domain:
            property_x.domain.remove(domain_x)


@_remove_axiom.register
def _(axiom: OWLPropertyRangeAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    with ont_x:
        property_x = conv._to_owlready2_property(axiom.get_property())
        range_x = conv.map_concept(axiom.get_range()) \
            if isinstance(axiom, OWLObjectPropertyRangeAxiom) else conv.map_datarange(axiom.get_range())
        if range_x is not None and property_x is not None and range_x in property_x.range:
            property_x.range.remove(range_x)


@_remove_axiom.register
def _(axiom: OWLNaryPropertyAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    with ont_x:
        properties_x = list(map(conv._to_owlready2_property, axiom.properties()))
        if len(properties_x) < 2 or not all(properties_x):
            return
        if isinstance(axiom, (OWLEquivalentObjectPropertiesAxiom, OWLEquivalentDataPropertiesAxiom,)):
            # Check if all equivalent properties are defined in the ontology
            if set(properties_x[1:-1]) <= set(properties_x[0].INDIRECT_equivalent_to):
                for property_1_x, property_2_x in combinations(properties_x, 2):
                    if property_1_x in property_2_x.equivalent_to:
                        property_2_x.equivalent_to.remove(property_1_x)
                    if property_2_x in property_1_x.equivalent_to:
                        property_1_x.equivalent_to.remove(property_2_x)
        elif isinstance(axiom, (OWLDisjointObjectPropertiesAxiom, OWLDisjointDataPropertiesAxiom,)):
            properties_x = set(properties_x)
            for disjoints_x in ont_x.disjoint_properties():
                if set(disjoints_x.entities) == properties_x:
                    del disjoints_x.entities[:-1]
                    break
        elif isinstance(axiom, OWLInverseObjectPropertiesAxiom):
            if len(properties_x) != 2:
                return
            first = properties_x[0]
            second = properties_x[1]
            if first.inverse_property == second and second.inverse_property == first:
                first.inverse_property = None
        else:
            raise ValueError(f'OWLNaryPropertyAxiom ({axiom}) is not defined.')


@_remove_axiom.register
def _(axiom: OWLObjectPropertyCharacteristicAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    with ont_x:
        property_x = conv._to_owlready2_property(axiom.get_property())
        if property_x is None:
            return

        if isinstance(axiom, OWLFunctionalObjectPropertyAxiom) and owlready2.FunctionalProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.FunctionalProperty)
        elif isinstance(axiom, OWLAsymmetricObjectPropertyAxiom) and owlready2.AsymmetricProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.AsymmetricProperty)
        elif isinstance(axiom, OWLInverseFunctionalObjectPropertyAxiom) \
                and owlready2.InverseFunctionalProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.InverseFunctionalProperty)
        elif isinstance(axiom, OWLIrreflexiveObjectPropertyAxiom) and owlready2.IrreflexiveProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.IrreflexiveProperty)
        elif isinstance(axiom, OWLReflexiveObjectPropertyAxiom) and owlready2.ReflexiveProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.ReflexiveProperty)
        elif isinstance(axiom, OWLSymmetricObjectPropertyAxiom) and owlready2.SymmetricProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.SymmetricProperty)
        elif isinstance(axiom, OWLTransitiveObjectPropertyAxiom) and owlready2.TransitiveProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.TransitiveProperty)
        else:
            raise ValueError(f'OWLObjectPropertyCharacteristicAxiom ({axiom}) is not defined.')


@_remove_axiom.register
def _(axiom: OWLDataPropertyCharacteristicAxiom, ontology: AbstractOWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    with ont_x:
        property_x = conv._to_owlready2_property(axiom.get_property())
        if property_x is not None and isinstance(axiom, OWLFunctionalDataPropertyAxiom) \
                and owlready2.FunctionalProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.FunctionalProperty)


class Ontology(AbstractOWLOntology):
    __slots__ = '_iri', '_world', '_onto', 'is_modified'

    _onto: owlready2.Ontology
    is_modified: bool

    def __init__(self, ontology_iri: IRI | str, load: bool = True, world_store=None):
        """Represents an Ontology in Ontolearn.

        Args:
            ontology_iri: IRI of the ontology.
            load: Whether to load the ontology or not.
        """
        self._iri = ontology_iri
        if world_store is None:
            self._world = owlready2.World()
        else:
            self._world = owlready2.World(filename=world_store)
        self.is_modified = False

        if isinstance(ontology_iri, str):
            onto = self._world.get_ontology(ontology_iri)
            self._iri = IRI.create(ontology_iri)
        else:
            onto = self._world.get_ontology(ontology_iri.as_str())
        if load:
            onto = onto.load()
        self._onto = onto

    def __len__(self) -> int:
        return len([t for t in self._onto.get_triples()])

    def classes_in_signature(self) -> Iterable[OWLClass]:
        for c in self._onto.classes():
            yield OWLClass(IRI.create(c.iri))

    def data_properties_in_signature(self) -> Iterable[OWLDataProperty]:
        for dp in self._onto.data_properties():
            yield OWLDataProperty(IRI.create(dp.iri))

    def object_properties_in_signature(self) -> Iterable[OWLObjectProperty]:
        for op in self._onto.object_properties():
            yield OWLObjectProperty(IRI.create(op.iri))

    def properties_in_signature(self) -> Iterable[OWLProperty]:
        yield from self.object_properties_in_signature()
        yield from self.data_properties_in_signature()

    def individuals_in_signature(self) -> Iterable[OWLNamedIndividual]:
        for i in self._onto.individuals():
            yield OWLNamedIndividual(IRI.create(i.iri))

    def get_abox_axioms(self) -> Iterable:
        raise NotImplementedError("will be implemented in future")

    def get_tbox_axioms(self) -> Iterable:
        # @TODO: CD: Return all information between owl classes, e.g. subclass or disjoint
        raise NotImplementedError("will be implemented in future")

    def get_abox_axioms_between_individuals(self) -> Iterable:
        # @TODO: CD: Return all information between owl_individuals, i.e., triples with object properties
        raise NotImplementedError("will be implemented in future")

    def get_abox_axioms_between_individuals_and_classes(self) -> Iterable:
        # @TODO: CD: Return all type information about individuals, i.e., individual type Class
        raise NotImplementedError("will be implemented in future")

    # @TODO:CD:Unsure it is working
    def equivalent_classes_axioms(self, c: OWLClass) -> Iterable[OWLEquivalentClassesAxiom]:
        c_x: owlready2.ThingClass = self._world[c.str]
        # TODO: Should this also return EquivalentClasses general class axioms? Compare to java owlapi
        for ec_x in c_x.equivalent_to:
            yield OWLEquivalentClassesAxiom([c, _parse_concept_to_owlapy(ec_x)])

    # @TODO:CD:Unsure it is working
    def general_class_axioms(self) -> Iterable[OWLClassAxiom]:
        # TODO: At the moment owlready2 only supports SubClassOf general class axioms. (18.02.2023)
        for ca in self._onto.general_class_axioms():
            yield from (OWLSubClassOfAxiom(_parse_concept_to_owlapy(ca.left_side), _parse_concept_to_owlapy(c))
                        for c in ca.is_a)

    def get_ontology_id(self) -> OWLOntologyID:
        onto_iri = self._world._unabbreviate(self._onto.storid)
        look_version = self._world._get_obj_triple_sp_o(
            self._onto.storid,
            self._world._abbreviate(_VERSION_IRI.as_str()))
        if look_version is not None:
            version_iri = self._world._unabbreviate(look_version)
        else:
            version_iri = None

        return OWLOntologyID(IRI.create(onto_iri) if onto_iri is not None else None,
                             IRI.create(version_iri) if version_iri is not None else None)

    def data_property_domain_axioms(self, pe: OWLDataProperty) -> Iterable[OWLDataPropertyDomainAxiom]:
        p_x: owlready2.DataPropertyClass = self._world[pe.str]
        domains = set(p_x.domains_indirect())
        if len(domains) == 0:
            yield OWLDataPropertyDomainAxiom(pe, OWLThing)
        else:
            for dom in domains:
                if isinstance(dom, (owlready2.ThingClass, owlready2.ClassConstruct)):
                    yield OWLDataPropertyDomainAxiom(pe, _parse_concept_to_owlapy(dom))
                else:
                    logger.warning("Construct %s not implemented at %s", dom, pe)
                    pass  # XXX TODO

    def data_property_range_axioms(self, pe: OWLDataProperty) -> Iterable[OWLDataPropertyRangeAxiom]:
        p_x: owlready2.DataPropertyClass = self._world[pe.str]
        ranges = set(chain.from_iterable(super_prop.range for super_prop in p_x.ancestors()))
        if len(ranges) == 0:
            pass
            # TODO
        else:
            for rng in ranges:
                if rng in _Datatype_map:
                    yield OWLDataPropertyRangeAxiom(pe, _Datatype_map[rng])
                elif isinstance(rng, owlready2.ClassConstruct):
                    yield OWLDataPropertyRangeAxiom(pe, _parse_datarange_to_owlapy(rng))
                else:
                    logger.warning("Datatype %s not implemented at %s", rng, pe)
                    pass  # XXX TODO

    def object_property_domain_axioms(self, pe: OWLObjectProperty) -> Iterable[OWLObjectPropertyDomainAxiom]:
        p_x: owlready2.ObjectPropertyClass = self._world[pe.str]
        domains = set(p_x.domains_indirect())
        if len(domains) == 0:
            yield OWLObjectPropertyDomainAxiom(pe, OWLThing)
        else:
            for dom in domains:
                if isinstance(dom, (owlready2.ThingClass, owlready2.ClassConstruct)):
                    yield OWLObjectPropertyDomainAxiom(pe, _parse_concept_to_owlapy(dom))
                else:
                    logger.warning("Construct %s not implemented at %s", dom, pe)
                    pass  # XXX TODO

    def object_property_range_axioms(self, pe: OWLObjectProperty) -> Iterable[OWLObjectPropertyRangeAxiom]:
        p_x: owlready2.ObjectPropertyClass = self._world[pe.str]
        ranges = set(chain.from_iterable(super_prop.range for super_prop in p_x.ancestors()))
        if len(ranges) == 0:
            yield OWLObjectPropertyRangeAxiom(pe, OWLThing)
        else:
            for rng in ranges:
                if isinstance(rng, (owlready2.ThingClass, owlready2.ClassConstruct)):
                    yield OWLObjectPropertyRangeAxiom(pe, _parse_concept_to_owlapy(rng))
                else:
                    logger.warning("Construct %s not implemented at %s", rng, pe)
                    pass  # XXX TODO

    def add_axiom(self, axiom: Union[OWLAxiom, Iterable[OWLAxiom]]):
        self.is_modified = True
        if isinstance(axiom, OWLAxiom):
            _add_axiom(axiom, self, self._world)
        else:
            for ax in axiom:
                _add_axiom(ax, self, self._world)

    def remove_axiom(self, axiom: Union[OWLAxiom, Iterable[OWLAxiom]]):
        self.is_modified = True
        if isinstance(axiom, OWLAxiom):
            _remove_axiom(axiom, self, self._world)
        else:
            for ax in axiom:
                _remove_axiom(ax, self, self._world)

    def save(self, path: Union[str, IRI] = None, inplace: bool = False, rdf_format="rdfxml"):
        # convert it into str.
        if isinstance(path, IRI):
            path = path.as_str()
        # Sanity checking
        if inplace is False:
            assert isinstance(path,str), f"path must be string if inplace is set to False. Current path is {type(path)}"
        # Get the current ontology defined in the world.
        ont_x: owlready2.namespace.Ontology
        ont_x = self._world.get_ontology(self.get_ontology_id().get_ontology_iri().as_str())

        if inplace:
            if os.path.exists(self._iri.as_str()):
                print(f"Saving {self} inplace...")
                ont_x.save(file=self._iri.as_str(), format=rdf_format)
            else:
                print(f"Saving {self} inplace with name of demo.owl...")
                self._world.get_ontology(self.get_ontology_id().get_ontology_iri().as_str()).save(file="demo.owl")
        else:
            print(f"Saving {path}..")
            ont_x.save(file=path, format=rdf_format)

    def get_original_iri(self):
        """Get the IRI argument that was used to create this ontology."""
        return self._iri

    def __eq__(self, other):
        if type(other) is type(self):
            return self._onto.loaded == other._onto.loaded and self._onto.base_iri == other._onto.base_iri
        return NotImplemented

    def __hash__(self):
        return hash(self._onto.base_iri)

    def __repr__(self):
        return f'Ontology({self._onto.base_iri}, loaded:{self._onto.loaded})'


class SyncOntology(AbstractOWLOntology):

    def __init__(self, path: Union[IRI, str], load: bool = True):
        if not jpype.isJVMStarted():
            startJVM()
        # noinspection PyUnresolvedReferences
        from org.semanticweb.owlapi.apibinding import OWLManager
        from owlapy.owlapi_mapper import OWLAPIMapper
        # noinspection PyUnresolvedReferences
        from java.io import File
        # noinspection PyUnresolvedReferences
        from java.util.stream import Stream
        # noinspection PyUnresolvedReferences
        from org.semanticweb.owlapi.model import IRI as owlapi_IRI

        self.owlapi_manager = OWLManager.createOWLOntologyManager()
        self.path = path
        self.load = load

        if isinstance(path, IRI):
            file_path = path.str
        else:
            file_path = path
        if not load:  # create new ontology
            if isinstance(path, IRI):
                self.owlapi_ontology = self.owlapi_manager.createOntology(Stream.empty(), owlapi_IRI.create(path.str))
            else:
                try:
                    self.owlapi_ontology = self.owlapi_manager.createOntology(Stream.empty(),
                                                                              owlapi_IRI.create(path))
                except Exception as e:
                    print(f"Error: {e}")
                    raise NotImplementedError("Cant initialize a new ontology using path. Use IRI instead")
        else:  # means we are loading an existing ontology
            self.owlapi_ontology = self.owlapi_manager.loadOntologyFromOntologyDocument(File(file_path))
        self.mapper = OWLAPIMapper()

    def __eq__(self, other):
        if isinstance(other, SyncOntology):
            return other.owlapi_ontology.getOntologyID().equals(other.owlapi_ontology.getOntologyID())
        return False

    def __hash__(self):
        return int(self.owlapi_ontology.getOntologyID().hashCode())

    def __repr__(self):
        return (f'SyncOntology:'
                f'\t|Tbox|={len(self.get_tbox_axioms())}'
                f'\t|Abox|={len(self.get_abox_axioms())}'
                f'\t|Individuals|={len(self.individuals_in_signature())}'
                f'\t|Classes|={len(self.classes_in_signature())}'
                f'\t|Object Properties|={len(self.object_properties_in_signature())}'
                f'\t|Data Properties|={len(self.data_properties_in_signature())}'
                f'\n tPath:{self.path}\tLoad:{self.load}')

    def __len__(self):
        return len([i for i in self.get_abox_axioms()] + [i for i in self.get_abox_axioms()])

    def classes_in_signature(self) -> Iterable[OWLClass]:
        return self.mapper.map_(self.owlapi_ontology.getClassesInSignature())

    def data_properties_in_signature(self) -> Iterable[OWLDataProperty]:
        return self.mapper.map_(self.owlapi_ontology.getDataPropertiesInSignature())

    def object_properties_in_signature(self) -> Iterable[OWLObjectProperty]:
        return self.mapper.map_(self.owlapi_ontology.getObjectPropertiesInSignature())

    def individuals_in_signature(self) -> Iterable[OWLNamedIndividual]:
        return self.mapper.map_(self.owlapi_ontology.getIndividualsInSignature())

    def equivalent_classes_axioms(self, c: OWLClass) -> Iterable[OWLEquivalentClassesAxiom]:
        return self.mapper.map_(self.owlapi_ontology.getEquivalentClassesAxioms(self.mapper.map_(c)))

    def general_class_axioms(self) -> Iterable[OWLClassAxiom]:
        return self.mapper.map_(self.owlapi_ontology.getGeneralClassAxioms())

    def data_property_domain_axioms(self, property: OWLDataProperty) -> Iterable[OWLDataPropertyDomainAxiom]:
        return self.mapper.map_(self.owlapi_ontology.getDataPropertyDomainAxioms(self.mapper.map_(property)))

    def data_property_range_axioms(self, property: OWLDataProperty) -> Iterable[OWLDataPropertyRangeAxiom]:
        return self.mapper.map_(self.owlapi_ontology.getDataPropertyRangeAxioms(self.mapper.map_(property)))

    def object_property_domain_axioms(self, property: OWLObjectProperty) -> Iterable[OWLObjectPropertyDomainAxiom]:
        return self.mapper.map_(self.owlapi_ontology.getObjectPropertyDomainAxioms(self.mapper.map_(property)))

    def object_property_range_axioms(self, property: OWLObjectProperty) -> Iterable[OWLObjectPropertyRangeAxiom]:
        return self.mapper.map_(self.owlapi_ontology.getObjectPropertyRangeAxioms(self.mapper.map_(property)))

    def _get_imports_enum(self, include_imports_closure: bool):
        # noinspection PyUnresolvedReferences
        from org.semanticweb.owlapi.model.parameters import Imports
        if include_imports_closure:
            imports = Imports.INCLUDED
        else:
            imports = Imports.EXCLUDED
        return imports

    def get_signature(self, include_imports_closure: bool = True):
        """Gets the entities that are in the signature of this ontology.

        Args:
            include_imports_closure: Whether to include/exclude imports from searches.

        Returns:
            Entities in signature.
        """
        return self.mapper.map_(self.owlapi_ontology.getSignature(self._get_imports_enum(include_imports_closure)))

    def get_abox_axioms(self, include_imports_closure: bool = True) -> Iterable[OWLAxiom]:
        """Get all ABox axioms.

        Args:
            include_imports_closure: Whether to include/exclude imports from searches.

        Returns:
            ABox axioms.
        """
        return self.mapper.map_(self.owlapi_ontology.getABoxAxioms(self._get_imports_enum(include_imports_closure)))

    def get_tbox_axioms(self, include_imports_closure: bool = True) -> Iterable[OWLAxiom]:
        """Get all TBox axioms.

        Args:
            include_imports_closure: Whether to include/exclude imports from searches.

        Returns:
            TBox axioms.
        """
        return self.mapper.map_(self.owlapi_ontology.getTBoxAxioms(self._get_imports_enum(include_imports_closure)))

    def get_owlapi_ontology(self):
        return self.owlapi_ontology

    def get_ontology_id(self) -> OWLOntologyID:
        return self.mapper.map_(self.owlapi_ontology.getOntologyID())

    def add_axiom(self, axiom: Union[OWLAxiom, Iterable[OWLAxiom]]):
        if isinstance(axiom, OWLAxiom):
            self.owlapi_ontology.addAxiom(self.mapper.map_(axiom))
        else:
            self.owlapi_ontology.addAxioms(self.mapper.map_(axiom))

    def remove_axiom(self, axiom: Union[OWLAxiom, Iterable[OWLAxiom]]):
        if isinstance(axiom, OWLAxiom):
            self.owlapi_ontology.removeAxiom(self.mapper.map_(axiom))
        else:
            self.owlapi_ontology.removeAxioms(self.mapper.map_(axiom))

    def save(self, path: str = None, document_iri: Optional[IRI] = None):
        """
        https://github.com/phillord/owl-api/blob/b2a5bfb9a0c6730c8ff950776af8f9bf19c78eac/
                contract/src/test/java/org/coode/owlapi/examples/Examples.java#L206
        """
        assert isinstance(path, str), "Path must be a string"
        # noinspection PyUnresolvedReferences
        from java.io import File
        # noinspection PyUnresolvedReferences
        import org.semanticweb.owlapi.model.IRI
        # //Create a file for the new format
        file = File(path)
        print(f"Saving Ontology into {path}")
        if document_iri is None:
            document_iri = org.semanticweb.owlapi.model.IRI.create(file.toURI())
        else:
            raise NotImplementedError("document_iri must be None for the time being")
        self.owlapi_manager.saveOntology(self.owlapi_ontology,
                                         self.owlapi_manager.getOntologyFormat(self.owlapi_ontology), document_iri)


class RDFLibOntology(AbstractOWLOntology):

    def __init__(self, path: str, load: bool = True):
        if load:
            assert os.path.exists(path)
            import rdflib

            self.rdflib_graph = rdflib.Graph().parse(path)
            self.str_owl_classes = [x.n3()[1:-1] for x in self.rdflib_graph.subjects(rdflib.RDF.type, rdflib.OWL.Class) if not isinstance(x, rdflib.term.BNode)]
            self.str_owl_individuals = [x.n3()[1:-1] for x in self.rdflib_graph.subjects(rdflib.RDF.type, rdflib.OWL.NamedIndividual) if not isinstance(x, rdflib.term.BNode)]
        else:  # create a blank rdf ontology
            raise NotImplementedError("Currently supports only loading an existing ontology")

    def __len__(self) -> int:
        return len(self.rdflib_graph)

    def get_tbox_axioms(self) -> Iterable[OWLSubClassOfAxiom | OWLEquivalentClassesAxiom]:
        results = []
        for owl_class in self.rdflib_graph.subjects(rdflib.RDF.type, rdflib.OWL.Class):
            if isinstance(owl_class, rdflib.term.URIRef):
                str_owl_class = owl_class.n3()[1:-1]
                for (_, p, o) in self.rdflib_graph.triples(triple=(owl_class, None, None)):
                    if isinstance(o, rdflib.term.BNode):
                        continue
                    str_iri_predicate = p.n3()
                    str_iri_object = o.n3()[1:-1]
                    if str_iri_predicate == "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>":
                        # Ignore for the timebing
                        axiom = OWLDeclarationAxiom(OWLClass(str_owl_class))
                    elif str_iri_predicate == "<http://www.w3.org/2000/01/rdf-schema#subClassOf>":
                        axiom = OWLSubClassOfAxiom(sub_class=OWLClass(str_owl_class),
                                                   super_class=OWLClass(str_iri_object))

                    elif str_iri_predicate == "<http://www.w3.org/2002/07/owl#equivalentClass>":
                        axiom = OWLEquivalentClassesAxiom([OWLClass(str_owl_class), OWLClass(str_iri_object)])
                    else:
                        raise NotImplementedError(f"{str_iri_predicate} unsure")
                    if axiom:
                        results.append(axiom)
        return results

    def get_abox_axioms(self) -> Iterable:
        results=[]
        for owl_individual in self.rdflib_graph.subjects(rdflib.RDF.type, rdflib.OWL.NamedIndividual):
            if isinstance(owl_individual, rdflib.term.URIRef):
                str_owl_individual = owl_individual.n3()[1:-1]
                for (_, p, o) in self.rdflib_graph.triples(triple=(owl_individual,None, None)):
                    if isinstance(o, rdflib.term.BNode):
                        continue
                    str_iri_predicate = p.n3()[1:-1]
                    str_iri_object = o.n3()[1:-1]
                    axiom=None
                    if str_iri_predicate == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type":
                        if str_iri_object in self.str_owl_classes:
                            axiom = OWLClassAssertionAxiom(OWLNamedIndividual(str_owl_individual), OWLClass(str_iri_object))
                        elif str_iri_object == "http://www.w3.org/2002/07/owl#NamedIndividual":
                            # axiom= OWLDeclarationAxiom(OWLNamedIndividual(str_owl_individual))
                            continue
                        else:
                            raise RuntimeError(f"Incorrect Parsing:\t{str_owl_individual}\t{str_iri_predicate}\t{str_iri_object}")
                    elif str_iri_object in self.str_owl_individuals:
                        axiom = OWLObjectPropertyAssertionAxiom(OWLNamedIndividual(str_owl_individual),
                                                                             OWLObjectProperty(str_iri_predicate),
                                                                             OWLNamedIndividual(str_iri_object))
                    else:

                        raise NotImplementedError("")
                    if axiom:
                        results.append(axiom)
        return results

    def classes_in_signature(self) -> Iterable[OWLClass]:
        raise NotImplementedError()
        for c in self._onto.classes():
            yield OWLClass(IRI.create(c.iri))

    def data_properties_in_signature(self) -> Iterable[OWLDataProperty]:
        raise NotImplementedError()

        for dp in self._onto.data_properties():
            yield OWLDataProperty(IRI.create(dp.iri))

    def object_properties_in_signature(self) -> Iterable[OWLObjectProperty]:
        raise NotImplementedError()

        for op in self._onto.object_properties():
            yield OWLObjectProperty(IRI.create(op.iri))

    def properties_in_signature(self) -> Iterable[OWLProperty]:
        raise NotImplementedError()

        yield from self.object_properties_in_signature()
        yield from self.data_properties_in_signature()

    def individuals_in_signature(self) -> Iterable[OWLNamedIndividual]:
        raise NotImplementedError()

        for (s,p,o) in self.rdflib_graph.subjects(rdflib.RDF.type, rdflib.OWL.NamedIndividual):
            print(s,p,o)
        # for i in self._onto.individuals():
        #    yield OWLNamedIndividual(IRI.create(i.iri))


    def get_abox_axioms_between_individuals(self)->Iterable:
        # @TODO: CD: Return all information between owl_individuals, i.e., triples with object properties
        raise NotImplementedError("will be implemented in future")
    def get_abox_axioms_between_individuals_and_classes(self)->Iterable:
        # @TODO: CD: Return all type information about individuals, i.e., individual type Class
        raise NotImplementedError("will be implemented in future")
    # @TODO:CD:Unsure it is working
    def equivalent_classes_axioms(self, c: OWLClass) -> Iterable[OWLEquivalentClassesAxiom]:
        raise NotImplementedError("will be implemented in future")
        c_x: owlready2.ThingClass = self._world[c.str]
        # TODO: Should this also return EquivalentClasses general class axioms? Compare to java owlapi
        for ec_x in c_x.equivalent_to:
            yield OWLEquivalentClassesAxiom([c, _parse_concept_to_owlapy(ec_x)])
    # @TODO:CD:Unsure it is working
    def general_class_axioms(self) -> Iterable[OWLClassAxiom]:
        raise NotImplementedError("will be implemented in future")
        # TODO: At the moment owlready2 only supports SubClassOf general class axioms. (18.02.2023)
        for ca in self._onto.general_class_axioms():
            yield from (OWLSubClassOfAxiom(_parse_concept_to_owlapy(ca.left_side), _parse_concept_to_owlapy(c))
                        for c in ca.is_a)

    def data_property_domain_axioms(self, pe: OWLDataProperty) -> Iterable[OWLDataPropertyDomainAxiom]:
        raise NotImplementedError("will be implemented in future")
        p_x: owlready2.DataPropertyClass = self._world[pe.str]
        domains = set(p_x.domains_indirect())
        if len(domains) == 0:
            yield OWLDataPropertyDomainAxiom(pe, OWLThing)
        else:
            for dom in domains:
                if isinstance(dom, (owlready2.ThingClass, owlready2.ClassConstruct)):
                    yield OWLDataPropertyDomainAxiom(pe, _parse_concept_to_owlapy(dom))
                else:
                    logger.warning("Construct %s not implemented at %s", dom, pe)
                    pass  # XXX TODO

    def data_property_range_axioms(self, pe: OWLDataProperty) -> Iterable[OWLDataPropertyRangeAxiom]:
        raise NotImplementedError("will be implemented in future")
        p_x: owlready2.DataPropertyClass = self._world[pe.str]
        ranges = set(chain.from_iterable(super_prop.range for super_prop in p_x.ancestors()))
        if len(ranges) == 0:
            pass
            # TODO
        else:
            for rng in ranges:
                if rng in _Datatype_map:
                    yield OWLDataPropertyRangeAxiom(pe, _Datatype_map[rng])
                elif isinstance(rng, owlready2.ClassConstruct):
                    yield OWLDataPropertyRangeAxiom(pe, _parse_datarange_to_owlapy(rng))
                else:
                    logger.warning("Datatype %s not implemented at %s", rng, pe)
                    pass  # XXX TODO

    def object_property_domain_axioms(self, pe: OWLObjectProperty) -> Iterable[OWLObjectPropertyDomainAxiom]:
        raise NotImplementedError("will be implemented in future")
        p_x: owlready2.ObjectPropertyClass = self._world[pe.str]
        domains = set(p_x.domains_indirect())
        if len(domains) == 0:
            yield OWLObjectPropertyDomainAxiom(pe, OWLThing)
        else:
            for dom in domains:
                if isinstance(dom, (owlready2.ThingClass, owlready2.ClassConstruct)):
                    yield OWLObjectPropertyDomainAxiom(pe, _parse_concept_to_owlapy(dom))
                else:
                    logger.warning("Construct %s not implemented at %s", dom, pe)
                    pass  # XXX TODO

    def object_property_range_axioms(self, pe: OWLObjectProperty) -> Iterable[OWLObjectPropertyRangeAxiom]:
        raise NotImplementedError("will be implemented in future")
        p_x: owlready2.ObjectPropertyClass = self._world[pe.str]

        ranges = set(chain.from_iterable(super_prop.range for super_prop in p_x.ancestors()))
        if len(ranges) == 0:
            yield OWLObjectPropertyRangeAxiom(pe, OWLThing)
        else:
            for rng in ranges:
                if isinstance(rng, (owlready2.ThingClass, owlready2.ClassConstruct)):
                    yield OWLObjectPropertyRangeAxiom(pe, _parse_concept_to_owlapy(rng))
                else:
                    logger.warning("Construct %s not implemented at %s", rng, pe)
                    pass  # XXX TODO

    def add_axiom(self, axiom: Union[OWLAxiom, Iterable[OWLAxiom]]):
        raise NotImplementedError("will be implemented in future")
        self.is_modified = True
        if isinstance(axiom, OWLAxiom):
            _add_axiom(axiom, self, self._world)
        else:
            for ax in axiom:
                _add_axiom(ax, self, self._world)

    def remove_axiom(self, axiom: Union[OWLAxiom, Iterable[OWLAxiom]]):
        raise NotImplementedError("will be implemented in future")
        self.is_modified = True
        if isinstance(axiom, OWLAxiom):
            _remove_axiom(axiom, self, self._world)
        else:
            for ax in axiom:
                _remove_axiom(ax, self, self._world)

    def save(self, path: Union[str,IRI] = None, inplace:bool=False, rdf_format = "rdfxml"):
        raise NotImplementedError("will be implemented in future")
        # convert it into str.
        if isinstance(path, IRI):
            path = path.as_str()
        # Sanity checking
        if inplace is False:
            assert isinstance(path,str), f"path must be string if inplace is set to False. Current path is {type(path)}"
        # Get the current ontology defined in the world.
        ont_x:owlready2.namespace.Ontology
        ont_x = self._world.get_ontology(self.get_ontology_id().get_ontology_iri().as_str())

        if inplace:
            if os.path.exists(self._iri.as_str()):
                print(f"Saving {self} inplace...")
                ont_x.save(file=self._iri.as_str(), format=rdf_format)
            else:
                print(f"Saving {self} inplace with name of demo.owl...")
                self._world.get_ontology(self.get_ontology_id().get_ontology_iri().as_str()).save(file="demo.owl")
        else:
            print(f"Saving {path}..")
            ont_x.save(file=path,format=rdf_format)

    def get_ontology_id(self):
        raise NotImplementedError("will be implemented in future")

    def __eq__(self, other):
        raise NotImplementedError("will be implemented in future")
        if type(other) is type(self):
            return self._onto.loaded == other._onto.loaded and self._onto.base_iri == other._onto.base_iri
        return NotImplemented

    def __hash__(self):
        raise NotImplementedError("will be implemented in future")
        return hash(self._onto.base_iri)

    def __repr__(self):
        raise NotImplementedError("will be implemented in future")
        return f'RDFLibOntology({self._onto.base_iri}, loaded:{self._onto.loaded})'


OWLREADY2_FACET_KEYS = MappingProxyType({
    OWLFacet.MIN_INCLUSIVE: "min_inclusive",
    OWLFacet.MIN_EXCLUSIVE: "min_exclusive",
    OWLFacet.MAX_INCLUSIVE: "max_inclusive",
    OWLFacet.MAX_EXCLUSIVE: "max_exclusive",
    OWLFacet.LENGTH: "length",
    OWLFacet.MIN_LENGTH: "min_length",
    OWLFacet.MAX_LENGTH: "max_length",
    OWLFacet.PATTERN: "pattern",
    OWLFacet.TOTAL_DIGITS: "total_digits",
    OWLFacet.FRACTION_DIGITS: "fraction_digits"
})

######################### Below classes must be outside of this script #########################
class ToOwlready2:
    __slots__ = '_world'

    _world: owlready2.World

    def __init__(self, world: owlready2.World):
        """Map owlapy model classes to owlready2.

        Args:
            world: Owlready2 World to use for mapping.
        """
        self._world = world

    @singledispatchmethod
    def map_object(self, o: OWLObject):
        """Map owlapy object classes."""
        raise NotImplementedError(f'don\'t know how to map {o}')

    @map_object.register
    def _(self, ce: OWLClassExpression) -> Union[owlready2.ClassConstruct, owlready2.ThingClass]:
        return self.map_concept(ce)

    @map_object.register
    def _(self, ont: AbstractOWLOntology) -> owlready2.namespace.Ontology:
        return self._world.get_ontology(
            ont.get_ontology_id().get_ontology_iri().as_str()
        )

    @map_object.register
    def _(self, ap: OWLAnnotationProperty) -> owlready2.annotation.AnnotationPropertyClass:
        return self._world[ap.str]

    # @TODO CD: map_object is buggy. and it can return None
    # single dispatch is still not implemented in mypy, see https://github.com/python/mypy/issues/2904
    @singledispatchmethod
    def map_concept(self, o: OWLClassExpression) \
            -> Union[owlready2.ClassConstruct, owlready2.ThingClass]:
        """Map owlapy concept classes."""
        raise NotImplementedError(o)

    @singledispatchmethod
    def _to_owlready2_property(self, p: OWLPropertyExpression) -> owlready2.Property:
        raise NotImplementedError(p)

    @_to_owlready2_property.register
    def _(self, p: OWLObjectInverseOf):
        p_x = self._to_owlready2_property(p.get_named_property())
        return owlready2.Inverse(p_x)

    @_to_owlready2_property.register
    def _(self, p: OWLObjectProperty) -> owlready2.prop.ObjectPropertyClass:
        return self._world[p.str]

    @_to_owlready2_property.register
    def _(self, p: OWLDataProperty) -> owlready2.prop.DataPropertyClass:
        return self._world[p.str]

    @singledispatchmethod
    def _to_owlready2_individual(self, i: OWLIndividual) -> owlready2.Thing:
        raise NotImplementedError(i)

    @_to_owlready2_individual.register
    def _(self, i: OWLNamedIndividual):
        return self._world[i.str]

    @map_concept.register
    def _(self, c: OWLClass) -> owlready2.ThingClass:
        x = self._world[c.str]
        try:
            assert x is not None
        except AssertionError:
            print(f"The world attribute{self._world} maps {c} into None")

        return x

    @map_concept.register
    def _(self, c: OWLObjectComplementOf) -> owlready2.class_construct.Not:
        return owlready2.Not(self.map_concept(c.get_operand()))

    @map_concept.register
    def _(self, ce: OWLObjectUnionOf) -> owlready2.class_construct.Or:
        return owlready2.Or(map(self.map_concept, ce.operands()))

    @map_concept.register
    def _(self, ce: OWLObjectIntersectionOf) -> owlready2.class_construct.And:
        return owlready2.And(map(self.map_concept, ce.operands()))

    @map_concept.register
    def _(self, ce: OWLObjectSomeValuesFrom) -> owlready2.class_construct.Restriction:
        prop = self._to_owlready2_property(ce.get_property())
        assert isinstance(ce.get_filler(),
                          OWLClassExpression), f"{ce.get_filler()} is not an OWL Class expression and cannot be serialized at the moment"
        return prop.some(self.map_concept(ce.get_filler()))

    @map_concept.register
    def _(self, ce: OWLObjectAllValuesFrom) -> owlready2.class_construct.Restriction:
        prop = self._to_owlready2_property(ce.get_property())
        return prop.only(self.map_concept(ce.get_filler()))

    @map_concept.register
    def _(self, ce: OWLObjectOneOf) -> owlready2.class_construct.OneOf:
        return owlready2.OneOf(list(map(self._to_owlready2_individual, ce.individuals())))

    @map_concept.register
    def _(self, ce: OWLObjectExactCardinality) -> owlready2.class_construct.Restriction:
        prop = self._to_owlready2_property(ce.get_property())
        return prop.exactly(ce.get_cardinality(), self.map_concept(ce.get_filler()))

    @map_concept.register
    def _(self, ce: OWLObjectMaxCardinality) -> owlready2.class_construct.Restriction:
        prop = self._to_owlready2_property(ce.get_property())
        return prop.max(ce.get_cardinality(), self.map_concept(ce.get_filler()))

    @map_concept.register
    def _(self, ce: OWLObjectMinCardinality) -> owlready2.class_construct.Restriction:
        prop = self._to_owlready2_property(ce.get_property())
        return prop.min(ce.get_cardinality(), self.map_concept(ce.get_filler()))

    @map_concept.register
    def _(self, ce: OWLObjectHasValue) -> owlready2.class_construct.Restriction:
        prop = self._to_owlready2_property(ce.get_property())
        return prop.value(self._to_owlready2_individual(ce.get_filler()))

    @map_concept.register
    def _(self, ce: OWLDataSomeValuesFrom) -> owlready2.class_construct.Restriction:
        prop = self._to_owlready2_property(ce.get_property())
        return prop.some(self.map_datarange(ce.get_filler()))

    @map_concept.register
    def _(self, ce: OWLDataAllValuesFrom) -> owlready2.class_construct.Restriction:
        prop = self._to_owlready2_property(ce.get_property())
        return prop.only(self.map_datarange(ce.get_filler()))

    @map_concept.register
    def _(self, ce: OWLDataExactCardinality) -> owlready2.class_construct.Restriction:
        prop = self._to_owlready2_property(ce.get_property())
        return prop.exactly(ce.get_cardinality(), self.map_datarange(ce.get_filler()))

    @map_concept.register
    def _(self, ce: OWLDataMaxCardinality) -> owlready2.class_construct.Restriction:
        prop = self._to_owlready2_property(ce.get_property())
        return prop.max(ce.get_cardinality(), self.map_datarange(ce.get_filler()))

    @map_concept.register
    def _(self, ce: OWLDataMinCardinality) -> owlready2.class_construct.Restriction:
        prop = self._to_owlready2_property(ce.get_property())
        return prop.min(ce.get_cardinality(), self.map_datarange(ce.get_filler()))

    @map_concept.register
    def _(self, ce: OWLDataHasValue) -> owlready2.class_construct.Restriction:
        prop = self._to_owlready2_property(ce.get_property())
        return prop.value(ce.get_filler().to_python())

    @singledispatchmethod
    def map_datarange(self, p: OWLDataRange) -> Union[owlready2.ClassConstruct, type]:
        """Map owlapy data range classes."""
        raise NotImplementedError(p)

    @map_datarange.register
    def _(self, p: OWLDataComplementOf) -> owlready2.class_construct.Not:
        return owlready2.Not(self.map_datarange(p.get_data_range()))

    @map_datarange.register
    def _(self, p: OWLDataUnionOf) -> owlready2.class_construct.Or:
        return owlready2.Or(map(self.map_datarange, p.operands()))

    @map_datarange.register
    def _(self, p: OWLDataIntersectionOf) -> owlready2.class_construct.And:
        return owlready2.And(map(self.map_datarange, p.operands()))

    @map_datarange.register
    def _(self, p: OWLDataOneOf) -> owlready2.class_construct.OneOf:
        return owlready2.OneOf([lit.to_python() for lit in p.operands()])

    @map_datarange.register
    def _(self, p: OWLDatatypeRestriction) -> owlready2.class_construct.ConstrainedDatatype:
        facet_args = dict()
        for facet_res in p.get_facet_restrictions():
            value = facet_res.get_facet_value().to_python()
            facet_key = OWLREADY2_FACET_KEYS[facet_res.get_facet()]
            facet_args[facet_key] = value
        return owlready2.ConstrainedDatatype(self.map_datarange(p.get_datatype()), **facet_args)

    @map_datarange.register
    def _(self, type_: OWLDatatype) -> type:
        if type_ == BooleanOWLDatatype:
            return bool
        elif type_ == DoubleOWLDatatype:
            return float
        elif type_ == IntegerOWLDatatype:
            return int
        elif type_ == StringOWLDatatype:
            return str
        elif type_ == DateOWLDatatype:
            return date
        elif type_ == DateTimeOWLDatatype:
            return datetime
        elif type_ == DurationOWLDatatype:
            return Timedelta
        else:
            raise ValueError(type_)


class FromOwlready2:
    """Map owlready2 classes to owlapy model classes."""
    __slots__ = ()

    @singledispatchmethod
    def map_concept(self, c: Union[owlready2.ClassConstruct, owlready2.ThingClass]) -> OWLClassExpression:
        """Map concept classes."""
        raise NotImplementedError(c)

    @singledispatchmethod
    def _from_owlready2_property(self, c: Union[owlready2.PropertyClass, owlready2.Inverse]) -> OWLPropertyExpression:
        raise NotImplementedError(c)

    @_from_owlready2_property.register
    def _(self, p: owlready2.ObjectPropertyClass) -> OWLObjectProperty:
        return OWLObjectProperty(IRI.create(p.iri))

    @_from_owlready2_property.register
    def _(self, p: owlready2.DataPropertyClass) -> OWLDataProperty:
        return OWLDataProperty(IRI.create(p.iri))

    @_from_owlready2_property.register
    def _(self, i: owlready2.Inverse) -> OWLObjectInverseOf:
        return OWLObjectInverseOf(self._from_owlready2_property(i.property))

    @map_concept.register
    def _(self, c: owlready2.ThingClass) -> OWLClass:
        return OWLClass(IRI.create(c.iri))

    @map_concept.register
    def _(self, c: owlready2.Not) -> OWLObjectComplementOf:
        return OWLObjectComplementOf(self.map_concept(c.Class))

    @map_concept.register
    def _(self, c: owlready2.And) -> OWLObjectIntersectionOf:
        return OWLObjectIntersectionOf(map(self.map_concept, c.Classes))

    @map_concept.register
    def _(self, c: owlready2.Or) -> OWLObjectUnionOf:
        return OWLObjectUnionOf(map(self.map_concept, c.Classes))

    @map_concept.register
    def _(self, c: owlready2.OneOf) -> OWLObjectOneOf:
        return OWLObjectOneOf([OWLNamedIndividual(IRI.create(ind.iri)) for ind in c.instances])

    @map_concept.register
    def _(self, c: owlready2.Restriction) -> OWLRestriction:
        if isinstance(c.property, owlready2.ObjectPropertyClass):
            return self._to_object_property(c)
        elif isinstance(c.property, owlready2.DataPropertyClass):
            return self._to_data_property(c)
        else:
            raise NotImplementedError(c)

    def _to_object_property(self, c: owlready2.Restriction) -> OWLObjectRestriction:
        p = self._from_owlready2_property(c.property)
        assert isinstance(p, OWLObjectPropertyExpression)

        if c.type == owlready2.VALUE:
            ind = OWLNamedIndividual(IRI.create(c.value.iri))
            return OWLObjectHasValue(p, ind)
        else:
            f = self.map_concept(c.value)
            if c.type == owlready2.SOME:
                return OWLObjectSomeValuesFrom(p, f)
            elif c.type == owlready2.ONLY:
                return OWLObjectAllValuesFrom(p, f)
            elif c.type == owlready2.EXACTLY:
                return OWLObjectExactCardinality(c.cardinality, p, f)
            elif c.type == owlready2.MIN:
                return OWLObjectMinCardinality(c.cardinality, p, f)
            elif c.type == owlready2.MAX:
                return OWLObjectMaxCardinality(c.cardinality, p, f)
            else:
                raise NotImplementedError(c)

    def _to_data_property(self, c: owlready2.Restriction) -> OWLDataRestriction:
        p = self._from_owlready2_property(c.property)
        assert isinstance(p, OWLDataPropertyExpression)

        if c.type == owlready2.VALUE:
            return OWLDataHasValue(p, OWLLiteral(c.value))
        else:
            f = self.map_datarange(c.value)
            if c.type == owlready2.SOME:
                return OWLDataSomeValuesFrom(p, f)
            elif c.type == owlready2.ONLY:
                return OWLDataAllValuesFrom(p, f)
            elif c.type == owlready2.EXACTLY:
                return OWLDataExactCardinality(c.cardinality, p, f)
            elif c.type == owlready2.MIN:
                return OWLDataMinCardinality(c.cardinality, p, f)
            elif c.type == owlready2.MAX:
                return OWLDataMaxCardinality(c.cardinality, p, f)
            else:
                raise NotImplementedError(c)

    @singledispatchmethod
    def map_datarange(self, p: owlready2.ClassConstruct) -> OWLDataRange:
        """Map data range classes."""
        raise NotImplementedError(p)

    @map_datarange.register
    def _(self, p: owlready2.Not) -> OWLDataComplementOf:
        return OWLDataComplementOf(self.map_datarange(p.Class))

    @map_datarange.register
    def _(self, p: owlready2.Or) -> OWLDataUnionOf:
        return OWLDataUnionOf(map(self.map_datarange, p.Classes))

    @map_datarange.register
    def _(self, p: owlready2.And) -> OWLDataIntersectionOf:
        return OWLDataIntersectionOf(map(self.map_datarange, p.Classes))

    @map_datarange.register
    def _(self, p: owlready2.OneOf) -> OWLDataOneOf:
        return OWLDataOneOf([OWLLiteral(i) for i in p.instances])

    @map_datarange.register
    def _(self, p: owlready2.ConstrainedDatatype) -> OWLDatatypeRestriction:
        restrictions = []
        for facet in OWLFacet:
            value = getattr(p, OWLREADY2_FACET_KEYS[facet], None)
            if value is not None:
                restrictions.append(OWLFacetRestriction(facet, OWLLiteral(value)))
        return OWLDatatypeRestriction(self.map_datarange(p.base_datatype), restrictions)

    @map_datarange.register
    def _(self, type_: type) -> OWLDatatype:
        if type_ is bool:
            return BooleanOWLDatatype
        elif type_ is float:
            return DoubleOWLDatatype
        elif type_ is int:
            return IntegerOWLDatatype
        elif type_ is str:
            return StringOWLDatatype
        elif type_ is date:
            return DateOWLDatatype
        elif type_ is datetime:
            return DateTimeOWLDatatype
        elif type_ is Timedelta:
            return DurationOWLDatatype
        else:
            raise ValueError(type_)


def is_valid_entity(text_input: str):
    return True if "/" in text_input else False


class NeuralOntology(AbstractOWLOntology):
    STR_IRI_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    STR_IRI_OWL_CLASS = "http://www.w3.org/2002/07/owl#Class"
    STR_IRI_OBJECT_PROPERTY = "http://www.w3.org/2002/07/owl#ObjectProperty"
    STR_IRI_DATA_PROPERTY = "http://www.w3.org/2002/07/owl#DatatypeProperty"

    def __init__(self, path_neural_embedding: str, train_if_not_exists: bool = False,
                 training_params: Optional[Dict[str, Any]] = None, batch_size: int = 1024, device: str = "gpu",
                 gamma: float = 0.5):
        """
        Initialize a Neural Ontology from a KGE model.

        Args:
            path_neural_embedding: Path to a pretrained KGE model, a directory containing a train.txt file or a .owl file
            train_if_not_exists: If True, train a new model if no pretrained model is found at the given path
            training_params: Optional dictionary of training parameters to override defaults
        """

        super().__init__()
        self.gamma = gamma

        path = Path(path_neural_embedding)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, "configuration.json")):
            # Path leads to a folder containing pretrained model
            self.model = KGE(path=path_neural_embedding)
        elif train_if_not_exists:
            # Train a new model
            self._train_model(path_neural_embedding, training_params)
        else:
            raise ValueError(
                f"No pretrained KGE model found at {path_neural_embedding} and train_if_not_exists is False")
        self.batch_size = batch_size

        if device == "gpu" and torch.cuda.is_available():
            self.model.to("cuda")
            print("EBR inference on GPU")
        elif device == "cpu":
            self.model.to("cpu")
            print("EBR inference on CPU")
        else:
            # warning
            print(f"Device {device} not supported, EBR will use CPU")

    def _train_model(self, path: str, training_params: Optional[Dict[str, Any]] = None):
        """
        Train a new KGE model with the given parameters.

        Args:
            path: Path to a directory containing train.txt or to the dataset directory
            training_params: Optional dictionary of training parameters
        """
        args = Namespace()

        # Set default parameters
        args.model = 'Keci'
        args.scoring_technique = "AllvsAll"
        if os.path.isdir(path):
            args.dataset_dir = path
            args.path_single_kg = None
        else:
            args.path_single_kg = path
            if path.endswith(".owl"):
                args.backend = "rdflib"
            path = os.path.dirname(path)

        args.trainer = "PL"
        # Always include the file name in the path
        file_name = os.path.basename(args.path_single_kg).replace(".owl", "")
        args.path_to_store_single_run = os.path.join(path, f"{file_name}_trained_model")
        args.num_epochs = 500
        args.embedding_dim = 512
        args.batch_size = 64

        # Override with user-provided parameters if any
        if training_params is not None:
            for key, value in training_params.items():
                setattr(args, key, value)

        # Train the model
        Execute(args).start()

        # Load the trained model
        self.model = KGE(path=args.path_to_store_single_run)

    def predict(self, h: List[str] = None, r: List[str] = None, t: List[str] = None) -> List[Tuple[str, float]]:
        if r is None:
            topk = len(self.model.relation_to_idx)
        else:
            topk = len(self.model.entity_to_idx)

        return [(top_entity, score) for row in
                self.model.predict_topk(h=h, r=r, t=t, topk=topk, batch_size=self.batch_size) for top_entity, score in
                row if score >= self.gamma and is_valid_entity(top_entity)]

    def classes_in_signature(self) -> List[OWLClass]:
        return [OWLClass(top_entity) for top_entity, score in self.predict(h=None,
                                                                           r=self.STR_IRI_TYPE,
                                                                           t=self.STR_IRI_OWL_CLASS)]

    def individuals_in_signature(self) -> List[OWLNamedIndividual]:
        set_str_entities = set()
        for top_entity, score in self.predict(h=None,
                                              r=self.STR_IRI_TYPE,
                                              t=[owl_class.iri.str for owl_class in self.classes_in_signature()]):
            set_str_entities.add(top_entity)
        return [OWLNamedIndividual(entity) for entity in set_str_entities]

    def data_properties_in_signature(self) -> List[OWLDataProperty]:
        return [OWLDataProperty(top_entity) for top_entity, score in self.predict(h=None,
                                                                                  r=self.STR_IRI_TYPE,
                                                                                  t=self.STR_IRI_DATA_PROPERTY)]

    def object_properties_in_signature(self) -> List[OWLObjectProperty]:
        return [OWLObjectProperty(top_entity) for top_entity, score in self.predict(h=None,
                                                                                    r=self.STR_IRI_TYPE,
                                                                                    t=self.STR_IRI_OBJECT_PROPERTY)]

    def equivalent_classes_axioms(self, c: OWLClass) -> Iterable[OWLEquivalentClassesAxiom]:
        raise NotImplementedError("Not implemented")

    def general_class_axioms(self) -> Iterable[OWLClassAxiom]:
        raise NotImplementedError("Not implemented")

    def data_property_domain_axioms(self, property: OWLDataProperty) -> Iterable[OWLDataPropertyDomainAxiom]:
        raise NotImplementedError("Not implemented")

    def data_property_range_axioms(self, property: OWLDataProperty) -> Iterable[OWLDataPropertyRangeAxiom]:
        raise NotImplementedError("Not implemented")

    def object_property_domain_axioms(self, property: OWLObjectProperty) -> Iterable[OWLObjectPropertyDomainAxiom]:
        raise NotImplementedError("Not implemented")

    def get_ontology_id(self) -> _OI:
        raise NotImplementedError("Not implemented")

    # LF: here we would need to retrain? -> ie we would need to store / have the path for the underlying ontology?
    def add_axiom(self, axiom: Union[OWLAxiom, Iterable[OWLAxiom]]):
        raise NotImplementedError("Not implemented")

    def remove_axiom(self, axiom: Union[OWLAxiom, Iterable[OWLAxiom]]):
        raise NotImplementedError("Not implemented")

    def save(self, document_iri: Optional[IRI] = None):
        raise NotImplementedError("Not implemented")

    def __eq__(self, other):
        return self.model == other.model

    def __hash__(self):
        return hash(self.model)

    def __repr__(self):
        return f"NeuralOntology(model={self.model})"

    def object_property_range_axioms(self, property: OWLObjectProperty) -> Iterable[OWLObjectPropertyRangeAxiom]:
        raise NotImplementedError("Not implemented")


_parse_concept_to_owlapy = FromOwlready2().map_concept
_parse_datarange_to_owlapy = FromOwlready2().map_datarange