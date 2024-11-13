"""OWL Base classes"""
from abc import abstractmethod, ABCMeta
from .meta_classes import HasIRI
from typing import TypeVar

_I = TypeVar('_I', bound='IRI')  # noqa: F821

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


class OWLNamedObject(OWLObject, HasIRI, metaclass=ABCMeta):
    """Represents a named object for example, class, property, ontology etc. - i.e. anything that has an
     IRI as its name."""
    __slots__ = ()

    _iri: _I

    def __eq__(self, other):
        if type(other) is type(self):
            return self._iri == other._iri
        else:
            return False
            # raise RuntimeError(f"Invalid equality checking:{self} cannot be compared with {other}")

    def __lt__(self, other):
        if type(other) is type(self):
            return self._iri.as_str() < other._iri.as_str()
        return NotImplemented

    def __hash__(self):
        return hash(self._iri)

    def __repr__(self):
        return f"{type(self).__name__}({repr(self._iri)})"


class OWLEntity(OWLNamedObject, metaclass=ABCMeta):
    """Represents Entities in the OWL 2 Specification."""
    __slots__ = ()

    def to_string_id(self) -> str:
        return self.str

    def is_anonymous(self) -> bool:
        return False

    pass
