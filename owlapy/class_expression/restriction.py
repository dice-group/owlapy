"""OWL Restrictions"""
from abc import ABCMeta, abstractmethod
from ..meta_classes import HasFiller, HasCardinality, HasOperands
from typing import TypeVar, Generic, Final, Sequence, Union, Iterable
from .nary_boolean_expression import OWLObjectIntersectionOf, OWLObjectUnionOf
from .class_expression import OWLAnonymousClassExpression, OWLClassExpression
from ..owl_property import OWLPropertyExpression, OWLObjectPropertyExpression, OWLDataPropertyExpression
from ..owl_data_ranges import OWLPropertyRange, OWLDataRange
from ..owl_literal import OWLLiteral
from ..owl_individual import OWLIndividual
from ..owl_datatype import OWLDatatype
from ..owl_object import OWLObject
from ..vocab import OWLFacet
from datetime import datetime, date
from pandas import Timedelta

_T = TypeVar('_T')  #:
_F = TypeVar('_F', bound=OWLPropertyRange)  #:

Literals = Union['OWLLiteral', int, float, bool, Timedelta, datetime, date, str]  #:


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


class OWLHasValueRestriction(Generic[_T], OWLRestriction, HasFiller[_T], metaclass=ABCMeta):
    """Represent a HasValue restriction in the OWL 2

    Args:
        value: The value type _T.
    """
    __slots__ = ()

    _v: _T

    def __init__(self, value: _T):
        self._v = value

    def __eq__(self, other):
        if type(other) is type(self):
            return self._v == other._v
        return False

    def __hash__(self):
        return hash(self._v)

    def get_filler(self) -> _T:
        # documented in parent
        return self._v


# =================================================================================================================
# =========================================OBJECT RESTRICTIONS=====================================================
# =================================================================================================================


class OWLObjectRestriction(OWLRestriction, metaclass=ABCMeta):
    """Represents an Object Property Restriction in the OWL 2 specification."""
    __slots__ = ()

    def is_object_restriction(self) -> bool:
        # documented in parent
        return True

    @abstractmethod
    def get_property(self) -> OWLObjectPropertyExpression:
        # documented in parent
        pass


class OWLQuantifiedRestriction(Generic[_T], OWLRestriction, HasFiller[_T], metaclass=ABCMeta):
    """Represents a quantified restriction.

    Args:
        _T: value type
    """
    __slots__ = ()
    pass


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


class OWLObjectCardinalityRestriction(OWLCardinalityRestriction[OWLClassExpression], OWLQuantifiedObjectRestriction,
                                      metaclass=ABCMeta):
    """Represents Object Property Cardinality Restrictions in the OWL 2 specification."""
    __slots__ = ()

    _property: OWLObjectPropertyExpression
    # @TODO: CD: property shows the in-built function

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
        if type(other) is type(self):
            return self._property == other._property \
                and self._cardinality == other._cardinality \
                and self._filler == other._filler
        else:
            return False

    def __hash__(self):
        return hash((self._property, self._cardinality, self._filler))


class OWLObjectMinCardinality(OWLObjectCardinalityRestriction):
    """A minimum cardinality expression ObjectMinCardinality( n OPE CE ) consists of a nonnegative integer n, an object
    property expression OPE, and a class expression CE, and it contains all those individuals that are connected by OPE
    to at least n different individuals that are instances of CE.
    (https://www.w3.org/TR/owl2-syntax/#Minimum_Cardinality)"""
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
    """A maximum cardinality expression ObjectMaxCardinality( n OPE CE ) consists of a nonnegative integer n, an object
    property expression OPE, and a class expression CE, and it contains all those individuals that are connected by OPE
     to at most n different individuals that are instances of CE.
     (https://www.w3.org/TR/owl2-syntax/#Maximum_Cardinality)"""
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
    """An exact cardinality expression ObjectExactCardinality( n OPE CE ) consists of a nonnegative integer n, an object
       property expression OPE, and a class expression CE, and it contains all those individuals that are connected by
       to exactly n different individuals that are instances of CE.
      (https://www.w3.org/TR/owl2-syntax/#Exact_Cardinality)
      """
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


class OWLObjectSomeValuesFrom(OWLQuantifiedObjectRestriction):
    """An existential class expression ObjectSomeValuesFrom( OPE CE ) consists of an object property expression OPE and
     a class expression CE, and it contains all those individuals that are connected by OPE to an individual that is
     an instance of CE. """
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
        else:
            return False

    def __hash__(self):
        return hash(("OWLObjectSomeValuesFrom",self._filler, self._property))

    def get_property(self) -> OWLObjectPropertyExpression:
        # documented in parent
        return self._property


class OWLObjectAllValuesFrom(OWLQuantifiedObjectRestriction):
    """A universal class expression ObjectAllValuesFrom( OPE CE ) consists of an object property expression OPE and a
    class expression CE, and it contains all those individuals that are connected by OPE only to
    individuals that are instances of CE. (https://www.w3.org/TR/owl2-syntax/#Universal_Quantification)"""
    __slots__ = '_property', '_filler'
    type_index: Final = 3006
    # @TODO: CD: property shows the in-built function
    def __init__(self, property: OWLObjectPropertyExpression, filler: OWLClassExpression):
        super().__init__(filler)
        self._property = property

    def __repr__(self):
        return f"OWLObjectAllValuesFrom(property={repr(self._property)},filler={repr(self._filler)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._filler == other._filler and self._property == other._property
        else:
            return False

    def __hash__(self):
        return hash(("OWLObjectAllValuesFrom",self._filler, self._property))

    def get_property(self) -> OWLObjectPropertyExpression:
        # documented in parent
        return self._property


class OWLObjectHasSelf(OWLObjectRestriction):
    """A self-restriction ObjectHasSelf( OPE ) consists of an object property expression OPE,
    and it contains all those individuals that are connected by OPE to themselves.
    (https://www.w3.org/TR/owl2-syntax/#Self-Restriction)
    """
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
        if type(other) is type(self):
            return self._property == other._property
        else:
            return False

    def __hash__(self):
        return hash(("OWLObjectHasSelf", self._property))

    def __repr__(self):
        return f'OWLObjectHasSelf({self._property})'


class OWLObjectHasValue(OWLHasValueRestriction[OWLIndividual], OWLObjectRestriction):
    """A has-value class expression ObjectHasValue( OPE a ) consists of an object property expression OPE and an
    individual a, and it contains all those individuals that are connected by OPE to a. Each such class expression
    can be seen as a syntactic shortcut for the class expression ObjectSomeValuesFrom( OPE ObjectOneOf( a ) ).
    (https://www.w3.org/TR/owl2-syntax/#Individual_Value_Restriction)
    """
    __slots__ = '_property', '_v'
    type_index: Final = 3007

    _property: OWLObjectPropertyExpression
    _v: OWLIndividual
    # @TODO: CD: property shows the in-built function
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
    """An enumeration of individuals ObjectOneOf( a1 ... an ) contains exactly the individuals ai with 1 ≤ i ≤ n.
    (https://www.w3.org/TR/owl2-syntax/#Enumeration_of_Individuals)
    """
    __slots__ = '_values'
    type_index: Final = 3004

    def __init__(self, values: OWLIndividual | Iterable[OWLIndividual]):
        #assert isinstance(values, OWLIndividual) | isinstance(values, set)
        #    f"The input of OWLObjectOneOf must be either an OWLIndividual or a set of OWLIndividual. Currently, {type(values)}!"
        if isinstance(values, OWLIndividual):
            self._values = values,
        else:
            for _ in values:
                assert isinstance(_, OWLIndividual)
            self._values = frozenset(values)

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
        return hash(("OWLObjectOneOf", self._values))

    def __eq__(self, other):
        if type(other) is type(self):
            if isinstance(self._values, OWLIndividual):
                return self._values == other._values
            else:
                return set(self._values) == set(other._values) and len(self._values) == len(other._values)
        return False

    def __repr__(self):
        return f'OWLObjectOneOf({self._values})'


# =================================================================================================================
# =========================================DATA RESTRICTIONS=======================================================
# =================================================================================================================


class OWLDataRestriction(OWLRestriction, metaclass=ABCMeta):
    """Represents a Data Property Restriction."""
    __slots__ = ()

    def is_data_restriction(self) -> bool:
        # documented in parent
        return True


class OWLQuantifiedDataRestriction(OWLQuantifiedRestriction[OWLDataRange],
                                   OWLDataRestriction, metaclass=ABCMeta):
    """Represents a quantified data restriction."""
    __slots__ = ()

    _filler: OWLDataRange

    def __init__(self, filler: OWLDataRange):
        assert isinstance(filler, OWLDataRange), "filler must be an OWLDataRange"
        self._filler = filler
    # @TODO:CD: define it as @property

    def get_filler(self) -> OWLDataRange:
        # documented in parent (HasFiller)
        return self._filler


class OWLDataCardinalityRestriction(OWLCardinalityRestriction[OWLDataRange],
                                    OWLQuantifiedDataRestriction,
                                    OWLDataRestriction, metaclass=ABCMeta):
    """Represents Data Property Cardinality Restrictions."""
    __slots__ = ()

    _property: OWLDataPropertyExpression
    # @TODO: CD: property shows the in-built function

    @abstractmethod
    def __init__(self, cardinality: int, property: OWLDataPropertyExpression, filler: OWLDataRange):
        assert isinstance(filler, OWLDataRange), "filler must be an OWLDataRange"
        super().__init__(cardinality, filler)
        self._property = property

    def __hash__(self):
        return hash(("OWLDataCardinalityRestriction",self._property, self._cardinality, self._filler))

    def __repr__(self):
        return f"{type(self).__name__}(" \
               f"property={repr(self.get_property())},{self.get_cardinality()},filler={repr(self.get_filler())})"

    def __eq__(self, other):
        if type(other) is type(self):
            return (self._property == other._property and self._cardinality == other._cardinality
                    and self._filler == other._filler)
        else:
            return False

    def get_property(self) -> OWLDataPropertyExpression:
        # documented in parent
        return self._property


class OWLDataMinCardinality(OWLDataCardinalityRestriction):
    """A minimum cardinality expression DataMinCardinality( n DPE DR ) consists of a nonnegative integer n, a data
       property expression DPE, and a unary data range DR, and it contains all those individuals that are connected by
       DPE to at least n different literals in DR.
       (https://www.w3.org/TR/owl2-syntax/#Minimum_Cardinality)
       """
    __slots__ = '_cardinality', '_filler', '_property'

    type_index: Final = 3015
    # @TODO: CD: property shows the in-built function

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


class OWLDataMaxCardinality(OWLDataCardinalityRestriction):
    """A maximum cardinality expression ObjectMaxCardinality( n OPE CE ) consists of a nonnegative integer n, an object
    property expression OPE, and a class expression CE, and it contains all those individuals that are connected by OPE
    to at most n different individuals that are instances of CE.
    (https://www.w3.org/TR/owl2-syntax/#Maximum_Cardinality)
    """
    __slots__ = '_cardinality', '_filler', '_property'

    type_index: Final = 3017
    # @TODO: CD: property shows the in-built function

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


class OWLDataExactCardinality(OWLDataCardinalityRestriction):
    """An exact cardinality expression ObjectExactCardinality( n OPE CE ) consists of a nonnegative integer n, an
    object property expression OPE, and a class expression CE, and it contains all those individuals that are connected
     by OPE to exactly n different individuals that are instances of CE
     (https://www.w3.org/TR/owl2-syntax/#Exact_Cardinality)
     """
    __slots__ = '_cardinality', '_filler', '_property'

    type_index: Final = 3016
    # @TODO: CD: property shows the in-built function

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


class OWLDataSomeValuesFrom(OWLQuantifiedDataRestriction):
    """An existential class expression DataSomeValuesFrom( DPE1 ... DPEn DR ) consists of n data property expressions
     DPEi, 1 ≤ i ≤ n, and a data range DR whose arity must be n. Such a class expression contains all those individuals
     that are connected by DPEi to literals lti, 1 ≤ i ≤ n, such that the tuple ( lt1 , ..., ltn ) is in DR. A class
     expression of the form DataSomeValuesFrom( DPE DR ) can be seen as a syntactic shortcut for the class expression
     DataMinCardinality( 1 DPE DR ).
     (https://www.w3.org/TR/owl2-syntax/#Existential_Quantification_2)
     """
    __slots__ = '_property'

    type_index: Final = 3012

    _property: OWLDataPropertyExpression
    # @TODO: CD: property shows the in-built function

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
        else:
            return False

    def __hash__(self):
        return hash(("OWLDataSomeValuesFrom",self._filler, self._property))

    def get_property(self) -> OWLDataPropertyExpression:
        # documented in parent
        return self._property


class OWLDataAllValuesFrom(OWLQuantifiedDataRestriction):
    """A universal class expression DataAllValuesFrom( DPE1 ... DPEn DR ) consists of n data property expressions DPEi,
    1 ≤ i ≤ n, and a data range DR whose arity must be n. Such a class expression contains all those individuals that
     are connected by DPEi only to literals lti, 1 ≤ i ≤ n, such that each tuple ( lt1 , ..., ltn ) is in DR. A class
      expression of the form DataAllValuesFrom( DPE DR ) can be seen as a syntactic shortcut for the class expression
      DataMaxCardinality( 0 DPE DataComplementOf( DR ) ).
      (https://www.w3.org/TR/owl2-syntax/#Universal_Quantification_2)
      """
    __slots__ = '_property'

    type_index: Final = 3013

    _property: OWLDataPropertyExpression
    # @TODO:CD:property shows the in-built function

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
        else:
            return False

    def __hash__(self):
        return hash(("OWLDataAllValuesFrom",self._filler, self._property))

    def get_property(self) -> OWLDataPropertyExpression:
        # documented in parent
        return self._property


class OWLDataHasValue(OWLHasValueRestriction[OWLLiteral], OWLDataRestriction):
    """A has-value class expression DataHasValue( DPE lt ) consists of a data property expression DPE and a literal lt,
    and it contains all those individuals that are connected by DPE to lt. Each such class expression can be seen as a
    syntactic shortcut for the class expression DataSomeValuesFrom( DPE DataOneOf( lt ) ).
    (https://www.w3.org/TR/owl2-syntax/#Literal_Value_Restriction)
    """
    __slots__ = '_property'
    # @TODO:CD:What is _v? even if it is inherited from somewhere, we should add it into docstring.
    # @TODO:CD: We should also name the class attributes in a more meaningful manner.
    # AB re: _v is indeed inherited and represents the value of this DataHasValue CE. It's name is kept general
    # because the value can have different types depending on the implementor of the base class.

    type_index: Final = 3014

    _property: OWLDataPropertyExpression
    # @TODO: CD: property shows the in-built function

    def __init__(self, property: OWLDataPropertyExpression, value: OWLLiteral):
        """Gets an OWLDataHasValue restriction.

        Args:
            property: The data property that the restriction acts along.
            value: The literal value.

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
        else:
            return False

    def __hash__(self):
        return hash(("OWLDataHasValue", self._v, self._property))

    def as_some_values_from(self) -> OWLClassExpression:
        """A convenience method that obtains this restriction as an existential restriction with a nominal filler.

        Returns:
            The existential equivalent of this value restriction. simp(HasValue(p a)) = some(p {a}).
        """
        return OWLDataSomeValuesFrom(self.get_property(), OWLDataOneOf(self.get_filler()))

    def get_property(self) -> OWLDataPropertyExpression:
        # documented in parent
        return self._property


class OWLDataOneOf(OWLDataRange, HasOperands[OWLLiteral]):
    """An enumeration of literals DataOneOf( lt1 ... ltn ) contains exactly the explicitly specified literals lti with
    1 ≤ i ≤ n. The resulting data range has arity one. (https://www.w3.org/TR/owl2-syntax/#Enumeration_of_Literals)"""
    type_index: Final = 4003

    _values: Sequence[OWLLiteral]

    def __init__(self, values: Union[OWLLiteral, Iterable[OWLLiteral]]):
        if isinstance(values, OWLLiteral):
            self._values = values,
        else:
            for _ in values:
                assert isinstance(_, OWLLiteral)
            self._values = tuple(values)

    def __repr__(self):
        return f'OWLDataOneOf({self._values})'

    def __hash__(self):
        return hash(("OWLDataOneOf",self._values))

    def __eq__(self, other):
        if type(other) is type(self):
            return {i for i in self._values} == {j for j in other._values}
        else:
            return False
    # TODO:CD: define it as @property as the name of the class method does not correspond to an action

    def values(self) -> Iterable[OWLLiteral]:
        """Gets the values that are in the oneOf.

         Returns:
             The values of this {@code DataOneOf} class expression.
        """
        yield from self._values

    def operands(self) -> Iterable[OWLLiteral]:
        # documented in parent
        yield from self.values()


class OWLDatatypeRestriction(OWLDataRange):
    """A datatype restriction DatatypeRestriction( DT F1 lt1 ... Fn ltn ) consists of a unary datatype DT and n pairs
    ( Fi , lti ). The resulting data range is unary and is obtained by restricting the value space of DT according to
    the semantics of all ( Fi , vi ) (multiple pairs are interpreted conjunctively), where vi are the data values of
    the literals lti.
    (https://www.w3.org/TR/owl2-syntax/#Datatype_Restrictions)
    """
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
        else:
            return False

    def __hash__(self):
        return hash(("OWLDatatypeRestriction", self._type, self._facet_restrictions))

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
        else:
            return False

    def __hash__(self):
        return hash(("OWLFacetRestriction", self._facet, self._literal))

    def __repr__(self):
        return f'OWLFacetRestriction({self._facet}, {repr(self._literal)})'

