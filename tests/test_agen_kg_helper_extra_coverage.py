"""Unit tests for the remaining untested functions in owlapy.agen_kg.helper:
configure_dspy, run_query, and extract_hierarchy_from_dbpedia. chunked_iterator
is already covered in tests/test_owlapy_graph_extractor.py.

No real network calls or LLM API calls are made -- requests.get and dspy.LM/
dspy.Predict are mocked so these tests run offline and deterministically.
"""
import unittest
from unittest.mock import MagicMock, patch

from owlapy.agen_kg.helper import configure_dspy, extract_hierarchy_from_dbpedia, run_query


class TestConfigureDspy(unittest.TestCase):
    def test_configure_dspy_builds_predict_model(self):
        mock_signature = MagicMock()
        with patch("owlapy.agen_kg.helper.dspy.LM") as mock_lm, \
             patch("owlapy.agen_kg.helper.dspy.configure") as mock_configure, \
             patch("owlapy.agen_kg.helper.dspy.Predict") as mock_predict:
            mock_lm_instance = MagicMock()
            mock_lm.return_value = mock_lm_instance
            mock_predict_instance = MagicMock()
            mock_predict.return_value = mock_predict_instance

            result = configure_dspy(mock_signature)

            mock_lm.assert_called_once()
            mock_configure.assert_called_once_with(lm=mock_lm_instance)
            mock_predict.assert_called_once_with(mock_signature)
            self.assertIs(result, mock_predict_instance)


class TestRunQuery(unittest.TestCase):
    def test_run_query_extracts_subclass_bindings(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": {"bindings": [
                {"subclass": {"value": "http://dbpedia.org/ontology/Athlete"}},
                {"subclass": {"value": "http://dbpedia.org/ontology/Politician"}},
            ]}
        }
        with patch("owlapy.agen_kg.helper.requests.get", return_value=mock_response) as mock_get:
            result = run_query("SELECT ?subclass WHERE { ... }")

        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        self.assertEqual(
            result,
            ["http://dbpedia.org/ontology/Athlete", "http://dbpedia.org/ontology/Politician"],
        )

    def test_run_query_extracts_superclass_bindings(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": {"bindings": [{"superclass": {"value": "http://dbpedia.org/ontology/Person"}}]}
        }
        with patch("owlapy.agen_kg.helper.requests.get", return_value=mock_response):
            result = run_query("SELECT ?superclass WHERE { ... }")

        self.assertEqual(result, ["http://dbpedia.org/ontology/Person"])


class TestExtractHierarchyFromDbpedia(unittest.TestCase):
    def test_extract_hierarchy_returns_super_and_sub_classes(self):
        with patch("owlapy.agen_kg.helper.run_query") as mock_run_query:
            mock_run_query.side_effect = [
                ["http://dbpedia.org/ontology/Agent"],  # superclasses
                ["http://dbpedia.org/ontology/Athlete"],  # subclasses
            ]
            superclasses, subclasses = extract_hierarchy_from_dbpedia("Person")

        self.assertEqual(superclasses, ["http://dbpedia.org/ontology/Agent"])
        self.assertEqual(subclasses, ["http://dbpedia.org/ontology/Athlete"])
        # Verify the DBpedia class URI was built from the capitalized class name.
        first_call_query = mock_run_query.call_args_list[0].args[0]
        self.assertIn("http://dbpedia.org/ontology/Person", first_call_query)

    def test_extract_hierarchy_applies_american_to_british_mapping(self):
        with patch("owlapy.agen_kg.helper.run_query") as mock_run_query:
            mock_run_query.side_effect = [[], []]
            extract_hierarchy_from_dbpedia("color")

        first_call_query = mock_run_query.call_args_list[0].args[0]
        # "color" -> "colour" -> capitalized "Colour" in the built DBpedia URI.
        self.assertIn("http://dbpedia.org/ontology/Colour", first_call_query)


if __name__ == '__main__':
    unittest.main()
