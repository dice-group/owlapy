"""Unit tests for owlapy.agen_kg.agent.AGenKG.

dspy.LM/dspy.configure are mocked to avoid any real network/API calls during
construction. The underlying extractors' own dspy.Predict(...) calls don't hit
the network at construction time (confirmed by test_owlapy_graph_extractor.py
already constructing DomainGraphExtractor() unmocked), so only the LM setup
in AGenKG.__init__ itself needs mocking here.
"""
import unittest
from unittest.mock import MagicMock, patch

from owlapy.agen_kg.agent import AGenKG
from owlapy.agen_kg.graph_extracting_models import DomainGraphExtractor, OpenGraphExtractor


def _make_agent(**kwargs):
    with patch("owlapy.agen_kg.agent.dspy.LM") as mock_lm, \
         patch("owlapy.agen_kg.agent.dspy.configure") as mock_configure:
        mock_lm.return_value = MagicMock()
        agent = AGenKG(**kwargs)
    return agent, mock_lm, mock_configure


class TestAGenKGInit(unittest.TestCase):
    def test_init_configures_lm_with_expected_model_prefix(self):
        agent, mock_lm, mock_configure = _make_agent(model="gpt-4o", api_key="fake-key")
        mock_lm.assert_called_once()
        _, call_kwargs = mock_lm.call_args
        self.assertEqual(call_kwargs["model"], "openai/gpt-4o")
        self.assertEqual(call_kwargs["api_key"], "fake-key")
        mock_configure.assert_called_once()

    def test_init_stores_configuration_attributes(self):
        agent, _, _ = _make_agent(
            model="gpt-4o-mini", api_key="k", api_base="https://example.com",
            temperature=0.3, seed=7, cache=True, enable_logging=True, max_tokens=2000,
        )
        self.assertEqual(agent.model, "gpt-4o-mini")
        self.assertEqual(agent.api_key, "k")
        self.assertEqual(agent.api_base, "https://example.com")
        self.assertEqual(agent.temperature, 0.3)
        self.assertEqual(agent.seed, 7)
        self.assertTrue(agent.cache)
        self.assertTrue(agent.enable_logging)
        self.assertEqual(agent.max_tokens, 2000)

    def test_init_creates_both_extractors(self):
        agent, _, _ = _make_agent()
        self.assertIsInstance(agent.open_graph_extractor, OpenGraphExtractor)
        self.assertIsInstance(agent.domain_graph_extractor, DomainGraphExtractor)


class TestAGenKGConfigureChunking(unittest.TestCase):
    def setUp(self):
        self.agent, _, _ = _make_agent()

    def test_configure_chunking_delegates_to_both_extractors(self):
        with patch.object(self.agent.open_graph_extractor, "configure_chunking") as mock_open, \
             patch.object(self.agent.domain_graph_extractor, "configure_chunking") as mock_domain:
            self.agent.configure_chunking(chunk_size=1000, overlap=50, strategy="paragraph")

        mock_open.assert_called_once_with(
            chunk_size=1000, overlap=50, strategy="paragraph",
            auto_chunk_threshold=None, summarization_threshold=None, max_summary_length=None,
        )
        mock_domain.assert_called_once_with(
            chunk_size=1000, overlap=50, strategy="paragraph",
            auto_chunk_threshold=None, summarization_threshold=None, max_summary_length=None,
        )

    def test_configure_chunking_for_model_delegates_to_both_extractors(self):
        with patch.object(self.agent.open_graph_extractor, "configure_chunking_for_model") as mock_open, \
             patch.object(self.agent.domain_graph_extractor, "configure_chunking_for_model") as mock_domain:
            self.agent.configure_chunking_for_model(max_context_tokens=8192, prompt_overhead_tokens=1000)

        mock_open.assert_called_once_with(max_context_tokens=8192, prompt_overhead_tokens=1000)
        mock_domain.assert_called_once_with(max_context_tokens=8192, prompt_overhead_tokens=1000)


class TestAGenKGGenerateOntology(unittest.TestCase):
    def setUp(self):
        self.agent, _, _ = _make_agent()

    def test_generate_ontology_rejects_invalid_ontology_type(self):
        with self.assertRaises(AssertionError):
            self.agent.generate_ontology(text="some text", ontology_type="invalid")

    def test_generate_ontology_dispatches_to_open_extractor(self):
        with patch.object(self.agent.open_graph_extractor, "generate_ontology") as mock_open:
            mock_open.return_value = "OPEN_RESULT"
            result = self.agent.generate_ontology(text="some text", ontology_type="open", query="q")

        mock_open.assert_called_once_with(text="some text", query="q")
        self.assertEqual(result, "OPEN_RESULT")

    def test_generate_ontology_dispatches_to_domain_extractor(self):
        with patch.object(self.agent.domain_graph_extractor, "generate_ontology") as mock_domain:
            mock_domain.return_value = "DOMAIN_RESULT"
            result = self.agent.generate_ontology(text="some text", ontology_type="domain")

        mock_domain.assert_called_once_with(text="some text", query=None)
        self.assertEqual(result, "DOMAIN_RESULT")

    def test_generate_ontology_defaults_to_domain_type(self):
        with patch.object(self.agent.domain_graph_extractor, "generate_ontology") as mock_domain:
            mock_domain.return_value = "DOMAIN_RESULT"
            result = self.agent.generate_ontology(text="some text")

        mock_domain.assert_called_once()
        self.assertEqual(result, "DOMAIN_RESULT")


if __name__ == '__main__':
    unittest.main()
