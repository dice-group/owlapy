"""OWL IRI"""
import weakref
from abc import ABCMeta
from typing import Final, Union, overload
from weakref import WeakKeyDictionary

from owlapy import namespaces
from .owl_annotation import OWLAnnotationSubject, OWLAnnotationValue
from owlapy.namespaces import Namespaces


class _WeakCached(type):
    __slots__ = ()

    def __init__(cls, what, bases, dct):
        super().__init__(what, bases, dct)
        cls._cache = WeakKeyDictionary()

    def __call__(cls, *args, **kwargs):
        _temp = super().__call__(*args, **kwargs)
        ret = cls._cache.get(_temp)
        if ret is None:
            cls._cache[_temp] = weakref.ref(_temp)
            return _temp
        else:
            return ret()


class _meta_IRI(ABCMeta, _WeakCached):
    __slots__ = ()
    pass


class IRI(OWLAnnotationSubject, OWLAnnotationValue, metaclass=_meta_IRI):
    """An IRI, consisting of a namespace and a remainder."""
    __slots__ = '_namespace', '_remainder', '__weakref__'
    type_index: Final = 0

    _namespace: str
    _remainder: str

    def __init__(self, namespace: Union[str, Namespaces], remainder: str):
        if isinstance(namespace, Namespaces):
            namespace = namespace.ns
        else:
            assert namespace[-1] in ("/", ":", "#")
        import sys
        self._namespace = sys.intern(namespace)
        self._remainder = remainder

    @overload
    @staticmethod
    def create(namespace: Namespaces, remainder: str) -> 'IRI':
        ...

    @overload
    @staticmethod
    def create(namespace: str, remainder: str) -> 'IRI':
        """Creates an IRI by concatenating two strings. The full IRI is an IRI that contains the characters in
        namespace + remainder.

        Args:
            namespace: The first string.
            remainder: The second string.

        Returns:
            An IRI whose characters consist of prefix + suffix.
        """
        ...

    @overload
    @staticmethod
    def create(string: str) -> 'IRI':
        """Creates an IRI from the specified String.

        Args:
            string: The String that specifies the IRI.

        Returns:
            The IRI that has the specified string representation.
        """
        ...

    @staticmethod
    def create(string, remainder=None) -> 'IRI':
        if remainder is not None:
            return IRI(string, remainder)
        index = 1 + max(string.rfind("/"), string.rfind(":"), string.rfind("#"))
        return IRI(string[0:index], string[index:])

    def __repr__(self):
        return f"IRI({repr(self._namespace)},{repr(self._remainder)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._namespace is other._namespace and self._remainder == other._remainder
        return NotImplemented

    def __hash__(self):
        return hash((self._namespace, self._remainder))

    def is_nothing(self):
        """Determines if this IRI is equal to the IRI that owl:Nothing is named with.

        Returns:
            :True if this IRI is equal to <http://www.w3.org/2002/07/owl#Nothing> and otherwise False.
        """
        from owlapy.vocab import OWLRDFVocabulary
        return self == OWLRDFVocabulary.OWL_NOTHING.iri

    def is_thing(self):
        """Determines if this IRI is equal to the IRI that owl:Thing is named with.

        Returns:
            :True if this IRI is equal to <http://www.w3.org/2002/07/owl#Thing> and otherwise False.
        """
        from owlapy.vocab import OWLRDFVocabulary
        return self == OWLRDFVocabulary.OWL_THING.iri

    def is_reserved_vocabulary(self) -> bool:
        """Determines if this IRI is in the reserved vocabulary. An IRI is in the reserved vocabulary if it starts with
        <http://www.w3.org/1999/02/22-rdf-syntax-ns#> or <http://www.w3.org/2000/01/rdf-schema#> or
        <http://www.w3.org/2001/XMLSchema#> or <http://www.w3.org/2002/07/owl#>.

        Returns:
            True if the IRI is in the reserved vocabulary, otherwise False.
        """
        return (self._namespace == namespaces.OWL or self._namespace == namespaces.RDF
                or self._namespace == namespaces.RDFS or self._namespace == namespaces.XSD)

    def as_iri(self) -> 'IRI':
        # documented in parent
        return self

    def as_str(self) -> str:
        """
        CD: Should be deprecated.
        Returns:
            The string that specifies the IRI.
        """
        return self._namespace + self._remainder

    @property
    def str(self) -> str:
        """

        Returns:
            The string that specifies the IRI.
        """
        return self.as_str()

    @property
    def reminder(self) -> str:
        """

        Returns:
            The string corresponding to the reminder of the IRI.
        """
        return self.reminder()

    def get_short_form(self) -> str:
        """Gets the short form.

        Returns:
            A string that represents the short form.
        """
        return self._remainder

    def get_namespace(self) -> str:
        """
        Returns:
            The namespace as string.
        """
        return self._namespace

    def get_remainder(self) -> str:
        """
        Returns:
            The remainder (coincident with NCName usually) for this IRI.
        """
        return self._remainder
