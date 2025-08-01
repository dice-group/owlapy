"""OWL Literals"""
from decimal import Decimal
from abc import ABCMeta, abstractmethod
from enum import Enum
from functools import total_ordering
from .owl_annotation import OWLAnnotationValue
from typing import Final, Optional, Union, Set
from .owl_datatype import OWLDatatype
from datetime import datetime, date, time
from pandas import Timedelta
from owlapy.vocab import OWLRDFVocabulary, XSDVocabulary
from .owl_property import OWLObjectProperty, OWLDataProperty
import re

#: the built-in top object property
OWLTopObjectProperty: Final = OWLObjectProperty(OWLRDFVocabulary.OWL_TOP_OBJECT_PROPERTY.iri)

#: the built-in bottom object property
OWLBottomObjectProperty: Final = OWLObjectProperty(OWLRDFVocabulary.OWL_BOTTOM_OBJECT_PROPERTY.iri)

#: the built-in top data property
OWLTopDataProperty: Final = OWLDataProperty(OWLRDFVocabulary.OWL_TOP_DATA_PROPERTY.iri)

#: the built-in bottom data property
OWLBottomDataProperty: Final = OWLDataProperty(OWLRDFVocabulary.OWL_BOTTOM_DATA_PROPERTY.iri)

#: An object representing a double datatype.
DoubleOWLDatatype: Final = OWLDatatype(XSDVocabulary.DOUBLE)

#: An object representing a double datatype.
FloatOWLDatatype: Final = OWLDatatype(XSDVocabulary.FLOAT)

#: An object representing a double datatype.
DecimalOWLDatatype: Final = OWLDatatype(XSDVocabulary.DECIMAL)

#: An object representing an integer datatype.
IntegerOWLDatatype: Final = OWLDatatype(XSDVocabulary.INTEGER)

#: An object representing a non-negative integer datatype.
NonNegativeIntegerOWLDatatype: Final = OWLDatatype(XSDVocabulary.NONNEGATIVEINTEGER)

#: An object representing a non-positive integer datatype.
NonPositiveIntegerOWLDatatype: Final = OWLDatatype(XSDVocabulary.NONPOSITIVEINTEGER)

#: An object representing a negative integer datatype.
NegativeIntegerOWLDatatype: Final = OWLDatatype(XSDVocabulary.NEGATIVEINTEGER)

#: An object representing a positive integer datatype.
PositiveIntegerOWLDatatype: Final = OWLDatatype(XSDVocabulary.POSITIVEINTEGER)

#: An object representing the boolean datatype.
BooleanOWLDatatype: Final = OWLDatatype(XSDVocabulary.BOOLEAN)

#: An object representing the string datatype.
StringOWLDatatype: Final = OWLDatatype(XSDVocabulary.STRING)

#: An object representing the date datatype.
DateOWLDatatype: Final = OWLDatatype(XSDVocabulary.DATE)

#: An object representing the time datatype.
TimeOWLDatatype: Final = OWLDatatype(XSDVocabulary.TIME)

#: An object representing the gYearMonth datatype.
GYearMonthOWLDatatype: Final = OWLDatatype(XSDVocabulary.GYEARMONTH)

#: An object representing the gMonthDay datatype.
GMonthDayOWLDatatype: Final = OWLDatatype(XSDVocabulary.GMONTHDAY)

#: An object representing the gYear datatype.
GYearOWLDatatype: Final = OWLDatatype(XSDVocabulary.GYEAR)

#: An object representing the gMonth datatype.
GMonthOWLDatatype: Final = OWLDatatype(XSDVocabulary.GMONTH)

#: An object representing the gDay datatype.
GDayOWLDatatype: Final = OWLDatatype(XSDVocabulary.GDAY)

#: An object representing the dateTime datatype.
DateTimeOWLDatatype: Final = OWLDatatype(XSDVocabulary.DATE_TIME)

#: An object representing the duration datatype.
DurationOWLDatatype: Final = OWLDatatype(XSDVocabulary.DURATION)

#: The OWL Datatype corresponding to the top data type
TopOWLDatatype: Final = OWLDatatype(OWLRDFVocabulary.RDFS_LITERAL)


NUMERIC_DATATYPES: Final[Set[OWLDatatype]] = {FloatOWLDatatype, DoubleOWLDatatype, DecimalOWLDatatype,
                                              IntegerOWLDatatype, PositiveIntegerOWLDatatype,
                                              NegativeIntegerOWLDatatype, NonPositiveIntegerOWLDatatype,
                                              NonNegativeIntegerOWLDatatype}
TIME_DATATYPES: Final[Set[OWLDatatype]] = {DateOWLDatatype, DateTimeOWLDatatype, DurationOWLDatatype}


class FloatSpecialValue(Enum):
    NAN = "Nan"
    POS_INF = "INF"
    NEG_INF = "-INF"

    def __str__(self):
        return self.value


Literals = Union['OWLLiteral', int, float, bool, Timedelta, datetime, date, str, FloatSpecialValue]


class OWLLiteral(OWLAnnotationValue, metaclass=ABCMeta):
    """Literals represent data values such as particular strings or integers. They are analogous to typed RDF
    literals and can also be understood as individuals denoting data values.
    Each literal consists of a lexical form, which is a string, and a datatype.

     (https://www.w3.org/TR/owl2-syntax/#Literals)
     """
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
            elif type_ == FloatOWLDatatype:
                return super().__new__(_OWLLiteralImplFloat)
            elif type_ == DecimalOWLDatatype:
                return super().__new__(_OWLLiteralImplDecimal)
            elif type_ == StringOWLDatatype:
                return super().__new__(_OWLLiteralImplString)
            elif type_ == DateOWLDatatype:
                return super().__new__(_OWLLiteralImplDate)
            elif type_ == DateTimeOWLDatatype:
                return super().__new__(_OWLLiteralImplDateTime)
            elif type_ == DurationOWLDatatype:
                return super().__new__(_OWLLiteralImplDuration)
            elif type_ == PositiveIntegerOWLDatatype:
                return super().__new__(_OWLLiteralImplPositiveInteger)
            elif type_ == NegativeIntegerOWLDatatype:
                return super().__new__(_OWLLiteralImplNegativeInteger)
            elif type_ == NonPositiveIntegerOWLDatatype:
                return super().__new__(_OWLLiteralImplNonPositiveInteger)
            elif type_ == NonNegativeIntegerOWLDatatype:
                return super().__new__(_OWLLiteralImplNonNegativeInteger)
            elif type_ == TimeOWLDatatype:
                return super().__new__(_OWLLiteralImplTime)
            elif type_ == GYearMonthOWLDatatype:
                return super().__new__(_OWLLiteralImplGYearMonth)
            elif type_ == GMonthDayOWLDatatype:
                return super().__new__(_OWLLiteralImplGMonthDay)
            elif type_ == GYearOWLDatatype:
                return super().__new__(_OWLLiteralImplGYear)
            elif type_ == GMonthOWLDatatype:
                return super().__new__(_OWLLiteralImplGMonth)
            elif type_ == GDayOWLDatatype:
                return super().__new__(_OWLLiteralImplGDay)
            else:
                return super().__new__(_OWLLiteralImpl)
        # If datatype not specified, find which literal type fits the value best
        if isinstance(value, bool):
            return super().__new__(_OWLLiteralImplBoolean)
        elif isinstance(value, int):
            # default for integer values is xs:integer
            return super().__new__(_OWLLiteralImplInteger)
        elif isinstance(value, float) or isinstance(value, FloatSpecialValue):
            # default for float values and float special values is xs:double
            return super().__new__(_OWLLiteralImplDouble)
        elif isinstance(value, Decimal):
            return super().__new__(_OWLLiteralImplDecimal)
        elif isinstance(value, str):
            return super().__new__(_OWLLiteralImplString)
        elif isinstance(value, datetime):
            return super().__new__(_OWLLiteralImplDateTime)
        elif isinstance(value, date):
            return super().__new__(_OWLLiteralImplDate)
        elif isinstance(value, Timedelta):
            return super().__new__(_OWLLiteralImplDuration)
        elif isinstance(value, time):
            return super().__new__(_OWLLiteralImplTime)
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
        lexical space of the double datatype ("https://www.w3.org/TR/owl2-syntax/#Floating-Point_Numbers").

        Returns:
            A double value that is represented by this literal.
        """
        raise ValueError

    def is_float(self) -> bool:
        """Whether this literal is typed as float."""
        return False

    def parse_float(self) -> float:
        """Parses the lexical value of this literal into a float. The lexical value of this literal should be in the
        lexical space of the float datatype ("https://www.w3.org/TR/owl2-syntax/#Floating-Point_Numbers").

        Returns:
            A float value that is represented by this literal.
        """
        raise ValueError

    def is_decimal(self) -> bool:
        """Whether this literal is typed as decimal."""
        return False

    def parse_decimal(self) -> Decimal:
        """Parses the lexical value of this literal into a decimal. The lexical value of this literal should be in the
        lexical space of the decimal datatype ("https://www.w3.org/TR/owl2-syntax/#Floating-Point_Numbers").

        Returns:
            A decimal value that is represented by this literal.
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
        return int(self._v)

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

    def is_time(self) -> bool:
        """Whether this literal is typed as time."""
        return False

    def parse_time(self) -> time:
        """Parses the lexical value of this literal into time. The lexical value of this literal should be in the
        lexical space of the time datatype ("http://www.w3.org/2001/XMLSchema#time").

        Returns:
            A time value that is represented by this literal.
        """
        raise ValueError

    def is_gyearmonth(self) -> bool:
        """Whether this literal is typed as gYearMonth."""
        return False

    def parse_gyearmonth(self) -> tuple:
        """Parses the lexical value of this literal into gYearMonth.

        Returns:
            A tuple value of length 2 that is represented by this literal.
        """
        raise ValueError

    def is_gmonthday(self) -> bool:
        """Whether this literal is typed as gMonthDay."""
        return False

    def parse_gmonthday(self) -> tuple:
        """Parses the lexical value of this literal into gMonthDay.

        Returns:
            A tuple value of length 2 that is represented by this literal.
        """
        raise ValueError

    def is_gyear(self) -> bool:
        """Whether this literal is typed as gYear."""
        return False

    def parse_gyear(self) -> tuple:
        """Parses the lexical value of this literal into gYear.

        Returns:
            A integer value that is represented by this literal.
        """
        raise ValueError

    def is_gmonth(self) -> bool:
        """Whether this literal is typed as gMonth."""
        return False

    def parse_gmonth(self) -> tuple:
        """Parses the lexical value of this literal into gMonth.

        Returns:
            A integer value that is represented by this literal.
        """
        raise ValueError

    def is_gday(self) -> bool:
        """Whether this literal is typed as gDay."""
        return False

    def parse_gday(self) -> tuple:
        """Parses the lexical value of this literal into gDay.

        Returns:
            A integer value that is represented by this literal.
        """
        raise ValueError

    def has_float_special_value(self) -> bool:
        """Whether this literal is using a float special value i.e. v ∈ ["NaN", "INF", "-INF"], defined by
        and enumeration class (not pure string value)."""
        return False


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


# ================================================== Numerical ==================================================

@total_ordering
class _OWLNumericLiteralInterface(OWLLiteral):
    __slots__ = '_v', '_type'

    _v: Union[int, float, Decimal, FloatSpecialValue]
    _type: OWLDatatype

    def __init__(self, value, type_=None):
        if isinstance(value, int) or type_ in [IntegerOWLDatatype,
                                               NonNegativeIntegerOWLDatatype,
                                               NonPositiveIntegerOWLDatatype,
                                               NegativeIntegerOWLDatatype,
                                               PositiveIntegerOWLDatatype]:
            value = int(value)
        elif isinstance(value, FloatSpecialValue):
            assert type_ in [DoubleOWLDatatype, FloatOWLDatatype]
        elif isinstance(value, float) or type_ in [DoubleOWLDatatype, FloatOWLDatatype]:
            if type_ == FloatOWLDatatype:
                # single-precision
                value = round(float(value), 7)
            else:
                # double-precision
                value = round(float(value), 15)
        elif isinstance(value, Decimal) or type_ == DecimalOWLDatatype:
            value = Decimal(value)
        else:
            raise TypeError("You either entered an unaccepted value type or an unaccepted datatype.")
        self._v = value
        self._type = type_

    def __eq__(self, other):
        if type(other) is type(self) and not isinstance(self._v, FloatSpecialValue):
            return self._v == other._v
        return NotImplemented

    def __lt__(self, other):
        if type(other) is type(self) and not isinstance(self._v, FloatSpecialValue):
            return self._v < other._v
        return NotImplemented

    def __gt__(self, other):
        if type(other) is type(self) and not isinstance(self._v, FloatSpecialValue):
            return self._v > other._v
        return NotImplemented

    def __le__(self, other):
        if type(other) is type(self) and not isinstance(self._v, FloatSpecialValue):
            return self._v <= other._v
        return NotImplemented

    def __ge__(self, other):
        if type(other) is type(self) and not isinstance(self._v, FloatSpecialValue):
            return self._v >= other._v
        return NotImplemented

    def __ne__(self, other):
        if type(other) is type(self) and not isinstance(self._v, FloatSpecialValue):
            return self._v != other._v
        return NotImplemented

    def __hash__(self):
        return hash((self._v, self._type))

    def __repr__(self):
        return f'OWLLiteral({self._v}, {self._type})'

    # noinspection PyMethodMayBeStatic
    def get_datatype(self) -> OWLDatatype:
        # documented in parent
        return self._type


@total_ordering
class _OWLIntegerLiteralInterface(_OWLNumericLiteralInterface):

    def is_integer(self):
        return True

    def parse_int(self) -> int:
        return self._v


@total_ordering
class _OWLLiteralImplFloat(_OWLNumericLiteralInterface):
    """Represents floating-point numbers with single-precision (7 digits of precision)."""

    def __init__(self, value, type_=FloatOWLDatatype):
        super().__init__(value, type_)

    def is_float(self):
        return True

    def parse_float(self) -> Union[float, FloatSpecialValue]:
        return self._v

    def has_float_special_value(self):
        if isinstance(self._v, FloatSpecialValue):
            return True
        return False


@total_ordering
class _OWLLiteralImplDouble(_OWLNumericLiteralInterface):
    """Represents floating-point numbers with double-precision (15 digits of precision)."""
    def __init__(self, value, type_=DoubleOWLDatatype):
        super().__init__(value, type_)

    def is_double(self):
        return True

    def parse_double(self) -> Union[float, FloatSpecialValue]:
        return self._v

    def has_float_special_value(self):
        if isinstance(self._v, FloatSpecialValue):
            return True
        return False


@total_ordering
class _OWLLiteralImplDecimal(_OWLNumericLiteralInterface):
    """Represents floating-point numbers with arbitrary precision."""

    def __init__(self, value, type_=DecimalOWLDatatype):
        super().__init__(value, type_)

    def is_decimal(self):
        return True

    def parse_decimal(self) -> Decimal:
        return self._v


@total_ordering
class _OWLLiteralImplInteger(_OWLIntegerLiteralInterface):

    def __init__(self, value, type_=IntegerOWLDatatype):
        super().__init__(value, type_)


@total_ordering
class _OWLLiteralImplNonNegativeInteger(_OWLIntegerLiteralInterface):

    def __init__(self, value, type_=NonNegativeIntegerOWLDatatype):
        assert value >= 0, "Negative value used to initialize a literal of type: " + str(type(self))
        super().__init__(value, type_)


@total_ordering
class _OWLLiteralImplNonPositiveInteger(_OWLIntegerLiteralInterface):

    def __init__(self, value, type_=NonPositiveIntegerOWLDatatype):
        assert value <= 0, "Positive value used to initialize a literal of type: " + str(type(self))
        super().__init__(value, type_)


@total_ordering
class _OWLLiteralImplPositiveInteger(_OWLIntegerLiteralInterface):

    def __init__(self, value, type_=PositiveIntegerOWLDatatype):
        assert value <= 0, "Non-Positive value used to initialize a literal of type: " + str(type(self))
        super().__init__(value, type_)


@total_ordering
class _OWLLiteralImplNegativeInteger(_OWLIntegerLiteralInterface):
    def __init__(self, value, type_=NegativeIntegerOWLDatatype):
        assert value <= 0, "Non-Negative value used to initialize a literal of type: " + str(type(self))
        super().__init__(value, type_)


# ================================================== Bool and String ==================================================

class _OWLLiteralImplBoolean(OWLLiteral):
    __slots__ = '_v', '_type'

    _v: bool
    _type: OWLDatatype

    def __init__(self, value, type_=None):
        assert type_ is None or type_ == BooleanOWLDatatype
        if not isinstance(value, bool):
            from distutils.util import strtobool
            value = bool(strtobool(value))
        self._v = value
        self._type = type_

    def get_literal(self) -> str:
        """Gets the lexical value of this literal. Note that the language tag is not included.
        boolean True/False should be true/false in string.
        Returns:
            The lexical value of this literal.
        """
        return str(self._v).lower()

    def __eq__(self, other):
        if type(other) is type(self):
            return self._v == other._v
        return NotImplemented

    def __hash__(self):
        return hash((self._v, self._type))

    def __repr__(self):
        return f'OWLLiteral({self._v, self._type})'

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
    __slots__ = '_v', '_type'

    _v: str
    _type: OWLDatatype

    def __init__(self, value, type_=None):
        assert type_ is None or type_ == StringOWLDatatype
        if not isinstance(value, str):
            value = str(value)
        self._v = value
        self._type = type_

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
        return hash((self._v, self._type))

    def __repr__(self):
        return f'OWLLiteral({self._v}, {self._type})'

    def is_string(self) -> bool:
        return True

    def parse_string(self) -> str:
        # documented in parent
        return self._v

    # noinspection PyMethodMayBeStatic
    def get_datatype(self) -> OWLDatatype:
        # documented in parent
        return StringOWLDatatype

# ================================================== Dates and times ==================================================


class _OWLLiteralBasicsInterface(OWLLiteral):
    __slots__ = '_v', '_type'
    _v: Union[datetime, date, time, Timedelta, tuple, int]
    _type: OWLDatatype

    def __eq__(self, other):
        if type(other) is type(self):
            return self._v == other._v
        return NotImplemented

    def __lt__(self, other):
        if type(other) is type(self):
            return self._v < other._v
        return NotImplemented

    def __gt__(self, other):
        if type(other) is type(self):
            return self._v > other._v
        return NotImplemented

    def __le__(self, other):
        if type(other) is type(self):
            return self._v <= other._v
        return NotImplemented

    def __ge__(self, other):
        if type(other) is type(self):
            return self._v >= other._v
        return NotImplemented

    def __ne__(self, other):
        if type(other) is type(self):
            return self._v != other._v
        return NotImplemented

    def __hash__(self):
        return hash((self._v, self._type))

    def __repr__(self):
        return f'OWLLiteral({self._v}, {self._type})'

    def get_datatype(self) -> OWLDatatype:
        return self._type


@total_ordering
class _OWLDateAndTimeLiteralInterface(_OWLLiteralBasicsInterface):
    __slots__ = '_v', '_type'
    _v: Union[datetime, date, time, Timedelta]
    _type: OWLDatatype

    def __init__(self, value, type_=None):
        if isinstance(value, datetime) or type_ == DateTimeOWLDatatype:
            if isinstance(value, str):
                if value[-1] == "Z":
                    value = value.replace("Z", "+00:00")
                value = datetime.fromisoformat(value)
        if isinstance(value, date) or type_ == DateOWLDatatype:
            if isinstance(value, str):
                if value[-1] == "Z":
                    value = value.replace("Z", "+00:00")
                value = date.fromisoformat(value)
        if isinstance(value, time) or type_ == TimeOWLDatatype:
            if isinstance(value, str):
                if value[-1] == "Z":
                    value = value.replace("Z", "+00:00")
                value = time.fromisoformat(value)
        if isinstance(value, Timedelta) or type_ == DurationOWLDatatype:
            value = Timedelta(value) if isinstance(value, str) else value
        assert type(value) in [datetime, date, time, Timedelta]
        self._v = value
        self._type = type_


@total_ordering
class _OWLLiteralImplDate(_OWLDateAndTimeLiteralInterface):

    def __init__(self, value, type_=DateOWLDatatype):
        super().__init__(value, type_)

    def is_date(self) -> bool:
        return True

    def parse_date(self) -> date:
        return self._v


@total_ordering
class _OWLLiteralImplDateTime(_OWLDateAndTimeLiteralInterface):

    def __init__(self, value, type_=DateTimeOWLDatatype):
        super().__init__(value, type_)

    def is_datetime(self) -> bool:
        return True

    def parse_datetime(self) -> datetime:
        return self._v


@total_ordering
class _OWLLiteralImplDuration(_OWLDateAndTimeLiteralInterface):
    def __init__(self, value, type_=DurationOWLDatatype):
        super().__init__(value, type_)

    def get_literal(self) -> str:
        return self._v.isoformat()

    def is_duration(self) -> bool:
        return True

    def parse_duration(self) -> Timedelta:
        return self._v


@total_ordering
class _OWLLiteralImplTime(_OWLDateAndTimeLiteralInterface):

    def __init__(self, value, type_=TimeOWLDatatype):
        super().__init__(value, type_)

    def is_time(self) -> bool:
        return True

    def parse_time(self) -> datetime:
        return self._v


@total_ordering
class _OWLGDatesInterface(_OWLLiteralBasicsInterface):
    __slots__ = '_v', '_type'
    # represent dual values as tuple of integers and single values as integers
    _v: Union[tuple, int]
    _type: OWLDatatype

    def __init__(self, value, type_=None):

        if isinstance(value, tuple) or type_ in [GYearMonthOWLDatatype, GMonthDayOWLDatatype]:
            if isinstance(value, tuple):
                assert len(value) == 2
            if isinstance(value, str):
                # expected string input examples: "2001-10", "--11-15"
                splits = value.lstrip("-").split("-")
                value = (int(splits[0]), int(splits[1][:2]))
            else:
                raise ValueError("Unsupported value type")
        if isinstance(value, str) and type_ in [GYearOWLDatatype, GMonthOWLDatatype, GDayOWLDatatype]:
            # expected string input examples: "2025", "-2001", "--05", "---01", "---31"
            first_numerical_value = r'^\d+'
            value = int(re.match(first_numerical_value, value.lstrip("-")).group())

        assert type(value) in [tuple, int]
        self._v = value
        self._type = type_


@total_ordering
class _OWLLiteralImplGYearMonth(_OWLGDatesInterface):
    def __init__(self, value, type_=GYearMonthOWLDatatype):
        super().__init__(value, type_)

    def is_gyearmonth(self) -> bool:
        return True

    def parse_gyearmonth(self) -> tuple:
        return self._v


@total_ordering
class _OWLLiteralImplGMonthDay(_OWLGDatesInterface):
    def __init__(self, value, type_=GMonthDayOWLDatatype):
        super().__init__(value, type_)

    def is_gmonthday(self) -> bool:
        return True

    def parse_gmonthday(self) -> tuple:
        return self._v


@total_ordering
class _OWLLiteralImplGYear(_OWLGDatesInterface):
    def __init__(self, value, type_=GYearOWLDatatype):
        super().__init__(value, type_)

    def is_gyear(self) -> bool:
        return True

    def parse_gyear(self) -> int:
        return self._v


@total_ordering
class _OWLLiteralImplGMonth(_OWLGDatesInterface):
    def __init__(self, value, type_=GMonthOWLDatatype):
        super().__init__(value, type_)

    def is_gmonth(self) -> bool:
        return True

    def parse_gmonth(self) -> int:
        return self._v


@total_ordering
class _OWLLiteralImplGDay(_OWLGDatesInterface):
    def __init__(self, value, type_=GDayOWLDatatype):
        super().__init__(value, type_)

    def is_gday(self) -> bool:
        return True

    def parse_gday(self) -> int:
        return self._v


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



