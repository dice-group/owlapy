from abc import ABCMeta
from .owlobject import OWLObject
# @TODO: metaclass=ABCMeta inheritance may not be required since OWLObject is defined as such
class OWLPropertyRange(OWLObject, metaclass=ABCMeta):
    """OWL Objects that can be the ranges of properties."""


class OWLDataRange(OWLPropertyRange, metaclass=ABCMeta):
    """Represents a DataRange in the OWL 2 Specification."""
