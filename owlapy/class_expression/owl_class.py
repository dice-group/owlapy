from .class_expression import OWLClassExpression, OWLObjectComplementOf
from ..owlobject import OWLObject, OWLEntity
from typing import Final, Union
from ..iri import IRI


class OWLClass(OWLClassExpression, OWLEntity):
    """An OWL 2 named Class"""
    __slots__ = '_iri', '_is_nothing', '_is_thing'
    type_index: Final = 1001

    _iri: 'IRI'
    _is_nothing: bool
    _is_thing: bool

    def __init__(self, iri: Union[IRI, str]):
        """Gets an instance of OWLClass that has the specified IRI.

        Args:
            iri:
        """
        if isinstance(iri, IRI):
            self._iri = iri
        else:
            self._iri = IRI.create(iri)

        self._is_nothing = self._iri.is_nothing()
        self._is_thing = self._iri.is_thing()

    def get_iri(self) -> 'IRI':
        # documented in parent
        return self._iri

    def is_owl_thing(self) -> bool:
        # documented in parent
        return self._is_thing

    def is_owl_nothing(self) -> bool:
        # documented in parent
        return self._is_nothing

    def get_object_complement_of(self) -> OWLObjectComplementOf:
        # documented in parent
        return OWLObjectComplementOf(self)

    def get_nnf(self) -> 'OWLClass':
        # documented in parent
        return self

    @property
    def str(self):
        return self.get_iri().as_str()

    @property
    def reminder(self) -> str:
        """The reminder of the IRI """
        return self.get_iri().get_remainder()
