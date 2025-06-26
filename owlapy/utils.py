"""Owlapy utils."""
from collections import Counter
from owlapy.owl_individual import OWLNamedIndividual
from sortedcontainers import SortedSet
from functools import singledispatchmethod, total_ordering
from typing import Iterable, List, Type,Callable, TypeVar, Generic, Tuple, cast, Optional, Union, overload, Protocol, ClassVar
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
    OWLObjectHasValue, OWLDatatypeRestriction, OWLFacetRestriction, OWLObjectOneOf, OWLQuantifiedObjectRestriction
from .owl_data_ranges import OWLDataComplementOf, OWLDataUnionOf, OWLDataIntersectionOf, OWLNaryDataRange, OWLDataRange, \
    OWLPropertyRange
from .owl_object import OWLObject
from .owl_datatype import OWLDatatype

import concurrent.futures

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
    return sorted(i, key=OrderedOWLObject)


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

class OperandSetTransform:
    def simplify(self, o: OWLClassExpression) -> OWLClassExpression:
        return self._simplify(o).get_nnf()

    # single dispatch is still not implemented in mypy, see https://github.com/python/mypy/issues/2904
    @singledispatchmethod
    def _simplify(self, o: _O) -> _O:
        raise NotImplementedError(o)

    @_simplify.register
    def _(self, o: OWLClass) -> OWLClass:
        return o

    @_simplify.register
    def _(self, p: OWLObjectProperty) -> OWLObjectProperty:
        return p

    @_simplify.register
    def _(self, p: OWLDataProperty) -> OWLDataProperty:
        return p

    @_simplify.register
    def _(self, i: OWLNamedIndividual) -> OWLNamedIndividual:
        return i

    @_simplify.register
    def _(self, i: OWLLiteral) -> OWLLiteral:
        return i

    @_simplify.register
    def _(self, e: OWLObjectSomeValuesFrom) -> OWLObjectSomeValuesFrom:
        return OWLObjectSomeValuesFrom(property=e.get_property(), filler=self._simplify(e.get_filler()))

    @_simplify.register
    def _(self, e: OWLObjectAllValuesFrom) -> OWLObjectAllValuesFrom:
        return OWLObjectAllValuesFrom(property=e.get_property(), filler=self._simplify(e.get_filler()))

    @_simplify.register
    def _(self, c: OWLObjectUnionOf) -> OWLClassExpression:
        s = set(map(self._simplify, set(c.operands())))
        if OWLThing in s:
            return OWLThing
        elif len(s) == 1:
            return s.pop()
        return OWLObjectUnionOf(_sort_by_ordered_owl_object(s))

    @_simplify.register
    def _(self, c: OWLObjectIntersectionOf) -> OWLClassExpression:
        s = set(map(self._simplify, set(c.operands())))
        s.discard(OWLThing)
        if not s:
            return OWLThing
        elif len(s) == 1:
            return s.pop()
        return OWLObjectIntersectionOf(_sort_by_ordered_owl_object(s))

    @_simplify.register
    def _(self, n: OWLObjectComplementOf) -> OWLObjectComplementOf:
        return n

    @_simplify.register
    def _(self, p: OWLObjectInverseOf) -> OWLObjectInverseOf:
        return p

    @_simplify.register
    def _(self, r: OWLObjectMinCardinality) -> OWLObjectMinCardinality:
        return OWLObjectMinCardinality(cardinality=r.get_cardinality(), property=r.get_property(),
                                       filler=self._simplify(r.get_filler()))

    @_simplify.register
    def _(self, r: OWLObjectExactCardinality) -> OWLObjectExactCardinality:
        return OWLObjectExactCardinality(cardinality=r.get_cardinality(), property=r.get_property(),
                                         filler=self._simplify(r.get_filler()))

    @_simplify.register
    def _(self, r: OWLObjectMaxCardinality) -> OWLObjectMaxCardinality:
        return OWLObjectMaxCardinality(cardinality=r.get_cardinality(), property=r.get_property(),
                                       filler=self._simplify(r.get_filler()))

    @_simplify.register
    def _(self, r: OWLObjectHasSelf) -> OWLObjectHasSelf:
        return r

    @_simplify.register
    def _(self, r: OWLObjectHasValue) -> OWLObjectHasValue:
        return r

    @_simplify.register
    def _(self, r: OWLObjectOneOf) -> OWLObjectOneOf:
        return OWLObjectOneOf(_sort_by_ordered_owl_object(set(r.individuals())))

    @_simplify.register
    def _(self, e: OWLDataSomeValuesFrom) -> OWLDataSomeValuesFrom:
        return OWLDataSomeValuesFrom(property=e.get_property(), filler=self._simplify(e.get_filler()))

    @_simplify.register
    def _(self, e: OWLDataAllValuesFrom) -> OWLDataAllValuesFrom:
        return OWLDataAllValuesFrom(property=e.get_property(), filler=self._simplify(e.get_filler()))

    @_simplify.register
    def _(self, c: OWLDataUnionOf) -> OWLDataRange:
        s = set(map(self._simplify, set(c.operands())))
        if len(s) == 1:
            return s.pop()
        return OWLDataUnionOf(_sort_by_ordered_owl_object(s))

    @_simplify.register
    def _(self, c: OWLDataIntersectionOf) -> OWLDataRange:
        s = set(map(self._simplify, set(c.operands())))
        if len(s) == 1:
            return s.pop()
        return OWLDataIntersectionOf(_sort_by_ordered_owl_object(s))

    @_simplify.register
    def _(self, n: OWLDatatypeRestriction) -> OWLDatatypeRestriction:
        return n

    @_simplify.register
    def _(self, n: OWLDataComplementOf) -> OWLDataComplementOf:
        return n

    @_simplify.register
    def _(self, r: OWLDataMinCardinality) -> OWLDataMinCardinality:
        return OWLDataMinCardinality(cardinality=r.get_cardinality(), property=r.get_property(),
                                     filler=self._simplify(r.get_filler()))

    @_simplify.register
    def _(self, r: OWLDataExactCardinality) -> OWLDataExactCardinality:
        return OWLDataExactCardinality(cardinality=r.get_cardinality(), property=r.get_property(),
                                       filler=self._simplify(r.get_filler()))

    @_simplify.register
    def _(self, r: OWLDataMaxCardinality) -> OWLDataMaxCardinality:
        return OWLDataMaxCardinality(cardinality=r.get_cardinality(), property=r.get_property(),
                                     filler=self._simplify(r.get_filler()))

    @_simplify.register
    def _(self, r: OWLDataHasValue) -> OWLDataHasValue:
        return r

    @_simplify.register
    def _(self, r: OWLDataOneOf) -> OWLDataOneOf:
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


def _sort_by_ordered_owl_object(i: Iterable[_O]) -> Iterable[_O]:
    return sorted(i, key=OrderedOWLObject)


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


# OWL-APy custom util start

class TopLevelCNF:
    """This class contains functions to transform a class expression into Top-Level Conjunctive Normal Form."""

    def get_top_level_cnf(self, ce: OWLClassExpression) -> OWLClassExpression:
        """Convert a class expression into Top-Level Conjunctive Normal Form. Operands will be sorted.

        Args:
            ce: Class Expression.

        Returns:
            Class Expression in Top-Level Conjunctive Normal Form.
            """
        c = _get_top_level_form(ce.get_nnf(), OWLObjectUnionOf, OWLObjectIntersectionOf)
        return combine_nary_expressions(c)


class TopLevelDNF:
    """This class contains functions to transform a class expression into Top-Level Disjunctive Normal Form."""

    def get_top_level_dnf(self, ce: OWLClassExpression) -> OWLClassExpression:
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
        ce = cast(OWLNaryBooleanClassExpression, combine_nary_expressions(ce))
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
        expressions: List[OWLPropertyRange] = []
        for op in ce.operands():
            expr = combine_nary_expressions(op)
            if type(expr) is type(ce):
                expr = cast(Union[OWLNaryBooleanClassExpression, OWLNaryDataRange], expr)
                expressions.extend(expr.operands())
            else:
                expressions.append(expr)
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
