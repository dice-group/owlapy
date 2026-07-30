"""Negation Normal Form and Top-Level CNF/DNF transformation for OWLClassExpression."""
from functools import singledispatchmethod
from typing import Type, cast

from owlapy.class_expression import (
    OWLClass,
    OWLClassExpression,
    OWLDataAllValuesFrom,
    OWLDataExactCardinality,
    OWLDataHasValue,
    OWLDataMaxCardinality,
    OWLDataMinCardinality,
    OWLDataOneOf,
    OWLDataSomeValuesFrom,
    OWLDatatypeRestriction,
    OWLNaryBooleanClassExpression,
    OWLNothing,
    OWLObjectAllValuesFrom,
    OWLObjectComplementOf,
    OWLObjectExactCardinality,
    OWLObjectHasSelf,
    OWLObjectHasValue,
    OWLObjectIntersectionOf,
    OWLObjectMaxCardinality,
    OWLObjectMinCardinality,
    OWLObjectOneOf,
    OWLObjectSomeValuesFrom,
    OWLObjectUnionOf,
    OWLThing,
)

from ..owl_data_ranges import OWLDataComplementOf, OWLDataIntersectionOf, OWLDataUnionOf
from ..owl_datatype import OWLDatatype
from .ordering import _sort_by_ordered_owl_object, combine_nary_expressions


class NNF:
    """This class contains functions to transform a Class Expression into Negation Normal Form."""
    @singledispatchmethod
    def get_class_nnf(self, ce: OWLClassExpression, negated: bool = False) -> OWLClassExpression:
        """Convert a Class Expression to Negation Normal Form. Operands will be sorted.

        Args:
            ce: Class Expression.
            negated: Whether the result should be negated.

        Returns:
            Class Expression in Negation Normal Form.
            """
        raise NotImplementedError

    @get_class_nnf.register
    def _(self, ce: OWLClass, negated: bool = False):
        if negated:
            if ce.is_owl_thing():
                return OWLNothing
            if ce.is_owl_nothing():
                return OWLThing
            return OWLObjectComplementOf(ce)
        return ce

    @get_class_nnf.register
    def _(self, ce: OWLObjectIntersectionOf, negated: bool = False):
        ops = map(lambda _: self.get_class_nnf(_, negated),
                  _sort_by_ordered_owl_object(ce.operands()))
        if negated:
            return OWLObjectUnionOf(ops)
        return OWLObjectIntersectionOf(ops)

    @get_class_nnf.register
    def _(self, ce: OWLObjectUnionOf, negated: bool = False):
        ops = map(lambda _: self.get_class_nnf(_, negated),
                  _sort_by_ordered_owl_object(ce.operands()))
        if negated:
            return OWLObjectIntersectionOf(ops)
        return OWLObjectUnionOf(ops)

    @get_class_nnf.register
    def _(self, ce: OWLObjectComplementOf, negated: bool = False):
        return self.get_class_nnf(ce.get_operand(), not negated)

    @get_class_nnf.register
    def _(self, ce: OWLObjectSomeValuesFrom, negated: bool = False):
        filler = self.get_class_nnf(ce.get_filler(), negated)
        if negated:
            return OWLObjectAllValuesFrom(ce.get_property(), filler)
        return OWLObjectSomeValuesFrom(ce.get_property(), filler)

    @get_class_nnf.register
    def _(self, ce: OWLObjectAllValuesFrom, negated: bool = False):
        filler = self.get_class_nnf(ce.get_filler(), negated)
        if negated:
            return OWLObjectSomeValuesFrom(ce.get_property(), filler)
        return OWLObjectAllValuesFrom(ce.get_property(), filler)

    @get_class_nnf.register
    def _(self, ce: OWLObjectHasValue, negated: bool = False):
        return self.get_class_nnf(ce.as_some_values_from(), negated)

    @get_class_nnf.register
    def _(self, ce: OWLObjectMinCardinality, negated: bool = False):
        card = ce.get_cardinality()
        if negated:
            card = max(0, card - 1)
        filler = self.get_class_nnf(ce.get_filler(), negated=False)
        if negated:
            return OWLObjectMaxCardinality(card, ce.get_property(), filler)
        return OWLObjectMinCardinality(card, ce.get_property(), filler)

    @get_class_nnf.register
    def _(self, ce: OWLObjectExactCardinality, negated: bool = False):
        return self.get_class_nnf(ce.as_intersection_of_min_max(), negated)

    @get_class_nnf.register
    def _(self, ce: OWLObjectMaxCardinality, negated: bool = False):
        card = ce.get_cardinality()
        if negated:
            card = card + 1
        filler = self.get_class_nnf(ce.get_filler(), negated=False)
        if negated:
            return OWLObjectMinCardinality(card, ce.get_property(), filler)
        return OWLObjectMaxCardinality(card, ce.get_property(), filler)

    @get_class_nnf.register
    def _(self, ce: OWLObjectHasSelf, negated: bool = False):
        if negated:
            return ce.get_object_complement_of()
        return ce

    @get_class_nnf.register
    def _(self, ce: OWLObjectOneOf, negated: bool = False):
        union = ce.as_object_union_of()
        if isinstance(union, OWLObjectOneOf):
            if negated:
                return ce.get_object_complement_of()
            return ce
        return self.get_class_nnf(union, negated)

    @get_class_nnf.register
    def _(self, ce: OWLDataSomeValuesFrom, negated: bool = False):
        filler = self.get_class_nnf(ce.get_filler(), negated)
        if negated:
            return OWLDataAllValuesFrom(ce.get_property(), filler)
        return OWLDataSomeValuesFrom(ce.get_property(), filler)

    @get_class_nnf.register
    def _(self, ce: OWLDataAllValuesFrom, negated: bool = False):
        filler = self.get_class_nnf(ce.get_filler(), negated)
        if negated:
            return OWLDataSomeValuesFrom(ce.get_property(), filler)
        return OWLDataAllValuesFrom(ce.get_property(), filler)

    @get_class_nnf.register
    def _(self, ce: OWLDatatypeRestriction, negated: bool = False):
        if negated:
            return OWLDataComplementOf(ce)
        return ce

    @get_class_nnf.register
    def _(self, ce: OWLDatatype, negated: bool = False):
        if negated:
            return OWLDataComplementOf(ce)
        return ce

    @get_class_nnf.register
    def _(self, ce: OWLDataComplementOf, negated: bool = False):
        return self.get_class_nnf(ce.get_data_range(), not negated)

    @get_class_nnf.register
    def _(self, ce: OWLDataHasValue, negated: bool = False):
        return self.get_class_nnf(ce.as_some_values_from(), negated)

    @get_class_nnf.register
    def _(self, ce: OWLDataOneOf, negated: bool = False):
        if len(list(ce.values())) == 1:
            if negated:
                return OWLDataComplementOf(ce)
            return ce
        union = OWLDataUnionOf([OWLDataOneOf(v) for v in ce.values()])
        return self.get_class_nnf(union, negated)

    @get_class_nnf.register
    def _(self, ce: OWLDataIntersectionOf, negated: bool = False):
        ops = map(lambda _: self.get_class_nnf(_, negated),
                  _sort_by_ordered_owl_object(ce.operands()))
        if negated:
            return OWLDataUnionOf(ops)
        return OWLDataIntersectionOf(ops)

    @get_class_nnf.register
    def _(self, ce: OWLDataUnionOf, negated: bool = False):
        ops = map(lambda _: self.get_class_nnf(_, negated),
                  _sort_by_ordered_owl_object(ce.operands()))
        if negated:
            return OWLDataIntersectionOf(ops)
        return OWLDataUnionOf(ops)

    @get_class_nnf.register
    def _(self, ce: OWLDataExactCardinality, negated: bool = False):
        return self.get_class_nnf(ce.as_intersection_of_min_max(), negated)

    @get_class_nnf.register
    def _(self, ce: OWLDataMinCardinality, negated: bool = False):
        card = ce.get_cardinality()
        if negated:
            card = max(0, card - 1)
        filler = self.get_class_nnf(ce.get_filler(), negated=False)
        if negated:
            return OWLDataMaxCardinality(card, ce.get_property(), filler)
        return OWLDataMinCardinality(card, ce.get_property(), filler)

    @get_class_nnf.register
    def _(self, ce: OWLDataMaxCardinality, negated: bool = False):
        card = ce.get_cardinality()
        if negated:
            card = card + 1
        filler = self.get_class_nnf(ce.get_filler(), negated=False)
        if negated:
            return OWLDataMinCardinality(card, ce.get_property(), filler)
        return OWLDataMaxCardinality(card, ce.get_property(), filler)


def get_top_level_cnf(ce: OWLClassExpression) -> OWLClassExpression:
    """Convert a class expression into Top-Level Conjunctive Normal Form. Operands will be sorted.

    Args:
        ce: Class Expression.

    Returns:
        Class Expression in Top-Level Conjunctive Normal Form.
        """
    c = _get_top_level_form(ce.get_nnf(), OWLObjectUnionOf, OWLObjectIntersectionOf)
    return combine_nary_expressions(c)


def get_top_level_dnf(ce: OWLClassExpression) -> OWLClassExpression:
    """Convert a class expression into Top-Level Disjunctive Normal Form. Operands will be sorted.

    Args:
        ce: Class Expression.

    Returns:
        Class Expression in Top-Level Disjunctive Normal Form.
        """
    c = _get_top_level_form(ce.get_nnf(), OWLObjectIntersectionOf, OWLObjectUnionOf)
    return combine_nary_expressions(c)


def _get_top_level_form(ce: OWLClassExpression,
                        type_a: Type[OWLNaryBooleanClassExpression],
                        type_b: Type[OWLNaryBooleanClassExpression]) -> OWLClassExpression:
    """ Transforms a class expression (that's already in NNF) into Top-Level Conjunctive/Disjunctive Normal Form.
    Here type_a specifies the operand which should be distributed inwards over type_b.

    Conjunctive Normal form:
        type_a = OWLObjectUnionOf
        type_b = OWLObjectIntersectionOf
    Disjunctive Normal form:
        type_a = OWLObjectIntersectionOf
        type_b = OWLObjectUnionOf
    """

    def distributive_law(a: OWLClassExpression, b: OWLNaryBooleanClassExpression) -> OWLNaryBooleanClassExpression:
        return type_b(type_a([a, op]) for op in b.operands())

    if isinstance(ce, type_a):
        ce = combine_nary_expressions(ce)
        if not isinstance(ce, type_a):
            return ce
        ce = cast(OWLNaryBooleanClassExpression, ce)
        type_b_exprs = [op for op in ce.operands() if isinstance(op, type_b)]
        non_type_b_exprs = [op for op in ce.operands() if not isinstance(op, type_b)]
        if not len(type_b_exprs):
            return ce

        if len(non_type_b_exprs):
            expr = non_type_b_exprs[0] if len(non_type_b_exprs) == 1 \
                else type_a(non_type_b_exprs)
            expr = distributive_law(expr, type_b_exprs[0])
        else:
            expr = type_b_exprs[0]

        if len(type_b_exprs) == 1:
            return _get_top_level_form(expr, type_a, type_b)

        for type_b_expr in type_b_exprs[1:]:
            expr = distributive_law(type_b_expr, expr)
        return _get_top_level_form(expr, type_a, type_b)
    elif isinstance(ce, type_b):
        return type_b(_get_top_level_form(op, type_a, type_b) for op in ce.operands())
    elif isinstance(ce, OWLClassExpression):
        return ce
    else:
        raise ValueError('Top-Level CNF/DNF only applicable on class expressions', ce)
