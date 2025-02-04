"""OWL Axioms"""
from abc import ABCMeta, abstractmethod
from itertools import combinations

from typing import TypeVar, List, Optional, Iterable, Generic, Union
from .owl_property import OWLDataPropertyExpression, OWLObjectPropertyExpression
from .owl_object import OWLObject, OWLEntity
from .owl_datatype import OWLDatatype, OWLDataRange
from .meta_classes import HasOperands
from .owl_property import OWLPropertyExpression, OWLProperty
from .class_expression import OWLClassExpression, OWLClass, OWLNothing, OWLThing, OWLObjectUnionOf
from .owl_individual import OWLIndividual
from .iri import IRI
from owlapy.owl_annotation import OWLAnnotationSubject, OWLAnnotationValue
from .owl_literal import OWLLiteral

_C = TypeVar('_C', bound='OWLObject')  # noqa: F821
_P = TypeVar('_P', bound='OWLPropertyExpression')  # noqa: F821
_R = TypeVar('_R', bound='OWLPropertyRange')  # noqa: F821


class OWLAxiom(OWLObject, metaclass=ABCMeta):
    """Represents Axioms in the OWL 2 Specification.

    An OWL ontology contains a set of axioms. These axioms can be annotation axioms, declaration axioms, imports axioms
    or logical axioms.
    """
    __slots__ = '_annotations'

    _annotations: List['OWLAnnotation']

    def __init__(self, annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._annotations = list(annotations) if annotations is not None else list()

    def annotations(self) -> Optional[List['OWLAnnotation']]:
        return self._annotations

    def is_annotated(self) -> bool:
        return self._annotations is not None and len(self._annotations) > 0

    def is_logical_axiom(self) -> bool:
        return False

    def is_annotation_axiom(self) -> bool:
        return False
    # TODO: XXX


class OWLLogicalAxiom(OWLAxiom, metaclass=ABCMeta):
    """A base interface of all axioms that affect the logical meaning of an ontology. This excludes declaration
    axioms (including imports declarations) and annotation axioms.
    """
    __slots__ = ()

    def __init__(self, annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(annotations=annotations)

    def is_logical_axiom(self) -> bool:
        return True


class OWLPropertyAxiom(OWLLogicalAxiom, metaclass=ABCMeta):
    """The base interface for property axioms."""
    __slots__ = ()

    def __init__(self, annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(annotations=annotations)


class OWLObjectPropertyAxiom(OWLPropertyAxiom, metaclass=ABCMeta):
    """The base interface for object property axioms."""
    __slots__ = ()


class OWLDataPropertyAxiom(OWLPropertyAxiom, metaclass=ABCMeta):
    """The base interface for data property axioms."""
    __slots__ = ()


class OWLIndividualAxiom(OWLLogicalAxiom, metaclass=ABCMeta):
    """The base interface for individual axioms."""
    __slots__ = ()

    def __init__(self, annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(annotations=annotations)


class OWLClassAxiom(OWLLogicalAxiom, metaclass=ABCMeta):
    """The base interface for class axioms."""
    __slots__ = ()

    def __init__(self, annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(annotations=annotations)


class OWLDeclarationAxiom(OWLAxiom):
    """Represents a Declaration axiom in the OWL 2 Specification. A declaration axiom declares an entity in an ontology.
       It doesn't affect the logical meaning of the ontology."""
    __slots__ = '_entity'

    _entity: OWLEntity

    def __init__(self, entity: OWLEntity, annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._entity = entity
        super().__init__(annotations=annotations)

    def get_entity(self) -> OWLEntity:
        return self._entity

    def __eq__(self, other):
        if type(other) is type(self):
            return self._entity == other._entity and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._entity, *self._annotations))

    def __repr__(self):
        return f'OWLDeclarationAxiom(entity={self._entity},annotations={self._annotations})'


class OWLDatatypeDefinitionAxiom(OWLLogicalAxiom):
    """A datatype definition DatatypeDefinition( DT DR ) defines a new datatype DT as being semantically
    equivalent to the data range DR; the latter must be a unary data range. This axiom allows one to use
    the defined datatype DT as a synonym for DR — that is, in any expression in the ontology containing
    such an axiom, DT can be replaced with DR without affecting the meaning of the ontology.

    (https://www.w3.org/TR/owl2-syntax/#Datatype_Definitions)"""
    __slots__ = '_datatype', '_datarange'

    _datatype: OWLDatatype
    _datarange: OWLDataRange

    def __init__(self, datatype: OWLDatatype, datarange: OWLDataRange,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._datatype = datatype
        self._datarange = datarange
        super().__init__(annotations=annotations)

    def get_datatype(self) -> OWLDatatype:
        return self._datatype

    def get_datarange(self) -> OWLDataRange:
        return self._datarange

    def __eq__(self, other):
        if type(other) is type(self):
            return self._datatype == other._datatype and self._datarange == other._datarange \
                and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._datatype, self._datarange, *self._annotations))

    def __repr__(self):
        return f'OWLDatatypeDefinitionAxiom(datatype={self._datatype},datarange={self._datarange},' \
               f'annotations={self._annotations})'


class OWLHasKeyAxiom(OWLLogicalAxiom, HasOperands[OWLPropertyExpression]):
    """A key axiom HasKey( CE ( OPE1 ... OPEm ) ( DPE1 ... DPEn ) ) states that each
    (named) instance of the class expression CE is uniquely identified by the object
    property expressions OPEi and/or the data property expressions DPEj — that is,
    no two distinct (named) instances of CE can coincide on the values of all
    object property expressions OPEi and all data property expressions DPEj. In each
    such axiom in an OWL ontology, m or n (or both) must be larger than zero. A key
    axiom of the form HasKey( owl:Thing ( OPE ) () ) is similar to the axiom
    InverseFunctionalObjectProperty( OPE ), the main differences being that the
    former axiom is applicable only to individuals that are explicitly named in an
    ontology, while the latter axiom is also applicable to anonymous individuals and
    individuals whose existence is implied by existential quantification.

    (https://www.w3.org/TR/owl2-syntax/#Keys)
    """
    __slots__ = '_class_expression', '_property_expressions'

    _class_expression: OWLClassExpression
    _property_expressions: List[OWLPropertyExpression]

    def __init__(self, class_expression: OWLClassExpression, property_expressions: List[OWLPropertyExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._class_expression = class_expression
        self._property_expressions = property_expressions
        super().__init__(annotations=annotations)

    def get_class_expression(self) -> OWLClassExpression:
        return self._class_expression

    def get_property_expressions(self) -> List[OWLPropertyExpression]:
        return self._property_expressions

    def operands(self) -> Iterable[OWLPropertyExpression]:
        yield from self._property_expressions

    def __eq__(self, other):
        if type(other) is type(self):
            return self._class_expression == other._class_expression \
                and set(self._property_expressions) == set(other._property_expressions) \
                and len(self._property_expressions) == len(other._property_expressions) \
                and set(self._annotations) == set(other._annotations)
        return False

    def __hash__(self):
        return hash((self._class_expression, *self._property_expressions, *self._annotations))

    def __repr__(self):
        return f'OWLHasKeyAxiom(class_expression={self._class_expression},' \
               f'property_expressions={self._property_expressions},annotations={self._annotations})'


class OWLNaryAxiom(Generic[_C], OWLAxiom, metaclass=ABCMeta):
    """Represents an axiom that contains two or more operands that could also be represented with multiple pairwise
    axioms.

    Args:
        _C: Class of contained objects.
    """
    __slots__ = ()

    @abstractmethod
    def as_pairwise_axioms(self) -> Iterable['OWLNaryAxiom[_C]']:
        pass


# noinspection PyUnresolvedReferences
# noinspection PyDunderSlots
class OWLNaryClassAxiom(OWLClassAxiom, OWLNaryAxiom[OWLClassExpression], metaclass=ABCMeta):
    """Represents an axiom that contains two or more operands that could also be represented with
        multiple pairwise axioms."""
    __slots__ = '_class_expressions'
    _class_expressions: List[OWLClassExpression]

    @abstractmethod
    def __init__(self, class_expressions: List[OWLClassExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._class_expressions = [*class_expressions]
        super().__init__(annotations=annotations)

    def class_expressions(self) -> Iterable[OWLClassExpression]:
        """Gets all of the top level class expressions that appear in this axiom.

        Returns:
            Sorted stream of class expressions that appear in the axiom.
        """
        yield from self._class_expressions

    def as_pairwise_axioms(self) -> Iterable['OWLNaryClassAxiom']:
        """Gets this axiom as a set of pairwise axioms; if the axiom contains only two operands,
        the axiom itself is returned unchanged, including its annotations.

        Returns:
            This axiom as a set of pairwise axioms.
        """
        if len(self._class_expressions) < 3:
            yield self
        else:
            yield from map(type(self), combinations(self._class_expressions, 2))

    def __eq__(self, other):
        if type(other) is type(self):
            # parsed to set to have order-insensitive comparison
            return (set(self._class_expressions) == set(other._class_expressions)
                    and len(self._class_expressions) == len(other._class_expressions)
                    and set(self._annotations) == set(other._annotations))
        return False

    def __hash__(self):
        return hash((*self._class_expressions, *self._annotations))

    def __repr__(self):
        return f'{type(self).__name__}({self._class_expressions},{self._annotations})'


class OWLEquivalentClassesAxiom(OWLNaryClassAxiom):
    """An equivalent classes axiom EquivalentClasses( CE1 ... CEn ) states that all of the class expressions CEi,
    1 ≤ i ≤ n, are semantically equivalent to each other. This axiom allows one to use each CEi as a synonym
    for each CEj — that is, in any expression in the ontology containing such an axiom, CEi can be replaced
    with CEj without affecting the meaning of the ontology.

    (https://www.w3.org/TR/owl2-syntax/#Equivalent_Classes)
    """
    __slots__ = ()

    def __init__(self, class_expressions: List[OWLClassExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(class_expressions=class_expressions, annotations=annotations)

    def __iter__(self):
        yield from self._class_expressions

    def contains_named_equivalent_class(self) -> bool:
        return any(isinstance(ce, OWLClass) for ce in self._class_expressions)

    def contains_owl_nothing(self) -> bool:
        return any(isinstance(ce, OWLNothing) for ce in self._class_expressions)

    def contains_owl_thing(self) -> bool:
        return any(isinstance(ce, OWLThing) for ce in self._class_expressions)

    def named_classes(self) -> Iterable[OWLClass]:
        yield from (ce for ce in self._class_expressions if isinstance(ce, OWLClass))


class OWLDisjointClassesAxiom(OWLNaryClassAxiom):
    """A disjoint classes axiom DisjointClasses( CE1 ... CEn ) states that all of the class expressions CEi, 1 ≤ i ≤ n,
    are pairwise disjoint; that is, no individual can be at the same time an instance of both CEi and CEj for i ≠ j.

    (https://www.w3.org/TR/owl2-syntax/#Disjoint_Classes)
    """
    __slots__ = ()

    def __init__(self, class_expressions: List[OWLClassExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(class_expressions=class_expressions, annotations=annotations)


class OWLNaryIndividualAxiom(OWLIndividualAxiom, OWLNaryAxiom[OWLIndividual], metaclass=ABCMeta):
    """Represents an axiom that contains two or more operands that could also be represented with
            multiple pairwise individual axioms."""
    __slots__ = '_individuals'

    _individuals: List[OWLIndividual]

    @abstractmethod
    def __init__(self, individuals: List[OWLIndividual],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._individuals = [*individuals]
        super().__init__(annotations=annotations)

    def individuals(self) -> Iterable[OWLIndividual]:
        """Get the individuals.

        Returns:
            Generator containing the individuals.
        """
        yield from self._individuals

    def as_pairwise_axioms(self) -> Iterable['OWLNaryIndividualAxiom']:
        if len(self._individuals) < 3:
            yield self
        else:
            yield from map(type(self), combinations(self._individuals, 2))

    def __eq__(self, other):
        if type(other) is type(self):
            return (set(self._individuals) == set(other._individuals)
                    and len(self._individuals) == len(other._individuals)
                    and set(self._annotations) == set(other._annotations))
        return False

    def __hash__(self):
        return hash((*self._individuals, *self._annotations))

    def __repr__(self):
        return f'{type(self).__name__}({self._individuals},{self._annotations})'


class OWLDifferentIndividualsAxiom(OWLNaryIndividualAxiom):
    """An individual inequality axiom DifferentIndividuals( a1 ... an ) states that all of the individuals ai,
      1 ≤ i ≤ n, are different from each other; that is, no individuals ai and aj with i ≠ j can be derived to be equal.
      This axiom can be used to axiomatize the unique name assumption — the assumption that all different individual
      names denote different individuals. (https://www.w3.org/TR/owl2-syntax/#Individual_Inequality)
      """
    __slots__ = ()

    def __init__(self, individuals: List[OWLIndividual],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(individuals=individuals, annotations=annotations)


class OWLSameIndividualAxiom(OWLNaryIndividualAxiom):
    """An individual equality axiom SameIndividual( a1 ... an ) states that all of the individuals ai, 1 ≤ i ≤ n,
    are equal to each other. This axiom allows one to use each ai as a synonym for each aj — that is, in any
    expression in the ontology containing such an axiom, ai can be replaced with aj without affecting the
    meaning of the ontology.

    (https://www.w3.org/TR/owl2-syntax/#Individual_Equality)
    """
    __slots__ = ()

    def __init__(self, individuals: List[OWLIndividual],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(individuals=individuals, annotations=annotations)


class OWLNaryPropertyAxiom(Generic[_P], OWLPropertyAxiom, OWLNaryAxiom[_P], metaclass=ABCMeta):
    """Represents an axiom that contains two or more operands that could also be represented with
       multiple pairwise property axioms."""
    __slots__ = '_properties'

    _properties: List[_P]

    @abstractmethod
    def __init__(self, properties: List[_P], annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._properties = [*properties]
        super().__init__(annotations=annotations)

    def properties(self) -> Iterable[_P]:
        """Get all the properties that appear in the axiom.

        Returns:
            Generator containing the properties.
        """
        yield from self._properties

    def as_pairwise_axioms(self) -> Iterable['OWLNaryPropertyAxiom']:
        if len(self._properties) < 3:
            yield self
        else:
            yield from map(type(self), combinations(self._properties, 2))

    def __eq__(self, other):
        if type(other) is type(self):
            # parsed to set to have order-insensitive comparison
            return (set(self._properties) == set(other._properties) and len(self._properties) == len(other._properties)
                    and set(self._annotations) == set(other._annotations))
        return False

    def __hash__(self):
        return hash((*self._properties, *self._annotations))

    def __repr__(self):
        return f'{type(self).__name__}({self._properties},{self._annotations})'


class OWLEquivalentObjectPropertiesAxiom(OWLNaryPropertyAxiom[OWLObjectPropertyExpression], OWLObjectPropertyAxiom):
    """An equivalent object properties axiom EquivalentObjectProperties( OPE1 ... OPEn ) states that all of the object
    property expressions OPEi, 1 ≤ i ≤ n, are semantically equivalent to each other. This axiom allows one to use each
    OPEi as a synonym for each OPEj — that is, in any expression in the ontology containing such an axiom, OPEi can be
    replaced with OPEj without affecting the meaning of the ontology.

    (https://www.w3.org/TR/owl2-syntax/#Equivalent_Object_Properties)
    """
    __slots__ = ()

    def __init__(self, properties: List[OWLObjectPropertyExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(properties=properties, annotations=annotations)


class OWLDisjointObjectPropertiesAxiom(OWLNaryPropertyAxiom[OWLObjectPropertyExpression], OWLObjectPropertyAxiom):
    """A disjoint object properties axiom DisjointObjectProperties( OPE1 ... OPEn ) states that all of the object
     property expressions OPEi, 1 ≤ i ≤ n, are pairwise disjoint; that is, no individual x can be connected to an
     individual y by both OPEi and OPEj for i ≠ j.

     (https://www.w3.org/TR/owl2-syntax/#Disjoint_Object_Properties)"""
    __slots__ = ()

    def __init__(self, properties: List[OWLObjectPropertyExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(properties=properties, annotations=annotations)


class OWLInverseObjectPropertiesAxiom(OWLNaryPropertyAxiom[OWLObjectPropertyExpression], OWLObjectPropertyAxiom):
    """An inverse object properties axiom InverseObjectProperties( OPE1 OPE2 ) states that the object property
    expression OPE1 is an inverse of the object property expression OPE2. Thus, if an individual x is connected by
    OPE1 to an individual y, then y is also connected by OPE2 to x, and vice versa.

    (https://www.w3.org/TR/owl2-syntax/#Inverse_Object_Properties_2)
    """
    __slots__ = '_first', '_second'

    _first: OWLObjectPropertyExpression
    _second: OWLObjectPropertyExpression

    def __init__(self, first: OWLObjectPropertyExpression, second: OWLObjectPropertyExpression,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._first = first
        self._second = second
        super().__init__(properties=[first, second], annotations=annotations)

    def get_first_property(self) -> OWLObjectPropertyExpression:
        return self._first

    def get_second_property(self) -> OWLObjectPropertyExpression:
        return self._second

    def __repr__(self):
        return f'OWLInverseObjectPropertiesAxiom(first={self._first},second={self._second},' \
               f'annotations={self._annotations})'


class OWLEquivalentDataPropertiesAxiom(OWLNaryPropertyAxiom[OWLDataPropertyExpression], OWLDataPropertyAxiom):
    """An equivalent data properties axiom EquivalentDataProperties( DPE1 ... DPEn ) states that all the data property
    expressions DPEi, 1 ≤ i ≤ n, are semantically equivalent to each other. This axiom allows one to use each DPEi as a
    synonym for each DPEj — that is, in any expression in the ontology containing such an axiom, DPEi can be replaced
    with DPEj without affecting the meaning of the ontology.

    (https://www.w3.org/TR/owl2-syntax/#Equivalent_Data_Properties)
    """
    __slots__ = ()

    def __init__(self, properties: List[OWLDataPropertyExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(properties=properties, annotations=annotations)


class OWLDisjointDataPropertiesAxiom(OWLNaryPropertyAxiom[OWLDataPropertyExpression], OWLDataPropertyAxiom):
    """A disjoint data properties axiom DisjointDataProperties( DPE1 ... DPEn ) states that all of the data property
    expressions DPEi, 1 ≤ i ≤ n, are pairwise disjoint; that is, no individual x can be connected to a literal y by both
     DPEi and DPEj for i ≠ j.

     (https://www.w3.org/TR/owl2-syntax/#Disjoint_Data_Properties)"""
    __slots__ = ()

    def __init__(self, properties: List[OWLDataPropertyExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(properties=properties, annotations=annotations)


class OWLSubClassOfAxiom(OWLClassAxiom):
    """A subclass axiom SubClassOf( CE1 CE2 ) states that the class expression CE1 is a subclass of the class
    expression CE2. Roughly speaking, this states that CE1 is more specific than CE2. Subclass axioms are a
    fundamental type of axioms in OWL 2 and can be used to construct a class hierarchy. Other kinds of class
    expression axiom can be seen as syntactic shortcuts for one or more subclass axioms.

     (https://www.w3.org/TR/owl2-syntax/#Subclass_Axioms)
     """
    __slots__ = '_sub_class', '_super_class'

    _sub_class: OWLClassExpression
    _super_class: OWLClassExpression

    def __init__(self, sub_class: OWLClassExpression, super_class: OWLClassExpression,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        """Get an equivalent classes axiom with specified operands and no annotations.

        Args:
            sub_class: The sub-class.
            super_class: The super class.
            annotations: Annotations.
        """
        self._sub_class = sub_class
        self._super_class = super_class
        super().__init__(annotations=annotations)

    @property
    def sub_class(self) -> OWLClassExpression:
        return self._sub_class
    @property
    def super_class(self) -> OWLClassExpression:
        return self._super_class

    def get_sub_class(self) -> OWLClassExpression:
        return self._sub_class

    def get_super_class(self) -> OWLClassExpression:
        return self._super_class

    def __eq__(self, other):
        if type(other) is type(self):
            return self._super_class == other._super_class and self._sub_class == other._sub_class \
                and self._annotations == other._annotations
        else:
            return False

    def __hash__(self):
        return hash((self._super_class, self._sub_class, *self._annotations))

    def __repr__(self):
        return f'OWLSubClassOfAxiom(sub_class={self._sub_class},super_class={self._super_class},' \
               f'annotations={self._annotations})'


class OWLDisjointUnionAxiom(OWLClassAxiom):
    """A disjoint union axiom DisjointUnion( C CE1 ... CEn ) states that a class C is a disjoint union of the class
    expressions CEi, 1 ≤ i ≤ n, all of which are pairwise disjoint. Such axioms are sometimes referred to as
    covering axioms, as they state that the extensions of all CEi exactly cover the extension of C. Thus, each
    instance of C is an instance of exactly one CEi, and each instance of CEi is an instance of C.

    (https://www.w3.org/TR/owl2-syntax/#Disjoint_Union_of_Class_Expressions)
    """
    __slots__ = '_cls', '_class_expressions'

    _cls: OWLClass
    _class_expressions: List[OWLClassExpression]

    def __init__(self, cls_: OWLClass, class_expressions: List[OWLClassExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._cls = cls_
        self._class_expressions = class_expressions
        super().__init__(annotations=annotations)

    def get_owl_class(self) -> OWLClass:
        return self._cls

    def get_class_expressions(self) -> Iterable[OWLClassExpression]:
        yield from self._class_expressions

    def get_owl_equivalent_classes_axiom(self) -> OWLEquivalentClassesAxiom:
        return OWLEquivalentClassesAxiom(self._cls, OWLObjectUnionOf(self._class_expressions))

    def get_owl_disjoint_classes_axiom(self) -> OWLDisjointClassesAxiom:
        return OWLDisjointClassesAxiom(self._class_expressions)

    def __eq__(self, other):
        if type(other) is type(self):
            return (self._cls == other._cls and set(self._class_expressions) == set(other._class_expressions)
                    and self._annotations == other._annotations
                    and len(self._class_expressions) == len(other._class_expressions))
        return False

    def __hash__(self):
        return hash((self._cls, *self._class_expressions, *self._annotations))

    def __repr__(self):
        return f'OWLDisjointUnionAxiom(class={self._cls},class_expressions={self._class_expressions},' \
               f'annotations={self._annotations})'


class OWLClassAssertionAxiom(OWLIndividualAxiom):
    """A class assertion ClassAssertion( CE a ) states that the individual a is an instance of the class expression CE.

    (https://www.w3.org/TR/owl2-syntax/#Class_Assertions)
    """
    __slots__ = '_individual', '_class_expression'

    _individual: OWLIndividual
    _class_expression: OWLClassExpression

    def __init__(self, individual: OWLIndividual, class_expression: OWLClassExpression,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        """Get a ClassAssertion axiom for the specified individual and class expression.
        Args:
            individual: The individual.
            class_expression: The class the individual belongs to.
            annotations: Annotations.
        """
        self._individual = individual
        self._class_expression = class_expression
        super().__init__(annotations=annotations)

    def get_individual(self) -> OWLIndividual:
        return self._individual

    def get_class_expression(self) -> OWLClassExpression:
        return self._class_expression

    def __eq__(self, other):
        if type(other) is type(self):
            return self._class_expression == other._class_expression and self._individual == other._individual \
                and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._individual, self._class_expression, *self._annotations))

    def __repr__(self):
        return f'OWLClassAssertionAxiom(individual={self._individual},class_expression={self._class_expression},' \
               f'annotations={self._annotations})'


class OWLAnnotationProperty(OWLProperty):
    """Represents an AnnotationProperty in the OWL 2 specification."""
    __slots__ = '_iri'

    _iri: IRI

    def __init__(self, iri: Union[IRI, str]):
        """Get a new OWLAnnotationProperty object.

        Args:
            iri: New OWLAnnotationProperty IRI.
        """
        if isinstance(iri, IRI):
            self._iri = iri
        else:
            self._iri = IRI.create(iri)

    @property
    def iri(self) -> IRI:
        return self._iri

    @property
    def str(self) -> str:
        return self._iri.as_str()


class OWLAnnotation(OWLObject):
    """Annotations are used in the various types of annotation axioms, which bind annotations to their subjects
    (i.e. axioms or declarations)."""
    __slots__ = '_property', '_value'

    _property: OWLAnnotationProperty
    _value: OWLAnnotationValue

    def __init__(self, property: OWLAnnotationProperty, value: OWLAnnotationValue):
        """Gets an annotation.

        Args:
            property: the annotation property.
            value: The annotation value.
        """
        self._property = property
        self._value = value

    def get_property(self) -> OWLAnnotationProperty:
        """Gets the property that this annotation acts along.

        Returns:
            The annotation property.
        """
        return self._property

    def get_value(self) -> OWLAnnotationValue:
        """Gets the annotation value. The type of value will depend upon the type of the annotation e.g. whether the
        annotation is an OWLLiteral, an IRI or an OWLAnonymousIndividual.

        Returns:
            The annotation value.
        """
        return self._value

    def __eq__(self, other):
        if type(other) is type(self):
            return self._property == other._property and self._value == other._value
        return NotImplemented

    def __hash__(self):
        return hash((self._property, self._value))

    def __repr__(self):
        return f'OWLAnnotation({self._property}, {self._value})'


class OWLAnnotationAxiom(OWLAxiom, metaclass=ABCMeta):
    """A super interface for annotation axioms."""
    __slots__ = ()

    def is_annotation_axiom(self) -> bool:
        return True


class OWLAnnotationAssertionAxiom(OWLAnnotationAxiom):
    """An annotation assertion AnnotationAssertion( AP as av ) states that the annotation subject as — an IRI or an
    anonymous individual — is annotated with the annotation property AP and the annotation value av.


    (https://www.w3.org/TR/owl2-syntax/#Annotation_Assertion)
    """
    __slots__ = '_subject', '_annotation'

    _subject: OWLAnnotationSubject
    _annotation: OWLAnnotation

    def __init__(self, subject: OWLAnnotationSubject, annotation: OWLAnnotation,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        """Get an annotation assertion axiom - with annotations.

        Args:
            subject: Subject.
            annotation: Annotation.
        """
        assert isinstance(subject, OWLAnnotationSubject)
        assert isinstance(annotation, OWLAnnotation)
        super().__init__(annotations)
        self._subject = subject
        self._annotation = annotation

    def get_subject(self) -> OWLAnnotationSubject:
        """Gets the subject of this object.

        Returns:
            The subject.
        """
        return self._subject

    def get_property(self) -> OWLAnnotationProperty:
        """Gets the property.

        Returns:
            The property.
        """
        return self._annotation.get_property()

    def get_value(self) -> OWLAnnotationValue:
        """Gets the annotation value. This is either an IRI, an OWLAnonymousIndividual or an OWLLiteral.

        Returns:
            The annotation value.
        """
        return self._annotation.get_value()

    def __eq__(self, other):
        if type(other) is type(self):
            return self._subject == other._subject and self._annotation == other._annotation
        return NotImplemented

    def __hash__(self):
        return hash((self._subject, self._annotation))

    def __repr__(self):
        return f'OWLAnnotationAssertionAxiom({self._subject}, {self._annotation}, {self.annotations()})'
class OWLSubAnnotationPropertyOfAxiom(OWLAnnotationAxiom):
    """An annotation subproperty axiom SubAnnotationPropertyOf( AP1 AP2 ) states that the annotation property AP1 is
    a subproperty of the annotation property AP2.

    (https://www.w3.org/TR/owl2-syntax/#Annotation_Subproperties)
    """
    __slots__ = '_sub_property', '_super_property'

    _sub_property: OWLAnnotationProperty
    _super_property: OWLAnnotationProperty

    def __init__(self, sub_property: OWLAnnotationProperty, super_property: OWLAnnotationProperty,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._sub_property = sub_property
        self._super_property = super_property
        super().__init__(annotations=annotations)

    def get_sub_property(self) -> OWLAnnotationProperty:
        return self._sub_property

    def get_super_property(self) -> OWLAnnotationProperty:
        return self._super_property

    def __eq__(self, other):
        if type(other) is type(self):
            return self._sub_property == other._sub_property and self._super_property == other._super_property \
                and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._sub_property, self._super_property, *self._annotations))

    def __repr__(self):
        return f'OWLSubAnnotationPropertyOfAxiom(sub_property={self._sub_property},' \
               f'super_property={self._super_property},annotations={self._annotations})'


class OWLAnnotationPropertyDomainAxiom(OWLAnnotationAxiom):
    """An annotation property domain axiom AnnotationPropertyDomain( AP U ) states that the domain of the annotation
    property AP is the IRI U.

     (https://www.w3.org/TR/owl2-syntax/#Annotation_Property_Domain)"""
    __slots__ = '_property', '_domain'

    _property: OWLAnnotationProperty
    _domain: IRI

    def __init__(self, property_: OWLAnnotationProperty, domain: IRI,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._property = property_
        self._domain = domain
        super().__init__(annotations=annotations)

    def get_property(self) -> OWLAnnotationProperty:
        return self._property

    def get_domain(self) -> IRI:
        return self._domain

    def __eq__(self, other):
        if type(other) is type(self):
            return self._property == other._property and self._domain == other._domain \
                and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._property, self._domain, *self._annotations))

    def __repr__(self):
        return f'OWLAnnotationPropertyDomainAxiom({repr(self._property)},{repr(self._domain)},' \
               f'{repr(self._annotations)})'


class OWLAnnotationPropertyRangeAxiom(OWLAnnotationAxiom):
    """An annotation property range axiom AnnotationPropertyRange( AP U )
    states that the range of the annotation property AP is the IRI U.

    (https://www.w3.org/TR/owl2-syntax/#Annotation_Property_Range)"""
    __slots__ = '_property', '_range'

    _property: OWLAnnotationProperty
    _range: IRI

    def __init__(self, property_: OWLAnnotationProperty, range_: IRI,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._property = property_
        self._range = range_
        super().__init__(annotations=annotations)

    def get_property(self) -> OWLAnnotationProperty:
        return self._property

    def get_range(self) -> IRI:
        return self._range

    def __eq__(self, other):
        if type(other) is type(self):
            return self._property == other._property and self._range == other._range \
                and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._property, self._range, *self._annotations))

    def __repr__(self):
        return f'OWLAnnotationPropertyRangeAxiom({repr(self._property)},{repr(self._range)},' \
               f'{repr(self._annotations)})'


class OWLSubPropertyAxiom(Generic[_P], OWLPropertyAxiom):
    """
    Base interface for object and data sub-property axioms.
    """
    __slots__ = '_sub_property', '_super_property'

    _sub_property: _P
    _super_property: _P

    @abstractmethod
    def __init__(self, sub_property: _P, super_property: _P,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        self._sub_property = sub_property
        self._super_property = super_property
        super().__init__(annotations=annotations)

    def get_sub_property(self) -> _P:
        return self._sub_property

    def get_super_property(self) -> _P:
        return self._super_property

    def __eq__(self, other):
        if type(other) is type(self):
            return self._sub_property == other._sub_property and self._super_property == other._super_property \
                and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._sub_property, self._super_property, *self._annotations))

    def __repr__(self):
        return f'{type(self).__name__}(sub_property={self._sub_property},super_property={self._super_property},' \
               f'annotations={self._annotations})'


class OWLSubObjectPropertyOfAxiom(OWLSubPropertyAxiom[OWLObjectPropertyExpression], OWLObjectPropertyAxiom):
    """Object subproperty axioms are analogous to subclass axioms, and they come in two forms.
       The basic form is SubObjectPropertyOf( OPE1 OPE2 ). This axiom states that the object property expression OPE1
       is a subproperty of the object property expression OPE2 — that is, if an individual x is connected by OPE1 to an
       individual y, then x is also connected by OPE2 to y.
       The more complex form is SubObjectPropertyOf( ObjectPropertyChain( OPE1 ... OPEn ) OPE )
       but ObjectPropertyChain is not represented in owlapy yet.

       (https://www.w3.org/TR/owl2-syntax/#Object_Subproperties)"""
    __slots__ = ()

    def __init__(self, sub_property: OWLObjectPropertyExpression, super_property: OWLObjectPropertyExpression,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(sub_property=sub_property, super_property=super_property, annotations=annotations)


class OWLSubDataPropertyOfAxiom(OWLSubPropertyAxiom[OWLDataPropertyExpression], OWLDataPropertyAxiom):
    """A data subproperty axiom SubDataPropertyOf( DPE1 DPE2 ) states that the data property expression DPE1 is a
    subproperty of the data property expression DPE2 — that is, if an individual x is connected by DPE1 to a literal y,
     then x is connected by DPE2 to y as well.

     (https://www.w3.org/TR/owl2-syntax/#Data_Subproperties)"""
    __slots__ = ()

    def __init__(self, sub_property: OWLDataPropertyExpression, super_property: OWLDataPropertyExpression,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(sub_property=sub_property, super_property=super_property, annotations=annotations)


class OWLPropertyAssertionAxiom(Generic[_P, _C], OWLIndividualAxiom, metaclass=ABCMeta):
    """Base class for Property Assertion axioms."""
    __slots__ = '_subject', '_property', '_object'

    _subject: OWLIndividual
    _property: _P
    _object: _C

    @abstractmethod
    def __init__(self, subject: OWLIndividual, property_: _P, object_: _C,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        """Get a PropertyAssertion axiom for the specified subject, property, object.
        Args:
            subject: The subject of the property assertion.
            property_: The property of the property assertion.
            object_: The object of the property assertion.
            annotations: Annotations.
        """
        assert isinstance(subject, OWLIndividual)

        self._subject = subject
        self._property = property_
        self._object = object_
        super().__init__(annotations=annotations)

    def get_subject(self) -> OWLIndividual:
        return self._subject

    def get_property(self) -> _P:
        return self._property

    def get_object(self) -> _C:
        return self._object

    def __eq__(self, other):
        if type(other) is type(self):
            return self._subject == other._subject and self._property == other._property and \
                self._object == other._object and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._subject, self._property, self._object, *self._annotations))

    def __repr__(self):
        return f'{type(self).__name__}(subject={self._subject},property_={self._property},' \
               f'object_={self._object},annotations={self._annotations})'


class OWLObjectPropertyAssertionAxiom(OWLPropertyAssertionAxiom[OWLObjectPropertyExpression, OWLIndividual]):
    """A positive object property assertion ObjectPropertyAssertion( OPE a1 a2 ) states that the individual a1 is
     connected by the object property expression OPE to the individual a2.

     (https://www.w3.org/TR/owl2-syntax/#Positive_Object_Property_Assertions)
     """
    __slots__ = ()

    def __init__(self, subject: OWLIndividual, property_: OWLObjectPropertyExpression, object_: OWLIndividual,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(subject, property_, object_, annotations)


class OWLNegativeObjectPropertyAssertionAxiom(OWLPropertyAssertionAxiom[OWLObjectPropertyExpression, OWLIndividual]):
    """A negative object property assertion NegativeObjectPropertyAssertion( OPE a1 a2 ) states that the individual a1
    is not connected by the object property expression OPE to the individual a2.

    (https://www.w3.org/TR/owl2-syntax/#Negative_Object_Property_Assertions)
    """
    __slots__ = ()

    def __init__(self, subject: OWLIndividual, property_: OWLObjectPropertyExpression, object_: OWLIndividual,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(subject, property_, object_, annotations)


class OWLDataPropertyAssertionAxiom(OWLPropertyAssertionAxiom[OWLDataPropertyExpression, OWLLiteral]):
    """A positive data property assertion DataPropertyAssertion( DPE a lt ) states that the individual a is connected
    by the data property expression DPE to the literal lt.

    (https://www.w3.org/TR/owl2-syntax/#Positive_Data_Property_Assertions)
    """
    __slots__ = ()

    def __init__(self, subject: OWLIndividual, property_: OWLDataPropertyExpression, object_: OWLLiteral,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        assert isinstance(subject,OWLIndividual), f"subject must be an OWLIndividual. Currently, {subject} of {type(subject)}"
        assert isinstance(property_,OWLDataPropertyExpression), f"property_ must be an OWLDataPropertyExpression. Currently, {type(property_)}"
        assert isinstance(object_,OWLLiteral), f"object_ must be an OWLLiteral. Currently, {type(object_)}"
        super().__init__(subject, property_, object_, annotations)


class OWLNegativeDataPropertyAssertionAxiom(OWLPropertyAssertionAxiom[OWLDataPropertyExpression, OWLLiteral]):
    """A negative data property assertion NegativeDataPropertyAssertion( DPE a lt ) states that the individual a is not
    connected by the data property expression DPE to the literal lt.

    (https://www.w3.org/TR/owl2-syntax/#Negative_Data_Property_Assertions)
    """
    __slots__ = ()

    def __init__(self, subject: OWLIndividual, property_: OWLDataPropertyExpression, object_: OWLLiteral,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(subject, property_, object_, annotations)


class OWLUnaryPropertyAxiom(Generic[_P], OWLPropertyAxiom, metaclass=ABCMeta):
    """Base class for Unary property axiom."""
    __slots__ = '_property'

    _property: _P

    def __init__(self, property_: _P, annotations: Optional[Iterable[OWLAnnotation]] = None):
        self._property = property_
        super().__init__(annotations=annotations)

    def get_property(self) -> _P:
        return self._property


class OWLObjectPropertyCharacteristicAxiom(OWLUnaryPropertyAxiom[OWLObjectPropertyExpression],
                                           OWLObjectPropertyAxiom, metaclass=ABCMeta):
    """Base interface for functional object property axiom."""
    __slots__ = ()

    @abstractmethod
    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)

    def __eq__(self, other):
        if type(other) is type(self):
            return self._property == other._property and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._property, *self._annotations))

    def __repr__(self):
        return f"{type(self).__name__}({repr(self._property)},{repr(self._annotations)})"


class OWLFunctionalObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """An object property functionality axiom FunctionalObjectProperty( OPE ) states that
    the object property expression OPE is functional — that is, for each individual x,
    there can be at most one distinct individual y such that x is connected by OPE to y.

    (https://www.w3.org/TR/owl2-syntax/#Functional_Object_Properties)"""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLAsymmetricObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """An object property asymmetry axiom AsymmetricObjectProperty( OPE ) states that
    the object property expression OPE is asymmetric — that is, if an individual x is
    connected by OPE to an individual y, then y cannot be connected by OPE to x.

    (https://www.w3.org/TR/owl2-syntax/#Symmetric_Object_Properties)"""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLInverseFunctionalObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """An object property inverse functionality axiom InverseFunctionalObjectProperty( OPE )
    states that the object property expression OPE is inverse-functional — that is, for each
    individual x, there can be at most one individual y such that y is connected by OPE with x.

    (https://www.w3.org/TR/owl2-syntax/#Inverse-Functional_Object_Properties)
    """
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLIrreflexiveObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """An object property irreflexivity axiom IrreflexiveObjectProperty( OPE ) states that the
    object property expression OPE is irreflexive — that is, no individual is connected by
    OPE to itself.

    (https://www.w3.org/TR/owl2-syntax/#Irreflexive_Object_Properties)
    """
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLReflexiveObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """An object property reflexivity axiom ReflexiveObjectProperty( OPE ) states that the
    object property expression OPE is reflexive — that is, each individual is connected
    by OPE to itself. Each such axiom can be seen as a syntactic shortcut for the
    following axiom: SubClassOf( owl:Thing ObjectHasSelf( OPE ) )

    (https://www.w3.org/TR/owl2-syntax/#Reflexive_Object_Properties)"""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLSymmetricObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """An object property symmetry axiom SymmetricObjectProperty( OPE ) states that
    the object property expression OPE is symmetric — that is, if an individual x
    is connected by OPE to an individual y, then y is also connected by OPE to x.
    Each such axiom can be seen as a syntactic shortcut for the following axiom:
     SubObjectPropertyOf( OPE ObjectInverseOf( OPE ) )

     (https://www.w3.org/TR/owl2-syntax/#Symmetric_Object_Properties)
     """
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLTransitiveObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """An object property transitivity axiom TransitiveObjectProperty( OPE ) states that the
    object property expressionOPE is transitive — that is, if an individual x is connected
    by OPE to an individual y that is connected by OPE to an individual z, then x is also
    connected by OPE to z. Each such axiom can be seen as a syntactic shortcut for the
    following axiom: SubObjectPropertyOf( ObjectPropertyChain( OPE OPE ) OPE )

     (https://www.w3.org/TR/owl2-syntax/#Transitive_Object_Properties)
     """
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLDataPropertyCharacteristicAxiom(OWLUnaryPropertyAxiom[OWLDataPropertyExpression],
                                         OWLDataPropertyAxiom, metaclass=ABCMeta):
    """Base interface for Functional data property axiom."""
    __slots__ = ()

    @abstractmethod
    def __init__(self, property_: OWLDataPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)

    def __eq__(self, other):
        if type(other) is type(self):
            return self._property == other._property and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._property, *self._annotations))

    def __repr__(self):
        return f"{type(self).__name__}({repr(self._property)},{repr(self._annotations)})"


class OWLFunctionalDataPropertyAxiom(OWLDataPropertyCharacteristicAxiom):
    """A data property functionality axiom FunctionalDataProperty( DPE ) states that
    the data property expression DPE is functional — that is, for each individual x,
    there can be at most one distinct literal y such that x is connected by DPE with
    y. Each such axiom can be seen as a syntactic shortcut for the following axiom:
    SubClassOf( owl:Thing DataMaxCardinality( 1 DPE ) )

    (https://www.w3.org/TR/owl2-syntax/#Transitive_Object_Properties)
    """
    __slots__ = ()

    def __init__(self, property_: OWLDataPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLPropertyDomainAxiom(Generic[_P], OWLUnaryPropertyAxiom[_P], metaclass=ABCMeta):
    """Base class for Property Domain axioms."""
    __slots__ = '_domain'

    _domain: OWLClassExpression

    @abstractmethod
    def __init__(self, property_: _P, domain: OWLClassExpression,
                 annotations: Optional[Iterable[OWLAnnotation]] = None):
        self._domain = domain
        super().__init__(property_=property_, annotations=annotations)

    def get_domain(self) -> OWLClassExpression:
        return self._domain

    def __eq__(self, other):
        if type(other) is type(self):
            return self._property == other._property and self._domain == other._domain \
                and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._property, self._domain, *self._annotations))

    def __repr__(self):
        return f"{type(self).__name__}({repr(self._property)},{repr(self._domain)},{repr(self._annotations)})"


class OWLPropertyRangeAxiom(Generic[_P, _R], OWLUnaryPropertyAxiom[_P], metaclass=ABCMeta):
    """Base class for Property Range axioms."""
    __slots__ = '_range'

    _range: _R

    @abstractmethod
    def __init__(self, property_: _P, range_: _R, annotations: Optional[Iterable[OWLAnnotation]] = None):
        self._range = range_
        super().__init__(property_=property_, annotations=annotations)

    @property
    def prop(self):
        return self._property

    @property
    def range(self):
        return self._range

    def get_range(self) -> _R:
        return self._range

    def __eq__(self, other):
        if type(other) is type(self):
            return self._property == other._property and self._range == other._range \
                and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._property, self._range, *self._annotations))

    def __repr__(self):
        return f"{type(self).__name__}({repr(self._property)},{repr(self._range)},{repr(self._annotations)})"


class OWLObjectPropertyDomainAxiom(OWLPropertyDomainAxiom[OWLObjectPropertyExpression]):
    """ An object property domain axiom ObjectPropertyDomain( OPE CE ) states that the domain of the
    object property expression OPE is the class expression CE — that is, if an individual x is
    connected by OPE with some other individual, then x is an instance of CE. Each such axiom can
    be seen as a syntactic shortcut for the following axiom:
    SubClassOf( ObjectSomeValuesFrom( OPE owl:Thing ) CE )

    (https://www.w3.org/TR/owl2-syntax/#Object_Property_Domain)
    """
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, domain: OWLClassExpression,
                 annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, domain=domain, annotations=annotations)

    @property
    def prop(self):
        return self._property


class OWLDataPropertyDomainAxiom(OWLPropertyDomainAxiom[OWLDataPropertyExpression]):
    """ A data property domain axiom DataPropertyDomain( DPE CE ) states that the domain of the
    data property expression DPE is the class expression CE — that is, if an individual x is
    connected by DPE with some literal, then x is an instance of CE. Each such axiom can be
    seen as a syntactic shortcut for the following axiom:
    SubClassOf( DataSomeValuesFrom( DPE rdfs:Literal) CE )

    (https://www.w3.org/TR/owl2-syntax/#Data_Property_Domain)
    """
    __slots__ = ()

    def __init__(self, property_: OWLDataPropertyExpression, domain: OWLClassExpression,
                 annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, domain=domain, annotations=annotations)


class OWLObjectPropertyRangeAxiom(OWLPropertyRangeAxiom[OWLObjectPropertyExpression, OWLClassExpression]):
    """ An object property range axiom ObjectPropertyRange( OPE CE ) states that the range of the object property
    expression OPE is the class expression CE — that is, if some individual is connected by OPE with an individual x,
    then x is an instance of CE. Each such axiom can be seen as a syntactic shortcut for the following axiom:
    SubClassOf( owl:Thing ObjectAllValuesFrom( OPE CE ) )

    (https://www.w3.org/TR/owl2-syntax/#Object_Property_Range)
    """
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, range_: OWLClassExpression,
                 annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, range_=range_, annotations=annotations)


class OWLDataPropertyRangeAxiom(OWLPropertyRangeAxiom[OWLDataPropertyExpression, OWLDataRange]):
    """ A data property range axiom DataPropertyRange( DPE DR ) states that the range of the data property
    expression DPE is the data range DR — that is, if some individual is connected by DPE with a literal x,
    then x is in DR. The arity of DR must be one. Each such axiom can be seen as a syntactic shortcut for
    the following axiom:  SubClassOf( owl:Thing DataAllValuesFrom( DPE DR ) )

    (https://www.w3.org/TR/owl2-syntax/#Data_Property_Range)
    """
    __slots__ = ()

    def __init__(self, property_: OWLDataPropertyExpression, range_: OWLDataRange,
                 annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, range_=range_, annotations=annotations)
