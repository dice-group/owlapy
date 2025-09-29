"""OWL IRI"""
import weakref
from abc import ABCMeta
from typing import Final, Union
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

    def __init__(self, namespace: Union[str, Namespaces], remainder: str="", is_file_path=False):
        if isinstance(namespace, Namespaces):
            namespace = namespace.ns
        elif not is_file_path:
            assert namespace[-1] in ("/", ":", "#"), ("It should be a valid IRI based on /, :, and #. "
                                                      "Are you saving a file? - then set is_file_path=True "
                                                      "to overcome this assertion.")
        import sys
        # https://docs.python.org/3.2/library/sys.html?highlight=sys.intern#sys.intern
        self._namespace = sys.intern(namespace)
        self._remainder = remainder

    @staticmethod
    def create(iri:str | Namespaces, remainder:str=None, is_file_path=False) -> 'IRI':
        assert isinstance(iri, str) | isinstance(iri, Namespaces), f"Input must be a string or an instance of Namespaces. Currently, {type(iri)}"
        if is_file_path and iri != "":
            return IRI(iri, "", is_file_path)
        elif remainder is not None:
            assert isinstance(remainder,str), f"Remainder must be string. Currently, {type(remainder)}"
            return IRI(iri, remainder)
        else:
            assert isinstance(iri, str) and remainder is None, \
                f"iri must be string if remainder is None. Currently, {type(iri)} and {type(remainder)}"
            # Extract remainder from input string
            assert "/" in iri, (f"Input must contain /\tCurrently, {iri}. Are you saving a file? - then "
                                f"set is_file_path=True to overcome this assertion.")
            # assert ":" in iri, "Input must contain :"
            assert " " not in iri, f"Input must not contain whitespace. Currently:{iri}."
            index = 1 + max(iri.rfind("/"), iri.rfind(":"), iri.rfind("#"))
            return IRI(iri[0:index], iri[index:])

    def __repr__(self):
        return f"IRI({repr(self._namespace)}, {repr(self._remainder)})"

    def __eq__(self, other):
        if type(other) is type(self):
            return self._namespace is other._namespace and self._remainder == other._remainder
        else:
            raise RuntimeError(f"Invalid equality checking:{self} cannot be compared with {other}")

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
    def remainder(self) -> str:
        """

        Returns:
            The string corresponding to the remainder of the IRI.
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
