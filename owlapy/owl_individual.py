"""OWL Individuals"""
from abc import ABCMeta
from .owl_object import OWLObject, OWLEntity
from .iri import IRI
from typing import Final, Union


class OWLIndividual(OWLObject, metaclass=ABCMeta):
    """Represents a named or anonymous individual."""
    __slots__ = ()
    pass


class OWLNamedIndividual(OWLIndividual, OWLEntity):
    """Named individuals are identified using an IRI. Since they are given an IRI, named individuals are entities.
        IRIs from the reserved vocabulary must not be used to identify named individuals in an OWL 2 DL ontology.

        (https://www.w3.org/TR/owl2-syntax/#Named_Individuals)
        """
    __slots__ = '_iri'
    type_index: Final = 1005

    _iri: IRI

    def __init__(self, iri: Union[IRI, str]):
        """Gets an instance of OWLNamedIndividual that has the specified IRI.

        Args:
            iri: an instance of IRI Class or a string representing the iri

        Returns:
            An OWLNamedIndividual that has the specified IRI.
        """
        if isinstance(iri, IRI):
            self._iri = iri
        else:
            self._iri = IRI.create(iri)
    @property
    def iri(self) -> IRI:
        return self._iri
    @property
    def str(self):
        return self._iri.as_str()
    @property
    def remainder(self):
        return self._iri.remainder