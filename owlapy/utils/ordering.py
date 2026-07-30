"""Canonical ordering/sorting of OWL objects and nary-expression combination, used to normalize
class expressions before comparison, simplification, and NNF conversion."""
import logging
from collections import Counter
from functools import singledispatchmethod, total_ordering
from typing import Callable, ClassVar, Generic, Iterable, List, Optional, Protocol, Set, Tuple, TypeVar, Union, cast, overload

from sortedcontainers import SortedSet

from owlapy.class_expression import (
    OWLClass,
    OWLClassExpression,
    OWLDataAllValuesFrom,
    OWLDataCardinalityRestriction,
    OWLDataExactCardinality,
    OWLDataHasValue,
    OWLDataMaxCardinality,
    OWLDataMinCardinality,
    OWLDataOneOf,
    OWLDataSomeValuesFrom,
    OWLDatatypeRestriction,
    OWLFacetRestriction,
    OWLNaryBooleanClassExpression,
    OWLObjectAllValuesFrom,
    OWLObjectCardinalityRestriction,
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
    OWLRestriction,
)

from ..meta_classes import HasCardinality, HasFiller, HasIRI, HasOperands
from ..owl_data_ranges import OWLDataComplementOf, OWLDataIntersectionOf, OWLDataRange, OWLDataUnionOf, OWLNaryDataRange, OWLPropertyRange
from ..owl_datatype import OWLDatatype
from ..owl_individual import OWLNamedIndividual
from ..owl_literal import OWLLiteral
from ..owl_object import OWLObject
from ..owl_property import OWLDataProperty, OWLObjectInverseOf, OWLObjectProperty

logger = logging.getLogger(__name__)

_N = TypeVar('_N')  #:
_O = TypeVar('_O')  #:


def iter_count(i: Iterable) -> int:
    """Count the number of elements in an iterable."""
    return sum(1 for _ in i)


class HasIndex(Protocol):
    """Interface for types with an index; this is used to group objects by type when sorting."""
    type_index: ClassVar[int]  #: index for this type. This is a sorting index for the types.

    def __eq__(self, other): ...


_HasIRI = TypeVar('_HasIRI', bound=HasIRI)  #:
_HasIndex = TypeVar('_HasIndex', bound=HasIndex)  #:


def as_index(o: OWLObject) -> HasIndex:
    """Cast OWL Object to HasIndex."""
    i = cast(HasIndex, o)
    assert type(i).type_index
    return i


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
    try:
        return sorted(i, key=OrderedOWLObject)
    except AttributeError:
        logger.debug(f"Could not sort by OrderedOWLObject: {i}")


def _avoid_overly_redundand_operands(operands: List[_O], max_count: int = 2) -> List[_O]:
    _max_count = max_count
    r = []
    counts = Counter(operands)
    for op in sorted(operands, key=OrderedOWLObject):
        for _ in range(min(_max_count, counts[op])):
            r.append(op)
    return r


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
