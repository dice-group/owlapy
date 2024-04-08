from abc import ABCMeta, abstractmethod

from typing import TypeVar, List, Optional, Iterable, Generic
from .owl_property import OWLDataPropertyExpression, OWLObjectPropertyExpression
from .owlobject import OWLObject, OWLEntity
from .types import OWLDatatype, OWLDataRange
from .has import HasOperands
from .owl_property import OWLPropertyExpression
from .owl_class_expression import OWLClassExpression, OWLClass
from .owl_individual import OWLIndividual

_C = TypeVar('_C', bound='OWLObject')  #:
_P = TypeVar('_P', bound='OWLPropertyExpression')  #:


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


class OWLAnnotationAxiom(OWLAxiom, metaclass=ABCMeta):
    """A super interface for annotation axioms."""
    __slots__ = ()

    def is_annotation_axiom(self) -> bool:
        return True
