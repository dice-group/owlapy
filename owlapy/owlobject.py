from abc import abstractmethod, ABCMeta
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
