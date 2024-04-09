from abc import ABCMeta, abstractmethod
from typing import Generic, Iterable, Sequence, Set, TypeVar, Union, Final, Optional, Protocol, ClassVar, List
from datetime import datetime, date
from pandas import Timedelta
from owlapy.vocab import OWLRDFVocabulary, XSDVocabulary, OWLFacet
from owlapy._utils import MOVE
from owlapy.owlobject import OWLObject, OWLEntity
from owlapy.owl_annotation import OWLAnnotationObject, OWLAnnotationSubject, OWLAnnotationValue
from owlapy.iri import IRI
from owlapy.has import HasIndex
from owlapy.meta_classes import HasIRI, HasOperands, HasFiller, HasCardinality
from owlapy.class_expression import OWLClassExpression, OWLNaryBooleanClassExpression, OWLObjectIntersectionOf, \
    OWLObjectUnionOf, OWLObjectComplementOf
from owlapy.class_expression import OWLThing, OWLNothing, OWLClass

from owlapy.owl_class_expression import OWLPropertyRange, OWLDataRange

from owlapy.owl_property import OWLObjectPropertyExpression, OWLProperty, OWLPropertyExpression, \
    OWLDataPropertyExpression, OWLDataProperty, OWLObjectProperty
from owlapy.owl_restriction import (OWLRestriction, OWLObjectAllValuesFrom, OWLObjectSomeValuesFrom,
                                    OWLQuantifiedRestriction, OWLQuantifiedObjectRestriction,
                                    OWLObjectRestriction, OWLHasValueRestriction, OWLDataRestriction,
                                    OWLCardinalityRestriction, OWLObjectMinCardinality, OWLObjectCardinalityRestriction,
                                    OWLDataAllValuesFrom,
                                    OWLObjectHasSelf, OWLObjectMaxCardinality, OWLObjectExactCardinality,
                                    OWLDataExactCardinality, OWLDataMinCardinality,
                                    OWLDataMaxCardinality, OWLDataSomeValuesFrom, OWLDataHasValue, OWLDataOneOf,
                                    OWLQuantifiedDataRestriction, OWLDataCardinalityRestriction)

from owlapy.owl_individual import OWLNamedIndividual, OWLIndividual
from owlapy.owl_axiom import (OWLEquivalentClassesAxiom, OWLClassAxiom,
                              OWLDataPropertyDomainAxiom, OWLAxiom, OWLDataPropertyRangeAxiom,
                              OWLObjectPropertyDomainAxiom, OWLObjectPropertyRangeAxiom)
from owlapy.types import OWLDatatype
from owlapy.owl_literal import OWLLiteral

MOVE(OWLObject, OWLAnnotationObject, OWLAnnotationSubject, OWLAnnotationValue, HasIRI, IRI)

_T = TypeVar('_T')  #:
_C = TypeVar('_C', bound='OWLObject')  #:
_P = TypeVar('_P', bound='OWLPropertyExpression')  #:
_R = TypeVar('_R', bound='OWLPropertyRange')  #:
Literals = Union['OWLLiteral', int, float, bool, Timedelta, datetime, date, str]  #:
_M = TypeVar('_M', bound='OWLOntologyManager')  #:


class OWLOntologyID:
    """An object that identifies an ontology. Since OWL 2, ontologies do not have to have an ontology IRI, or if they
    have an ontology IRI then they can optionally also have a version IRI. Instances of this OWLOntologyID class bundle
    identifying information of an ontology together. If an ontology doesn't have an ontology IRI then we say that it is
    "anonymous".
    """
    __slots__ = '_ontology_iri', '_version_iri'

    _ontology_iri: Optional[IRI]
    _version_iri: Optional[IRI]

    def __init__(self, ontology_iri: Optional[IRI] = None, version_iri: Optional[IRI] = None):
        """Constructs an ontology identifier specifying the ontology IRI and version IRI.

        Args:
            ontology_iri: The ontology IRI (optional).
            version_iri: The version IRI (must be None if no ontology_iri is provided).
        """
        self._ontology_iri = ontology_iri
        self._version_iri = version_iri

    def get_ontology_iri(self) -> Optional[IRI]:
        """Gets the ontology IRI.

        Returns:
            Ontology IRI. If the ontology is anonymous, it will return None.
        """
        return self._ontology_iri

    def get_version_iri(self) -> Optional[IRI]:
        """Gets the version IRI.

        Returns:
            Version IRI or None.
        """
        return self._version_iri

    def get_default_document_iri(self) -> Optional[IRI]:
        """Gets the IRI which is used as a default for the document that contain a representation of an ontology with
        this ID. This will be the version IRI if there is an ontology IRI and version IRI, else it will be the ontology
        IRI if there is an ontology IRI but no version IRI, else it will be None if there is no ontology IRI. See
        Ontology Documents in the OWL 2 Structural Specification.

        Returns:
            the IRI that can be used as a default for an ontology document, or None.
        """
        if self._ontology_iri is not None:
            if self._version_iri is not None:
                return self._version_iri
        return self._ontology_iri

    def is_anonymous(self) -> bool:
        return self._ontology_iri is None

    def __repr__(self):
        return f"OWLOntologyID({repr(self._ontology_iri)}, {repr(self._version_iri)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._ontology_iri == other._ontology_iri and self._version_iri == other._version_iri
        return NotImplemented


class OWLImportsDeclaration(HasIRI):
    """Represents an import statement in an ontology."""
    __slots__ = '_iri'

    def __init__(self, import_iri: IRI):
        """
        Args:
            import_import_iri: Imported ontology.

        Returns:
            An imports declaration.
        """
        self._iri = import_iri

    def get_iri(self) -> IRI:
        """Gets the import IRI.

        Returns:
            The import IRI that points to the ontology to be imported. The imported ontology might have this IRI as
            its ontology IRI but this is not mandated. For example, an ontology with a non-resolvable ontology IRI
            can be deployed at a resolvable URL.
        """
        return self._iri


class OWLOntology(OWLObject, metaclass=ABCMeta):
    """Represents an OWL 2 Ontology  in the OWL 2 specification.

    An OWLOntology consists of a possibly empty set of OWLAxioms and a possibly empty set of OWLAnnotations.
    An ontology can have an ontology IRI which can be used to identify the ontology. If it has an ontology IRI then
    it may also have an ontology version IRI. Since OWL 2, an ontology need not have an ontology IRI. (See the OWL 2
    Structural Specification).

    An ontology cannot be modified directly. Changes must be applied via its OWLOntologyManager.
    """
    __slots__ = ()
    type_index: Final = 1

    @abstractmethod
    def classes_in_signature(self) -> Iterable[OWLClass]:
        """Gets the classes in the signature of this object.

        Returns:
            Classes in the signature of this object.
        """
        pass

    @abstractmethod
    def data_properties_in_signature(self) -> Iterable[OWLDataProperty]:
        """Get the data properties that are in the signature of this object.

        Returns:
            Data properties that are in the signature of this object.
        """
        pass

    @abstractmethod
    def object_properties_in_signature(self) -> Iterable[OWLObjectProperty]:
        """A convenience method that obtains the object properties that are in the signature of this object.

        Returns:
            Object properties that are in the signature of this object.
        """
        pass

    @abstractmethod
    def individuals_in_signature(self) -> Iterable[OWLNamedIndividual]:
        """A convenience method that obtains the individuals that are in the signature of this object.

        Returns:
            Individuals that are in the signature of this object.
        """
        pass

    @abstractmethod
    def equivalent_classes_axioms(self, c: OWLClass) -> Iterable[OWLEquivalentClassesAxiom]:
        """ Gets all of the equivalent axioms in this ontology that contain the specified class as an operand.

        Args:
            c: The class for which the EquivalentClasses axioms should be retrieved.

        Returns:
            EquivalentClasses axioms contained in this ontology.
        """
        pass

    @abstractmethod
    def general_class_axioms(self) -> Iterable[OWLClassAxiom]:
        """Get the general class axioms of this ontology. This includes SubClass axioms with a complex class expression
           as the sub class and EquivalentClass axioms and DisjointClass axioms with only complex class expressions.

        Returns:
            General class axioms contained in this ontology.
        """
        pass

    @abstractmethod
    def data_property_domain_axioms(self, property: OWLDataProperty) -> Iterable[OWLDataPropertyDomainAxiom]:
        """Gets the OWLDataPropertyDomainAxiom objects where the property is equal to the specified property.

        Args:
            property: The property which is equal to the property of the retrieved axioms.

        Returns:
            The axioms matching the search.
        """
        pass

    @abstractmethod
    def data_property_range_axioms(self, property: OWLDataProperty) -> Iterable[OWLDataPropertyRangeAxiom]:
        """Gets the OWLDataPropertyRangeAxiom objects where the property is equal to the specified property.

        Args:
            property: The property which is equal to the property of the retrieved axioms.

        Returns:
            The axioms matching the search.
        """
        pass

    @abstractmethod
    def object_property_domain_axioms(self, property: OWLObjectProperty) -> Iterable[OWLObjectPropertyDomainAxiom]:
        """Gets the OWLObjectPropertyDomainAxiom objects where the property is equal to the specified property.

        Args:
            property: The property which is equal to the property of the retrieved axioms.

        Returns:
            The axioms matching the search.
        """
        pass

    @abstractmethod
    def object_property_range_axioms(self, property: OWLObjectProperty) -> Iterable[OWLObjectPropertyRangeAxiom]:
        """Gets the OWLObjectPropertyRangeAxiom objects where the property is equal to the specified property.

        Args:
            property: The property which is equal to the property of the retrieved axioms.

        Returns:
            The axioms matching the search.
        """
        pass

    @abstractmethod
    def get_owl_ontology_manager(self) -> _M:
        """Gets the manager that manages this ontology."""
        pass

    @abstractmethod
    def get_ontology_id(self) -> OWLOntologyID:
        """Gets the OWLOntologyID belonging to this object.

        Returns:
            The OWLOntologyID.
        """
        pass

    def is_anonymous(self) -> bool:
        """Check whether this ontology does contain an IRI or not."""
        return self.get_ontology_id().is_anonymous()


# noinspection PyUnresolvedReferences
# noinspection PyDunderSlots
class OWLOntologyChange(metaclass=ABCMeta):
    """Represents an ontology change."""
    __slots__ = ()

    _ont: OWLOntology

    @abstractmethod
    def __init__(self, ontology: OWLOntology):
        self._ont = ontology

    def get_ontology(self) -> OWLOntology:
        """Gets the ontology that the change is/was applied to.

        Returns:
            The ontology that the change is applicable to.
        """
        return self._ont


class AddImport(OWLOntologyChange):
    """Represents an ontology change where an import statement is added to an ontology."""
    __slots__ = '_ont', '_declaration'

    def __init__(self, ontology: OWLOntology, import_declaration: OWLImportsDeclaration):
        """
        Args:
            ontology: The ontology to which the change is to be applied.
            import_declaration: The import declaration.
        """
        super().__init__(ontology)
        self._declaration = import_declaration

    def get_import_declaration(self) -> OWLImportsDeclaration:
        """Gets the import declaration that the change pertains to.

        Returns:
            The import declaration.
        """
        return self._declaration


class OWLOntologyManager(metaclass=ABCMeta):
    """An OWLOntologyManager manages a set of ontologies. It is the main point for creating, loading and accessing
    ontologies."""

    @abstractmethod
    def create_ontology(self, iri: IRI) -> OWLOntology:
        """Creates a new (empty) ontology that that has the specified ontology IRI (and no version IRI).

        Args:
            iri: The IRI of the ontology to be created.

        Returns:
            The newly created ontology, or if an ontology with the specified IRI already exists then this existing
            ontology will be returned.
        """
        pass

    @abstractmethod
    def load_ontology(self, iri: IRI) -> OWLOntology:
        """Loads an ontology that is assumed to have the specified ontology IRI as its IRI or version IRI. The ontology
        IRI will be mapped to an ontology document IRI.

        Args:
            iri: The IRI that identifies the ontology. It is expected that the ontology will also have this IRI
                (although the OWL API should tolerate situations where this is not the case).

        Returns:
            The OWLOntology representation of the ontology that was loaded.
        """
        pass

    @abstractmethod
    def apply_change(self, change: OWLOntologyChange):
        """A convenience method that applies just one change to an ontology. When this method is used through an
        OWLOntologyManager implementation, the instance used should be the one that the ontology returns through the
        get_owl_ontology_manager() call.

        Args:
            change: The change to be applied.

        Raises:
            ChangeApplied.UNSUCCESSFULLY: if the change was not applied successfully.
        """
        pass

    @abstractmethod
    def add_axiom(self, ontology: OWLOntology, axiom: OWLAxiom):
        """A convenience method that adds a single axiom to an ontology.

        Args:
            ontology: The ontology to add the axiom to.
            axiom: The axiom to be added.
        """
        pass

    @abstractmethod
    def remove_axiom(self, ontology: OWLOntology, axiom: OWLAxiom):
        """A convenience method that removes a single axiom from an ontology.

        Args:
            ontology: The ontology to remove the axiom from.
            axiom: The axiom to be removed.
        """
        pass

    @abstractmethod
    def save_ontology(self, ontology: OWLOntology, document_iri: IRI):
        """Saves the specified ontology, using the specified document IRI to determine where/how the ontology should be
        saved.

        Args:
            ontology: The ontology to be saved.
            document_iri: The document IRI where the ontology should be saved to.
        """
        pass


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
    def data_property_values(self, ind: OWLNamedIndividual, pe: OWLDataProperty, direct: bool = True) \
            -> Iterable['OWLLiteral']:
        """Gets the data property values for the specified individual and data property expression.

        Args:
            ind: The individual that is the subject of the data property values.
            pe: The data property expression whose values are to be retrieved for the specified individual.
            direct: Specifies if the direct values should be retrieved (True), or if all values should be retrieved
                (False), so that sub properties are taken into account.

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
    def flush(self) -> None:
        """Flushes any changes stored in the buffer, which causes the reasoner to take into consideration the changes
        the current root ontology specified by the changes."""
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
    def is_isolated(self):
        """Return True if this reasoner is using an isolated ontology."""
        pass

    @abstractmethod
    def is_using_triplestore(self):
        """Return True if this reasoner is using a triplestore to retrieve instances."""
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


"""Important constant objects section"""
# @TODO: Some of them must be removed from here as they are defined under owl literal

#: the built in top object property
OWLTopObjectProperty: Final = OWLObjectProperty(OWLRDFVocabulary.OWL_TOP_OBJECT_PROPERTY.get_iri())
#: the built in bottom object property
OWLBottomObjectProperty: Final = OWLObjectProperty(OWLRDFVocabulary.OWL_BOTTOM_OBJECT_PROPERTY.get_iri())
#: the built in top data property
OWLTopDataProperty: Final = OWLDataProperty(OWLRDFVocabulary.OWL_TOP_DATA_PROPERTY.get_iri())
#: the built in bottom data property
OWLBottomDataProperty: Final = OWLDataProperty(OWLRDFVocabulary.OWL_BOTTOM_DATA_PROPERTY.get_iri())

DoubleOWLDatatype: Final = OWLDatatype(XSDVocabulary.DOUBLE)  #: An object representing a double datatype.
IntegerOWLDatatype: Final = OWLDatatype(XSDVocabulary.INTEGER)  #: An object representing an integer datatype.
BooleanOWLDatatype: Final = OWLDatatype(XSDVocabulary.BOOLEAN)  #: An object representing the boolean datatype.
StringOWLDatatype: Final = OWLDatatype(XSDVocabulary.STRING)  #: An object representing the string datatype.
DateOWLDatatype: Final = OWLDatatype(XSDVocabulary.DATE)  #: An object representing the date datatype.
DateTimeOWLDatatype: Final = OWLDatatype(XSDVocabulary.DATE_TIME)  #: An object representing the dateTime datatype.
DurationOWLDatatype: Final = OWLDatatype(XSDVocabulary.DURATION)  #: An object representing the duration datatype.
#: The OWL Datatype corresponding to the top data type
TopOWLDatatype: Final = OWLDatatype(OWLRDFVocabulary.RDFS_LITERAL)

NUMERIC_DATATYPES: Final[Set[OWLDatatype]] = {DoubleOWLDatatype, IntegerOWLDatatype}
TIME_DATATYPES: Final[Set[OWLDatatype]] = {DateOWLDatatype, DateTimeOWLDatatype, DurationOWLDatatype}
