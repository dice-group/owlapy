from abc import ABCMeta
from .owlobject import OWLObject, OWLEntity
from .iri import IRI
from typing import Final, Union
class OWLIndividual(OWLObject, metaclass=ABCMeta):
    """Represents a named or anonymous individual."""
    __slots__ = ()
    pass

class OWLNamedIndividual(OWLIndividual, OWLEntity):
    """Represents a Named Individual in the OWL 2 Specification."""
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

    def get_iri(self) -> IRI:
        # TODO:CD: can be deprecated
        # documented in parent
        return self._iri

    @property
    def iri(self):
        return self._iri

    @property
    def str(self):
        return self._iri.as_str()
