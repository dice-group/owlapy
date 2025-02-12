from owlapy.owl_ontology import SyncOntology
from owlapy.util_owl_static_funcs import save_owl_class_expressions, csv_to_rdf_kg
from owlapy.class_expression import OWLClass, OWLObjectIntersectionOf, OWLObjectSomeValuesFrom
from owlapy.owl_property import OWLObjectProperty
from sklearn.datasets import load_iris
import pandas as pd
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

    def test_csv_to_kg(self):
        data = load_iris()
        df = pd.DataFrame(data.data, columns=data.feature_names)
        df['target'] = data.target
        df.to_csv("iris_dataset.csv", index=False)
        assert len(df) == 150
        path_kg = "iris_kg.owl"
        csv_to_rdf_kg(path_csv="iris_dataset.csv", path_kg=path_kg, namespace="http://example.com/society")
        onto = SyncOntology(path_kg)
        assert len(onto.get_abox_axioms()) == 750
