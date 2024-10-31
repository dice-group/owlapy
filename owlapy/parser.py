"""String to OWL parsers."""
from types import MappingProxyType
from typing import Final, List, Optional, Union
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from parsimonious.nodes import Node
from .iri import IRI
from .owl_individual import OWLNamedIndividual
from .owl_literal import IntegerOWLDatatype, BooleanOWLDatatype, DoubleOWLDatatype, StringOWLDatatype, DateOWLDatatype, \
    DateTimeOWLDatatype, DurationOWLDatatype, OWLLiteral
from .owl_property import OWLObjectPropertyExpression, OWLObjectProperty, OWLDataProperty
from .owl_object import OWLObjectParser
from .namespaces import Namespaces
from .render import _DL_SYNTAX, _MAN_SYNTAX
from .owl_datatype import OWLDatatype
from .vocab import OWLFacet, OWLRDFVocabulary
from owlapy.class_expression import OWLObjectHasSelf, OWLObjectIntersectionOf, OWLObjectMinCardinality, \
    OWLObjectSomeValuesFrom, OWLObjectUnionOf, OWLClass, OWLObjectOneOf, \
    OWLClassExpression, OWLObjectComplementOf, OWLObjectExactCardinality, \
    OWLQuantifiedDataRestriction, OWLQuantifiedObjectRestriction,  OWLFacetRestriction, \
    OWLDataSomeValuesFrom, OWLDataExactCardinality, OWLObjectHasValue, \
    OWLDataMaxCardinality, OWLObjectMaxCardinality, OWLDataMinCardinality, OWLDataHasValue, \
    OWLDataOneOf, OWLObjectCardinalityRestriction, OWLDatatypeRestriction, \
    OWLDataCardinalityRestriction, OWLObjectAllValuesFrom, OWLDataAllValuesFrom
from owlapy.owl_data_ranges import OWLDataIntersectionOf, OWLDataUnionOf, OWLDataComplementOf, OWLDataRange


MANCHESTER_GRAMMAR = Grammar(r"""
    union = intersection (must_ws "or" must_ws intersection)*
    intersection = primary (must_ws "and" must_ws primary)*

    # Main entry point + object properties
    primary = ("not" must_ws)? (data_some_only_res / some_only_res / data_cardinality_res / cardinality_res
                           / data_value_res / value_res / has_self / class_expression)
    some_only_res = object_property must_ws ("some"/"only") must_ws primary
    cardinality_res = object_property must_ws ("max"/"min"/"exactly") must_ws non_negative_integer must_ws primary
    value_res = object_property must_ws "value" must_ws individual_iri
    has_self = object_property must_ws "Self"
    object_property = ("inverse" must_ws)? object_property_iri
    class_expression = class_iri / individual_list / parentheses
    individual_list = "{" maybe_ws individual_iri (maybe_ws "," maybe_ws individual_iri)* maybe_ws "}"

    # Back to start symbol (first production rule)
    parentheses = "(" maybe_ws union maybe_ws ")"

    # Data properties
    data_some_only_res = data_property_iri must_ws ("some"/"only") must_ws data_primary
    data_cardinality_res = data_property_iri must_ws ("max"/"min"/"exactly")
                           must_ws non_negative_integer must_ws data_primary
    data_value_res = data_property_iri must_ws "value" must_ws literal
    data_primary = ("not" must_ws)? data_range
    data_range = datatype_restriction / datatype_iri / literal_list / data_parentheses
    literal_list = "{" maybe_ws literal (maybe_ws "," maybe_ws literal)* maybe_ws "}"
    data_parentheses = "(" maybe_ws data_union maybe_ws ")"
    data_union = data_intersection (must_ws "or" must_ws data_intersection)*
    data_intersection = data_primary (must_ws "and" must_ws data_primary)*
    datatype_restriction = datatype_iri "[" maybe_ws facet_restrictions maybe_ws "]"
    facet_restrictions = facet_restriction (maybe_ws "⊓" maybe_ws facet_restriction)*
    facet_restriction = facet must_ws literal
    facet = "length" / "minLength" / "maxLength" / "pattern" / "langRange"
            / "totalDigits" / "fractionDigits" / "<=" / ">=" / "<" / ">"
    datatype_iri = ("<http://www.w3.org/2001/XMLSchema#" datatype ">") / ("xsd:"? datatype)
    datatype = "double" / "integer" / "boolean" / "string" / "dateTime" / "date" / "duration"

    # Literals
    literal = typed_literal / string_literal_language / string_literal_no_language / datetime_literal /
              duration_literal / date_literal / float_literal / decimal_literal / integer_literal /
              boolean_literal
    typed_literal = quoted_string "^^" datatype_iri
    string_literal_language = quoted_string language_tag
    string_literal_no_language = quoted_string / no_match
    quoted_string = ~"\"([^\"\\\\]|\\\\[\"\\\\])*\""
    language_tag = "@" ~"[a-zA-Z]+" ("-" ~"[a-zA-Z0-9]+")*
    float_literal = sign (float_with_integer_part / float_no_integer_part) ("f"/"F")
    float_with_integer_part = non_negative_integer ("." ~"[0-9]+")? exponent?
    float_no_integer_part = "." ~"[0-9]+" exponent?
    exponent = ("e"/"E") sign ~"[0-9]+"
    decimal_literal = sign non_negative_integer "." ~"[0-9]+"
    integer_literal = sign non_negative_integer
    boolean_literal = ~"[tT]rue" / ~"[fF]alse"
    date_literal = ~"[0-9]{4}-((0[1-9])|(1[0-2]))-(([0-2][0-9])|(3[01]))"
    datetime_literal = ~"[0-9]{4}-((0[1-9])|(1[0-2]))-(([0-2][0-9])|(3[01]))[T\u0020]"
                       ~"(([0-1][0-9])|(2[0-3])):[0-5][0-9]:[0-5][0-9](\\.[0-9]{6})?"
                       ~"(Z|([+-](([0-1][0-9])|(2[0-3])):[0-5][0-9](:[0-5][0-9](\\.[0-9]{6})?)?))?"
    duration_literal = ~"P([0-9]+W)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+(\\.[0-9]{6})?S)?)?"
    sign = ("+"/"-")?
    non_negative_integer = ~"0|([1-9][0-9]*)"

    # IRIs / Characters
    class_iri = iri / no_match
    individual_iri = iri / no_match
    object_property_iri = iri / no_match
    data_property_iri = iri / no_match
    iri = full_iri / abbreviated_iri / simple_iri
    full_iri = iri_ref / no_match
    abbreviated_iri = pname_ln / no_match
    simple_iri = pn_local / no_match

    iri_ref = "<" ~"[^<>\"{}|^`\\\\\u0000-\u0020]*" ">"
    pname_ln = pname_ns pn_local
    pname_ns = pn_prefix? ":"
    pn_prefix = pn_chars_base ("."* pn_chars)*
    pn_local = (pn_chars_u / ~"[0-9]") ("."* pn_chars)*
    pn_chars = pn_chars_u / "-" / ~"[0-9]" / ~"\u00B7" / ~"[\u0300-\u036F]" / ~"[\u203F-\u2040]"
    pn_chars_u = pn_chars_base / "_"
    pn_chars_base = ~"[a-zA-Z]" / ~"[\u00C0-\u00D6]" / ~"[\u00D8-\u00F6]" / ~"[\u00F8-\u02FF]" /
                    ~"[\u0370-\u037D]" / ~"[\u037F-\u1FFF]" / ~"[\u200C-\u200D]" / ~"[\u2070-\u218F]" /
                    ~"[\u2C00-\u2FEF]" / ~"[\u3001-\uD7FF]" / ~"[\uF900-\uFDCF]" / ~"[\uFDF0-\uFFFD]" /
                    ~"[\U00010000-\U000EFFFF]"

    must_ws = ~"[\u0020\u000D\u0009\u000A]+"
    maybe_ws = ~"[\u0020\u000D\u0009\u000A]*"

    # hacky workaround: can be added to a pass through production rule that is semantically important
    # so nodes are not combined which makes the parsing cleaner
    no_match = ~"(?!a)a"
    """)


def _transform_children(nary_visit_function):
    def transform(self, node, visited_children):
        if len(visited_children) > 2:
            *_, first_operand, operands, _, _ = visited_children
        else:
            first_operand, operands = visited_children
        children = first_operand if isinstance(operands, Node) else [first_operand] + [node[-1] for node in operands]
        return nary_visit_function(self, node, children)
    return transform


def _node_text(node) -> str:
    return node.text.strip()


_STRING_TO_DATATYPE: Final = MappingProxyType({
    "integer": IntegerOWLDatatype,
    "double": DoubleOWLDatatype,
    "boolean": BooleanOWLDatatype,
    "string": StringOWLDatatype,
    "date": DateOWLDatatype,
    "dateTime": DateTimeOWLDatatype,
    "duration": DurationOWLDatatype,
})


_DATATYPE_TO_FACETS: Final = MappingProxyType({
    IntegerOWLDatatype: {OWLFacet.MIN_INCLUSIVE, OWLFacet.MIN_EXCLUSIVE, OWLFacet.MAX_EXCLUSIVE,
                         OWLFacet.MAX_INCLUSIVE, OWLFacet.TOTAL_DIGITS},
    DoubleOWLDatatype: {OWLFacet.MIN_INCLUSIVE, OWLFacet.MIN_EXCLUSIVE, OWLFacet.MAX_EXCLUSIVE, OWLFacet.MAX_INCLUSIVE},
    DateOWLDatatype: {OWLFacet.MIN_INCLUSIVE, OWLFacet.MIN_EXCLUSIVE, OWLFacet.MAX_EXCLUSIVE, OWLFacet.MAX_INCLUSIVE},
    DateTimeOWLDatatype: {OWLFacet.MIN_INCLUSIVE, OWLFacet.MIN_EXCLUSIVE,
                          OWLFacet.MAX_EXCLUSIVE, OWLFacet.MAX_INCLUSIVE},
    DurationOWLDatatype: {OWLFacet.MIN_INCLUSIVE, OWLFacet.MIN_EXCLUSIVE,
                          OWLFacet.MAX_EXCLUSIVE, OWLFacet.MAX_INCLUSIVE},
    StringOWLDatatype: {OWLFacet.LENGTH, OWLFacet.MIN_LENGTH, OWLFacet.MAX_LENGTH, OWLFacet.PATTERN},
    BooleanOWLDatatype: {}
})


_FACET_TO_LITERAL_DATATYPE: Final = MappingProxyType({
    OWLFacet.MIN_EXCLUSIVE: {IntegerOWLDatatype, DoubleOWLDatatype, DateOWLDatatype,
                             DateTimeOWLDatatype, DurationOWLDatatype},
    OWLFacet.MAX_EXCLUSIVE: {IntegerOWLDatatype, DoubleOWLDatatype, DateOWLDatatype,
                             DateTimeOWLDatatype, DurationOWLDatatype},
    OWLFacet.MIN_INCLUSIVE: {IntegerOWLDatatype, DoubleOWLDatatype, DateOWLDatatype,
                             DateTimeOWLDatatype, DurationOWLDatatype},
    OWLFacet.MAX_INCLUSIVE: {IntegerOWLDatatype, DoubleOWLDatatype, DateOWLDatatype,
                             DateTimeOWLDatatype, DurationOWLDatatype},
    OWLFacet.PATTERN: {IntegerOWLDatatype, DoubleOWLDatatype, DateOWLDatatype, DateTimeOWLDatatype,
                       DurationOWLDatatype, StringOWLDatatype},
    OWLFacet.LENGTH: {IntegerOWLDatatype},
    OWLFacet.MIN_LENGTH: {IntegerOWLDatatype},
    OWLFacet.MAX_LENGTH: {IntegerOWLDatatype},
    OWLFacet.TOTAL_DIGITS: {IntegerOWLDatatype},
    OWLFacet.FRACTION_DIGITS: {IntegerOWLDatatype}
})


# workaround to support multiple inheritance with different metaclasses
class _ManchesterOWLSyntaxParserMeta(type(NodeVisitor), type(OWLObjectParser)):
    pass


class ManchesterOWLSyntaxParser(NodeVisitor, OWLObjectParser, metaclass=_ManchesterOWLSyntaxParserMeta):
    """Manchester Syntax parser to parse strings to OWLClassExpressions.
       Following: https://www.w3.org/TR/owl2-manchester-syntax."""

    slots = 'ns', 'grammar'

    ns: Optional[Union[str, Namespaces]]

    def __init__(self, namespace: Optional[Union[str, Namespaces]] = None, grammar=None):
        """Create a new Manchester Syntax parser. Names (entities) can be given as full IRIs enclosed in < and >
           or as simple strings, in that case the namespace attribute of the parser has to be set to resolve them.
           See https://www.w3.org/TR/owl2-manchester-syntax/#IRIs.2C_Integers.2C_Literals.2C_and_Entities
           for more information.
           Prefixes are currently not supported, except for datatypes.

        Args:
            namespace: Namespace to resolve names that were given without one.
            grammar: Grammar (defaults to MANCHESTERGRAMMAR).
        """
        self.ns = namespace
        self.grammar = grammar

        if self.grammar is None:
            self.grammar = MANCHESTER_GRAMMAR

    def parse_expression(self, expression_str: str) -> OWLClassExpression:
        tree = self.grammar.parse(expression_str.strip())
        return self.visit(tree)

    @_transform_children
    def visit_union(self, node, children) -> OWLClassExpression:
        return children if isinstance(children, OWLClassExpression) else OWLObjectUnionOf(children)

    @_transform_children
    def visit_intersection(self, node, children) -> OWLClassExpression:
        return children if isinstance(children, OWLClassExpression) else OWLObjectIntersectionOf(children)

    def visit_primary(self, node, children) -> OWLClassExpression:
        match_not, expr = children
        return OWLObjectComplementOf(expr[0]) if isinstance(match_not, list) else expr[0]

    def visit_some_only_res(self, node, children) -> OWLQuantifiedObjectRestriction:
        property_, _, type_, _, filler = children
        type_ = _node_text(*type_)
        if type_ == _MAN_SYNTAX.EXISTS:
            return OWLObjectSomeValuesFrom(property_, filler)
        else:
            return OWLObjectAllValuesFrom(property_, filler)

    def visit_cardinality_res(self, node, children) -> OWLObjectCardinalityRestriction:
        property_, _, type_, _, cardinality, _, filler = children
        type_ = _node_text(*type_)
        if type_ == _MAN_SYNTAX.MIN:
            return OWLObjectMinCardinality(cardinality, property_, filler)
        elif type_ == _MAN_SYNTAX.MAX:
            return OWLObjectMaxCardinality(cardinality, property_, filler)
        else:
            return OWLObjectExactCardinality(cardinality, property_, filler)

    def visit_value_res(self, node, children) -> OWLObjectHasValue:
        property_, *_, individual = children
        return OWLObjectHasValue(property_, individual)

    def visit_has_self(self, node, children) -> OWLObjectHasSelf:
        property_, *_ = children
        return OWLObjectHasSelf(property_)

    def visit_object_property(self, node, children) -> OWLObjectPropertyExpression:
        inverse, property_ = children
        return property_.get_inverse_property() if isinstance(inverse, list) else property_

    def visit_class_expression(self, node, children) -> OWLClassExpression:
        return children[0]

    @_transform_children
    def visit_individual_list(self, node, children) -> OWLObjectOneOf:
        return OWLObjectOneOf(children)

    def visit_data_primary(self, node, children) -> OWLDataRange:
        match_not, expr = children
        return OWLDataComplementOf(expr[0]) if isinstance(match_not, list) else expr[0]

    def visit_data_some_only_res(self, node, children) -> OWLQuantifiedDataRestriction:
        property_, _, type_, _, filler = children
        type_ = _node_text(*type_)
        if type_ == _MAN_SYNTAX.EXISTS:
            return OWLDataSomeValuesFrom(property_, filler)
        else:
            return OWLDataAllValuesFrom(property_, filler)

    def visit_data_cardinality_res(self, node, children) -> OWLDataCardinalityRestriction:
        property_, _, type_, _, cardinality, _, filler = children
        type_ = _node_text(*type_)
        if type_ == _MAN_SYNTAX.MIN:
            return OWLDataMinCardinality(cardinality, property_, filler)
        elif type_ == _MAN_SYNTAX.MAX:
            return OWLDataMaxCardinality(cardinality, property_, filler)
        else:
            return OWLDataExactCardinality(cardinality, property_, filler)

    def visit_data_value_res(self, node, children) -> OWLDataHasValue:
        property_, *_, literal = children
        return OWLDataHasValue(property_, literal)

    @_transform_children
    def visit_data_union(self, node, children) -> OWLDataRange:
        return children if isinstance(children, OWLDataRange) else OWLDataUnionOf(children)

    @_transform_children
    def visit_data_intersection(self, node, children) -> OWLDataRange:
        return children if isinstance(children, OWLDataRange) else OWLDataIntersectionOf(children)

    @_transform_children
    def visit_literal_list(self, node, children) -> OWLDataOneOf:
        return OWLDataOneOf(children)

    def visit_data_parentheses(self, node, children) -> OWLDataRange:
        *_, expr, _, _ = children
        return expr

    def visit_datatype_restriction(self, node, children) -> OWLDatatypeRestriction:
        datatype, *_, facet_restrictions, _, _ = children
        if isinstance(facet_restrictions, OWLFacetRestriction):
            facet_restrictions = facet_restrictions,
        not_valid_literals = []
        if datatype != StringOWLDatatype:
            not_valid_literals = [res.get_facet_value() for res in facet_restrictions
                                  if res.get_facet_value().get_datatype() != datatype]
        not_valid_facets = [res.get_facet() for res in facet_restrictions
                            if res.get_facet() not in _DATATYPE_TO_FACETS[datatype]]

        if not_valid_literals or not_valid_facets:
            raise ValueError(f"Literals: {not_valid_literals} and Facets: {not_valid_facets}"
                             f" not valid for datatype: {datatype}")
        return OWLDatatypeRestriction(datatype, facet_restrictions)

    @_transform_children
    def visit_facet_restrictions(self, node, children) -> List[OWLFacetRestriction]:
        return children

    def visit_facet_restriction(self, node, children) -> OWLFacetRestriction:
        facet, _, literal = children
        if literal.get_datatype() not in _FACET_TO_LITERAL_DATATYPE[facet]:
            raise ValueError(f"Literal: {literal} not valid for facet: {facet}")
        return OWLFacetRestriction(facet, literal)

    def visit_literal(self, node, children) -> OWLLiteral:
        return children[0]

    def visit_typed_literal(self, node, children) -> OWLLiteral:
        value, _, datatype = children
        return OWLLiteral(value[1:-1], datatype)

    def visit_string_literal_language(self, node, children):
        raise NotImplementedError(f"Language tags and plain literals not supported in owlapy yet: {_node_text(node)}")

    def visit_string_literal_no_language(self, node, children) -> OWLLiteral:
        value = children[0]
        return OWLLiteral(value[1:-1], StringOWLDatatype)

    def visit_quoted_string(self, node, children) -> str:
        return _node_text(node)

    def visit_float_literal(self, node, children) -> OWLLiteral:
        return OWLLiteral(_node_text(node)[:-1], DoubleOWLDatatype)

    def visit_decimal_literal(self, node, children) -> OWLLiteral:
        # TODO: Just use float for now, decimal not supported in owlapy yet
        return OWLLiteral(_node_text(node), DoubleOWLDatatype)

    def visit_integer_literal(self, node, children) -> OWLLiteral:
        return OWLLiteral(_node_text(node), IntegerOWLDatatype)

    def visit_boolean_literal(self, node, children) -> OWLLiteral:
        return OWLLiteral(_node_text(node), BooleanOWLDatatype)

    def visit_datetime_literal(self, node, children) -> OWLLiteral:
        return OWLLiteral(_node_text(node), DateTimeOWLDatatype)

    def visit_duration_literal(self, node, children) -> OWLLiteral:
        return OWLLiteral(_node_text(node), DurationOWLDatatype)

    def visit_date_literal(self, node, children) -> OWLLiteral:
        return OWLLiteral(_node_text(node), DateOWLDatatype)

    def visit_non_negative_integer(self, node, children) -> int:
        return int(_node_text(node))

    def visit_datatype_iri(self, node, children) -> str:
        return children[0][1]

    def visit_datatype(self, node, children) -> OWLDatatype:
        return _STRING_TO_DATATYPE[_node_text(node)]

    def visit_facet(self, node, children) -> OWLFacet:
        return OWLFacet.from_str(_node_text(node))

    def visit_class_iri(self, node, children) -> OWLClass:
        return OWLClass(children[0])

    def visit_individual_iri(self, node, children) -> OWLNamedIndividual:
        return OWLNamedIndividual(children[0])

    def visit_object_property_iri(self, node, children) -> OWLObjectProperty:
        return OWLObjectProperty(children[0])

    def visit_data_property_iri(self, node, children) -> OWLDataProperty:
        return OWLDataProperty(children[0])

    def visit_iri(self, node, children) -> IRI:
        return children[0]

    def visit_full_iri(self, node, children) -> IRI:
        try:
            iri = _node_text(node)[1:-1]
            return IRI.create(iri)
        except IndexError:
            raise ValueError(f"{iri} is not a valid IRI.")

    def visit_abbreviated_iri(self, node, children):
        # TODO: Add support for prefixes
        raise NotImplementedError(f"Parsing of prefixes is not supported yet: {_node_text(node)}")

    def visit_simple_iri(self, node, children) -> IRI:
        simple_iri = _node_text(node)
        if simple_iri == "Thing":
            return OWLRDFVocabulary.OWL_THING.iri
        elif simple_iri == "Nothing":
            return OWLRDFVocabulary.OWL_NOTHING.iri
        elif self.ns is not None:
            return IRI(self.ns, simple_iri)
        else:
            raise ValueError(f"If entities are specified without a full iri ({simple_iri}), "
                             "the namespace attribute of the parser has to be set.")

    def visit_parentheses(self, node, children) -> OWLClassExpression:
        *_, expr, _, _ = children
        return expr

    def generic_visit(self, node, children):
        return children or node


DL_GRAMMAR = Grammar(r"""
    union = intersection (must_ws "⊔" must_ws intersection)*
    intersection = primary (must_ws "⊓" must_ws primary)*

    # Main entry point + object properties
    primary = ("¬" maybe_ws)? (has_self / data_value_res / value_res / data_some_only_res / some_only_res /
                data_cardinality_res / cardinality_res / class_expression)
    some_only_res = ("∃"/"∀") maybe_ws object_property "." primary
    cardinality_res = ("≥"/"≤"/"=") must_ws non_negative_integer must_ws object_property "." primary
    value_res = "∃" maybe_ws object_property "." "{" individual_iri "}"
    has_self = "∃" maybe_ws object_property "." "Self"
    object_property = object_property_iri "⁻"?

    class_expression = class_iri / individual_list / parentheses
    individual_list = "{" maybe_ws individual_iri (maybe_ws "⊔" maybe_ws individual_iri)* maybe_ws "}"

    # Back to start symbol (first production rule)
    parentheses = "(" maybe_ws union maybe_ws ")"

    # Data properties
    data_some_only_res = ("∃"/"∀") maybe_ws data_property_iri "." data_primary
    data_cardinality_res = ("≥"/"≤"/"=") must_ws non_negative_integer must_ws data_property_iri "." data_primary
    data_value_res = "∃" maybe_ws data_property_iri "." "{" literal "}"
    data_primary = ("¬" maybe_ws)? data_range
    data_range = datatype_restriction / datatype_iri / literal_list / data_parentheses
    literal_list = "{" maybe_ws literal (maybe_ws "⊔" maybe_ws literal)* maybe_ws "}"
    data_parentheses = "(" maybe_ws data_union maybe_ws ")"
    data_union = data_intersection (must_ws "⊔" must_ws data_intersection)*
    data_intersection = data_primary (must_ws "⊓" must_ws data_primary)*
    datatype_restriction = datatype_iri "[" maybe_ws facet_restrictions maybe_ws "]"
    facet_restrictions = facet_restriction (maybe_ws "⊓" maybe_ws facet_restriction)*
    facet_restriction = facet must_ws literal
    facet = "length" / "minLength" / "maxLength" / "pattern" / "langRange"
            / "totalDigits" / "fractionDigits" / "≥" / "≤" / "<" / ">"
    datatype_iri = ("<http://www.w3.org/2001/XMLSchema#" datatype ">") / ("xsd:"? datatype)
    datatype = "double" / "integer" / "boolean" / "string" / "dateTime" / "date" / "duration"

    # Literals
    literal = typed_literal / string_literal_language / string_literal_no_language / datetime_literal /
              duration_literal / date_literal / float_literal / decimal_literal / integer_literal /
              boolean_literal
    typed_literal = quoted_string "^^" datatype_iri
    string_literal_language = quoted_string language_tag
    string_literal_no_language = quoted_string / no_match
    quoted_string = ~"\"([^\"\\\\]|\\\\[\"\\\\])*\""
    language_tag = "@" ~"[a-zA-Z]+" ("-" ~"[a-zA-Z0-9]+")*
    float_literal = sign (float_with_integer_part / float_no_integer_part) ("f"/"F")
    float_with_integer_part = non_negative_integer ("." ~"[0-9]+")? exponent?
    float_no_integer_part = "." ~"[0-9]+" exponent?
    exponent = ("e"/"E") sign ~"[0-9]+"
    decimal_literal = sign non_negative_integer "." ~"[0-9]+"
    integer_literal = sign non_negative_integer
    boolean_literal = ~"[tT]rue" / ~"[fF]alse"
    date_literal = ~"[0-9]{4}-((0[1-9])|(1[0-2]))-(([0-2][0-9])|(3[01]))"
    datetime_literal = ~"[0-9]{4}-((0[1-9])|(1[0-2]))-(([0-2][0-9])|(3[01]))[T\u0020]"
                       ~"(([0-1][0-9])|(2[0-3])):[0-5][0-9]:[0-5][0-9](\\.[0-9]{6})?"
                       ~"(Z|([+-](([0-1][0-9])|(2[0-3])):[0-5][0-9](:[0-5][0-9](\\.[0-9]{6})?)?))?"
    duration_literal = ~"P([0-9]+W)?([0-9]+D)?(T([0-9]+H)?([0-9]+M)?([0-9]+(\\.[0-9]{6})?S)?)?"
    sign = ("+"/"-")?
    non_negative_integer = ~"0|([1-9][0-9]*)"

    # IRIs / Characters
    class_iri = "⊤" / "⊥" / iri
    object_property_iri = iri / no_match
    data_property_iri = iri / no_match
    individual_iri = iri / no_match
    iri = full_iri / abbreviated_iri / simple_iri
    full_iri = iri_ref / no_match
    abbreviated_iri = pname_ln / no_match
    simple_iri = pn_local / no_match

    # Changes to ManchesterGrammar -- Don't allow:
    # . used as a separator
    # ⁻ used for inverse properties (\u207B)
    iri_ref = "<" ~"[^<>\"{}|^`\\\\\u0000-\u0020]*" ">"
    pname_ln = pname_ns pn_local
    pname_ns = pn_prefix? ":"
    pn_prefix = pn_chars_base pn_chars*
    pn_local = (pn_chars_u / ~"[0-9]") pn_chars*
    pn_chars = pn_chars_u / "-" / ~"[0-9]" / ~"\u00B7" / ~"[\u0300-\u036F]" / ~"[\u203F-\u2040]"
    pn_chars_u = pn_chars_base / "_"
    pn_chars_base = ~"[a-zA-Z]" / ~"[\u00C0-\u00D6]" / ~"[\u00D8-\u00F6]" / ~"[\u00F8-\u02FF]" /
                    ~"[\u0370-\u037D]" / ~"[\u037F-\u1FFF]" / ~"[\u200C-\u200D]" / ~"[\u2070-\u207A]" /
                    ~"[\u207C-\u218F]"/ ~"[\u2C00-\u2FEF]" / ~"[\u3001-\uD7FF]" / ~"[\uF900-\uFDCF]" /
                    ~"[\uFDF0-\uFFFD]" / ~"[\U00010000-\U000EFFFF]"

    must_ws = ~"[\u0020\u000D\u0009\u000A]+"
    maybe_ws = ~"[\u0020\u000D\u0009\u000A]*"

    # hacky workaround: can be added to a pass through production rule that is semantically important
    # so nodes are not combined which makes the parsing cleaner
    no_match = ~"(?!a)a"
    """)


# workaround to support multiple inheritance with different metaclasses
class _DLSyntaxParserMeta(type(NodeVisitor), type(OWLObjectParser)):
    pass


class DLSyntaxParser(NodeVisitor, OWLObjectParser, metaclass=_DLSyntaxParserMeta):
    """Description Logic Syntax parser to parse strings to OWLClassExpressions."""

    slots = 'ns', 'grammar'

    ns: Optional[Union[str, Namespaces]]

    def __init__(self, namespace: Optional[Union[str, Namespaces]] = None, grammar=None):
        """Create a new Description Logic Syntax parser. Names (entities) can be given as full IRIs enclosed in < and >
           or as simple strings, in that case the namespace attribute of the parser has to be set to resolve them.
           Prefixes are currently not supported, except for datatypes.

        Args:
            namespace: Namespace to resolve names that were given without one.
            grammar: Grammar (defaults to DL_GRAMMAR).
        """
        self.ns = namespace
        self.grammar = grammar

        if self.grammar is None:
            self.grammar = DL_GRAMMAR

    def parse_expression(self, expression_str: str) -> OWLClassExpression:
        tree = self.grammar.parse(expression_str.strip())
        return self.visit(tree)

    @_transform_children
    def visit_union(self, node, children) -> OWLClassExpression:
        return children if isinstance(children, OWLClassExpression) else OWLObjectUnionOf(children)

    @_transform_children
    def visit_intersection(self, node, children) -> OWLClassExpression:
        return children if isinstance(children, OWLClassExpression) else OWLObjectIntersectionOf(children)

    def visit_primary(self, node, children) -> OWLClassExpression:
        match_not, expr = children
        return OWLObjectComplementOf(expr[0]) if isinstance(match_not, list) else expr[0]

    def visit_some_only_res(self, node, children) -> OWLQuantifiedObjectRestriction:
        type_, _, property_, _, filler = children
        type_ = _node_text(*type_)
        if type_ == _DL_SYNTAX.EXISTS:
            return OWLObjectSomeValuesFrom(property_, filler)
        else:
            return OWLObjectAllValuesFrom(property_, filler)

    def visit_cardinality_res(self, node, children) -> OWLObjectCardinalityRestriction:
        type_, _, cardinality, _, property_, _, filler = children
        type_ = _node_text(*type_)
        if type_ == _DL_SYNTAX.MIN:
            return OWLObjectMinCardinality(cardinality, property_, filler)
        elif type_ == _DL_SYNTAX.MAX:
            return OWLObjectMaxCardinality(cardinality, property_, filler)
        else:
            return OWLObjectExactCardinality(cardinality, property_, filler)

    def visit_value_res(self, node, children) -> OWLObjectHasValue:
        _, _, property_, _, _, individual, _ = children
        return OWLObjectHasValue(property_, individual)

    def visit_has_self(self, node, children) -> OWLObjectHasSelf:
        _, _, property_, _, _ = children
        return OWLObjectHasSelf(property_)

    def visit_object_property(self, node, children) -> OWLObjectPropertyExpression:
        property_, inverse = children
        return property_.get_inverse_property() if isinstance(inverse, list) else property_

    def visit_class_expression(self, node, children) -> OWLClassExpression:
        return children[0]

    @_transform_children
    def visit_individual_list(self, node, children) -> OWLObjectOneOf:
        return OWLObjectOneOf(children)

    def visit_data_primary(self, node, children) -> OWLDataRange:
        match_not, expr = children
        return OWLDataComplementOf(expr[0]) if isinstance(match_not, list) else expr[0]

    def visit_data_some_only_res(self, node, children) -> OWLQuantifiedDataRestriction:
        type_, _, property_, _, filler = children
        type_ = _node_text(*type_)
        if type_ == _DL_SYNTAX.EXISTS:
            return OWLDataSomeValuesFrom(property_, filler)
        else:
            return OWLDataAllValuesFrom(property_, filler)

    def visit_data_cardinality_res(self, node, children) -> OWLDataCardinalityRestriction:
        type_, _, cardinality, _, property_, _, filler = children
        type_ = _node_text(*type_)
        if type_ == _DL_SYNTAX.MIN:
            return OWLDataMinCardinality(cardinality, property_, filler)
        elif type_ == _DL_SYNTAX.MAX:
            return OWLDataMaxCardinality(cardinality, property_, filler)
        else:
            return OWLDataExactCardinality(cardinality, property_, filler)

    def visit_data_value_res(self, node, children) -> OWLDataHasValue:
        _, _, property_, _, _, literal, _ = children
        return OWLDataHasValue(property_, literal)

    @_transform_children
    def visit_data_union(self, node, children) -> OWLDataRange:
        return children if isinstance(children, OWLDataRange) else OWLDataUnionOf(children)

    @_transform_children
    def visit_data_intersection(self, node, children) -> OWLDataRange:
        return children if isinstance(children, OWLDataRange) else OWLDataIntersectionOf(children)

    @_transform_children
    def visit_literal_list(self, node, children) -> OWLDataOneOf:
        return OWLDataOneOf(children)

    def visit_data_parentheses(self, node, children) -> OWLDataRange:
        *_, expr, _, _ = children
        return expr

    def visit_datatype_restriction(self, node, children) -> OWLDatatypeRestriction:
        datatype, *_, facet_restrictions, _, _ = children
        if isinstance(facet_restrictions, OWLFacetRestriction):
            facet_restrictions = facet_restrictions,
        not_valid_literals = []
        if datatype != StringOWLDatatype:
            not_valid_literals = [res.get_facet_value() for res in facet_restrictions
                                  if res.get_facet_value().get_datatype() != datatype]
        not_valid_facets = [res.get_facet() for res in facet_restrictions
                            if res.get_facet() not in _DATATYPE_TO_FACETS[datatype]]

        if not_valid_literals or not_valid_facets:
            raise ValueError(f"Literals: {not_valid_literals} and Facets: {not_valid_facets}"
                             f" not valid for datatype: {datatype}")
        return OWLDatatypeRestriction(datatype, facet_restrictions)

    @_transform_children
    def visit_facet_restrictions(self, node, children) -> List[OWLFacetRestriction]:
        return children

    def visit_facet_restriction(self, node, children) -> OWLFacetRestriction:
        facet, _, literal = children
        if literal.get_datatype() not in _FACET_TO_LITERAL_DATATYPE[facet]:
            raise ValueError(f"Literal: {literal} not valid for facet: {facet}")
        return OWLFacetRestriction(facet, literal)

    def visit_literal(self, node, children) -> OWLLiteral:
        return children[0]

    def visit_typed_literal(self, node, children) -> OWLLiteral:
        value, _, datatype = children
        return OWLLiteral(value[1:-1], datatype)

    def visit_string_literal_language(self, node, children):
        raise NotImplementedError(f"Language tags and plain literals not supported in owlapy yet: {_node_text(node)}")

    def visit_string_literal_no_language(self, node, children) -> OWLLiteral:
        value = children[0]
        return OWLLiteral(value[1:-1], StringOWLDatatype)

    def visit_quoted_string(self, node, children) -> str:
        return _node_text(node)

    def visit_float_literal(self, node, children) -> OWLLiteral:
        return OWLLiteral(_node_text(node)[:-1], DoubleOWLDatatype)

    def visit_decimal_literal(self, node, children) -> OWLLiteral:
        # TODO: Just use float for now, decimal not supported in owlapy yet
        return OWLLiteral(_node_text(node), DoubleOWLDatatype)

    def visit_integer_literal(self, node, children) -> OWLLiteral:
        return OWLLiteral(_node_text(node), IntegerOWLDatatype)

    def visit_boolean_literal(self, node, children) -> OWLLiteral:
        return OWLLiteral(_node_text(node), BooleanOWLDatatype)

    def visit_datetime_literal(self, node, children) -> OWLLiteral:
        return OWLLiteral(_node_text(node), DateTimeOWLDatatype)

    def visit_duration_literal(self, node, children) -> OWLLiteral:
        return OWLLiteral(_node_text(node), DurationOWLDatatype)

    def visit_date_literal(self, node, children) -> OWLLiteral:
        return OWLLiteral(_node_text(node), DateOWLDatatype)

    def visit_non_negative_integer(self, node, children) -> int:
        return int(_node_text(node))

    def visit_datatype_iri(self, node, children) -> str:
        return children[0][1]

    def visit_datatype(self, node, children) -> OWLDatatype:
        return _STRING_TO_DATATYPE[_node_text(node)]

    def visit_facet(self, node, children) -> OWLFacet:
        symbolic_form = _node_text(node)
        if symbolic_form == _DL_SYNTAX.MIN:
            symbolic_form = '>='
        elif symbolic_form == _DL_SYNTAX.MAX:
            symbolic_form = '<='
        return OWLFacet.from_str(symbolic_form)

    def visit_class_iri(self, node, children) -> OWLClass:
        top_bottom = _node_text(node)
        if top_bottom == _DL_SYNTAX.TOP:
            return OWLClass(OWLRDFVocabulary.OWL_THING.iri)
        elif top_bottom == _DL_SYNTAX.BOTTOM:
            return OWLClass(OWLRDFVocabulary.OWL_NOTHING.iri)
        else:
            return OWLClass(children[0])

    def visit_individual_iri(self, node, children) -> OWLNamedIndividual:
        return OWLNamedIndividual(children[0])

    def visit_object_property_iri(self, node, children) -> OWLObjectProperty:
        return OWLObjectProperty(children[0])

    def visit_data_property_iri(self, node, children) -> OWLDataProperty:
        return OWLDataProperty(children[0])

    def visit_iri(self, node, children) -> IRI:
        return children[0]

    def visit_full_iri(self, node, children) -> IRI:
        try:
            iri = _node_text(node)[1:-1]
            return IRI.create(iri)
        except IndexError:
            raise ValueError(f"{_node_text(node)[1:-1]} is not a valid IRI.")

    def visit_abbreviated_iri(self, node, children):
        # TODO: Add support for prefixes
        raise NotImplementedError(f"Parsing of prefixes is not supported yet: {_node_text(node)}")

    def visit_simple_iri(self, node, children) -> IRI:
        simple_iri = _node_text(node)
        if self.ns is not None:
            return IRI(self.ns, simple_iri)
        else:
            raise ValueError(f"If entities are specified without a full iri ({simple_iri}), "
                             "the namespace attribute of the parser has to be set.")

    def visit_parentheses(self, node, children) -> OWLClassExpression:
        *_, expr, _, _ = children
        return expr

    def generic_visit(self, node, children):
        return children or node


DLparser = DLSyntaxParser()
ManchesterParser = ManchesterOWLSyntaxParser()


def dl_to_owl_expression(dl_expression: str, namespace: str):
    DLparser.ns = namespace
    return DLparser.parse_expression(dl_expression)


def manchester_to_owl_expression(manchester_expression: str, namespace: str):
    ManchesterParser.ns = namespace
    return ManchesterParser.parse_expression(manchester_expression)
