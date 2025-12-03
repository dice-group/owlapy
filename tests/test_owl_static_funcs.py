from sklearn.datasets import load_iris
import rdflib
import unittest
import os
import json
import tempfile
import pandas as pd
from owlapy.util_owl_static_funcs import (
    save_owl_class_expressions, csv_to_rdf_kg, rdf_kg_to_csv,
    create_ontology, generate_ontology, make_kb_incomplete,
    make_kb_incomplete_ass
)
from owlapy.class_expression import (
    OWLClass, OWLObjectIntersectionOf, OWLObjectUnionOf,
    OWLObjectSomeValuesFrom
)
from owlapy.owl_property import OWLObjectProperty
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import SyncOntology, Ontology
from owlapy.iri import IRI


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

class TestSaveOwlClassExpressions(unittest.TestCase):
    """Test save_owl_class_expressions function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_files = []

    def tearDown(self):
        """Clean up test files."""
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_save_single_expression(self):
        """Test saving a single OWL class expression."""
        ns = "http://example.com/test#"
        person = OWLClass(IRI.create(ns, "Person"))

        path = "test_single_expr.owl"
        self.test_files.append(path)

        save_owl_class_expressions(person, path=path, namespace=ns)

        self.assertTrue(os.path.exists(path))

    def test_save_multiple_expressions(self):
        """Test saving multiple OWL class expressions."""
        ns = "http://example.com/test#"
        person = OWLClass(IRI.create(ns, "Person"))
        male = OWLClass(IRI.create(ns, "Male"))
        has_child = OWLObjectProperty(IRI.create(ns, "hasChild"))

        father = OWLObjectIntersectionOf([
            male,
            OWLObjectSomeValuesFrom(has_child, person)
        ])

        path = "test_multiple_expr.owl"
        self.test_files.append(path)

        expressions = [person, male, father]
        save_owl_class_expressions(expressions, path=path, namespace=ns)

        self.assertTrue(os.path.exists(path))

    def test_save_with_custom_namespace(self):
        """Test saving with custom namespace."""
        ns = "http://custom.org/onto#"
        person = OWLClass(IRI.create(ns, "Person"))

        path = "test_custom_ns.owl"
        self.test_files.append(path)

        save_owl_class_expressions(person, path=path, namespace=ns)

        self.assertTrue(os.path.exists(path))

    def test_save_complex_expression(self):
        """Test saving complex class expressions."""
        ns = "http://example.com/test#"
        male = OWLClass(IRI.create(ns, "Male"))
        female = OWLClass(IRI.create(ns, "Female"))
        has_child = OWLObjectProperty(IRI.create(ns, "hasChild"))

        # Male ⊔ (∃hasChild.Female)
        complex_expr = OWLObjectUnionOf([
            male,
            OWLObjectSomeValuesFrom(has_child, female)
        ])

        path = "test_complex_expr.owl"
        self.test_files.append(path)

        save_owl_class_expressions(complex_expr, path=path, namespace=ns)

        self.assertTrue(os.path.exists(path))


class TestCsvToRdfKg(unittest.TestCase):
    """Test csv_to_rdf_kg function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_files = []

    def tearDown(self):
        """Clean up test files."""
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_csv_to_kg_basic(self):
        """Test basic CSV to RDF KG conversion."""
        # Create test CSV
        csv_path = "test_basic.csv"
        kg_path = "test_basic_kg.owl"
        self.test_files.extend([csv_path, kg_path])

        df = pd.DataFrame({
            'name': ['Alice', 'Bob'],
            'age': [30, 25],
            'city': ['NYC', 'LA']
        })
        df.to_csv(csv_path, index=False)

        csv_to_rdf_kg(
            path_csv=csv_path,
            path_kg=kg_path,
            namespace="http://example.com/test"
        )

        self.assertTrue(os.path.exists(kg_path))

        # Verify the ontology
        onto = SyncOntology(kg_path)
        axioms = list(onto.get_abox_axioms())
        self.assertGreater(len(axioms), 0)

    def test_csv_with_numeric_data(self):
        """Test CSV with numeric data."""
        csv_path = "test_numeric.csv"
        kg_path = "test_numeric_kg.owl"
        self.test_files.extend([csv_path, kg_path])

        df = pd.DataFrame({
            'value': [1.5, 2.7, 3.9],
            'count': [10, 20, 30]
        })
        df.to_csv(csv_path, index=False)

        csv_to_rdf_kg(
            path_csv=csv_path,
            path_kg=kg_path,
            namespace="http://example.com/numeric"
        )

        self.assertTrue(os.path.exists(kg_path))

    def test_csv_with_special_characters(self):
        """Test CSV with special characters in column names."""
        csv_path = "test_special.csv"
        kg_path = "test_special_kg.owl"
        self.test_files.extend([csv_path, kg_path])

        df = pd.DataFrame({
            'size (cm)': [10, 20],
            'weight': [5, 10]
        })
        df.to_csv(csv_path, index=False)

        csv_to_rdf_kg(
            path_csv=csv_path,
            path_kg=kg_path,
            namespace="http://example.com/special"
        )

        self.assertTrue(os.path.exists(kg_path))


class TestRdfKgToCsv(unittest.TestCase):
    """Test rdf_kg_to_csv function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_files = []

    def tearDown(self):
        """Clean up test files."""
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_rdf_kg_to_csv_basic(self):
        """Test basic RDF KG to CSV conversion."""
        csv_path = "test_orig.csv"
        kg_path = "test_kg.owl"
        reconstructed_path = "test_reconstructed.csv"
        self.test_files.extend([csv_path, kg_path, reconstructed_path])

        # Create original CSV
        df = pd.DataFrame({
            'name': ['Alice', 'Bob'],
            'age': [30, 25]
        })
        df.to_csv(csv_path, index=False)

        # Convert to KG
        csv_to_rdf_kg(
            path_csv=csv_path,
            path_kg=kg_path,
            namespace="http://example.com/test"
        )

        # Convert back to CSV
        rdf_kg_to_csv(path_kg=kg_path, path_csv=reconstructed_path)

        self.assertTrue(os.path.exists(reconstructed_path))

        # Verify data
        reconstructed_df = pd.read_csv(reconstructed_path)
        self.assertGreater(len(reconstructed_df), 0)


class TestCreateOntology(unittest.TestCase):
    """Test create_ontology function."""

    def test_create_ontology_default(self):
        """Test creating ontology with default settings."""
        iri = "http://example.com/test"
        onto = create_ontology(iri, with_owlapi=False)

        self.assertIsInstance(onto, Ontology)

    def test_create_ontology_with_owlapi(self):
        """Test creating ontology with OWLAPI."""
        iri = "http://example.com/test"
        onto = create_ontology(iri, with_owlapi=True)

        self.assertIsInstance(onto, SyncOntology)


class TestGenerateOntology(unittest.TestCase):
    """Test generate_ontology function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_files = []

    def tearDown(self):
        """Clean up test files."""
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_generate_ontology_without_classes(self):
        """Test generating ontology without class generation."""
        # Create test JSON data
        json_path = "test_graph.json"
        output_path = "test_generated.owl"
        self.test_files.extend([json_path, output_path])

        graph_data = {
            "graphs": [
                {
                    "quadruples": [
                        {
                            "subject": "Alice",
                            "predicate": "knows",
                            "object": "Bob"
                        },
                        {
                            "subject": "Alice",
                            "predicate": "age",
                            "object": "30"
                        }
                    ]
                }
            ]
        }

        with open(json_path, 'w') as f:
            json.dump(graph_data, f)

        generate_ontology(
            graph_as_json=json_path,
            output_path=output_path,
            output_format="xml",
            namespace="http://example.com/test/",
            generate_classes=False
        )

        self.assertTrue(os.path.exists(output_path))

    def test_generate_ontology_different_formats(self):
        """Test generating ontology in different formats."""
        json_path = "test_graph2.json"
        self.test_files.append(json_path)

        graph_data = {
            "graphs": [
                {
                    "quadruples": [
                        {
                            "subject": "Entity1",
                            "predicate": "relatesTo",
                            "object": "Entity2"
                        }
                    ]
                }
            ]
        }

        with open(json_path, 'w') as f:
            json.dump(graph_data, f)

        for fmt in ["xml", "turtle", "n3"]:
            output_path = f"test_generated_{fmt}.owl"
            self.test_files.append(output_path)

            generate_ontology(
                graph_as_json=json_path,
                output_path=output_path,
                output_format=fmt,
                namespace="http://example.com/test/",
                generate_classes=False
            )

            self.assertTrue(os.path.exists(output_path))

    def test_generate_ontology_with_numeric_objects(self):
        """Test generating ontology with numeric objects."""
        json_path = "test_numeric_graph.json"
        output_path = "test_numeric_generated.owl"
        self.test_files.extend([json_path, output_path])

        graph_data = {
            "graphs": [
                {
                    "quadruples": [
                        {
                            "subject": "Item1",
                            "predicate": "hasIntValue",
                            "object": "42"
                        },
                        {
                            "subject": "Item1",
                            "predicate": "hasFloatValue",
                            "object": "3.14"
                        },
                        {
                            "subject": "Item1",
                            "predicate": "hasStringValue",
                            "object": "hello"
                        }
                    ]
                }
            ]
        }

        with open(json_path, 'w') as f:
            json.dump(graph_data, f)

        generate_ontology(
            graph_as_json=json_path,
            output_path=output_path,
            output_format="xml",
            namespace="http://example.com/test/",
            generate_classes=False
        )

        self.assertTrue(os.path.exists(output_path))


class TestMakeKbIncomplete(unittest.TestCase):
    """Test make_kb_incomplete and make_kb_incomplete_ass functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_files = []
        # Create a test ontology
        self.kb_path = "test_kb.owl"
        self.test_files.append(self.kb_path)

        ns = "http://example.com/test#"
        onto = SyncOntology(ns, load=False)

        # Add some individuals and axioms
        from owlapy.owl_axiom import OWLClassAssertionAxiom, OWLObjectPropertyAssertionAxiom

        person_class = OWLClass(IRI.create(ns, "Person"))
        alice = OWLNamedIndividual(IRI.create(ns, "Alice"))
        bob = OWLNamedIndividual(IRI.create(ns, "Bob"))
        knows = OWLObjectProperty(IRI.create(ns, "knows"))

        onto.add_axiom(OWLClassAssertionAxiom(alice, person_class))
        onto.add_axiom(OWLClassAssertionAxiom(bob, person_class))
        onto.add_axiom(OWLObjectPropertyAssertionAxiom(alice, knows, bob))

        onto.save(path=self.kb_path)

    def tearDown(self):
        """Clean up test files."""
        for file_path in self.test_files:
            if os.path.exists(file_path):
                os.remove(file_path)

    def test_make_kb_incomplete_basic(self):
        """Test making KB incomplete by removing individuals."""
        output_path = "test_incomplete_kb.owl"
        self.test_files.append(output_path)

        # Remove 50% of individuals
        make_kb_incomplete(
            kb_path=self.kb_path,
            output_path=output_path,
            rate=50,
            seed=42
        )

        self.assertTrue(os.path.exists(output_path))

    def test_make_kb_incomplete_zero_percent(self):
        """Test making KB incomplete with 0% removal."""
        output_path = "test_incomplete_zero.owl"
        self.test_files.append(output_path)

        make_kb_incomplete(
            kb_path=self.kb_path,
            output_path=output_path,
            rate=0,
            seed=42
        )

        self.assertTrue(os.path.exists(output_path))

    def test_make_kb_incomplete_ass_basic(self):
        """Test making KB incomplete by removing assertions."""
        output_path = "test_incomplete_ass.owl"
        self.test_files.append(output_path)

        # Remove 30% of assertions
        make_kb_incomplete_ass(
            kb_path=self.kb_path,
            output_path=output_path,
            rate=30,
            seed=42
        )

        self.assertTrue(os.path.exists(output_path))


class TestAssertions(unittest.TestCase):
    """Test assertion validations in functions."""

    def test_save_expressions_invalid_format(self):
        """Test save_owl_class_expressions with invalid format."""
        ns = "http://example.com/test#"
        person = OWLClass(IRI.create(ns, "Person"))

        with self.assertRaises(AssertionError):
            save_owl_class_expressions(
                person,
                path="test.owl",
                rdf_format="turtle",  # Only rdfxml is supported
                namespace=ns
            )

    def test_save_expressions_invalid_namespace(self):
        """Test save_owl_class_expressions with invalid namespace."""
        ns = "http://example.com/test"  # Missing #
        person = OWLClass(IRI.create(ns + "#", "Person"))

        with self.assertRaises(AssertionError):
            save_owl_class_expressions(
                person,
                path="test.owl",
                namespace=ns
            )

    def test_csv_to_kg_none_path(self):
        """Test csv_to_rdf_kg with None path."""
        with self.assertRaises(AssertionError):
            csv_to_rdf_kg(
                path_csv=None,
                path_kg="test.owl",
                namespace="http://example.com/test"
            )

    def test_csv_to_kg_invalid_path(self):
        """Test csv_to_rdf_kg with non-existent path."""
        with self.assertRaises(AssertionError):
            csv_to_rdf_kg(
                path_csv="nonexistent.csv",
                path_kg="test.owl",
                namespace="http://example.com/test"
            )

    def test_csv_to_kg_invalid_namespace(self):
        """Test csv_to_rdf_kg with invalid namespace."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("a,b\n1,2\n")
            temp_path = f.name

        try:
            with self.assertRaises(AssertionError):
                csv_to_rdf_kg(
                    path_csv=temp_path,
                    path_kg="test.owl",
                    namespace="ftp://invalid.com/test"  # Must start with http://
                )
        finally:
            os.remove(temp_path)

    def test_rdf_kg_to_csv_none_paths(self):
        """Test rdf_kg_to_csv with None paths."""
        with self.assertRaises(AssertionError):
            rdf_kg_to_csv(path_kg=None, path_csv="test.csv")

        with self.assertRaises(AssertionError):
            rdf_kg_to_csv(path_kg="test.owl", path_csv=None)

    def test_rdf_kg_to_csv_nonexistent_kg(self):
        """Test rdf_kg_to_csv with non-existent KG."""
        with self.assertRaises(AssertionError):
            rdf_kg_to_csv(
                path_kg="nonexistent.owl",
                path_csv="output.csv"
            )

    def test_generate_ontology_invalid_format(self):
        """Test generate_ontology with invalid output format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"graphs": [{"quadruples": []}]}, f)
            temp_path = f.name

        try:
            with self.assertRaises(AssertionError):
                generate_ontology(
                    graph_as_json=temp_path,
                    output_path="test.owl",
                    output_format="invalid_format",
                    namespace="http://example.com/test/",
                    generate_classes=False
                )
        finally:
            os.remove(temp_path)


if __name__ == '__main__':
    unittest.main()
