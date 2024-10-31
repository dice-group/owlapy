"""OWL Reasoner"""
from abc import ABCMeta, abstractmethod
from inspect import signature
from typing import Iterable
import logging

from owlapy.class_expression import OWLClassExpression
from owlapy.class_expression import OWLClass
from owlapy.owl_data_ranges import OWLDataRange
from owlapy.owl_object import OWLEntity
from owlapy.abstracts.abstract_owl_ontology import AbstractOWLOntology
from owlapy.owl_property import OWLObjectPropertyExpression, OWLDataProperty, OWLObjectProperty
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral

logger = logging.getLogger(__name__)


class AbstractOWLReasoner(metaclass=ABCMeta):
    """An OWLReasoner reasons over a set of axioms (the set of reasoner axioms) that is based on the imports closure of
    a particular ontology - the "root" ontology."""
    __slots__ = ()

    @abstractmethod
    def __init__(self, ontology: AbstractOWLOntology):
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
    def equivalent_classes(self, ce: OWLClassExpression) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are equivalent to the specified class expression with respect to the set of
        reasoner axioms.

        Args:
            ce: The class expression whose equivalent classes are to be retrieved.

        Returns:
            All class expressions C where the root ontology imports closure entails EquivalentClasses(ce C). If ce is
            not a class name (i.e. it is an anonymous class expression) and there are no such classes C then there will
            be no result. If ce is unsatisfiable with respect to the set of reasoner axioms then  owl:Nothing, i.e. the
            bottom node, will be returned.
        """
        pass

    @abstractmethod
    def disjoint_classes(self, ce: OWLClassExpression) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are disjoint with specified class expression with respect to the set of
        reasoner axioms.

        Args:
            ce: The class expression whose disjoint classes are to be retrieved.

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
    def data_property_values(self, e: OWLEntity, pe: OWLDataProperty) \
            -> Iterable['OWLLiteral']:
        """Gets the data property values for the specified entity and data property expression.

        Args:
            e: The owl entity (usually an individual) that is the subject of the data property values.
            pe: The data property expression whose values are to be retrieved for the specified entity.

        Note: Can be used to get values, for example, of 'label' property of owl entities such as classes and properties
        too (not only individuals).

        Returns:
            A set of OWLLiterals containing literals such that for each literal l in the set, the set of reasoner
            axioms entails DataPropertyAssertion(pe ind l).
        """
        pass

    @abstractmethod
    def object_property_values(self, ind: OWLNamedIndividual, pe: OWLObjectPropertyExpression) \
            -> Iterable[OWLNamedIndividual]:
        """Gets the object property values for the specified individual and object property expression.

        Args:
            ind: The individual that is the subject of the object property values.
            pe: The object property expression whose values are to be retrieved for the specified individual.

        Returns:
            The named individuals such that for each individual j, the set of reasoner axioms entails
            ObjectPropertyAssertion(pe ind j).
        """
        pass

    @abstractmethod
    def instances(self, ce: OWLClassExpression, direct: bool = False, timeout: int = 1000) -> Iterable[OWLNamedIndividual]:
        """Gets the individuals which are instances of the specified class expression.

        Args:
            ce: The class expression whose instances are to be retrieved.
            direct: Specifies if the direct instances should be retrieved (True), or if all instances should be
                retrieved (False).
            timeout: Time limit in seconds until results must be returned, else empty set is returned.

        Returns:
            If direct is True, each named individual j where the set of reasoner axioms entails
            DirectClassAssertion(ce, j). If direct is False, each named individual j where the set of reasoner axioms
            entails ClassAssertion(ce, j). If ce is unsatisfiable with respect to the set of reasoner axioms then
            nothing returned.
        """
        pass

    @abstractmethod
    def sub_classes(self, ce: OWLClassExpression, direct: bool = False) \
            -> Iterable[OWLClassExpression]:
        """Gets the set of named classes that are the strict (potentially direct) subclasses of the specified class
        expression with respect to the reasoner axioms.

        Args:
            ce: The class expression whose strict (direct) subclasses are to be retrieved.
            direct: Specifies if the direct subclasses should be retrieved (True) or if the all subclasses
                (descendant) classes should be retrieved (False).

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
    def get_root_ontology(self) -> AbstractOWLOntology:
        """Gets the "root" ontology that is loaded into this reasoner. The reasoner takes into account the axioms in
        this ontology and its import's closure."""
        pass

    @abstractmethod
    def super_classes(self, ce: OWLClassExpression, direct: bool = False) \
            -> Iterable[OWLClassExpression]:
        """Gets the stream of named classes that are the strict (potentially direct) super classes of the specified
        class expression with respect to the imports closure of the root ontology.

        Args:
            ce: The class expression whose strict (direct) super classes are to be retrieved.
            direct: Specifies if the direct super classes should be retrieved (True) or if the all super classes
                (ancestors) classes should be retrieved (False).

        Returns:
            If direct is True, each class C where the set of reasoner axioms entails DirectSubClassOf(ce, C).
            If direct is False, each class C where  set of reasoner axioms entails StrictSubClassOf(ce, C).
            If ce is equivalent to owl:Thing then nothing will be returned.
        """
        pass

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
        has_direct = "direct" in str(signature(self.data_property_values))
        for ind in onto.individuals_in_signature():
            if has_direct:
                dpv = self.data_property_values(ind, pe, direct)
            else:
                dpv = self.data_property_values(ind, pe)
            for lit in dpv:
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
        has_direct = "direct" in str(signature(self.data_property_values))
        for dp in onto.data_properties_in_signature():
            try:
                if has_direct:
                    next(iter(self.data_property_values(ind, dp, direct)))
                else:
                    next(iter(self.data_property_values(ind, dp)))
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
        has_direct = "direct" in str(signature(self.object_property_values))
        for op in onto.object_properties_in_signature():
            try:
                if has_direct:
                    next(iter(self.object_property_values(ind, op, direct)))
                else:
                    next(iter(self.object_property_values(ind, op)))
                yield op
            except StopIteration:
                pass
