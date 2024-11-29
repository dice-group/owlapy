"""OWL nary boolean expressions"""
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
        # TODO: CD: Replace tuple with set
        self._operands = tuple(operands)

        assert len(self._operands)>1, "OWLNaryBooleanClassExpression requires at least one operand."

    def operands(self) -> Iterable[OWLClassExpression]:
        # documented in parent
        yield from self._operands

    def __repr__(self):
        return f'{type(self).__name__}({repr(self._operands)})'

    def __eq__(self, other):
        if type(other) is type(self):
            return (set(self._operands) == set(other.operands())
                    and len(list(self._operands)) == len(list(other.operands())))
        return False

    def __hash__(self):
        return hash(self._operands)


class OWLObjectUnionOf(OWLNaryBooleanClassExpression):
    """A union class expression ObjectUnionOf( CE1 ... CEn ) contains all individuals that are instances
       of at least one class expression CEi for 1 ≤ i ≤ n.
       (https://www.w3.org/TR/owl2-syntax/#Union_of_Class_Expressions)
    """
    __slots__ = '_operands'
    type_index: Final = 3002

    _operands: Sequence[OWLClassExpression]


class OWLObjectIntersectionOf(OWLNaryBooleanClassExpression):
    """An intersection class expression ObjectIntersectionOf( CE1 ... CEn ) contains all individuals that are instances
    of all class expressions CEi for 1 ≤ i ≤ n.
    (https://www.w3.org/TR/owl2-syntax/#Intersection_of_Class_Expressions)
    """
    __slots__ = '_operands'
    type_index: Final = 3001

    _operands: Sequence[OWLClassExpression]
