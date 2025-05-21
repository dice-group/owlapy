"""OWL Base Classes Expressions"""
from abc import abstractmethod, ABCMeta
from ..owl_data_ranges import OWLPropertyRange
from ..meta_classes import HasOperands

from typing import Final, Iterable


class OWLClassExpression(OWLPropertyRange):
    """OWL Class expressions represent sets of individuals by formally specifying conditions on the individuals' properties;
     individuals satisfying these conditions are said to be instances of the respective class expressions.
     In the structural specification of OWL 2, class expressions are represented by ClassExpression.
     (https://www.w3.org/TR/owl2-syntax/#Class_Expressions)
     """
    __slots__ = ()

    @abstractmethod
    def is_owl_thing(self) -> bool:
        """Determines if this expression is the built in class owl:Thing. This method does not determine if the class
        is equivalent to owl:Thing.

        Returns:
            True if this expression is owl:Thing.
        """
        pass

    @abstractmethod
    def is_owl_nothing(self) -> bool:
        """Determines if this expression is the built in class owl:Nothing. This method does not determine if the class
        is equivalent to owl:Nothing.
        """
        pass

    @abstractmethod
    def get_object_complement_of(self) -> 'OWLObjectComplementOf':
        """Gets the object complement of this class expression.

        Returns:
            A class expression that is the complement of this class expression.
        """
        pass

    @abstractmethod
    def get_nnf(self) -> 'OWLClassExpression':
        """Gets the negation normal form of the complement of this expression.

        Returns:
            A expression that represents the NNF of the complement of this expression.
        """
        pass


class OWLAnonymousClassExpression(OWLClassExpression, metaclass=ABCMeta):
    """A Class Expression which is not a named Class."""

    def is_owl_nothing(self) -> bool:
        # documented in parent
        return False

    def is_owl_thing(self) -> bool:
        # documented in parent
        return False

    def get_object_complement_of(self) -> 'OWLObjectComplementOf':
        # documented in parent
        return OWLObjectComplementOf(self)

    def get_nnf(self) -> 'OWLClassExpression':
        # documented in parent
        from owlapy.utils import NNF
        return NNF().get_class_nnf(self)


class OWLBooleanClassExpression(OWLAnonymousClassExpression, metaclass=ABCMeta):
    """Represent an anonymous boolean class expression."""
    __slots__ = ()
    pass


class OWLObjectComplementOf(OWLBooleanClassExpression, HasOperands[OWLClassExpression]):
    """Represents an ObjectComplementOf class expression in the OWL 2 Specification."""
    __slots__ = '_operand'
    type_index: Final = 3003

    _operand: OWLClassExpression

    def __new__(cls, op: OWLClassExpression = None):
        """
        Creates a new instance or returns the operand if op is already a complement.
        """
        if isinstance(op, OWLObjectComplementOf):
            return op.get_operand()
        else:
            return super(OWLObjectComplementOf, cls).__new__(cls)

    def __init__(self, op: OWLClassExpression):
        """
        Args:
            op: Class expression to complement.
        """
        self._operand = op

    def get_operand(self) -> OWLClassExpression:
        """
        Returns:
            The wrapped expression.
        """
        return self._operand

    def operands(self) -> Iterable[OWLClassExpression]:
        # documented in parent
        yield self._operand

    def __repr__(self):
        return f"OWLObjectComplementOf({repr(self._operand)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._operand == other._operand
        return NotImplemented

    def __hash__(self):
        return hash(self._operand)
