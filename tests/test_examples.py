from owlapy.class_expression import OWLClass, OWLObjectIntersectionOf
from owlapy.owl_property import OWLObjectProperty
from owlapy.class_expression import OWLObjectSomeValuesFrom
from owlapy.converter import owl_expression_to_sparql
from owlapy.render import owl_expression_to_dl

class TestRunningExamples:
    def test_readme(self):
        # Create the male class
        male = OWLClass("http://example.com/society#male")

        # Create an object property using the iri as a string for 'hasChild' property.
        hasChild = OWLObjectProperty("http://example.com/society#hasChild")

        # Create an existential restrictions
        males_with_children = OWLObjectSomeValuesFrom(hasChild, male)

        # Let's make it more complex by intersecting with another class
        teacher = OWLClass("http://example.com/society#teacher")
        male_teachers_with_children = OWLObjectIntersectionOf([males_with_children, teacher])

        assert owl_expression_to_dl(male_teachers_with_children)=="(∃ hasChild.male) ⊓ teacher"
        assert owl_expression_to_sparql(male_teachers_with_children)=="""SELECT
 DISTINCT ?x WHERE { 
?x <http://example.com/society#hasChild> ?s_1 . 
?s_1 a <http://example.com/society#male> . 
?x a <http://example.com/society#teacher> . 
 }"""