import json
import shutil
import tempfile
import unittest
from pathlib import Path

from owlapy.agen_kg.domain_examples_cache import EXAMPLE_TYPE_MAPPING, DomainExamplesCache


def _make_valid_examples():
    return {key: f"example text for {key}" for key in EXAMPLE_TYPE_MAPPING.keys()}


class TestDomainExamplesCache(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.cache = DomainExamplesCache(cache_dir=self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_init_creates_cache_dir_if_missing(self):
        nested_dir = Path(self.tmp_dir) / "nested" / "cache"
        self.assertFalse(nested_dir.exists())
        DomainExamplesCache(cache_dir=str(nested_dir))
        self.assertTrue(nested_dir.exists())

    def test_init_defaults_to_cwd_when_no_dir_given(self):
        cache = DomainExamplesCache()
        self.assertEqual(cache.cache_dir, Path.cwd())

    def test_sanitize_domain_name_lowercases_and_strips(self):
        self.assertEqual(DomainExamplesCache._sanitize_domain_name("  Biology  "), "biology")

    def test_sanitize_domain_name_replaces_special_chars(self):
        self.assertEqual(DomainExamplesCache._sanitize_domain_name("Bio-Medical/Science!"), "bio_medical_science_")

    def test_sanitize_domain_name_collapses_consecutive_underscores(self):
        self.assertEqual(DomainExamplesCache._sanitize_domain_name("a   b"), "a_b")

    def test_get_cache_file_path_uses_sanitized_name(self):
        path = self.cache.get_cache_file_path("My Domain")
        self.assertTrue(path.endswith("domain_examples_my_domain.json"))

    def test_save_and_load_round_trip(self):
        examples = _make_valid_examples()
        self.assertTrue(self.cache.save_examples("biology", examples))
        loaded = self.cache.load_examples("biology")
        self.assertEqual(loaded, examples)

    def test_save_examples_missing_key_fails(self):
        incomplete = _make_valid_examples()
        incomplete.pop("entity_extraction")
        self.assertFalse(self.cache.save_examples("biology", incomplete))
        self.assertFalse(self.cache.examples_exist("biology"))

    def test_load_examples_returns_none_when_not_cached(self):
        self.assertIsNone(self.cache.load_examples("nonexistent"))

    def test_load_examples_returns_none_for_corrupted_json(self):
        cache_file = self.cache._get_cache_file("broken")
        cache_file.write_text("not valid json{", encoding="utf-8")
        self.assertIsNone(self.cache.load_examples("broken"))

    def test_load_examples_returns_none_when_missing_expected_key(self):
        cache_file = self.cache._get_cache_file("partial")
        cache_file.write_text(json.dumps({"entity_extraction": "only one"}), encoding="utf-8")
        self.assertIsNone(self.cache.load_examples("partial"))

    def test_examples_exist_true_and_false(self):
        self.assertFalse(self.cache.examples_exist("chemistry"))
        self.cache.save_examples("chemistry", _make_valid_examples())
        self.assertTrue(self.cache.examples_exist("chemistry"))

    def test_clear_domain_cache_removes_file(self):
        self.cache.save_examples("physics", _make_valid_examples())
        self.assertTrue(self.cache.examples_exist("physics"))
        self.assertTrue(self.cache.clear_domain_cache("physics"))
        self.assertFalse(self.cache.examples_exist("physics"))

    def test_clear_domain_cache_nonexistent_domain_returns_true(self):
        self.assertTrue(self.cache.clear_domain_cache("never_existed"))

    def test_clear_all_caches_removes_every_file(self):
        self.cache.save_examples("biology", _make_valid_examples())
        self.cache.save_examples("chemistry", _make_valid_examples())
        self.assertTrue(self.cache.clear_all_caches())
        self.assertEqual(self.cache.list_cached_domains(), [])

    def test_list_cached_domains_returns_sorted_names(self):
        self.cache.save_examples("zoology", _make_valid_examples())
        self.cache.save_examples("astronomy", _make_valid_examples())
        self.assertEqual(self.cache.list_cached_domains(), ["astronomy", "zoology"])

    def test_list_cached_domains_empty_when_no_cache_files(self):
        self.assertEqual(self.cache.list_cached_domains(), [])


if __name__ == "__main__":
    unittest.main()
