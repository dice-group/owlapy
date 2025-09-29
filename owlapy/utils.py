"""Owlapy utils."""
from collections import Counter
from copy import copy
from itertools import repeat

from owlapy.owl_individual import OWLNamedIndividual
from sortedcontainers import SortedSet
from functools import singledispatchmethod, total_ordering
from typing import Iterable, List, Type, Callable, TypeVar, Generic, Tuple, cast, Optional, Union, overload, Protocol, \
    ClassVar, Set

from .meta_classes import HasIRI, HasFiller, HasCardinality, HasOperands
from .owl_literal import OWLLiteral
from .owl_property import OWLObjectInverseOf, OWLObjectProperty, OWLDataProperty
from owlapy.class_expression import OWLClassExpression, OWLClass, OWLObjectCardinalityRestriction, \
    OWLObjectComplementOf, OWLNothing, OWLRestriction, OWLThing, OWLObjectSomeValuesFrom, \
    OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality, OWLObjectHasSelf, \
    OWLDataMaxCardinality, OWLDataMinCardinality, OWLDataExactCardinality, OWLDataHasValue, \
    OWLDataAllValuesFrom, OWLDataSomeValuesFrom, OWLObjectAllValuesFrom, \
    OWLDataOneOf, OWLObjectIntersectionOf, \
    OWLDataCardinalityRestriction, OWLNaryBooleanClassExpression, OWLObjectUnionOf, \
    OWLObjectHasValue, OWLDatatypeRestriction, OWLFacetRestriction, OWLObjectOneOf, OWLQuantifiedObjectRestriction, \
    OWLCardinalityRestriction
from .owl_data_ranges import OWLDataComplementOf, OWLDataUnionOf, OWLDataIntersectionOf, OWLNaryDataRange, OWLDataRange, \
    OWLPropertyRange
from .owl_object import OWLObject
from .owl_datatype import OWLDatatype

import concurrent.futures

from .vocab import OWLFacet


def jaccard_similarity(set1, set2) -> float:
    """Calculate the Jaccard similarity between two sets.
    
    Args:
        set1: First set
        set2: Second set
        
    Returns:
        Jaccard similarity: intersection(set1, set2) / union(set1, set2)
    """
    if len(set1) == 0 and len(set2) == 0:
        return 1.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union


def f1_set_similarity(set1, set2) -> float:
    """Calculate the F1 score between two sets.
    
    Args:
        set1: First set (treated as ground truth)
        set2: Second set (treated as prediction)
        
    Returns:
        F1 score
    """
    if len(set1) == 0 and len(set2) == 0:
        return 1.0
    
    if len(set2) == 0:
        return 0.0
    
    true_positives = len(set1.intersection(set2))
    precision = true_positives / len(set2) if len(set2) > 0 else 0
    recall = true_positives / len(set1) if len(set1) > 0 else 0
    
    if precision + recall == 0:
        return 0.0
    
    return 2 * (precision * recall) / (precision + recall)

def run_with_timeout(func, timeout, args=(), **kwargs):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            result = future.result(timeout=timeout)
            return result
        except concurrent.futures.TimeoutError:
            return set()


def concept_reducer(concepts:Iterable, opt:Callable):
    """
    Reduces a set of concepts by applying a binary operation to each pair of concepts.

    Args:
        concepts (set): A set of concepts to be reduced.
        opt (function): A binary function that takes a pair of concepts and returns a single concept.

    Returns:
        set: A set containing the results of applying the binary operation to each pair of concepts.

    Example:
        >>> concepts = {1, 2, 3}
        >>> opt = lambda x: x[0] + x[1]
        >>> concept_reducer(concepts, opt)
        {2, 3, 4, 5, 6}

    Note:
        The operation `opt` should be commutative and associative to ensure meaningful reduction in the context of set operations.
    """
    result = set()
    for i in concepts:
        for j in concepts:
            result.add(opt((i, j)))
    return result

def concept_reducer_properties(
        concepts: Iterable, properties, cls: Callable = None, cardinality: int = 2
) -> Iterable[Union[OWLQuantifiedObjectRestriction, OWLObjectCardinalityRestriction]]:
    """
    Map a set of owl concepts and a set of properties into OWL Restrictions

    Args:
        concepts:
        properties:
        cls (Callable): An owl Restriction class
        cardinality: A positive Integer

    Returns: List of OWL Restrictions

    """
    assert isinstance(concepts, Iterable), "Concepts must be an Iterable"
    assert isinstance(properties, Iterable), "properties must be an Iterable"
    assert isinstance(cls, Callable), "cls must be an Callable"
    assert cardinality > 0
    result = set()
    for i in concepts:
        for j in properties:
            if cls == OWLObjectMinCardinality or cls == OWLObjectMaxCardinality:
                result.add(cls(cardinality=cardinality, property=j, filler=i))
                continue
            result.add(cls(j, i))
    return result


class OWLClassExpressionLengthMetric:
    """Length calculation of OWLClassExpression

    Args:
        class_length: Class: "C"
        object_intersection_length: Intersection: A ⨅ B
        object_union_length: Union: A ⨆ B
        object_complement_length: Complement: ¬ C
        object_some_values_length: Obj. Some Values: ∃ r.C
        object_all_values_length: Obj. All Values: ∀ r.C
        object_has_value_length: Obj. Has Value: ∃ r.{I}
        object_cardinality_length: Obj. Cardinality restriction: ≤n r.C
        object_has_self_length: Obj. Self restriction: ∃ r.Self
        object_one_of_length: Obj. One of: ∃ r.{X,Y,Z}
        data_some_values_length: Data Some Values: ∃ p.t
        data_all_values_length: Data All Values: ∀ p.t
        data_has_value_length: Data Has Value: ∃ p.{V}
        data_cardinality_length: Data Cardinality restriction: ≤n r.t
        object_property_length: Obj. Property: ∃ r.C
        object_inverse_length: Inverse property: ∃ r⁻.C
        data_property_length: Data Property: ∃ p.t
        datatype_length: Datatype: ^^datatype
        data_one_of_length: Data One of: ∃ p.{U,V,W}
        data_complement_length: Data Complement: ¬datatype
        data_intersection_length: Data Intersection: datatype ⨅ datatype
        data_union_length: Data Union: datatype ⨆ datatype
    """

    __slots__ = 'class_length', 'object_intersection_length', 'object_union_length', 'object_complement_length', \
                'object_some_values_length', 'object_all_values_length', 'object_has_value_length', \
                'object_cardinality_length', 'object_has_self_length', 'object_one_of_length', \
                'data_some_values_length', 'data_all_values_length', 'data_has_value_length', \
                'data_cardinality_length', 'object_property_length', 'object_inverse_length', 'data_property_length', \
                'datatype_length', 'data_one_of_length', 'data_complement_length', 'data_intersection_length', \
                'data_union_length'

    class_length: int
    object_intersection_length: int
    object_union_length: int
    object_complement_length: int
    object_some_values_length: int
    object_all_values_length: int
    object_has_value_length: int
    object_cardinality_length: int
    object_has_self_length: int
    object_one_of_length: int
    data_some_values_length: int
    data_all_values_length: int
    data_has_value_length: int
    data_cardinality_length: int
    object_property_length: int
    object_inverse_length: int
    data_property_length: int
    datatype_length: int
    data_one_of_length: int
    data_complement_length: int
    data_intersection_length: int
    data_union_length: int

    def __init__(self, *,
                 class_length: int,
                 object_intersection_length: int,
                 object_union_length: int,
                 object_complement_length: int,
                 object_some_values_length: int,
                 object_all_values_length: int,
                 object_has_value_length: int,
                 object_cardinality_length: int,
                 object_has_self_length: int,
                 object_one_of_length: int,
                 data_some_values_length: int,
                 data_all_values_length: int,
                 data_has_value_length: int,
                 data_cardinality_length: int,
                 object_property_length: int,
                 object_inverse_length: int,
                 data_property_length: int,
                 datatype_length: int,
                 data_one_of_length: int,
                 data_complement_length: int,
                 data_intersection_length: int,
                 data_union_length: int,
                 ):
        self.class_length = class_length
        self.object_intersection_length = object_intersection_length
        self.object_union_length = object_union_length
        self.object_complement_length = object_complement_length
        self.object_some_values_length = object_some_values_length
        self.object_all_values_length = object_all_values_length
        self.object_has_value_length = object_has_value_length
        self.object_cardinality_length = object_cardinality_length
        self.object_has_self_length = object_has_self_length
        self.object_one_of_length = object_one_of_length
        self.data_some_values_length = data_some_values_length
        self.data_all_values_length = data_all_values_length
        self.data_has_value_length = data_has_value_length
        self.data_cardinality_length = data_cardinality_length
        self.object_property_length = object_property_length
        self.object_inverse_length = object_inverse_length
        self.data_property_length = data_property_length
        self.datatype_length = datatype_length
        self.data_one_of_length = data_one_of_length
        self.data_complement_length = data_complement_length
        self.data_intersection_length = data_intersection_length
        self.data_union_length = data_union_length

    @staticmethod
    def get_default() -> 'OWLClassExpressionLengthMetric':
        return OWLClassExpressionLengthMetric(
            class_length=1,
            object_intersection_length=1,
            object_union_length=1,
            object_complement_length=1,
            object_some_values_length=1,
            object_all_values_length=1,
            object_has_value_length=2,
            object_cardinality_length=2,
            object_has_self_length=1,
            object_one_of_length=1,
            data_some_values_length=1,
            data_all_values_length=1,
            data_has_value_length=2,
            data_cardinality_length=2,
            object_property_length=1,
            object_inverse_length=2,
            data_property_length=1,
            datatype_length=1,
            data_one_of_length=1,
            data_complement_length=1,
            data_intersection_length=1,
            data_union_length=1,
        )

    # single dispatch is still not implemented in mypy, see https://github.com/python/mypy/issues/2904
    @singledispatchmethod
    def length(self, o: OWLObject) -> int:
        raise NotImplementedError

    @length.register
    def _(self, o: OWLClass) -> int:
        return self.class_length

    @length.register
    def _(self, p: OWLObjectProperty) -> int:
        return self.object_property_length

    @length.register
    def _(self, e: OWLObjectSomeValuesFrom) -> int:
        return self.object_some_values_length \
               + self.length(e.get_property()) \
               + self.length(e.get_filler())

    @length.register
    def _(self, e: OWLObjectAllValuesFrom) -> int:
        return self.object_all_values_length \
               + self.length(e.get_property()) \
               + self.length(e.get_filler())

    @length.register
    def _(self, c: OWLObjectUnionOf) -> int:
        length = -self.object_union_length
        for op in c.operands():
            length += self.length(op) + self.object_union_length

        return length

    @length.register
    def _(self, c: OWLObjectIntersectionOf) -> int:
        length = -self.object_intersection_length
        for op in c.operands():
            length += self.length(op) + self.object_intersection_length

        return length

    @length.register
    def _(self, n: OWLObjectComplementOf) -> int:
        return self.length(n.get_operand()) + self.object_complement_length

    @length.register
    def _(self, p: OWLObjectInverseOf) -> int:
        return self.object_inverse_length

    @length.register
    def _(self, e: OWLObjectCardinalityRestriction) -> int:
        return self.object_cardinality_length \
               + self.length(e.get_property()) \
               + self.length(e.get_filler())

    @length.register
    def _(self, s: OWLObjectHasSelf) -> int:
        return self.object_has_self_length + self.length(s.get_property())

    @length.register
    def _(self, v: OWLObjectHasValue) -> int:
        return self.object_has_value_length + self.length(v.get_property())

    @length.register
    def _(self, o: OWLObjectOneOf) -> int:
        return self.object_one_of_length

    @length.register
    def _(self, p: OWLDataProperty) -> int:
        return self.data_property_length

    @length.register
    def _(self, e: OWLDataSomeValuesFrom) -> int:
        return self.data_some_values_length \
               + self.length(e.get_property()) \
               + self.length(e.get_filler())

    @length.register
    def _(self, e: OWLDataAllValuesFrom) -> int:
        return self.data_all_values_length \
               + self.length(e.get_property()) \
               + self.length(e.get_filler())

    @length.register
    def _(self, e: OWLDataCardinalityRestriction) -> int:
        return self.data_cardinality_length \
               + self.length(e.get_property()) \
               + self.length(e.get_filler())

    @length.register
    def _(self, v: OWLDataHasValue) -> int:
        return self.data_has_value_length + self.length(v.get_property())

    @length.register
    def _(self, o: OWLDataOneOf) -> int:
        return self.data_one_of_length

    @length.register
    def _(self, n: OWLDatatypeRestriction) -> int:
        return iter_count(n.get_facet_restrictions())

    @length.register
    def _(self, n: OWLDataComplementOf) -> int:
        return self.data_complement_length + self.length(n.get_data_range())

    @length.register
    def _(self, c: OWLDataUnionOf) -> int:
        length = -self.data_union_length
        for op in c.operands():
            length += self.length(op) + self.data_union_length
        return length

    @length.register
    def _(self, c: OWLDataIntersectionOf) -> int:
        length = -self.data_intersection_length
        for op in c.operands():
            length += self.length(op) + self.data_intersection_length
        return length

    @length.register
    def _(self, t: OWLDatatype) -> int:
        return self.datatype_length


measurer = OWLClassExpressionLengthMetric.get_default()


def get_expression_length(ce: OWLClassExpression) -> int:
    return measurer.length(ce)


_N = TypeVar('_N')  #:
_O = TypeVar('_O')  #:


class EvaluatedDescriptionSet(Generic[_N, _O]):
    __slots__ = 'items', '_max_size', '_Ordering'

    items: 'SortedSet[_N]'
    _max_size: int
    _Ordering: Callable[[_N], _O]

    def __init__(self, ordering: Callable[[_N], _O], max_size: int = 10):
        self._max_size = max_size
        self._Ordering = ordering
        self.items = SortedSet(key=self._Ordering)

    def maybe_add(self, node: _N):
        if len(self.items) == self._max_size:
            worst = self.items[0]
            if self._Ordering(node) > self._Ordering(worst):
                self.items.pop(0)
                self.items.add(node)
                return True
        else:
            self.items.add(node)
            return True
        return False

    def clean(self):
        self.items.clear()

    def worst(self):
        return self.items[0]

    def best(self):
        return self.items[-1]

    def best_quality_value(self) -> float:
        return self.items[-1].quality

    def __iter__(self) -> Iterable[_N]:
        yield from reversed(self.items)


def _avoid_overly_redundand_operands(operands: List[_O], max_count: int = 2) -> List[_O]:
    _max_count = max_count
    r = []
    counts = Counter(operands)
    for op in sorted(operands, key=OrderedOWLObject):
        for _ in range(min(_max_count, counts[op])):
            r.append(op)
    return r


def _sort_by_ordered_owl_object(i: Iterable[_O]) -> Iterable[_O]:
    try:
        return sorted(i, key=OrderedOWLObject)
    except AttributeError:
        print(i)


class ConceptOperandSorter:
    # single dispatch is still not implemented in mypy, see https://github.com/python/mypy/issues/2904
    @singledispatchmethod
    def sort(self, o: _O) -> _O:
        raise NotImplementedError(o)

    @sort.register
    def _(self, o: OWLClass) -> OWLClass:
        return o

    @sort.register
    def _(self, p: OWLObjectProperty) -> OWLObjectProperty:
        return p

    @sort.register
    def _(self, p: OWLDataProperty) -> OWLDataProperty:
        return p

    @sort.register
    def _(self, i: OWLNamedIndividual) -> OWLNamedIndividual:
        return i

    @sort.register
    def _(self, i: OWLLiteral) -> OWLLiteral:
        return i

    @sort.register
    def _(self, e: OWLObjectSomeValuesFrom) -> OWLObjectSomeValuesFrom:
        t = OWLObjectSomeValuesFrom(property=e.get_property(), filler=self.sort(e.get_filler()))
        if t == e:
            return e
        else:
            return t

    @sort.register
    def _(self, e: OWLObjectAllValuesFrom) -> OWLObjectAllValuesFrom:
        t = OWLObjectAllValuesFrom(property=e.get_property(), filler=self.sort(e.get_filler()))
        if t == e:
            return e
        else:
            return t

    @sort.register
    def _(self, c: OWLObjectUnionOf) -> OWLObjectUnionOf:
        t = OWLObjectUnionOf(_sort_by_ordered_owl_object(c.operands()))
        if t == c:
            return c
        else:
            return t

    @sort.register
    def _(self, c: OWLObjectIntersectionOf) -> OWLObjectIntersectionOf:
        t = OWLObjectIntersectionOf(_sort_by_ordered_owl_object(c.operands()))
        if t == c:
            return c
        else:
            return t

    @sort.register
    def _(self, n: OWLObjectComplementOf) -> OWLObjectComplementOf:
        return n

    @sort.register
    def _(self, p: OWLObjectInverseOf) -> OWLObjectInverseOf:
        return p

    @sort.register
    def _(self, r: OWLObjectMinCardinality) -> OWLObjectMinCardinality:
        t = OWLObjectMinCardinality(cardinality=r.get_cardinality(), property=r.get_property(),
                                    filler=self.sort(r.get_filler()))
        if t == r:
            return r
        else:
            return t

    @sort.register
    def _(self, r: OWLObjectExactCardinality) -> OWLObjectExactCardinality:
        t = OWLObjectExactCardinality(cardinality=r.get_cardinality(), property=r.get_property(),
                                      filler=self.sort(r.get_filler()))
        if t == r:
            return r
        else:
            return t

    @sort.register
    def _(self, r: OWLObjectMaxCardinality) -> OWLObjectMaxCardinality:
        t = OWLObjectMaxCardinality(cardinality=r.get_cardinality(), property=r.get_property(),
                                    filler=self.sort(r.get_filler()))
        if t == r:
            return r
        else:
            return t

    @sort.register
    def _(self, r: OWLObjectHasSelf) -> OWLObjectHasSelf:
        return r

    @sort.register
    def _(self, r: OWLObjectHasValue) -> OWLObjectHasValue:
        return r

    @sort.register
    def _(self, r: OWLObjectOneOf) -> OWLObjectOneOf:
        t = OWLObjectOneOf(_sort_by_ordered_owl_object(r.individuals()))
        if t == r:
            return r
        else:
            return t

    @sort.register
    def _(self, e: OWLDataSomeValuesFrom) -> OWLDataSomeValuesFrom:
        t = OWLDataSomeValuesFrom(property=e.get_property(), filler=self.sort(e.get_filler()))
        if t == e:
            return e
        else:
            return t

    @sort.register
    def _(self, e: OWLDataAllValuesFrom) -> OWLDataAllValuesFrom:
        t = OWLDataAllValuesFrom(property=e.get_property(), filler=self.sort(e.get_filler()))
        if t == e:
            return e
        else:
            return t

    @sort.register
    def _(self, c: OWLDataUnionOf) -> OWLDataUnionOf:
        t = OWLDataUnionOf(_sort_by_ordered_owl_object(c.operands()))
        if t == c:
            return c
        else:
            return t

    @sort.register
    def _(self, c: OWLDataIntersectionOf) -> OWLDataIntersectionOf:
        t = OWLDataIntersectionOf(_sort_by_ordered_owl_object(c.operands()))
        if t == c:
            return c
        else:
            return t

    @sort.register
    def _(self, n: OWLDataComplementOf) -> OWLDataComplementOf:
        return n

    @sort.register
    def _(self, n: OWLDatatypeRestriction) -> OWLDatatypeRestriction:
        t = OWLDatatypeRestriction(n.get_datatype(), _sort_by_ordered_owl_object(n.get_facet_restrictions()))
        if t == n:
            return n
        else:
            return t

    @sort.register
    def _(self, d: OWLDatatype) -> OWLDatatype:
        return d

    @sort.register
    def _(self, r: OWLDataMinCardinality) -> OWLDataMinCardinality:
        t = OWLDataMinCardinality(cardinality=r.get_cardinality(), property=r.get_property(),
                                  filler=self.sort(r.get_filler()))
        if t == r:
            return r
        else:
            return t

    @sort.register
    def _(self, r: OWLDataExactCardinality) -> OWLDataExactCardinality:
        t = OWLDataExactCardinality(cardinality=r.get_cardinality(), property=r.get_property(),
                                    filler=self.sort(r.get_filler()))
        if t == r:
            return r
        else:
            return t

    @sort.register
    def _(self, r: OWLDataMaxCardinality) -> OWLDataMaxCardinality:
        t = OWLDataMaxCardinality(cardinality=r.get_cardinality(), property=r.get_property(),
                                  filler=self.sort(r.get_filler()))
        if t == r:
            return r
        else:
            return t

    @sort.register
    def _(self, r: OWLDataHasValue) -> OWLDataHasValue:
        return r

    @sort.register
    def _(self, n: OWLDataOneOf) -> OWLDataOneOf:
        t = OWLDataOneOf(_sort_by_ordered_owl_object(n.values()))
        if t == n:
            return n
        else:
            return t



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
        # Check for card restrictions that have the share the same cardinality and property.
        # They can be simplified into a single card restriction with a merged filler.
        # E.g.:
        # (> 1 r.A) ⊔ (> 1 r.B) ≡ > 1 r.(A ⊔ B)
        # (< 2 r.xsd:boolean) ⊔ (< 2 r.xsd:integer) ≡ < 2 r.(xsd:boolean ⊔ xsd:integer)
        if isinstance(nary_ce, OWLObjectUnionOf):
            operands = set(nary_ce.operands())
            same_root = []
            for op in operands:
                if (isinstance(op, type(restriction))
                        and op.get_cardinality() == restriction.get_cardinality()
                        and op.get_property() == restriction.get_property()):
                    same_root.append(op)
            if not len(same_root) == 1:
                fillers = _sort_by_ordered_owl_object([p.get_filler() for p in same_root])
                if isinstance(list(fillers)[0],OWLDataRange):
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
                if isinstance(op, OWLObjectHasValue):
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
        # Check if C and ¬C (C can be non-atomic) are both part of operands and apply the law of the excluded middle
        for el in copy(s):
            if isinstance(el, OWLObjectComplementOf) and el.get_operand() in s:
                s = s - {el, el.get_operand()}
                if len(s) == 0:
                    return OWLThing
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
        s.discard(OWLThing)
        if not s:
            return OWLThing
        if len(s) == 1:
            return s.pop()

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


class HasIndex(Protocol):
    """Interface for types with an index; this is used to group objects by type when sorting."""
    type_index: ClassVar[int]  #: index for this type. This is a sorting index for the types.

    def __eq__(self, other): ...


_HasIRI = TypeVar('_HasIRI', bound=HasIRI)  #:
_HasIndex = TypeVar('_HasIndex', bound=HasIndex)  #:
_O = TypeVar('_O')  #:
_Enc = TypeVar('_Enc')
_Con = TypeVar('_Con')
_K = TypeVar('_K')
_V = TypeVar('_V')


@total_ordering
class OrderedOWLObject:
    """Holder of OWL Objects that can be used for Python sorted.

    The Ordering is dependent on the type_index of the impl. classes recursively followed by all components of the
    OWL Object.

    Attributes:
        o: OWL object.
    """
    __slots__ = 'o', '_chain'

    o: _HasIndex  # o: Intersection[OWLObject, HasIndex]
    _chain: Optional[Tuple]

    # we are limited by https://github.com/python/typing/issues/213 # o: Intersection[OWLObject, HasIndex]
    def __init__(self, o: _HasIndex):
        """OWL Object holder with a defined sort order.

        Args:
            o: OWL Object.
        """
        self.o = o
        self._chain = None

    def _comparison_chain(self):
        if self._chain is None:
            c = [self.o.type_index]

            if isinstance(self.o, OWLRestriction):
                c.append(OrderedOWLObject(as_index(self.o.get_property())))
            if isinstance(self.o, OWLObjectInverseOf):
                c.append(self.o.get_named_property().str)
            if isinstance(self.o, HasFiller):
                c.append(OrderedOWLObject(self.o.get_filler()))
            if isinstance(self.o, HasCardinality):
                c.append(self.o.get_cardinality())
            if isinstance(self.o, HasOperands):
                c.append(tuple(map(OrderedOWLObject, self.o.operands())))
            if isinstance(self.o, HasIRI):
                c.append(self.o.str)
            if isinstance(self.o, OWLDataComplementOf):
                c.append(OrderedOWLObject(self.o.get_data_range()))
            if isinstance(self.o, OWLDatatypeRestriction):
                c.append((OrderedOWLObject(self.o.get_datatype()),
                          tuple(map(OrderedOWLObject, self.o.get_facet_restrictions()))))
            if isinstance(self.o, OWLFacetRestriction):
                c.append((self.o.get_facet().str, self.o.get_facet_value().get_literal()))
            if isinstance(self.o, OWLLiteral):
                c.append(self.o.get_literal())
            if len(c) == 1:
                raise NotImplementedError(type(self.o))

            self._chain = tuple(c)

        return self._chain

    def __lt__(self, other):
        if self.o.type_index < other.o.type_index:
            return True
        elif self.o.type_index > other.o.type_index:
            return False
        else:
            return self._comparison_chain() < other._comparison_chain()

    def __eq__(self, other):
        return self.o == other.o


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



@overload
def combine_nary_expressions(ce: OWLClassExpression) -> OWLClassExpression:
    ...


@overload
def combine_nary_expressions(ce: OWLDataRange) -> OWLDataRange:
    ...


def combine_nary_expressions(ce: OWLPropertyRange) -> OWLPropertyRange:
    """ Shortens an OWLClassExpression or OWLDataRange by combining all nested nary expressions of the same type.
    Operands will be sorted.

    E.g. OWLObjectUnionOf(A, OWLObjectUnionOf(C, B)) -> OWLObjectUnionOf(A, B, C).
    """

    if isinstance(ce, (OWLNaryBooleanClassExpression, OWLNaryDataRange)):
        expressions: Set[OWLPropertyRange] = set()
        for op in ce.operands():
            expr = combine_nary_expressions(op)
            if type(expr) is type(ce):
                expr = cast(Union[OWLNaryBooleanClassExpression, OWLNaryDataRange], expr)
                expressions.update(expr.operands())
            else:
                expressions.add(expr)
        if len(expressions) == 1:
            return expressions.pop()
        return type(ce)(_sort_by_ordered_owl_object(expressions))  # type: ignore
    elif isinstance(ce, OWLObjectComplementOf):
        return OWLObjectComplementOf(combine_nary_expressions(ce.get_operand()))
    elif isinstance(ce, OWLDataComplementOf):
        return OWLDataComplementOf(combine_nary_expressions(ce.get_data_range()))
    elif isinstance(ce, OWLObjectCardinalityRestriction):
        return type(ce)(ce.get_cardinality(), ce.get_property(), combine_nary_expressions(ce.get_filler()))
    elif isinstance(ce, OWLDataCardinalityRestriction):
        return type(ce)(ce.get_cardinality(), ce.get_property(), combine_nary_expressions(ce.get_filler()))
    elif isinstance(ce, (OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom)):
        return type(ce)(ce.get_property(), combine_nary_expressions(ce.get_filler()))
    elif isinstance(ce, (OWLDataSomeValuesFrom, OWLDataAllValuesFrom)):
        return type(ce)(ce.get_property(), combine_nary_expressions(ce.get_filler()))
    elif isinstance(ce, OWLObjectOneOf):
        return OWLObjectOneOf(_sort_by_ordered_owl_object(ce.operands()))
    elif isinstance(ce, OWLDataOneOf):
        return OWLDataOneOf(_sort_by_ordered_owl_object(ce.operands()))
    elif isinstance(ce, OWLPropertyRange):
        return ce
    else:
        raise ValueError(f'({ce}) is not an OWLObject.')


def iter_count(i: Iterable) -> int:
    """Count the number of elements in an iterable."""
    return sum(1 for _ in i)


def as_index(o: OWLObject) -> HasIndex:
    """Cast OWL Object to HasIndex."""
    i = cast(HasIndex, o)
    assert type(i).type_index
    return i


class LRUCache(Generic[_K, _V]):
    """Constants shares by all lru cache instances.

    Adapted from functools.lru_cache.

    Attributes:
        sentinel: Unique object used to signal cache misses.
        PREV: Name for the link field 0.
        NEXT: Name for the link field 1.
        KEY: Name for the link field 2.
        RESULT: Name for the link field 3.
    """

    sentinel = object()
    PREV, NEXT, KEY, RESULT = 0, 1, 2, 3  # names for the link fields

    def __init__(self, maxsize: Optional[int] = None):
        from _thread import RLock

        self.cache = {}
        self.hits = self.misses = 0
        self.full = False
        self.cache_get = self.cache.get  # bound method to lookup a key or return None
        self.cache_len = self.cache.__len__  # get cache size without calling len()
        self.lock = RLock()  # because linkedlist updates aren't threadsafe
        self.root = []  # root of the circular doubly linked list
        self.root[:] = [self.root, self.root, None, None]  # initialize by pointing to self
        self.maxsize = maxsize

    def __contains__(self, item: _K) -> bool:
        with self.lock:
            link = self.cache_get(item)
            if link is not None:
                self.hits += 1
                return True
            self.misses += 1
            return False

    def __getitem__(self, item: _K) -> _V:
        with self.lock:
            link = self.cache_get(item)
            if link is not None:
                # Move the link to the front of the circular queue
                link_prev, link_next, _key, result = link
                link_prev[LRUCache.NEXT] = link_next
                link_next[LRUCache.PREV] = link_prev
                last = self.root[LRUCache.PREV]
                last[LRUCache.NEXT] = self.root[LRUCache.PREV] = link
                link[LRUCache.PREV] = last
                link[LRUCache.NEXT] = self.root
                return result

    def __setitem__(self, key: _K, value: _V):
        with self.lock:
            if key in self.cache:
                # Getting here means that this same key was added to the
                # cache while the lock was released.  Since the link
                # update is already done, we need only return the
                # computed result and update the count of misses.
                pass
            elif self.full:
                # Use the old root to store the new key and result.
                oldroot = self.root
                oldroot[LRUCache.KEY] = key
                oldroot[LRUCache.RESULT] = value
                # Empty the oldest link and make it the new root.
                # Keep a reference to the old key and old result to
                # prevent their ref counts from going to zero during the
                # update. That will prevent potentially arbitrary object
                # clean-up code (i.e. __del__) from running while we're
                # still adjusting the links.
                self.root = oldroot[LRUCache.NEXT]
                oldkey = self.root[LRUCache.KEY]
                _oldresult = self.root[LRUCache.RESULT]  # noqa: F841
                self.root[LRUCache.KEY] = self.root[LRUCache.RESULT] = None
                # Now update the cache dictionary.
                del self.cache[oldkey]
                # Save the potentially reentrant cache[key] assignment
                # for last, after the root and links have been put in
                # a consistent state.
                self.cache[key] = oldroot
            else:
                # Put result in a new link at the front of the queue.
                last = self.root[LRUCache.PREV]
                link = [last, self.root, key, value]
                last[LRUCache.NEXT] = self.root[LRUCache.PREV] = self.cache[key] = link
                # Use the cache_len bound method instead of the len() function
                # which could potentially be wrapped in an lru_cache itself.
                if self.maxsize is not None:
                    self.full = (self.cache_len() >= self.maxsize)

    def cache_info(self):
        """Report cache statistics."""
        with self.lock:
            from collections import namedtuple
            return namedtuple("CacheInfo", ["hits", "misses", "maxsize", "currsize"])(
                self.hits, self.misses, self.maxsize, self.cache_len())

    def cache_clear(self):
        """Clear the cache and cache statistics."""
        with self.lock:
            self.cache.clear()
            self.root[:] = [self.root, self.root, None, None]
            self.hits = self.misses = 0
            self.full = False


transformer = CESimplifier()

def simplify_class_expression(ce: OWLClassExpression) -> OWLClassExpression:
    """Simplify a class expression by removing redundant expressions and sorting operands."""
    return transformer.simplify(ce)
