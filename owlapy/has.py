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
