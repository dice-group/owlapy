"""OWL Reasoner"""
import operator
import logging
import owlready2
import os

from collections import defaultdict, Counter
from functools import singledispatchmethod, reduce, cached_property
from itertools import chain, repeat
from types import MappingProxyType, FunctionType
from typing import (DefaultDict,Generator, Iterable, Dict, Mapping, Set, Type, TypeVar, Optional, FrozenSet, Union,
                    List, Tuple)

from owlapy.class_expression import OWLClassExpression, OWLObjectSomeValuesFrom, OWLObjectUnionOf, \
    OWLObjectIntersectionOf, OWLObjectComplementOf, OWLObjectAllValuesFrom, OWLObjectOneOf, OWLObjectHasValue, \
    OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality, OWLObjectCardinalityRestriction, \
    OWLDataSomeValuesFrom, OWLDataOneOf, OWLDatatypeRestriction, OWLFacetRestriction, OWLDataHasValue, \
    OWLDataAllValuesFrom, OWLNothing, OWLThing
from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLAxiom, OWLSubClassOfAxiom
from owlapy.owl_data_ranges import OWLDataComplementOf, OWLDataUnionOf, OWLDataIntersectionOf
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_object import OWLEntity
from owlapy.owl_ontology import Ontology, _parse_concept_to_owlapy, SyncOntology, NeuralOntology
from owlapy.abstracts.abstract_owl_ontology import AbstractOWLOntology
from owlapy.owl_property import OWLObjectPropertyExpression, OWLDataProperty, OWLObjectProperty, OWLObjectInverseOf, \
    OWLPropertyExpression, OWLDataPropertyExpression, OWLProperty
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral, OWLBottomObjectProperty, OWLTopObjectProperty, OWLBottomDataProperty, \
    OWLTopDataProperty
from owlapy.utils import run_with_timeout
from owlapy.abstracts.abstract_owl_reasoner import AbstractOWLReasoner


logger = logging.getLogger(__name__)

_P = TypeVar('_P', bound=OWLPropertyExpression)


class StructuralReasoner(AbstractOWLReasoner):
    """Tries to check instances fast (but maybe incomplete)."""

    def __init__(self, ontology: Union[AbstractOWLOntology, str], *, class_cache: bool = True,
                 property_cache: bool = True, negation_default: bool = True, sub_properties: bool = False):
        """Fast instance checker.

        Args:
            ontology: Ontology to use.
            property_cache: Whether to cache property values.
            negation_default: Whether to assume a missing fact means it is false ("closed world view").
            sub_properties: Whether to take sub properties into account for the
                :func:`StructuralReasoner.instances` retrieval.
            """
        if isinstance(ontology, str):
            ontology = Ontology(ontology)

        super().__init__(ontology)
        assert isinstance(ontology, Ontology)
        self._world: owlready2.World = ontology._world
        self._ontology: Ontology = ontology
        self.class_cache: bool = class_cache
        self._property_cache: bool = property_cache
        self._negation_default: bool = negation_default
        self._sub_properties: bool = sub_properties
        self.__warned: int = 0
        self._init()

    def _init(self):
        if self.class_cache:
            # Class => individuals
            self._cls_to_ind: Dict[OWLClass, FrozenSet[OWLNamedIndividual]] = {}

        if self._property_cache:
            # ObjectProperty => { individual => individuals }
            self._obj_prop: Dict[OWLObjectProperty, Mapping[OWLNamedIndividual, Set[OWLNamedIndividual]]] = dict()
            # ObjectProperty => { individual => individuals }
            self._obj_prop_inv: Dict[OWLObjectProperty, Mapping[OWLNamedIndividual, Set[OWLNamedIndividual]]] = dict()
            # DataProperty => { individual => literals }
            self._data_prop: Dict[OWLDataProperty, Mapping[OWLNamedIndividual, Set[OWLLiteral]]] = dict()
        else:
            self._has_prop: Mapping[Type[_P], Dict[_P, FrozenSet[OWLNamedIndividual]]] = {
                OWLDataProperty: {},
                OWLObjectProperty: {},
                OWLObjectInverseOf: {},
            }

    def reset(self):
        """The reset method shall reset any cached state."""
        self._init()

    def data_property_domains(self, pe: OWLDataProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        domains = {d.get_domain() for d in self.get_root_ontology().data_property_domain_axioms(pe)}
        sub_domains = set(chain.from_iterable([self.sub_classes(d) for d in domains]))
        yield from domains - sub_domains
        if not direct:
            yield from sub_domains

    def object_property_domains(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        domains = {d.get_domain() for d in self.get_root_ontology().object_property_domain_axioms(pe)}
        sub_domains = set(chain.from_iterable([self.sub_classes(d) for d in domains]))
        yield from domains - sub_domains
        if not direct:
            yield from sub_domains

    def object_property_ranges(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        ranges = {r.get_range() for r in self.get_root_ontology().object_property_range_axioms(pe)}
        sub_ranges = set(chain.from_iterable([self.sub_classes(d) for d in ranges]))
        yield from ranges - sub_ranges
        if not direct:
            yield from sub_ranges

    def data_property_ranges(self, pe: OWLDataProperty, direct: bool = True) -> Iterable[OWLClassExpression]:
        if direct:
            yield from [r.get_range() for r in self.get_root_ontology().data_property_range_axioms(pe)]
        else:
            # hierarchy of data types is not considered.
            return NotImplemented()

    def equivalent_classes(self, ce: OWLClassExpression, only_named: bool = True) -> Iterable[OWLClassExpression]:
        seen_set = {ce}
        if isinstance(ce, OWLClass):
            c_x: owlready2.ThingClass = self._world[ce.str]
            for eq_x in c_x.INDIRECT_equivalent_to:
                eq = _parse_concept_to_owlapy(eq_x)
                if (isinstance(eq, OWLClass) or
                    (isinstance(eq, OWLClassExpression) and not only_named)) and eq not in seen_set:
                    seen_set.add(eq)
                    yield eq
                # Workaround for problems in owlready2. It does not always recognize equivalent complex class
                # expressions through INDIRECT_equivalent_to. Maybe it will work as soon as owlready2 adds support for
                # EquivalentClasses general class axioms.
                if not only_named and isinstance(eq_x, owlready2.ThingClass):
                    for eq_2_x in eq_x.equivalent_to:
                        eq_2 = _parse_concept_to_owlapy(eq_2_x)
                        if eq_2 not in seen_set:
                            seen_set.add(eq_2)
                            yield eq_2
        elif isinstance(ce, OWLClassExpression):
            # Extend as soon as owlready2 supports EquivalentClasses general class axioms
            # Slow but works. No better way to do this in owlready2 without using the reasoners at the moment.
            # Might be able to change this when owlready2 supports general class axioms for EquivalentClasses.
            for c in self._ontology.classes_in_signature():
                if ce in self.equivalent_classes(c, only_named=False) and c not in seen_set:
                    seen_set.add(c)
                    yield c
                    for e_c in self.equivalent_classes(c, only_named=False):
                        if e_c not in seen_set and (not only_named or isinstance(e_c, OWLClass)):
                            seen_set.add(e_c)
                            yield e_c
        else:
            raise ValueError(f'Equivalent classes not implemented for: {ce}')

    def _find_disjoint_classes(self, ce: OWLClassExpression, only_named: bool = True, seen_set=None):
        if isinstance(ce, OWLClass):
            c_x: owlready2.ThingClass = self._world[ce.str]
            for d_x in chain.from_iterable(map(lambda d: d.entities, c_x.disjoints())):
                if d_x != c_x and (isinstance(d_x, owlready2.ThingClass) or
                                   (isinstance(d_x, owlready2.ClassConstruct) and not only_named)):
                    d_owlapy = _parse_concept_to_owlapy(d_x)
                    seen_set.add(d_owlapy)
                    yield d_owlapy
                    for c in self.equivalent_classes(d_owlapy, only_named=only_named):
                        if c not in seen_set:
                            seen_set.add(c)
                            yield c
                    for c in self.sub_classes(d_owlapy, only_named=only_named):
                        if c not in seen_set:
                            seen_set.add(c)
                            yield c
        elif isinstance(ce, OWLClassExpression):
            # Extend as soon as owlready2 supports DisjointClasses general class axioms
            # Slow but works. No better way to do this in owlready2 without using the reasoners at the moment.
            # Might be able to change this when owlready2 supports general class axioms for DjsjointClasses
            yield from (c for c in self._ontology.classes_in_signature() if ce in self.disjoint_classes(c, False))
        else:
            raise ValueError(f'Equivalent classes not implemented for: {ce}')

    def disjoint_classes(self, ce: OWLClassExpression, only_named: bool = True) -> Iterable[OWLClassExpression]:
        seen_set = set()
        if ce is OWLNothing:
            yield from self._ontology.classes_in_signature()
            yield OWLThing
            return
        if ce is OWLThing:
            yield OWLNothing
            return
        yield from self._find_disjoint_classes(ce, only_named, seen_set)
        for c in self.super_classes(ce, only_named=only_named):
            if c != OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')):
                yield from self._find_disjoint_classes(c, only_named=only_named, seen_set=seen_set)

    def different_individuals(self, ind: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        i: owlready2.Thing = self._world[ind.str]
        yield from (OWLNamedIndividual(IRI.create(d_i.iri))
                    for d_i in chain.from_iterable(map(lambda x: x.entities, i.differents()))
                    if isinstance(d_i, owlready2.Thing) and i != d_i)

    def same_individuals(self, ind: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        i: owlready2.Thing = self._world[ind.str]
        yield from (OWLNamedIndividual(IRI.create(d_i.iri)) for d_i in i.equivalent_to
                    if isinstance(d_i, owlready2.Thing))

    def data_property_values(self, e: OWLEntity, pe: OWLDataProperty, direct: bool = True) \
            -> Iterable[OWLLiteral]:
        i: owlready2.Thing = self._world[e.str]
        p: owlready2.DataPropertyClass = self._world[pe.str]
        retrieval_func = p._get_values_for_individual if direct else p._get_indirect_values_for_individual
        for val in retrieval_func(i):
            yield OWLLiteral(val)

    def all_data_property_values(self, pe: OWLDataProperty, direct: bool = True) -> Iterable[OWLLiteral]:
        p: owlready2.DataPropertyClass = self._world[pe.str]
        relations = p.get_relations()
        if not direct:
            indirect_relations = chain.from_iterable(
                map(lambda x: self._world[x.str].get_relations(),
                    self.sub_data_properties(pe, direct=False)))
            relations = chain(relations, indirect_relations)
        for _, val in relations:
            yield OWLLiteral(val)

    def object_property_values(self, ind: OWLNamedIndividual, pe: OWLObjectPropertyExpression, direct: bool = False) \
            -> Iterable[OWLNamedIndividual]:
        if isinstance(pe, OWLObjectProperty):
            i: owlready2.Thing = self._world[ind.str]
            p: owlready2.ObjectPropertyClass = self._world[pe.str]
            # Recommended to use direct=False because _get_values_for_individual does not give consistent result
            # for the case when there are equivalent object properties. At least until this is fixed on owlready2.
            retieval_func = p._get_values_for_individual if direct else p._get_indirect_values_for_individual
            for val in retieval_func(i):
                yield OWLNamedIndividual(IRI.create(val.iri))
        elif isinstance(pe, OWLObjectInverseOf):
            p: owlready2.ObjectPropertyClass = self._world[pe.get_named_property().str]
            inverse_p = p.inverse_property
            # If the inverse property is explicitly defined we can take shortcut
            if inverse_p is not None:
                yield from self.object_property_values(ind, OWLObjectProperty(IRI.create(inverse_p.iri)), direct)
            else:
                if not direct:
                    raise NotImplementedError('Indirect values of inverse properties are only implemented if the '
                                              'inverse property is explicitly defined in the ontology.'
                                              f'Property: {pe}')
                i: owlready2.Thing = self._world[ind.str]
                for val in p._get_inverse_values_for_individual(i):
                    yield OWLNamedIndividual(IRI.create(val.iri))
        else:
            raise NotImplementedError(pe)

    def _instances(self, ce: OWLClassExpression, direct: bool = False) -> Iterable[OWLNamedIndividual]:
        if direct:
            if not self.__warned & 2:
                logger.warning("direct not implemented")
                self.__warned |= 2
        temp = self._find_instances(ce)
        yield from temp

    def instances(self, ce: OWLClassExpression, direct: bool = False, timeout: int = 1000):
        return run_with_timeout(self._instances, timeout, (ce, direct))

    def _sub_classes_recursive(self, ce: OWLClassExpression, seen_set: Set, only_named: bool = True) \
            -> Iterable[OWLClassExpression]:

        # work around issue in class equivalence detection in Owlready2
        for c in [ce, *self.equivalent_classes(ce, only_named=False)]:
            if c not in seen_set:
                seen_set.add(c)
                yield c
            # First go through all general class axioms, they should only have complex classes as sub_classes.
            # Done for OWLClass and OWLClassExpression.
            for axiom in self._ontology.general_class_axioms():
                if (isinstance(axiom, OWLSubClassOfAxiom) and axiom.get_super_class() == c
                        and axiom.get_sub_class() not in seen_set):
                    seen_set.add(axiom.get_sub_class())
                    if not only_named:
                        yield axiom.get_sub_class()
                    yield from self._sub_classes_recursive(axiom.get_sub_class(), seen_set, only_named)

            if isinstance(c, OWLClass):
                c_x: owlready2.EntityClass = self._world[c.str]
                # Subclasses will only return named classes
                for sc_x in c_x.subclasses(world=self._world):
                    sc = _parse_concept_to_owlapy(sc_x)
                    if isinstance(sc, OWLClass) and sc not in seen_set:
                        seen_set.add(sc)
                        yield sc
                        yield from self._sub_classes_recursive(sc, seen_set, only_named=only_named)
            elif isinstance(c, OWLClassExpression):
                # Slow but works. No better way to do this in owlready2 without using the reasoners at the moment.
                for atomic_c in self._ontology.classes_in_signature():
                    if c in self.super_classes(atomic_c, direct=True, only_named=False) and atomic_c not in seen_set:
                        seen_set.add(atomic_c)
                        yield atomic_c
                        yield from self._sub_classes_recursive(atomic_c, seen_set, only_named=only_named)
                if isinstance(ce, OWLObjectSomeValuesFrom):
                    for r in self.sub_object_properties(ce.get_property()):
                        osvf = OWLObjectSomeValuesFrom(property=r,
                                                       filler=ce.get_filler())
                        if osvf not in seen_set:
                            seen_set.add(osvf)
                            yield osvf
                            # yield from self._sub_classes_recursive(osvf, seen_set, only_named=only_named)
            else:
                raise ValueError(f'Sub classes retrieval not implemented for: {ce}')

    def sub_classes(self, ce: OWLClassExpression, direct: bool = False, only_named: bool = True) \
            -> Iterable[OWLClassExpression]:
        if not direct:
            seen_set = {ce}
            yield from self._sub_classes_recursive(ce, seen_set, only_named=only_named)
        else:
            # First go through all general class axioms, they should only have complex classes as sub_classes.
            # Done for OWLClass and OWLClassExpression.
            if not only_named:
                for axiom in self._ontology.general_class_axioms():
                    if isinstance(axiom, OWLSubClassOfAxiom) and axiom.get_super_class() == ce:
                        yield axiom.get_sub_class()
            if isinstance(ce, OWLClass):
                c_x: owlready2.ThingClass = self._world[ce.str]
                # Subclasses will only return named classes
                for sc in c_x.subclasses(world=self._world):
                    if isinstance(sc, owlready2.ThingClass):
                        yield OWLClass(IRI.create(sc.iri))
            elif isinstance(ce, OWLClassExpression):
                # Slow but works. No better way to do this in owlready2 without using the reasoners at the moment.
                for c in self._ontology.classes_in_signature():
                    if ce in self.super_classes(c, direct=True, only_named=False):
                        yield c
            else:
                raise ValueError(f'Sub classes retrieval not implemented for: {ce}')

    def _super_classes_recursive(self, ce: OWLClassExpression, seen_set: Set, only_named: bool = True) \
            -> Iterable[OWLClassExpression]:
        # work around issue in class equivalence detection in Owlready2
        for c in [ce, *self.equivalent_classes(ce, only_named=False)]:
            if c not in seen_set:
                seen_set.add(c)
                yield c
            if isinstance(c, OWLClass):
                c_x: owlready2.EntityClass = self._world[c.str]
                for sc_x in c_x.is_a:
                    sc = _parse_concept_to_owlapy(sc_x)
                    if (isinstance(sc, OWLClass) or isinstance(sc, OWLClassExpression)) and sc not in seen_set:
                        seen_set.add(sc)
                        # Return class expression if it is a named class or complex class expressions should be
                        # included
                        if isinstance(sc, OWLClass) or not only_named:
                            yield sc
                        yield from self._super_classes_recursive(sc, seen_set, only_named=only_named)
            elif isinstance(c, OWLClassExpression):
                for axiom in self._ontology.general_class_axioms():
                    if (isinstance(axiom, OWLSubClassOfAxiom) and axiom.get_sub_class() == c
                            and (axiom.get_super_class() not in seen_set)):
                        super_class = axiom.get_super_class()
                        seen_set.add(super_class)
                        # Return class expression if it is a named class or complex class expressions should be
                        # included
                        if isinstance(super_class, OWLClass) or not only_named:
                            yield super_class
                        yield from self._super_classes_recursive(super_class, seen_set, only_named=only_named)

                # Slow but works. No better way to do this in owlready2 without using the reasoners at the moment.
                for atomic_c in self._ontology.classes_in_signature():
                    if c in self.sub_classes(atomic_c, direct=True, only_named=False) and atomic_c not in seen_set:
                        seen_set.add(atomic_c)
                        yield atomic_c
                        yield from self._super_classes_recursive(atomic_c, seen_set, only_named=only_named)
            else:
                raise ValueError(f'Super classes retrieval not supported for: {ce}')

    def super_classes(self, ce: OWLClassExpression, direct: bool = False, only_named: bool = True) \
            -> Iterable[OWLClassExpression]:
        if not direct:
            seen_set = {ce}
            yield from self._super_classes_recursive(ce, seen_set, only_named=only_named)
        else:
            if isinstance(ce, OWLClass):
                c_x: owlready2.ThingClass = self._world[ce.str]
                for sc in c_x.is_a:
                    if (isinstance(sc, owlready2.ThingClass) or
                            (not only_named and isinstance(sc, owlready2.ClassConstruct))):
                        yield _parse_concept_to_owlapy(sc)
            elif isinstance(ce, OWLClassExpression):
                seen_set = set()
                for axiom in self._ontology.general_class_axioms():
                    if (isinstance(axiom, OWLSubClassOfAxiom) and axiom.get_sub_class() == ce
                            and (not only_named or isinstance(axiom.get_super_class(), OWLClass))):
                        seen_set.add(axiom.get_super_class())
                        yield axiom.get_super_class()
                # Slow but works. No better way to do this in owlready2 without using the reasoners at the moment.
                # TODO: Might not be needed, in theory the general class axioms above should cover all classes
                # that can be found here
                for c in self._ontology.classes_in_signature():
                    if ce in self.sub_classes(c, direct=True, only_named=False) and c not in seen_set:
                        seen_set.add(c)
                        yield c
            else:
                raise ValueError(f'Super classes retrieval not supported for {ce}')

    def equivalent_object_properties(self, op: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        if isinstance(op, OWLObjectProperty):
            p_x: owlready2.ObjectPropertyClass = self._world[op.str]
            yield from (OWLObjectProperty(IRI.create(ep_x.iri)) for ep_x in p_x.INDIRECT_equivalent_to
                        if isinstance(ep_x, owlready2.ObjectPropertyClass))
        else:
            raise NotImplementedError("equivalent properties of inverse properties not yet implemented", op)

    def equivalent_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        p_x: owlready2.DataPropertyClass = self._world[dp.str]
        yield from (OWLDataProperty(IRI.create(ep_x.iri)) for ep_x in p_x.INDIRECT_equivalent_to
                    if isinstance(ep_x, owlready2.DataPropertyClass))

    def _find_disjoint_object_properties(self, op: OWLObjectPropertyExpression, seen_set=None) \
            -> Iterable[OWLObjectPropertyExpression]:
        if isinstance(op, OWLObjectProperty):
            p_x: owlready2.ObjectPropertyClass = self._world[op.str]
            ont_x: owlready2.Ontology = self.get_root_ontology()._onto
            for disjoint in ont_x.disjoint_properties():
                if p_x in disjoint.entities:
                    for o_p in disjoint.entities:
                        if isinstance(o_p, owlready2.ObjectPropertyClass) and o_p != p_x:
                            op_owlapy = OWLObjectProperty(IRI.create(o_p.iri))
                            seen_set.add(op_owlapy)
                            yield op_owlapy
                            for o in self.equivalent_object_properties(op_owlapy):
                                if o not in seen_set:
                                    seen_set.add(o)
                                    yield o
                            for o in self.sub_object_properties(op_owlapy):
                                if o not in seen_set:
                                    seen_set.add(o)
                                    yield o
        else:
            raise NotImplementedError("disjoint object properties of inverse properties not yet implemented", op)

    def disjoint_object_properties(self, op: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        seen_set = set()
        if op is OWLBottomObjectProperty:
            yield from self._ontology.object_properties_in_signature()
            yield OWLTopObjectProperty
            return
        if op is OWLTopObjectProperty:
            yield OWLBottomObjectProperty
            return
        yield from self._find_disjoint_object_properties(op, seen_set)
        for o in self.super_object_properties(op):
            if o != OWLObjectProperty(IRI('http://www.w3.org/2002/07/owl#', 'ObjectProperty')):
                yield from self._find_disjoint_object_properties(o, seen_set=seen_set)

    def _find_disjoint_data_properties(self, dp: OWLDataProperty, seen_set=None) -> Iterable[OWLDataProperty]:
        p_x: owlready2.DataPropertyClass = self._world[dp.str]
        ont_x: owlready2.Ontology = self.get_root_ontology()._onto
        for disjoint in ont_x.disjoint_properties():
            if p_x in disjoint.entities:
                for d_p in disjoint.entities:
                    if isinstance(d_p, owlready2.DataPropertyClass) and d_p != p_x:
                        dp_owlapy = OWLDataProperty(IRI.create(d_p.iri))
                        seen_set.add(dp_owlapy)
                        yield dp_owlapy
                        for d in self.equivalent_data_properties(dp_owlapy):
                            if d not in seen_set:
                                seen_set.add(d)
                                yield d
                        for d in self.sub_data_properties(dp_owlapy):
                            if d not in seen_set:
                                seen_set.add(d)
                                yield d

    def disjoint_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        seen_set = set()
        if dp is OWLBottomDataProperty:
            yield from self._ontology.data_properties_in_signature()
            yield OWLTopDataProperty
            return
        if dp is OWLTopDataProperty:
            yield OWLBottomDataProperty
            return
        yield from self._find_disjoint_data_properties(dp, seen_set)
        for d in self.super_data_properties(dp):
            if d != OWLDataProperty(IRI('http://www.w3.org/2002/07/owl#', 'DatatypeProperty')):
                yield from self._find_disjoint_data_properties(d, seen_set=seen_set)

    def _sup_or_sub_data_properties_recursive(self, dp: OWLDataProperty, seen_set: Set, super_or_sub="") \
            -> Iterable[OWLDataProperty]:
        for d in self.equivalent_data_properties(dp):
            if d not in seen_set:
                seen_set.add(d)
                yield d
        p_x: owlready2.DataPropertyClass = self._world[dp.str]
        assert isinstance(p_x, owlready2.DataPropertyClass)
        if super_or_sub == "super":
            dps = set(p_x.is_a)
        else:
            dps = set(p_x.subclasses(world=self._world))
        for sp_x in dps:
            if isinstance(sp_x, owlready2.DataPropertyClass):
                sp = OWLDataProperty(IRI.create(sp_x.iri))
                if sp not in seen_set:
                    seen_set.add(sp)
                    yield sp
                    yield from self._sup_or_sub_data_properties_recursive(sp, seen_set, super_or_sub)

    def _sup_or_sub_data_properties(self, dp: OWLDataProperty, direct: bool = False, super_or_sub=""):
        assert isinstance(dp, OWLDataProperty)
        if direct:
            p_x: owlready2.DataPropertyClass = self._world[dp.str]
            if super_or_sub == "super":
                dps = set(p_x.is_a)
            else:
                dps = set(p_x.subclasses(world=self._world))
            for sp in dps:
                if isinstance(sp, owlready2.DataPropertyClass):
                    yield OWLDataProperty(IRI.create(sp.iri))
        else:
            seen_set = set()
            yield from self._sup_or_sub_data_properties_recursive(dp, seen_set, super_or_sub)

    def super_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        yield from self._sup_or_sub_data_properties(dp, direct, "super")

    def sub_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        yield from self._sup_or_sub_data_properties(dp, direct, "sub")

    def _sup_or_sub_object_properties_recursive(self, op: OWLObjectProperty, seen_set: Set, super_or_sub=""):
        for o in self.equivalent_object_properties(op):
            if o not in seen_set:
                seen_set.add(o)
                yield o
        p_x: owlready2.ObjectPropertyClass = self._world[op.str]
        assert isinstance(p_x, owlready2.ObjectPropertyClass)
        if super_or_sub == "super":
            dps = set(p_x.is_a)
        else:
            dps = set(p_x.subclasses(world=self._world))
        for sp_x in dps:
            if isinstance(sp_x, owlready2.ObjectPropertyClass):
                sp = OWLObjectProperty(IRI.create(sp_x.iri))
                if sp not in seen_set:
                    seen_set.add(sp)
                    yield sp
                    yield from self._sup_or_sub_object_properties_recursive(sp, seen_set, super_or_sub)

    def _sup_or_sub_object_properties(self, op: OWLObjectPropertyExpression, direct: bool = False, super_or_sub="") \
            -> Iterable[OWLObjectPropertyExpression]:
        if isinstance(op, OWLObjectProperty):
            if direct:
                p_x: owlready2.ObjectPropertyClass = self._world[op.str]
                if super_or_sub == "super":
                    dps = set(p_x.is_a)
                else:
                    dps = set(p_x.subclasses(world=self._world))
                for sp in dps:
                    if isinstance(sp, owlready2.ObjectPropertyClass):
                        yield OWLObjectProperty(IRI.create(sp.iri))
            else:
                seen_set = set()
                yield from self._sup_or_sub_object_properties_recursive(op, seen_set, super_or_sub)
        elif isinstance(op, OWLObjectInverseOf):
            p: owlready2.ObjectPropertyClass = self._world[op.get_named_property().str]
            inverse_p = p.inverse_property
            if inverse_p is not None:
                yield from self._sup_or_sub_object_properties(OWLObjectProperty(IRI.create(inverse_p.iri)), direct,
                                                              super_or_sub)
            else:
                raise NotImplementedError(f'{super_or_sub} properties of inverse properties are only implemented if the'
                                          ' inverse property is explicitly defined in the ontology. '
                                          f'Property: {op}')
        else:
            raise NotImplementedError(op)

    def super_object_properties(self, op: OWLObjectPropertyExpression, direct: bool = False) \
            -> Iterable[OWLObjectPropertyExpression]:
        """Gets the stream of object properties that are the strict (potentially direct) super properties of the
         specified object property with respect to the imports closure of the root ontology.

         Args:
             op (OWLObjectPropertyExpression): The object property expression whose super properties are to be
                                                retrieved.
             direct (bool): Specifies if the direct super properties should be retrieved (True) or if the all
                            super properties (ancestors) should be retrieved (False).

         Returns:
             Iterable of super properties.
         """
        yield from self._sup_or_sub_object_properties(op, direct, "super")

    def sub_object_properties(self, op: OWLObjectPropertyExpression, direct: bool = False) \
            -> Iterable[OWLObjectPropertyExpression]:
        yield from self._sup_or_sub_object_properties(op, direct, "sub")

    def types(self, ind: OWLNamedIndividual, direct: bool = False) -> Iterable[OWLClass]:
        i: owlready2.Thing = self._world[ind.str]
        if direct:
            for c in i.is_a:
                if isinstance(c, owlready2.ThingClass):
                    yield OWLClass(IRI.create(c.iri))
                # Anonymous classes are ignored
        else:
            for c in i.INDIRECT_is_a:
                if isinstance(c, owlready2.ThingClass):
                    yield OWLClass(IRI.create(c.iri))
                # Anonymous classes are ignored

    def get_root_ontology(self) -> AbstractOWLOntology:
        return self._ontology

    def _lazy_cache_obj_prop(self, pe: OWLObjectPropertyExpression) -> None:
        """Get all individuals involved in this object property and put them in a Dict."""
        if isinstance(pe, OWLObjectInverseOf):
            inverse = True
            if pe.get_named_property() in self._obj_prop_inv:
                return
        elif isinstance(pe, OWLObjectProperty):
            inverse = False
            if pe in self._obj_prop:
                return
        else:
            raise NotImplementedError

        # Dict with Individual => Set[Individual]
        opc: DefaultDict[OWLNamedIndividual, Set[OWLNamedIndividual]] = defaultdict(set)

        # shortcut for owlready2
        from owlapy.owl_ontology import Ontology
        if isinstance(self._ontology, Ontology):
            import owlready2
            # _x => owlready2 objects
            for l_x, r_x in self._retrieve_triples(pe):
                if inverse:
                    o_x = l_x
                    s_x = r_x
                else:
                    s_x = l_x
                    o_x = r_x
                if isinstance(s_x, owlready2.Thing) and isinstance(o_x, owlready2.Thing):
                    s = OWLNamedIndividual(IRI.create(s_x.iri))
                    o = OWLNamedIndividual(IRI.create(o_x.iri))
                    if s not in opc:
                        opc[s] = set()
                    opc[s] |= {o}
        else:
            all_ = frozenset(self._ontology.individuals_in_signature())
            for s in all_:
                individuals = set(self.object_property_values(s, pe, not self._sub_properties))
                if individuals:
                    opc[s] = individuals

        if inverse:
            self._obj_prop_inv[pe.get_named_property()] = MappingProxyType(opc)
        else:
            self._obj_prop[pe] = MappingProxyType(opc)

    def _some_values_subject_index(self, pe: OWLPropertyExpression) -> FrozenSet[OWLNamedIndividual]:
        if isinstance(pe, OWLDataProperty):
            typ = OWLDataProperty
        elif isinstance(pe, OWLObjectProperty):
            typ = OWLObjectProperty
        elif isinstance(pe, OWLObjectInverseOf):
            typ = OWLObjectInverseOf
        else:
            raise NotImplementedError

        if pe not in self._has_prop[typ]:
            subs = set()

            # shortcut for owlready2
            from owlapy.owl_ontology import Ontology
            if isinstance(self._ontology, Ontology):
                import owlready2
                # _x => owlready2 objects
                for s_x, o_x in self._retrieve_triples(pe):
                    if isinstance(pe, OWLObjectInverseOf):
                        l_x = o_x
                    else:
                        l_x = s_x
                    if isinstance(l_x, owlready2.Thing):
                        subs |= {OWLNamedIndividual(IRI.create(l_x.iri))}
            else:
                if isinstance(pe, OWLDataProperty):
                    func = self.data_property_values
                else:
                    func = self.object_property_values
                all_ = frozenset(self._ontology.individuals_in_signature())
                for s in all_:
                    try:
                        next(iter(func(s, pe, not self._sub_properties)))
                        subs |= {s}
                    except StopIteration:
                        pass

            self._has_prop[typ][pe] = frozenset(subs)

        return self._has_prop[typ][pe]

    def _find_some_values(self, pe: OWLObjectPropertyExpression, filler_inds: Set[OWLNamedIndividual],
                          min_count: int = 1, max_count: Optional[int] = None) -> FrozenSet[OWLNamedIndividual]:
        """Get all individuals that have one of filler_inds as their object property value."""
        ret = set()
        if self._ontology.is_modified and (self.class_cache or self._property_cache):
            self.reset_and_disable_cache()
        if self._property_cache:
            self._lazy_cache_obj_prop(pe)

            if isinstance(pe, OWLObjectInverseOf):
                ops = self._obj_prop_inv[pe.get_named_property()]
            elif isinstance(pe, OWLObjectProperty):
                ops = self._obj_prop[pe]
            else:
                raise ValueError

            exists_p = min_count == 1 and max_count is None

            for s, o_set in ops.items():
                if exists_p:
                    if o_set & filler_inds:
                        ret |= {s}
                else:
                    count = len(o_set & filler_inds)
                    if count >= min_count and (max_count is None or count <= max_count):
                        ret |= {s}
        else:
            subs = self._some_values_subject_index(pe)

            for s in subs:
                count = 0
                for o in self.object_property_values(s, pe, not self._sub_properties):
                    if {o} & filler_inds:
                        count = count + 1
                        if max_count is None and count >= min_count:
                            break
                if count >= min_count and (max_count is None or count <= max_count):
                    ret |= {s}

        return frozenset(ret)

    def _lazy_cache_data_prop(self, pe: OWLDataPropertyExpression) -> None:
        """Get all individuals and values involved in this data property and put them in a Dict."""
        assert (isinstance(pe, OWLDataProperty))
        if pe in self._data_prop:
            return

        opc: Dict[OWLNamedIndividual, Set[OWLLiteral]] = dict()

        # shortcut for owlready2
        from owlapy.owl_ontology import Ontology
        if isinstance(self._ontology, Ontology):
            import owlready2
            # _x => owlready2 objects
            for s_x, o_x in self._retrieve_triples(pe):
                if isinstance(s_x, owlready2.Thing):
                    o_literal = OWLLiteral(o_x)
                    s = OWLNamedIndividual(IRI.create(s_x.iri))
                    if s not in opc:
                        opc[s] = set()
                    opc[s].add(o_literal)
        else:
            for s in self._ind_set:
                values = set(self.data_property_values(s, pe))
                if len(values) > 0:
                    opc[s] = values

        self._data_prop[pe] = MappingProxyType(opc)

    # single dispatch is still not implemented in mypy, see https://github.com/python/mypy/issues/2904
    @singledispatchmethod
    def _find_instances(self, ce: OWLClassExpression) -> FrozenSet[OWLNamedIndividual]:
        raise NotImplementedError(ce)

    @_find_instances.register
    def _(self, c: OWLClass) -> FrozenSet[OWLNamedIndividual]:
        if self._ontology.is_modified and (self.class_cache or self._property_cache):
            self.reset_and_disable_cache()
        if self.class_cache:
            self._lazy_cache_class(c)
            return self._cls_to_ind[c]
        else:
            return frozenset(self.get_instances_from_owl_class(c))

    @_find_instances.register
    def _(self, ce: OWLObjectUnionOf) -> FrozenSet[OWLNamedIndividual]:
        return reduce(operator.or_, map(self._find_instances, ce.operands()))

    @_find_instances.register
    def _(self, ce: OWLObjectIntersectionOf) -> FrozenSet[OWLNamedIndividual]:
        return reduce(operator.and_, map(self._find_instances, ce.operands()))

    @_find_instances.register
    def _(self, ce: OWLObjectSomeValuesFrom) -> FrozenSet[OWLNamedIndividual]:
        p = ce.get_property()
        assert isinstance(p, OWLObjectPropertyExpression)
        if not self._property_cache and ce.get_filler().is_owl_thing():
            return self._some_values_subject_index(p)

        filler_ind = self._find_instances(ce.get_filler())

        ind = self._find_some_values(p, filler_ind)

        return ind

    @_find_instances.register
    def _(self, ce: OWLObjectComplementOf) -> FrozenSet[OWLNamedIndividual]:
        if self._negation_default:
            all_ = frozenset(self._ontology.individuals_in_signature())
            complement_ind = self._find_instances(ce.get_operand())
            return all_ ^ complement_ind
        else:
            # TODO! XXX
            if not self.__warned & 1:
                logger.warning("Object Complement Of not implemented at %s", ce)
                self.__warned |= 1
            return frozenset()
            # if self.complement_as_negation:
            #     ...
            # else:
            #     self._lazy_cache_negation

    @_find_instances.register
    def _(self, ce: OWLObjectAllValuesFrom) -> FrozenSet[OWLNamedIndividual]:
        return self._find_instances(
            OWLObjectSomeValuesFrom(
                property=ce.get_property(),
                filler=ce.get_filler().get_object_complement_of().get_nnf()
            ).get_object_complement_of())

    @_find_instances.register
    def _(self, ce: OWLObjectOneOf) -> FrozenSet[OWLNamedIndividual]:
        return frozenset(ce.individuals())

    @_find_instances.register
    def _(self, ce: OWLObjectHasValue) -> FrozenSet[OWLNamedIndividual]:
        return self._find_instances(ce.as_some_values_from())

    @_find_instances.register
    def _(self, ce: OWLObjectMinCardinality) -> FrozenSet[OWLNamedIndividual]:
        return self._get_instances_object_card_restriction(ce)

    @_find_instances.register
    def _(self, ce: OWLObjectMaxCardinality) -> FrozenSet[OWLNamedIndividual]:
        all_ = frozenset(self._ontology.individuals_in_signature())
        min_ind = self._find_instances(OWLObjectMinCardinality(cardinality=ce.get_cardinality() + 1,
                                                               property=ce.get_property(),
                                                               filler=ce.get_filler()))
        return all_ ^ min_ind

    @_find_instances.register
    def _(self, ce: OWLObjectExactCardinality) -> FrozenSet[OWLNamedIndividual]:
        return self._get_instances_object_card_restriction(ce)

    def _get_instances_object_card_restriction(self, ce: OWLObjectCardinalityRestriction):
        p = ce.get_property()
        assert isinstance(p, OWLObjectPropertyExpression)

        if isinstance(ce, OWLObjectMinCardinality):
            min_count = ce.get_cardinality()
            max_count = None
        elif isinstance(ce, OWLObjectExactCardinality):
            min_count = max_count = ce.get_cardinality()
        elif isinstance(ce, OWLObjectMaxCardinality):
            min_count = 0
            max_count = ce.get_cardinality()
        else:
            assert isinstance(ce, OWLObjectCardinalityRestriction)
            raise NotImplementedError
        assert min_count >= 0
        assert max_count is None or max_count >= 0

        filler_ind = self._find_instances(ce.get_filler())

        ind = self._find_some_values(p, filler_ind, min_count=min_count, max_count=max_count)

        return ind

    @_find_instances.register
    def _(self, ce: OWLDataSomeValuesFrom) -> FrozenSet[OWLNamedIndividual]:
        pe = ce.get_property()
        filler = ce.get_filler()
        assert isinstance(pe, OWLDataProperty)

        if self._ontology.is_modified and (self.class_cache or self._property_cache):
            self.reset_and_disable_cache()
        property_cache = self._property_cache

        if property_cache:
            self._lazy_cache_data_prop(pe)
            dps = self._data_prop[pe]
        else:
            subs = self._some_values_subject_index(pe)

        ind = set()

        if isinstance(filler, OWLDatatype):
            if property_cache:
                # TODO: Currently we just assume that the values are of the given type (also done in DLLearner)
                for s in dps.keys():
                    ind |= {s}
            else:
                for s in subs:
                    for lit in self.data_property_values(s, pe):
                        if lit.get_datatype() == filler:
                            ind |= {s}
                            break
        elif isinstance(filler, OWLDataOneOf):
            values = set(filler.values())
            if property_cache:
                for s, literals in dps.items():
                    if literals & values:
                        ind |= {s}
            else:
                for s in subs:
                    for lit in self.data_property_values(s, pe):
                        if lit in values:
                            ind |= {s}
                            break
        elif isinstance(filler, OWLDataComplementOf):
            temp = self._find_instances(
                OWLDataSomeValuesFrom(property=pe, filler=filler.get_data_range()))
            if property_cache:
                subs = set()
                for s in dps.keys():
                    subs |= {s}

            ind = subs.difference(temp)
        elif isinstance(filler, OWLDataUnionOf):
            operands = [OWLDataSomeValuesFrom(pe, op) for op in filler.operands()]
            ind = reduce(operator.or_, map(self._find_instances, operands))
        elif isinstance(filler, OWLDataIntersectionOf):
            operands = [OWLDataSomeValuesFrom(pe, op) for op in filler.operands()]
            ind = reduce(operator.and_, map(self._find_instances, operands))
        elif isinstance(filler, OWLDatatypeRestriction):
            def res_to_callable(res: OWLFacetRestriction):
                op = res.get_facet().operator
                v = res.get_facet_value()

                def inner(lv: OWLLiteral):
                    return op(lv, v)

                return inner

            apply = FunctionType.__call__

            facet_restrictions = tuple(map(res_to_callable, filler.get_facet_restrictions()))

            def include(lv: OWLLiteral):
                return lv.get_datatype() == filler.get_datatype() and \
                    all(map(apply, facet_restrictions, repeat(lv)))

            if property_cache:
                for s, literals in dps.items():
                    for lit in literals:
                        if include(lit):
                            ind |= {s}
                            break
            else:
                for s in subs:
                    for lit in self.data_property_values(s, pe):
                        if include(lit):
                            ind |= {s}
                            break
        else:
            raise ValueError

        r = frozenset(ind)
        return r

    @_find_instances.register
    def _(self, ce: OWLDataAllValuesFrom) -> FrozenSet[OWLNamedIndividual]:
        filler = ce.get_filler()
        if isinstance(filler, OWLDataComplementOf):
            filler = filler.get_data_range()
        else:
            filler = OWLDataComplementOf(filler)
        return self._find_instances(
            OWLDataSomeValuesFrom(
                property=ce.get_property(),
                filler=filler
            ).get_object_complement_of())

    @_find_instances.register
    def _(self, ce: OWLDataHasValue) -> FrozenSet[OWLNamedIndividual]:
        return self._find_instances(ce.as_some_values_from())

    def _lazy_cache_class(self, c: OWLClass) -> None:
        if c in self._cls_to_ind:
            return
        temp = self.get_instances_from_owl_class(c)
        self._cls_to_ind[c] = frozenset(temp)

    def get_instances_from_owl_class(self, c: OWLClass):
        if c.is_owl_thing():
            yield from self._ontology.individuals_in_signature()
        elif isinstance(c, OWLClass):
            c_x: owlready2.ThingClass = self._world[c.str]
            for i in c_x.instances(world=self._world):
                if isinstance(i, owlready2.Thing):
                    yield OWLNamedIndividual(IRI.create(i.iri))

    def _retrieve_triples(self, pe: OWLPropertyExpression) -> Iterable:
        """Retrieve all subject/object pairs for the given property."""

        if isinstance(pe, OWLObjectPropertyExpression):
            retrieval_func = self.sub_object_properties
            p_x: owlready2.ObjectProperty = self._ontology._world[pe.get_named_property().str]
        else:
            retrieval_func = self.sub_data_properties
            p_x: owlready2.DataProperty = self._ontology._world[pe.str]

        relations = p_x.get_relations()
        if self._sub_properties:
            # Retrieve the subject/object pairs for all sub properties of pe
            indirect_relations = chain.from_iterable(
                map(lambda x: self._ontology._world[x.str].get_relations(),
                    retrieval_func(pe, direct=False)))
            # If pe is an OWLObjectInverseOf we need to swap the pairs
            if isinstance(pe, OWLObjectInverseOf):
                indirect_relations = ((r[1], r[0]) for r in indirect_relations)
            relations = chain(relations, indirect_relations)
        yield from relations

    def reset_and_disable_cache(self):
        self.class_cache = False
        self._property_cache = False
        self.reset()


class SyncReasoner(AbstractOWLReasoner):

    def create_justifications(self, owl_individuals: Set[OWLNamedIndividual] = None,
                              owl_class_expression: OWLClassExpression = None,
                              save: bool = False) -> List[Set[OWLAxiom]]:
        """
        Generate multiple justifications for why the given individual(s) are inferred to be instances of the specified class.

        Args:
            owl_individuals (Set[OWLNamedIndividual]): Set of individuals to explain.
            owl_class_expression (OWLClassExpression): Class expression to justify.
            save (bool): If True, saves all justifications in a new ontology as axioms.

        Returns:
            List[Set[OWLAxiom]]: Each item is a justification (set of OWLAxioms).
        """
        if owl_individuals is None or owl_class_expression is None:
            raise ValueError("Both owl_individuals and owl_class_expression are required.")

        from com.clarkparsia.owlapi.explanation import (
            BlackBoxExplanation, HSTExplanationGenerator, SatisfiabilityConverter
        )
        from openllet.owlapi import PelletReasonerFactory

        j_class_expr = self.mapper.map_(owl_class_expression)
        j_ontology = self._owlapi_ontology
        j_reasoner = self._owlapi_reasoner
        j_data_factory = self._owlapi_manager.getOWLDataFactory()

        reasoner_factory = PelletReasonerFactory.getInstance()
        blackbox_exp = BlackBoxExplanation(j_ontology, reasoner_factory, j_reasoner)
        explanation_gen = HSTExplanationGenerator(blackbox_exp)
        converter = SatisfiabilityConverter(j_data_factory)

        justifications = []

        for ind in owl_individuals:
            j_individual = self.mapper.map_(ind)
            class_assertion_axiom = j_data_factory.getOWLClassAssertionAxiom(j_class_expr, j_individual)
            unsat_class = converter.convert(class_assertion_axiom)

            j_explanations = explanation_gen.getExplanations(unsat_class)

            for j_expl in j_explanations:
                py_axioms = {self.mapper.map_(ax) for ax in j_expl}
                justifications.append(py_axioms)

        # Save to justifications.owl if requested
        if save:
            from owlapy.owl_ontology import SyncOntology
            from owlapy.iri import IRI

            # Create a new in-memory ontology to store justifications
            just_iri = IRI.create("http://example.org/justifications")
            just_ontology = SyncOntology(path=just_iri, load=False)

            for axiom_set in justifications:
                for axiom in axiom_set:
                    just_ontology.add_axiom(axiom)

            # Save to file
            save_path = "justifications.owl"
            just_ontology.save(save_path)
            print(f"Justifications saved to {os.path.abspath(save_path)}")

        return justifications

    def __init__(self, ontology: Union[SyncOntology, str], reasoner="HermiT"):
        """
        OWL reasoner that syncs to other reasoners like HermiT,Pellet,etc.

        Args:
            ontology(SyncOntology): Ontology that will be used by this reasoner.
               reasoner: Name of the reasoner. Possible values (case-sensitive): ["HermiT", "Pellet", "ELK", "JFact",
               "Openllet", "Structural"]. Default: "HermiT".
        """
        assert reasoner in ["HermiT", "Pellet", "ELK", "JFact", "Openllet", "Structural"], \
            (f"'{reasoner}' is not implemented. Available reasoners: ['HermiT', 'Pellet', 'ELK', 'JFact', 'Openllet', "
             f"'Structural']. "
             f"This field is case sensitive.")

        #  TODO: ELK does not support all reasoning methods. That means that mapping unsupported methods in owlapy will
        #   also raise NotImplementedError. Check for new release of elk and if any of these method is
        #   implemented, remove the `raise NotImplementedError` statement for the respective mapping
        #   implemented in this class. Current version of elk is 0.6.0.
        #   Maven releases: https://mvnrepository.com/artifact/io.github.liveontologies/elk-owlapi
        #   ElkReasoner GitHub link: https://github.com/liveontologies/elk-reasoner/blob/main/elk-owlapi/src/main/java/org/semanticweb/elk/owlapi/ElkReasoner.java

        if isinstance(ontology, SyncOntology):
            self.ontology = ontology
        elif isinstance(ontology, str):
            self.ontology = SyncOntology(ontology)

        self.reasoner_name = reasoner
        self._owlapi_manager = self.ontology.owlapi_manager
        self._owlapi_ontology = self.ontology.get_owlapi_ontology()
        self.mapper = self.ontology.mapper
        self.inference_types_mapping = import_and_include_axioms_generators()
        self._owlapi_reasoner = initialize_reasoner(reasoner, self._owlapi_ontology)

    def _instances(self, ce: OWLClassExpression, direct=False) -> Set[OWLNamedIndividual]:
        """
        Get the instances for a given class expression using HermiT.

        Args:
            ce (OWLClassExpression): The class expression in OWLAPY format.
            direct (bool): Whether to get direct instances or not. Defaults to False.

        Returns:
            set: A set of individuals classified by the given class expression.
        """
        mapped_ce = self.mapper.map_(ce)
        instances = self._owlapi_reasoner.getInstances(mapped_ce, direct)
        flattened_instances = instances.getFlattened()
        assert str(type(flattened_instances)) == "<java class 'java.util.LinkedHashSet'>"
        return {self.mapper.map_(ind) for ind in flattened_instances}

    def instances(self, ce: OWLClassExpression, direct: bool = False, timeout: int = 1000):
        return run_with_timeout(self._instances, timeout, (ce, direct))

    def equivalent_classes(self, ce: OWLClassExpression):
        """
        Gets the set of named classes that are equivalent to the specified class expression with
        respect to the set of reasoner axioms.

        Args:
            ce (OWLClassExpression): The class expression whose equivalent classes are to be retrieved.

        Returns:
            Equivalent classes of the given class expression.
        """
        classes = self._owlapi_reasoner.getEquivalentClasses(self.mapper.map_(ce)).getEntities()
        yield from [self.mapper.map_(cls) for cls in classes]

    def disjoint_classes(self, ce: OWLClassExpression, include_bottom_entity=False):
        """
        Gets the classes that are disjoint with the specified class expression.

        Args:
            ce (OWLClassExpression): The class expression whose disjoint classes are to be retrieved.
            include_bottom_entity(bool,optional): Whether to consider OWL Nothing. Defaults to False.

        Returns:
            Disjoint classes of the given class expression.
        """
        if self.reasoner_name == "ELK":
            raise NotImplementedError("`getDisjointClasses` is not yet implemented for ELK!")
        classes = self._owlapi_reasoner.getDisjointClasses(self.mapper.map_(ce)).getFlattened()
        if include_bottom_entity:
            yield from [self.mapper.map_(cls) for cls in classes]
        else:
            yield from [self.mapper.map_(cls) for cls in classes if not cls.isBottomEntity()]

    def sub_classes(self, ce: OWLClassExpression, direct=False, include_bottom_entity=False):
        """
         Gets the set of named classes that are the strict (potentially direct) subclasses of the
         specified class expression with respect to the reasoner axioms.

         Args:
             ce (OWLClassExpression): The class expression whose strict (direct) subclasses are to be retrieved.
             direct (bool, optional): Specifies if the direct subclasses should be retrieved (True) or if
                all subclasses (descendant) classes should be retrieved (False). Defaults to False.
             include_bottom_entity (bool, optional): Specifies if owl nothing should be returned or not.
        Returns:
            The subclasses of the given class expression depending on `direct` field.
        """
        classes = list(self._owlapi_reasoner.getSubClasses(self.mapper.map_(ce), direct).getFlattened())
        if include_bottom_entity:
            yield from [self.mapper.map_(cls) for cls in classes]
        else:
            yield from [self.mapper.map_(cls) for cls in classes if not cls.isBottomEntity()]

    def super_classes(self, ce: OWLClassExpression, direct=False):
        """
        Gets the stream of named classes that are the strict (potentially direct) super classes of
        the specified class expression with respect to the imports closure of the root ontology.

        Args:
             ce (OWLClassExpression): The class expression whose strict (direct) subclasses are to be retrieved.
             direct (bool, optional): Specifies if the direct superclasses should be retrieved (True) or if
                all superclasses (descendant) classes should be retrieved (False). Defaults to False.

        Returns:
            The subclasses of the given class expression depending on `direct` field.
        """
        classes = self._owlapi_reasoner.getSuperClasses(self.mapper.map_(ce), direct).getFlattened()
        yield from [self.mapper.map_(cls) for cls in classes]

    def data_property_domains(self, p: OWLDataProperty, direct: bool = False):
        """Gets the class expressions that are the direct or indirect domains of this property with respect to the
           imports closure of the root ontology.

        Args:
            p: The property expression whose domains are to be retrieved.
            direct: Specifies if the direct domains should be retrieved (True), or if all domains should be retrieved
                (False).

        Returns:
            :Let N = equivalent_classes(DataSomeValuesFrom(pe rdfs:Literal)). If direct is True: then if N is not
            empty then the return value is N, else the return value is the result of
            super_classes(DataSomeValuesFrom(pe rdfs:Literal), true). If direct is False: then the result of
            super_classes(DataSomeValuesFrom(pe rdfs:Literal), false) together with N if N is non-empty.
            (Note, rdfs:Literal is the top datatype).
        """
        if self.reasoner_name == "ELK":
            raise NotImplementedError("`getDataPropertyDomains` is not yet implemented by ELK!")
        yield from [self.mapper.map_(ce) for ce in
                    self._owlapi_reasoner.getDataPropertyDomains(self.mapper.map_(p), direct).getFlattened()]

    def object_property_domains(self, p: OWLObjectProperty, direct: bool = False):
        """Gets the class expressions that are the direct or indirect domains of this property with respect to the
           imports closure of the root ontology.

        Args:
            p: The property expression whose domains are to be retrieved.
            direct: Specifies if the direct domains should be retrieved (True), or if all domains should be retrieved
                (False).

        Returns:
            :Let N = equivalent_classes(ObjectSomeValuesFrom(pe owl:Thing)). If direct is True: then if N is not empty
            then the return value is N, else the return value is the result of
            super_classes(ObjectSomeValuesFrom(pe owl:Thing), true). If direct is False: then the result of
            super_classes(ObjectSomeValuesFrom(pe owl:Thing), false) together with N if N is non-empty.
        """
        if self.reasoner_name == "ELK":
            raise NotImplementedError("`getObjectPropertyDomains` is not yet implemented by ELK!")
        yield from [self.mapper.map_(ce) for ce in
                    self._owlapi_reasoner.getObjectPropertyDomains(self.mapper.map_(p), direct).getFlattened()]

    def object_property_ranges(self, p: OWLObjectProperty, direct: bool = False):
        """Gets the class expressions that are the direct or indirect ranges of this property with respect to the
           imports closure of the root ontology.

        Args:
            p: The property expression whose ranges are to be retrieved.
            direct: Specifies if the direct ranges should be retrieved (True), or if all ranges should be retrieved
                (False).

        Returns:
            :Let N = equivalent_classes(ObjectSomeValuesFrom(ObjectInverseOf(pe) owl:Thing)). If direct is True: then
            if N is not empty then the return value is N, else the return value is the result of
            super_classes(ObjectSomeValuesFrom(ObjectInverseOf(pe) owl:Thing), true). If direct is False: then
            the result of super_classes(ObjectSomeValuesFrom(ObjectInverseOf(pe) owl:Thing), false) together with N
            if N is non-empty.
        """
        if self.reasoner_name == "ELK":
            raise NotImplementedError("`getObjectPropertyRanges` is not yet implemented by ELK!")
        yield from [self.mapper.map_(ce) for ce in
                    self._owlapi_reasoner.getObjectPropertyRanges(self.mapper.map_(p), direct).getFlattened()]

    def sub_object_properties(self, p: OWLObjectProperty, direct: bool = False, include_bottom_entity=False):
        """Gets the stream of simplified object property expressions that are the strict (potentially direct)
        subproperties of the specified object property expression with respect to the imports closure of the root
        ontology.

        Args:
            p: The object property expression whose strict (direct) subproperties are to be retrieved.
            direct: Specifies if the direct subproperties should be retrieved (True) or if the all subproperties
                (descendants) should be retrieved (False).
            include_bottom_entity (bool, optional): Specifies if the bottomObjectProperty should be returned.

        Returns:
            If direct is True, simplified object property expressions, such that for each simplified object property
            expression, P, the set of reasoner axioms entails DirectSubObjectPropertyOf(P, pe).
            If direct is False, simplified object property expressions, such that for each simplified object property
            expression, P, the set of reasoner axioms entails StrictSubObjectPropertyOf(P, pe).
            If pe is equivalent to owl:bottomObjectProperty then nothing will be returned.
        """
        if include_bottom_entity:
            yield from [self.mapper.map_(pe) for pe in
                        self._owlapi_reasoner.getSubObjectProperties(self.mapper.map_(p), direct).getFlattened()]
        else:
            yield from [self.mapper.map_(pe) for pe in
                        self._owlapi_reasoner.getSubObjectProperties(self.mapper.map_(p), direct).getFlattened()
                        if not pe.isBottomEntity()]

    def super_object_properties(self, p: OWLObjectProperty, direct: bool = False):
        """Gets the stream of object properties that are the strict (potentially direct) super properties of the
         specified object property with respect to the imports closure of the root ontology.

         Args:
             p (OWLObjectPropertyExpression): The object property expression whose super properties are to be
                                                retrieved.
             direct (bool): Specifies if the direct super properties should be retrieved (True) or if the all
                            super properties (ancestors) should be retrieved (False).

         Returns:
             Iterable of super properties.
         """
        yield from [self.mapper.map_(pe) for pe in
                    self._owlapi_reasoner.getSuperObjectProperties(self.mapper.map_(p), direct).getFlattened()]

    def sub_data_properties(self, p: OWLDataProperty, direct: bool = False, include_bottom_entity=False):
        """Gets the set of named data properties that are the strict (potentially direct) subproperties of the
        specified data property expression with respect to the imports closure of the root ontology.

        Args:
            p: The data property whose strict (direct) subproperties are to be retrieved.
            direct: Specifies if the direct subproperties should be retrieved (True) or if the all subproperties
                (descendants) should be retrieved (False).
            include_bottom_entity: Specifies if the bottomDataProperty should be returned.

        Returns:
            If direct is True, each property P where the set of reasoner axioms entails DirectSubDataPropertyOf(P, pe).
            If direct is False, each property P where the set of reasoner axioms entails
            StrictSubDataPropertyOf(P, pe). If pe is equivalent to owl:bottomDataProperty then nothing will be
            returned.
        """
        if self.reasoner_name == "ELK":
            raise NotImplementedError("`getSubDataProperties` is not yet implemented by ELK!")
        if include_bottom_entity:
            yield from [self.mapper.map_(pe) for pe in
                        self._owlapi_reasoner.getSubDataProperties(self.mapper.map_(p), direct).getFlattened()]
        else:
            yield from [self.mapper.map_(pe) for pe in
                        self._owlapi_reasoner.getSubDataProperties(self.mapper.map_(p), direct).getFlattened()
                        if not pe.isBottomEntity()]

    def super_data_properties(self, p: OWLDataProperty, direct: bool = False):
        """Gets the stream of data properties that are the strict (potentially direct) super properties of the
         specified data property with respect to the imports closure of the root ontology.

         Args:
             p (OWLDataProperty): The data property whose super properties are to be retrieved.
             direct (bool): Specifies if the direct super properties should be retrieved (True) or if the all
                            super properties (ancestors) should be retrieved (False).

         Returns:
             Iterable of super properties.
         """
        if self.reasoner_name == "ELK":
            raise NotImplementedError("`getSuperDataProperties` is not yet implemented by ELK!")
        yield from [self.mapper.map_(pe) for pe in
                    self._owlapi_reasoner.getSuperDataProperties(self.mapper.map_(p), direct).getFlattened()]

    def different_individuals(self, i: OWLNamedIndividual):
        """Gets the individuals that are different from the specified individual with respect to the set of
        reasoner axioms.

        Args:
            i: The individual whose different individuals are to be retrieved.

        Returns:
            All individuals x where the set of reasoner axioms entails DifferentIndividuals(ind x).
        """
        if self.reasoner_name == "ELK":
            raise NotImplementedError("`getDifferentIndividuals` is not yet implemented by ELK!")
        yield from [self.mapper.map_(ind) for ind in
                    self._owlapi_reasoner.getDifferentIndividuals(self.mapper.map_(i)).getFlattened()]

    def same_individuals(self, i: OWLNamedIndividual):
        """Gets the individuals that are the same as the specified individual with respect to the set of
        reasoner axioms.

        Args:
            i: The individual whose same individuals are to be retrieved.

        Returns:
            All individuals x where the root ontology imports closure entails SameIndividual(ind x).
        """
        yield from [self.mapper.map_(ind) for ind in
                    self.mapper.to_list(self._owlapi_reasoner.sameIndividuals(self.mapper.map_(i)))]

    def equivalent_object_properties(self, p: OWLObjectProperty):
        """Gets the simplified object properties that are equivalent to the specified object property with respect
        to the set of reasoner axioms.

        Args:
            p: The object property whose equivalent object properties are to be retrieved.

        Returns:
            All simplified object properties e where the root ontology imports closure entails
            EquivalentObjectProperties(op e). If op is unsatisfiable with respect to the set of reasoner axioms
            then owl:bottomDataProperty will be returned.
        """
        yield from [self.mapper.map_(pe) for pe in
                    self.mapper.to_list(self._owlapi_reasoner.equivalentObjectProperties(self.mapper.map_(p)))]

    def equivalent_data_properties(self, p: OWLDataProperty):
        """Gets the data properties that are equivalent to the specified data property with respect to the set of
        reasoner axioms.

        Args:
            p: The data property whose equivalent data properties are to be retrieved.

        Returns:
            All data properties e where the root ontology imports closure entails EquivalentDataProperties(dp e).
            If dp is unsatisfiable with respect to the set of reasoner axioms then owl:bottomDataProperty will
            be returned.
        """
        if self.reasoner_name == "ELK":
            raise NotImplementedError("`getEquivalentDataProperties` is not yet implemented by ELK!")
        yield from [self.mapper.map_(pe) for pe in
                    self.mapper.to_list(self._owlapi_reasoner.getEquivalentDataProperties(self.mapper.map_(p)))]

    def object_property_values(self, i: OWLNamedIndividual, p: OWLObjectProperty):
        """Gets the object property values for the specified individual and object property expression.

        Args:
            i: The individual that is the subject of the object property values.
            p: The object property expression whose values are to be retrieved for the specified individual.

        Returns:
            The named individuals such that for each individual j, the set of reasoner axioms entails
            ObjectPropertyAssertion(pe ind j).
        """
        if self.reasoner_name == "ELK":
            raise NotImplementedError("`getObjectPropertyValues` is not yet implemented by ELK!")
        yield from [self.mapper.map_(ind) for ind in
                    self._owlapi_reasoner.getObjectPropertyValues(self.mapper.map_(i),
                                                                  self.mapper.map_(p)).getFlattened()]

    def data_property_values(self, e: OWLEntity, p: OWLDataProperty):
        """Gets the data property values for the specified entity and data property expression.

        Args:
            e: The entity (usually an individual) that is the subject of the data property values.
            p: The data property expression whose values are to be retrieved for the specified individual.

        Returns:
            A set of OWLLiterals containing literals such that for each literal l in the set, the set of reasoner
            axioms entails DataPropertyAssertion(pe ind l).
        """
        yield from [self.mapper.map_(literal) for literal in
                    self.mapper.to_list(
                        self._owlapi_reasoner.dataPropertyValues(self.mapper.map_(e), self.mapper.map_(p)))]

    def disjoint_object_properties(self, p: OWLObjectProperty, include_bottom_entity=False):
        """Gets the simplified object properties that are disjoint with the specified object property with respect
        to the set of reasoner axioms.

        Args:
            p: The object property whose disjoint object properties are to be retrieved.
            include_bottom_entity(bool,optional): Whether to consider bottomObjectProperty.

        Returns:
            All simplified object properties e where the root ontology imports closure entails
            EquivalentObjectProperties(e ObjectPropertyComplementOf(op)) or
            StrictSubObjectPropertyOf(e ObjectPropertyComplementOf(op)).
        """
        if self.reasoner_name == "ELK":
            raise NotImplementedError("`getDisjointObjectProperties` is not yet implemented by ELK!")
        if include_bottom_entity:
            yield from [self.mapper.map_(pe) for pe in
                        self._owlapi_reasoner.getDisjointObjectProperties(self.mapper.map_(p)).getFlattened()]
        else:
            yield from [self.mapper.map_(pe) for pe in
                        self._owlapi_reasoner.getDisjointObjectProperties(self.mapper.map_(p)).getFlattened()
                        if not pe.isBottomEntity()]

    def disjoint_data_properties(self, p: OWLDataProperty, include_bottom_entity=False):
        """Gets the data properties that are disjoint with the specified data property with respect
        to the set of reasoner axioms.

        Args:
            p: The data property whose disjoint data properties are to be retrieved.
            include_bottom_entity(bool,optional): Whether to consider bottomDataProperty.

        Returns:
            All data properties e where the root ontology imports closure entails
            EquivalentDataProperties(e DataPropertyComplementOf(dp)) or
            StrictSubDataPropertyOf(e DataPropertyComplementOf(dp)).
        """
        if self.reasoner_name == "ELK":
            raise NotImplementedError("`getDisjointDataProperties` is not yet implemented by ELK!")
        if include_bottom_entity:
            yield from [self.mapper.map_(pe) for pe in
                        self._owlapi_reasoner.getDisjointDataProperties(self.mapper.map_(p)).getFlattened()]
        else:
            yield from [self.mapper.map_(pe) for pe in
                        self._owlapi_reasoner.getDisjointDataProperties(self.mapper.map_(p)).getFlattened()
                        if not pe.isBottomEntity()]

    def types(self, individual: OWLNamedIndividual, direct: bool = False):
        """Gets the named classes which are (potentially direct) types of the specified named individual.

        Args:
            individual: The individual whose types are to be retrieved.
            direct: Specifies if the direct types should be retrieved (True), or if all types should be retrieved
                (False).

        Returns:
            If direct is True, each named class C where the set of reasoner axioms entails
            DirectClassAssertion(C, ind). If direct is False, each named class C where the set of reasoner axioms
            entails ClassAssertion(C, ind).
        """
        yield from [self.mapper.map_(ind) for ind in
                    self._owlapi_reasoner.getTypes(self.mapper.map_(individual), direct).getFlattened()]

    def has_consistent_ontology(self) -> bool:
        """
        Check if the used ontology is consistent.

        Returns:
            bool: True if the ontology used by this reasoner is consistent, False otherwise.
        """
        return self._owlapi_reasoner.isConsistent()

    def infer_axioms(self, inference_types: list[str]) -> Iterable[OWLAxiom]:
        """
        Infer the specified inference type of axioms for the ontology managed by this instance's reasoner and
        return them.

        Args:
            inference_types: Axiom inference types: Avaliable options (can set more than 1):
             ["InferredClassAssertionAxiomGenerator", "InferredSubClassAxiomGenerator",
             "InferredDisjointClassesAxiomGenerator", "InferredEquivalentClassAxiomGenerator",
             "InferredEquivalentDataPropertiesAxiomGenerator","InferredEquivalentObjectPropertyAxiomGenerator",
             "InferredInverseObjectPropertiesAxiomGenerator","InferredSubDataPropertyAxiomGenerator",
             "InferredSubObjectPropertyAxiomGenerator","InferredDataPropertyCharacteristicAxiomGenerator",
             "InferredObjectPropertyCharacteristicAxiomGenerator"
             ]

        Returns:
            Iterable of inferred axioms.
        """
        # noinspection PyUnresolvedReferences
        from java.util import ArrayList
        # noinspection PyUnresolvedReferences
        from org.semanticweb.owlapi.util import InferredOntologyGenerator

        generators = ArrayList()
        for i in inference_types:
            if java_object := self.inference_types_mapping.get(i, None):
                generators.add(java_object)
        iog = InferredOntologyGenerator(self._owlapi_reasoner, generators)
        inferred_axioms = list(iog.getAxiomGenerators())
        for ia in inferred_axioms:
            for axiom in ia.createAxioms(self._owlapi_manager.getOWLDataFactory(), self._owlapi_reasoner):
                yield self.mapper.map_(axiom)

    def infer_axioms_and_save(self, output_path: str = None, output_format: str = None,
                              inference_types: list[str] = None):
        """
        Generates inferred axioms for the ontology managed by this instance's reasoner and saves them to a file.
        This function uses the OWL API to generate inferred class assertion axioms based on the ontology and reasoner
        associated with this instance. The inferred axioms are saved to the specified output file in the desired format.

        Args:
            output_path : The name of the file where the inferred axioms will be saved.
            output_format : The format in which to save the inferred axioms. Supported formats are:
                - "ttl" or "turtle" for Turtle format
                - "rdf/xml" for RDF/XML format
                - "owl/xml" for OWL/XML format
                If not specified, the format of the original ontology is used.
            inference_types: Axiom inference types: Avaliable options (can set more than 1):
             ["InferredClassAssertionAxiomGenerator", "InferredSubClassAxiomGenerator",
             "InferredDisjointClassesAxiomGenerator", "InferredEquivalentClassAxiomGenerator",
             "InferredEquivalentDataPropertiesAxiomGenerator","InferredEquivalentObjectPropertyAxiomGenerator",
             "InferredInverseObjectPropertiesAxiomGenerator","InferredSubDataPropertyAxiomGenerator",
             "InferredSubObjectPropertyAxiomGenerator","InferredDataPropertyCharacteristicAxiomGenerator",
             "InferredObjectPropertyCharacteristicAxiomGenerator"
             ]

        Returns:
            None (the file is saved to the specified directory)
        """
        # noinspection PyUnresolvedReferences
        from java.io import File, FileOutputStream
        # noinspection PyUnresolvedReferences
        from java.util import ArrayList
        # noinspection PyUnresolvedReferences
        from org.semanticweb.owlapi.util import InferredOntologyGenerator
        # noinspection PyUnresolvedReferences
        from org.semanticweb.owlapi.formats import TurtleDocumentFormat, RDFXMLDocumentFormat, OWLXMLDocumentFormat
        if output_format == "ttl" or output_format == "turtle":
            document_format = TurtleDocumentFormat()
        elif output_format == "rdf/xml":
            document_format = RDFXMLDocumentFormat()
        elif output_format == "owl/xml":
            document_format = OWLXMLDocumentFormat()
        else:
            document_format = self._owlapi_manager.getOntologyFormat(self._owlapi_ontology)
        generators = ArrayList()

        for i in inference_types:
            if java_object := self.inference_types_mapping.get(i, None):
                generators.add(java_object)
        iog = InferredOntologyGenerator(self._owlapi_reasoner, generators)
        # CD: No need to create a new ontology
        # inferred_axioms_ontology = self._owlapi_manager.createOntology()
        iog.fillOntology(self._owlapi_manager.getOWLDataFactory(), self._owlapi_ontology)
        self._owlapi_manager.saveOntology(self._owlapi_ontology,
                                          document_format,
                                          FileOutputStream(File(output_path).getAbsoluteFile()))

    def generate_and_save_inferred_class_assertion_axioms(self, output="temp.ttl", output_format: str = None):
        """
        Generates inferred class assertion axioms for the ontology managed by this instance's reasoner and saves them
        to a file. This function uses the OWL API to generate inferred class assertion axioms based on the ontology
        and reasoner associated with this instance. The inferred axioms are saved to the specified output file in
        the desired format.
        Parameters:
        -----------
        output : str, optional
            The name of the file where the inferred axioms will be saved. Default is "temp.ttl".
        output_format : str, optional
            The format in which to save the inferred axioms. Supported formats are:
            - "ttl" or "turtle" for Turtle format
            - "rdf/xml" for RDF/XML format
            - "owl/xml" for OWL/XML format
            If not specified, the format of the original ontology is used.
        Notes:
        ------
        - The function supports saving in multiple formats: Turtle, RDF/XML, and OWL/XML.
        - The inferred axioms are generated using the reasoner associated with this instance and the OWL API's
          InferredClassAssertionAxiomGenerator.
        - The inferred axioms are added to a new ontology which is then saved in the specified format.
        Example:
        --------
        >>> instance.generate_and_save_inferred_class_assertion_axioms(output="inferred_axioms.ttl", format="ttl")
        This will save the inferred class assertion axioms to the file "inferred_axioms.ttl" in Turtle format.
        """
        self.infer_axioms_and_save(output, output_format, ["InferredClassAssertionAxiomGenerator"])

    def is_entailed(self, axiom: OWLAxiom) -> bool:
        """A convenience method that determines if the specified axiom is entailed by the set of reasoner axioms.

        Args:
            axiom: The axiom to check for entailment.

        Return:
            True if the axiom is entailed by the reasoner axioms and False otherwise.
        """
        return bool(self._owlapi_reasoner.isEntailed(self.mapper.map_(axiom)))

    def is_satisfiable(self, ce: OWLClassExpression) -> bool:
        """A convenience method that determines if the specified class expression is satisfiable with respect
        to the reasoner axioms.

        Args:
            ce: The class expression to check for satisfiability.

        Return:
            True if the class expression is satisfiable by the reasoner axioms and False otherwise.
        """

        return bool(self._owlapi_reasoner.isSatisfiable(self.mapper.map_(ce)))

    def unsatisfiable_classes(self):
        """A convenience method that obtains the classes in the signature of the root ontology that are
        unsatisfiable."""
        return self.mapper.map_(self._owlapi_reasoner.unsatisfiableClasses())

    def get_root_ontology(self) -> AbstractOWLOntology:
        return self.ontology


def initialize_reasoner(reasoner: str, owlapi_ontology):
    # () Create a reasoner using the ontology
    if reasoner == "HermiT":
        # noinspection PyUnresolvedReferences
        from org.semanticweb.HermiT import ReasonerFactory
        owlapi_reasoner = ReasonerFactory().createReasoner(owlapi_ontology)
        assert owlapi_reasoner.getReasonerName() == "HermiT"
    elif reasoner == "ELK":
        from org.semanticweb.elk.owlapi import ElkReasonerFactory
        owlapi_reasoner = ElkReasonerFactory().createReasoner(owlapi_ontology)
    elif reasoner == "JFact":
        # noinspection PyUnresolvedReferences
        from uk.ac.manchester.cs.jfact import JFactFactory
        owlapi_reasoner = JFactFactory().createReasoner(owlapi_ontology)
    elif reasoner == "Pellet":
        # noinspection PyUnresolvedReferences
        from openllet.owlapi import PelletReasonerFactory
        owlapi_reasoner = PelletReasonerFactory().createReasoner(owlapi_ontology)
    elif reasoner == "Openllet":
        # noinspection PyUnresolvedReferences
        from openllet.owlapi import OpenlletReasonerFactory
        owlapi_reasoner = OpenlletReasonerFactory().getInstance().createReasoner(owlapi_ontology)
    elif reasoner == "Structural":
        # noinspection PyUnresolvedReferences
        from org.semanticweb.owlapi.reasoner.structural import StructuralReasonerFactory
        owlapi_reasoner = StructuralReasonerFactory().createReasoner(owlapi_ontology)
    else:
        raise NotImplementedError("Not implemented")
    return owlapi_reasoner


def import_and_include_axioms_generators():
    # noinspection PyUnresolvedReferences
    from org.semanticweb.owlapi.util import (InferredClassAssertionAxiomGenerator, InferredSubClassAxiomGenerator,
                                             InferredEquivalentClassAxiomGenerator,
                                             InferredDisjointClassesAxiomGenerator,
                                             InferredEquivalentDataPropertiesAxiomGenerator,
                                             InferredEquivalentObjectPropertyAxiomGenerator,
                                             InferredInverseObjectPropertiesAxiomGenerator,
                                             InferredSubDataPropertyAxiomGenerator,
                                             InferredSubObjectPropertyAxiomGenerator,
                                             InferredDataPropertyCharacteristicAxiomGenerator,
                                             InferredObjectPropertyCharacteristicAxiomGenerator)

    return {"InferredClassAssertionAxiomGenerator": InferredClassAssertionAxiomGenerator(),
            "InferredSubClassAxiomGenerator": InferredSubClassAxiomGenerator(),
            "InferredDisjointClassesAxiomGenerator": InferredDisjointClassesAxiomGenerator(),
            "InferredEquivalentClassAxiomGenerator": InferredEquivalentClassAxiomGenerator(),
            "InferredInverseObjectPropertiesAxiomGenerator": InferredInverseObjectPropertiesAxiomGenerator(),
            "InferredEquivalentDataPropertiesAxiomGenerator": InferredEquivalentDataPropertiesAxiomGenerator(),
            "InferredEquivalentObjectPropertyAxiomGenerator": InferredEquivalentObjectPropertyAxiomGenerator(),
            "InferredSubDataPropertyAxiomGenerator": InferredSubDataPropertyAxiomGenerator(),
            "InferredSubObjectPropertyAxiomGenerator": InferredSubObjectPropertyAxiomGenerator(),
            "InferredDataPropertyCharacteristicAxiomGenerator": InferredDataPropertyCharacteristicAxiomGenerator(),
            "InferredObjectPropertyCharacteristicAxiomGenerator": InferredObjectPropertyCharacteristicAxiomGenerator()}


class EBR(AbstractOWLReasoner):
    """The Embedding-Based Reasoner uses neural embeddings to retrieve concept instances from knowledge bases. """

    STR_IRI_SUBCLASSOF = "http://www.w3.org/2000/01/rdf-schema#subClassOf"
    STR_IRI_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    STR_IRI_OWL_CLASS = "http://www.w3.org/2002/07/owl#Class"
    STR_IRI_OBJECT_PROPERTY = "http://www.w3.org/2002/07/owl#ObjectProperty"
    STR_IRI_RANGE = "http://www.w3.org/2000/01/rdf-schema#range"
    STR_IRI_DOMAIN = "http://www.w3.org/2000/01/rdf-schema#domain"
    STR_IRI_DOUBLE = "http://www.w3.org/2001/XMLSchema#double"
    STR_IRI_BOOLEAN = "http://www.w3.org/2001/XMLSchema#boolean"
    STR_IRI_DATA_PROPERTY = "http://www.w3.org/2002/07/owl#DatatypeProperty"
    STR_IRI_SUBPROPERTY = "http://www.w3.org/2000/01/rdf-schema#subPropertyOf"

    def __init__(self, ontology: NeuralOntology):
        super().__init__(ontology)
        self.gamma = ontology.gamma
        self.ontology = ontology
        self.model = ontology.model

    def __str__(self):
        return f"Embedding-Based Reasoner using: {self.model.model} with gamma: {self.gamma}"

    @cached_property
    def inferred_object_properties(self) -> set:
        return set(self.object_properties_in_signature())

    @cached_property
    def inferred_owl_classes(self) -> set:
        return set(self.classes_in_signature())

    def predict(self, h: List[str] = None, r: List[str] = None, t: List[str] = None) -> List[Tuple[str, float]]:
        return self.ontology.predict(h=h, r=r, t=t)

    def predict_individuals_of_owl_class(self, owl_class: OWLClass) -> List[OWLNamedIndividual]:
        top_entities = set()
        # Find all subconcepts
        owl_classes = [owl_class] + self.sub_classes(owl_class)
        top_entity: str
        for top_entity, score in self.predict(h=None,
                                              r=self.STR_IRI_TYPE,
                                              t=[c.iri.str for c in owl_classes]):
            top_entities.add(top_entity)
        return [OWLNamedIndividual(i) for i in top_entities]

    def abox(self, str_iri: str) -> Generator[
        Tuple[
            Tuple[OWLNamedIndividual, OWLProperty, OWLClass],
            Tuple[OWLObjectProperty, OWLObjectProperty, OWLNamedIndividual],
            Tuple[OWLObjectProperty, OWLDataProperty, OWLLiteral]], None, None]:
        # Initialize an owl named individual object.
        subject_ = OWLNamedIndividual(str_iri)
        # Return a triple indicating the type.
        for cl in self.types(subject_):
            yield subject_, OWLProperty(self.STR_IRI_TYPE), cl

        # Return a triple based on an object property.
        for op in self.object_properties_in_signature():
            for o in self.object_property_values(subject_, op):
                yield subject_, op, o
        # TODO: Data properties

    def classes_in_signature(self) -> List[OWLClass]:
        return self.ontology.classes_in_signature()

    def individuals_in_signature(self) -> List[OWLNamedIndividual]:
        return self.ontology.individuals_in_signature()

    def data_properties_in_signature(self) -> List[OWLDataProperty]:
        return self.ontology.data_properties_in_signature()

    def object_properties_in_signature(self) -> List[OWLObjectProperty]:
        return self.ontology.object_properties_in_signature()

    def direct_subconcepts(self, named_concept: OWLClass) -> List[OWLClass]:
        if self.STR_IRI_SUBCLASSOF not in self.model.relation_to_idx:
            return []
        return [OWLClass(top_entity) for top_entity, score in self.predict(h=None,
                                                                           r=self.STR_IRI_SUBCLASSOF,
                                                                           t=named_concept.str)]

    def sub_classes(self, named_concept: OWLClass, visited=None) -> List[OWLClass]:
        if visited is None:
            visited = set()
        all_subconcepts = []
        for subconcept in self.direct_subconcepts(named_concept):
            if subconcept not in self.classes_in_signature() or subconcept in visited:
                continue
            visited.add(subconcept)
            all_subconcepts.append(subconcept)
            all_subconcepts.extend(self.sub_classes(subconcept, visited))
        return all_subconcepts

    def most_general_classes(self) -> List[OWLClass]:  # pragma: no cover
        """At least it has single subclass and there is no superclass"""
        owl_concepts_not_having_parents = set()
        for c in self.classes_in_signature():
            direct_parents = set()
            for x in self.get_direct_parents(c):
                # Ignore c if (c subclass x) \in KG.
                direct_parents.add(x)
                break
            if len(direct_parents) == 0:
                for sub_c in self.sub_classes(named_concept=c):
                    owl_concepts_not_having_parents.add(sub_c)
                    break
        return [i for i in owl_concepts_not_having_parents]

    def least_general_named_concepts(self) -> Generator[OWLClass, None, None]:  # pragma: no cover
        """At least it has single superclass and there is no subclass"""
        for _class in self.classes_in_signature():
            for concept in self.sub_classes(
                    named_concept=_class
            ):
                break
            else:
                # checks if superclasses is not empty -> there is at least one superclass
                if list(
                        self.get_direct_parents(_class)
                ):
                    yield _class

    def get_direct_parents(self, named_concept: OWLClass) -> List[OWLClass]:  # pragma: no cover
        return [OWLClass(entity) for entity, score in self.predict(h=named_concept.str, r=self.STR_IRI_SUBCLASSOF,
                                                                   t=None)]

    def super_classes(self, ce: OWLClassExpression, direct: bool = False) -> Iterable[OWLClassExpression]:
        if not isinstance(ce, OWLClass):
            raise NotImplementedError("Only named classes are supported in the embedding-based reasoner")

        if direct:
            return self.get_direct_parents(ce)
        else:
            visited = set()
            all_superclasses = []

            def collect_superclasses(concept):
                for parent in self.get_direct_parents(concept):
                    if parent not in visited:
                        visited.add(parent)
                        all_superclasses.append(parent)
                        collect_superclasses(parent)

            collect_superclasses(ce)
            return all_superclasses

    def types(self, individual: OWLNamedIndividual) -> List[OWLClass]:
        return [OWLClass(top_entity) for top_entity, score in
                self.predict(h=individual.str, r=self.STR_IRI_TYPE, t=None)]

    def boolean_data_properties(self) -> Generator[OWLDataProperty, None, None]:  # pragma: no cover
        return [OWLDataProperty(top_entity) for top_entity, score in self.predict(h=None, r=self.STR_IRI_RANGE,
                                                                                  t=self.STR_IRI_BOOLEAN)]

    def double_data_properties(self) -> List[OWLDataProperty]:  # pragma: no cover
        return [OWLDataProperty(top_entity) for top_entity, score in self.predict(
            h=None,
            r=self.STR_IRI_RANGE,
            t=self.STR_IRI_DOUBLE)]

    def individuals(self, expression: OWLClassExpression = None, named_individuals: bool = False) -> Generator[
        OWLNamedIndividual, None, None]:
        if expression is None or expression.is_owl_thing():
            yield from self.individuals_in_signature()
        else:
            yield from self.instances(expression)

    def instances(self, expression: OWLClassExpression, direct: bool = False, timeout: int = 1000) -> Generator[
        OWLNamedIndividual, None, None]:
        if isinstance(expression, OWLClass):
            """ Given an OWLClass A, retrieve its instances Retrieval(A)={ x | phi(x, type, A) ≥ γ } """
            yield from self.predict_individuals_of_owl_class(expression)
        elif isinstance(expression, OWLObjectComplementOf):
            """ Handling complement of class expressions:
            Given an OWLObjectComplementOf ¬A, hence (A is an OWLClass),
            retrieve its instances => Retrieval(¬A)= All Instance Set-DIFF { x | phi(x, type, A) ≥ γ } """
            excluded_individuals: Set[OWLNamedIndividual]
            excluded_individuals = set(self.instances(expression.get_operand()))
            all_individuals = {i for i in self.individuals_in_signature()}
            yield from all_individuals - excluded_individuals
        elif isinstance(expression, OWLObjectIntersectionOf):
            """ Handling intersection of class expressions:
            Given an OWLObjectIntersectionOf (C ⊓ D),  
            retrieve its instances by intersecting the instance of each operands.
            {x | phi(x, type, C) ≥ γ} ∩ {x | phi(x, type, D) ≥ γ}
            """
            # Get the class expressions
            #
            result = None
            for op in expression.operands():
                retrieval_of_op = {_ for _ in self.instances(expression=op)}
                if result is None:
                    result = retrieval_of_op
                else:
                    result = result.intersection(retrieval_of_op)
            yield from result
        elif isinstance(expression, OWLObjectAllValuesFrom):
            """
            Given an OWLObjectAllValuesFrom ∀ r.C, retrieve its instances => 
            Retrieval(¬∃ r.¬C) =             
            Entities \setminus {x | ∃ y: \phi(y, type, C) < \gamma AND \phi(x,r,y)  ≥ \gamma } 
            """
            object_property = expression.get_property()
            filler_expression = expression.get_filler()
            yield from self.instances(OWLObjectComplementOf(
                OWLObjectSomeValuesFrom(object_property, OWLObjectComplementOf(filler_expression))))

        elif isinstance(expression, OWLObjectMinCardinality) or isinstance(expression, OWLObjectSomeValuesFrom):
            """
            Given an OWLObjectSomeValuesFrom ∃ r.C, retrieve its instances => 
            Retrieval(∃ r.C) = 
            {x | ∃ y : phi(y, type, C) ≥ \gamma AND phi(x, r, y) ≥ \gamma }  
            """
            object_property = expression.get_property()
            filler_expression = expression.get_filler()
            cardinality = 1
            if isinstance(expression, OWLObjectMinCardinality):
                cardinality = expression.get_cardinality()

            object_individuals = self.instances(filler_expression)
            result = Counter()
            subjects = self.get_individuals_with_object_property(
                objs=object_individuals,
                object_property=object_property)
            # Update the counter for all subjects found
            result.update(subjects)
            # Yield only those individuals who meet the cardinality requirement
            for individual, count in result.items():
                if count >= cardinality:
                    yield individual
        elif isinstance(expression, OWLObjectMaxCardinality):
            object_property = expression.get_property()
            filler_expression = expression.get_filler()
            cardinality = expression.get_cardinality()

            # Get all individuals that are instances of the filler expression.
            object_individuals = list(self.instances(filler_expression))

            # Initialize counts for every subject in the signature.
            counts = {ind.str: (ind, 0) for ind in self.individuals_in_signature()}

            # Retrieve all subjects related to any of the object individuals at once.
            subject_individuals = self.get_individuals_with_object_property(
                objs=object_individuals,
                object_property=object_property
            )

            # Increment counts for each related subject.
            for subj in subject_individuals:
                if subj.str in counts:
                    owl_obj, cnt = counts[subj.str]
                    counts[subj.str] = (owl_obj, cnt + 1)

            # Yield only those subjects whose count does not exceed the max cardinality.
            yield from {
                ind for _, (ind, cnt) in counts.items()
                if cnt <= cardinality
            }


        elif isinstance(expression, OWLObjectUnionOf):
            result = None
            for op in expression.operands():
                retrieval_of_op = {_ for _ in self.instances(expression=op)}
                if result is None:
                    result = retrieval_of_op
                else:
                    result = result.union(retrieval_of_op)
            yield from result

        elif isinstance(expression, OWLObjectOneOf):
            yield from expression.individuals()
        else:
            raise NotImplementedError(f"Instances for {type(expression)} are not implemented yet")

    def object_property_values(
            self, subject: OWLNamedIndividual, object_property: OWLObjectProperty = None) -> List[OWLNamedIndividual]:
        assert isinstance(object_property, OWLObjectProperty) or isinstance(object_property, OWLObjectInverseOf)
        if is_inverse := isinstance(object_property, OWLObjectInverseOf):
            object_property = object_property.get_inverse()
        return [OWLNamedIndividual(top_entity) for top_entity, score in self.predict(
            h=None if is_inverse else subject.str,
            r=object_property.iri.str,
            t=subject.str if is_inverse else None)]

    def get_individuals_with_object_property(
            self,
            object_property: OWLObjectProperty, objs: List[OWLClass]) \
            -> Generator[OWLNamedIndividual, None, None]:
        is_inverse = isinstance(object_property, OWLObjectInverseOf)

        if is_inverse:
            object_property = object_property.get_inverse()
        return_subjects = list()
        for entity, score in self.predict(
                h=[obj.str for obj in objs] if is_inverse else None,
                r=object_property.str,
                t=None if is_inverse else [obj.str for obj in objs]):
            try:
                return_subjects.append(OWLNamedIndividual(entity))
            except Exception as e:  # pragma: no cover
                # Log the invalid IRI
                print(f"Invalid IRI detected: {entity}, error: {e}")
                continue

        return return_subjects

    def data_property_domains(self, pe: OWLDataProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are the direct or indirect domains of this property with respect to the imports closure of the root ontology.

        Args:
            pe: The property expression whose domains are to be retrieved.
            direct: Specifies if the direct domains should be retrieved (True), or if all domains should be retrieved (False).

        Returns:
            The class expressions that are the domains of the specified property.
        """
        # Get all classes that are domains of this property
        domain_classes = [OWLClass(top_entity) for top_entity, score in self.predict(
            h=pe.str,
            r=self.STR_IRI_DOMAIN,
            t=None
        )]

        if direct:
            # If only direct domains are requested, return them as is
            yield from domain_classes
        else:
            # If all domains are requested, also include all superclasses of each domain
            all_domains = set(domain_classes)
            for cls in domain_classes:
                all_domains.update(self.super_classes(cls))
            yield from all_domains

            # If no domain is found, yield OWLThing as the default domain
            if not all_domains:
                yield OWLThing

    def object_property_domains(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        # Check if the property is inverse
        is_inverse = isinstance(pe, OWLObjectInverseOf)
        if is_inverse:
            # For inverse properties, the domains are the ranges of the original property
            original_property = pe.get_inverse()
            yield from self.object_property_ranges(original_property, direct)
        else:
            # Get all classes that are domains of this property
            domain_classes = [OWLClass(top_entity) for top_entity, score in self.predict(
                h=pe.str,
                r=self.STR_IRI_DOMAIN,
                t=None
            )]

            if direct:
                # If only direct domains are requested, return them as is
                yield from domain_classes
            else:
                # If all domains are requested, also include all superclasses of each domain
                all_domains = set(domain_classes)
                for cls in domain_classes:
                    all_domains.update(self.super_classes(cls))
                yield from all_domains

                # If no domain is found, yield OWLThing as the default domain
                if not all_domains:
                    yield OWLThing

    def object_property_ranges(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        # Check if the property is inverse
        is_inverse = isinstance(pe, OWLObjectInverseOf)
        if is_inverse:
            pe = pe.get_inverse()
            # For inverse properties, the ranges are the domains of the original property
            if direct:
                yield from [OWLClass(top_entity) for top_entity, score in self.predict(
                    h=pe.str,
                    r=self.STR_IRI_DOMAIN,
                    t=None
                )]
            else:
                # Get all domains and their superclasses
                domain_classes = [OWLClass(top_entity) for top_entity, score in self.predict(
                    h=pe.str,
                    r=self.STR_IRI_DOMAIN,
                    t=None
                )]
                all_domains = set(domain_classes)
                for cls in domain_classes:
                    all_domains.update(self.super_classes(cls))
                yield from all_domains

                # If no range is found, yield OWLThing as the default range
                if not all_domains:
                    yield OWLThing
        else:
            # For regular properties, get ranges directly
            range_classes = [OWLClass(top_entity) for top_entity, score in self.predict(
                h=pe.str,
                r=self.STR_IRI_RANGE,
                t=None
            )]

            if direct:
                # If only direct ranges are requested, return them as is
                yield from range_classes
            else:
                # If all ranges are requested, also include all superclasses of each range
                all_ranges = set(range_classes)
                for cls in range_classes:
                    all_ranges.update(self.super_classes(cls))
                yield from all_ranges

                # If no range is found, yield OWLThing as the default range
                if not all_ranges:
                    yield OWLThing

    def equivalent_classes(self, ce: OWLClassExpression) -> Iterable[OWLClassExpression]:
        raise NotImplementedError("Equivalent classes are not implemented for the embedding-based reasoner")

    def disjoint_classes(self, ce: OWLClassExpression) -> Iterable[OWLClassExpression]:
        raise NotImplementedError("Disjoint classes are not implemented for the embedding-based reasoner")

    def different_individuals(self, ind: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        raise NotImplementedError("Different individuals are not implemented for the embedding-based reasoner")

    def same_individuals(self, ind: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        raise NotImplementedError("Same individuals are not implemented for the embedding-based reasoner")

    def equivalent_object_properties(self, op: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        raise NotImplementedError("Equivalent object properties are not implemented for the embedding-based reasoner")

    def equivalent_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        raise NotImplementedError("Equivalent data properties are not implemented for the embedding-based reasoner")

    def data_property_values(self, e: OWLEntity, pe: OWLDataProperty) -> Iterable['OWLLiteral']:
        raise NotImplementedError("Data property values are not implemented for the embedding-based reasoner")

    def disjoint_object_properties(self, op: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        raise NotImplementedError("Disjoint object properties are not implemented for the embedding-based reasoner")

    def disjoint_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        raise NotImplementedError("Disjoint data properties are not implemented for the embedding-based reasoner")

    def sub_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        # Get direct sub properties
        sub_properties = [OWLDataProperty(top_entity) for top_entity, score in self.predict(
            h=None,
            r=self.STR_IRI_SUBPROPERTY,
            t=dp.str
        )]

        if direct:
            # If only direct sub properties are requested, return them as is
            yield from sub_properties
        else:
            # If all sub properties are requested, also include all sub properties of each sub property
            visited = set()
            all_sub_properties = []

            def collect_sub_properties(property_):
                for sub_prop in [OWLDataProperty(top_entity) for top_entity, score in self.predict(
                        h=None,
                        r=self.STR_IRI_SUBPROPERTY,
                        t=property_.str
                )]:
                    if sub_prop not in visited:
                        visited.add(sub_prop)
                        all_sub_properties.append(sub_prop)
                        collect_sub_properties(sub_prop)

            for prop in sub_properties:
                visited.add(prop)
                all_sub_properties.append(prop)
                collect_sub_properties(prop)

            yield from all_sub_properties

    def super_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        # Get direct super properties
        super_properties = [OWLDataProperty(top_entity) for top_entity, score in self.predict(
            h=dp.str,
            r=self.STR_IRI_SUBPROPERTY,
            t=None
        )]

        if direct:
            # If only direct super properties are requested, return them as is
            yield from super_properties
        else:
            # If all super properties are requested, also include all super properties of each super property
            visited = set()
            all_super_properties = []

            def collect_super_properties(property_):
                for super_prop in [OWLDataProperty(top_entity) for top_entity, score in self.predict(
                        h=property_.str,
                        r=self.STR_IRI_SUBPROPERTY,
                        t=None
                )]:
                    if super_prop not in visited:
                        visited.add(super_prop)
                        all_super_properties.append(super_prop)
                        collect_super_properties(super_prop)

            for prop in super_properties:
                visited.add(prop)
                all_super_properties.append(prop)
                collect_super_properties(prop)

            yield from all_super_properties

    def sub_object_properties(self, op: OWLObjectPropertyExpression, direct: bool = False) -> Iterable[
        OWLObjectPropertyExpression]:
        # Check if the property is inverse
        is_inverse = isinstance(op, OWLObjectInverseOf)
        if is_inverse:
            # For inverse properties, the sub properties are the inverse of the super properties of the original property
            original_property = op.get_inverse()
            for super_prop in self.super_object_properties(original_property, direct):
                yield OWLObjectInverseOf(super_prop)
        else:
            # Get direct sub properties
            sub_properties = [OWLObjectProperty(top_entity) for top_entity, score in self.predict(
                h=None,
                r=self.STR_IRI_SUBPROPERTY,
                t=op.str
            )]

            if direct:
                # If only direct sub properties are requested, return them as is
                yield from sub_properties
            else:
                # If all sub properties are requested, also include all sub properties of each sub property
                visited = set()
                all_sub_properties = []

                def collect_sub_properties(property_):
                    for sub_prop in [OWLObjectProperty(top_entity) for top_entity, score in self.predict(
                            h=None,
                            r=self.STR_IRI_SUBPROPERTY,
                            t=property_.str
                    )]:
                        if sub_prop not in visited:
                            visited.add(sub_prop)
                            all_sub_properties.append(sub_prop)
                            collect_sub_properties(sub_prop)

                for prop in sub_properties:
                    visited.add(prop)
                    all_sub_properties.append(prop)
                    collect_sub_properties(prop)

                yield from all_sub_properties

    def super_object_properties(self, op: OWLObjectPropertyExpression, direct: bool = False) -> Iterable[
        OWLObjectPropertyExpression]:
        # Check if the property is inverse
        is_inverse = isinstance(op, OWLObjectInverseOf)
        if is_inverse:
            # For inverse properties, the super properties are the inverse of the sub properties of the original property
            original_property = op.get_inverse()
            for sub_prop in self.sub_object_properties(original_property, direct):
                yield OWLObjectInverseOf(sub_prop)
        else:
            # Get direct super properties
            super_properties = [OWLObjectProperty(top_entity) for top_entity, score in self.predict(
                h=op.str,
                r=self.STR_IRI_SUBPROPERTY,
                t=None
            )]

            if direct:
                # If only direct super properties are requested, return them as is
                yield from super_properties
            else:
                # If all super properties are requested, also include all super properties of each super property
                visited = set()
                all_super_properties = []

                def collect_super_properties(property_):
                    for super_prop in [OWLObjectProperty(top_entity) for top_entity, score in self.predict(
                            h=property_.str,
                            r=self.STR_IRI_SUBPROPERTY,
                            t=None
                    )]:
                        if super_prop not in visited:
                            visited.add(super_prop)
                            all_super_properties.append(super_prop)
                            collect_super_properties(super_prop)

                for prop in super_properties:
                    visited.add(prop)
                    all_super_properties.append(prop)
                    collect_super_properties(prop)

                yield from all_super_properties

    def get_root_ontology(self) -> NeuralOntology:
        return self.ontology