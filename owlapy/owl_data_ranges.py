"""OWL Data Ranges

https://www.w3.org/TR/owl2-syntax/#Data_Ranges

DataRange := Datatype | DataIntersectionOf | DataUnionOf | DataComplementOf | DataOneOf | DatatypeRestriction
"""
from abc import ABCMeta
from typing import TYPE_CHECKING, Final, Iterable, Sequence, Set

from .meta_classes import HasOperands
from .owl_object import OWLObject

if TYPE_CHECKING:
    from .owl_object import OWLEntity


class OWLPropertyRange(OWLObject, metaclass=ABCMeta):
    """OWL Objects that can be the ranges of properties."""

    def signature(self) -> Set['OWLEntity']:
        """Gets the set of named entities (classes, object/data properties, individuals, datatypes) that are
        used in this class expression/data range.

        Note:
            Coverage is currently limited to a core set of constructs; see
            :class:`owlapy.utils.SignatureExtractor` and
            https://github.com/dice-group/owlapy/issues/231 for remaining gaps.

        Returns:
            The signature of this class expression/data range.
        """
        from owlapy.utils import SignatureExtractor
        return SignatureExtractor().get_signature(self)


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
        operands = tuple(operands)
        for i, op in enumerate(operands):
            # NB: checked against OWLPropertyRange (the common base of OWLDataRange and
            # OWLClassExpression), not OWLDataRange itself -- owlapy.utils.nnf.NNF deliberately
            # reuses this constructor to combine data-property restriction class expressions
            # (e.g. OWLDataSomeValuesFrom) during negation, not just genuine data ranges.
            if not isinstance(op, OWLPropertyRange):
                raise TypeError(
                    f"Expected all operands to be instances of OWLPropertyRange, got {type(op).__name__} instead ({op!r}) at index {i}."
                )
        self._operands = operands

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
        return hash((type(self).__name__, self._operands))


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
        # NB: checked against OWLPropertyRange, not OWLDataRange -- see OWLNaryDataRange.__init__.
        if not isinstance(data_range, OWLPropertyRange):
            raise TypeError(
                f"Expected 'data_range' to be an instance of OWLPropertyRange, got {type(data_range).__name__} instead ({data_range!r})."
            )
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
        return False

    def __hash__(self):
        return hash(("OWLDataComplementOf", self._data_range))
