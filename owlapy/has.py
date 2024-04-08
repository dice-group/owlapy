from typing import Protocol, ClassVar
from abc import ABCMeta, abstractmethod
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
