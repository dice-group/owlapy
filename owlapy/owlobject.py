from abc import abstractmethod, ABCMeta
from typing import Optional
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



class OWLObjectRenderer(metaclass=ABCMeta):
    """Abstract class with a render method to render an OWL Object into a string."""
    @abstractmethod
    def set_short_form_provider(self, short_form_provider) -> None:
        """Configure a short form provider that shortens the OWL objects during rendering.

        Args:
            short_form_provider: Short form provider.
        """
        pass

    @abstractmethod
    def render(self, o: OWLObject) -> str:
        """Render OWL Object to string.

        Args:
            o: OWL Object.

        Returns:
            String rendition of OWL object.
        """
        pass


class OWLObjectParser(metaclass=ABCMeta):
    """Abstract class with a parse method to parse a string to an OWL Object."""
    @abstractmethod
    def parse_expression(self, expression_str: str) -> OWLObject:
        """Parse a string to an OWL Object.

        Args:
            expression_str (str): Expression string.

        Returns:
            The OWL Object which is represented by the string.
        """
        pass

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
