"""OWL Individuals"""
from abc import ABCMeta
from typing import ClassVar, Final, Optional, Union

from .iri import IRI
from .owl_annotation import OWLAnnotationSubject, OWLAnnotationValue
from .owl_object import OWLEntity, OWLObject


class OWLIndividual(OWLObject, metaclass=ABCMeta):
    """Represents a named or anonymous individual."""
    __slots__ = ()
    pass


class NodeID:
    """Generates and normalizes the node IDs used to identify :class:`OWLAnonymousIndividual` instances,
    loosely modeled after OWLAPI's ``org.semanticweb.owlapi.model.NodeID``.

    Node IDs are local to an ontology document: they let one distinguish different anonymous individuals
    without asserting any particular identity for them.
    """
    __slots__ = ()
    _counter: ClassVar[int] = 0

    @staticmethod
    def get_node_id(id_: Optional[str] = None) -> str:
        """Normalize a node id, generating a fresh, unused one if none is given.

        Args:
            id_: A string identifying an anonymous individual, optionally prefixed with "_:" (as blank node
                labels are written in Turtle/N-Triples). If None, a fresh node id is generated.

        Returns:
            The normalized node id string, without a "_:" prefix.
        """
        if id_ is None:
            NodeID._counter += 1
            return f"genid-{NodeID._counter}"
        return id_[2:] if id_.startswith("_:") else id_


class OWLNamedIndividual(OWLIndividual, OWLEntity):
    """Named individuals are identified using an IRI. Since they are given an IRI, named individuals are entities.
        IRIs from the reserved vocabulary must not be used to identify named individuals in an OWL 2 DL ontology.

        (https://www.w3.org/TR/owl2-syntax/#Named_Individuals)
        """
    __slots__ = '_iri'
    type_index: Final = 1005

    _iri: IRI

    def __init__(self, iri: Union[IRI, str]):
        """Gets an instance of OWLNamedIndividual that has the specified IRI.

        Args:
            iri: an instance of IRI Class or a string representing the iri

        Returns:
            An OWLNamedIndividual that has the specified IRI.
        """
        if isinstance(iri, IRI):
            self._iri = iri
        else:
            self._iri = IRI.create(iri)
    @property
    def iri(self) -> IRI:
        return self._iri
    @property
    def str(self):
        return self._iri.as_str()
    @property
    def remainder(self):
        return self._iri.remainder


class OWLAnonymousIndividual(OWLIndividual, OWLAnnotationSubject, OWLAnnotationValue):
    """Anonymous individuals are identified using a node ID rather than an IRI. Node IDs are local to an
    ontology document: they allow different anonymous individuals to be distinguished from one another
    without asserting any particular identity for them.

    (https://www.w3.org/TR/owl2-syntax/#Anonymous_Individuals)
    """
    __slots__ = '_node_id'
    type_index: Final = 1006

    _node_id: str

    def __init__(self, node_id: Optional[str] = None):
        """Gets an instance of OWLAnonymousIndividual identified by the given node id, generating a fresh,
        unused one if none is given.

        Args:
            node_id: A string identifying this anonymous individual, or None to generate a fresh one.

        Returns:
            An OWLAnonymousIndividual identified by the given (or a freshly generated) node id.
        """
        self._node_id = NodeID.get_node_id(node_id)

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def str(self) -> str:
        return self.to_string_id()

    def to_string_id(self) -> str:
        return f"_:{self._node_id}"

    def is_anonymous(self) -> bool:
        return True

    def as_anonymous_individual(self) -> 'OWLAnonymousIndividual':
        return self

    def __eq__(self, other):
        if type(other) is type(self):
            return self._node_id == other._node_id
        return False

    def __hash__(self):
        return hash(("OWLAnonymousIndividual", self._node_id))

    def __repr__(self):
        return f"OWLAnonymousIndividual({self._node_id!r})"
