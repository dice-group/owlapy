"""Syntactic simplification of OWLClassExpression (redundancy removal, factorization, absorption)."""
from copy import copy
from functools import singledispatchmethod
from itertools import repeat
from typing import TypeVar, Union, cast

from owlapy.class_expression import (
    OWLCardinalityRestriction,
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
from owlapy.owl_individual import OWLNamedIndividual

from ..owl_data_ranges import OWLDataComplementOf, OWLDataIntersectionOf, OWLDataRange, OWLDataUnionOf
from ..owl_datatype import OWLDatatype
from ..owl_literal import OWLLiteral
from ..owl_property import OWLDataProperty, OWLObjectInverseOf, OWLObjectProperty
from ..vocab import OWLFacet
from .nnf import get_top_level_dnf
from .ordering import ConceptOperandSorter, _sort_by_ordered_owl_object, combine_nary_expressions

_O = TypeVar('_O')  #:


def get_remaining(original_set, common_part, type_b):
    """Used in factorization function 'factor_nary_expression'."""
    remaining = original_set - common_part
    if len(remaining) == 1:
        remaining = remaining.pop()
    elif len(remaining) > 1:
        remaining = type_b(remaining)
    else:
        remaining = None
    return remaining

def factor_nary_expression(expr: Union[OWLObjectIntersectionOf, OWLObjectUnionOf], transform_to_dnf_on_first_iteration = False):
    """Factor a common operand from a top-level Union (⊔) or Intersection (⊓) if possible. This
    factorization takes into consideration only boolean construction. Restrictions are not considered (use CESimplifier)
    for that."""

    assert(isinstance(expr, Union[OWLObjectIntersectionOf, OWLObjectUnionOf])), "Expression must be an OWLObjectIntersectionOf or an OWLObjectUnionOf"

    if transform_to_dnf_on_first_iteration:
        expr = get_top_level_dnf(expr)

    if isinstance(expr, OWLObjectUnionOf):
        type_a = OWLObjectUnionOf
        type_b = OWLObjectIntersectionOf
    else:
        type_a = OWLObjectIntersectionOf
        type_b = OWLObjectUnionOf

    if not isinstance(expr, type_a) and not isinstance(expr, type_b):
        # sometime when the get_top_level_dnf will remove duplicates (due to its processing) and we are left
        # with a single expression (no nary expression) so we just return it.
        return expr

    ce = cast(OWLNaryBooleanClassExpression, combine_nary_expressions(expr))
    type_b_nary_expressions = {op for op in ce.operands() if isinstance(op, type_b)}
    non_type_b_nary_expressions = {op for op in ce.operands() if not isinstance(op, type_b)}

    ce_no_repetitions = type_a([*type_b_nary_expressions, *non_type_b_nary_expressions])
    if ce != ce_no_repetitions:
        # if repeated operands are found just continue factoring the expression without repeated operands
        return factor_nary_expression(ce_no_repetitions)

    if len(non_type_b_nary_expressions) and len(type_b_nary_expressions):
        # check if a non-nary expression occurs in any of the nary expression then omit the nary expression and continue
        # or return the non-nary expression if these were the only 2 operands left
        for i in non_type_b_nary_expressions:
            for j in type_b_nary_expressions:
                j_op = set(j.operands())
                if i in j_op:
                    ce_op = set(ce.operands())
                    if len(ce_op) == 2:
                        return i
                    else:
                        ce_op.remove(j)
                        return factor_nary_expression(type_a(ce_op))

    if len(type_b_nary_expressions) < 2:
        if len(type_b_nary_expressions) == 1:
            simplifier = CESimplifier()
            # if we are left with only 1 nary expression of type_b then run factor_expression for its operands
            # where type_a and type_b switch places to factorize any nary expression of type_b left there.
            ce = type_a({*non_type_b_nary_expressions, *[factor_nary_expression(exp) for exp in type_b_nary_expressions]})
            # Sometimes we need another step of simplification before returning the result because the dnf can leave the
            # expression in a state where simplification can cover what factorization could not.
            # For example: {a ⊔ b} ⊔ ({b ⊔ c} ⊓ D) should return {a ⊔ b} ⊔ (D ⊓ {c}) but if not simplified it would
            # return {a} ⊔ {b} ⊔ (D ⊓ {c})  which is not as compact.
            s = set(map(simplifier._simplify, set(ce.operands()), repeat(ce)))
            return type_a(s)
        # if no nary expression is left just return ce
        return ce
    else:
        for i in type_b_nary_expressions:
            # we take each nary expression of type_b in the operands of ce and see if any other operand of the same
            # type has any common expression. The moment we find a common expression we perform a factorization for
            # those 2 nary expressions and depending on the length of the operands to process we decide whether to
            # return the factorization or go through another cycle of factorization using the union of the
            # localized factorization with what's left from other operands.
            i_op = set(i.operands())
            for j in copy(type_b_nary_expressions) - {i}:
                j_op = set(j.operands())
                common = i_op.intersection(j_op)
                if len(common):
                    remaining_i = get_remaining(i_op, common, type_b)
                    remaining_j = get_remaining(j_op, common, type_b)
                    if remaining_i and remaining_j:
                        # if more than 1 remaining, put them in a type_a expression
                        localized_factorization = type_b({*common, type_a([remaining_i, remaining_j])})
                    else:
                        # if 1 remaining, rule it out. The way this function is structured make this line
                        # safe because it only omits redundant remains.
                        localized_factorization = type_b(common)
                    if len(type_b_nary_expressions) == 2 and len(non_type_b_nary_expressions) == 0:
                        return combine_nary_expressions(localized_factorization)
                    elif len(type_b_nary_expressions) == 2 and len(non_type_b_nary_expressions) > 0:
                        return combine_nary_expressions(type_a([localized_factorization,*non_type_b_nary_expressions]))
                    else:
                        type_b_nary_expressions_without_i_j = copy(type_b_nary_expressions) - {i,j}
                        return factor_nary_expression(type_a({*type_b_nary_expressions_without_i_j,*non_type_b_nary_expressions, localized_factorization}))
    if len(type_b_nary_expressions):
        # if we reach this point we make a last check to see if there is any nary expression of type_b in ce and process
        # each of them before returning the type_a object.
        return type_a({*non_type_b_nary_expressions, *[factor_nary_expression(exp) for exp in type_b_nary_expressions]})

    # no nary expression of type_b? -> just return ce, nothing to do here
    return ce

def _factor_negation_outof_oneofs(ce: Union[OWLObjectIntersectionOf, OWLObjectUnionOf]):
    """Factor negation for objectOneOf expression
        E.g. #1: ¬{a} ⊓ ¬{b} ⊓ ¬{c}  => ¬({a} ⊔ {b} ⊔ {c}) => ¬{a ⊔ b ⊔ c}
        E.g. #2:  ¬{a} ⊔ ¬{b} => ¬({a} ⊓ {b}) => ¬(⊥) => ⊤    // considering that a != b

        Note: We consider Unique Name Assumption (UNA) for such simplifications but otherwise the simplification in
        example 2 is not semantically valid unless proven that a != b.
        P.S: Comparing individuals will require a reasoner. We will leave that when implementing the semantic
        simplifier.
    """
    nary_exp = []
    neg_one_of = []
    others = []
    for op in ce.operands():
        if isinstance(op, OWLObjectUnionOf) or isinstance(op,OWLObjectIntersectionOf):
            nary_exp.append(_factor_negation_outof_oneofs(op))
        elif isinstance(op, OWLObjectComplementOf) and isinstance(op.get_operand(), OWLObjectOneOf):
            neg_one_of.append(op)
        else:
            others.append(op)

    if len(neg_one_of) > 1:
        simplifier = CESimplifier()
        if isinstance(ce, OWLObjectIntersectionOf):
            simplified_oofs = simplifier.simplify(OWLObjectUnionOf([nof.get_operand() for nof in neg_one_of]))
        else: # isinstance(ce, OWLObjectUnionOf)
            simplified_oofs = simplifier.simplify(OWLObjectIntersectionOf([nof.get_operand() for nof in neg_one_of]))

        if simplified_oofs == OWLNothing:
            if len(others) + len(nary_exp) > 1:
                return type(ce)([*others, *nary_exp])
            elif len(others):
                return others.pop()
            elif len(nary_exp):
                return nary_exp.pop()
            else:
                return OWLThing

        if len(others) + len(nary_exp) >= 1:
            return type(ce)([OWLObjectComplementOf(simplified_oofs), *nary_exp, *others])
        else:
            return OWLObjectComplementOf(simplified_oofs)
    return type(ce)([*neg_one_of, *others, *nary_exp])


class CESimplifier:
    """Simplifies OWLClassExpression by removing redundant operands and normalizing the structure.
        Simplifications include:
        - Merging redundant cardinality restrictions
        - Merging redundant existential restrictions
        - Normalizing union and intersection of class expressions
        - Absorption of redundant class expressions
        - Converting to negation normal form (NNF)
        - and more...

        Note: This simplifier follows Unique Name Assumption (UNA) meaning that every class/individual/property is
        unique as long as its name is unique.
    """

    # TODO AB: This simplifier considers only syntactic simplifications (CWA). It can be extended to consider semantic
    #          simplifications. This will require passing a reasoner to access TBox information.
    #          Implementation idea: you can either set it as an option here or create a new class that extends this one.

    # TODO AB: Consider scenarios when cardinality restrictions contradict each other and return OWLNothing. Rare
    #          scenario but possible.

    sorter = ConceptOperandSorter()

    def simplify(self, o: OWLClassExpression) -> OWLClassExpression:
        return self._simplify(o, None)


    def _merge_card_r_with_same_body(self, restriction, nary_ce = None):
        # Check for card restrictions that have the same property and filler and remove redundant restrictions
        # by merging their cardinality depending on the type of nary expression we are dealing.
        # E.g.:
        # (> 1 r.A) ⊔ (> 2 r.A) ≡ > 1 r.A
        # (> 1 r.A) ⊓ (> 2 r.A) ≡ > 2 r.A

        operands = set(nary_ce.operands())
        same_prop_and_filler = []
        for op in operands:
            if (isinstance(op, type(restriction))
                    and op.get_filler() == restriction.get_filler()
                    and op.get_property() == restriction.get_property()):
                same_prop_and_filler.append(op)
        same_prop_and_filler_vals = [p.get_cardinality() for p in same_prop_and_filler]
        max_card = max(same_prop_and_filler_vals)
        min_card = min(same_prop_and_filler_vals)
        cardinality = restriction.get_cardinality()
        if isinstance(restriction, (OWLObjectMinCardinality, OWLDataMinCardinality)):
            if isinstance(nary_ce,  OWLObjectIntersectionOf):
                cardinality = max_card
            if isinstance(nary_ce, OWLObjectUnionOf):
                cardinality = min_card
        if isinstance(restriction, (OWLObjectMaxCardinality, OWLDataMaxCardinality)):
            if isinstance(nary_ce, OWLObjectIntersectionOf):
                cardinality = min_card
            # if nary_ce is an intersection then we leave cardinality as it is
            if isinstance(nary_ce, OWLObjectUnionOf):
                cardinality = max_card
        # if isinstance(restriction, OWLObjectExactCardinality):
            # TODO AB: implement solution when we have exact cardinality restrictions. Need to take in consideration
            #          scenarios when the cardinality in this kind of restrictions is subsumed by min/max cardinality restriction.
            #          Immediate idea includes a lot of "ifs" which does not feel right. Find a better way if possible.


        return type(restriction)(cardinality=cardinality,
                                 property=restriction.get_property(),
                                 filler=self._simplify(restriction.get_filler()))

    def _process_cardinality_restriction(self, restriction, nary_ce = None):
        # Check for card restrictions that share the same cardinality and property.
        # They can be simplified into a single card restriction with a merged filler,
        # but only for scenarios where the equivalence actually holds:
        #
        # For OWLObjectMinCardinality / OWLDataMinCardinality with cardinality = 1 in a union:
        #   (≥ 1 r.A) ⊔ (≥ 1 r.B) ≡ ≥ 1 r.(A ⊔ B)   ← valid (equivalent to ∃r)
        if isinstance(nary_ce, OWLObjectUnionOf):
            # Only apply filler merging for min-cardinality restrictions with cardinality == 1
            if (isinstance(restriction, (OWLObjectMinCardinality, OWLDataMinCardinality))
                    and restriction.get_cardinality() == 1):
                operands = set(nary_ce.operands())
                same_root = []
                for op in operands:
                    if (isinstance(op, type(restriction))
                            and op.get_cardinality() == restriction.get_cardinality()
                            and op.get_property() == restriction.get_property()):
                        same_root.append(op)
                if not len(same_root) == 1:
                    fillers = _sort_by_ordered_owl_object([p.get_filler() for p in same_root])
                    if isinstance(list(fillers)[0], OWLDataRange):
                        return type(restriction)(cardinality=restriction.get_cardinality(),
                                                 property=restriction.get_property(),
                                                 filler=self._simplify(OWLDataUnionOf(fillers)))
                    return type(restriction)(cardinality=restriction.get_cardinality(),
                                             property=restriction.get_property(),
                                             filler=self._simplify(OWLObjectUnionOf(fillers)))
        return type(restriction)(cardinality=restriction.get_cardinality(),
                                 property=restriction.get_property(),
                                 filler=self._simplify(restriction.get_filler(), None))

    def _process_quantified_restriction(self, restriction, nary_ce=None):
        # We can factorize the quantified restriction that share the same property by merging their fillers,
        # following the rules of description logics.
        # E.g.:
        # ∀r.A ⊓ ∀r.B ≡ ∀r.(A ⊓ B)
        # ∃r.A ⊔ ∃r.B ≡ ∃r.(A ⊔ B)
        if nary_ce is not None:
            operands = set(nary_ce.operands())
            same_root = []
            for op in operands:
                if isinstance(op, type(restriction)) and op.get_property() == restriction.get_property():
                    same_root.append(op)
            if not len(same_root) == 1:
                fillers = _sort_by_ordered_owl_object([p.get_filler() for p in same_root])
                if isinstance(nary_ce, OWLObjectUnionOf) and (isinstance(restriction, OWLObjectSomeValuesFrom) or
                                                              isinstance(restriction, OWLDataSomeValuesFrom)):
                    if isinstance(list(fillers)[0], OWLDataRange):
                        # Union of data ranges should be treated as OWLDataUnionOf
                        return type(restriction)(property=restriction.get_property(),
                                                 filler=self._simplify(OWLDataUnionOf(fillers)))
                    return type(restriction)(property=restriction.get_property(),
                                             filler=self._simplify(OWLObjectUnionOf(fillers)))
                if isinstance(nary_ce, OWLObjectIntersectionOf) and (isinstance(restriction, OWLObjectAllValuesFrom)
                                                                     or isinstance(restriction, OWLDataAllValuesFrom)):
                    if isinstance(list(fillers)[0], OWLDataRange):
                        # Intersection of data ranges should be treated as OWLDataIntersectionOf
                        return type(restriction)(property=restriction.get_property(),
                                                 filler=self._simplify(OWLDataIntersectionOf(fillers)))
                    return type(restriction)(property=restriction.get_property(),
                                             filler=self._simplify(OWLObjectIntersectionOf(fillers)))
        return type(restriction)(property=restriction.get_property(), filler=self._simplify(restriction.get_filler()))

    def _simplify_existential_restrictions_with_oneof_filler(self, e, nary_ce):
        s = set(e.get_filler().individuals())
        if isinstance(nary_ce, OWLObjectUnionOf):
            for op in nary_ce.operands():
                if isinstance(op, OWLObjectHasValue) and op.get_property() == e.get_property():
                    s.add(op.get_filler())
        return OWLObjectSomeValuesFrom(property=e.get_property(), filler=OWLObjectOneOf(s))

    @singledispatchmethod
    def _simplify(self, o: _O, nary_ce) -> _O:
        raise NotImplementedError(o)

    @_simplify.register
    def _(self, o: OWLClass, nary_ce = None) -> OWLClass:
        return o

    @_simplify.register
    def _(self, p: OWLObjectProperty, nary_ce = None) -> OWLObjectProperty:
        return p

    @_simplify.register
    def _(self, p: OWLDataProperty, nary_ce = None) -> OWLDataProperty:
        return p

    @_simplify.register
    def _(self, i: OWLNamedIndividual, nary_ce = None) -> OWLNamedIndividual:
        return i

    @_simplify.register
    def _(self, i: OWLLiteral, nary_ce = None) -> OWLLiteral:
        return i

    @_simplify.register
    def _(self, n: OWLDatatype, nary_ce = None) -> OWLDatatype:
        return n

    @_simplify.register
    def _(self, e: OWLObjectSomeValuesFrom, nary_ce = None) -> OWLObjectSomeValuesFrom:
        e = self._process_quantified_restriction(e, nary_ce)
        if isinstance(e.get_filler(), OWLObjectOneOf):
            e = self._simplify_existential_restrictions_with_oneof_filler(e, nary_ce)
        return e

    @_simplify.register
    def _(self, e: OWLObjectAllValuesFrom, nary_ce = None) -> OWLObjectAllValuesFrom:
        e = self._process_quantified_restriction(e, nary_ce)
        return e

    @_simplify.register
    def _(self, c: OWLObjectUnionOf, nary_ce = None) -> OWLClassExpression:
        c_c = combine_nary_expressions(c)
        if c != c_c:
            return self._simplify(c_c)
        if nary_ce is not None:
            # Absorption law (e.g. A ⊔ (A ⊓ B) = A )
            nary_ce_operands = set(nary_ce.operands())
            c_operands = set(c.operands())
            intersection = nary_ce_operands.intersection(c_operands)
            if len(intersection) > 0:
                # We just pop the first element because this union (c) that we are currently processing will be absorbed
                # or in simple terms, completely removed. The returned ce will not affect the nary_ce concept because
                # it will be removed as a duplicate ce when the outer recursion cycle reaches the s = set(...) line.
                # E.g A ⊔ (A ⊓ B) ==> s = {A, {A,(A ⊓ B)}.intersect{A,B}.pop()} ==> s = {A, A} = {A}
                return intersection.pop()

        # simplify each operand, put results in a set to remove duplicates
        s = set(map(self._simplify, set(c.operands()), repeat(c)))
        if OWLThing in s:
            return OWLThing
        if len(s) == 1:
            return s.pop()
        if OWLNothing in s:
            s = s - {OWLNothing}

        # Check if C and ¬C (C can be non-atomic) are both part of operands and apply the law of the excluded middle
        for el in copy(s):
            if isinstance(el, OWLObjectComplementOf) and el.get_operand() in s:
                s = s - {el, el.get_operand()}
                if len(s) == 0:
                    return OWLThing
                if len(s) == 1:
                    return s.pop()
                # return self._simplify(OWLObjectUnionOf(_sort_by_ordered_owl_object(s)))

        ce_to_return = combine_nary_expressions(OWLObjectUnionOf(_sort_by_ordered_owl_object(s)))
        if isinstance(ce_to_return, OWLObjectUnionOf):
            for op in ce_to_return.operands():
                # Simplify cardinality restrictions with same property and filler.
                # This has to be done here because _process_cardinality_restriction simplifies only restrictions with the
                # same prop and cardinality and it cannot do both at the same time.
                if isinstance(op, OWLCardinalityRestriction):
                    s = set(map(self._merge_card_r_with_same_body , set(r for r in ce_to_return.operands() if isinstance(r, OWLCardinalityRestriction)), repeat(ce_to_return)))
                    s = s.union(set(ce for ce in ce_to_return.operands() if not isinstance(ce, OWLCardinalityRestriction)))
                    if len(s) == 1:
                        return s.pop()
                    ce_to_return = combine_nary_expressions(OWLObjectUnionOf(_sort_by_ordered_owl_object(s)))
                    break
        if nary_ce is None and isinstance(ce_to_return, OWLObjectUnionOf): # check if we are at the root nary expression and apply factorization
            ce_to_return = self.sorter.sort(factor_nary_expression(ce_to_return, True))
            if isinstance(ce_to_return, OWLObjectUnionOf) or isinstance(ce_to_return, OWLObjectIntersectionOf):
                for op in ce_to_return.operands():
                    if isinstance(op, OWLObjectComplementOf) and isinstance(op.get_operand(), OWLObjectOneOf):
                        return self.sorter.sort(_factor_negation_outof_oneofs(ce_to_return))
        return ce_to_return

    @_simplify.register
    def _(self, c: OWLObjectIntersectionOf, nary_ce = None) -> OWLClassExpression:
        c_c = combine_nary_expressions(c)
        if c != c_c:
            return self._simplify(c_c)
        if nary_ce is not None:
            # Absorption law (e.g. A ⊓ (A ⊔ B) = A)
            nary_ce_operands = set(nary_ce.operands())
            c_operands = set(c.operands())
            intersection = nary_ce_operands.intersection(c_operands)
            if len(intersection) > 0:
                # We just pop the first element because this intersection (c) that we are currently processing will be
                # absorbed or in simple terms, completely removed. The returned ce will not affect the nary_ce concept
                # because it will be removed as a duplicate ce when the outer recursion cycle reaches the s = set(...)
                # line. E.g A ⊓ (A ⊔ B) ==> s = {A, {A,(A ⊓ B)}.intersect{A,B}.pop()} ==> s = {A, A} = {A}
                return intersection.pop()

        # simplify each operand, put results in a set to remove duplicates
        s = set(map(self._simplify, set(c.operands()), repeat(c)))
        if len(s) == 1:
            return s.pop()
        # if top concept is found in the operands, remove it because of the identity law (𝐶 ⊓ ⊤ ≡ 𝐶)
        if OWLThing in s:
            s = s - {OWLThing}
            if len(s) == 1:
                return s.pop()
        # if bottom concept is found in the operands, return bottom concept because of the domination law (𝐶 ⊓ ⊥ ≡ ⊥)
        if OWLNothing in s:
            return OWLNothing

        # Check if C and ¬C are both part of operands and apply the law of non-contradiction
        for el in copy(s):
            if isinstance(el, OWLObjectComplementOf) and el.get_operand() in s:
                s = s - {el, el.get_operand()}
                s.add(OWLNothing)
                if len(s) == 1:
                    return OWLNothing
                return self._simplify(OWLObjectIntersectionOf(_sort_by_ordered_owl_object(s)))

        # the following line can remove duplicates and return a type other than OWLObjectIntersectionOf, so we need to
        # check below if we are still left with an OWLObjectIntersectionOf.
        ce_to_return = combine_nary_expressions(OWLObjectIntersectionOf(_sort_by_ordered_owl_object(s)))

        if isinstance(ce_to_return, OWLObjectIntersectionOf):
            for op in ce_to_return.operands():
                # Simplify cardinality restrictions with same property and filler.
                # This has to be done here because _process_cardinality_restriction simplifies only restrictions with the
                # same prop and cardinality, and it cannot do both at the same time.
                if isinstance(op, OWLCardinalityRestriction):
                    s = set(map(self._merge_card_r_with_same_body , set(r for r in ce_to_return.operands() if isinstance(r, OWLCardinalityRestriction)), repeat(ce_to_return)))
                    s = s.union(set(ce for ce in ce_to_return.operands() if not isinstance(ce, OWLCardinalityRestriction)))
                    if len(s) == 1:
                        return s.pop()
                    ce_to_return = combine_nary_expressions(OWLObjectIntersectionOf(_sort_by_ordered_owl_object(s)))
                    break
        if nary_ce is None and isinstance(ce_to_return, OWLObjectIntersectionOf): # check if we are at the root nary expression and apply factorization
            ce_to_return = self.sorter.sort(factor_nary_expression(ce_to_return, True))
            if isinstance(ce_to_return, OWLObjectUnionOf) or isinstance(ce_to_return, OWLObjectIntersectionOf):
                for op in ce_to_return.operands():
                    if isinstance(op, OWLObjectComplementOf) and isinstance(op.get_operand(), OWLObjectOneOf):
                        return self.sorter.sort(_factor_negation_outof_oneofs(ce_to_return))
        return ce_to_return

    @_simplify.register
    def _(self, n: OWLObjectComplementOf, nary_ce = None) -> OWLClassExpression:
        nnnf = n.get_nnf()
        if not isinstance(nnnf, OWLObjectComplementOf):
            return self._simplify(nnnf)
        return nnnf

    @_simplify.register
    def _(self, p: OWLObjectInverseOf, nary_ce = None) -> OWLObjectInverseOf:
        return p

    @_simplify.register
    def _(self, r: OWLObjectMinCardinality, nary_ce = None) -> OWLObjectMinCardinality:
        return self._process_cardinality_restriction(r, nary_ce)

    @_simplify.register
    def _(self, r: OWLObjectExactCardinality, nary_ce = None) -> OWLObjectExactCardinality:
        return self._process_cardinality_restriction(r, nary_ce)

    @_simplify.register
    def _(self, r: OWLObjectMaxCardinality, nary_ce = None) -> OWLObjectMaxCardinality:
        return self._process_cardinality_restriction(r, nary_ce)

    @_simplify.register
    def _(self, r: OWLObjectHasSelf, nary_ce = None) -> OWLObjectHasSelf:
        return r

    @_simplify.register
    def _(self, r: OWLObjectHasValue, nary_ce = None) -> Union[OWLObjectHasValue, OWLObjectSomeValuesFrom]:
        r_prop = r.get_property()
        if isinstance(nary_ce, OWLObjectUnionOf):
            nary_ce_op_without_r = set(nary_ce.operands()) - {r}
            ohvs = []
            for op in nary_ce_op_without_r:
                # get all expressions that have the same property and the filler is either an individual or a set of individuals
                if (isinstance(op, OWLObjectHasValue) and op.get_property() == r_prop) or \
                    (isinstance(op, OWLObjectSomeValuesFrom) and op.get_property() == r_prop and isinstance(op.get_filler(),OWLObjectOneOf)):
                    ohvs.append(op)
            if len(ohvs) > 0:
                s = {r.get_filler()}
                # merge all fillers of hasValue and someValuesFrom (if the filler is a oneOf) into a single someValuesFrom with a oneOf filler
                for ohv in ohvs:
                    if isinstance(ohv, OWLObjectHasValue):
                        s.add(ohv.get_filler())
                    if isinstance(ohv, OWLObjectSomeValuesFrom) and isinstance(ohv.get_filler(),OWLObjectOneOf):
                        s.update(ohv.get_filler().individuals())
                return OWLObjectSomeValuesFrom(property=r_prop, filler=OWLObjectOneOf(s))
        return r

    @_simplify.register
    def _(self, r: OWLObjectOneOf, nary_ce = None) -> OWLObjectOneOf:
        r_inds = set(r.individuals())
        if nary_ce is not None:
            # Absorb oneOfs from the nary expression.
            nary_ce_op_without_r = set(nary_ce.operands()) - {r}
            ooos = []
            for op in nary_ce_op_without_r:
                if isinstance(op, OWLObjectOneOf):
                    ooos.append(op)
            if len(ooos) > 0:
                if isinstance(nary_ce, OWLObjectUnionOf):
                    return OWLObjectOneOf(_sort_by_ordered_owl_object(r_inds.union({inds for ooo in ooos for inds in ooo.individuals()})))
                if isinstance(nary_ce, OWLObjectIntersectionOf):
                    s = r_inds.intersection(*(ooo.individuals() for ooo in ooos))
                    if len(s) == 0: # if intersection of multiple oneOfs is empty the expression is not satisfiable
                        return OWLNothing
                    return OWLObjectOneOf(_sort_by_ordered_owl_object(s))
        return OWLObjectOneOf(_sort_by_ordered_owl_object(r_inds))

    @_simplify.register
    def _(self, e: OWLDataSomeValuesFrom, nary_ce = None) -> OWLDataSomeValuesFrom:
        return self._process_quantified_restriction(e, nary_ce)

    @_simplify.register
    def _(self, e: OWLDataAllValuesFrom, nary_ce = None) -> OWLDataAllValuesFrom:
        return self._process_quantified_restriction(e, nary_ce)

    @_simplify.register
    def _(self, c: OWLDataUnionOf, nary_ce = None) -> OWLDataRange:
        c_c = combine_nary_expressions(c)
        if c != c_c:
            return self._simplify(c_c)
        s = set(map(self._simplify, set(c.operands()), repeat(c)))
        if len(s) == 1:
            return s.pop()
        return combine_nary_expressions(OWLDataUnionOf(_sort_by_ordered_owl_object(s)))

    @_simplify.register
    def _(self, c: OWLDataIntersectionOf, nary_ce = None) -> OWLDataRange:
        c_c = combine_nary_expressions(c)
        if c != c_c:
            return self._simplify(c_c)
        s = set(map(self._simplify, set(c.operands()), repeat(c)))
        if len(s) == 1:
            return s.pop()
        return combine_nary_expressions(OWLDataIntersectionOf(_sort_by_ordered_owl_object(s)))


    def datatype_restriction_inwards_simplification(self, n):
        # remove duplicated OWLFacetRestriction
        s = {r for r in n.get_facet_restrictions()}
        if len(s) == 1:
            return OWLDatatypeRestriction(n.get_datatype(), s)

        # remove redundant OWLFacetRestriction (that are already covered by another facet restriction)
        # multiple facet restrictions for a datatype restrictions are interpreted conjuctively
        for i in copy(s):
            for j in copy(s) - {i}:
                i_fc = i.get_facet()
                j_fc = j.get_facet()
                if i_fc == j_fc:
                    i_v = i.get_facet_value()._v
                    j_v = j.get_facet_value()._v
                    if i_fc == OWLFacet.MAX_EXCLUSIVE or i_fc == OWLFacet.MAX_INCLUSIVE or i_fc == OWLFacet.MAX_LENGTH:
                        if i_v <= j_v:
                            s.discard(j)
                        else:
                            s.discard(i)
                    elif i_fc == OWLFacet.MIN_EXCLUSIVE or i_fc == OWLFacet.MIN_INCLUSIVE or i_fc == OWLFacet.MIN_LENGTH:
                        if i_v <= j_v:
                            s.discard(i)
                        else:
                            s.discard(j)
                    elif i == OWLFacet.LENGTH and i_v == j_v:
                        s.discard(i)
        return OWLDatatypeRestriction(n.get_datatype(), s)

    @_simplify.register
    def _(self, n: OWLDatatypeRestriction, nary_ce=None) -> OWLDatatypeRestriction:
        if len(n.get_facet_restrictions()) > 1:  # check if it is a collection of OWLFacetRestriction
            n = self.datatype_restriction_inwards_simplification(n)
        fr = n.get_facet_restrictions()
        if len(fr) == 1 and nary_ce is not None:
            fr = fr[0]
            for ce in set(nary_ce.operands()) - {n}:
                if isinstance(ce, OWLDatatypeRestriction):
                    if n.get_datatype() == ce.get_datatype():
                        ce_fr = ce.get_facet_restrictions()
                        # todo: scenarios when len(ce_fr) > 1 are not covered but rarely a simplification can be made
                        if len(ce_fr) == 1 and fr.get_facet() == ce_fr[0].get_facet():
                            ce_fr = ce_fr[0]
                            i_v = fr.get_facet_value()._v
                            j_v = ce_fr.get_facet_value()._v
                            fr_fc = fr.get_facet()
                            if fr_fc == OWLFacet.MAX_EXCLUSIVE or fr_fc == OWLFacet.MAX_INCLUSIVE or fr_fc == OWLFacet.MAX_LENGTH:
                                if isinstance(nary_ce, OWLDataUnionOf):
                                    if i_v <= j_v:
                                        return ce
                                    else:
                                        return n
                                elif isinstance(nary_ce, OWLDataIntersectionOf):
                                    if i_v <= j_v:
                                        return n
                                    else:
                                        return ce
                            elif fr_fc == OWLFacet.MIN_EXCLUSIVE or fr_fc == OWLFacet.MIN_INCLUSIVE or fr_fc == OWLFacet.MIN_LENGTH:
                                if isinstance(nary_ce, OWLDataUnionOf):
                                    if i_v <= j_v:
                                        return n
                                    else:
                                        return ce
                                elif isinstance(nary_ce, OWLDataIntersectionOf):
                                    if i_v <= j_v:
                                        return ce
                                    else:
                                        return n
                            elif fr_fc == OWLFacet.LENGTH and i_v == j_v:
                                return n
        return n

    @_simplify.register
    def _(self, n: OWLDataComplementOf, nary_ce = None) -> OWLDataComplementOf:
        return n

    @_simplify.register
    def _(self, r: OWLDataMinCardinality, nary_ce = None) -> OWLDataMinCardinality:
        return self._process_cardinality_restriction(r, nary_ce)

    @_simplify.register
    def _(self, r: OWLDataExactCardinality, nary_ce = None) -> OWLDataExactCardinality:
        return self._process_cardinality_restriction(r, nary_ce)

    @_simplify.register
    def _(self, r: OWLDataMaxCardinality, nary_ce = None) -> OWLDataMaxCardinality:
        return self._process_cardinality_restriction(r, nary_ce)

    @_simplify.register
    def _(self, r: OWLDataHasValue, nary_ce = None) -> OWLDataHasValue:
        return r

    @_simplify.register
    def _(self, r: OWLDataOneOf, nary_ce = None) -> OWLDataOneOf:
        return OWLDataOneOf(_sort_by_ordered_owl_object(set(r.values())))


transformer = CESimplifier()

def simplify_class_expression(ce: OWLClassExpression) -> OWLClassExpression:
    """Simplify a class expression by removing redundant expressions and sorting operands."""
    return transformer.simplify(ce)
