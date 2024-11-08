from owlapy.util_owl_static_funcs import save_owl_class_expressions
from owlapy.class_expression import OWLClass, OWLObjectIntersectionOf, OWLObjectSomeValuesFrom
from owlapy.owl_property import OWLObjectProperty
from owlapy import owl_expression_to_sparql, owl_expression_to_dl
from owlapy.owl_ontology_manager import OntologyManager
from owlapy.owl_axiom import OWLDeclarationAxiom, OWLClassAssertionAxiom
from owlapy.owl_individual import OWLNamedIndividual, IRI
import rdflib

class TestRunningExamples:
    def test_readme(self):
        # Using owl classes to create a complex class expression
        male = OWLClass("http://example.com/society#male")
        hasChild = OWLObjectProperty("http://example.com/society#hasChild")
        hasChild_male = OWLObjectSomeValuesFrom(hasChild, male)
        teacher = OWLClass("http://example.com/society#teacher")
        teacher_that_hasChild_male = OWLObjectIntersectionOf([hasChild_male, teacher])

        expressions= [male, teacher_that_hasChild_male]
        save_owl_class_expressions(expressions=expressions,
                                   namespace="https://ontolearn.org/predictions#",
                                   path="owl_class_expressions.owl",
                                   rdf_format= 'rdfxml')
        g=rdflib.Graph().parse("owl_class_expressions.owl")
        assert len(g)==22