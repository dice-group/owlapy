from abc import ABCMeta, abstractmethod

from typing import TypeVar, List, Optional, Iterable, Generic, Final
from .owl_property import OWLDataPropertyExpression, OWLObjectPropertyExpression
from .owlobject import OWLObject, OWLEntity
from .types import OWLDatatype, OWLDataRange
from .has import HasOperands
from .owl_property import OWLPropertyExpression, OWLProperty
from .owl_class_expression import OWLClassExpression, OWLClass
from .owl_individual import OWLIndividual
from .iri import IRI
from owlapy.owl_annotation import OWLAnnotationSubject, OWLAnnotationValue
from .owl_literal import OWLLiteral

_C = TypeVar('_C', bound='OWLObject')  #:
_P = TypeVar('_P', bound='OWLPropertyExpression')  #:
_R = TypeVar('_R', bound='OWLPropertyRange')  #:

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
    """A base interface of all axioms that affect the logical meaning of an ontology. This excludes declaration axioms
    (including imports declarations) and annotation axioms.
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
    """Represents a DatatypeDefinition axiom in the OWL 2 Specification."""
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
    """Represents a HasKey axiom in the OWL 2 Specification."""
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
                and self._property_expressions == other._property_expressions \
                and self._annotations == other._annotations
        return NotImplemented

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
            return self._class_expressions == other._class_expressions and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((*self._class_expressions, *self._annotations))

    def __repr__(self):
        return f'{type(self).__name__}({self._class_expressions},{self._annotations})'


class OWLEquivalentClassesAxiom(OWLNaryClassAxiom):
    """Represents an EquivalentClasses axiom in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, class_expressions: List[OWLClassExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(class_expressions=class_expressions, annotations=annotations)

    def contains_named_equivalent_class(self) -> bool:
        return any(isinstance(ce, OWLClass) for ce in self._class_expressions)

    def contains_owl_nothing(self) -> bool:
        return any(isinstance(ce, OWLNothing) for ce in self._class_expressions)

    def contains_owl_thing(self) -> bool:
        return any(isinstance(ce, OWLThing) for ce in self._class_expressions)

    def named_classes(self) -> Iterable[OWLClass]:
        yield from (ce for ce in self._class_expressions if isinstance(ce, OWLClass))


class OWLDisjointClassesAxiom(OWLNaryClassAxiom):
    """Represents a DisjointClasses axiom in the OWL 2 Specification."""
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
            return self._individuals == other._individuals and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((*self._individuals, *self._annotations))

    def __repr__(self):
        return f'{type(self).__name__}({self._individuals},{self._annotations})'


class OWLDifferentIndividualsAxiom(OWLNaryIndividualAxiom):
    """Represents a DifferentIndividuals axiom in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, individuals: List[OWLIndividual],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(individuals=individuals, annotations=annotations)


class OWLSameIndividualAxiom(OWLNaryIndividualAxiom):
    """Represents a SameIndividual axiom in the OWL 2 Specification."""
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
            return self._properties == other._properties and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((*self._properties, *self._annotations))

    def __repr__(self):
        return f'{type(self).__name__}({self._properties},{self._annotations})'


class OWLEquivalentObjectPropertiesAxiom(OWLNaryPropertyAxiom[OWLObjectPropertyExpression], OWLObjectPropertyAxiom):
    """Represents EquivalentObjectProperties axioms in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, properties: List[OWLObjectPropertyExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(properties=properties, annotations=annotations)


class OWLDisjointObjectPropertiesAxiom(OWLNaryPropertyAxiom[OWLObjectPropertyExpression], OWLObjectPropertyAxiom):
    """Represents DisjointObjectProperties axioms in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, properties: List[OWLObjectPropertyExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(properties=properties, annotations=annotations)


class OWLInverseObjectPropertiesAxiom(OWLNaryPropertyAxiom[OWLObjectPropertyExpression], OWLObjectPropertyAxiom):
    """Represents InverseObjectProperties axioms in the OWL 2 Specification."""
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
    """Represents EquivalentDataProperties axioms in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, properties: List[OWLDataPropertyExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(properties=properties, annotations=annotations)


class OWLDisjointDataPropertiesAxiom(OWLNaryPropertyAxiom[OWLDataPropertyExpression], OWLDataPropertyAxiom):
    """Represents DisjointDataProperties axioms in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, properties: List[OWLDataPropertyExpression],
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(properties=properties, annotations=annotations)


class OWLSubClassOfAxiom(OWLClassAxiom):
    """Represents an SubClassOf axiom in the OWL 2 Specification."""
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

    def get_sub_class(self) -> OWLClassExpression:
        return self._sub_class

    def get_super_class(self) -> OWLClassExpression:
        return self._super_class

    def __eq__(self, other):
        if type(other) is type(self):
            return self._super_class == other._super_class and self._sub_class == other._sub_class \
                and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._super_class, self._sub_class, *self._annotations))

    def __repr__(self):
        return f'OWLSubClassOfAxiom(sub_class={self._sub_class},super_class={self._super_class},' \
               f'annotations={self._annotations})'


class OWLDisjointUnionAxiom(OWLClassAxiom):
    """Represents a DisjointUnion axiom in the OWL 2 Specification."""
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
            return self._cls == other._cls and self._class_expressions == other._class_expressions \
                and self._annotations == other._annotations
        return NotImplemented

    def __hash__(self):
        return hash((self._cls, *self._class_expressions, *self._annotations))

    def __repr__(self):
        return f'OWLDisjointUnionAxiom(class={self._cls},class_expressions={self._class_expressions},' \
               f'annotations={self._annotations})'


class OWLClassAssertionAxiom(OWLIndividualAxiom):
    """Represents ClassAssertion axioms in the OWL 2 Specification."""
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

    def __init__(self, iri: IRI):
        """Get a new OWLAnnotationProperty object.

        Args:
            iri: New OWLAnnotationProperty IRI.
        """
        self._iri = iri

    def get_iri(self) -> IRI:
        # documented in parent
        return self._iri

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
    """Represents AnnotationAssertion axioms in the OWL 2 specification."""
    __slots__ = '_subject', '_annotation'

    _subject: OWLAnnotationSubject
    _annotation: OWLAnnotation

    def __init__(self, subject: OWLAnnotationSubject, annotation: OWLAnnotation):
        """Get an annotation assertion axiom - with annotations.

        Args:
            subject: Subject.
            annotation: Annotation.
        """
        assert isinstance(subject, OWLAnnotationSubject)
        assert isinstance(annotation, OWLAnnotation)

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
        return f'OWLAnnotationAssertionAxiom({self._subject}, {self._annotation})'
class OWLSubAnnotationPropertyOfAxiom(OWLAnnotationAxiom):
    """Represents an SubAnnotationPropertyOf axiom in the OWL 2 specification."""
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
    """Represents an AnnotationPropertyDomain axiom in the OWL 2 specification."""
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
    """Represents an AnnotationPropertyRange axiom in the OWL 2 specification."""
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
    """Represents a SubObjectPropertyOf axiom in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, sub_property: OWLObjectPropertyExpression, super_property: OWLObjectPropertyExpression,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(sub_property=sub_property, super_property=super_property, annotations=annotations)
class OWLSubDataPropertyOfAxiom(OWLSubPropertyAxiom[OWLDataPropertyExpression], OWLDataPropertyAxiom):
    """Represents a SubDataPropertyOf axiom in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, sub_property: OWLDataPropertyExpression, super_property: OWLDataPropertyExpression,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(sub_property=sub_property, super_property=super_property, annotations=annotations)

class OWLPropertyAssertionAxiom(Generic[_P, _C], OWLIndividualAxiom, metaclass=ABCMeta):
    """Represents a PropertyAssertion axiom in the OWL 2 specification."""
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
        return f'{type(self).__name__}(subject={self._subject},property={self._property},' \
               f'object={self._object},annotation={self._annotations})'
class OWLObjectPropertyAssertionAxiom(OWLPropertyAssertionAxiom[OWLObjectPropertyExpression, OWLIndividual]):
    """Represents an ObjectPropertyAssertion axiom in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, subject: OWLIndividual, property_: OWLObjectPropertyExpression, object_: OWLIndividual,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(subject, property_, object_, annotations)
class OWLNegativeObjectPropertyAssertionAxiom(OWLPropertyAssertionAxiom[OWLObjectPropertyExpression, OWLIndividual]):
    """Represents a NegativeObjectPropertyAssertion axiom in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, subject: OWLIndividual, property_: OWLObjectPropertyExpression, object_: OWLIndividual,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(subject, property_, object_, annotations)
class OWLDataPropertyAssertionAxiom(OWLPropertyAssertionAxiom[OWLDataPropertyExpression, OWLLiteral]):
    """Represents an DataPropertyAssertion axiom in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, subject: OWLIndividual, property_: OWLDataPropertyExpression, object_: OWLLiteral,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(subject, property_, object_, annotations)
class OWLNegativeDataPropertyAssertionAxiom(OWLPropertyAssertionAxiom[OWLDataPropertyExpression, OWLLiteral]):
    """Represents an NegativeDataPropertyAssertion axiom in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, subject: OWLIndividual, property_: OWLDataPropertyExpression, object_: OWLLiteral,
                 annotations: Optional[Iterable['OWLAnnotation']] = None):
        super().__init__(subject, property_, object_, annotations)
class OWLUnaryPropertyAxiom(Generic[_P], OWLPropertyAxiom, metaclass=ABCMeta):
    """Unary property axiom."""
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
    """Represents FunctionalObjectProperty axioms in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLAsymmetricObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """Represents AsymmetricObjectProperty axioms in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLInverseFunctionalObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """Represents InverseFunctionalObjectProperty axioms in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLIrreflexiveObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """Represents IrreflexiveObjectProperty axioms in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLReflexiveObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """Represents ReflexiveObjectProperty axioms in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLSymmetricObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """Represents SymmetricObjectProperty axioms in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLTransitiveObjectPropertyAxiom(OWLObjectPropertyCharacteristicAxiom):
    """Represents TransitiveObjectProperty axioms in the OWL 2 specification."""
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
    """Represents FunctionalDataProperty axioms in the OWL 2 specification."""
    __slots__ = ()

    def __init__(self, property_: OWLDataPropertyExpression, annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, annotations=annotations)


class OWLPropertyDomainAxiom(Generic[_P], OWLUnaryPropertyAxiom[_P], metaclass=ABCMeta):
    """Represents ObjectPropertyDomain axioms in the OWL 2 specification."""
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
    """Represents ObjectPropertyRange axioms in the OWL 2 specification."""
    __slots__ = '_range'

    _range: _R

    @abstractmethod
    def __init__(self, property_: _P, range_: _R, annotations: Optional[Iterable[OWLAnnotation]] = None):
        self._range = range_
        super().__init__(property_=property_, annotations=annotations)

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
    """ Represents a ObjectPropertyDomain axiom in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, domain: OWLClassExpression,
                 annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, domain=domain, annotations=annotations)


class OWLDataPropertyDomainAxiom(OWLPropertyDomainAxiom[OWLDataPropertyExpression]):
    """ Represents a DataPropertyDomain axiom in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, property_: OWLDataPropertyExpression, domain: OWLClassExpression,
                 annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, domain=domain, annotations=annotations)


class OWLObjectPropertyRangeAxiom(OWLPropertyRangeAxiom[OWLObjectPropertyExpression, OWLClassExpression]):
    """ Represents a ObjectPropertyRange axiom in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, property_: OWLObjectPropertyExpression, range_: OWLClassExpression,
                 annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, range_=range_, annotations=annotations)


class OWLDataPropertyRangeAxiom(OWLPropertyRangeAxiom[OWLDataPropertyExpression, OWLDataRange]):
    """ Represents a DataPropertyRange axiom in the OWL 2 Specification."""
    __slots__ = ()

    def __init__(self, property_: OWLDataPropertyExpression, range_: OWLDataRange,
                 annotations: Optional[Iterable[OWLAnnotation]] = None):
        super().__init__(property_=property_, range_=range_, annotations=annotations)
