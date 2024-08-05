"""Renderers for different syntax."""
# -*- coding: utf-8 -*-

import types
from functools import singledispatchmethod
from typing import List, Callable

from owlapy import namespaces
from .iri import IRI
from .owl_individual import OWLNamedIndividual, OWLIndividual
from .owl_literal import OWLLiteral
from .owl_object import OWLObjectRenderer, OWLEntity, OWLObject
from .owl_property import OWLObjectInverseOf, OWLPropertyExpression, OWLDataProperty, OWLObjectProperty
from .class_expression import OWLClassExpression, OWLBooleanClassExpression, OWLClass, OWLObjectSomeValuesFrom, \
    OWLObjectAllValuesFrom, OWLObjectUnionOf, OWLObjectIntersectionOf, OWLObjectComplementOf, OWLObjectMinCardinality, \
    OWLObjectExactCardinality, OWLObjectMaxCardinality, OWLObjectHasSelf, OWLDataSomeValuesFrom, OWLDataAllValuesFrom, \
    OWLDataHasValue, OWLDataMinCardinality, OWLDataExactCardinality, OWLDataMaxCardinality, OWLDataOneOf, \
    OWLNaryBooleanClassExpression, OWLRestriction
from owlapy.vocab import OWLFacet
from .owl_data_ranges import OWLNaryDataRange, OWLDataComplementOf, OWLDataUnionOf, OWLDataIntersectionOf
from .class_expression import OWLObjectHasValue, OWLFacetRestriction, OWLDatatypeRestriction, OWLObjectOneOf
from .owl_datatype import OWLDatatype
from .owl_reasoner import OWLReasoner

_DL_SYNTAX = types.SimpleNamespace(
    SUBCLASS="⊑",
    EQUIVALENT_TO="≡",
    NOT="¬",
    DISJOINT_WITH="⊑" + " " + "¬",
    EXISTS="∃",
    FORALL="∀",
    IN="∈",
    MIN="≥",
    EQUAL="=",
    NOT_EQUAL="≠",
    MAX="≤",
    INVERSE="⁻",
    AND="⊓",
    TOP="⊤",
    BOTTOM="⊥",
    OR="⊔",
    COMP="∘",
    WEDGE="⋀",
    IMPLIES="←",
    COMMA=",",
    SELF="Self",
)


def _simple_short_form_provider(e: OWLEntity) -> str:
    iri: IRI = e.iri
    sf = iri.reminder
    for ns in [namespaces.XSD, namespaces.OWL, namespaces.RDFS, namespaces.RDF]:
        if iri.get_namespace() == ns:
            return "%s:%s" % (ns.prefix, sf)
    else:
        return sf


mapper = {
    'OWLNamedIndividual': "http://www.w3.org/2002/07/owl#NamedIndividual",
    'OWLObjectProperty': "http://www.w3.org/2002/07/owl#ObjectProperty",
    'OWLDataProperty': "http://www.w3.org/2002/07/owl#DatatypeProperty",
    'OWLClass': "http://www.w3.org/2002/07/owl#Class"
}


def translating_short_form_provider(e: OWLEntity, reasoner, rules: dict[str:str] = None) -> str:
    """
    e: entity.
    reasoner: OWLReasoner or Triplestore(from Ontolearn)
    rules: A mapping from OWLEntity to predicates,
        Keys in rules can be  general or specific iris, e.g.,
        IRI to IRI s.t. the second IRI must be a predicate leading to literal
    """
    label_iri = "http://www.w3.org/2000/01/rdf-schema#label"

    def get_label(entity, r, predicate=label_iri):
        if isinstance(r, OWLReasoner):
            values = list(r.data_property_values(OWLNamedIndividual(e.iri), OWLDataProperty(label_iri)))
            if values:
                return str(values[0].get_literal())
            else:
                return _simple_short_form_provider(entity)
        else:
            # else we have a TripleStore
            sparql = f"""select ?o where {{ <{entity.str}> <{predicate}> ?o}}"""
            if results := list(r.query(sparql)):
                return str(results[0])
            else:
                return _simple_short_form_provider(entity)

    if rules is None:
        return get_label(e, reasoner)
    else:
        # Check if a predicate is set for a specific IRI:
        # (e.g "http://www.example.org/SomeSpecificClass":"http://www.example.org/SomePredicate")
        # WARNING: This will only replace the specified class not individuals belonging to this class.
        # This is to avoid confusion, because entity can also be a property and properties does not classify individual.
        # So to avoid confusion, the specified predicate in the rules will only be used to 'label' the specified entity
        # iri.
        if specific_predicate := rules.get(e.str, None):
            return get_label(e, reasoner, specific_predicate)
        # Check if a predicate is set for a general IRI:
        # (e.g "http://www.w3.org/2002/07/owl#NamedIndividual":"http://www.example.org/SomePredicate")
        # then it will label any entity of that type using the given predicate.
        elif general_predicate := rules.get(mapper[str(type(e))], None):
            return get_label(e, reasoner, general_predicate)
        # No specific rule set, use http://www.w3.org/2000/01/rdf-schema#label (by default)
        else:
            return get_label(e, reasoner)


class DLSyntaxObjectRenderer(OWLObjectRenderer):
    """DL Syntax renderer for OWL Objects."""
    __slots__ = '_sfp'

    _sfp: Callable[[OWLEntity], str]

    def __init__(self, short_form_provider: Callable[[OWLEntity], str] = _simple_short_form_provider):
        """Create a new DL Syntax renderer.

        Args:
            short_form_provider: Custom short form provider.
        """
        self._sfp = short_form_provider

    def set_short_form_provider(self, short_form_provider: Callable[[OWLEntity], str]) -> None:
        self._sfp = short_form_provider

    @singledispatchmethod
    def render(self, o: OWLObject) -> str:
        assert isinstance(o, OWLObject), f"Tried to render non-OWLObject {o} of {type(o)}"
        raise NotImplementedError

    @render.register
    def _(self, o: OWLClass) -> str:
        if o.is_owl_nothing():
            return _DL_SYNTAX.BOTTOM
        elif o.is_owl_thing():
            return _DL_SYNTAX.TOP
        else:
            return self._sfp(o)

    @render.register
    def _(self, p: OWLPropertyExpression) -> str:
        return self._sfp(p)

    @render.register
    def _(self, i: OWLNamedIndividual) -> str:
        return self._sfp(i)

    @render.register
    def _(self, e: OWLObjectSomeValuesFrom) -> str:
        return "%s %s.%s" % (_DL_SYNTAX.EXISTS, self.render(e.get_property()), self._render_nested(e.get_filler()))

    @render.register
    def _(self, e: OWLObjectAllValuesFrom) -> str:
        return "%s %s.%s" % (_DL_SYNTAX.FORALL, self.render(e.get_property()), self._render_nested(e.get_filler()))

    @render.register
    def _(self, c: OWLObjectUnionOf) -> str:
        return (" %s " % _DL_SYNTAX.OR).join(self._render_operands(c))

    @render.register
    def _(self, c: OWLObjectIntersectionOf) -> str:
        return (" %s " % _DL_SYNTAX.AND).join(self._render_operands(c))

    @render.register
    def _(self, n: OWLObjectComplementOf) -> str:
        return "%s%s" % (_DL_SYNTAX.NOT, self._render_nested(n.get_operand()))

    @render.register
    def _(self, p: OWLObjectInverseOf) -> str:
        return "%s%s" % (self.render(p.get_named_property()), _DL_SYNTAX.INVERSE)

    @render.register
    def _(self, r: OWLObjectMinCardinality) -> str:
        return "%s %s %s.%s" % (
            _DL_SYNTAX.MIN, r.get_cardinality(), self.render(r.get_property()), self._render_nested(r.get_filler()))

    @render.register
    def _(self, r: OWLObjectExactCardinality) -> str:
        return "%s %s %s.%s" % (
            _DL_SYNTAX.EQUAL, r.get_cardinality(), self.render(r.get_property()), self._render_nested(r.get_filler()))

    @render.register
    def _(self, r: OWLObjectMaxCardinality) -> str:
        return "%s %s %s.%s" % (
            _DL_SYNTAX.MAX, r.get_cardinality(), self.render(r.get_property()), self._render_nested(r.get_filler()))

    @render.register
    def _(self, r: OWLObjectHasSelf) -> str:
        return "%s %s.%s" % (_DL_SYNTAX.EXISTS, self.render(r.get_property()), _DL_SYNTAX.SELF)

    @render.register
    def _(self, r: OWLObjectHasValue):
        return "%s %s.{%s}" % (_DL_SYNTAX.EXISTS, self.render(r.get_property()),
                               self.render(r.get_filler()))

    @render.register
    def _(self, r: OWLObjectOneOf):
        return "{%s}" % (" %s " % _DL_SYNTAX.COMMA).join(
            "%s" % (self.render(_)) for _ in r.individuals())

    @render.register
    def _(self, e: OWLDataSomeValuesFrom) -> str:
        return "%s %s.%s" % (_DL_SYNTAX.EXISTS, self.render(e.get_property()), self._render_nested(e.get_filler()))

    @render.register
    def _(self, e: OWLDataAllValuesFrom) -> str:
        return "%s %s.%s" % (_DL_SYNTAX.FORALL, self.render(e.get_property()), self._render_nested(e.get_filler()))

    @render.register
    def _(self, r: OWLFacetRestriction) -> str:
        symbolic_form = r.get_facet().symbolic_form
        if r.get_facet() == OWLFacet.MIN_INCLUSIVE:
            symbolic_form = _DL_SYNTAX.MIN
        elif r.get_facet() == OWLFacet.MAX_INCLUSIVE:
            symbolic_form = _DL_SYNTAX.MAX
        return "%s %s" % (symbolic_form, r.get_facet_value().get_literal())

    @render.register
    def _(self, r: OWLDatatypeRestriction) -> str:
        s = [self.render(_) for _ in r.get_facet_restrictions()]
        return "%s[%s]" % (self.render(r.get_datatype()), (" %s " % _DL_SYNTAX.COMMA).join(s))

    @render.register
    def _(self, r: OWLDataHasValue):
        return "%s %s.{%s}" % (_DL_SYNTAX.EXISTS, self.render(r.get_property()),
                               self.render(r.get_filler()))

    @render.register
    def _(self, r: OWLDataMinCardinality) -> str:
        return "%s %s %s.%s" % (
            _DL_SYNTAX.MIN, r.get_cardinality(), self.render(r.get_property()), self._render_nested(r.get_filler()))

    @render.register
    def _(self, r: OWLDataExactCardinality) -> str:
        return "%s %s %s.%s" % (
            _DL_SYNTAX.EQUAL, r.get_cardinality(), self.render(r.get_property()), self._render_nested(r.get_filler()))

    @render.register
    def _(self, r: OWLDataMaxCardinality) -> str:
        return "%s %s %s.%s" % (
            _DL_SYNTAX.MAX, r.get_cardinality(), self.render(r.get_property()), self._render_nested(r.get_filler()))

    @render.register
    def _(self, r: OWLDataOneOf):
        return "{%s}" % (" %s " % _DL_SYNTAX.OR).join(
            "%s" % (self.render(_)) for _ in r.values())

    # TODO
    # @render.register
    # def _(self, r: OWLObjectPropertyChain):
    #     return (" %s " % _DL_SYNTAX.COMP).join(self.render(_) for _ in r.property_chain())

    @render.register
    def _(self, n: OWLDataComplementOf) -> str:
        return "%s%s" % (_DL_SYNTAX.NOT, self._render_nested(n.get_data_range()))

    @render.register
    def _(self, c: OWLDataUnionOf) -> str:
        return (" %s " % _DL_SYNTAX.OR).join(self._render_operands(c))

    @render.register
    def _(self, c: OWLDataIntersectionOf) -> str:
        return (" %s " % _DL_SYNTAX.AND).join(self._render_operands(c))

    @render.register
    def _(self, t: OWLDatatype) -> str:
        return self._sfp(t)

    @render.register
    def _(self, t: OWLLiteral) -> str:
        return t.get_literal()

    def _render_operands(self, c: OWLNaryBooleanClassExpression) -> List[str]:
        return [self._render_nested(_) for _ in c.operands()]

    def _render_nested(self, c: OWLClassExpression) -> str:
        if isinstance(c, OWLBooleanClassExpression) or isinstance(c, OWLRestriction) \
                or isinstance(c, OWLNaryDataRange):
            return "(%s)" % self.render(c)
        else:
            return self.render(c)


_MAN_SYNTAX = types.SimpleNamespace(
    SUBCLASS="SubClassOf",
    EQUIVALENT_TO="EquivalentTo",
    NOT="not",
    DISJOINT_WITH="DisjointWith",
    EXISTS="some",
    FORALL="only",
    MIN="min",
    EQUAL="exactly",
    MAX="max",
    AND="and",
    TOP="Thing",
    BOTTOM="Nothing",
    OR="or",
    INVERSE="inverse",
    COMMA=",",
    SELF="Self",
    VALUE="value",
)


class ManchesterOWLSyntaxOWLObjectRenderer(OWLObjectRenderer):
    """Manchester Syntax renderer for OWL Objects"""
    __slots__ = '_sfp', '_no_render_thing'

    _sfp: Callable[[OWLEntity], str]

    def __init__(self, short_form_provider: Callable[[OWLEntity], str] = _simple_short_form_provider,
                 no_render_thing=False):
        """Create a new Manchester Syntax renderer

        Args:
            short_form_provider: custom short form provider
            no_render_thing: disable manchester rendering for Thing and Nothing
        """
        self._sfp = short_form_provider
        self._no_render_thing = no_render_thing

    def set_short_form_provider(self, short_form_provider: Callable[[OWLEntity], str]) -> None:
        self._sfp = short_form_provider

    @singledispatchmethod
    def render(self, o: OWLObject) -> str:
        assert isinstance(o, OWLObject), f"Tried to render non-OWLObject {o} of {type(o)}"
        raise NotImplementedError

    @render.register
    def _(self, o: OWLClass) -> str:
        if not self._no_render_thing:
            if o.is_owl_nothing():
                return _MAN_SYNTAX.BOTTOM
            if o.is_owl_thing():
                return _MAN_SYNTAX.TOP
        return self._sfp(o)

    @render.register
    def _(self, p: OWLPropertyExpression) -> str:
        return self._sfp(p)

    @render.register
    def _(self, i: OWLNamedIndividual) -> str:
        return self._sfp(i)

    @render.register
    def _(self, e: OWLObjectSomeValuesFrom) -> str:
        return "%s %s %s" % (self.render(e.get_property()), _MAN_SYNTAX.EXISTS, self._render_nested(e.get_filler()))

    @render.register
    def _(self, e: OWLObjectAllValuesFrom) -> str:
        return "%s %s %s" % (self.render(e.get_property()), _MAN_SYNTAX.FORALL, self._render_nested(e.get_filler()))

    @render.register
    def _(self, c: OWLObjectUnionOf) -> str:
        return (" %s " % _MAN_SYNTAX.OR).join(self._render_operands(c))

    @render.register
    def _(self, c: OWLObjectIntersectionOf) -> str:
        return (" %s " % _MAN_SYNTAX.AND).join(self._render_operands(c))

    @render.register
    def _(self, n: OWLObjectComplementOf) -> str:
        return "%s %s" % (_MAN_SYNTAX.NOT, self._render_nested(n.get_operand()))

    @render.register
    def _(self, p: OWLObjectInverseOf) -> str:
        return "%s %s" % (_MAN_SYNTAX.INVERSE, self.render(p.get_named_property()))

    @render.register
    def _(self, r: OWLObjectMinCardinality) -> str:
        return "%s %s %s %s" % (
            self.render(r.get_property()), _MAN_SYNTAX.MIN, r.get_cardinality(), self._render_nested(r.get_filler()))

    @render.register
    def _(self, r: OWLObjectExactCardinality) -> str:
        return "%s %s %s %s" % (
            self.render(r.get_property()), _MAN_SYNTAX.EQUAL, r.get_cardinality(), self._render_nested(r.get_filler()))

    @render.register
    def _(self, r: OWLObjectMaxCardinality) -> str:
        return "%s %s %s %s" % (
            self.render(r.get_property()), _MAN_SYNTAX.MAX, r.get_cardinality(), self._render_nested(r.get_filler()))

    @render.register
    def _(self, r: OWLObjectHasSelf) -> str:
        return "%s %s" % (self.render(r.get_property()), _MAN_SYNTAX.SELF)

    @render.register
    def _(self, r: OWLObjectHasValue):
        return "%s %s %s" % (self.render(r.get_property()), _MAN_SYNTAX.VALUE,
                             self.render(r.get_filler()))

    @render.register
    def _(self, r: OWLObjectOneOf):
        return "{%s}" % (" %s " % _MAN_SYNTAX.COMMA).join(
            "%s" % (self.render(_)) for _ in r.individuals())

    @render.register
    def _(self, e: OWLDataSomeValuesFrom) -> str:
        return "%s %s %s" % (self.render(e.get_property()), _MAN_SYNTAX.EXISTS, self._render_nested(e.get_filler()))

    @render.register
    def _(self, e: OWLDataAllValuesFrom) -> str:
        return "%s %s %s" % (self.render(e.get_property()), _MAN_SYNTAX.FORALL, self._render_nested(e.get_filler()))

    @render.register
    def _(self, r: OWLFacetRestriction):
        return "%s %s" % (r.get_facet().symbolic_form, r.get_facet_value().get_literal())

    @render.register
    def _(self, r: OWLDatatypeRestriction):
        s = [self.render(_) for _ in r.get_facet_restrictions()]
        return "%s[%s]" % (self.render(r.get_datatype()), (" %s " % _MAN_SYNTAX.COMMA).join(s))

    @render.register
    def _(self, r: OWLDataHasValue):
        return "%s %s %s" % (self.render(r.get_property()), _MAN_SYNTAX.VALUE,
                             self.render(r.get_filler()))

    @render.register
    def _(self, r: OWLDataMinCardinality) -> str:
        return "%s %s %s %s" % (
            self.render(r.get_property()), _MAN_SYNTAX.MIN, r.get_cardinality(), self._render_nested(r.get_filler()))

    @render.register
    def _(self, r: OWLDataExactCardinality) -> str:
        return "%s %s %s %s" % (
            self.render(r.get_property()), _MAN_SYNTAX.EQUAL, r.get_cardinality(), self._render_nested(r.get_filler()))

    @render.register
    def _(self, r: OWLDataMaxCardinality) -> str:
        return "%s %s %s %s" % (
            self.render(r.get_property()), _MAN_SYNTAX.MAX, r.get_cardinality(), self._render_nested(r.get_filler()))

    @render.register
    def _(self, r: OWLDataOneOf):
        return "{%s}" % (" %s " % _MAN_SYNTAX.COMMA).join(
            "%s" % (self.render(_)) for _ in r.values())

    # TODO
    # @render.register
    # def _(self, r: OWLObjectPropertyChain):
    #     return (" %s " % _MAN_SYNTAX.COMP).join(self.render(_) for _ in r.property_chain())

    @render.register
    def _(self, n: OWLDataComplementOf) -> str:
        return "%s %s" % (_MAN_SYNTAX.NOT, self._render_nested(n.get_data_range()))

    @render.register
    def _(self, c: OWLDataUnionOf) -> str:
        return (" %s " % _MAN_SYNTAX.OR).join(self._render_operands(c))

    @render.register
    def _(self, c: OWLDataIntersectionOf) -> str:
        return (" %s " % _MAN_SYNTAX.AND).join(self._render_operands(c))

    @render.register
    def _(self, t: OWLDatatype):
        return self._sfp(t)

    @render.register
    def _(self, t: OWLLiteral) -> str:
        return t.get_literal()

    def _render_operands(self, c: OWLNaryBooleanClassExpression) -> List[str]:
        return [self._render_nested(_) for _ in c.operands()]

    def _render_nested(self, c: OWLClassExpression) -> str:
        if isinstance(c, OWLBooleanClassExpression) or isinstance(c, OWLRestriction) \
                or isinstance(c, OWLNaryDataRange):
            return "(%s)" % self.render(c)
        else:
            return self.render(c)


DLrenderer = DLSyntaxObjectRenderer()
ManchesterRenderer = ManchesterOWLSyntaxOWLObjectRenderer()


def owl_expression_to_dl(o: OWLObject) -> str:
    return DLrenderer.render(o)


def owl_expression_to_manchester(o: OWLObject) -> str:
    return ManchesterRenderer.render(o)
