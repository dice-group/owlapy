from abc import abstractmethod, ABCMeta
from .owlobject import OWLObject, OWLEntity
from .has import HasOperands
from typing import Final, Iterable, Sequence
from .ranges import OWLPropertyRange, OWLDataRange


class OWLClassExpression(OWLPropertyRange):
    """An OWL 2 Class Expression."""
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
        from owlapy.util import NNF
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


class OWLClass(OWLClassExpression, OWLEntity):
    """An OWL 2 named Class"""
    __slots__ = '_iri', '_is_nothing', '_is_thing'
    type_index: Final = 1001

    _iri: 'IRI'
    _is_nothing: bool
    _is_thing: bool

    def __init__(self, iri: 'IRI'):
        """Gets an instance of OWLClass that has the specified IRI.

        Args:
            iri: The IRI.
        """
        self._is_nothing = iri.is_nothing()
        self._is_thing = iri.is_thing()
        self._iri = iri

    def get_iri(self) -> 'IRI':
        # documented in parent
        return self._iri

    def is_owl_thing(self) -> bool:
        # documented in parent
        return self._is_thing

    def is_owl_nothing(self) -> bool:
        # documented in parent
        return self._is_nothing

    def get_object_complement_of(self) -> OWLObjectComplementOf:
        # documented in parent
        return OWLObjectComplementOf(self)

    def get_nnf(self) -> 'OWLClass':
        # documented in parent
        return self

    @property
    def str(self):
        return self.get_iri().as_str()

    @property
    def reminder(self) -> str:
        """The reminder of the IRI """
        return self.get_iri().get_remainder()

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
