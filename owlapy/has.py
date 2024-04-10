from typing import Protocol, ClassVar
class HasIndex(Protocol):
    """Interface for types with an index; this is used to group objects by type when sorting."""
    type_index: ClassVar[int]  #: index for this type. This is a sorting index for the types.

    def __eq__(self, other): ...

