"""OWL Literals"""
from abc import ABCMeta, abstractmethod
from functools import total_ordering
from .owl_annotation import OWLAnnotationValue
from typing import Final, Optional, Union, Set
from .owl_datatype import OWLDatatype
from datetime import datetime, date
from pandas import Timedelta
from owlapy.vocab import OWLRDFVocabulary, XSDVocabulary
from .owl_property import OWLObjectProperty, OWLDataProperty

Literals = Union['OWLLiteral', int, float, bool, Timedelta, datetime, date, str]  #:


class OWLLiteral(OWLAnnotationValue, metaclass=ABCMeta):
    """Literals represent data values such as particular strings or integers. They are analogous to typed RDF
    literals and can also be understood as individuals denoting
    data values. Each literal consists of a lexical form, which is a string, and a datatype.

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

    def get_literal(self) -> str:
        """Gets the lexical value of this literal. Note that the language tag is not included.
        boolean True/False should be true/false in string
        Returns:
            The lexical value of this literal.
        """
        return str(self._v).lower()

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


#: the built in top object property
OWLTopObjectProperty: Final = OWLObjectProperty(OWLRDFVocabulary.OWL_TOP_OBJECT_PROPERTY.iri)
#: the built in bottom object property
OWLBottomObjectProperty: Final = OWLObjectProperty(OWLRDFVocabulary.OWL_BOTTOM_OBJECT_PROPERTY.iri)
#: the built in top data property
OWLTopDataProperty: Final = OWLDataProperty(OWLRDFVocabulary.OWL_TOP_DATA_PROPERTY.iri)
#: the built in bottom data property
OWLBottomDataProperty: Final = OWLDataProperty(OWLRDFVocabulary.OWL_BOTTOM_DATA_PROPERTY.iri)

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
