from abc import ABCMeta, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from owlapy.model._iri import IRI
    from owlapy.model import OWLLiteral


class OWLObject(metaclass=ABCMeta):
    """Base interface for OWL objects"""
    __slots__ = ()

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def __hash__(self):
        pass

    @abstractmethod
    def __repr__(self):
        pass

    # default
    def is_anonymous(self) -> bool:
        return True


class OWLAnnotationObject(OWLObject, metaclass=ABCMeta):
    """A marker interface for the values (objects) of annotations."""
    __slots__ = ()

    # noinspection PyMethodMayBeStatic
    def as_iri(self) -> Optional['IRI']:
        """
        Returns:
            if the value is an IRI, return it. Return Mone otherwise.
        """
        return None

    # noinspection PyMethodMayBeStatic
    def as_anonymous_individual(self):
        """
        Returns:
            if the value is an anonymous, return it. Return None otherwise.
        """
        return None


class OWLAnnotationSubject(OWLAnnotationObject, metaclass=ABCMeta):
    """A marker interface for annotation subjects, which can either be IRIs or anonymous individuals"""
    __slots__ = ()
    pass


class OWLAnnotationValue(OWLAnnotationObject, metaclass=ABCMeta):
    """A marker interface for annotation values, which can either be an IRI (URI), Literal or Anonymous Individual."""
    __slots__ = ()

    def is_literal(self) -> bool:
        """
        Returns:
            true if the annotation value is a literal
        """
        return False

    # noinspection PyMethodMayBeStatic
    def as_literal(self) -> Optional['OWLLiteral']:
        """
        Returns:
            if the value is a literal, returns it. Return None otherwise
        """
        return None
