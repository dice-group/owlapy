from abc import ABCMeta, abstractmethod
from typing import Union

from owlapy.abstracts.abstract_owl_ontology import OWLOntology
from owlapy.iri import IRI


class OWLOntologyChange(metaclass=ABCMeta):
    """Represents an ontology change."""
    __slots__ = ()

    _ont: OWLOntology

    @abstractmethod
    def __init__(self, ontology: OWLOntology):
        self._ont = ontology

    def get_ontology(self) -> OWLOntology:
        """Gets the ontology that the change is/was applied to.

        Returns:
            The ontology that the change is applicable to.
        """
        return self._ont


class OWLOntologyManager(metaclass=ABCMeta):
    """An OWLOntologyManager manages a set of ontologies. It is the main point for creating, loading and accessing
    ontologies."""

    @abstractmethod
    def create_ontology(self, iri: Union[str, IRI]) -> OWLOntology:
        """Creates a new (empty) ontology that that has the specified ontology IRI (and no version IRI).

        Args:
            iri: The IRI of the ontology to be created, can also be a string.

        Returns:
            The newly created ontology.
        """
        pass

    @abstractmethod
    def load_ontology(self, iri: Union[IRI, str]) -> OWLOntology:
        """Loads an ontology that is assumed to have the specified ontology IRI as its IRI or version IRI. The ontology
        IRI will be mapped to an ontology document IRI.

        Args:
            iri: The IRI that identifies the ontology, can also be a string.
                 It is expected that the ontology will also have this IRI
                (although the OWL API should tolerate situations where this is not the case).

        Returns:
            The OWLOntology representation of the ontology that was loaded.
        """
        pass

    @abstractmethod
    def apply_change(self, change: OWLOntologyChange):
        """A convenience method that applies just one change to an ontology. When this method is used through an
        OWLOntologyManager implementation, the instance used should be the one that the ontology returns through the
        get_owl_ontology_manager() call.

        Args:
            change: The change to be applied.

        Raises:
            ChangeApplied.UNSUCCESSFULLY: if the change was not applied successfully.
        """
        pass
