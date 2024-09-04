"""Meta classes for OWL objects."""

# https://docs.python.org/3/reference/datamodel.html#metaclasses
from typing import TypeVar, Generic, Iterable
from abc import ABCMeta, abstractmethod

_T = TypeVar('_T')  #:


class HasIRI(metaclass=ABCMeta):
    """Simple class to access the IRI."""
    __slots__ = ()

    @property
    @abstractmethod
    def iri(self):
        """Gets the IRI of this object.

        Returns:
            The IRI of this object.
        """
        pass

    @property
    @abstractmethod
    def str(self) -> str:
        """Gets the string representation of this object

        Returns:
            The IRI as string
        """
        pass


class HasOperands(Generic[_T], metaclass=ABCMeta):
    """An interface to objects that have a collection of operands.

    Args:
        _T: Operand type.
    """
    __slots__ = ()

    @abstractmethod
    def operands(self) -> Iterable[_T]:
        """Gets the operands - e.g., the individuals in a sameAs axiom, or the classes in an equivalent
        classes axiom.

        Returns:
            The operands.
        """
        pass


class HasFiller(Generic[_T], metaclass=ABCMeta):
    """An interface to objects that have a filler.

    Args:
        _T: Filler type.
    """
    __slots__ = ()

    @abstractmethod
    def get_filler(self) -> _T:
        """Gets the filler for this restriction. In the case of an object restriction this will be an individual, in
        the case of a data restriction this will be a constant (data value). For quantified restriction this will be
        a class expression or a data range.

        Returns:
            the value
        """
        pass


class HasCardinality(metaclass=ABCMeta):
    """An interface to objects that have a cardinality."""
    __slots__ = ()

    @abstractmethod
    def get_cardinality(self) -> int:
        """Gets the cardinality of a restriction.

        Returns:
            The cardinality. A non-negative integer.
        """
        pass
