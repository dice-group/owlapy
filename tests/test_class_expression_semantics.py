from owlapy.iri import IRI

from owlapy.class_expression import OWLClass, OWLObjectComplementOf, OWLObjectUnionOf
from owlapy.class_expression import OWLBooleanClassExpression, OWLObjectIntersectionOf, OWLClassExpression
from owlapy.owl_property import OWLObjectProperty
from owlapy.class_expression import OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom

from owlapy.owl2sparql.converter import owl_expression_to_sparql
from owlapy.render import owl_expression_to_dl


class TestClassExpression:
    def test_iri(self):
        # Create the male class
        C = OWLClass("http://example.com/society#C")
        assert isinstance(C, OWLClassExpression)
        Not_C=OWLObjectComplementOf(C)
        assert isinstance(Not_C, OWLClassExpression)
        C_AND_C=OWLObjectIntersectionOf([C, C])
        assert isinstance(C_AND_C, OWLClassExpression)
        C_OR_C = OWLObjectUnionOf([C, C])
        assert isinstance(C_OR_C, OWLClassExpression)

        hasChild = OWLObjectProperty("http://example.com/society#hasChild")
        assert isinstance(OWLObjectSomeValuesFrom(hasChild, C), OWLClassExpression)

        assert isinstance(OWLObjectAllValuesFrom(hasChild, C), OWLClassExpression)
