"""Owlapy utils."""
from functools import singledispatchmethod, total_ordering
from typing import Iterable, List, Type, TypeVar, Generic, Tuple, cast, Optional, Union, overload, Protocol, ClassVar
from .meta_classes import HasIRI, HasFiller, HasCardinality, HasOperands
from .owl_literal import OWLLiteral
from .owl_property import OWLObjectInverseOf
from owlapy.class_expression import OWLClassExpression, OWLClass, OWLObjectCardinalityRestriction, \
    OWLObjectComplementOf, OWLNothing, OWLRestriction, OWLThing, OWLObjectSomeValuesFrom, \
    OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality, OWLObjectHasSelf, \
    OWLDataMaxCardinality, OWLDataMinCardinality, OWLDataExactCardinality, OWLDataHasValue, \
    OWLDataAllValuesFrom, OWLDataSomeValuesFrom, OWLObjectAllValuesFrom, \
    OWLDataOneOf, OWLObjectIntersectionOf, \
    OWLDataCardinalityRestriction, OWLNaryBooleanClassExpression, OWLObjectUnionOf, \
    OWLObjectHasValue, OWLDatatypeRestriction, OWLFacetRestriction, OWLObjectOneOf
from .owl_data_ranges import OWLDataComplementOf, OWLDataUnionOf, OWLDataIntersectionOf, OWLNaryDataRange, OWLDataRange, \
    OWLPropertyRange
from .owl_object import OWLObject
from .owl_datatype import OWLDatatype


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


def move(*args):
    """"Move" an imported class to the current module by setting the classes __module__ attribute.

    This is useful for documentation purposes to hide internal packages in sphinx.

    Args:
        args: List of classes to move.
    """
    from inspect import currentframe
    f = currentframe()
    f = f.f_back
    mod = f.f_globals['__name__']
    for cls in args:
        cls.__module__ = mod
