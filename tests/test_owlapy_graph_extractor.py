import unittest
from unittest.mock import MagicMock

from owlapy.agen_kg.graph_extracting_models.domain_graph_extractor import DomainGraphExtractor
from owlapy.agen_kg.helper import RDFS_COMMENT_IRI, RDFS_LABEL_IRI, chunked_iterator
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

    def test_snake_case_removes_special_chars_and_lowercases(self):
        self.assertEqual(DomainGraphExtractor.snake_case("Hello, World!"), "hello_world")

    def test_snake_case_collapses_multiple_spaces(self):
        self.assertEqual(DomainGraphExtractor.snake_case("Person   Type"), "person_type")

    def test_snake_case_already_lowercase_single_word(self):
        self.assertEqual(DomainGraphExtractor.snake_case("vehicle"), "vehicle")

    def test_plan_decompose_stores_task_instructions(self):
        results = MagicMock(
            entity_extraction_task="extract entities",
            triple_extraction_task="extract triples",
            type_generation_task="generate types",
            type_assertion_task="assert types",
            literal_extraction_task="extract literals",
            triple_with_literal_extraction_task="extract spl triples",
            fact_checking_task="check facts",
        )
        self.graph_extractor.plan_decomposer = MagicMock(return_value=results)

        self.graph_extractor.plan_decompose("Extract info about companies")

        self.graph_extractor.plan_decomposer.assert_called_once_with(user_request="Extract info about companies")
        self.assertEqual(self.graph_extractor.entity_extraction_instructions, "extract entities")
        self.assertEqual(self.graph_extractor.triple_extraction_instructions, "extract triples")
        self.assertEqual(self.graph_extractor.type_generation_instructions, "generate types")
        self.assertEqual(self.graph_extractor.type_assertion_instructions, "assert types")
        self.assertEqual(self.graph_extractor.literal_extraction_instructions, "extract literals")
        self.assertEqual(self.graph_extractor.triple_with_literal_extraction_instructions, "extract spl triples")
        self.assertEqual(self.graph_extractor.fact_checking_instructions, "check facts")

    def test_plan_decompose_defaults_query_when_none(self):
        results = MagicMock(
            entity_extraction_task="e", triple_extraction_task="t", type_generation_task="tg",
            type_assertion_task="ta", literal_extraction_task="l", triple_with_literal_extraction_task="spl",
            fact_checking_task="fc",
        )
        self.graph_extractor.plan_decomposer = MagicMock(return_value=results)

        self.graph_extractor.plan_decompose(None)

        _, call_kwargs = self.graph_extractor.plan_decomposer.call_args
        self.assertIn("Extract knowledge graph relevant information", call_kwargs["user_request"])


class TestGenerateBatchRdfsCommentAxioms(unittest.TestCase):
    def setUp(self):
        self.graph_extractor = DomainGraphExtractor()
        self.class_iri = IRI.create("http://example.org/TestClass")
        self.prop_iri = IRI.create("http://example.org/testProperty")

    def test_generates_axioms_for_valid_entities(self):
        self.graph_extractor.batch_rdfs_comment_generator = MagicMock(return_value=MagicMock(
            entity_comment_pairs=[
                (self.class_iri.as_str(), "A test class."),
                (self.prop_iri.as_str(), "A test property."),
            ]
        ))
        axioms = self.graph_extractor.generate_batch_rdfs_comment_axioms(
            entities_meta=[(self.class_iri, "class"), (self.prop_iri, "property")],
            context="some ontology context",
        )
        self.assertEqual(len(axioms), 2)
        expected = OWLAnnotationAssertionAxiom(
            self.class_iri, OWLAnnotation(OWLAnnotationProperty(IRI.create(RDFS_COMMENT_IRI)), OWLLiteral("A test class."))
        )
        self.assertIn(expected, axioms)

    def test_skips_entities_not_in_input_set(self):
        self.graph_extractor.batch_rdfs_comment_generator = MagicMock(return_value=MagicMock(
            entity_comment_pairs=[("http://example.org/Unknown", "unexpected comment")]
        ))
        axioms = self.graph_extractor.generate_batch_rdfs_comment_axioms(
            entities_meta=[(self.class_iri, "class")], context="context"
        )
        self.assertEqual(axioms, [])

    def test_skips_none_comments(self):
        self.graph_extractor.batch_rdfs_comment_generator = MagicMock(return_value=MagicMock(
            entity_comment_pairs=[(self.class_iri.as_str(), None)]
        ))
        axioms = self.graph_extractor.generate_batch_rdfs_comment_axioms(
            entities_meta=[(self.class_iri, "class")], context="context"
        )
        self.assertEqual(axioms, [])

    def test_llm_failure_returns_empty_list(self):
        self.graph_extractor.batch_rdfs_comment_generator = MagicMock(side_effect=RuntimeError("LLM error"))
        axioms = self.graph_extractor.generate_batch_rdfs_comment_axioms(
            entities_meta=[(self.class_iri, "class")], context="context"
        )
        self.assertEqual(axioms, [])

    def test_llm_failure_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True)
        extractor.batch_rdfs_comment_generator = MagicMock(side_effect=RuntimeError("LLM error"))
        axioms = extractor.generate_batch_rdfs_comment_axioms(
            entities_meta=[(self.class_iri, "class")], context="context"
        )
        self.assertEqual(axioms, [])


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
