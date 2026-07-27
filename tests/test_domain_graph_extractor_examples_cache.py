"""Unit tests for DomainGraphExtractor's few-shot example generation and its
thin delegation methods over DomainExamplesCache (clear_domain_cache,
clear_all_domain_caches, list_cached_domains, is_domain_cached,
get_cache_file_path). A real DomainExamplesCache backed by a tmp_path is used
(pure filesystem/JSON, no LLM), while few_shot_generator (dspy.Predict) is
stubbed for generate_domain_specific_examples -- no real API calls.
"""
import unittest
from unittest.mock import MagicMock

from owlapy.agen_kg.graph_extracting_models.domain_graph_extractor import DomainGraphExtractor
from owlapy.agen_kg.helper import task_example_mapping


class TestGenerateDomainSpecificExamples(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp_dir = tempfile.mkdtemp()
        self.extractor = DomainGraphExtractor(examples_cache_dir=self.tmp_dir)
        self.extractor.few_shot_generator = MagicMock(
            side_effect=lambda domain, task_type, num_examples, examples_example_structure: MagicMock(
                few_shot_examples=f"examples for {task_type} in {domain}"
            )
        )

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_generates_examples_for_all_task_types(self):
        examples = self.extractor.generate_domain_specific_examples("biology")
        self.assertEqual(set(examples.keys()), set(task_example_mapping.keys()))
        self.assertEqual(examples["entity_extraction"], "examples for entity_extraction in biology")
        self.assertEqual(self.extractor.few_shot_generator.call_count, len(task_example_mapping))

    def test_caches_generated_examples_to_disk(self):
        self.extractor.generate_domain_specific_examples("chemistry")
        self.assertTrue(self.extractor.is_domain_cached("chemistry"))

    def test_second_call_loads_from_cache_without_regenerating(self):
        self.extractor.generate_domain_specific_examples("physics")
        self.extractor.few_shot_generator.reset_mock()

        examples = self.extractor.generate_domain_specific_examples("physics")

        self.extractor.few_shot_generator.assert_not_called()
        self.assertEqual(set(examples.keys()), set(task_example_mapping.keys()))

    def test_logs_when_enabled(self):
        import tempfile
        tmp_dir = tempfile.mkdtemp()
        try:
            extractor = DomainGraphExtractor(enable_logging=True, examples_cache_dir=tmp_dir)
            extractor.few_shot_generator = MagicMock(return_value=MagicMock(few_shot_examples="ex"))
            extractor.generate_domain_specific_examples("astronomy")
            # Second call exercises the "loaded cached examples" logging branch.
            extractor.generate_domain_specific_examples("astronomy")
        finally:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_logs_warning_when_caching_fails(self):
        extractor = DomainGraphExtractor(enable_logging=True, examples_cache_dir=self.tmp_dir)
        extractor.few_shot_generator = MagicMock(return_value=MagicMock(few_shot_examples="ex"))
        extractor.examples_cache.save_examples = MagicMock(return_value=False)
        extractor.generate_domain_specific_examples("geology")  # should not raise


class TestDomainCacheDelegationMethods(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp_dir = tempfile.mkdtemp()
        self.extractor = DomainGraphExtractor(examples_cache_dir=self.tmp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def _seed_domain(self, domain):
        from owlapy.agen_kg.domain_examples_cache import EXAMPLE_TYPE_MAPPING
        examples = {key: f"example for {key}" for key in EXAMPLE_TYPE_MAPPING}
        self.extractor.examples_cache.save_examples(domain, examples)

    def test_is_domain_cached_true_and_false(self):
        self.assertFalse(self.extractor.is_domain_cached("biology"))
        self._seed_domain("biology")
        self.assertTrue(self.extractor.is_domain_cached("biology"))

    def test_get_cache_file_path_matches_underlying_cache(self):
        self.assertEqual(
            self.extractor.get_cache_file_path("biology"),
            self.extractor.examples_cache.get_cache_file_path("biology"),
        )

    def test_list_cached_domains(self):
        self._seed_domain("biology")
        self._seed_domain("chemistry")
        self.assertEqual(self.extractor.list_cached_domains(), ["biology", "chemistry"])

    def test_list_cached_domains_logs_when_enabled_and_nonempty(self):
        extractor = DomainGraphExtractor(enable_logging=True, examples_cache_dir=self.tmp_dir)
        self._seed_domain("biology")
        extractor.list_cached_domains()  # should not raise

    def test_clear_domain_cache_removes_only_that_domain(self):
        self._seed_domain("biology")
        self._seed_domain("chemistry")
        self.assertTrue(self.extractor.clear_domain_cache("biology"))
        self.assertFalse(self.extractor.is_domain_cached("biology"))
        self.assertTrue(self.extractor.is_domain_cached("chemistry"))

    def test_clear_domain_cache_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True, examples_cache_dir=self.tmp_dir)
        self._seed_domain("biology")
        self.assertTrue(extractor.clear_domain_cache("biology"))

    def test_clear_all_domain_caches(self):
        self._seed_domain("biology")
        self._seed_domain("chemistry")
        self.assertTrue(self.extractor.clear_all_domain_caches())
        self.assertEqual(self.extractor.list_cached_domains(), [])

    def test_clear_all_domain_caches_logs_when_enabled(self):
        extractor = DomainGraphExtractor(enable_logging=True, examples_cache_dir=self.tmp_dir)
        self._seed_domain("biology")
        self.assertTrue(extractor.clear_all_domain_caches())


if __name__ == '__main__':
    unittest.main()
