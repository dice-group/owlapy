from abc import abstractmethod, ABCMeta
from ..owlobject import OWLObject, OWLEntity
from ..meta_classes import HasOperands
from typing import Final, Iterable, Sequence
from ..ranges import OWLPropertyRange, OWLDataRange
from ..owl_literal import OWLLiteral
from typing import Final, Sequence, Union, Iterable
from ..iri import IRI

class OWLDataComplementOf(OWLDataRange):
    """Represents DataComplementOf in the OWL 2 Specification."""
    type_index: Final = 4002

    _data_range: OWLDataRange

    def __init__(self, data_range: OWLDataRange):
        """
        Args:
            data_range: Data range to complement.
        """
        self._data_range = data_range

    def get_data_range(self) -> OWLDataRange:
        """
        Returns:
            The wrapped data range.
        """
        return self._data_range

    def __repr__(self):
        return f"OWLDataComplementOf({repr(self._data_range)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._data_range == other._data_range
        return NotImplemented

    def __hash__(self):
        return hash(self._data_range)

class OWLNaryDataRange(OWLDataRange, HasOperands[OWLDataRange]):
    """OWLNaryDataRange."""
    __slots__ = ()

    _operands: Sequence[OWLDataRange]

    def __init__(self, operands: Iterable[OWLDataRange]):
        """
        Args:
            operands: Data ranges.
        """
        self._operands = tuple(operands)

    def operands(self) -> Iterable[OWLDataRange]:
        # documented in parent
        yield from self._operands

    def __repr__(self):
        return f'{type(self).__name__}({repr(self._operands)})'

    def __eq__(self, other):
        if type(other) == type(self):
            return self._operands == other._operands
        return NotImplemented

    def __hash__(self):
        return hash(self._operands)

class OWLDataUnionOf(OWLNaryDataRange):
    """Represents a DataUnionOf data range in the OWL 2 Specification."""
    __slots__ = '_operands'
    type_index: Final = 4005

    _operands: Sequence[OWLDataRange]

class OWLDataIntersectionOf(OWLNaryDataRange):
    """Represents DataIntersectionOf  in the OWL 2 Specification."""
    __slots__ = '_operands'
    type_index: Final = 4004

    _operands: Sequence[OWLDataRange]

