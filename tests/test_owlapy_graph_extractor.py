import unittest

from owlapy.agen_kg.graph_extracting_models.domain_graph_extractor import DomainGraphExtractor
from owlapy.agen_kg.helper import RDFS_LABEL_IRI, chunked_iterator
from owlapy.iri import IRI
from owlapy.owl_axiom import (
    OWLAnnotation,
    OWLAnnotationAssertionAxiom,
    OWLAnnotationProperty,
    OWLLiteral,
)


class TestGraphExtractor(unittest.TestCase):
    """Test annotation assertion axiom generation provided by the abstract GraphExtractor class"""

    def setUp(self):
        """Create test instance"""
        self.graph_extractor = DomainGraphExtractor()
        self.test_class_iri_str = "http://example.org/TestClass"
        self.test_annotation_iri_str = "http://example.org/testAnnotation"

    def test_get_annotation_assertion_axiom(self):
        """Test creation of generic annotation assertion axiom"""

        entity_iri = IRI.create(self.test_class_iri_str)
        annotation_iri = IRI.create(self.test_annotation_iri_str)
        value = "Test annotation"

        result = self.graph_extractor._get_annotation_assertion_axiom(entity_iri=entity_iri, annotation_iri=annotation_iri, value=value)

        expected = OWLAnnotationAssertionAxiom(entity_iri, OWLAnnotation(OWLAnnotationProperty(annotation_iri), OWLLiteral(value)))

        self.assertEqual(result, expected)

    def test_get_rdfs_label_axiom(self):
        """Test creation of rdfs:label annotation assertion axiom"""

        entity_iri = IRI.create(self.test_class_iri_str)
        label = "Test class"

        result = self.graph_extractor.get_rdfs_label_axiom(entity_iri=entity_iri, label=label)

        expected_annotation_iri = IRI.create(RDFS_LABEL_IRI)

        expected = OWLAnnotationAssertionAxiom(entity_iri, OWLAnnotation(OWLAnnotationProperty(expected_annotation_iri), OWLLiteral(label)))

        self.assertEqual(result, expected)

    def test_format_rdfs_label_uppercase_class_name(self):
        """Test formatting uppercase class label"""
        result = DomainGraphExtractor.format_rdfs_label("PERSON")
        self.assertEqual(result, "Person")

    def test_format_rdfs_label_snake_case_class_name(self):
        """Test formatting snake_case class label"""
        result = DomainGraphExtractor.format_rdfs_label("person_type")
        self.assertEqual(result, "Person type")

    def test_format_rdfs_label_space_separated_class_name(self):
        """Test formatting space separated class label"""
        result = DomainGraphExtractor.format_rdfs_label("PERSON TYPE")
        self.assertEqual(result, "Person type")

    def test_format_rdfs_label_property_name(self):
        """Test formatting property label"""
        result = DomainGraphExtractor.format_rdfs_label("has_name", is_property=True)
        self.assertEqual(result, "has name")

    def test_format_rdfs_label_property_uppercase(self):
        """Test formatting uppercase property label"""
        result = DomainGraphExtractor.format_rdfs_label("HAS_PARENT", is_property=True)
        self.assertEqual(result, "has parent")

    def test_format_rdfs_label_single_word_class(self):
        """Test formatting single word class label"""
        result = DomainGraphExtractor.format_rdfs_label("Vehicle")
        self.assertEqual(result, "Vehicle")

    def test_format_rdfs_label_single_word_property(self):
        """Test formatting single word property label"""
        result = DomainGraphExtractor.format_rdfs_label("CREATEDBY", is_property=True)
        self.assertEqual(result, "createdby")

    def test_format_rdfs_label_multiple_underscores(self):
        """Test formatting label with multiple underscores"""
        result = DomainGraphExtractor.format_rdfs_label("very_long_entity_name")
        self.assertEqual(result, "Very long entity name")

    def test_format_rdfs_label_empty_string(self):
        """Test formatting empty label"""
        result = DomainGraphExtractor.format_rdfs_label("")
        self.assertEqual(result, "")


class TestGraphExtractorHelpers(unittest.TestCase):
    """Test GraphExtractor helpers"""

    def test_chunked_iterator_exact_division(self):
        """Test chunking when sequence divides exactly into equal parts"""
        data = [1, 2, 3, 4]
        result = list(chunked_iterator(data, size=2))
        self.assertEqual(result, [[1, 2], [3, 4]])

    def test_chunked_iterator_non_exact_division(self):
        """Test chunking when sequence does not divide evenly"""
        data = [1, 2, 3, 4, 5]
        result = list(chunked_iterator(data, size=2))
        self.assertEqual(result, [[1, 2], [3, 4], [5]])

    def test_chunked_iterator_size_larger_than_input(self):
        """Test chunking when chunk size exceeds input length"""
        data = [1, 2, 3]
        result = list(chunked_iterator(data, size=10))
        self.assertEqual(result, [[1, 2, 3]])

    def test_chunked_iterator_single_element_chunks(self):
        """Test chunking when size is 1"""
        data = [1, 2, 3]
        result = list(chunked_iterator(data, size=1))
        self.assertEqual(result, [[1], [2], [3]])

    def test_chunked_iterator_empty_input(self):
        """Test chunking with an empty iterable"""
        data = []
        result = list(chunked_iterator(data, size=3))
        self.assertEqual(result, [])

    def test_chunked_iterator_works_with_iterable_not_list(self):
        """Test chunking with a generator input"""
        data = (x for x in range(5))
        result = list(chunked_iterator(data, size=2))
        self.assertEqual(result, [[0, 1], [2, 3], [4]])

    def test_chunked_iterator_does_not_eagerly_consume(self):
        """Test that iterator is consumed lazily"""
        data = iter([1, 2, 3, 4, 5])
        it = chunked_iterator(data, size=2)

        first = next(it)
        self.assertEqual(first, [1, 2])

        second = next(it)
        self.assertEqual(second, [3, 4])
