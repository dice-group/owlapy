from typing import Protocol, ClassVar, TypeVar, Generic, Iterable
from abc import ABCMeta, abstractmethod
_T = TypeVar('_T')  #:

class HasIndex(Protocol):
    """Interface for types with an index; this is used to group objects by type when sorting."""
    type_index: ClassVar[int]  #: index for this type. This is a sorting index for the types.

    def __eq__(self, other): ...


class HasIRI(metaclass=ABCMeta):
    """Simple class to access the IRI."""
    __slots__ = ()

    @abstractmethod
    def get_iri(self) -> 'IRI':
        """Gets the IRI of this object.

        Returns:
            The IRI of this object.
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
