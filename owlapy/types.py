from .owlobject import OWLObject, OWLEntity
from .ranges import OWLDataRange
from .iri import IRI
from .has import HasIRI
from typing import Final, Union

class OWLDatatype(OWLEntity, OWLDataRange):
    """Represents a Datatype (named data range) in the OWL 2 Specification."""
    __slots__ = '_iri'

    type_index: Final = 4001

    _iri: IRI

    def __init__(self, iri: Union[IRI, HasIRI]):
        """Gets an instance of OWLDatatype that has the specified IRI.

        Args:
            iri: The IRI.
        """
        if isinstance(iri, HasIRI):
            self._iri = iri.get_iri()
        else:
            assert isinstance(iri, IRI)
            self._iri = iri

    def get_iri(self) -> IRI:
        # documented in parent
        return self._iri
