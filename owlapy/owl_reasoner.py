"""OWL Reasoner"""
import operator
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from enum import Enum, auto
from functools import singledispatchmethod, reduce
from itertools import chain, repeat
from types import MappingProxyType, FunctionType
from typing import DefaultDict, Iterable, Dict, Mapping, Set, Type, TypeVar, Optional, FrozenSet, List, cast
import logging

import owlready2

from owlapy.class_expression import OWLClassExpression, OWLObjectSomeValuesFrom, OWLObjectUnionOf, \
    OWLObjectIntersectionOf, OWLObjectComplementOf, OWLObjectAllValuesFrom, OWLObjectOneOf, OWLObjectHasValue, \
    OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality, OWLObjectCardinalityRestriction, \
    OWLDataSomeValuesFrom, OWLDataOneOf, OWLDatatypeRestriction, OWLFacetRestriction, OWLDataHasValue, \
    OWLDataAllValuesFrom
from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLAxiom, OWLSubClassOfAxiom
from owlapy.owl_data_ranges import OWLDataRange, OWLDataComplementOf, OWLDataUnionOf, OWLDataIntersectionOf
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_object import OWLEntity
from owlapy.owl_ontology import OWLOntology, Ontology, _parse_concept_to_owlapy, ToOwlready2
from owlapy.owl_ontology_manager import OntologyManager
from owlapy.owl_property import OWLObjectPropertyExpression, OWLDataProperty, OWLObjectProperty, OWLObjectInverseOf, \
    OWLPropertyExpression, OWLDataPropertyExpression
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
from owlapy.owlapi_adaptor import OWLAPIAdaptor
from owlapy.utils import LRUCache

logger = logging.getLogger(__name__)


class OWLReasoner(metaclass=ABCMeta):
    """An OWLReasoner reasons over a set of axioms (the set of reasoner axioms) that is based on the imports closure of
    a particular ontology - the "root" ontology."""
    __slots__ = ()

    @abstractmethod
    def __init__(self, ontology: OWLOntology):
        pass

    @abstractmethod
    def data_property_domains(self, pe: OWLDataProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are the direct or indirect domains of this property with respect to the
           imports closure of the root ontology.

        Args:
            pe: The property expression whose domains are to be retrieved.
            direct: Specifies if the direct domains should be retrieved (True), or if all domains should be retrieved
                (False).

        Returns:
            :Let N = equivalent_classes(DataSomeValuesFrom(pe rdfs:Literal)). If direct is True: then if N is not
            empty then the return value is N, else the return value is the result of
            super_classes(DataSomeValuesFrom(pe rdfs:Literal), true). If direct is False: then the result of
            super_classes(DataSomeValuesFrom(pe rdfs:Literal), false) together with N if N is non-empty.
            (Note, rdfs:Literal is the top datatype).
        """
        pass

    @abstractmethod
    def object_property_domains(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are the direct or indirect domains of this property with respect to the
           imports closure of the root ontology.

        Args:
            pe: The property expression whose domains are to be retrieved.
            direct: Specifies if the direct domains should be retrieved (True), or if all domains should be retrieved
                (False).

        Returns:
            :Let N = equivalent_classes(ObjectSomeValuesFrom(pe owl:Thing)). If direct is True: then if N is not empty
            then the return value is N, else the return value is the result of
            super_classes(ObjectSomeValuesFrom(pe owl:Thing), true). If direct is False: then the result of
            super_classes(ObjectSomeValuesFrom(pe owl:Thing), false) together with N if N is non-empty.
        """
        pass

    @abstractmethod
    def object_property_ranges(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are the direct or indirect ranges of this property with respect to the
           imports closure of the root ontology.

        Args:
            pe: The property expression whose ranges are to be retrieved.
            direct: Specifies if the direct ranges should be retrieved (True), or if all ranges should be retrieved
                (False).

        Returns:
            :Let N = equivalent_classes(ObjectSomeValuesFrom(ObjectInverseOf(pe) owl:Thing)). If direct is True: then
            if N is not empty then the return value is N, else the return value is the result of
            super_classes(ObjectSomeValuesFrom(ObjectInverseOf(pe) owl:Thing), true). If direct is False: then
            the result of super_classes(ObjectSomeValuesFrom(ObjectInverseOf(pe) owl:Thing), false) together with N
            if N is non-empty.
        """
        pass

    @abstractmethod
    def equivalent_classes(self, ce: OWLClassExpression, only_named: bool = True) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are equivalent to the specified class expression with respect to the set of
        reasoner axioms.

        Args:
            ce: The class expression whose equivalent classes are to be retrieved.
            only_named: Whether to only retrieve named equivalent classes or also complex class expressions.

        Returns:
            All class expressions C where the root ontology imports closure entails EquivalentClasses(ce C). If ce is
            not a class name (i.e. it is an anonymous class expression) and there are no such classes C then there will
            be no result. If ce is unsatisfiable with respect to the set of reasoner axioms then  owl:Nothing, i.e. the
            bottom node, will be returned.
        """
        pass

    @abstractmethod
    def disjoint_classes(self, ce: OWLClassExpression, only_named: bool = True) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are disjoint with specified class expression with respect to the set of
        reasoner axioms.

        Args:
            ce: The class expression whose disjoint classes are to be retrieved.
            only_named: Whether to only retrieve named disjoint classes or also complex class expressions.

        Returns:
            All class expressions D where the set of reasoner axioms entails EquivalentClasses(D ObjectComplementOf(ce))
            or StrictSubClassOf(D ObjectComplementOf(ce)).
        """
        pass

    @abstractmethod
    def different_individuals(self, ind: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        """Gets the individuals that are different from the specified individual with respect to the set of
        reasoner axioms.

        Args:
            ind: The individual whose different individuals are to be retrieved.

        Returns:
            All individuals x where the set of reasoner axioms entails DifferentIndividuals(ind x).
        """
        pass

    @abstractmethod
    def same_individuals(self, ind: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        """Gets the individuals that are the same as the specified individual with respect to the set of
        reasoner axioms.

        Args:
            ind: The individual whose same individuals are to be retrieved.

        Returns:
            All individuals x where the root ontology imports closure entails SameIndividual(ind x).
        """
        pass

    @abstractmethod
    def equivalent_object_properties(self, op: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        """Gets the simplified object properties that are equivalent to the specified object property with respect
        to the set of reasoner axioms.

        Args:
            op: The object property whose equivalent object properties are to be retrieved.

        Returns:
            All simplified object properties e where the root ontology imports closure entails
            EquivalentObjectProperties(op e). If op is unsatisfiable with respect to the set of reasoner axioms
            then owl:bottomDataProperty will be returned.
        """
        pass

    @abstractmethod
    def equivalent_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        """Gets the data properties that are equivalent to the specified data property with respect to the set of
        reasoner axioms.

        Args:
            dp: The data property whose equivalent data properties are to be retrieved.

        Returns:
            All data properties e where the root ontology imports closure entails EquivalentDataProperties(dp e).
            If dp is unsatisfiable with respect to the set of reasoner axioms then owl:bottomDataProperty will
            be returned.
        """
        pass

    @abstractmethod
    def data_property_values(self, e: OWLEntity, pe: OWLDataProperty, direct: bool = True) \
            -> Iterable['OWLLiteral']:
        """Gets the data property values for the specified entity and data property expression.

        Args:
            e: The owl entity (usually an individual) that is the subject of the data property values.
            pe: The data property expression whose values are to be retrieved for the specified entity.
            direct: Specifies if the direct values should be retrieved (True), or if all values should be retrieved
                (False), so that sub properties are taken into account.

        Note: Can be used to get values, for example, of 'label' property of owl entities such as classes and properties
        too (not only individuals).

        Returns:
            A set of OWLLiterals containing literals such that for each literal l in the set, the set of reasoner
            axioms entails DataPropertyAssertion(pe ind l).
        """
        pass

    @abstractmethod
    def object_property_values(self, ind: OWLNamedIndividual, pe: OWLObjectPropertyExpression, direct: bool = True) \
            -> Iterable[OWLNamedIndividual]:
        """Gets the object property values for the specified individual and object property expression.

        Args:
            ind: The individual that is the subject of the object property values.
            pe: The object property expression whose values are to be retrieved for the specified individual.
            direct: Specifies if the direct values should be retrieved (True), or if all values should be retrieved
                (False), so that sub properties are taken into account.

        Returns:
            The named individuals such that for each individual j, the set of reasoner axioms entails
            ObjectPropertyAssertion(pe ind j).
        """
        pass

    @abstractmethod
    def instances(self, ce: OWLClassExpression, direct: bool = False) -> Iterable[OWLNamedIndividual]:
        """Gets the individuals which are instances of the specified class expression.

        Args:
            ce: The class expression whose instances are to be retrieved.
            direct: Specifies if the direct instances should be retrieved (True), or if all instances should be
                retrieved (False).

        Returns:
            If direct is True, each named individual j where the set of reasoner axioms entails
            DirectClassAssertion(ce, j). If direct is False, each named individual j where the set of reasoner axioms
            entails ClassAssertion(ce, j). If ce is unsatisfiable with respect to the set of reasoner axioms then
            nothing returned.
        """
        pass

    @abstractmethod
    def sub_classes(self, ce: OWLClassExpression, direct: bool = False, only_named: bool = True) \
            -> Iterable[OWLClassExpression]:
        """Gets the set of named classes that are the strict (potentially direct) subclasses of the specified class
        expression with respect to the reasoner axioms.

        Args:
            ce: The class expression whose strict (direct) subclasses are to be retrieved.
            direct: Specifies if the direct subclasses should be retrieved (True) or if the all subclasses
                (descendant) classes should be retrieved (False).
            only_named: Whether to only retrieve named sub-classes or also complex class expressions.

        Returns:
            If direct is True, each class C where reasoner axioms entails DirectSubClassOf(C, ce). If direct is False,
            each class C where reasoner axioms entails StrictSubClassOf(C, ce). If ce is equivalent to owl:Nothing then
            nothing will be returned.
        """
        pass

    @abstractmethod
    def disjoint_object_properties(self, op: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        """Gets the simplified object properties that are disjoint with the specified object property with respect
        to the set of reasoner axioms.

        Args:
            op: The object property whose disjoint object properties are to be retrieved.

        Returns:
            All simplified object properties e where the root ontology imports closure entails
            EquivalentObjectProperties(e ObjectPropertyComplementOf(op)) or
            StrictSubObjectPropertyOf(e ObjectPropertyComplementOf(op)).
        """
        pass

    @abstractmethod
    def disjoint_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        """Gets the data properties that are disjoint with the specified data property with respect
        to the set of reasoner axioms.

        Args:
            dp: The data property whose disjoint data properties are to be retrieved.

        Returns:
            All data properties e where the root ontology imports closure entails
            EquivalentDataProperties(e DataPropertyComplementOf(dp)) or
            StrictSubDataPropertyOf(e DataPropertyComplementOf(dp)).
        """
        pass

    @abstractmethod
    def sub_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        """Gets the set of named data properties that are the strict (potentially direct) subproperties of the
        specified data property expression with respect to the imports closure of the root ontology.

        Args:
            dp: The data property whose strict (direct) subproperties are to be retrieved.
            direct: Specifies if the direct subproperties should be retrieved (True) or if the all subproperties
                (descendants) should be retrieved (False).

        Returns:
            If direct is True, each property P where the set of reasoner axioms entails DirectSubDataPropertyOf(P, pe).
            If direct is False, each property P where the set of reasoner axioms entails
            StrictSubDataPropertyOf(P, pe). If pe is equivalent to owl:bottomDataProperty then nothing will be
            returned.
        """
        pass

    @abstractmethod
    def super_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        """Gets the stream of data properties that are the strict (potentially direct) super properties of the
         specified data property with respect to the imports closure of the root ontology.

         Args:
             dp (OWLDataProperty): The data property whose super properties are to be retrieved.
             direct (bool): Specifies if the direct super properties should be retrieved (True) or if the all
                            super properties (ancestors) should be retrieved (False).

         Returns:
             Iterable of super properties.
         """
        pass

    @abstractmethod
    def sub_object_properties(self, op: OWLObjectPropertyExpression, direct: bool = False) \
            -> Iterable[OWLObjectPropertyExpression]:
        """Gets the stream of simplified object property expressions that are the strict (potentially direct)
        subproperties of the specified object property expression with respect to the imports closure of the root
        ontology.

        Args:
            op: The object property expression whose strict (direct) subproperties are to be retrieved.
            direct: Specifies if the direct subproperties should be retrieved (True) or if the all subproperties
                (descendants) should be retrieved (False).

        Returns:
            If direct is True, simplified object property expressions, such that for each simplified object property
            expression, P, the set of reasoner axioms entails DirectSubObjectPropertyOf(P, pe).
            If direct is False, simplified object property expressions, such that for each simplified object property
            expression, P, the set of reasoner axioms entails StrictSubObjectPropertyOf(P, pe).
            If pe is equivalent to owl:bottomObjectProperty then nothing will be returned.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def types(self, ind: OWLNamedIndividual, direct: bool = False) -> Iterable[OWLClass]:
        """Gets the named classes which are (potentially direct) types of the specified named individual.

        Args:
            ind: The individual whose types are to be retrieved.
            direct: Specifies if the direct types should be retrieved (True), or if all types should be retrieved
                (False).

        Returns:
            If direct is True, each named class C where the set of reasoner axioms entails
            DirectClassAssertion(C, ind). If direct is False, each named class C where the set of reasoner axioms
            entails ClassAssertion(C, ind).
        """
        pass

    @abstractmethod
    def get_root_ontology(self) -> OWLOntology:
        """Gets the "root" ontology that is loaded into this reasoner. The reasoner takes into account the axioms in
        this ontology and its import's closure."""
        pass

    @abstractmethod
    def super_classes(self, ce: OWLClassExpression, direct: bool = False, only_named: bool = True) \
            -> Iterable[OWLClassExpression]:
        """Gets the stream of named classes that are the strict (potentially direct) super classes of the specified
        class expression with respect to the imports closure of the root ontology.

        Args:
            ce: The class expression whose strict (direct) super classes are to be retrieved.
            direct: Specifies if the direct super classes should be retrieved (True) or if the all super classes
                (ancestors) classes should be retrieved (False).
            only_named: Whether to only retrieve named super classes or also complex class expressions.

        Returns:
            If direct is True, each class C where the set of reasoner axioms entails DirectSubClassOf(ce, C).
            If direct is False, each class C where  set of reasoner axioms entails StrictSubClassOf(ce, C).
            If ce is equivalent to owl:Thing then nothing will be returned.
        """
        pass


# Deprecated
# class BaseReasoner(Enum):
#     """Enumeration class for base reasoner when calling sync_reasoner.
#
#     Attributes:
#         PELLET: Pellet base reasoner.
#         HERMIT: HermiT base reasoner.
#     """
#     PELLET = auto()
#     HERMIT = auto()


class OWLReasonerEx(OWLReasoner, metaclass=ABCMeta):
    """Extra convenience methods for OWL Reasoners"""

    # default
    def data_property_ranges(self, pe: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataRange]:
        """Gets the data ranges that are the direct or indirect ranges of this property with respect to the imports
        closure of the root ontology.

        Args:
            pe: The property expression whose ranges are to be retrieved.
            direct: Specifies if the direct ranges should be retrieved (True), or if all ranges should be retrieved
                (False).

        Returns:
        """
        for ax in self.get_root_ontology().data_property_range_axioms(pe):
            yield ax.get_range()
            if not direct:
                logger.warning("indirect not implemented")
                # TODO:

    # default
    def all_data_property_values(self, pe: OWLDataProperty, direct: bool = True) -> Iterable[OWLLiteral]:
        """Gets all values for the given data property expression that appear in the knowledge base.

        Args:
            pe: The data property expression whose values are to be retrieved
            direct: Specifies if only the direct values of the data property pe should be retrieved (True), or if
                    the values of sub properties of pe should be taken into account (False).

        Returns:
            A set of OWLLiterals containing literals such that for each literal l in the set, the set of reasoner
            axioms entails DataPropertyAssertion(pe ind l) for any ind.
        """
        onto = self.get_root_ontology()
        for ind in onto.individuals_in_signature():
            for lit in self.data_property_values(ind, pe, direct):
                yield lit

    # default
    def ind_data_properties(self, ind: OWLNamedIndividual, direct: bool = True) -> Iterable[OWLDataProperty]:
        """Gets all data properties for the given individual that appear in the knowledge base.

        Args:
            ind: The named individual whose data properties are to be retrieved
            direct: Specifies if the direct data properties should be retrieved (True), or if all
                data properties should be retrieved (False), so that sub properties are taken into account.

        Returns:
            All data properties pe where the set of reasoner axioms entails DataPropertyAssertion(pe ind l)
            for atleast one l.
        """
        onto = self.get_root_ontology()
        for dp in onto.data_properties_in_signature():
            try:
                next(iter(self.data_property_values(ind, dp, direct)))
                yield dp
            except StopIteration:
                pass

    # default
    def ind_object_properties(self, ind: OWLNamedIndividual, direct: bool = True) -> Iterable[OWLObjectProperty]:
        """Gets all object properties for the given individual that appear in the knowledge base.

        Args:
            ind: The named individual whose object properties are to be retrieved
            direct: Specifies if the direct object properties should be retrieved (True), or if all
                object properties should be retrieved (False), so that sub properties are taken into account.

        Returns:
            All data properties pe where the set of reasoner axioms entails ObjectPropertyAssertion(pe ind ind2)
            for atleast one ind2.
        """
        onto = self.get_root_ontology()
        for op in onto.object_properties_in_signature():
            try:
                next(iter(self.object_property_values(ind, op, direct)))
                yield op
            except StopIteration:
                pass


class OntologyReasoner(OWLReasonerEx):
    __slots__ = '_ontology', '_world'

    _ontology: Ontology
    _world: owlready2.World

    def __init__(self, ontology: Ontology):
        """
        Base reasoner in Ontolearn, used to reason in the given ontology.

        Args:
            ontology: The ontology that should be used by the reasoner.
        """
        super().__init__(ontology)
        assert isinstance(ontology, Ontology)
        self._isolated = False
        self._ontology = ontology
        self._world = ontology._world

    def data_property_domains(self, pe: OWLDataProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        domains = {d.get_domain() for d in self.get_root_ontology().data_property_domain_axioms(pe)}
        super_domains = set(chain.from_iterable([self.super_classes(d) for d in domains]))
        yield from domains - super_domains
        if not direct:
            yield from super_domains

    def object_property_domains(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        domains = {d.get_domain() for d in self.get_root_ontology().object_property_domain_axioms(pe)}
        super_domains = set(chain.from_iterable([self.super_classes(d) for d in domains]))
        yield from domains - super_domains
        if not direct:
            yield from super_domains

    def object_property_ranges(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        ranges = {r.get_range() for r in self.get_root_ontology().object_property_range_axioms(pe)}
        super_ranges = set(chain.from_iterable([self.super_classes(d) for d in ranges]))
        yield from ranges - super_ranges
        if not direct:
            yield from super_ranges

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

    def instances(self, ce: OWLClassExpression, direct: bool = False) -> Iterable[OWLNamedIndividual]:
        if direct:
            if isinstance(ce, OWLClass):
                c_x: owlready2.ThingClass = self._world[ce.str]
                for i in self._ontology._onto.get_instances_of(c_x):
                    if isinstance(i, owlready2.Thing):
                        yield OWLNamedIndividual(IRI.create(i.iri))
            else:
                raise NotImplementedError("instances for complex class expressions not implemented", ce)
        else:
            if ce.is_owl_thing():
                yield from self._ontology.individuals_in_signature()
            elif isinstance(ce, OWLClass):
                c_x: owlready2.ThingClass = self._world[ce.str]
                for i in c_x.instances(world=self._world):
                    if isinstance(i, owlready2.Thing):
                        yield OWLNamedIndividual(IRI.create(i.iri))
            # elif isinstance(ce, OWLObjectSomeValuesFrom) and ce.get_filler().is_owl_thing()\
            #         and isinstance(ce.get_property(), OWLProperty):
            #     seen_set = set()
            #     p_x: owlready2.ObjectProperty = self._world[ce.get_property().get_named_property().str]
            #     for i, _ in p_x.get_relations():
            #         if isinstance(i, owlready2.Thing) and i not in seen_set:
            #             seen_set.add(i)
            #             yield OWLNamedIndividual(IRI.create(i.iri))
            else:
                raise NotImplementedError("instances for complex class expressions not implemented", ce)

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

    # Deprecated
    # def _sync_reasoner(self, other_reasoner: BaseReasoner = None,
    #                    infer_property_values: bool = True,
    #                    infer_data_property_values: bool = True, debug: bool = False) -> None:
    #     """Call Owlready2's sync_reasoner method, which spawns a Java process on a temp file to infer more.
    #
    #     Args:
    #         other_reasoner: Set to BaseReasoner.PELLET (default) or BaseReasoner.HERMIT.
    #         infer_property_values: Whether to infer property values.
    #         infer_data_property_values: Whether to infer data property values (only for PELLET).
    #     """
    #     assert other_reasoner is None or isinstance(other_reasoner, BaseReasoner)
    #     with self.get_root_ontology()._onto:
    #         if other_reasoner == BaseReasoner.HERMIT:
    #             owlready2.sync_reasoner_hermit(self._world, infer_property_values=infer_property_values, debug=debug)
    #         else:
    #             owlready2.sync_reasoner_pellet(self._world,
    #                                            infer_property_values=infer_property_values,
    #                                            infer_data_property_values=infer_data_property_values,
    #                                            debug=debug)

    def get_root_ontology(self) -> OWLOntology:
        return self._ontology


_P = TypeVar('_P', bound=OWLPropertyExpression)


class FastInstanceCheckerReasoner(OWLReasonerEx):
    """Tries to check instances fast (but maybe incomplete)."""
    __slots__ = '_ontology', '_base_reasoner', \
                '_ind_set', '_cls_to_ind', \
                '_has_prop', \
                '_objectsomevalues_cache', '_datasomevalues_cache', '_objectcardinality_cache', \
                '_property_cache', \
                '_obj_prop', '_obj_prop_inv', '_data_prop', \
                '_negation_default', \
                '__warned'

    _ontology: OWLOntology
    _base_reasoner: OWLReasoner
    _cls_to_ind: Dict[OWLClass, FrozenSet[OWLNamedIndividual]]  # Class => individuals
    _has_prop: Mapping[Type[_P], LRUCache[_P, FrozenSet[OWLNamedIndividual]]]  # Type => Property => individuals
    _ind_set: FrozenSet[OWLNamedIndividual]
    # ObjectSomeValuesFrom => individuals
    _objectsomevalues_cache: LRUCache[OWLClassExpression, FrozenSet[OWLNamedIndividual]]
    # DataSomeValuesFrom => individuals
    _datasomevalues_cache: LRUCache[OWLClassExpression, FrozenSet[OWLNamedIndividual]]
    # ObjectCardinalityRestriction => individuals
    _objectcardinality_cache: LRUCache[OWLClassExpression, FrozenSet[OWLNamedIndividual]]
    # ObjectProperty => { individual => individuals }
    _obj_prop: Dict[OWLObjectProperty, Mapping[OWLNamedIndividual, Set[OWLNamedIndividual]]]
    # ObjectProperty => { individual => individuals }
    _obj_prop_inv: Dict[OWLObjectProperty, Mapping[OWLNamedIndividual, Set[OWLNamedIndividual]]]
    # DataProperty => { individual => literals }
    _data_prop: Dict[OWLDataProperty, Mapping[OWLNamedIndividual, Set[OWLLiteral]]]
    _property_cache: bool
    _negation_default: bool
    _sub_properties: bool

    def __init__(self, ontology: OWLOntology, base_reasoner: OWLReasoner, *,
                 property_cache: bool = True, negation_default: bool = True, sub_properties: bool = False):
        """Fast instance checker.

        Args:
            ontology: Ontology to use.
            base_reasoner: Reasoner to get instances/types from.
            property_cache: Whether to cache property values.
            negation_default: Whether to assume a missing fact means it is false ("closed world view").
            sub_properties: Whether to take sub properties into account for the
                :func:`OWLReasoner_FastInstanceChecker.instances` retrieval.
            """
        super().__init__(ontology)
        self._ontology = ontology
        self._base_reasoner = base_reasoner
        self._property_cache = property_cache
        self._negation_default = negation_default
        self._sub_properties = sub_properties
        self.__warned = 0
        self._init()

    def _init(self, cache_size=128):
        self._cls_to_ind = dict()
        individuals = self._ontology.individuals_in_signature()
        self._ind_set = frozenset(individuals)
        self._objectsomevalues_cache = LRUCache(maxsize=cache_size)
        self._datasomevalues_cache = LRUCache(maxsize=cache_size)
        self._objectcardinality_cache = LRUCache(maxsize=cache_size)
        if self._property_cache:
            self._obj_prop = dict()
            self._obj_prop_inv = dict()
            self._data_prop = dict()
        else:
            self._has_prop = MappingProxyType({
                OWLDataProperty: LRUCache(maxsize=cache_size),
                OWLObjectProperty: LRUCache(maxsize=cache_size),
                OWLObjectInverseOf: LRUCache(maxsize=cache_size),
            })

    def reset(self):
        """The reset method shall reset any cached state."""
        self._init()

    def data_property_domains(self, pe: OWLDataProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        yield from self._base_reasoner.data_property_domains(pe, direct=direct)

    def data_property_ranges(self, pe: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataRange]:
        yield from self._base_reasoner.data_property_ranges(pe, direct=direct)

    def object_property_domains(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        yield from self._base_reasoner.object_property_domains(pe, direct=direct)

    def object_property_ranges(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        yield from self._base_reasoner.object_property_ranges(pe, direct=direct)

    def equivalent_classes(self, ce: OWLClassExpression, only_named: bool = True) -> Iterable[OWLClassExpression]:
        yield from self._base_reasoner.equivalent_classes(ce, only_named=only_named)

    def disjoint_classes(self, ce: OWLClassExpression, only_named: bool = True) -> Iterable[OWLClassExpression]:
        yield from self._base_reasoner.disjoint_classes(ce, only_named=only_named)

    def different_individuals(self, ce: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        yield from self._base_reasoner.different_individuals(ce)

    def same_individuals(self, ce: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        yield from self._base_reasoner.same_individuals(ce)

    def data_property_values(self, e: OWLEntity, pe: OWLDataProperty, direct: bool = True) \
            -> Iterable[OWLLiteral]:
        yield from self._base_reasoner.data_property_values(e, pe, direct)

    def all_data_property_values(self, pe: OWLDataProperty, direct: bool = True) -> Iterable[OWLLiteral]:
        yield from self._base_reasoner.all_data_property_values(pe, direct)

    def object_property_values(self, ind: OWLNamedIndividual, pe: OWLObjectPropertyExpression, direct: bool = True) \
            -> Iterable[OWLNamedIndividual]:
        yield from self._base_reasoner.object_property_values(ind, pe, direct)

    def instances(self, ce: OWLClassExpression, direct: bool = False) -> Iterable[OWLNamedIndividual]:
        if direct:
            if not self.__warned & 2:
                logger.warning("direct not implemented")
                self.__warned |= 2
        temp = self._find_instances(ce)
        yield from temp

    def sub_classes(self, ce: OWLClassExpression, direct: bool = False, only_named: bool = True) \
            -> Iterable[OWLClassExpression]:
        yield from self._base_reasoner.sub_classes(ce, direct=direct, only_named=only_named)

    def super_classes(self, ce: OWLClassExpression, direct: bool = False, only_named: bool = True) \
            -> Iterable[OWLClassExpression]:
        yield from self._base_reasoner.super_classes(ce, direct=direct, only_named=only_named)

    def types(self, ind: OWLNamedIndividual, direct: bool = False) -> Iterable[OWLClass]:
        yield from self._base_reasoner.types(ind, direct=direct)

    def equivalent_object_properties(self, dp: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        yield from self._base_reasoner.equivalent_object_properties(dp)

    def equivalent_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        yield from self._base_reasoner.equivalent_data_properties(dp)

    def disjoint_object_properties(self, dp: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        yield from self._base_reasoner.disjoint_object_properties(dp)

    def disjoint_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        yield from self._base_reasoner.disjoint_data_properties(dp)

    def sub_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        yield from self._base_reasoner.sub_data_properties(dp=dp, direct=direct)

    def super_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        yield from self._base_reasoner.super_data_properties(dp=dp, direct=direct)

    def super_object_properties(self, op: OWLObjectProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        yield from self._base_reasoner.super_object_properties(op=op, direct=direct)

    def sub_object_properties(self, op: OWLObjectPropertyExpression, direct: bool = False) \
            -> Iterable[OWLObjectPropertyExpression]:
        yield from self._base_reasoner.sub_object_properties(op=op, direct=direct)

    def get_root_ontology(self) -> OWLOntology:
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
            for s in self._ind_set:
                individuals = set(self._base_reasoner.object_property_values(s, pe, not self._sub_properties))
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
                    func = self._base_reasoner.data_property_values
                else:
                    func = self._base_reasoner.object_property_values

                for s in self._ind_set:
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
                for o in self._base_reasoner.object_property_values(s, pe, not self._sub_properties):
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
        from owlapy.owl_ontology  import Ontology
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
                values = set(self._base_reasoner.data_property_values(s, pe))
                if len(values) > 0:
                    opc[s] = values

        self._data_prop[pe] = MappingProxyType(opc)

    # single dispatch is still not implemented in mypy, see https://github.com/python/mypy/issues/2904
    @singledispatchmethod
    def _find_instances(self, ce: OWLClassExpression) -> FrozenSet[OWLNamedIndividual]:
        raise NotImplementedError(ce)

    @_find_instances.register
    def _(self, c: OWLClass) -> FrozenSet[OWLNamedIndividual]:
        self._lazy_cache_class(c)
        return self._cls_to_ind[c]

    @_find_instances.register
    def _(self, ce: OWLObjectUnionOf) -> FrozenSet[OWLNamedIndividual]:
        return reduce(operator.or_, map(self._find_instances, ce.operands()))

    @_find_instances.register
    def _(self, ce: OWLObjectIntersectionOf) -> FrozenSet[OWLNamedIndividual]:
        return reduce(operator.and_, map(self._find_instances, ce.operands()))

    @_find_instances.register
    def _(self, ce: OWLObjectSomeValuesFrom) -> FrozenSet[OWLNamedIndividual]:
        if ce in self._objectsomevalues_cache:
            return self._objectsomevalues_cache[ce]

        p = ce.get_property()
        assert isinstance(p, OWLObjectPropertyExpression)
        if not self._property_cache and ce.get_filler().is_owl_thing():
            return self._some_values_subject_index(p)

        filler_ind = self._find_instances(ce.get_filler())

        ind = self._find_some_values(p, filler_ind)

        self._objectsomevalues_cache[ce] = ind
        return ind

    @_find_instances.register
    def _(self, ce: OWLObjectComplementOf) -> FrozenSet[OWLNamedIndividual]:
        if self._negation_default:
            all_ = self._ind_set
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
        all_ = self._ind_set
        min_ind = self._find_instances(OWLObjectMinCardinality(cardinality=ce.get_cardinality() + 1,
                                                               property=ce.get_property(),
                                                               filler=ce.get_filler()))
        return all_ ^ min_ind

    @_find_instances.register
    def _(self, ce: OWLObjectExactCardinality) -> FrozenSet[OWLNamedIndividual]:
        return self._get_instances_object_card_restriction(ce)

    def _get_instances_object_card_restriction(self, ce: OWLObjectCardinalityRestriction):
        if ce in self._objectcardinality_cache:
            return self._objectcardinality_cache[ce]

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

        self._objectcardinality_cache[ce] = ind
        return ind

    @_find_instances.register
    def _(self, ce: OWLDataSomeValuesFrom) -> FrozenSet[OWLNamedIndividual]:
        if ce in self._datasomevalues_cache:
            return self._datasomevalues_cache[ce]

        pe = ce.get_property()
        filler = ce.get_filler()
        assert isinstance(pe, OWLDataProperty)
        #

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
                    for lit in self._base_reasoner.data_property_values(s, pe):
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
                    for lit in self._base_reasoner.data_property_values(s, pe):
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
                    for lit in self._base_reasoner.data_property_values(s, pe):
                        if include(lit):
                            ind |= {s}
                            break
        else:
            raise ValueError

        r = frozenset(ind)
        self._datasomevalues_cache[ce] = r
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
        temp = self._base_reasoner.instances(c)
        self._cls_to_ind[c] = frozenset(temp)

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


class SyncReasoner(OWLReasonerEx):

    def __init__(self, ontology_path: str, reasoner="HermiT"):
        """
        OWL reasoner that syncs to other reasoners like HermiT,Pellet,etc.

        Args:
            ontology_path: Path of ontology that should be used by the reasoner.
            reasoner: Choose from (case-sensitive): ["HermiT", "Pellet", "JFact", "Openllet"]. Default: "HermiT".
        """
        self.manager = OntologyManager()
        self.ontology = self.manager.load_ontology(IRI.create("file://" + ontology_path))
        super().__init__(self.ontology)
        self.adaptor = OWLAPIAdaptor(ontology_path, reasoner)

    def instances(self, ce: OWLClassExpression, direct: bool = False) -> Iterable[OWLNamedIndividual]:
        yield from self.adaptor.instances(ce, direct)

    def data_property_domains(self, pe: OWLDataProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        yield from self.adaptor.data_property_domains(pe, direct)

    def object_property_domains(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        yield from self.adaptor.object_property_domains(pe, direct)

    def object_property_ranges(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        yield from self.adaptor.object_property_ranges(pe, direct)

    def equivalent_classes(self, ce: OWLClassExpression, only_named: bool = True) -> Iterable[OWLClassExpression]:
        yield from self.adaptor.equivalent_classes(ce)

    def disjoint_classes(self, ce: OWLClassExpression, only_named: bool = True) -> Iterable[OWLClassExpression]:
        yield from self.adaptor.disjoint_classes(ce)

    def different_individuals(self, ind: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        yield from self.adaptor.different_individuals(ind)

    def same_individuals(self, ind: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        yield from self.adaptor.same_individuals(ind)

    def data_property_values(self, e: OWLEntity, pe: OWLDataProperty, direct: bool = True) -> Iterable[OWLLiteral]:
        yield from self.adaptor.data_property_values(e, pe)

    def object_property_values(self, ind: OWLNamedIndividual, pe: OWLObjectPropertyExpression, direct: bool = False) -> \
            Iterable[OWLNamedIndividual]:
        yield from self.adaptor.object_property_values(ind, pe)

    def sub_classes(self, ce: OWLClassExpression, direct: bool = False, only_named: bool = True) -> Iterable[
        OWLClassExpression]:
        yield from self.adaptor.sub_classes(ce, direct)

    def super_classes(self, ce: OWLClassExpression, direct: bool = False, only_named: bool = True) -> Iterable[
        OWLClassExpression]:
        yield from self.adaptor.super_classes(ce, direct)

    def equivalent_object_properties(self, op: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        yield from self.adaptor.equivalent_object_properties(op)

    def equivalent_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        yield from self.adaptor.equivalent_data_properties(dp)

    def disjoint_object_properties(self, op: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        yield from self.adaptor.disjoint_object_properties(op)

    def disjoint_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        yield from self.adaptor.disjoint_data_properties(dp)

    def super_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        yield from self.adaptor.super_data_properties(dp, direct)

    def sub_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        yield from self.adaptor.sub_data_properties(dp, direct)

    def super_object_properties(self, op: OWLObjectPropertyExpression, direct: bool = False) -> Iterable[
        OWLObjectPropertyExpression]:
        yield from self.adaptor.super_object_properties(op, direct)

    def sub_object_properties(self, op: OWLObjectPropertyExpression, direct: bool = False) -> Iterable[
        OWLObjectPropertyExpression]:
        yield from self.adaptor.sub_object_properties(op, direct)

    def types(self, ind: OWLNamedIndividual, direct: bool = False) -> Iterable[OWLClass]:
        yield from self.adaptor.types(ind, direct)

    def get_root_ontology(self) -> OWLOntology:
        return self.ontology