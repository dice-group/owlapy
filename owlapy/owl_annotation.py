"""OWL Annotations"""
from abc import ABCMeta
from .owl_object import OWLObject


class OWLAnnotationObject(OWLObject, metaclass=ABCMeta):
    """A marker interface for the values (objects) of annotations."""
    __slots__ = ()

    # noinspection PyMethodMayBeStatic
    def as_iri(self):
        """
        Returns:
            if the value is an IRI, return it. Return None otherwise.
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
    def as_literal(self):
        """
        Returns:
            if the value is a literal, returns it. Return None otherwise
        """
        return None