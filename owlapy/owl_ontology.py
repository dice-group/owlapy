"""OWL Ontology"""
from abc import ABCMeta, abstractmethod
from typing import Iterable, TypeVar, Final, Optional
from owlapy.owl_axiom import OWLEquivalentClassesAxiom, OWLClassAxiom, OWLDataPropertyDomainAxiom, \
    OWLDataPropertyRangeAxiom, OWLObjectPropertyDomainAxiom, OWLObjectPropertyRangeAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_object import OWLObject
from owlapy.iri import IRI
from owlapy.class_expression import OWLClass
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty


_M = TypeVar('_M', bound='OWLOntologyManager')


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


