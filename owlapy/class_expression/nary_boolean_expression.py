from .class_expression import OWLClassExpression, OWLBooleanClassExpression
from ..meta_classes import HasOperands
from typing import Final, Sequence, Iterable
class OWLNaryBooleanClassExpression(OWLBooleanClassExpression, HasOperands[OWLClassExpression]):
    """OWLNaryBooleanClassExpression."""
    __slots__ = ()

    _operands: Sequence[OWLClassExpression]

    def __init__(self, operands: Iterable[OWLClassExpression]):
        """
        Args:
            operands: Class expressions.
        """
        self._operands = tuple(operands)

    def operands(self) -> Iterable[OWLClassExpression]:
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




class OWLObjectUnionOf(OWLNaryBooleanClassExpression):
    """Represents an ObjectUnionOf class expression in the OWL 2 Specification."""
    __slots__ = '_operands'
    type_index: Final = 3002

    _operands: Sequence[OWLClassExpression]


class OWLObjectIntersectionOf(OWLNaryBooleanClassExpression):
    """Represents an OWLObjectIntersectionOf class expression in the OWL 2 Specification."""
    __slots__ = '_operands'
    type_index: Final = 3001

    _operands: Sequence[OWLClassExpression]
