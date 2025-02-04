"""Enumerations."""
from abc import ABCMeta
from enum import Enum, EnumMeta
from typing import Final, Callable, TypeVar
from operator import lt, le, gt, ge
from re import match

from owlapy import namespaces
from .meta_classes import HasIRI
from .iri import IRI
from owlapy.namespaces import Namespaces


class _Vocabulary(HasIRI):
    __slots__ = '_namespace', '_remainder', '_iri'

    _namespace: Namespaces
    _remainder: str
    _iri: IRI

    def __init__(self, namespace: Namespaces, remainder: str):
        self._namespace = namespace
        self._remainder = remainder
        self._iri = IRI(namespace, remainder)

    @property
    def iri(self) -> IRI:
        return self._iri

    @property
    def str(self) -> str:
        return self._iri.as_str()

    def as_str(self) -> str:
        return self._iri.as_str()

    def __repr__(self):
        return f"<<{self._namespace.prefix}:{self._remainder}>>"


class _meta_Enum(ABCMeta, EnumMeta):
    __slots__ = ()
    pass


class OWLRDFVocabulary(_Vocabulary, Enum, metaclass=_meta_Enum):
    """Enumerations for OWL/RDF vocabulary."""
    def __new__(cls, namespace: Namespaces, remainder: str, *args):
        obj = object.__new__(cls)
        obj._value_ = f"{namespace.prefix}:{remainder}"
        return obj
    OWL_THING = (namespaces.OWL, "Thing")  #:
    OWL_NOTHING = (namespaces.OWL, "Nothing")  #:
    OWL_CLASS = (namespaces.OWL, "Class")  #:
    OWL_NAMED_INDIVIDUAL = (namespaces.OWL, "NamedIndividual")  #:
    OWL_TOP_OBJECT_PROPERTY = (namespaces.OWL, "topObjectProperty")  #:
    OWL_BOTTOM_OBJECT_PROPERTY = (namespaces.OWL, "bottomObjectProperty")  #:
    OWL_TOP_DATA_PROPERTY = (namespaces.OWL, "topDataProperty")  #:
    OWL_BOTTOM_DATA_PROPERTY = (namespaces.OWL, "bottomDataProperty")  #:
    RDFS_LITERAL = (namespaces.RDFS, "Literal")  #:


class XSDVocabulary(_Vocabulary, Enum, metaclass=_meta_Enum):
    """Enumerations for XSD vocabulary."""
    def __new__(cls, remainder: str, *args):
        obj = object.__new__(cls)
        obj._value_ = f"{namespaces.XSD.prefix}:{remainder}"
        return obj

    def __init__(self, remainder: str):
        super().__init__(namespaces.XSD, remainder)
    DECIMAL: Final = "decimal"  #:
    INTEGER: Final = "integer"  #:
    NONNEGATIVEINTEGER: Final = "nonNegativeInteger"  #:
    NONPOSITIVEINTEGER: Final = "nonPositiveInteger"  #:
    POSITIVEINTEGER: Final = "positiveInteger"  #:
    NEGATIVEINTEGER: Final = "negativeInteger"  #:
    LONG: Final = "long"  #:
    DOUBLE: Final = "double"  #:
    FLOAT: Final = "float"  #:
    BOOLEAN: Final = "boolean"  #:
    STRING: Final = "string"  #:
    DATE: Final = "date"  #:
    DATE_TIME: Final = "dateTime"  #:
    DATE_TIME_STAMP: Final = "dateTimeStamp"  #:
    DURATION: Final = "duration"  #:
    TIME: Final = "time"
    GYEARMONTH: Final = "gYearMonth"
    GMONTHDAY: Final = "gMonthDay"
    GYEAR: Final = "gYear"
    GMONTH: Final = "gMonth"
    GDAY: Final = "gDay"



_X = TypeVar('_X')

# TODO: Add langRange facet
class OWLFacet(_Vocabulary, Enum, metaclass=_meta_Enum):
    """Enumerations for OWL facets."""
    def __new__(cls, remainder: str, *args):
        obj = object.__new__(cls)
        obj._value_ = f"{namespaces.XSD.prefix}:{remainder}"
        return obj

    def __init__(self, remainder: str, symbolic_form: str, operator: Callable[[_X, _X], bool]):
        super().__init__(namespaces.XSD, remainder)
        self._symbolic_form = symbolic_form
        self._operator = operator

    @property
    def symbolic_form(self):
        return self._symbolic_form

    @property
    def operator(self):
        return self._operator

    @staticmethod
    def from_str(name: str) -> 'OWLFacet':
        try:
            return next(facet for facet in OWLFacet if name == facet.symbolic_form)
        except StopIteration:
            raise ValueError(f"No facet with symbolic form {name} exists.")

    MIN_INCLUSIVE: Final = ("minInclusive", ">=", ge)  #:
    MIN_EXCLUSIVE: Final = ("minExclusive", ">", gt)  #:
    MAX_INCLUSIVE: Final = ("maxInclusive", "<=", le)  #:
    MAX_EXCLUSIVE: Final = ("maxExclusive", "<", lt)  #:
    LENGTH: Final = ("length", "length", lambda a, b: len(a) == b.parse_integer())  #:
    MIN_LENGTH: Final = ("minLength", "minLength", lambda a, b: len(a) >= b.parse_integer())  #:
    MAX_LENGTH: Final = ("maxLength", "maxLength", lambda a, b: len(a) <= b.parse_integer())  #:
    PATTERN: Final = ("pattern", "pattern", lambda a, b: bool(match(b.parse_string() + "$", a.get_literal())))
    TOTAL_DIGITS: Final = ("totalDigits", "totalDigits",
                           lambda a, b: sum(1 for c in a.get_literal() if c.isdigit()) <= b.parse_integer())
    FRACTION_DIGITS: Final = ("fractionDigits", "fractionDigits",
                              lambda a, b: a.get_literal()[::-1].find('.') <= b.parse_integer())
