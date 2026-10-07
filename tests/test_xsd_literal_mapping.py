"""Datatype fidelity of literals crossing the owlapy <-> OWLAPI boundary (#292).

General guarantee under test: a literal read from a file keeps its datatype and lexical value, and a literal written
from Python and read back is equal to the original -- for every XSD datatype, not just the numeric ones.
"""
from datetime import date, datetime, time
from decimal import Decimal

import pytest

from owlapy import namespaces
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLDataPropertyAssertionAxiom
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import (BooleanOWLDatatype, DateOWLDatatype, DateTimeOWLDatatype, DecimalOWLDatatype,
                                DoubleOWLDatatype, FloatOWLDatatype, IntegerOWLDatatype, IntOWLDatatype,
                                LongOWLDatatype, NegativeIntegerOWLDatatype, NonNegativeIntegerOWLDatatype,
                                NonPositiveIntegerOWLDatatype, OWLLiteral, PositiveIntegerOWLDatatype,
                                StringOWLDatatype, TimeOWLDatatype, lexical_literal)
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_property import OWLDataProperty

NS = "http://example.org/e#"
PROP = OWLDataProperty(IRI.create(NS, "p"))
IND = OWLNamedIndividual(IRI.create(NS, "a"))


def xsd(name: str) -> OWLDatatype:
    return OWLDatatype(IRI(namespaces.XSD, name))


# (xsd local name, lexical form in the file, expected python value or None when only the lexical form is kept)
TYPED_CASES = [
    ("string", "x", "x"),
    ("boolean", "true", True),
    ("decimal", "1.5", Decimal("1.5")),
    ("float", "3.0", 3.0),
    ("double", "2.5", 2.5),
    ("integer", "9", 9),
    ("int", "7", 7),
    ("long", "8", 8),
    ("short", "10", 10),
    ("byte", "-3", -3),
    ("nonNegativeInteger", "1", 1),
    ("nonPositiveInteger", "-1", -1),
    ("positiveInteger", "1", 1),
    ("negativeInteger", "-1", -1),
    ("unsignedLong", "1", 1),
    ("unsignedInt", "1", 1),
    ("unsignedShort", "1", 1),
    ("unsignedByte", "1", 1),
    ("date", "2020-01-02", date(2020, 1, 2)),
    ("dateTime", "2020-01-02T10:11:12", datetime(2020, 1, 2, 10, 11, 12)),
    ("time", "10:11:12", time(10, 11, 12)),
    ("dateTimeStamp", "2020-01-02T10:11:12Z", None),
    ("duration", "P1Y2M", None),
    ("gYear", "2020", None),
    ("gYearMonth", "2020-01", None),
    ("gMonth", "--01", None),
    ("gMonthDay", "--01-02", None),
    ("gDay", "---02", None),
    ("hexBinary", "0F", None),
    ("base64Binary", "AAA=", None),
    ("anyURI", "http://a.b/c", None),
    ("normalizedString", "x", None),
    ("token", "x", None),
    ("language", "en", None),
    ("NMTOKEN", "x", None),
    ("Name", "x", None),
    ("NCName", "x", None),
]


def _load(tmp_path, body: str) -> SyncOntology:
    path = tmp_path / "o.ttl"
    path.write_text(
        f"@prefix : <{NS}> .\n@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
        f":p a owl:DatatypeProperty .\n:a a owl:NamedIndividual ; :p {body} .\n")
    return SyncOntology(str(path), load=True)


def _literals(onto: SyncOntology):
    return [ax.get_object() for ax in onto.get_axioms(False) if isinstance(ax, OWLDataPropertyAssertionAxiom)]


def _lexical(lit: OWLLiteral) -> str:
    if lit.is_datetime():
        return lit.parse_datetime().isoformat()
    if lit.is_date():
        return lit.parse_date().isoformat()
    if lit.is_time():
        return lit.parse_time().isoformat()
    if lit.is_boolean():
        return "true" if lit.parse_boolean() else "false"
    return lit.get_literal()


@pytest.mark.parametrize("name,lexical,expected", TYPED_CASES, ids=[c[0] for c in TYPED_CASES])
def test_read_keeps_datatype(tmp_path, name, lexical, expected):
    [lit] = _literals(_load(tmp_path, f'"{lexical}"^^xsd:{name}'))
    assert lit.get_datatype() == xsd(name)
    if expected is not None:
        parsed = {bool: "parse_boolean", int: "parse_integer", float: "parse_double", Decimal: "parse_decimal",
                  str: "get_literal", date: "parse_date", datetime: "parse_datetime", time: "parse_time"}
        # bool is an int subclass, so look the accessor up by exact type; xsd:float has its own accessor
        accessor = "parse_float" if name == "float" else parsed[type(expected)]
        assert getattr(lit, accessor)() == expected
    else:
        assert lit.get_literal() == lexical


def test_read_all_types_in_one_ontology(tmp_path):
    body = ", ".join(f'"{lex}"^^xsd:{name}' for name, lex, _ in TYPED_CASES)
    found = sorted(l.get_datatype().str for l in _literals(_load(tmp_path, body)))
    assert found == sorted(xsd(name).str for name, _, _ in TYPED_CASES)


def test_read_custom_datatype_is_kept(tmp_path):
    [lit] = _literals(_load(tmp_path, '"x"^^<http://example.org/custom>'))
    assert lit.get_datatype() == OWLDatatype(IRI.create("http://example.org/custom"))
    assert lit.get_literal() == "x"


@pytest.mark.parametrize("body", ['"hello"@en', '"plain"'])
def test_read_plain_and_language_tagged_literals(tmp_path, body):
    """Used to raise ``RuntimeError: Inconsistent hierarchy`` (unmapped OWLLiteralImplPlain)."""
    [lit] = _literals(_load(tmp_path, body))
    assert lit.get_literal() == body.split("@")[0].strip('"')


def test_float_and_double_stay_distinct(tmp_path):
    """The reported bug: an xsd:float value must not be read as xsd:double."""
    found = {l.get_datatype(): l for l in _literals(_load(tmp_path, '"3.0"^^xsd:float, "3.0"^^xsd:double'))}
    assert set(found) == {FloatOWLDatatype, DoubleOWLDatatype}


ROUND_TRIP = [
    OWLLiteral("x"), OWLLiteral(True), OWLLiteral(False), OWLLiteral(5), OWLLiteral(2.5),
    OWLLiteral(1.5, type_=FloatOWLDatatype), OWLLiteral(Decimal("1.25"), type_=DecimalOWLDatatype),
    OWLLiteral(7, type_=IntOWLDatatype), OWLLiteral(8, type_=LongOWLDatatype),
    OWLLiteral(1, type_=PositiveIntegerOWLDatatype), OWLLiteral(-1, type_=NegativeIntegerOWLDatatype),
    OWLLiteral(0, type_=NonNegativeIntegerOWLDatatype), OWLLiteral(0, type_=NonPositiveIntegerOWLDatatype),
    OWLLiteral(date(2020, 1, 2)), OWLLiteral(datetime(2020, 1, 2, 10, 11, 12)), OWLLiteral(time(10, 11, 12)),
    lexical_literal("P1Y2M", xsd("duration")), lexical_literal("2020", xsd("gYear")),
    lexical_literal("--01-02", xsd("gMonthDay")), lexical_literal("0F", xsd("hexBinary")),
    lexical_literal("http://a.b/c", xsd("anyURI")), lexical_literal("10", xsd("short")),
    lexical_literal("1", xsd("unsignedInt")), lexical_literal("x", OWLDatatype(IRI.create("http://example.org/custom"))),
]


@pytest.mark.parametrize("literal", ROUND_TRIP, ids=lambda l: f"{l.get_datatype().iri.get_remainder()}={l.get_literal()}")
def test_write_then_read_back_is_identical(tmp_path, literal):
    onto = SyncOntology(NS[:-1], load=False)
    onto.add_axiom(OWLDataPropertyAssertionAxiom(IND, PROP, literal))
    path = str(tmp_path / "out.owl")
    onto.save(path=path)
    [back] = _literals(SyncOntology(path, load=True))
    assert back.get_datatype() == literal.get_datatype()
    assert _lexical(back) == _lexical(literal)


def test_mapper_roundtrip_without_file():
    from owlapy.owlapi_mapper import OWLAPIMapper
    onto = SyncOntology(NS[:-1], load=False)
    mapper = onto.mapper if hasattr(onto, "mapper") else OWLAPIMapper(onto)
    for literal in ROUND_TRIP:
        back = mapper.map_(mapper.map_(literal))
        assert back.get_datatype() == literal.get_datatype(), literal
        assert _lexical(back) == _lexical(literal), literal


def test_default_literal_types_unchanged():
    assert OWLLiteral("s").get_datatype() == StringOWLDatatype
    assert OWLLiteral(True).get_datatype() == BooleanOWLDatatype
    assert OWLLiteral(1).get_datatype() == IntegerOWLDatatype
    assert OWLLiteral(1.0).get_datatype() == DoubleOWLDatatype
    assert OWLLiteral(date(2020, 1, 2)).get_datatype() == DateOWLDatatype
    assert OWLLiteral(datetime(2020, 1, 2)).get_datatype() == DateTimeOWLDatatype
    assert OWLLiteral(time(1, 2)).get_datatype() == TimeOWLDatatype
