"""OWL Ontology"""
from abc import ABCMeta, abstractmethod
from functools import singledispatchmethod
from itertools import chain
from types import MappingProxyType
from typing import Iterable, TypeVar, Final, Optional, Union
import logging
import owlready2
from pandas import Timedelta
from owlapy import namespaces
from owlapy.owl_axiom import OWLEquivalentClassesAxiom, OWLClassAxiom, OWLDataPropertyDomainAxiom, \
    OWLDataPropertyRangeAxiom, OWLObjectPropertyDomainAxiom, OWLObjectPropertyRangeAxiom, OWLSubClassOfAxiom, \
    OWLAnnotationProperty
from owlapy.owl_data_ranges import OWLDataRange, OWLDataComplementOf, OWLDataUnionOf, OWLDataIntersectionOf
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_individual import OWLNamedIndividual, OWLIndividual
from owlapy.owl_literal import IntegerOWLDatatype, DoubleOWLDatatype, BooleanOWLDatatype, StringOWLDatatype, \
    DateOWLDatatype, DateTimeOWLDatatype, DurationOWLDatatype, OWLLiteral
from owlapy.owl_object import OWLObject
from owlapy.iri import IRI
from owlapy.class_expression import OWLClass, OWLThing, OWLClassExpression, OWLObjectComplementOf, OWLObjectUnionOf, \
    OWLObjectIntersectionOf, OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom, OWLObjectOneOf, OWLObjectExactCardinality, \
    OWLObjectMaxCardinality, OWLObjectMinCardinality, OWLObjectHasValue, OWLDataSomeValuesFrom, OWLDataAllValuesFrom, \
    OWLDataExactCardinality, OWLDataMaxCardinality, OWLDataMinCardinality, OWLDataHasValue, OWLDataOneOf, \
    OWLDatatypeRestriction, OWLRestriction, OWLObjectRestriction, OWLDataRestriction, OWLFacetRestriction
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty, OWLPropertyExpression, OWLObjectInverseOf, \
    OWLObjectPropertyExpression, OWLDataPropertyExpression
from datetime import date, datetime

from owlapy.vocab import OWLFacet

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

_M = TypeVar('_M', bound='OWLOntologyManager')
_SM = TypeVar('_SM', bound='SyncOntologyManager')


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


class OWLOntology(OWLObject, metaclass=ABCMeta):
    """Represents an OWL 2 Ontology  in the OWL 2 specification.

    An OWLOntology consists of a possibly empty set of OWLAxioms and a possibly empty set of OWLAnnotations.
    An ontology can have an ontology IRI which can be used to identify the ontology. If it has an ontology IRI then
    it may also have an ontology version IRI. Since OWL 2, an ontology need not have an ontology IRI. (See the OWL 2
    Structural Specification).

    An ontology cannot be modified directly. Changes must be applied via its OWLOntologyManager.
    """
    __slots__ = ()
    type_index: Final = 1

    @abstractmethod
    def classes_in_signature(self) -> Iterable[OWLClass]:
        """Gets the classes in the signature of this object.

        Returns:
            Classes in the signature of this object.
        """
        pass

    @abstractmethod
    def data_properties_in_signature(self) -> Iterable[OWLDataProperty]:
        """Get the data properties that are in the signature of this object.

        Returns:
            Data properties that are in the signature of this object.
        """
        pass

    @abstractmethod
    def object_properties_in_signature(self) -> Iterable[OWLObjectProperty]:
        """A convenience method that obtains the object properties that are in the signature of this object.

        Returns:
            Object properties that are in the signature of this object.
        """
        pass

    @abstractmethod
    def individuals_in_signature(self) -> Iterable[OWLNamedIndividual]:
        """A convenience method that obtains the individuals that are in the signature of this object.

        Returns:
            Individuals that are in the signature of this object.
        """
        pass

    @abstractmethod
    def equivalent_classes_axioms(self, c: OWLClass) -> Iterable[OWLEquivalentClassesAxiom]:
        """ Gets all of the equivalent axioms in this ontology that contain the specified class as an operand.

        Args:
            c: The class for which the EquivalentClasses axioms should be retrieved.

        Returns:
            EquivalentClasses axioms contained in this ontology.
        """
        pass

    @abstractmethod
    def general_class_axioms(self) -> Iterable[OWLClassAxiom]:
        """Get the general class axioms of this ontology. This includes SubClass axioms with a complex class expression
           as the sub class and EquivalentClass axioms and DisjointClass axioms with only complex class expressions.

        Returns:
            General class axioms contained in this ontology.
        """
        pass

    @abstractmethod
    def data_property_domain_axioms(self, property: OWLDataProperty) -> Iterable[OWLDataPropertyDomainAxiom]:
        """Gets the OWLDataPropertyDomainAxiom objects where the property is equal to the specified property.

        Args:
            property: The property which is equal to the property of the retrieved axioms.

        Returns:
            The axioms matching the search.
        """
        pass

    @abstractmethod
    def data_property_range_axioms(self, property: OWLDataProperty) -> Iterable[OWLDataPropertyRangeAxiom]:
        """Gets the OWLDataPropertyRangeAxiom objects where the property is equal to the specified property.

        Args:
            property: The property which is equal to the property of the retrieved axioms.

        Returns:
            The axioms matching the search.
        """
        pass

    @abstractmethod
    def object_property_domain_axioms(self, property: OWLObjectProperty) -> Iterable[OWLObjectPropertyDomainAxiom]:
        """Gets the OWLObjectPropertyDomainAxiom objects where the property is equal to the specified property.

        Args:
            property: The property which is equal to the property of the retrieved axioms.

        Returns:
            The axioms matching the search.
        """
        pass

    @abstractmethod
    def object_property_range_axioms(self, property: OWLObjectProperty) -> Iterable[OWLObjectPropertyRangeAxiom]:
        """Gets the OWLObjectPropertyRangeAxiom objects where the property is equal to the specified property.

        Args:
            property: The property which is equal to the property of the retrieved axioms.

        Returns:
            The axioms matching the search.
        """
        pass

    @abstractmethod
    def get_owl_ontology_manager(self) -> _M:
        """Gets the manager that manages this ontology."""
        pass

    @abstractmethod
    def get_ontology_id(self) -> OWLOntologyID:
        """Gets the OWLOntologyID belonging to this object.

        Returns:
            The OWLOntologyID.
        """
        pass

    def is_anonymous(self) -> bool:
        """Check whether this ontology does contain an IRI or not."""
        return self.get_ontology_id().is_anonymous()


class Ontology(OWLOntology):
    __slots__ = '_manager', '_iri', '_world', '_onto'

    _manager: 'OntologyManager'
    _onto: owlready2.Ontology
    _world: owlready2.World

    def __init__(self, manager: 'OntologyManager', ontology_iri: IRI, load: bool):
        """Represents an Ontology in Ontolearn.

        Args:
            manager: Ontology manager.
            ontology_iri: IRI of the ontology.
            load: Whether to load the ontology or not.
        """
        self._manager = manager
        self._iri = ontology_iri
        self._world = manager._world
        onto = self._world.get_ontology(ontology_iri.as_str())
        if load:
            onto = onto.load()
        self._onto = onto

    def classes_in_signature(self) -> Iterable[OWLClass]:
        for c in self._onto.classes():
            yield OWLClass(IRI.create(c.iri))

    def data_properties_in_signature(self) -> Iterable[OWLDataProperty]:
        for dp in self._onto.data_properties():
            yield OWLDataProperty(IRI.create(dp.iri))

    def object_properties_in_signature(self) -> Iterable[OWLObjectProperty]:
        for op in self._onto.object_properties():
            yield OWLObjectProperty(IRI.create(op.iri))

    def individuals_in_signature(self) -> Iterable[OWLNamedIndividual]:
        for i in self._onto.individuals():
            yield OWLNamedIndividual(IRI.create(i.iri))

    def equivalent_classes_axioms(self, c: OWLClass) -> Iterable[OWLEquivalentClassesAxiom]:
        c_x: owlready2.ThingClass = self._world[c.str]
        # TODO: Should this also return EquivalentClasses general class axioms? Compare to java owlapi
        for ec_x in c_x.equivalent_to:
            yield OWLEquivalentClassesAxiom([c, _parse_concept_to_owlapy(ec_x)])

    def general_class_axioms(self) -> Iterable[OWLClassAxiom]:
        # TODO: At the moment owlready2 only supports SubClassOf general class axioms. (18.02.2023)
        for ca in self._onto.general_class_axioms():
            yield from (OWLSubClassOfAxiom(_parse_concept_to_owlapy(ca.left_side), _parse_concept_to_owlapy(c))
                        for c in ca.is_a)

    def get_owl_ontology_manager(self) -> 'OntologyManager':
        return self._manager

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

    def get_original_iri(self):
        """Get the IRI argument that was used to create this ontology."""
        return self._iri

    def __eq__(self, other):
        if type(other) == type(self):
            return self._onto.loaded == other._onto.loaded and self._onto.base_iri == other._onto.base_iri
        return NotImplemented

    def __hash__(self):
        return hash(self._onto.base_iri)

    def __repr__(self):
        return f'Ontology({IRI.create(self._onto.base_iri)}, {self._onto.loaded})'


class SyncOntology(OWLOntology):

    def __init__(self, manager: _SM, iri: IRI, new: bool = False):
        from owlapy.owlapi_mapper import OWLAPIMapper
        from java.io import File
        from java.util.stream import Stream
        self.manager = manager
        self._iri = iri
        if new:  # create new ontology
            self.owlapi_ontology = manager.createOntology(Stream.empty(), File(iri.str))
        else:  # means we are loading an existing ontology
            self.owlapi_ontology = manager.get_owlapi_manager().loadOntologyFromOntologyDocument(File(iri.str))
        self.mapper = OWLAPIMapper(self)

    def classes_in_signature(self) -> Iterable[OWLClass]:
        pass

    def data_properties_in_signature(self) -> Iterable[OWLDataProperty]:
        pass

    def object_properties_in_signature(self) -> Iterable[OWLObjectProperty]:
        pass

    def individuals_in_signature(self) -> Iterable[OWLNamedIndividual]:
        pass

    def equivalent_classes_axioms(self, c: OWLClass) -> Iterable[OWLEquivalentClassesAxiom]:
        pass

    def general_class_axioms(self) -> Iterable[OWLClassAxiom]:
        pass

    def data_property_domain_axioms(self, property: OWLDataProperty) -> Iterable[OWLDataPropertyDomainAxiom]:
        pass

    def data_property_range_axioms(self, property: OWLDataProperty) -> Iterable[OWLDataPropertyRangeAxiom]:
        pass

    def object_property_domain_axioms(self, property: OWLObjectProperty) -> Iterable[OWLObjectPropertyDomainAxiom]:
        pass

    def object_property_range_axioms(self, property: OWLObjectProperty) -> Iterable[OWLObjectPropertyRangeAxiom]:
        pass

    def get_owl_ontology_manager(self) -> _M:
        pass

    def get_owlapi_ontology(self):
        return self.owlapi_ontology

    def get_ontology_id(self) -> OWLOntologyID:
        pass

    def __eq__(self, other):
        pass

    def __hash__(self):
        pass

    def __repr__(self):
        pass




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
    def _(self, ont: OWLOntology) -> owlready2.namespace.Ontology:
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
        if type_ == bool:
            return BooleanOWLDatatype
        elif type_ == float:
            return DoubleOWLDatatype
        elif type_ == int:
            return IntegerOWLDatatype
        elif type_ == str:
            return StringOWLDatatype
        elif type_ == date:
            return DateOWLDatatype
        elif type_ == datetime:
            return DateTimeOWLDatatype
        elif type_ == Timedelta:
            return DurationOWLDatatype
        else:
            raise ValueError(type_)


_parse_concept_to_owlapy = FromOwlready2().map_concept
_parse_datarange_to_owlapy = FromOwlready2().map_datarange