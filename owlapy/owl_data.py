from .ranges import OWLDataRange

from .owl_restriction import OWLHasValueRestriction, OWLDataRestriction, OWLDataCardinalityRestriction, OWLQuantifiedDataRestriction
from .owl_literal import OWLLiteral
from .has import HasOperands
from typing import Final, Sequence, Union, Iterable
from .owl_property import OWLDataPropertyExpression
from .owl_class_expression import OWLClassExpression

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
class OWLDataHasValue(OWLHasValueRestriction[OWLLiteral], OWLDataRestriction):
    """Represents DataHasValue restrictions in the OWL 2 Specification."""
    __slots__ = '_property'

    type_index: Final = 3014

    _property: OWLDataPropertyExpression

    def __init__(self, property: OWLDataPropertyExpression, value: OWLLiteral):
        """Gets an OWLDataHasValue restriction.

        Args:
            property: The data property that the restriction acts along.
            filler: The literal value.

        Returns:
            An OWLDataHasValue restriction along the specified property with the specified literal.
        """
        super().__init__(value)
        self._property = property

    def __repr__(self):
        return f"OWLDataHasValue(property={repr(self._property)},value={repr(self._v)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._v == other._v and self._property == other._property
        return NotImplemented

    def __hash__(self):
        return hash((self._v, self._property))

    def as_some_values_from(self) -> OWLClassExpression:
        """A convenience method that obtains this restriction as an existential restriction with a nominal filler.

        Returns:
            The existential equivalent of this value restriction. simp(HasValue(p a)) = some(p {a}).
        """
        return OWLDataSomeValuesFrom(self.get_property(), OWLDataOneOf(self.get_filler()))

    def get_property(self) -> OWLDataPropertyExpression:
        # documented in parent
        return self._property

class OWLDataMaxCardinality(OWLDataCardinalityRestriction):
    """Represents DataMaxCardinality restrictions in the OWL 2 Specification."""
    __slots__ = '_cardinality', '_filler', '_property'

    type_index: Final = 3017

    def __init__(self, cardinality: int, property: OWLDataPropertyExpression, filler: OWLDataRange):
        """
        Args:
            cardinality: Cannot be negative.
            property: The property that the restriction acts along.
            filler: Data range for restriction.

        Returns:
            A DataMaxCardinality on the specified property.
        """
        super().__init__(cardinality, property, filler)
class OWLDataMinCardinality(OWLDataCardinalityRestriction):
    """Represents DataMinCardinality restrictions in the OWL 2 Specification."""
    __slots__ = '_cardinality', '_filler', '_property'

    type_index: Final = 3015

    def __init__(self, cardinality: int, property: OWLDataPropertyExpression, filler: OWLDataRange):
        """
        Args:
            cardinality: Cannot be negative.
            property: The property that the restriction acts along.
            filler: Data range for restriction.

        Returns:
            A DataMinCardinality on the specified property.
        """
        super().__init__(cardinality, property, filler)
class OWLDataOneOf(OWLDataRange, HasOperands[OWLLiteral]):
    """Represents DataOneOf in the OWL 2 Specification."""
    type_index: Final = 4003

    _values: Sequence[OWLLiteral]

    def __init__(self, values: Union[OWLLiteral, Iterable[OWLLiteral]]):
        if isinstance(values, OWLLiteral):
            self._values = values,
        else:
            for _ in values:
                assert isinstance(_, OWLLiteral)
            self._values = tuple(values)

    def values(self) -> Iterable[OWLLiteral]:
        """Gets the values that are in the oneOf.

         Returns:
             The values of this {@code DataOneOf} class expression.
        """
        yield from self._values

    def operands(self) -> Iterable[OWLLiteral]:
        # documented in parent
        yield from self.values()

    def __hash__(self):
        return hash(self._values)

    def __eq__(self, other):
        if type(other) == type(self):
            return self._values == other._values
        return NotImplemented

    def __repr__(self):
        return f'OWLDataOneOf({self._values})'
class OWLDataSomeValuesFrom(OWLQuantifiedDataRestriction):
    """Represents a DataSomeValuesFrom restriction in the OWL 2 Specification."""
    __slots__ = '_property'

    type_index: Final = 3012

    _property: OWLDataPropertyExpression

    def __init__(self, property: OWLDataPropertyExpression, filler: OWLDataRange):
        """Gets an OWLDataSomeValuesFrom restriction.

        Args:
            property: The data property that the restriction acts along.
            filler: The data range that is the filler.

        Returns:
            An OWLDataSomeValuesFrom restriction along the specified property with the specified filler.
        """
        super().__init__(filler)
        self._property = property

    def __repr__(self):
        return f"OWLDataSomeValuesFrom(property={repr(self._property)},filler={repr(self._filler)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._filler == other._filler and self._property == other._property
        return NotImplemented

    def __hash__(self):
        return hash((self._filler, self._property))

    def get_property(self) -> OWLDataPropertyExpression:
        # documented in parent
        return self._property
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