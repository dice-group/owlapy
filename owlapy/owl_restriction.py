from abc import ABCMeta, abstractmethod
from .has import HasFiller, HasCardinality
from typing import TypeVar, Generic, Final
from .owl_class_expression import OWLAnonymousClassExpression, OWLClassExpression, OWLObjectIntersectionOf
from .owl_property import OWLPropertyExpression, OWLObjectPropertyExpression, OWLDataPropertyExpression
from .ranges import OWLPropertyRange, OWLDataRange

_T = TypeVar('_T')  #:
_F = TypeVar('_F', bound=OWLPropertyRange)  #:
class OWLRestriction(OWLAnonymousClassExpression):
    """Represents an Object Property Restriction or Data Property Restriction in the OWL 2 specification."""
    __slots__ = ()

    @abstractmethod
    def get_property(self) -> OWLPropertyExpression:
        """
        Returns:
            Property being restricted.
        """
        pass

    def is_data_restriction(self) -> bool:
        """Determines if this is a data restriction.

        Returns:
            True if this is a data restriction.
        """
        return False

    def is_object_restriction(self) -> bool:
        """Determines if this is an object restriction.

        Returns:
            True if this is an object restriction.
        """
        return False
class OWLDataRestriction(OWLRestriction, metaclass=ABCMeta):
    """Represents a Data Property Restriction in the OWL 2 specification."""
    __slots__ = ()

    def is_data_restriction(self) -> bool:
        # documented in parent
        return True

    pass
class OWLObjectRestriction(OWLRestriction, metaclass=ABCMeta):
    """Represents a Object Property Restriction in the OWL 2 specification."""
    __slots__ = ()

    def is_object_restriction(self) -> bool:
        # documented in parent
        return True

    @abstractmethod
    def get_property(self) -> OWLObjectPropertyExpression:
        # documented in parent
        pass
class OWLHasValueRestriction(Generic[_T], OWLRestriction, HasFiller[_T], metaclass=ABCMeta):
    """OWLHasValueRestriction.

    Args:
        _T: The value type.
    """
    __slots__ = ()

    _v: _T

    def __init__(self, value: _T):
        self._v = value

    def __eq__(self, other):
        if type(other) is type(self):
            return self._v == other._v
        return NotImplemented

    def __hash__(self):
        return hash(self._v)

    def get_filler(self) -> _T:
        # documented in parent
        return self._v
class OWLQuantifiedRestriction(Generic[_T], OWLRestriction, HasFiller[_T], metaclass=ABCMeta):
    """Represents a quantified restriction.

    Args:
        _T: value type
    """
    __slots__ = ()
    pass
class OWLQuantifiedObjectRestriction(OWLQuantifiedRestriction[OWLClassExpression], OWLObjectRestriction,
                                     metaclass=ABCMeta):
    """Represents a quantified object restriction."""
    __slots__ = ()

    _filler: OWLClassExpression

    def __init__(self, filler: OWLClassExpression):
        self._filler = filler

    def get_filler(self) -> OWLClassExpression:
        # documented in parent (HasFiller)
        return self._filler
class OWLObjectSomeValuesFrom(OWLQuantifiedObjectRestriction):
    """Represents an ObjectSomeValuesFrom class expression in the OWL 2 Specification."""
    __slots__ = '_property', '_filler'
    type_index: Final = 3005

    def __init__(self, property: OWLObjectPropertyExpression, filler: OWLClassExpression):
        """Gets an OWLObjectSomeValuesFrom restriction.

        Args:
            property: The object property that the restriction acts along.
            filler: The class expression that is the filler.

        Returns:
            An OWLObjectSomeValuesFrom restriction along the specified property with the specified filler.
        """
        super().__init__(filler)
        self._property = property

    def __repr__(self):
        return f"OWLObjectSomeValuesFrom(property={repr(self._property)},filler={repr(self._filler)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._filler == other._filler and self._property == other._property
        return NotImplemented

    def __hash__(self):
        return hash((self._filler, self._property))

    def get_property(self) -> OWLObjectPropertyExpression:
        # documented in parent
        return self._property
class OWLObjectAllValuesFrom(OWLQuantifiedObjectRestriction):
    """Represents an ObjectAllValuesFrom class expression in the OWL 2 Specification."""
    __slots__ = '_property', '_filler'
    type_index: Final = 3006

    def __init__(self, property: OWLObjectPropertyExpression, filler: OWLClassExpression):
        super().__init__(filler)
        self._property = property

    def __repr__(self):
        return f"OWLObjectAllValuesFrom(property={repr(self._property)},filler={repr(self._filler)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._filler == other._filler and self._property == other._property
        return NotImplemented

    def __hash__(self):
        return hash((self._filler, self._property))

    def get_property(self) -> OWLObjectPropertyExpression:
        # documented in parent
        return self._property

class OWLCardinalityRestriction(Generic[_F], OWLQuantifiedRestriction[_F], HasCardinality, metaclass=ABCMeta):
    """Base interface for owl min and max cardinality restriction.

    Args:
        _F: Type of filler.
    """
    __slots__ = ()

    _cardinality: int
    _filler: _F

    def __init__(self, cardinality: int, filler: _F):
        self._cardinality = cardinality
        self._filler = filler

    def get_cardinality(self) -> int:
        # documented in parent
        return self._cardinality

    def get_filler(self) -> _F:
        # documented in parent
        return self._filler


class OWLObjectCardinalityRestriction(OWLCardinalityRestriction[OWLClassExpression], OWLQuantifiedObjectRestriction):
    """Represents Object Property Cardinality Restrictions in the OWL 2 specification."""
    __slots__ = ()

    _property: OWLObjectPropertyExpression

    @abstractmethod
    def __init__(self, cardinality: int, property: OWLObjectPropertyExpression, filler: OWLClassExpression):
        super().__init__(cardinality, filler)
        self._property = property

    def get_property(self) -> OWLObjectPropertyExpression:
        # documented in parent
        return self._property

    def __repr__(self):
        return f"{type(self).__name__}(" \
               f"property={repr(self.get_property())},{self.get_cardinality()},filler={repr(self.get_filler())})"

    def __eq__(self, other):
        if type(other) == type(self):
            return self._property == other._property \
                and self._cardinality == other._cardinality \
                and self._filler == other._filler
        return NotImplemented

    def __hash__(self):
        return hash((self._property, self._cardinality, self._filler))

class OWLObjectMinCardinality(OWLObjectCardinalityRestriction):
    """Represents a ObjectMinCardinality restriction in the OWL 2 Specification."""
    __slots__ = '_cardinality', '_filler', '_property'
    type_index: Final = 3008

    def __init__(self, cardinality: int, property: OWLObjectPropertyExpression, filler: OWLClassExpression):
        """
        Args:
            cardinality: Cannot be negative.
            property: The property that the restriction acts along.
            filler: Class expression for restriction.

        Returns:
            An ObjectMinCardinality on the specified property.
        """
        super().__init__(cardinality, property, filler)
class OWLObjectMaxCardinality(OWLObjectCardinalityRestriction):
    """Represents a ObjectMaxCardinality restriction in the OWL 2 Specification."""
    __slots__ = '_cardinality', '_filler', '_property'
    type_index: Final = 3010

    def __init__(self, cardinality: int, property: OWLObjectPropertyExpression, filler: OWLClassExpression):
        """
        Args:
            cardinality: Cannot be negative.
            property: The property that the restriction acts along.
            filler: Class expression for restriction.

        Returns:
            An ObjectMaxCardinality on the specified property.
        """
        super().__init__(cardinality, property, filler)
class OWLObjectExactCardinality(OWLObjectCardinalityRestriction):
    """Represents an ObjectExactCardinality  restriction in the OWL 2 Specification."""
    __slots__ = '_cardinality', '_filler', '_property'
    type_index: Final = 3009

    def __init__(self, cardinality: int, property: OWLObjectPropertyExpression, filler: OWLClassExpression):
        """
        Args:
            cardinality: Cannot be negative.
            property: The property that the restriction acts along.
            filler: Class expression for restriction.

        Returns:
            An ObjectExactCardinality on the specified property.
        """
        super().__init__(cardinality, property, filler)

    def as_intersection_of_min_max(self) -> OWLObjectIntersectionOf:
        """Obtains an equivalent form that is a conjunction of a min cardinality and max cardinality restriction.

        Returns:
            The semantically equivalent but structurally simpler form (= 1 R C) = >= 1 R C and <= 1 R C.
        """
        args = self.get_cardinality(), self.get_property(), self.get_filler()
        return OWLObjectIntersectionOf((OWLObjectMinCardinality(*args), OWLObjectMaxCardinality(*args)))
class OWLObjectHasSelf(OWLObjectRestriction):
    """Represents an ObjectHasSelf class expression in the OWL 2 Specification."""
    __slots__ = '_property'
    type_index: Final = 3011

    _property: OWLObjectPropertyExpression

    def __init__(self, property: OWLObjectPropertyExpression):
        """Object has self restriction

        Args:
            property: The property that the restriction acts along.

        Returns:
            A ObjectHasSelf class expression on the specified property.
        """
        self._property = property

    def get_property(self) -> OWLObjectPropertyExpression:
        # documented in parent
        return self._property

    def __eq__(self, other):
        if type(other) == type(self):
            return self._property == other._property
        return NotImplemented

    def __hash__(self):
        return hash(self._property)

    def __repr__(self):
        return f'OWLObjectHasSelf({self._property})'


class OWLQuantifiedDataRestriction(OWLQuantifiedRestriction[OWLDataRange],
                                   OWLDataRestriction, metaclass=ABCMeta):
    """Represents a quantified data restriction."""
    __slots__ = ()

    _filler: OWLDataRange

    def __init__(self, filler: OWLDataRange):
        self._filler = filler

    def get_filler(self) -> OWLDataRange:
        # documented in parent (HasFiller)
        return self._filler
class OWLDataAllValuesFrom(OWLQuantifiedDataRestriction):
    """Represents DataAllValuesFrom class expressions in the OWL 2 Specification."""
    __slots__ = '_property'

    type_index: Final = 3013

    _property: OWLDataPropertyExpression

    def __init__(self, property: OWLDataPropertyExpression, filler: OWLDataRange):
        """Gets an OWLDataAllValuesFrom restriction.

        Args:
            property: The data property that the restriction acts along.
            filler: The data range that is the filler.

        Returns:
            An OWLDataAllValuesFrom restriction along the specified property with the specified filler.
        """
        super().__init__(filler)
        self._property = property

    def __repr__(self):
        return f"OWLDataAllValuesFrom(property={repr(self._property)},filler={repr(self._filler)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._filler == other._filler and self._property == other._property
        return NotImplemented

    def __hash__(self):
        return hash((self._filler, self._property))

    def get_property(self) -> OWLDataPropertyExpression:
        # documented in parent
        return self._property
class OWLDataCardinalityRestriction(OWLCardinalityRestriction[OWLDataRange],
                                    OWLQuantifiedDataRestriction,
                                    OWLDataRestriction, metaclass=ABCMeta):
    """Represents Data Property Cardinality Restrictions in the OWL 2 specification."""
    __slots__ = ()

    _property: OWLDataPropertyExpression

    @abstractmethod
    def __init__(self, cardinality: int, property: OWLDataPropertyExpression, filler: OWLDataRange):
        super().__init__(cardinality, filler)
        self._property = property

    def get_property(self) -> OWLDataPropertyExpression:
        # documented in parent
        return self._property

    def __repr__(self):
        return f"{type(self).__name__}(" \
               f"property={repr(self.get_property())},{self.get_cardinality()},filler={repr(self.get_filler())})"

    def __eq__(self, other):
        if type(other) == type(self):
            return self._property == other._property \
                and self._cardinality == other._cardinality \
                and self._filler == other._filler
        return NotImplemented

    def __hash__(self):
        return hash((self._property, self._cardinality, self._filler))

class OWLDataExactCardinality(OWLDataCardinalityRestriction):
    """Represents DataExactCardinality restrictions in the OWL 2 Specification."""
    __slots__ = '_cardinality', '_filler', '_property'

    type_index: Final = 3016

    def __init__(self, cardinality: int, property: OWLDataPropertyExpression, filler: OWLDataRange):
        """
        Args:
            cardinality: Cannot be negative.
            property: The property that the restriction acts along.
            filler: Data range for restriction

        Returns:
            A DataExactCardinality on the specified property.
        """
        super().__init__(cardinality, property, filler)

    def as_intersection_of_min_max(self) -> OWLObjectIntersectionOf:
        """Obtains an equivalent form that is a conjunction of a min cardinality and max cardinality restriction.

        Returns:
            The semantically equivalent but structurally simpler form (= 1 R D) = >= 1 R D and <= 1 R D.
        """
        args = self.get_cardinality(), self.get_property(), self.get_filler()
        return OWLObjectIntersectionOf((OWLDataMinCardinality(*args), OWLDataMaxCardinality(*args)))
