"""OWL Class"""
from .class_expression import OWLClassExpression, OWLObjectComplementOf
from ..owl_object import OWLEntity
from typing import Final, Union
from ..iri import IRI


class OWLClass(OWLClassExpression, OWLEntity):
    """An OWL 2 named Class. Classes can be understood as sets of individuals.
    (https://www.w3.org/TR/owl2-syntax/#Classes)"""
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

    @property
    def iri(self) -> 'IRI':
        # documented in parent
        return self._iri

    @property
    def str(self):
        return self._iri.as_str()

    @property
    def remainder(self) -> str:
        """The remainder of the IRI """
        return self._iri.get_remainder()

    def is_owl_thing(self) -> bool:
        # documented in parent
        return self._is_thing

    def is_owl_nothing(self) -> bool:
        # documented in parent
        return self._is_nothing

    def get_object_complement_of(self) -> OWLObjectComplementOf:
        # TODO: CD: get_object_complement_of is not correct term.
        # TODO: CD : we might want to use get_complement_of instead

        # documented in parent
        return OWLObjectComplementOf(self)

    def get_nnf(self) -> 'OWLClass':
        # documented in parent
        return self


