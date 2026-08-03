"""Unit tests for owlapy.owl_literal: OWLLiteral's __new__ dispatch, per-datatype
implementations (numeric, boolean, string, date/time, gDate, and the generic fallback),
and the OWLLiteral base-class default behaviour (is_* -> False, parse_* -> ValueError)."""
from datetime import date, datetime, time
from decimal import Decimal

import pytest
from pandas import Timedelta

from owlapy.iri import IRI
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_literal import (
    BooleanOWLDatatype,
    DateOWLDatatype,
    DateTimeOWLDatatype,
    DecimalOWLDatatype,
    DoubleOWLDatatype,
    DurationOWLDatatype,
    FloatOWLDatatype,
    FloatSpecialValue,
    GDayOWLDatatype,
    GMonthDayOWLDatatype,
    GMonthOWLDatatype,
    GYearMonthOWLDatatype,
    GYearOWLDatatype,
    IntegerOWLDatatype,
    IntOWLDatatype,
    NegativeIntegerOWLDatatype,
    NonNegativeIntegerOWLDatatype,
    NonPositiveIntegerOWLDatatype,
    OWLLiteral,
    PositiveIntegerOWLDatatype,
    StringOWLDatatype,
    TimeOWLDatatype,
)

# ---------------------------------------------------------------------------
# FloatSpecialValue
# ---------------------------------------------------------------------------

def test_float_special_value_str():
    assert str(FloatSpecialValue.NAN) == "Nan"
    assert str(FloatSpecialValue.POS_INF) == "INF"
    assert str(FloatSpecialValue.NEG_INF) == "-INF"


# ---------------------------------------------------------------------------
# __new__ dispatch by explicit type_
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("type_,value", [
    (BooleanOWLDatatype, True),
    (IntegerOWLDatatype, 5),
    (IntOWLDatatype, 5),
    (DoubleOWLDatatype, 1.5),
    (FloatOWLDatatype, 1.5),
    (DecimalOWLDatatype, Decimal("1.5")),
    (StringOWLDatatype, "hello"),
    (DateOWLDatatype, date(2020, 1, 1)),
    (DateTimeOWLDatatype, datetime(2020, 1, 1, 12, 0)),
    (DurationOWLDatatype, Timedelta(days=1)),
    (PositiveIntegerOWLDatatype, 1),
    (NegativeIntegerOWLDatatype, -1),
    (NonPositiveIntegerOWLDatatype, 0),
    (NonNegativeIntegerOWLDatatype, 0),
    (TimeOWLDatatype, time(12, 0)),
    (GYearMonthOWLDatatype, "2020-05"),
    (GMonthDayOWLDatatype, "--05-20"),
    (GYearOWLDatatype, 2020),
    (GMonthOWLDatatype, 5),
    (GDayOWLDatatype, 20),
])
def test_new_dispatches_on_explicit_type(type_, value):
    lit = OWLLiteral(value, type_)
    assert lit.get_datatype() == type_


def test_new_dispatches_to_generic_impl_for_unknown_type():
    custom_type = OWLDatatype(IRI.create("http://www.w3.org/2001/XMLSchema#", "anyURI"))
    lit = OWLLiteral("http://example.com", custom_type)
    assert lit.get_datatype() == custom_type


# ---------------------------------------------------------------------------
# __new__ dispatch by value-type inference (no explicit type_)
# ---------------------------------------------------------------------------

def test_new_infers_boolean():
    assert OWLLiteral(True).get_datatype() == BooleanOWLDatatype


def test_new_infers_integer():
    assert OWLLiteral(5).get_datatype() == IntegerOWLDatatype


def test_new_infers_double_from_float():
    assert OWLLiteral(1.5).get_datatype() == DoubleOWLDatatype


def test_new_infers_double_from_float_special_value():
    lit = OWLLiteral(FloatSpecialValue.NAN, DoubleOWLDatatype)
    assert lit.get_datatype() == DoubleOWLDatatype
    assert lit.has_float_special_value()


def test_new_infers_decimal():
    assert OWLLiteral(Decimal("2.5")).get_datatype() == DecimalOWLDatatype


def test_new_infers_string():
    assert OWLLiteral("hi").get_datatype() == StringOWLDatatype


def test_new_infers_datetime():
    assert OWLLiteral(datetime(2020, 1, 1)).get_datatype() == DateTimeOWLDatatype


def test_new_infers_date():
    assert OWLLiteral(date(2020, 1, 1)).get_datatype() == DateOWLDatatype


def test_new_infers_duration():
    assert OWLLiteral(Timedelta(hours=1)).get_datatype() == DurationOWLDatatype


def test_new_infers_time():
    assert OWLLiteral(time(10, 30)).get_datatype() == TimeOWLDatatype


def test_new_raises_not_implemented_for_unsupported_value():
    with pytest.raises(NotImplementedError):
        OWLLiteral([1, 2, 3])


# ---------------------------------------------------------------------------
# Base OWLLiteral default methods: is_* False and parse_* raise ValueError
# when not overridden by the concrete type.
# ---------------------------------------------------------------------------

def test_base_defaults_on_string_literal():
    lit = OWLLiteral("hello")
    assert lit.is_boolean() is False
    assert lit.is_double() is False
    assert lit.is_float() is False
    assert lit.is_decimal() is False
    assert lit.is_date() is False
    assert lit.is_datetime() is False
    assert lit.is_duration() is False
    assert lit.is_time() is False
    assert lit.is_gyearmonth() is False
    assert lit.is_gmonthday() is False
    assert lit.is_gyear() is False
    assert lit.is_gmonth() is False
    assert lit.is_gday() is False
    assert lit.has_float_special_value() is False
    assert lit.is_literal() is True
    assert lit.as_literal() is lit
    assert lit.to_python() == "hello"

    with pytest.raises(ValueError):
        lit.parse_boolean()
    with pytest.raises(ValueError):
        lit.parse_double()
    with pytest.raises(ValueError):
        lit.parse_float()
    with pytest.raises(ValueError):
        lit.parse_decimal()
    with pytest.raises(ValueError):
        lit.parse_date()
    with pytest.raises(ValueError):
        lit.parse_datetime()
    with pytest.raises(ValueError):
        lit.parse_duration()
    with pytest.raises(ValueError):
        lit.parse_time()
    with pytest.raises(ValueError):
        lit.parse_gyearmonth()
    with pytest.raises(ValueError):
        lit.parse_gmonthday()
    with pytest.raises(ValueError):
        lit.parse_gyear()
    with pytest.raises(ValueError):
        lit.parse_gmonth()
    with pytest.raises(ValueError):
        lit.parse_gday()


def test_base_default_get_literal_uses_str():
    lit = OWLLiteral(2020, GYearOWLDatatype)
    assert lit.get_literal() == "2020"


def test_base_default_parse_integer_on_non_integer_literal():
    # parse_integer() is NOT abstract/raising -- it's implemented on the base class via int(self._v).
    lit = OWLLiteral("42")
    assert lit.parse_integer() == 42


# ---------------------------------------------------------------------------
# Numeric literals: integer family
# ---------------------------------------------------------------------------

def test_integer_literal_basic():
    lit = OWLLiteral(7)
    assert lit.is_integer()
    assert lit.parse_int() == 7
    assert lit.get_literal() == "7"
    assert lit.get_datatype() == IntegerOWLDatatype
    assert repr(lit) == f"OWLLiteral(7, {IntegerOWLDatatype})"
    assert hash(lit) == hash(OWLLiteral(7))
    assert lit == OWLLiteral(7)
    assert lit != OWLLiteral(8)
    assert lit != "not a literal"


def test_integer_literal_ordering():
    a, b = OWLLiteral(1), OWLLiteral(2)
    assert a < b
    assert b > a
    assert a <= a
    assert b >= b
    # Comparing against a different concrete type returns False (not an exception).
    assert (a < OWLLiteral(1.5)) is False
    assert (a > OWLLiteral(1.5)) is False
    assert (a <= OWLLiteral(1.5)) is False
    assert (a >= OWLLiteral(1.5)) is False


def test_positive_negative_nonpositive_nonnegative_integers():
    assert OWLLiteral(1, PositiveIntegerOWLDatatype).parse_int() == 1
    assert OWLLiteral(-1, NegativeIntegerOWLDatatype).parse_int() == -1
    assert OWLLiteral(0, NonPositiveIntegerOWLDatatype).parse_int() == 0
    assert OWLLiteral(0, NonNegativeIntegerOWLDatatype).parse_int() == 0


def test_positive_integer_rejects_non_positive_value():
    with pytest.raises(AssertionError):
        OWLLiteral(0, PositiveIntegerOWLDatatype)


def test_negative_integer_rejects_non_negative_value():
    with pytest.raises(AssertionError):
        OWLLiteral(0, NegativeIntegerOWLDatatype)


def test_non_positive_integer_rejects_positive_value():
    with pytest.raises(AssertionError):
        OWLLiteral(1, NonPositiveIntegerOWLDatatype)


def test_non_negative_integer_rejects_negative_value():
    with pytest.raises(AssertionError):
        OWLLiteral(-1, NonNegativeIntegerOWLDatatype)


# ---------------------------------------------------------------------------
# Numeric literals: float/double/decimal
# ---------------------------------------------------------------------------

def test_float_literal_rounds_to_seven_digits():
    lit = OWLLiteral(1.123456789, FloatOWLDatatype)
    assert lit.is_float()
    assert lit.parse_float() == round(1.123456789, 7)
    assert lit.has_float_special_value() is False


def test_double_literal_rounds_to_fifteen_digits():
    lit = OWLLiteral(1.123456789012345678, DoubleOWLDatatype)
    assert lit.is_double()
    assert lit.parse_double() == round(1.123456789012345678, 15)
    assert lit.has_float_special_value() is False


def test_float_and_double_with_special_value():
    float_lit = OWLLiteral(FloatSpecialValue.POS_INF, FloatOWLDatatype)
    assert float_lit.has_float_special_value()
    assert float_lit.parse_float() == FloatSpecialValue.POS_INF

    double_lit = OWLLiteral(FloatSpecialValue.NEG_INF, DoubleOWLDatatype)
    assert double_lit.has_float_special_value()


def test_float_special_value_comparisons_return_false():
    lit = OWLLiteral(FloatSpecialValue.NAN, DoubleOWLDatatype)
    other = OWLLiteral(FloatSpecialValue.NAN, DoubleOWLDatatype)
    assert (lit == other) is False
    assert (lit < other) is False
    assert (lit > other) is False
    assert (lit <= other) is False
    assert (lit >= other) is False


def test_decimal_literal():
    lit = OWLLiteral(Decimal("3.14"))
    assert lit.is_decimal()
    assert lit.parse_decimal() == Decimal("3.14")
    assert lit.get_datatype() == DecimalOWLDatatype




# ---------------------------------------------------------------------------
# Boolean literal
# ---------------------------------------------------------------------------

def test_boolean_literal_from_bool():
    lit = OWLLiteral(True)
    assert lit.is_boolean()
    assert lit.parse_boolean() is True
    assert lit.get_literal() == "true"
    assert lit.get_datatype() == BooleanOWLDatatype
    assert lit == OWLLiteral(True)
    assert lit != OWLLiteral(False)
    assert lit != "not a literal"
    assert hash(lit) == hash(OWLLiteral(True))
    assert "OWLLiteral" in repr(lit)


def test_boolean_literal_from_string():
    lit = OWLLiteral("true", BooleanOWLDatatype)
    assert lit.parse_boolean() is True
    lit_false = OWLLiteral("false", BooleanOWLDatatype)
    assert lit_false.parse_boolean() is False


# ---------------------------------------------------------------------------
# String literal
# ---------------------------------------------------------------------------

def test_string_literal_from_non_str_value():
    lit = OWLLiteral(42, StringOWLDatatype)
    assert lit.is_string()
    assert lit.parse_string() == "42"
    assert len(lit) == 2
    assert lit.get_datatype() == StringOWLDatatype


def test_string_literal_ordering_and_equality():
    a, b = OWLLiteral("abc"), OWLLiteral("abd")
    assert a < b
    assert (a < OWLLiteral(1)) is False
    assert a == OWLLiteral("abc")
    assert a != OWLLiteral("xyz")
    assert a != 123
    assert hash(a) == hash(OWLLiteral("abc"))
    assert "abc" in repr(a)


# ---------------------------------------------------------------------------
# Date / DateTime / Time / Duration literals
# ---------------------------------------------------------------------------

def test_date_literal_from_object_and_iso_string():
    lit = OWLLiteral(date(2020, 5, 17))
    assert lit.is_date()
    assert lit.parse_date() == date(2020, 5, 17)

    lit_from_str = OWLLiteral("2020-05-17", DateOWLDatatype)
    assert lit_from_str.parse_date() == date(2020, 5, 17)


def test_datetime_literal_from_object_and_zulu_string():
    lit = OWLLiteral(datetime(2020, 5, 17, 10, 30))
    assert lit.is_datetime()
    assert lit.parse_datetime() == datetime(2020, 5, 17, 10, 30)

    lit_from_str = OWLLiteral("2020-05-17T10:30:00Z", DateTimeOWLDatatype)
    assert lit_from_str.is_datetime()


def test_time_literal_from_object_and_zulu_string():
    lit = OWLLiteral(time(10, 30))
    assert lit.is_time()
    assert lit.parse_time() == time(10, 30)

    lit_from_str = OWLLiteral("10:30:00Z", TimeOWLDatatype)
    assert lit_from_str.is_time()


def test_duration_literal():
    lit = OWLLiteral(Timedelta(days=1, hours=2))
    assert lit.is_duration()
    assert lit.parse_duration() == Timedelta(days=1, hours=2)
    assert lit.get_literal() == Timedelta(days=1, hours=2).isoformat()

    lit_from_str = OWLLiteral("P1DT2H", DurationOWLDatatype)
    assert lit_from_str.is_duration()


def test_date_and_time_literal_equality_hash_repr():
    a = OWLLiteral(date(2020, 1, 1))
    b = OWLLiteral(date(2020, 1, 1))
    c = OWLLiteral(date(2021, 1, 1))
    assert a == b
    assert a != c
    assert a != "not a literal"
    assert hash(a) == hash(b)
    assert "OWLLiteral" in repr(a)


def test_date_and_time_literal_ordering():
    a = OWLLiteral(date(2020, 1, 1))
    b = OWLLiteral(date(2021, 1, 1))
    assert a < b
    assert b > a
    assert a <= b
    assert b >= a


def test_date_and_time_literal_rejects_invalid_combination():
    # type_=DateOWLDatatype forces dispatch into _OWLLiteralImplDate, but an int value
    # matches none of the str/date-conversion branches, so it falls through to the
    # final `assert type(value) in [datetime, date, time, Timedelta]`.
    with pytest.raises(AssertionError):
        OWLLiteral(123, DateOWLDatatype)


# ---------------------------------------------------------------------------
# gDate literals: GYearMonth / GMonthDay (tuple-valued), GYear / GMonth / GDay (int-valued)
# ---------------------------------------------------------------------------

def test_gyearmonth_from_string():
    lit = OWLLiteral("2020-05", GYearMonthOWLDatatype)
    assert lit.is_gyearmonth()
    assert lit.parse_gyearmonth() == (2020, 5)


def test_gyearmonth_accepts_tuple_value_directly():
    lit = OWLLiteral((2020, 5), GYearMonthOWLDatatype)
    assert lit.is_gyearmonth()
    assert lit.parse_gyearmonth() == (2020, 5)


def test_gmonthday_from_string():
    lit_from_str = OWLLiteral("--05-20", GMonthDayOWLDatatype)
    assert lit_from_str.is_gmonthday()
    assert lit_from_str.parse_gmonthday() == (5, 20)


def test_gmonthday_accepts_tuple_value_directly():
    lit = OWLLiteral((5, 20), GMonthDayOWLDatatype)
    assert lit.is_gmonthday()
    assert lit.parse_gmonthday() == (5, 20)


def test_gyear_gmonth_gday_from_int_and_string():
    assert OWLLiteral(2020, GYearOWLDatatype).parse_gyear() == 2020
    assert OWLLiteral("2020", GYearOWLDatatype).parse_gyear() == 2020
    assert OWLLiteral("-44", GYearOWLDatatype).parse_gyear() == 44

    assert OWLLiteral(5, GMonthOWLDatatype).parse_gmonth() == 5
    assert OWLLiteral("--05", GMonthOWLDatatype).parse_gmonth() == 5

    assert OWLLiteral(20, GDayOWLDatatype).parse_gday() == 20
    assert OWLLiteral("---20", GDayOWLDatatype).parse_gday() == 20


def test_gdate_rejects_non_string_non_tuple_for_dual_types():
    with pytest.raises(ValueError):
        OWLLiteral(123, GYearMonthOWLDatatype)


def test_gdate_equality_hash_repr():
    a = OWLLiteral(2020, GYearOWLDatatype)
    b = OWLLiteral(2020, GYearOWLDatatype)
    c = OWLLiteral(2021, GYearOWLDatatype)
    assert a == b
    assert a != c
    assert hash(a) == hash(b)
    assert "OWLLiteral" in repr(a)


# ---------------------------------------------------------------------------
# Generic fallback literal (_OWLLiteralImpl) for datatypes with no dedicated class
# ---------------------------------------------------------------------------

def test_generic_literal_impl_for_custom_datatype():
    custom_type = OWLDatatype(IRI.create("http://example.com/", "myCustomType"))
    lit = OWLLiteral("http://example.com/thing", custom_type)
    assert lit.get_datatype() == custom_type
    assert lit == OWLLiteral("http://example.com/thing", custom_type)
    assert lit != OWLLiteral("http://example.com/other", custom_type)
    assert hash(lit) == hash(OWLLiteral("http://example.com/thing", custom_type))
    assert "OWLLiteral" in repr(lit)


def test_generic_literal_impl_requires_owl_datatype():
    with pytest.raises(AssertionError):
        from owlapy.owl_literal import _OWLLiteralImpl
        _OWLLiteralImpl("value", "not a datatype")
