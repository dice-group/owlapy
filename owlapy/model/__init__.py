"""@TODO: CD: This is not a python code. We should refactor this model module."""

from abc import ABCMeta, abstractmethod
from functools import total_ordering
from itertools import combinations
from typing import Generic, Iterable, Sequence, Set, TypeVar, Union, Final, Optional, Protocol, ClassVar, List
from pandas import Timedelta
from datetime import datetime, date

from owlapy.vocab import OWLRDFVocabulary, XSDVocabulary, OWLFacet
from owlapy._utils import MOVE
from owlapy.model._base import OWLObject, OWLAnnotationObject, OWLAnnotationSubject, OWLAnnotationValue
from owlapy.model._iri import HasIRI, IRI

MOVE(OWLObject, OWLAnnotationObject, OWLAnnotationSubject, OWLAnnotationValue, HasIRI, IRI)

_T = TypeVar('_T')  #:
_C = TypeVar('_C', bound='OWLObject')  #:
_P = TypeVar('_P', bound='OWLPropertyExpression')  #:
_R = TypeVar('_R', bound='OWLPropertyRange')  #:
Literals = Union['OWLLiteral', int, float, bool, Timedelta, datetime, date, str]  #:


class HasIndex(Protocol):
    """Interface for types with an index; this is used to group objects by type when sorting."""
    type_index: ClassVar[int]  #: index for this type. This is a sorting index for the types.

    def __eq__(self, other): ...


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


class OWLPropertyRange(OWLObject, metaclass=ABCMeta):
    """OWL Objects that can be the ranges of properties."""


class OWLDataRange(OWLPropertyRange, metaclass=ABCMeta):
    """Represents a DataRange in the OWL 2 Specification."""


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


class OWLNamedObject(OWLObject, HasIRI, metaclass=ABCMeta):
    """Represents a named object for example, class, property, ontology etc. - i.e. anything that has an
     IRI as its name."""
    __slots__ = ()

    _iri: IRI

    def __eq__(self, other):
        if type(other) is type(self):
            return self._iri == other._iri
        return NotImplemented

    def __lt__(self, other):
        if type(other) is type(self):
            return self._iri.as_str() < other._iri.as_str()
        return NotImplemented

    def __hash__(self):
        return hash(self._iri)

    def __repr__(self):
        return f"{type(self).__name__}({repr(self._iri)})"

    pass


class OWLEntity(OWLNamedObject, metaclass=ABCMeta):
    """Represents Entities in the OWL 2 Specification."""
    __slots__ = ()

    def to_string_id(self) -> str:
        return self.get_iri().as_str()

    def is_anonymous(self) -> bool:
        return False

    pass


class OWLClass(OWLClassExpression, OWLEntity):
    """An OWL 2 named Class"""
    __slots__ = '_iri', '_is_nothing', '_is_thing'
    type_index: Final = 1001

    _iri: IRI
    _is_nothing: bool
    _is_thing: bool

    def __init__(self, iri: IRI):
        """Gets an instance of OWLClass that has the specified IRI.

        Args:
            iri: The IRI.
        """
        self._is_nothing = iri.is_nothing()
        self._is_thing = iri.is_thing()
        self._iri = iri

    def get_iri(self) -> IRI:
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
    def reminder(self)->str:
        """The reminder of the IRI """
        return self.get_iri().get_remainder()

class OWLPropertyExpression(OWLObject, metaclass=ABCMeta):
    """Represents a property or possibly the inverse of a property."""
    __slots__ = ()

    def is_data_property_expression(self) -> bool:
        """
        Returns:
            True if this is a data property.
        """
        return False

    def is_object_property_expression(self) -> bool:
        """
        Returns:
            True if this is an object property.
        """
        return False

    def is_owl_top_object_property(self) -> bool:
        """Determines if this is the owl:topObjectProperty.

        Returns:
            True if this property is the owl:topObjectProperty.
        """
        return False

    def is_owl_top_data_property(self) -> bool:
        """Determines if this is the owl:topDataProperty.

        Returns:
            True if this property is the owl:topDataProperty.
        """
        return False


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


class OWLObjectPropertyExpression(OWLPropertyExpression):
    """A high level interface to describe different types of object properties."""
    __slots__ = ()

    @abstractmethod
    def get_inverse_property(self) -> 'OWLObjectPropertyExpression':
        """Obtains the property that corresponds to the inverse of this property.

        Returns:
            The inverse of this property. Note that this property will not necessarily be in the simplest form.
        """
        pass

    @abstractmethod
    def get_named_property(self) -> 'OWLObjectProperty':
        """Get the named object property used in this property expression.

        Returns:
            P if this expression is either inv(P) or P.
        """
        pass

    def is_object_property_expression(self) -> bool:
        # documented in parent
        return True


class OWLDataPropertyExpression(OWLPropertyExpression, metaclass=ABCMeta):
    """A high level interface to describe different types of data properties."""
    __slots__ = ()

    def is_data_property_expression(self):
        # documented in parent
        return True


class OWLProperty(OWLPropertyExpression, OWLEntity, metaclass=ABCMeta):
    """A marker interface for properties that aren't expression i.e. named properties. By definition, properties
    are either data properties or object properties."""
    __slots__ = ()
    pass


class OWLDataProperty(OWLDataPropertyExpression, OWLProperty):
    """Represents a Data Property in the OWL 2 Specification."""
    __slots__ = '_iri'
    type_index: Final = 1004

    _iri: IRI

    def __init__(self, iri: IRI):
        """Gets an instance of OWLDataProperty that has the specified IRI.

        Args:
            iri: The IRI.
        """
        self._iri = iri

    def get_iri(self) -> IRI:
        # documented in parent
        return self._iri

    def is_owl_top_data_property(self) -> bool:
        # documented in parent
        return self.get_iri() == OWLRDFVocabulary.OWL_TOP_DATA_PROPERTY.get_iri()


class OWLObjectProperty(OWLObjectPropertyExpression, OWLProperty):
    """Represents an Object Property in the OWL 2 Specification."""
    __slots__ = '_iri'
    type_index: Final = 1002

    _iri: IRI

    def get_named_property(self) -> 'OWLObjectProperty':
        # documented in parent
        return self

    def __init__(self, iri: IRI):
        """Gets an instance of OWLObjectProperty that has the specified IRI.

        Args:
            iri: The IRI.
        """
        self._iri = iri

    def get_inverse_property(self) -> 'OWLObjectInverseOf':
        # documented in parent
        return OWLObjectInverseOf(self)

    def get_iri(self) -> IRI:
        # documented in parent
        return self._iri

    def is_owl_top_object_property(self) -> bool:
        # documented in parent
        return self.get_iri() == OWLRDFVocabulary.OWL_TOP_OBJECT_PROPERTY.get_iri()

    @property
    def str(self)->str:
        return self.get_iri().as_str()


class OWLObjectInverseOf(OWLObjectPropertyExpression):
    """Represents the inverse of a property expression (ObjectInverseOf). This can be used to refer to the inverse of
    a property, without actually naming the property. For example, consider the property hasPart, the inverse property
    of hasPart (isPartOf) can be referred to using this interface inverseOf(hasPart), which can be used in
    restrictions e.g. inverseOf(hasPart) some Car refers to the set of things that are part of at least one car."""
    __slots__ = '_inverse_property'
    type_index: Final = 1003

    _inverse_property: OWLObjectProperty

    def __init__(self, property: OWLObjectProperty):
        """Gets the inverse of an object property.

        Args:
            property: The property of which the inverse will be returned.
        """
        self._inverse_property = property

    def get_inverse(self) -> OWLObjectProperty:
        """Gets the property expression that this is the inverse of.

        Returns:
            The object property expression such that this object property expression is an inverse of it.
        """
        return self._inverse_property

    def get_inverse_property(self) -> OWLObjectProperty:
        # documented in parent
        return self.get_inverse()

    def get_named_property(self) -> OWLObjectProperty:
        # documented in parent
        return self._inverse_property

    def __repr__(self):
        return f"OWLObjectInverseOf({repr(self._inverse_property)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._inverse_property == other._inverse_property
        return NotImplemented

    def __hash__(self):
        return hash(self._inverse_property)


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


_F = TypeVar('_F', bound=OWLPropertyRange)  #:


class OWLCardinalityRestriction(Generic[_F], OWLQuantifiedRestriction[_F], HasCardinality, metaclass=ABCMeta):
    """Base interface for owl min and max cardinality restriction.

    Args:
        _F: Type of filler.
    """
    __slots__ = ()

    _cardinality: int
    _filler: _F

    def __init__(self, cardinality: int, filler: _F):
        self._cardinality = cardinality
        self._filler = filler

    def get_cardinality(self) -> int:
        # documented in parent
        return self._cardinality

    def get_filler(self) -> _F:
        # documented in parent
        return self._filler


class OWLObjectCardinalityRestriction(OWLCardinalityRestriction[OWLClassExpression], OWLQuantifiedObjectRestriction):
    """Represents Object Property Cardinality Restrictions in the OWL 2 specification."""
    __slots__ = ()

    _property: OWLObjectPropertyExpression

    @abstractmethod
    def __init__(self, cardinality: int, property: OWLObjectPropertyExpression, filler: OWLClassExpression):
        super().__init__(cardinality, filler)
        self._property = property

    def get_property(self) -> OWLObjectPropertyExpression:
        # documented in parent
        return self._property

    def __repr__(self):
        return f"{type(self).__name__}(" \
               f"property={repr(self.get_property())},{self.get_cardinality()},filler={repr(self.get_filler())})"

    def __eq__(self, other):
        if type(other) == type(self):
            return self._property == other._property \
                   and self._cardinality == other._cardinality \
                   and self._filler == other._filler
        return NotImplemented

    def __hash__(self):
        return hash((self._property, self._cardinality, self._filler))


class OWLObjectMinCardinality(OWLObjectCardinalityRestriction):
    """Represents a ObjectMinCardinality restriction in the OWL 2 Specification."""
    __slots__ = '_cardinality', '_filler', '_property'
    type_index: Final = 3008

    def __init__(self, cardinality: int, property: OWLObjectPropertyExpression, filler: OWLClassExpression):
        """
        Args:
            cardinality: Cannot be negative.
            property: The property that the restriction acts along.
            filler: Class expression for restriction.

        Returns:
            An ObjectMinCardinality on the specified property.
        """
        super().__init__(cardinality, property, filler)


class OWLObjectMaxCardinality(OWLObjectCardinalityRestriction):
    """Represents a ObjectMaxCardinality restriction in the OWL 2 Specification."""
    __slots__ = '_cardinality', '_filler', '_property'
    type_index: Final = 3010

    def __init__(self, cardinality: int, property: OWLObjectPropertyExpression, filler: OWLClassExpression):
        """
        Args:
            cardinality: Cannot be negative.
            property: The property that the restriction acts along.
            filler: Class expression for restriction.

        Returns:
            An ObjectMaxCardinality on the specified property.
        """
        super().__init__(cardinality, property, filler)


class OWLObjectExactCardinality(OWLObjectCardinalityRestriction):
    """Represents an ObjectExactCardinality  restriction in the OWL 2 Specification."""
    __slots__ = '_cardinality', '_filler', '_property'
    type_index: Final = 3009

    def __init__(self, cardinality: int, property: OWLObjectPropertyExpression, filler: OWLClassExpression):
        """
        Args:
            cardinality: Cannot be negative.
            property: The property that the restriction acts along.
            filler: Class expression for restriction.

        Returns:
            An ObjectExactCardinality on the specified property.
        """
        super().__init__(cardinality, property, filler)

    def as_intersection_of_min_max(self) -> OWLObjectIntersectionOf:
        """Obtains an equivalent form that is a conjunction of a min cardinality and max cardinality restriction.

        Returns:
            The semantically equivalent but structurally simpler form (= 1 R C) = >= 1 R C and <= 1 R C.
        """
        args = self.get_cardinality(), self.get_property(), self.get_filler()
        return OWLObjectIntersectionOf((OWLObjectMinCardinality(*args), OWLObjectMaxCardinality(*args)))


class OWLObjectHasSelf(OWLObjectRestriction):
    """Represents an ObjectHasSelf class expression in the OWL 2 Specification."""
    __slots__ = '_property'
    type_index: Final = 3011

    _property: OWLObjectPropertyExpression

    def __init__(self, property: OWLObjectPropertyExpression):
        """Object has self restriction

        Args:
            property: The property that the restriction acts along.

        Returns:
            A ObjectHasSelf class expression on the specified property.
        """
        self._property = property

    def get_property(self) -> OWLObjectPropertyExpression:
        # documented in parent
        return self._property

    def __eq__(self, other):
        if type(other) == type(self):
            return self._property == other._property
        return NotImplemented

    def __hash__(self):
        return hash(self._property)

    def __repr__(self):
        return f'OWLObjectHasSelf({self._property})'


class OWLIndividual(OWLObject, metaclass=ABCMeta):
    """Represents a named or anonymous individual."""
    __slots__ = ()
    pass


class OWLObjectHasValue(OWLHasValueRestriction[OWLIndividual], OWLObjectRestriction):
    """Represents an ObjectHasValue class expression in the OWL 2 Specification."""
    __slots__ = '_property', '_v'
    type_index: Final = 3007

    _property: OWLObjectPropertyExpression
    _v: OWLIndividual

    def __init__(self, property: OWLObjectPropertyExpression, individual: OWLIndividual):
        """
        Args:
            property: The property that the restriction acts along.
            individual: Individual for restriction.

        Returns:
            A HasValue restriction with specified property and value
        """
        super().__init__(individual)
        self._property = property

    def get_property(self) -> OWLObjectPropertyExpression:
        # documented in parent
        return self._property

    def as_some_values_from(self) -> OWLClassExpression:
        """A convenience method that obtains this restriction as an existential restriction with a nominal filler.

        Returns:
            The existential equivalent of this value restriction. simp(HasValue(p a)) = some(p {a}).
        """
        return OWLObjectSomeValuesFrom(self.get_property(), OWLObjectOneOf(self.get_filler()))

    def __repr__(self):
        return f'OWLObjectHasValue(property={self.get_property()}, individual={self._v})'


class OWLObjectOneOf(OWLAnonymousClassExpression, HasOperands[OWLIndividual]):
    """Represents an ObjectOneOf class expression in the OWL 2 Specification."""
    __slots__ = '_values'
    type_index: Final = 3004

    def __init__(self, values: Union[OWLIndividual, Iterable[OWLIndividual]]):
        if isinstance(values, OWLIndividual):
            self._values = values,
        else:
            for _ in values:
                assert isinstance(_, OWLIndividual)
            self._values = tuple(values)

    def individuals(self) -> Iterable[OWLIndividual]:
        """Gets the individuals that are in the oneOf. These individuals represent the exact instances (extension)
         of this class expression.

         Returns:
             The individuals that are the values of this {@code ObjectOneOf} class expression.
        """
        yield from self._values

    def operands(self) -> Iterable[OWLIndividual]:
        # documented in parent
        yield from self.individuals()

    def as_object_union_of(self) -> OWLClassExpression:
        """Simplifies this enumeration to a union of singleton nominals.

        Returns:
            This enumeration in a more standard DL form.
            simp({a}) = {a} simp({a0, ... , {an}) = unionOf({a0}, ... , {an})
        """
        if len(self._values) == 1:
            return self
        return OWLObjectUnionOf(map(lambda _: OWLObjectOneOf(_), self.individuals()))

    def __hash__(self):
        return hash(self._values)

    def __eq__(self, other):
        if type(other) == type(self):
            return self._values == other._values
        return NotImplemented

    def __repr__(self):
        return f'OWLObjectOneOf({self._values})'


class OWLNamedIndividual(OWLIndividual, OWLEntity):
    """Represents a Named Individual in the OWL 2 Specification."""
    __slots__ = '_iri'
    type_index: Final = 1005

    _iri: IRI

    def __init__(self, iri: IRI):
        """Gets an instance of OWLNamedIndividual that has the specified IRI.

        Args:
            iri: The IRI.

        Returns:
            An OWLNamedIndividual that has the specified IRI.
        """
        self._iri = iri

    def get_iri(self) -> IRI:
        # documented in parent
        return self._iri

    @property
    def iri(self):
        return self._iri

    @property
    def str(self):
        return self._iri.as_str()


_M = TypeVar('_M', bound='OWLOntologyManager')  #:


class OWLOntologyID:
    """An object that identifies an ontology. Since OWL 2, ontologies do not have to have an ontology IRI, or if they
    have an ontology IRI then they can optionally also have a version IRI. Instances of this OWLOntologyID class bundle
    identifying information of an ontology together. If an ontology doesn't have an ontology IRI then we say that it is
    "anonymous".
    """
    __slots__ = '_ontology_iri', '_version_iri'

    _ontology_iri: Optional[IRI]
    _version_iri: Optional[IRI]

    def __init__(self, ontology_iri: Optional[IRI] = None, version_iri: Optional[IRI] = None):
        """Constructs an ontology identifier specifying the ontology IRI and version IRI.

        Args:
            ontology_iri: The ontology IRI (optional).
            version_iri: The version IRI (must be None if no ontology_iri is provided).
        """
        self._ontology_iri = ontology_iri
        self._version_iri = version_iri

    def get_ontology_iri(self) -> Optional[IRI]:
        """Gets the ontology IRI.

        Returns:
            Ontology IRI. If the ontology is anonymous, it will return None.
        """
        return self._ontology_iri

    def get_version_iri(self) -> Optional[IRI]:
        """Gets the version IRI.

        Returns:
            Version IRI or None.
        """
        return self._version_iri

    def get_default_document_iri(self) -> Optional[IRI]:
        """Gets the IRI which is used as a default for the document that contain a representation of an ontology with
        this ID. This will be the version IRI if there is an ontology IRI and version IRI, else it will be the ontology
        IRI if there is an ontology IRI but no version IRI, else it will be None if there is no ontology IRI. See
        Ontology Documents in the OWL 2 Structural Specification.

        Returns:
            the IRI that can be used as a default for an ontology document, or None.
        """
        if self._ontology_iri is not None:
            if self._version_iri is not None:
                return self._version_iri
        return self._ontology_iri

    def is_anonymous(self) -> bool:
        return self._ontology_iri is None

    def __repr__(self):
        return f"OWLOntologyID({repr(self._ontology_iri)}, {repr(self._version_iri)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._ontology_iri == other._ontology_iri and self._version_iri == other._version_iri
        return NotImplemented


class OWLAxiom(OWLObject, metaclass=ABCMeta):
    """Represents Axioms in the OWL 2 Specification.

    An OWL ontology contains a set of axioms. These axioms can be annotation axioms, declaration axioms, imports axioms
    or logical axioms.
    """
    __slots__ = '_annotations'

    _annotations: List['OWLAnnotation']

    def __init__(self, annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._annotations = list(annotations) if annotations is not None else list()

    def annotations(self) -> Optional[List['OWLAnnotation']]:
        return self._annotations

    def is_annotated(self) -> bool:
        return self._annotations is not None and len(self._annotations) > 0

    def is_logical_axiom(self) -> bool:
        return False

    def is_annotation_axiom(self) -> bool:
        return False
    # TODO: XXX


class OWLDatatype(OWLEntity, OWLDataRange):
    """Represents a Datatype (named data range) in the OWL 2 Specification."""
    __slots__ = '_iri'

    type_index: Final = 4001

    _iri: IRI

    def __init__(self, iri: Union[IRI, HasIRI]):
        """Gets an instance of OWLDatatype that has the specified IRI.

        Args:
            iri: The IRI.
        """
        if isinstance(iri, HasIRI):
            self._iri = iri.get_iri()
        else:
            assert isinstance(iri, IRI)
            self._iri = iri

    def get_iri(self) -> 'IRI':
        # documented in parent
        return self._iri


class OWLDatatypeRestriction(OWLDataRange):
    """Represents a DatatypeRestriction data range in the OWL 2 Specification."""
    __slots__ = '_type', '_facet_restrictions'

    type_index: Final = 4006

    _type: OWLDatatype
    _facet_restrictions: Sequence['OWLFacetRestriction']

    def __init__(self, type_: OWLDatatype, facet_restrictions: Union['OWLFacetRestriction',
                                                                     Iterable['OWLFacetRestriction']]):
        self._type = type_
        if isinstance(facet_restrictions, OWLFacetRestriction):
            facet_restrictions = facet_restrictions,
        self._facet_restrictions = tuple(facet_restrictions)

    def get_datatype(self) -> OWLDatatype:
        return self._type

    def get_facet_restrictions(self) -> Sequence['OWLFacetRestriction']:
        return self._facet_restrictions

    def __eq__(self, other):
        if type(other) is type(self):
            return self._type == other._type \
                   and self._facet_restrictions == other._facet_restrictions
        return NotImplemented

    def __hash__(self):
        return hash((self._type, self._facet_restrictions))

    def __repr__(self):
        return f'OWLDatatypeRestriction({repr(self._type)}, {repr(self._facet_restrictions)})'


class OWLFacetRestriction(OWLObject):
    """A facet restriction is used to restrict a particular datatype."""

    __slots__ = '_facet', '_literal'

    type_index: Final = 4007

    _facet: OWLFacet
    _literal: 'OWLLiteral'

    def __init__(self, facet: OWLFacet, literal: Literals):
        self._facet = facet
        if isinstance(literal, OWLLiteral):
            self._literal = literal
        else:
            self._literal = OWLLiteral(literal)

    def get_facet(self) -> OWLFacet:
        return self._facet

    def get_facet_value(self) -> 'OWLLiteral':
        return self._literal

    def __eq__(self, other):
        if type(other) is type(self):
            return self._facet == other._facet and self._literal == other._literal
        return NotImplemented

    def __hash__(self):
        return hash((self._facet, self._literal))

    def __repr__(self):
        return f'OWLFacetRestriction({self._facet}, {repr(self._literal)})'


class OWLLiteral(OWLAnnotationValue, metaclass=ABCMeta):
    """Represents a Literal in the OWL 2 Specification."""
    __slots__ = ()

    type_index: Final = 4008

    def __new__(cls, value, type_: Optional[OWLDatatype] = None):
        """Convenience method that obtains a literal.

        Args:
            value: The value of the literal.
            type_: The datatype of the literal.
        """
        if type_ is not None:
            if type_ == BooleanOWLDatatype:
                return super().__new__(_OWLLiteralImplBoolean)
            elif type_ == IntegerOWLDatatype:
                return super().__new__(_OWLLiteralImplInteger)
            elif type_ == DoubleOWLDatatype:
                return super().__new__(_OWLLiteralImplDouble)
            elif type_ == StringOWLDatatype:
                return super().__new__(_OWLLiteralImplString)
            elif type_ == DateOWLDatatype:
                return super().__new__(_OWLLiteralImplDate)
            elif type_ == DateTimeOWLDatatype:
                return super().__new__(_OWLLiteralImplDateTime)
            elif type_ == DurationOWLDatatype:
                return super().__new__(_OWLLiteralImplDuration)
            else:
                return super().__new__(_OWLLiteralImpl)
        if isinstance(value, bool):
            return super().__new__(_OWLLiteralImplBoolean)
        elif isinstance(value, int):
            return super().__new__(_OWLLiteralImplInteger)
        elif isinstance(value, float):
            return super().__new__(_OWLLiteralImplDouble)
        elif isinstance(value, str):
            return super().__new__(_OWLLiteralImplString)
        elif isinstance(value, datetime):
            return super().__new__(_OWLLiteralImplDateTime)
        elif isinstance(value, date):
            return super().__new__(_OWLLiteralImplDate)
        elif isinstance(value, Timedelta):
            return super().__new__(_OWLLiteralImplDuration)
        # TODO XXX
        raise NotImplementedError(value)

    def get_literal(self) -> str:
        """Gets the lexical value of this literal. Note that the language tag is not included.

        Returns:
            The lexical value of this literal.
        """
        return str(self._v)

    def is_boolean(self) -> bool:
        """Whether this literal is typed as boolean."""
        return False

    def parse_boolean(self) -> bool:
        """Parses the lexical value of this literal into a bool. The lexical value of this literal should be in the
        lexical space of the boolean datatype ("http://www.w3.org/2001/XMLSchema#boolean").

        Returns:
            A bool value that is represented by this literal.
        """
        raise ValueError

    def is_double(self) -> bool:
        """Whether this literal is typed as double."""
        return False

    def parse_double(self) -> float:
        """Parses the lexical value of this literal into a double. The lexical value of this literal should be in the
        lexical space of the double datatype ("http://www.w3.org/2001/XMLSchema#double").

        Returns:
            A double value that is represented by this literal.
        """
        raise ValueError

    def is_integer(self) -> bool:
        """Whether this literal is typed as integer."""
        return False

    def parse_integer(self) -> int:
        """Parses the lexical value of this literal into an integer. The lexical value of this literal should be in the
        lexical space of the integer datatype ("http://www.w3.org/2001/XMLSchema#integer").

        Returns:
            An integer value that is represented by this literal.
        """
        raise ValueError

    def is_string(self) -> bool:
        """Whether this literal is typed as string."""
        return False

    def parse_string(self) -> str:
        """Parses the lexical value of this literal into a string. The lexical value of this literal should be in the
        lexical space of the string datatype ("http://www.w3.org/2001/XMLSchema#string").

        Returns:
            A string value that is represented by this literal.
        """
        raise ValueError

    def is_date(self) -> bool:
        """Whether this literal is typed as date."""
        return False

    def parse_date(self) -> date:
        """Parses the lexical value of this literal into a date. The lexical value of this literal should be in the
        lexical space of the date datatype ("http://www.w3.org/2001/XMLSchema#date").

        Returns:
            A date value that is represented by this literal.
        """
        raise ValueError

    def is_datetime(self) -> bool:
        """Whether this literal is typed as dateTime."""
        return False

    def parse_datetime(self) -> datetime:
        """Parses the lexical value of this literal into a datetime. The lexical value of this literal should be in the
        lexical space of the dateTime datatype ("http://www.w3.org/2001/XMLSchema#dateTime").

        Returns:
            A datetime value that is represented by this literal.
        """
        raise ValueError

    def is_duration(self) -> bool:
        """Whether this literal is typed as duration."""
        return False

    def parse_duration(self) -> Timedelta:
        """Parses the lexical value of this literal into a Timedelta. The lexical value of this literal should be in the
        lexical space of the duration datatype ("http://www.w3.org/2001/XMLSchema#duration").

        Returns:
            A Timedelta value that is represented by this literal.
        """
        raise ValueError

    # noinspection PyMethodMayBeStatic
    def is_literal(self) -> bool:
        # documented in parent
        return True

    def as_literal(self) -> 'OWLLiteral':
        # documented in parent
        return self

    def to_python(self) -> Literals:
        return self._v

    @abstractmethod
    def get_datatype(self) -> OWLDatatype:
        """Gets the OWLDatatype which types this literal.

        Returns:
            The OWLDatatype that types this literal.
        """
        pass


@total_ordering
class _OWLLiteralImplDouble(OWLLiteral):
    __slots__ = '_v'

    _v: float

    def __init__(self, value, type_=None):
        assert type_ is None or type_ == DoubleOWLDatatype
        if not isinstance(value, float):
            value = float(value)
        self._v = value

    def __eq__(self, other):
        if type(other) is type(self):
            return self._v == other._v
        return NotImplemented

    def __lt__(self, other):
        if type(other) is type(self):
            return self._v < other._v
        return NotImplemented

    def __hash__(self):
        return hash(self._v)

    def __repr__(self):
        return f'OWLLiteral({self._v})'

    def is_double(self) -> bool:
        return True

    def parse_double(self) -> float:
        # documented in parent
        return self._v

    # noinspection PyMethodMayBeStatic
    def get_datatype(self) -> OWLDatatype:
        # documented in parent
        return DoubleOWLDatatype


@total_ordering
class _OWLLiteralImplInteger(OWLLiteral):
    __slots__ = '_v'

    _v: int

    def __init__(self, value, type_=None):
        assert type_ is None or type_ == IntegerOWLDatatype
        if not isinstance(value, int):
            value = int(value)
        self._v = value

    def __eq__(self, other):
        if type(other) is type(self):
            return self._v == other._v
        return NotImplemented

    def __lt__(self, other):
        if type(other) is type(self):
            return self._v < other._v
        return NotImplemented

    def __hash__(self):
        return hash(self._v)

    def __repr__(self):
        return f'OWLLiteral({self._v})'

    def is_integer(self) -> bool:
        return True

    def parse_integer(self) -> int:
        # documented in parent
        return self._v

    # noinspection PyMethodMayBeStatic
    def get_datatype(self) -> OWLDatatype:
        # documented in parent
        return IntegerOWLDatatype


class _OWLLiteralImplBoolean(OWLLiteral):
    __slots__ = '_v'

    _v: bool

    def __init__(self, value, type_=None):
        assert type_ is None or type_ == BooleanOWLDatatype
        if not isinstance(value, bool):
            from distutils.util import strtobool
            value = bool(strtobool(value))
        self._v = value

    def __eq__(self, other):
        if type(other) is type(self):
            return self._v == other._v
        return NotImplemented

    def __hash__(self):
        return hash(self._v)

    def __repr__(self):
        return f'OWLLiteral({self._v})'

    def is_boolean(self) -> bool:
        return True

    def parse_boolean(self) -> bool:
        # documented in parent
        return self._v

    # noinspection PyMethodMayBeStatic
    def get_datatype(self) -> OWLDatatype:
        # documented in parent
        return BooleanOWLDatatype


@total_ordering
class _OWLLiteralImplString(OWLLiteral):
    __slots__ = '_v'

    _v: str

    def __init__(self, value, type_=None):
        assert type_ is None or type_ == StringOWLDatatype
        if not isinstance(value, str):
            value = str(value)
        self._v = value

    def __eq__(self, other):
        if type(other) is type(self):
            return self._v == other._v
        return NotImplemented

    def __lt__(self, other):
        if type(other) is type(self):
            return self._v < other._v
        return NotImplemented

    def __len__(self):
        return len(self._v)

    def __hash__(self):
        return hash(self._v)

    def __repr__(self):
        return f'OWLLiteral({self._v})'

    def is_string(self) -> bool:
        return True

    def parse_string(self) -> str:
        # documented in parent
        return self._v

    # noinspection PyMethodMayBeStatic
    def get_datatype(self) -> OWLDatatype:
        # documented in parent
        return StringOWLDatatype


@total_ordering
class _OWLLiteralImplDate(OWLLiteral):
    __slots__ = '_v'

    _v: date

    def __init__(self, value, type_=None):
        assert type_ is None or type_ == DateOWLDatatype
        if not isinstance(value, date):
            value = date.fromisoformat(value)
        self._v = value

    def __eq__(self, other):
        if type(other) is type(self):
            return self._v == other._v
        return NotImplemented

    def __lt__(self, other):
        if type(other) is type(self):
            return self._v < other._v
        return NotImplemented

    def __hash__(self):
        return hash(self._v)

    def __repr__(self):
        return f'OWLLiteral({self._v})'

    def is_date(self) -> bool:
        return True

    def parse_date(self) -> date:
        # documented in parent
        return self._v

    # noinspection PyMethodMayBeStatic
    def get_datatype(self) -> OWLDatatype:
        # documented in parent
        return DateOWLDatatype


@total_ordering
class _OWLLiteralImplDateTime(OWLLiteral):
    __slots__ = '_v'

    _v: datetime

    def __init__(self, value, type_=None):
        assert type_ is None or type_ == DateTimeOWLDatatype
        if not isinstance(value, datetime):
            value = value.replace("Z", "+00:00") if isinstance(value, str) and value[-1] == "Z" else value
            value = datetime.fromisoformat(value)
        self._v = value

    def __eq__(self, other):
        if type(other) is type(self):
            return self._v == other._v
        return NotImplemented

    def __lt__(self, other):
        if type(other) is type(self):
            return self._v < other._v
        return NotImplemented

    def __hash__(self):
        return hash(self._v)

    def __repr__(self):
        return f'OWLLiteral({self._v})'

    def is_datetime(self) -> bool:
        return True

    def parse_datetime(self) -> datetime:
        # documented in parent
        return self._v

    # noinspection PyMethodMayBeStatic
    def get_datatype(self) -> OWLDatatype:
        # documented in parent
        return DateTimeOWLDatatype


@total_ordering
class _OWLLiteralImplDuration(OWLLiteral):
    __slots__ = '_v'

    _v: Timedelta

    def __init__(self, value, type_=None):
        assert type_ is None or type_ == DurationOWLDatatype
        if not isinstance(value, Timedelta):
            value = Timedelta(value)
        self._v = value

    def get_literal(self) -> str:
        return self._v.isoformat()

    def __eq__(self, other):
        if type(other) is type(self):
            return self._v == other._v
        return NotImplemented

    def __lt__(self, other):
        if type(other) is type(self):
            return self._v < other._v
        return NotImplemented

    def __hash__(self):
        return hash(self._v)

    def __repr__(self):
        return f'OWLLiteral({self._v})'

    def is_duration(self) -> bool:
        return True

    def parse_duration(self) -> Timedelta:
        # documented in parent
        return self._v

    # noinspection PyMethodMayBeStatic
    def get_datatype(self) -> OWLDatatype:
        # documented in parent
        return DurationOWLDatatype


class _OWLLiteralImpl(OWLLiteral):
    __slots__ = '_v', '_datatype'

    def __init__(self, v, type_: OWLDatatype):
        assert isinstance(type_, OWLDatatype)
        self._v = v
        self._datatype = type_

    def get_datatype(self) -> OWLDatatype:
        return self._datatype

    def __eq__(self, other):
        if type(other) is type(self) and other.get_datatype() == self.get_datatype():
            return self._v == other._v
        return NotImplemented

    def __hash__(self):
        return hash((self._v, self._datatype))

    def __repr__(self):
        return f'OWLLiteral({repr(self._v)}, {self._datatype})'


class OWLQuantifiedDataRestriction(OWLQuantifiedRestriction[OWLDataRange],
                                   OWLDataRestriction, metaclass=ABCMeta):
    """Represents a quantified data restriction."""
    __slots__ = ()

    _filler: OWLDataRange

    def __init__(self, filler: OWLDataRange):
        self._filler = filler

    def get_filler(self) -> OWLDataRange:
        # documented in parent (HasFiller)
        return self._filler


class OWLDataCardinalityRestriction(OWLCardinalityRestriction[OWLDataRange],
                                    OWLQuantifiedDataRestriction,
                                    OWLDataRestriction, metaclass=ABCMeta):
    """Represents Data Property Cardinality Restrictions in the OWL 2 specification."""
    __slots__ = ()

    _property: OWLDataPropertyExpression

    @abstractmethod
    def __init__(self, cardinality: int, property: OWLDataPropertyExpression, filler: OWLDataRange):
        super().__init__(cardinality, filler)
        self._property = property

    def get_property(self) -> OWLDataPropertyExpression:
        # documented in parent
        return self._property

    def __repr__(self):
        return f"{type(self).__name__}(" \
               f"property={repr(self.get_property())},{self.get_cardinality()},filler={repr(self.get_filler())})"

    def __eq__(self, other):
        if type(other) == type(self):
            return self._property == other._property \
                   and self._cardinality == other._cardinality \
                   and self._filler == other._filler
        return NotImplemented

    def __hash__(self):
        return hash((self._property, self._cardinality, self._filler))


class OWLDataAllValuesFrom(OWLQuantifiedDataRestriction):
    """Represents DataAllValuesFrom class expressions in the OWL 2 Specification."""
    __slots__ = '_property'

    type_index: Final = 3013

    _property: OWLDataPropertyExpression

    def __init__(self, property: OWLDataPropertyExpression, filler: OWLDataRange):
        """Gets an OWLDataAllValuesFrom restriction.

        Args:
            property: The data property that the restriction acts along.
            filler: The data range that is the filler.

        Returns:
            An OWLDataAllValuesFrom restriction along the specified property with the specified filler.
        """
        super().__init__(filler)
        self._property = property

    def __repr__(self):
        return f"OWLDataAllValuesFrom(property={repr(self._property)},filler={repr(self._filler)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._filler == other._filler and self._property == other._property
        return NotImplemented

    def __hash__(self):
        return hash((self._filler, self._property))

    def get_property(self) -> OWLDataPropertyExpression:
        # documented in parent
        return self._property


class OWLDataComplementOf(OWLDataRange):
    """Represents DataComplementOf in the OWL 2 Specification."""
    type_index: Final = 4002

    _data_range: OWLDataRange

    def __init__(self, data_range: OWLDataRange):
        """
        Args:
            data_range: Data range to complement.
        """
        self._data_range = data_range

    def get_data_range(self) -> OWLDataRange:
        """
        Returns:
            The wrapped data range.
        """
        return self._data_range

    def __repr__(self):
        return f"OWLDataComplementOf({repr(self._data_range)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._data_range == other._data_range
        return NotImplemented

    def __hash__(self):
        return hash(self._data_range)


class OWLDataExactCardinality(OWLDataCardinalityRestriction):
    """Represents DataExactCardinality restrictions in the OWL 2 Specification."""
    __slots__ = '_cardinality', '_filler', '_property'

    type_index: Final = 3016

    def __init__(self, cardinality: int, property: OWLDataPropertyExpression, filler: OWLDataRange):
        """
        Args:
            cardinality: Cannot be negative.
            property: The property that the restriction acts along.
            filler: Data range for restriction

        Returns:
            A DataExactCardinality on the specified property.
        """
        super().__init__(cardinality, property, filler)

    def as_intersection_of_min_max(self) -> OWLObjectIntersectionOf:
        """Obtains an equivalent form that is a conjunction of a min cardinality and max cardinality restriction.

        Returns:
            The semantically equivalent but structurally simpler form (= 1 R D) = >= 1 R D and <= 1 R D.
        """
        args = self.get_cardinality(), self.get_property(), self.get_filler()
        return OWLObjectIntersectionOf((OWLDataMinCardinality(*args), OWLDataMaxCardinality(*args)))


class OWLDataHasValue(OWLHasValueRestriction[OWLLiteral], OWLDataRestriction):
    """Represents DataHasValue restrictions in the OWL 2 Specification."""
    __slots__ = '_property'

    type_index: Final = 3014

    _property: OWLDataPropertyExpression

    def __init__(self, property: OWLDataPropertyExpression, value: OWLLiteral):
        """Gets an OWLDataHasValue restriction.

        Args:
            property: The data property that the restriction acts along.
            filler: The literal value.

        Returns:
            An OWLDataHasValue restriction along the specified property with the specified literal.
        """
        super().__init__(value)
        self._property = property

    def __repr__(self):
        return f"OWLDataHasValue(property={repr(self._property)},value={repr(self._v)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._v == other._v and self._property == other._property
        return NotImplemented

    def __hash__(self):
        return hash((self._v, self._property))

    def as_some_values_from(self) -> OWLClassExpression:
        """A convenience method that obtains this restriction as an existential restriction with a nominal filler.

        Returns:
            The existential equivalent of this value restriction. simp(HasValue(p a)) = some(p {a}).
        """
        return OWLDataSomeValuesFrom(self.get_property(), OWLDataOneOf(self.get_filler()))

    def get_property(self) -> OWLDataPropertyExpression:
        # documented in parent
        return self._property


class OWLDataMaxCardinality(OWLDataCardinalityRestriction):
    """Represents DataMaxCardinality restrictions in the OWL 2 Specification."""
    __slots__ = '_cardinality', '_filler', '_property'

    type_index: Final = 3017

    def __init__(self, cardinality: int, property: OWLDataPropertyExpression, filler: OWLDataRange):
        """
        Args:
            cardinality: Cannot be negative.
            property: The property that the restriction acts along.
            filler: Data range for restriction.

        Returns:
            A DataMaxCardinality on the specified property.
        """
        super().__init__(cardinality, property, filler)


class OWLDataMinCardinality(OWLDataCardinalityRestriction):
    """Represents DataMinCardinality restrictions in the OWL 2 Specification."""
    __slots__ = '_cardinality', '_filler', '_property'

    type_index: Final = 3015

    def __init__(self, cardinality: int, property: OWLDataPropertyExpression, filler: OWLDataRange):
        """
        Args:
            cardinality: Cannot be negative.
            property: The property that the restriction acts along.
            filler: Data range for restriction.

        Returns:
            A DataMinCardinality on the specified property.
        """
        super().__init__(cardinality, property, filler)


class OWLDataOneOf(OWLDataRange, HasOperands[OWLLiteral]):
    """Represents DataOneOf in the OWL 2 Specification."""
    type_index: Final = 4003

    _values: Sequence[OWLLiteral]

    def __init__(self, values: Union[OWLLiteral, Iterable[OWLLiteral]]):
        if isinstance(values, OWLLiteral):
            self._values = values,
        else:
            for _ in values:
                assert isinstance(_, OWLLiteral)
            self._values = tuple(values)

    def values(self) -> Iterable[OWLLiteral]:
        """Gets the values that are in the oneOf.

         Returns:
             The values of this {@code DataOneOf} class expression.
        """
        yield from self._values

    def operands(self) -> Iterable[OWLLiteral]:
        # documented in parent
        yield from self.values()

    def __hash__(self):
        return hash(self._values)

    def __eq__(self, other):
        if type(other) == type(self):
            return self._values == other._values
        return NotImplemented

    def __repr__(self):
        return f'OWLDataOneOf({self._values})'


class OWLDataSomeValuesFrom(OWLQuantifiedDataRestriction):
    """Represents a DataSomeValuesFrom restriction in the OWL 2 Specification."""
    __slots__ = '_property'

    type_index: Final = 3012

    _property: OWLDataPropertyExpression

    def __init__(self, property: OWLDataPropertyExpression, filler: OWLDataRange):
        """Gets an OWLDataSomeValuesFrom restriction.

        Args:
            property: The data property that the restriction acts along.
            filler: The data range that is the filler.

        Returns:
            An OWLDataSomeValuesFrom restriction along the specified property with the specified filler.
        """
        super().__init__(filler)
        self._property = property

    def __repr__(self):
        return f"OWLDataSomeValuesFrom(property={repr(self._property)},filler={repr(self._filler)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._filler == other._filler and self._property == other._property
        return NotImplemented

    def __hash__(self):
        return hash((self._filler, self._property))

    def get_property(self) -> OWLDataPropertyExpression:
        # documented in parent
        return self._property


class OWLNaryDataRange(OWLDataRange, HasOperands[OWLDataRange]):
    """OWLNaryDataRange."""
    __slots__ = ()

    _operands: Sequence[OWLDataRange]

    def __init__(self, operands: Iterable[OWLDataRange]):
        """
        Args:
            operands: Data ranges.
        """
        self._operands = tuple(operands)

    def operands(self) -> Iterable[OWLDataRange]:
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


class OWLDataUnionOf(OWLNaryDataRange):
    """Represents a DataUnionOf data range in the OWL 2 Specification."""
    __slots__ = '_operands'
    type_index: Final = 4005

    _operands: Sequence[OWLDataRange]


class OWLDataIntersectionOf(OWLNaryDataRange):
    """Represents DataIntersectionOf  in the OWL 2 Specification."""
    __slots__ = '_operands'
    type_index: Final = 4004

    _operands: Sequence[OWLDataRange]


class OWLImportsDeclaration(HasIRI):
    """Represents an import statement in an ontology."""
    __slots__ = '_iri'

    def __init__(self, import_iri: IRI):
        """
        Args:
            import_import_iri: Imported ontology.

        Returns:
            An imports declaration.
        """
        self._iri = import_iri

    def get_iri(self) -> IRI:
        """Gets the import IRI.

        Returns:
            The import IRI that points to the ontology to be imported. The imported ontology might have this IRI as
            its ontology IRI but this is not mandated. For example, an ontology with a non-resolvable ontology IRI
            can be deployed at a resolvable URL.
        """
        return self._iri


class OWLLogicalAxiom(OWLAxiom, metaclass=ABCMeta):
    """A base interface of all axioms that affect the logical meaning of an ontology. This excludes declaration axioms
    (including imports declarations) and annotation axioms.
    """
    __slots__ = ()

    def __init__(self, annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(annotations=annotations)

    def is_logical_axiom(self) -> bool:
        return True


class OWLPropertyAxiom(OWLLogicalAxiom, metaclass=ABCMeta):
    """The base interface for property axioms."""
    __slots__ = ()

    def __init__(self, annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(annotations=annotations)


class OWLObjectPropertyAxiom(OWLPropertyAxiom, metaclass=ABCMeta):
    """The base interface for object property axioms."""
    __slots__ = ()


class OWLDataPropertyAxiom(OWLPropertyAxiom, metaclass=ABCMeta):
    """The base interface for data property axioms."""
    __slots__ = ()


class OWLIndividualAxiom(OWLLogicalAxiom, metaclass=ABCMeta):
    """The base interface for individual axioms."""
    __slots__ = ()

    def __init__(self, annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(annotations=annotations)


class OWLClassAxiom(OWLLogicalAxiom, metaclass=ABCMeta):
    """The base interface for class axioms."""
    __slots__ = ()

    def __init__(self, annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(annotations=annotations)


class OWLDeclarationAxiom(OWLAxiom):
    """Represents a Declaration axiom in the OWL 2 Specification. A declaration axiom declares an entity in an ontology.
       It doesn't affect the logical meaning of the ontology."""
    __slots__ = '_entity'

    _entity: OWLEntity

    def __init__(self, entity: OWLEntity, annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._entity = entity
        super().__init__(annotations=annotations)

    def get_entity(self) -> OWLEntity:
        return self._entity

    def __eq__(self, other):
        if type(other) is type(self):
            return self._entity == other._entity and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._entity, *self._annotations))

    def __repr__(self):
        return f'OWLDeclarationAxiom(entity={self._entity},annotations={self._annotations})'


class OWLDatatypeDefinitionAxiom(OWLLogicalAxiom):
    """Represents a DatatypeDefinition axiom in the OWL 2 Specification."""
    __slots__ = '_datatype', '_datarange'

    _datatype: OWLDatatype
    _datarange: OWLDataRange

    def __init__(self, datatype: OWLDatatype, datarange: OWLDataRange,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._datatype = datatype
        self._datarange = datarange
        super().__init__(annotations=annotations)

    def get_datatype(self) -> OWLDatatype:
        return self._datatype

    def get_datarange(self) -> OWLDataRange:
        return self._datarange

    def __eq__(self, other):
        if type(other) is type(self):
            return self._datatype == other._datatype and self._datarange == other._datarange \
                   and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._datatype, self._datarange, *self._annotations))

    def __repr__(self):
        return f'OWLDatatypeDefinitionAxiom(datatype={self._datatype},datarange={self._datarange},' \
               f'annotations={self._annotations})'


class OWLHasKeyAxiom(OWLLogicalAxiom, HasOperands[OWLPropertyExpression]):
    """Represents a HasKey axiom in the OWL 2 Specification."""
    __slots__ = '_class_expression', '_property_expressions'

    _class_expression: OWLClassExpression
    _property_expressions: List[OWLPropertyExpression]

    def __init__(self, class_expression: OWLClassExpression, property_expressions: List[OWLPropertyExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._class_expression = class_expression
        self._property_expressions = property_expressions
        super().__init__(annotations=annotations)

    def get_class_expression(self) -> OWLClassExpression:
        return self._class_expression

    def get_property_expressions(self) -> List[OWLPropertyExpression]:
        return self._property_expressions

    def operands(self) -> Iterable[OWLPropertyExpression]:
        yield from self._property_expressions

    def __eq__(self, other):
        if type(other) is type(self):
            return self._class_expression == other._class_expression \
                   and self._property_expressions == other._property_expressions \
                   and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._class_expression, *self._property_expressions, *self._annotations))

    def __repr__(self):
        return f'OWLHasKeyAxiom(class_expression={self._class_expression},' \
               f'property_expressions={self._property_expressions},annotations={self._annotations})'


class OWLNaryAxiom(Generic[_C], OWLAxiom, metaclass=ABCMeta):
    """Represents an axiom that contains two or more operands that could also be represented with multiple pairwise
    axioms.

    Args:
        _C: Class of contained objects.
    """
    __slots__ = ()

    @abstractmethod
    def as_pairwise_axioms(self) -> Iterable['OWLNaryAxiom[_C]']:
        pass


# noinspection PyUnresolvedReferences
# noinspection PyDunderSlots
class OWLNaryClassAxiom(OWLClassAxiom, OWLNaryAxiom[OWLClassExpression], metaclass=ABCMeta):
    """Represents an axiom that contains two or more operands that could also be represented with
        multiple pairwise axioms."""
    __slots__ = '_class_expressions'
    _class_expressions: List[OWLClassExpression]

    @abstractmethod
    def __init__(self, class_expressions: List[OWLClassExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._class_expressions = [*class_expressions]
        super().__init__(annotations=annotations)

    def class_expressions(self) -> Iterable[OWLClassExpression]:
        """Gets all of the top level class expressions that appear in this axiom.

        Returns:
            Sorted stream of class expressions that appear in the axiom.
        """
        yield from self._class_expressions

    def as_pairwise_axioms(self) -> Iterable['OWLNaryClassAxiom']:
        """Gets this axiom as a set of pairwise axioms; if the axiom contains only two operands,
        the axiom itself is returned unchanged, including its annotations.

        Returns:
            This axiom as a set of pairwise axioms.
        """
        if len(self._class_expressions) < 3:
            yield self
        else:
            yield from map(type(self), combinations(self._class_expressions, 2))

    def __eq__(self, other):
        if type(other) is type(self):
            return self._class_expressions == other._class_expressions and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((*self._class_expressions, *self._annotations))

    def __repr__(self):
        return f'{type(self).__name__}({self._class_expressions},{self._annotations})'


class OWLEquivalentClassesAxiom(OWLNaryClassAxiom):
    """Represents an EquivalentClasses axiom in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, class_expressions: List[OWLClassExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(class_expressions=class_expressions, annotations=annotations)

    def contains_named_equivalent_class(self) -> bool:
        return any(isinstance(ce, OWLClass) for ce in self._class_expressions)

    def contains_owl_nothing(self) -> bool:
        return any(isinstance(ce, OWLNothing) for ce in self._class_expressions)

    def contains_owl_thing(self) -> bool:
        return any(isinstance(ce, OWLThing) for ce in self._class_expressions)

    def named_classes(self) -> Iterable[OWLClass]:
        yield from (ce for ce in self._class_expressions if isinstance(ce, OWLClass))


class OWLDisjointClassesAxiom(OWLNaryClassAxiom):
    """Represents a DisjointClasses axiom in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, class_expressions: List[OWLClassExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(class_expressions=class_expressions, annotations=annotations)


class OWLNaryIndividualAxiom(OWLIndividualAxiom, OWLNaryAxiom[OWLIndividual], metaclass=ABCMeta):
    """Represents an axiom that contains two or more operands that could also be represented with
            multiple pairwise individual axioms."""
    __slots__ = '_individuals'

    _individuals: List[OWLIndividual]

    @abstractmethod
    def __init__(self, individuals: List[OWLIndividual],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._individuals = [*individuals]
        super().__init__(annotations=annotations)

    def individuals(self) -> Iterable[OWLIndividual]:
        """Get the individuals.

        Returns:
            Generator containing the individuals.
        """
        yield from self._individuals

    def as_pairwise_axioms(self) -> Iterable['OWLNaryIndividualAxiom']:
        if len(self._individuals) < 3:
            yield self
        else:
            yield from map(type(self), combinations(self._individuals, 2))

    def __eq__(self, other):
        if type(other) is type(self):
            return self._individuals == other._individuals and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((*self._individuals, *self._annotations))

    def __repr__(self):
        return f'{type(self).__name__}({self._individuals},{self._annotations})'


class OWLDifferentIndividualsAxiom(OWLNaryIndividualAxiom):
    """Represents a DifferentIndividuals axiom in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, individuals: List[OWLIndividual],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(individuals=individuals, annotations=annotations)


class OWLSameIndividualAxiom(OWLNaryIndividualAxiom):
    """Represents a SameIndividual axiom in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, individuals: List[OWLIndividual],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(individuals=individuals, annotations=annotations)


class OWLNaryPropertyAxiom(Generic[_P], OWLPropertyAxiom, OWLNaryAxiom[_P], metaclass=ABCMeta):
    """Represents an axiom that contains two or more operands that could also be represented with
       multiple pairwise property axioms."""
    __slots__ = '_properties'

    _properties: List[_P]

    @abstractmethod
    def __init__(self, properties: List[_P], annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._properties = [*properties]
        super().__init__(annotations=annotations)

    def properties(self) -> Iterable[_P]:
        """Get all the properties that appear in the axiom.

        Returns:
            Generator containing the properties.
        """
        yield from self._properties

    def as_pairwise_axioms(self) -> Iterable['OWLNaryPropertyAxiom']:
        if len(self._properties) < 3:
            yield self
        else:
            yield from map(type(self), combinations(self._properties, 2))

    def __eq__(self, other):
        if type(other) is type(self):
            return self._properties == other._properties and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((*self._properties, *self._annotations))

    def __repr__(self):
        return f'{type(self).__name__}({self._properties},{self._annotations})'


class OWLEquivalentObjectPropertiesAxiom(OWLNaryPropertyAxiom[OWLObjectPropertyExpression], OWLObjectPropertyAxiom):
    """Represents EquivalentObjectProperties axioms in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, properties: List[OWLObjectPropertyExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(properties=properties, annotations=annotations)


class OWLDisjointObjectPropertiesAxiom(OWLNaryPropertyAxiom[OWLObjectPropertyExpression], OWLObjectPropertyAxiom):
    """Represents DisjointObjectProperties axioms in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, properties: List[OWLObjectPropertyExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(properties=properties, annotations=annotations)


class OWLInverseObjectPropertiesAxiom(OWLNaryPropertyAxiom[OWLObjectPropertyExpression], OWLObjectPropertyAxiom):
    """Represents InverseObjectProperties axioms in the OWL 2 Specification."""
    __slots__ = '_first', '_second'

    _first: OWLObjectPropertyExpression
    _second: OWLObjectPropertyExpression

    def __init__(self, first: OWLObjectPropertyExpression, second: OWLObjectPropertyExpression,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._first = first
        self._second = second
        super().__init__(properties=[first, second], annotations=annotations)

    def get_first_property(self) -> OWLObjectPropertyExpression:
        return self._first

    def get_second_property(self) -> OWLObjectPropertyExpression:
        return self._second

    def __repr__(self):
        return f'OWLInverseObjectPropertiesAxiom(first={self._first},second={self._second},' \
               f'annotations={self._annotations})'


class OWLEquivalentDataPropertiesAxiom(OWLNaryPropertyAxiom[OWLDataPropertyExpression], OWLDataPropertyAxiom):
    """Represents EquivalentDataProperties axioms in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, properties: List[OWLDataPropertyExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(properties=properties, annotations=annotations)


class OWLDisjointDataPropertiesAxiom(OWLNaryPropertyAxiom[OWLDataPropertyExpression], OWLDataPropertyAxiom):
    """Represents DisjointDataProperties axioms in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, properties: List[OWLDataPropertyExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(properties=properties, annotations=annotations)


class OWLSubClassOfAxiom(OWLClassAxiom):
    """Represents an SubClassOf axiom in the OWL 2 Specification."""
    __slots__ = '_sub_class', '_super_class'

    _sub_class: OWLClassExpression
    _super_class: OWLClassExpression

    def __init__(self, sub_class: OWLClassExpression, super_class: OWLClassExpression,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        """Get an equivalent classes axiom with specified operands and no annotations.

        Args:
            sub_class: The sub-class.
            super_class: The super class.
            annotations: Annotations.
        """
        self._sub_class = sub_class
        self._super_class = super_class
        super().__init__(annotations=annotations)

    def get_sub_class(self) -> OWLClassExpression:
        return self._sub_class

    def get_super_class(self) -> OWLClassExpression:
        return self._super_class

    def __eq__(self, other):
        if type(other) is type(self):
            return self._super_class == other._super_class and self._sub_class == other._sub_class \
                   and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._super_class, self._sub_class, *self._annotations))

    def __repr__(self):
        return f'OWLSubClassOfAxiom(sub_class={self._sub_class},super_class={self._super_class},' \
               f'annotations={self._annotations})'


class OWLDisjointUnionAxiom(OWLClassAxiom):
    """Represents a DisjointUnion axiom in the OWL 2 Specification."""
    __slots__ = '_cls', '_class_expressions'

    _cls: OWLClass
    _class_expressions: List[OWLClassExpression]

    def __init__(self, cls_: OWLClass, class_expressions: List[OWLClassExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._cls = cls_
        self._class_expressions = class_expressions
        super().__init__(annotations=annotations)

    def get_owl_class(self) -> OWLClass:
        return self._cls

    def get_class_expressions(self) -> Iterable[OWLClassExpression]:
        yield from self._class_expressions

    def get_owl_equivalent_classes_axiom(self) -> OWLEquivalentClassesAxiom:
        return OWLEquivalentClassesAxiom(self._cls, OWLObjectUnionOf(self._class_expressions))

    def get_owl_disjoint_classes_axiom(self) -> OWLDisjointClassesAxiom:
        return OWLDisjointClassesAxiom(self._class_expressions)

    def __eq__(self, other):
        if type(other) is type(self):
            return self._cls == other._cls and self._class_expressions == other._class_expressions \
                   and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._cls, *self._class_expressions, *self._annotations))

    def __repr__(self):
        return f'OWLDisjointUnionAxiom(class={self._cls},class_expressions={self._class_expressions},' \
               f'annotations={self._annotations})'


class OWLClassAssertionAxiom(OWLIndividualAxiom):
    """Represents ClassAssertion axioms in the OWL 2 Specification."""
    __slots__ = '_individual', '_class_expression'

    _individual: OWLIndividual
    _class_expression: OWLClassExpression

    def __init__(self, individual: OWLIndividual, class_expression: OWLClassExpression,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        """Get a ClassAssertion axiom for the specified individual and class expression.
        Args:
            individual: The individual.
            class_expression: The class the individual belongs to.
            annotations: Annotations.
        """
        self._individual = individual
        self._class_expression = class_expression
        super().__init__(annotations=annotations)

    def get_individual(self) -> OWLIndividual:
        return self._individual

    def get_class_expression(self) -> OWLClassExpression:
        return self._class_expression

    def __eq__(self, other):
        if type(other) is type(self):
            return self._class_expression == other._class_expression and self._individual == other._individual \
                   and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._individual, self._class_expression, *self._annotations))

    def __repr__(self):
        return f'OWLClassAssertionAxiom(individual={self._individual},class_expression={self._class_expression},' \
               f'annotations={self._annotations})'


class OWLAnnotationAxiom(OWLAxiom, metaclass=ABCMeta):
    """A super interface for annotation axioms."""
    __slots__ = ()

    def is_annotation_axiom(self) -> bool:
        return True


class OWLAnnotationProperty(OWLProperty):
    """Represents an AnnotationProperty in the OWL 2 specification."""
    __slots__ = '_iri'

    _iri: IRI

    def __init__(self, iri: IRI):
        """Get a new OWLAnnotationProperty object.

        Args:
            iri: New OWLAnnotationProperty IRI.
        """
        self._iri = iri

    def get_iri(self) -> IRI:
        # documented in parent
        return self._iri


class OWLAnnotation(OWLObject):
    """Annotations are used in the various types of annotation axioms, which bind annotations to their subjects
    (i.e. axioms or declarations)."""
    __slots__ = '_property', '_value'

    _property: OWLAnnotationProperty
    _value: OWLAnnotationValue

    def __init__(self, property: OWLAnnotationProperty, value: OWLAnnotationValue):
        """Gets an annotation.

        Args:
            property: the annotation property.
            value: The annotation value.
        """
        self._property = property
        self._value = value

    def get_property(self) -> OWLAnnotationProperty:
        """Gets the property that this annotation acts along.

        Returns:
            The annotation property.
        """
        return self._property

    def get_value(self) -> OWLAnnotationValue:
        """Gets the annotation value. The type of value will depend upon the type of the annotation e.g. whether the
        annotation is an OWLLiteral, an IRI or an OWLAnonymousIndividual.

        Returns:
            The annotation value.
        """
        return self._value

    def __eq__(self, other):
        if type(other) is type(self):
            return self._property == other._property and self._value == other._value
        return NotImplemented

    def __hash__(self):
        return hash((self._property, self._value))

    def __repr__(self):
        return f'OWLAnnotation({self._property}, {self._value})'


class OWLAnnotationAssertionAxiom(OWLAnnotationAxiom):
    """Represents AnnotationAssertion axioms in the OWL 2 specification."""
    __slots__ = '_subject', '_annotation'

    _subject: OWLAnnotationSubject
    _annotation: OWLAnnotation

    def __init__(self, subject: OWLAnnotationSubject, annotation: OWLAnnotation):
        """Get an annotation assertion axiom - with annotations.

        Args:
            subject: Subject.
            annotation: Annotation.
        """
        assert isinstance(subject, OWLAnnotationSubject)
        assert isinstance(annotation, OWLAnnotation)

        self._subject = subject
        self._annotation = annotation

    def get_subject(self) -> OWLAnnotationSubject:
        """Gets the subject of this object.

        Returns:
            The subject.
        """
        return self._subject

    def get_property(self) -> OWLAnnotationProperty:
        """Gets the property.

        Returns:
            The property.
        """
        return self._annotation.get_property()

    def get_value(self) -> OWLAnnotationValue:
        """Gets the annotation value. This is either an IRI, an OWLAnonymousIndividual or an OWLLiteral.

        Returns:
            The annotation value.
        """
        return self._annotation.get_value()

    def __eq__(self, other):
        if type(other) is type(self):
            return self._subject == other._subject and self._annotation == other._annotation
        return NotImplemented

    def __hash__(self):
        return hash((self._subject, self._annotation))

    def __repr__(self):
        return f'OWLAnnotationAssertionAxiom({self._subject}, {self._annotation})'


class OWLSubAnnotationPropertyOfAxiom(OWLAnnotationAxiom):
    """Represents an SubAnnotationPropertyOf axiom in the OWL 2 specification."""
    __slots__ = '_sub_property', '_super_property'

    _sub_property: OWLAnnotationProperty
    _super_property: OWLAnnotationProperty

    def __init__(self, sub_property: OWLAnnotationProperty, super_property: OWLAnnotationProperty,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._sub_property = sub_property
        self._super_property = super_property
        super().__init__(annotations=annotations)

    def get_sub_property(self) -> OWLAnnotationProperty:
        return self._sub_property

    def get_super_property(self) -> OWLAnnotationProperty:
        return self._super_property

    def __eq__(self, other):
        if type(other) is type(self):
            return self._sub_property == other._sub_property and self._super_property == other._super_property \
                   and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._sub_property, self._super_property, *self._annotations))

    def __repr__(self):
        return f'OWLSubAnnotationPropertyOfAxiom(sub_property={self._sub_property},' \
               f'super_property={self._super_property},annotations={self._annotations})'


class OWLAnnotationPropertyDomainAxiom(OWLAnnotationAxiom):
    """Represents an AnnotationPropertyDomain axiom in the OWL 2 specification."""
    __slots__ = '_property', '_domain'

    _property: OWLAnnotationProperty
    _domain: IRI

    def __init__(self, property_: OWLAnnotationProperty, domain: IRI,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._property = property_
        self._domain = domain
        super().__init__(annotations=annotations)

    def get_property(self) -> OWLAnnotationProperty:
        return self._property

    def get_domain(self) -> IRI:
        return self._domain

    def __eq__(self, other):
        if type(other) is type(self):
            return self._property == other._property and self._domain == other._domain \
                   and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._property, self._domain, *self._annotations))

    def __repr__(self):
        return f'OWLAnnotationPropertyDomainAxiom({repr(self._property)},{repr(self._domain)},' \
               f'{repr(self._annotations)})'


class OWLAnnotationPropertyRangeAxiom(OWLAnnotationAxiom):
    """Represents an AnnotationPropertyRange axiom in the OWL 2 specification."""
    __slots__ = '_property', '_range'

    _property: OWLAnnotationProperty
    _range: IRI

    def __init__(self, property_: OWLAnnotationProperty, range_: IRI,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._property = property_
        self._range = range_
        super().__init__(annotations=annotations)

    def get_property(self) -> OWLAnnotationProperty:
        return self._property

    def get_range(self) -> IRI:
        return self._range

    def __eq__(self, other):
        if type(other) is type(self):
            return self._property == other._property and self._range == other._range \
                   and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._property, self._range, *self._annotations))

    def __repr__(self):
        return f'OWLAnnotationPropertyRangeAxiom({repr(self._property)},{repr(self._range)},' \
               f'{repr(self._annotations)})'


class OWLSubPropertyAxiom(Generic[_P], OWLPropertyAxiom):
    """
    Base interface for object and data sub-property axioms.
    """
    __slots__ = '_sub_property', '_super_property'

    _sub_property: _P
    _super_property: _P

    @abstractmethod
    def __init__(self, sub_property: _P, super_property: _P,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._sub_property = sub_property
        self._super_property = super_property
        super().__init__(annotations=annotations)

    def get_sub_property(self) -> _P:
        return self._sub_property

    def get_super_property(self) -> _P:
        return self._super_property

    def __eq__(self, other):
        if type(other) is type(self):
            return self._sub_property == other._sub_property and self._super_property == other._super_property \
                   and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._sub_property, self._super_property, *self._annotations))

    def __repr__(self):
        return f'{type(self).__name__}(sub_property={self._sub_property},super_property={self._super_property},' \
               f'annotations={self._annotations})'


class OWLSubObjectPropertyOfAxiom(OWLSubPropertyAxiom[OWLObjectPropertyExpression], OWLObjectPropertyAxiom):
    """Represents a SubObjectPropertyOf axiom in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, sub_property: OWLObjectPropertyExpression, super_property: OWLObjectPropertyExpression,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(sub_property=sub_property, super_property=super_property, annotations=annotations)


class OWLSubDataPropertyOfAxiom(OWLSubPropertyAxiom[OWLDataPropertyExpression], OWLDataPropertyAxiom):
    """Represents a SubDataPropertyOf axiom in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, sub_property: OWLDataPropertyExpression, super_property: OWLDataPropertyExpression,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(sub_property=sub_property, super_property=super_property, annotations=annotations)


class OWLPropertyAssertionAxiom(Generic[_P, _C], OWLIndividualAxiom, metaclass=ABCMeta):
    """Represents a PropertyAssertion axiom in the OWL 2 specification."""
    __slots__ = '_subject', '_property', '_object'

    _subject: OWLIndividual
    _property: _P
    _object: _C

    @abstractmethod
    def __init__(self, subject: OWLIndividual, property_: _P, object_: _C,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        """Get a PropertyAssertion axiom for the specified subject, property, object.
        Args:
            subject: The subject of the property assertion.
            property_: The property of the property assertion.
            object_: The object of the property assertion.
            annotations: Annotations.
        """
        assert isinstance(subject, OWLIndividual)

        self._subject = subject
        self._property = property_
        self._object = object_
        super().__init__(annotations=annotations)

    def get_subject(self) -> OWLIndividual:
        return self._subject

    def get_property(self) -> _P:
        return self._property

    def get_object(self) -> _C:
        return self._object

    def __eq__(self, other):
        if type(other) is type(self):
            return self._subject == other._subject and self._property == other._property and \
                   self._object == other._object and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._subject, self._property, self._object, *self._annotations))

    def __repr__(self):
        return f'{type(self).__name__}(subject={self._subject},property={self._property},' \
               f'object={self._object},annotation={self._annotations})'


class OWLObjectPropertyAssertionAxiom(OWLPropertyAssertionAxiom[OWLObjectPropertyExpression, OWLIndividual]):
    """Represents an ObjectPropertyAssertion axiom in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, subject: OWLIndividual, property_: OWLObjectPropertyExpression, object_: OWLIndividual,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(subject, property_, object_, annotations)


class OWLNegativeObjectPropertyAssertionAxiom(OWLPropertyAssertionAxiom[OWLObjectPropertyExpression, OWLIndividual]):
    """Represents a NegativeObjectPropertyAssertion axiom in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, subject: OWLIndividual, property_: OWLObjectPropertyExpression, object_: OWLIndividual,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(subject, property_, object_, annotations)


class OWLDataPropertyAssertionAxiom(OWLPropertyAssertionAxiom[OWLDataPropertyExpression, OWLLiteral]):
    """Represents an DataPropertyAssertion axiom in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, subject: OWLIndividual, property_: OWLDataPropertyExpression, object_: OWLLiteral,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(subject, property_, object_, annotations)


class OWLNegativeDataPropertyAssertionAxiom(OWLPropertyAssertionAxiom[OWLDataPropertyExpression, OWLLiteral]):
    """Represents an NegativeDataPropertyAssertion axiom in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, subject: OWLIndividual, property_: OWLDataPropertyExpression, object_: OWLLiteral,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(subject, property_, object_, annotations)


class OWLUnaryPropertyAxiom(Generic[_P], OWLPropertyAxiom, metaclass=ABCMeta):
    """Unary property axiom."""
    __slots__ = '_property'

    _property: _P

    def __init__(self, property_: _P, annotations: Optional[Iterable[OWLAnnotation]] = None):
        self._property = property_
        super().__init__(annotations=annotations)

    def get_property(self) -> _P:
        return self._property


class OWLObjectPropertyCharacteristicAxiom(OWLUnaryPropertyAxiom[OWLObjectPropertyExpression],
                                           OWLObjectPropertyAxiom, metaclass=ABCMeta):
    """Base interface for functional object property axiom."""
    __slots__ = ()

    @abstractmethod
    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)

    def __eq__(self, other):
        if type(other) is type(self):
            return self._property == other._property and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._property, *self._annotations))

    def __repr__(self):
        return f"{type(self).__name__}({repr(self._property)},{repr(self._annotations)})"


class OWLFunctionalObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """Represents FunctionalObjectProperty axioms in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLAsymmetricObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """Represents AsymmetricObjectProperty axioms in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLInverseFunctionalObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """Represents InverseFunctionalObjectProperty axioms in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLIrreflexiveObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """Represents IrreflexiveObjectProperty axioms in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLReflexiveObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """Represents ReflexiveObjectProperty axioms in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLSymmetricObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """Represents SymmetricObjectProperty axioms in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLTransitiveObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """Represents TransitiveObjectProperty axioms in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLDataPropertyCharacteristicAxiom(OWLUnaryPropertyAxiom[OWLDataPropertyExpression],
                                         OWLDataPropertyAxiom, metaclass=ABCMeta):
    """Base interface for Functional data property axiom."""
    __slots__ = ()

    @abstractmethod
    def __init__(self, property_: OWLDataPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)

    def __eq__(self, other):
        if type(other) is type(self):
            return self._property == other._property and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._property, *self._annotations))

    def __repr__(self):
        return f"{type(self).__name__}({repr(self._property)},{repr(self._annotations)})"


class OWLFunctionalDataPropertyAxiom(OWLDataPropertyCharacteristicAxiom):
    """Represents FunctionalDataProperty axioms in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, property_: OWLDataPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLPropertyDomainAxiom(Generic[_P], OWLUnaryPropertyAxiom[_P], metaclass=ABCMeta):
    """Represents ObjectPropertyDomain axioms in the OWL 2 specification."""
    __slots__ = '_domain'

    _domain: OWLClassExpression

    @abstractmethod
    def __init__(self, property_: _P, domain: OWLClassExpression,
                 annotations: Optional[Iterable[OWLAnnotation]] = None):
        self._domain = domain
        super().__init__(property_=property_, annotations=annotations)

    def get_domain(self) -> OWLClassExpression:
        return self._domain

    def __eq__(self, other):
        if type(other) is type(self):
            return self._property == other._property and self._domain == other._domain \
                   and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._property, self._domain, *self._annotations))

    def __repr__(self):
        return f"{type(self).__name__}({repr(self._property)},{repr(self._domain)},{repr(self._annotations)})"


class OWLPropertyRangeAxiom(Generic[_P, _R], OWLUnaryPropertyAxiom[_P], metaclass=ABCMeta):
    """Represents ObjectPropertyRange axioms in the OWL 2 specification."""
    __slots__ = '_range'

    _range: _R

    @abstractmethod
    def __init__(self, property_: _P, range_: _R, annotations: Optional[Iterable[OWLAnnotation]] = None):
        self._range = range_
        super().__init__(property_=property_, annotations=annotations)

    def get_range(self) -> _R:
        return self._range

    def __eq__(self, other):
        if type(other) is type(self):
            return self._property == other._property and self._range == other._range \
                   and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._property, self._range, *self._annotations))

    def __repr__(self):
        return f"{type(self).__name__}({repr(self._property)},{repr(self._range)},{repr(self._annotations)})"


class OWLObjectPropertyDomainAxiom(OWLPropertyDomainAxiom[OWLObjectPropertyExpression]):
    """ Represents a ObjectPropertyDomain axiom in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, domain: OWLClassExpression,
                 annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, domain=domain, annotations=annotations)


class OWLDataPropertyDomainAxiom(OWLPropertyDomainAxiom[OWLDataPropertyExpression]):
    """ Represents a DataPropertyDomain axiom in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, property_: OWLDataPropertyExpression, domain: OWLClassExpression,
                 annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, domain=domain, annotations=annotations)


class OWLObjectPropertyRangeAxiom(OWLPropertyRangeAxiom[OWLObjectPropertyExpression, OWLClassExpression]):
    """ Represents a ObjectPropertyRange axiom in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, range_: OWLClassExpression,
                 annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, range_=range_, annotations=annotations)


class OWLDataPropertyRangeAxiom(OWLPropertyRangeAxiom[OWLDataPropertyExpression, OWLDataRange]):
    """ Represents a DataPropertyRange axiom in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, property_: OWLDataPropertyExpression, range_: OWLDataRange,
                 annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, range_=range_, annotations=annotations)


class OWLOntology(OWLObject, metaclass=ABCMeta):
    """Represents an OWL 2 Ontology  in the OWL 2 specification.

    An OWLOntology consists of a possibly empty set of OWLAxioms and a possibly empty set of OWLAnnotations.
    An ontology can have an ontology IRI which can be used to identify the ontology. If it has an ontology IRI then
    it may also have an ontology version IRI. Since OWL 2, an ontology need not have an ontology IRI. (See the OWL 2
    Structural Specification).

    An ontology cannot be modified directly. Changes must be applied via its OWLOntologyManager.
    """
    __slots__ = ()
    type_index: Final = 1

    @abstractmethod
    def classes_in_signature(self) -> Iterable[OWLClass]:
        """Gets the classes in the signature of this object.

        Returns:
            Classes in the signature of this object.
        """
        pass

    @abstractmethod
    def data_properties_in_signature(self) -> Iterable[OWLDataProperty]:
        """Get the data properties that are in the signature of this object.

        Returns:
            Data properties that are in the signature of this object.
        """
        pass

    @abstractmethod
    def object_properties_in_signature(self) -> Iterable[OWLObjectProperty]:
        """A convenience method that obtains the object properties that are in the signature of this object.

        Returns:
            Object properties that are in the signature of this object.
        """
        pass

    @abstractmethod
    def individuals_in_signature(self) -> Iterable[OWLNamedIndividual]:
        """A convenience method that obtains the individuals that are in the signature of this object.

        Returns:
            Individuals that are in the signature of this object.
        """
        pass

    @abstractmethod
    def equivalent_classes_axioms(self, c: OWLClass) -> Iterable[OWLEquivalentClassesAxiom]:
        """ Gets all of the equivalent axioms in this ontology that contain the specified class as an operand.

        Args:
            c: The class for which the EquivalentClasses axioms should be retrieved.

        Returns:
            EquivalentClasses axioms contained in this ontology.
        """
        pass

    @abstractmethod
    def general_class_axioms(self) -> Iterable[OWLClassAxiom]:
        """Get the general class axioms of this ontology. This includes SubClass axioms with a complex class expression
           as the sub class and EquivalentClass axioms and DisjointClass axioms with only complex class expressions.

        Returns:
            General class axioms contained in this ontology.
        """
        pass

    @abstractmethod
    def data_property_domain_axioms(self, property: OWLDataProperty) -> Iterable[OWLDataPropertyDomainAxiom]:
        """Gets the OWLDataPropertyDomainAxiom objects where the property is equal to the specified property.

        Args:
            property: The property which is equal to the property of the retrieved axioms.

        Returns:
            The axioms matching the search.
        """
        pass

    @abstractmethod
    def data_property_range_axioms(self, property: OWLDataProperty) -> Iterable[OWLDataPropertyRangeAxiom]:
        """Gets the OWLDataPropertyRangeAxiom objects where the property is equal to the specified property.

        Args:
            property: The property which is equal to the property of the retrieved axioms.

        Returns:
            The axioms matching the search.
        """
        pass

    @abstractmethod
    def object_property_domain_axioms(self, property: OWLObjectProperty) -> Iterable[OWLObjectPropertyDomainAxiom]:
        """Gets the OWLObjectPropertyDomainAxiom objects where the property is equal to the specified property.

        Args:
            property: The property which is equal to the property of the retrieved axioms.

        Returns:
            The axioms matching the search.
        """
        pass

    @abstractmethod
    def object_property_range_axioms(self, property: OWLObjectProperty) -> Iterable[OWLObjectPropertyRangeAxiom]:
        """Gets the OWLObjectPropertyRangeAxiom objects where the property is equal to the specified property.

        Args:
            property: The property which is equal to the property of the retrieved axioms.

        Returns:
            The axioms matching the search.
        """
        pass

    @abstractmethod
    def get_owl_ontology_manager(self) -> _M:
        """Gets the manager that manages this ontology."""
        pass

    @abstractmethod
    def get_ontology_id(self) -> OWLOntologyID:
        """Gets the OWLOntologyID belonging to this object.

        Returns:
            The OWLOntologyID.
        """
        pass

    def is_anonymous(self) -> bool:
        """Check whether this ontology does contain an IRI or not."""
        return self.get_ontology_id().is_anonymous()


# noinspection PyUnresolvedReferences
# noinspection PyDunderSlots
class OWLOntologyChange(metaclass=ABCMeta):
    """Represents an ontology change."""
    __slots__ = ()

    _ont: OWLOntology

    @abstractmethod
    def __init__(self, ontology: OWLOntology):
        self._ont = ontology

    def get_ontology(self) -> OWLOntology:
        """Gets the ontology that the change is/was applied to.

        Returns:
            The ontology that the change is applicable to.
        """
        return self._ont


class AddImport(OWLOntologyChange):
    """Represents an ontology change where an import statement is added to an ontology."""
    __slots__ = '_ont', '_declaration'

    def __init__(self, ontology: OWLOntology, import_declaration: OWLImportsDeclaration):
        """
        Args:
            ontology: The ontology to which the change is to be applied.
            import_declaration: The import declaration.
        """
        super().__init__(ontology)
        self._declaration = import_declaration

    def get_import_declaration(self) -> OWLImportsDeclaration:
        """Gets the import declaration that the change pertains to.

        Returns:
            The import declaration.
        """
        return self._declaration


class OWLOntologyManager(metaclass=ABCMeta):
    """An OWLOntologyManager manages a set of ontologies. It is the main point for creating, loading and accessing
    ontologies."""

    @abstractmethod
    def create_ontology(self, iri: IRI) -> OWLOntology:
        """Creates a new (empty) ontology that that has the specified ontology IRI (and no version IRI).

        Args:
            iri: The IRI of the ontology to be created.

        Returns:
            The newly created ontology, or if an ontology with the specified IRI already exists then this existing
            ontology will be returned.
        """
        pass

    @abstractmethod
    def load_ontology(self, iri: IRI) -> OWLOntology:
        """Loads an ontology that is assumed to have the specified ontology IRI as its IRI or version IRI. The ontology
        IRI will be mapped to an ontology document IRI.

        Args:
            iri: The IRI that identifies the ontology. It is expected that the ontology will also have this IRI
                (although the OWL API should tolerate situations where this is not the case).

        Returns:
            The OWLOntology representation of the ontology that was loaded.
        """
        pass

    @abstractmethod
    def apply_change(self, change: OWLOntologyChange):
        """A convenience method that applies just one change to an ontology. When this method is used through an
        OWLOntologyManager implementation, the instance used should be the one that the ontology returns through the
        get_owl_ontology_manager() call.

        Args:
            change: The change to be applied.

        Raises:
            ChangeApplied.UNSUCCESSFULLY: if the change was not applied successfully.
        """
        pass

    @abstractmethod
    def add_axiom(self, ontology: OWLOntology, axiom: OWLAxiom):
        """A convenience method that adds a single axiom to an ontology.

        Args:
            ontology: The ontology to add the axiom to.
            axiom: The axiom to be added.
        """
        pass

    @abstractmethod
    def remove_axiom(self, ontology: OWLOntology, axiom: OWLAxiom):
        """A convenience method that removes a single axiom from an ontology.

        Args:
            ontology: The ontology to remove the axiom from.
            axiom: The axiom to be removed.
        """
        pass

    @abstractmethod
    def save_ontology(self, ontology: OWLOntology, document_iri: IRI):
        """Saves the specified ontology, using the specified document IRI to determine where/how the ontology should be
        saved.

        Args:
            ontology: The ontology to be saved.
            document_iri: The document IRI where the ontology should be saved to.
        """
        pass


class OWLReasoner(metaclass=ABCMeta):
    """An OWLReasoner reasons over a set of axioms (the set of reasoner axioms) that is based on the imports closure of
    a particular ontology - the "root" ontology."""
    __slots__ = ()

    @abstractmethod
    def __init__(self, ontology: OWLOntology):
        pass

    @abstractmethod
    def data_property_domains(self, pe: OWLDataProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are the direct or indirect domains of this property with respect to the
           imports closure of the root ontology.

        Args:
            pe: The property expression whose domains are to be retrieved.
            direct: Specifies if the direct domains should be retrieved (True), or if all domains should be retrieved
                (False).

        Returns:
            :Let N = equivalent_classes(DataSomeValuesFrom(pe rdfs:Literal)). If direct is True: then if N is not
            empty then the return value is N, else the return value is the result of
            super_classes(DataSomeValuesFrom(pe rdfs:Literal), true). If direct is False: then the result of
            super_classes(DataSomeValuesFrom(pe rdfs:Literal), false) together with N if N is non-empty.
            (Note, rdfs:Literal is the top datatype).
        """
        pass

    @abstractmethod
    def object_property_domains(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are the direct or indirect domains of this property with respect to the
           imports closure of the root ontology.

        Args:
            pe: The property expression whose domains are to be retrieved.
            direct: Specifies if the direct domains should be retrieved (True), or if all domains should be retrieved
                (False).

        Returns:
            :Let N = equivalent_classes(ObjectSomeValuesFrom(pe owl:Thing)). If direct is True: then if N is not empty
            then the return value is N, else the return value is the result of
            super_classes(ObjectSomeValuesFrom(pe owl:Thing), true). If direct is False: then the result of
            super_classes(ObjectSomeValuesFrom(pe owl:Thing), false) together with N if N is non-empty.
        """
        pass

    @abstractmethod
    def object_property_ranges(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are the direct or indirect ranges of this property with respect to the
           imports closure of the root ontology.

        Args:
            pe: The property expression whose ranges are to be retrieved.
            direct: Specifies if the direct ranges should be retrieved (True), or if all ranges should be retrieved
                (False).

        Returns:
            :Let N = equivalent_classes(ObjectSomeValuesFrom(ObjectInverseOf(pe) owl:Thing)). If direct is True: then
            if N is not empty then the return value is N, else the return value is the result of
            super_classes(ObjectSomeValuesFrom(ObjectInverseOf(pe) owl:Thing), true). If direct is False: then
            the result of super_classes(ObjectSomeValuesFrom(ObjectInverseOf(pe) owl:Thing), false) together with N
            if N is non-empty.
        """
        pass

    @abstractmethod
    def equivalent_classes(self, ce: OWLClassExpression, only_named: bool = True) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are equivalent to the specified class expression with respect to the set of
        reasoner axioms.

        Args:
            ce: The class expression whose equivalent classes are to be retrieved.
            only_named: Whether to only retrieve named equivalent classes or also complex class expressions.

        Returns:
            All class expressions C where the root ontology imports closure entails EquivalentClasses(ce C). If ce is
            not a class name (i.e. it is an anonymous class expression) and there are no such classes C then there will
            be no result. If ce is unsatisfiable with respect to the set of reasoner axioms then  owl:Nothing, i.e. the
            bottom node, will be returned.
        """
        pass

    @abstractmethod
    def disjoint_classes(self, ce: OWLClassExpression, only_named: bool = True) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are disjoint with specified class expression with respect to the set of
        reasoner axioms.

        Args:
            ce: The class expression whose disjoint classes are to be retrieved.
            only_named: Whether to only retrieve named disjoint classes or also complex class expressions.

        Returns:
            All class expressions D where the set of reasoner axioms entails EquivalentClasses(D ObjectComplementOf(ce))
            or StrictSubClassOf(D ObjectComplementOf(ce)).
        """
        pass

    @abstractmethod
    def different_individuals(self, ind: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        """Gets the individuals that are different from the specified individual with respect to the set of
        reasoner axioms.

        Args:
            ind: The individual whose different individuals are to be retrieved.

        Returns:
            All individuals x where the set of reasoner axioms entails DifferentIndividuals(ind x).
        """
        pass

    @abstractmethod
    def same_individuals(self, ind: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        """Gets the individuals that are the same as the specified individual with respect to the set of
        reasoner axioms.

        Args:
            ind: The individual whose same individuals are to be retrieved.

        Returns:
            All individuals x where the root ontology imports closure entails SameIndividual(ind x).
        """
        pass

    @abstractmethod
    def equivalent_object_properties(self, op: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        """Gets the simplified object properties that are equivalent to the specified object property with respect
        to the set of reasoner axioms.

        Args:
            op: The object property whose equivalent object properties are to be retrieved.

        Returns:
            All simplified object properties e where the root ontology imports closure entails
            EquivalentObjectProperties(op e). If op is unsatisfiable with respect to the set of reasoner axioms
            then owl:bottomDataProperty will be returned.
        """
        pass

    @abstractmethod
    def equivalent_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        """Gets the data properties that are equivalent to the specified data property with respect to the set of
        reasoner axioms.

        Args:
            dp: The data property whose equivalent data properties are to be retrieved.

        Returns:
            All data properties e where the root ontology imports closure entails EquivalentDataProperties(dp e).
            If dp is unsatisfiable with respect to the set of reasoner axioms then owl:bottomDataProperty will
            be returned.
        """
        pass

    @abstractmethod
    def data_property_values(self, ind: OWLNamedIndividual, pe: OWLDataProperty, direct: bool = True) \
            -> Iterable['OWLLiteral']:
        """Gets the data property values for the specified individual and data property expression.

        Args:
            ind: The individual that is the subject of the data property values.
            pe: The data property expression whose values are to be retrieved for the specified individual.
            direct: Specifies if the direct values should be retrieved (True), or if all values should be retrieved
                (False), so that sub properties are taken into account.

        Returns:
            A set of OWLLiterals containing literals such that for each literal l in the set, the set of reasoner
            axioms entails DataPropertyAssertion(pe ind l).
        """
        pass

    @abstractmethod
    def object_property_values(self, ind: OWLNamedIndividual, pe: OWLObjectPropertyExpression, direct: bool = True) \
            -> Iterable[OWLNamedIndividual]:
        """Gets the object property values for the specified individual and object property expression.

        Args:
            ind: The individual that is the subject of the object property values.
            pe: The object property expression whose values are to be retrieved for the specified individual.
            direct: Specifies if the direct values should be retrieved (True), or if all values should be retrieved
                (False), so that sub properties are taken into account.

        Returns:
            The named individuals such that for each individual j, the set of reasoner axioms entails
            ObjectPropertyAssertion(pe ind j).
        """
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flushes any changes stored in the buffer, which causes the reasoner to take into consideration the changes
        the current root ontology specified by the changes."""
        pass

    @abstractmethod
    def instances(self, ce: OWLClassExpression, direct: bool = False) -> Iterable[OWLNamedIndividual]:
        """Gets the individuals which are instances of the specified class expression.

        Args:
            ce: The class expression whose instances are to be retrieved.
            direct: Specifies if the direct instances should be retrieved (True), or if all instances should be
                retrieved (False).

        Returns:
            If direct is True, each named individual j where the set of reasoner axioms entails
            DirectClassAssertion(ce, j). If direct is False, each named individual j where the set of reasoner axioms
            entails ClassAssertion(ce, j). If ce is unsatisfiable with respect to the set of reasoner axioms then
            nothing returned.
        """
        pass

    @abstractmethod
    def sub_classes(self, ce: OWLClassExpression, direct: bool = False, only_named: bool = True) \
            -> Iterable[OWLClassExpression]:
        """Gets the set of named classes that are the strict (potentially direct) subclasses of the specified class
        expression with respect to the reasoner axioms.

        Args:
            ce: The class expression whose strict (direct) subclasses are to be retrieved.
            direct: Specifies if the direct subclasses should be retrieved (True) or if the all subclasses
                (descendant) classes should be retrieved (False).
            only_named: Whether to only retrieve named sub-classes or also complex class expressions.

        Returns:
            If direct is True, each class C where reasoner axioms entails DirectSubClassOf(C, ce). If direct is False,
            each class C where reasoner axioms entails StrictSubClassOf(C, ce). If ce is equivalent to owl:Nothing then
            nothing will be returned.
        """
        pass

    @abstractmethod
    def disjoint_object_properties(self, op: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        """Gets the simplified object properties that are disjoint with the specified object property with respect
        to the set of reasoner axioms.

        Args:
            op: The object property whose disjoint object properties are to be retrieved.

        Returns:
            All simplified object properties e where the root ontology imports closure entails
            EquivalentObjectProperties(e ObjectPropertyComplementOf(op)) or
            StrictSubObjectPropertyOf(e ObjectPropertyComplementOf(op)).
        """
        pass

    @abstractmethod
    def disjoint_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        """Gets the data properties that are disjoint with the specified data property with respect
        to the set of reasoner axioms.

        Args:
            dp: The data property whose disjoint data properties are to be retrieved.

        Returns:
            All data properties e where the root ontology imports closure entails
            EquivalentDataProperties(e DataPropertyComplementOf(dp)) or
            StrictSubDataPropertyOf(e DataPropertyComplementOf(dp)).
        """
        pass

    @abstractmethod
    def sub_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        """Gets the set of named data properties that are the strict (potentially direct) subproperties of the
        specified data property expression with respect to the imports closure of the root ontology.

        Args:
            dp: The data property whose strict (direct) subproperties are to be retrieved.
            direct: Specifies if the direct subproperties should be retrieved (True) or if the all subproperties
                (descendants) should be retrieved (False).

        Returns:
            If direct is True, each property P where the set of reasoner axioms entails DirectSubDataPropertyOf(P, pe).
            If direct is False, each property P where the set of reasoner axioms entails
            StrictSubDataPropertyOf(P, pe). If pe is equivalent to owl:bottomDataProperty then nothing will be
            returned.
        """
        pass

    @abstractmethod
    def super_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        """Gets the stream of data properties that are the strict (potentially direct) super properties of the
         specified data property with respect to the imports closure of the root ontology.

         Args:
             dp (OWLDataProperty): The data property whose super properties are to be retrieved.
             direct (bool): Specifies if the direct super properties should be retrieved (True) or if the all
                            super properties (ancestors) should be retrieved (False).

         Returns:
             Iterable of super properties.
         """
        pass

    @abstractmethod
    def sub_object_properties(self, op: OWLObjectPropertyExpression, direct: bool = False) \
            -> Iterable[OWLObjectPropertyExpression]:
        """Gets the stream of simplified object property expressions that are the strict (potentially direct)
        subproperties of the specified object property expression with respect to the imports closure of the root
        ontology.

        Args:
            op: The object property expression whose strict (direct) subproperties are to be retrieved.
            direct: Specifies if the direct subproperties should be retrieved (True) or if the all subproperties
                (descendants) should be retrieved (False).

        Returns:
            If direct is True, simplified object property expressions, such that for each simplified object property
            expression, P, the set of reasoner axioms entails DirectSubObjectPropertyOf(P, pe).
            If direct is False, simplified object property expressions, such that for each simplified object property
            expression, P, the set of reasoner axioms entails StrictSubObjectPropertyOf(P, pe).
            If pe is equivalent to owl:bottomObjectProperty then nothing will be returned.
        """
        pass

    @abstractmethod
    def super_object_properties(self, op: OWLObjectPropertyExpression, direct: bool = False) \
            -> Iterable[OWLObjectPropertyExpression]:
        """Gets the stream of object properties that are the strict (potentially direct) super properties of the
         specified object property with respect to the imports closure of the root ontology.

         Args:
             op (OWLObjectPropertyExpression): The object property expression whose super properties are to be
                                                retrieved.
             direct (bool): Specifies if the direct super properties should be retrieved (True) or if the all
                            super properties (ancestors) should be retrieved (False).

         Returns:
             Iterable of super properties.
         """
        pass

    @abstractmethod
    def types(self, ind: OWLNamedIndividual, direct: bool = False) -> Iterable[OWLClass]:
        """Gets the named classes which are (potentially direct) types of the specified named individual.

        Args:
            ind: The individual whose types are to be retrieved.
            direct: Specifies if the direct types should be retrieved (True), or if all types should be retrieved
                (False).

        Returns:
            If direct is True, each named class C where the set of reasoner axioms entails
            DirectClassAssertion(C, ind). If direct is False, each named class C where the set of reasoner axioms
            entails ClassAssertion(C, ind).
        """
        pass

    @abstractmethod
    def get_root_ontology(self) -> OWLOntology:
        """Gets the "root" ontology that is loaded into this reasoner. The reasoner takes into account the axioms in
        this ontology and its import's closure."""
        pass

    @abstractmethod
    def is_isolated(self):
        """Return True if this reasoner is using an isolated ontology."""
        pass

    @abstractmethod
    def is_using_triplestore(self):
        """Return True if this reasoner is using a triplestore to retrieve instances."""
        pass

    @abstractmethod
    def super_classes(self, ce: OWLClassExpression, direct: bool = False, only_named: bool = True) \
            -> Iterable[OWLClassExpression]:
        """Gets the stream of named classes that are the strict (potentially direct) super classes of the specified
        class expression with respect to the imports closure of the root ontology.

        Args:
            ce: The class expression whose strict (direct) super classes are to be retrieved.
            direct: Specifies if the direct super classes should be retrieved (True) or if the all super classes
                (ancestors) classes should be retrieved (False).
            only_named: Whether to only retrieve named super classes or also complex class expressions.

        Returns:
            If direct is True, each class C where the set of reasoner axioms entails DirectSubClassOf(ce, C).
            If direct is False, each class C where  set of reasoner axioms entails StrictSubClassOf(ce, C).
            If ce is equivalent to owl:Thing then nothing will be returned.
        """
        pass


"""Important constant objects section"""

OWLThing: Final = OWLClass(OWLRDFVocabulary.OWL_THING.get_iri())  #: : :The OWL Class corresponding to owl:Thing
OWLNothing: Final = OWLClass(OWLRDFVocabulary.OWL_NOTHING.get_iri())  #: : :The OWL Class corresponding to owl:Nothing
#: the built in top object property
OWLTopObjectProperty: Final = OWLObjectProperty(OWLRDFVocabulary.OWL_TOP_OBJECT_PROPERTY.get_iri())
#: the built in bottom object property
OWLBottomObjectProperty: Final = OWLObjectProperty(OWLRDFVocabulary.OWL_BOTTOM_OBJECT_PROPERTY.get_iri())
#: the built in top data property
OWLTopDataProperty: Final = OWLDataProperty(OWLRDFVocabulary.OWL_TOP_DATA_PROPERTY.get_iri())
#: the built in bottom data property
OWLBottomDataProperty: Final = OWLDataProperty(OWLRDFVocabulary.OWL_BOTTOM_DATA_PROPERTY.get_iri())

DoubleOWLDatatype: Final = OWLDatatype(XSDVocabulary.DOUBLE)  #: An object representing a double datatype.
IntegerOWLDatatype: Final = OWLDatatype(XSDVocabulary.INTEGER)  #: An object representing an integer datatype.
BooleanOWLDatatype: Final = OWLDatatype(XSDVocabulary.BOOLEAN)  #: An object representing the boolean datatype.
StringOWLDatatype: Final = OWLDatatype(XSDVocabulary.STRING)  #: An object representing the string datatype.
DateOWLDatatype: Final = OWLDatatype(XSDVocabulary.DATE)  #: An object representing the date datatype.
DateTimeOWLDatatype: Final = OWLDatatype(XSDVocabulary.DATE_TIME)  #: An object representing the dateTime datatype.
DurationOWLDatatype: Final = OWLDatatype(XSDVocabulary.DURATION)  #: An object representing the duration datatype.
#: The OWL Datatype corresponding to the top data type
TopOWLDatatype: Final = OWLDatatype(OWLRDFVocabulary.RDFS_LITERAL)

NUMERIC_DATATYPES: Final[Set[OWLDatatype]] = {DoubleOWLDatatype, IntegerOWLDatatype}
TIME_DATATYPES: Final[Set[OWLDatatype]] = {DateOWLDatatype, DateTimeOWLDatatype, DurationOWLDatatype}
