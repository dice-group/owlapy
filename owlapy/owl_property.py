"""OWL Properties"""
from .owl_object import OWLObject, OWLEntity
from abc import ABCMeta, abstractmethod
from typing import Final, Union
from .iri import IRI


class OWLPropertyExpression(OWLObject, metaclass=ABCMeta):
    """Represents a property or possibly the inverse of a property."""
    __slots__ = ()

    def is_data_property_expression(self) -> bool:
        """
        Returns:
            True if this is a data property.
        """
        return False

    def is_object_property_expression(self) -> bool:
        """
        Returns:
            True if this is an object property.
        """
        return False

    def is_owl_top_object_property(self) -> bool:
        """Determines if this is the owl:topObjectProperty.

        Returns:
            True if this property is the owl:topObjectProperty.
        """
        return False

    def is_owl_top_data_property(self) -> bool:
        """Determines if this is the owl:topDataProperty.

        Returns:
            True if this property is the owl:topDataProperty.
        """
        return False


class OWLObjectPropertyExpression(OWLPropertyExpression):
    """A high level interface to describe different types of object properties."""
    __slots__ = ()

    @abstractmethod
    def get_inverse_property(self) -> 'OWLObjectPropertyExpression':
        """Obtains the property that corresponds to the inverse of this property.

        Returns:
            The inverse of this property. Note that this property will not necessarily be in the simplest form.
        """
        pass

    @abstractmethod
    def get_named_property(self) -> 'OWLObjectProperty':
        """Get the named object property used in this property expression.

        Returns:
            P if this expression is either inv(P) or P.
        """
        pass

    def is_object_property_expression(self) -> bool:
        # documented in parent
        return True


class OWLDataPropertyExpression(OWLPropertyExpression, metaclass=ABCMeta):
    """A high level interface to describe different types of data properties."""
    __slots__ = ()

    def is_data_property_expression(self):
        # documented in parent
        return True


class OWLProperty(OWLPropertyExpression, OWLEntity):
    """A base class for properties that aren't expression i.e. named properties. By definition, properties
    are either data properties or object properties."""
    __slots__ = '_iri'

    _iri: IRI

    def __init__(self, iri: Union['IRI', str]):
        """Gets an instance of OWLObjectProperty that has the specified IRI.

        Args:
            iri: The IRI.
        """
        if isinstance(iri, IRI):
            self._iri = iri
        else:
            self._iri = IRI.create(iri)

    @property
    def str(self) -> str:
        return self._iri.as_str()

    @property
    def iri(self) -> IRI:
        return self._iri


class OWLObjectProperty(OWLObjectPropertyExpression, OWLProperty):
    """Represents an Object Property in the OWL 2 Specification. Object properties connect pairs of individuals.

    (https://www.w3.org/TR/owl2-syntax/#Object_Properties)
    """
    __slots__ = '_iri'
    type_index: Final = 1002

    _iri: IRI

    @property
    def remainder(self):
        return self._iri.remainder

    def get_named_property(self) -> 'OWLObjectProperty':
        # documented in parent
        return self

    def get_inverse_property(self) -> 'OWLObjectInverseOf':
        # documented in parent
        return OWLObjectInverseOf(self)

    def is_owl_top_object_property(self) -> bool:
        # documented in parent
        return self.str == "http://www.w3.org/2002/07/owl#topObjectProperty"

    def __eq__(self, other):
        if isinstance(other, OWLObjectProperty):
            return self.iri.str == other.iri.str

    def __hash__(self):
        return hash(self.iri)


class OWLObjectInverseOf(OWLObjectPropertyExpression):
    """Represents the inverse of a property expression (ObjectInverseOf). An inverse object property expression
    ObjectInverseOf( P ) connects an individual I1 with I2 if and only if the object property P connects I2 with I1.
    This can be used to refer to the inverse of a property, without actually naming the property.
    For example, consider the property hasPart, the inverse
    property of hasPart (isPartOf) can be referred to using this interface inverseOf(hasPart), which can be used in
    restrictions e.g. inverseOf(hasPart) some Car refers to the set of things that are part of at least one car.

    (https://www.w3.org/TR/owl2-syntax/#Inverse_Object_Properties)
    """
    __slots__ = '_inverse_property'
    type_index: Final = 1003

    _inverse_property: OWLObjectProperty

    def __init__(self, property: OWLObjectProperty):
        """Gets the inverse of an object property.

        Args:
            property: The property of which the inverse will be returned.
        """
        self._inverse_property = property

    def get_inverse(self) -> OWLObjectProperty:
        """Gets the property expression that this is the inverse of.

        Returns:
            The object property expression such that this object property expression is an inverse of it.
        """
        return self._inverse_property

    def get_inverse_property(self) -> OWLObjectProperty:
        # documented in parent
        return self.get_inverse()

    def get_named_property(self) -> OWLObjectProperty:
        # documented in parent
        return self._inverse_property

    def __repr__(self):
        return f"OWLObjectInverseOf({repr(self._inverse_property)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._inverse_property == other._inverse_property
        return NotImplemented

    def __hash__(self):
        return hash(self._inverse_property)


class OWLDataProperty(OWLDataPropertyExpression, OWLProperty):
    """Represents a Data Property in the OWL 2 Specification. Data properties connect individuals with literals.
    In some knowledge representation systems, functional data properties are called attributes.

    (https://www.w3.org/TR/owl2-syntax/#Data_Properties)
    """
    __slots__ = '_iri'
    type_index: Final = 1004

    _iri: IRI

    def is_owl_top_data_property(self) -> bool:
        # documented in parent
        return self.str == "http://www.w3.org/2002/07/owl#topDataProperty"
