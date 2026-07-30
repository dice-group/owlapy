"""Structural length calculation for OWLClassExpression."""
from functools import singledispatchmethod

from owlapy.class_expression import (
    OWLClass,
    OWLClassExpression,
    OWLDataAllValuesFrom,
    OWLDataCardinalityRestriction,
    OWLDataHasValue,
    OWLDataOneOf,
    OWLDataSomeValuesFrom,
    OWLDatatypeRestriction,
    OWLObjectAllValuesFrom,
    OWLObjectCardinalityRestriction,
    OWLObjectComplementOf,
    OWLObjectHasSelf,
    OWLObjectHasValue,
    OWLObjectIntersectionOf,
    OWLObjectOneOf,
    OWLObjectSomeValuesFrom,
    OWLObjectUnionOf,
)

from ..owl_data_ranges import OWLDataComplementOf, OWLDataIntersectionOf, OWLDataUnionOf
from ..owl_datatype import OWLDatatype
from ..owl_object import OWLObject
from ..owl_property import OWLDataProperty, OWLObjectInverseOf, OWLObjectProperty
from .ordering import iter_count


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
