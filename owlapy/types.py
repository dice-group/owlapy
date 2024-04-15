"""OWL Datatype"""
from .owlobject import OWLEntity
from .data_ranges import OWLDataRange
from .iri import IRI
from .meta_classes import HasIRI
from typing import Final, Union


class OWLDatatype(OWLEntity, OWLDataRange):
    """Datatypes are entities that refer to sets of data values. Thus, datatypes are analogous to classes,
    the main difference being that the former contain data values such as strings and numbers, rather than individuals.
    Datatypes are a kind of data range, which allows them to be used in restrictions. Each data range is associated
    with an arity; for datatypes, the arity is always one. The built-in datatype rdfs:Literal denotes any set of data
    values that contains the union of the value spaces of all datatypes.

    (https://www.w3.org/TR/owl2-syntax/#Datatypes)
    """
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
