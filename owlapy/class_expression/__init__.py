from .class_expression import OWLClassExpression, OWLAnonymousClassExpression, OWLBooleanClassExpression, OWLObjectComplementOf
from .owl_class import OWLClass
from .nary_boolean_expression import OWLNaryBooleanClassExpression, OWLObjectUnionOf, OWLObjectIntersectionOf

from typing import Final
from ..vocab import OWLRDFVocabulary

OWLThing: Final = OWLClass(OWLRDFVocabulary.OWL_THING.get_iri())  #: : :The OWL Class corresponding to owl:Thing
OWLNothing: Final = OWLClass(OWLRDFVocabulary.OWL_NOTHING.get_iri())  #: : :The OWL Class corresponding to owl:Nothing
