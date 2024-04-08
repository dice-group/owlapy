from abc import ABCMeta, abstractmethod
from .has import HasFiller
from typing import TypeVar, Generic, Final
from .owl_class_expression import OWLAnonymousClassExpression, OWLClassExpression
from .owl_property import OWLPropertyExpression, OWLObjectPropertyExpression
_T = TypeVar('_T')  #:
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
