"""OWL Data Ranges

https://www.w3.org/TR/owl2-syntax/#Data_Ranges

DataRange := Datatype | DataIntersectionOf | DataUnionOf | DataComplementOf | DataOneOf | DatatypeRestriction
"""
from .owl_object import OWLObject
from .meta_classes import HasOperands
from typing import Final, Sequence, Iterable

from abc import ABCMeta


class OWLPropertyRange(OWLObject, metaclass=ABCMeta):
    """OWL Objects that can be the ranges of properties."""


class OWLDataRange(OWLPropertyRange, metaclass=ABCMeta):
    """Represents a DataRange in the OWL 2 Specification."""


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
        if type(other) is type(self):
            return (set(self._operands) == set(other._operands)
                    and len(list((self._operands))) == len(list((other._operands))))
        return False

    def __hash__(self):
        return hash(self._operands)


class OWLDataIntersectionOf(OWLNaryDataRange):
    """An intersection data range DataIntersectionOf( DR1 ... DRn ) contains all tuples of literals that are contained
    in each data range DRi for 1 ≤ i ≤ n. All data ranges DRi must be of the same arity, and the resulting data range
    is of that arity as well.

    (https://www.w3.org/TR/owl2-syntax/#Intersection_of_Data_Ranges)
    """
    __slots__ = '_operands'
    type_index: Final = 4004

    _operands: Sequence[OWLDataRange]


class OWLDataUnionOf(OWLNaryDataRange):
    """A union data range DataUnionOf( DR1 ... DRn ) contains all tuples of literals that are contained in the at least
     one data range DRi for 1 ≤ i ≤ n. All data ranges DRi must be of the same arity, and the resulting data range is of
     that arity as well.

     (https://www.w3.org/TR/owl2-syntax/#Union_of_Data_Ranges)"""
    __slots__ = '_operands'
    type_index: Final = 4005

    _operands: Sequence[OWLDataRange]


class OWLDataComplementOf(OWLDataRange):
    """A complement data range DataComplementOf( DR ) contains all tuples of literals that are not contained in the
    data range DR. The resulting data range has the arity equal to the arity of DR.

    (https://www.w3.org/TR/owl2-syntax/#Complement_of_Data_Ranges)
    """
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
