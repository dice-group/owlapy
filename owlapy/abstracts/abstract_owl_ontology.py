from abc import ABCMeta, abstractmethod
from typing import Final, Iterable, Union, Optional, TypeVar

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLEquivalentClassesAxiom, OWLClassAxiom, OWLDataPropertyDomainAxiom, \
    OWLDataPropertyRangeAxiom, OWLObjectPropertyDomainAxiom, OWLObjectPropertyRangeAxiom, OWLAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_object import OWLObject
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty

_OI = TypeVar('_OI', bound='OWLOntologyID')  # noqa: F821


class AbstractOWLOntology(OWLObject, metaclass=ABCMeta):
    """Represents an OWL 2 Ontology  in the OWL 2 specification.

    An OWLOntology consists of a possibly empty set of OWLAxioms and a possibly empty set of OWLAnnotations.
    An ontology can have an ontology IRI which can be used to identify the ontology. If it has an ontology IRI then
    it may also have an ontology version IRI. Since OWL 2, an ontology need not have an ontology IRI. (See the OWL 2
    Structural Specification).
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
    def get_ontology_id(self) -> _OI:
        """Gets the OWLOntologyID belonging to this object.

        Returns:
            The OWLOntologyID.
        """
        pass

    def is_anonymous(self) -> bool:
        """Check whether this ontology does contain an IRI or not."""
        return self.get_ontology_id().is_anonymous()

    @abstractmethod
    def add_axiom(self, axiom: Union[OWLAxiom, Iterable[OWLAxiom]]):
        """Add the specified axiom/axioms to the ontology.

        Args:
            axiom: Can be a single axiom or a collection of axioms.

        Returns:
            Nothing.
        """
        pass

    @abstractmethod
    def remove_axiom(self, axiom: Union[OWLAxiom, Iterable[OWLAxiom]]):
        """Removes the specified axiom/axioms to the ontology.

        Args:
            axiom: Can be a single axiom or a collection of axioms.

        Returns:
            Nothing.
        """
        pass

    @abstractmethod
    def save(self, document_iri: Optional[IRI] = None):
        """Saves this ontology, using its IRI to determine where/how the ontology should be
         saved.

         Args:
             document_iri: Whether you want to save in a different location.

        """
        pass
