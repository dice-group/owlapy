"""
Tests for SyncOntology.save() document_format parameter.

One test per supported format.  Files are saved into the
'tests/saved_formats/' directory and intentionally NOT deleted after
testing so the user can inspect them.

Formats are split into two groups:

OWL API–backed
    Written directly by OWL API's built-in storers.

rdflib-backed
    Written by first dumping to a temporary RDF/XML file via OWL API,
    then re-serialising with rdflib.  These are: turtle2, json-ld /
    jsonld, ntriples / nt, nt11, n3, trig, trix, nquads / nq.
"""
import glob
import os
import unittest

from owlapy.owl_ontology import SyncOntology

_HERE = os.path.dirname(os.path.abspath(__file__))

# All saved files land here – created automatically by _out().
OUTPUT_DIR = os.path.join(_HERE, "saved_formats")


def _out(filename: str) -> str:
    """Return absolute path for an output file inside OUTPUT_DIR."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, filename)


def _axiom_counts(onto: SyncOntology):
    abox = len(list(onto.get_abox_axioms()))
    tbox = len(list(onto.get_tbox_axioms()))
    return abox, tbox


class TestSyncOntologySaveFormats(unittest.TestCase):
    """
    Each test:
      1. Loads the father ontology.
      2. Saves it using a specific document_format string.
      3. Asserts the output file exists and is non-empty.
      4. For formats that OWL API can reload (RDF/XML, OWL/XML, Turtle,
         Functional Syntax) also asserts ABox/TBox axiom counts match
         the original (roundtrip check).
    """

    @classmethod
    def setUpClass(cls):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        cls.source = SyncOntology("KGs/Family/father.owl")
        cls.expected_abox, cls.expected_tbox = _axiom_counts(cls.source)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _assert_file_exists_and_nonempty(self, path: str):
        self.assertTrue(os.path.exists(path),
                        f"Expected output file not found: {path}")
        self.assertGreater(os.path.getsize(path), 0,
                           f"Output file is empty: {path}")

    def _assert_roundtrip(self, path: str):
        """Reload file with OWL API and verify axiom counts match source."""
        reloaded = SyncOntology(path)
        abox, tbox = _axiom_counts(reloaded)
        self.assertEqual(self.expected_abox, abox,
                         f"ABox count mismatch after roundtrip ({path})")
        self.assertEqual(self.expected_tbox, tbox,
                         f"TBox count mismatch after roundtrip ({path})")

    # ==================================================================
    # OWL API–backed formats
    # ==================================================================

    def test_save_rdfxml(self):
        path = _out("father_rdfxml.owl")
        self.source.save(path=path, document_format="rdfxml")
        self._assert_file_exists_and_nonempty(path)
        self._assert_roundtrip(path)

    def test_save_rdf_xml_slash(self):
        """Alias 'rdf/xml'."""
        path = _out("father_rdf_xml_slash.owl")
        self.source.save(path=path, document_format="rdf/xml")
        self._assert_file_exists_and_nonempty(path)
        self._assert_roundtrip(path)

    def test_save_owlxml(self):
        path = _out("father_owlxml.owl")
        self.source.save(path=path, document_format="owlxml")
        self._assert_file_exists_and_nonempty(path)
        self._assert_roundtrip(path)

    def test_save_owl_xml_slash(self):
        """Alias 'owl/xml'."""
        path = _out("father_owl_xml_slash.owl")
        self.source.save(path=path, document_format="owl/xml")
        self._assert_file_exists_and_nonempty(path)
        self._assert_roundtrip(path)

    def test_save_turtle_owlapi(self):
        """Turtle via OWL API ('turtle' key)."""
        path = _out("father_turtle_owlapi.ttl")
        self.source.save(path=path, document_format="turtle")
        self._assert_file_exists_and_nonempty(path)
        self._assert_roundtrip(path)

    def test_save_ttl_alias(self):
        """Alias 'ttl' for OWL API Turtle."""
        path = _out("father_ttl.ttl")
        self.source.save(path=path, document_format="ttl")
        self._assert_file_exists_and_nonempty(path)
        self._assert_roundtrip(path)

    def test_save_functional(self):
        path = _out("father_functional.ofn")
        self.source.save(path=path, document_format="functional")
        self._assert_file_exists_and_nonempty(path)
        self._assert_roundtrip(path)

    def test_save_fss_alias(self):
        """Alias 'fss' for Functional Syntax."""
        path = _out("father_fss.ofn")
        self.source.save(path=path, document_format="fss")
        self._assert_file_exists_and_nonempty(path)
        self._assert_roundtrip(path)

    def test_save_manchester(self):
        """Manchester Syntax – write-only check (OWL API cannot reload it)."""
        path = _out("father_manchester.omn")
        self.source.save(path=path, document_format="manchester")
        self._assert_file_exists_and_nonempty(path)

    def test_save_ms_alias(self):
        """Alias 'ms' for Manchester Syntax."""
        path = _out("father_ms.omn")
        self.source.save(path=path, document_format="ms")
        self._assert_file_exists_and_nonempty(path)

    def test_save_latex(self):
        path = _out("father_latex.tex")
        self.source.save(path=path, document_format="latex")
        self._assert_file_exists_and_nonempty(path)

    def test_save_dlsyntax(self):
        path = _out("father_dlsyntax.dl")
        self.source.save(path=path, document_format="dlsyntax")
        self._assert_file_exists_and_nonempty(path)

    def test_save_dl_alias(self):
        """Alias 'dl' for DL Syntax."""
        path = _out("father_dl.dl")
        self.source.save(path=path, document_format="dl")
        self._assert_file_exists_and_nonempty(path)

    def test_save_krss2(self):
        path = _out("father_krss2.krss")
        self.source.save(path=path, document_format="krss2")
        self._assert_file_exists_and_nonempty(path)


    def test_save_obo(self):
        path = _out("father_obo.obo")
        self.source.save(path=path, document_format="obo")
        self._assert_file_exists_and_nonempty(path)

    # ==================================================================
    # rdflib-backed formats
    # ==================================================================

    def test_save_turtle2(self):
        """Turtle via rdflib ('turtle2' key)."""
        path = _out("father_turtle2.ttl")
        self.source.save(path=path, document_format="turtle2")
        self._assert_file_exists_and_nonempty(path)

    def test_save_ntriples(self):
        """N-Triples via rdflib ('ntriples' key)."""
        path = _out("father_ntriples.nt")
        self.source.save(path=path, document_format="ntriples")
        self._assert_file_exists_and_nonempty(path)

    def test_save_nt_alias(self):
        """Alias 'nt' for N-Triples via rdflib."""
        path = _out("father_nt.nt")
        self.source.save(path=path, document_format="nt")
        self._assert_file_exists_and_nonempty(path)

    def test_save_nt11(self):
        """N-Triples 1.1 via rdflib ('nt11' key)."""
        path = _out("father_nt11.nt")
        self.source.save(path=path, document_format="nt11")
        self._assert_file_exists_and_nonempty(path)

    def test_save_n3(self):
        """Notation3 via rdflib ('n3' key)."""
        path = _out("father_n3.n3")
        self.source.save(path=path, document_format="n3")
        self._assert_file_exists_and_nonempty(path)

    def test_save_trig(self):
        """TriG via rdflib ('trig' key)."""
        path = _out("father_trig.trig")
        self.source.save(path=path, document_format="trig")
        self._assert_file_exists_and_nonempty(path)

    def test_save_trix(self):
        """TriX via rdflib ('trix' key)."""
        path = _out("father_trix.trix")
        self.source.save(path=path, document_format="trix")
        self._assert_file_exists_and_nonempty(path)

    def test_save_nquads(self):
        """N-Quads via rdflib ('nquads' key)."""
        path = _out("father_nquads.nq")
        self.source.save(path=path, document_format="nquads")
        self._assert_file_exists_and_nonempty(path)

    def test_save_nq_alias(self):
        """Alias 'nq' for N-Quads via rdflib."""
        path = _out("father_nq.nq")
        self.source.save(path=path, document_format="nq")
        self._assert_file_exists_and_nonempty(path)

    def test_save_jsonld(self):
        """JSON-LD via rdflib ('jsonld' key)."""
        path = _out("father_jsonld.jsonld")
        self.source.save(path=path, document_format="jsonld")
        self._assert_file_exists_and_nonempty(path)

    def test_save_json_ld_alias(self):
        """Alias 'json-ld' for JSON-LD via rdflib."""
        path = _out("father_json-ld.jsonld")
        self.source.save(path=path, document_format="json-ld")
        self._assert_file_exists_and_nonempty(path)

    # ==================================================================
    # Edge-case / behavioural tests
    # ==================================================================

    def test_save_default_format(self):
        """document_format=None keeps the ontology's current format."""
        path = _out("father_default_format.owl")
        self.source.save(path=path, document_format=None)
        self._assert_file_exists_and_nonempty(path)
        self._assert_roundtrip(path)

    def test_save_format_case_insensitive(self):
        """OWL API format strings are matched case-insensitively."""
        path = _out("father_turtle_upper.ttl")
        self.source.save(path=path, document_format="TURTLE")
        self._assert_file_exists_and_nonempty(path)
        self._assert_roundtrip(path)

    def test_save_rdflib_format_case_insensitive(self):
        """rdflib format strings are also matched case-insensitively."""
        path = _out("father_ntriples_upper.nt")
        self.source.save(path=path, document_format="NTRIPLES")
        self._assert_file_exists_and_nonempty(path)

    def test_save_invalid_format_raises(self):
        """An unrecognised format string raises ValueError."""
        with self.assertRaises(ValueError):
            self.source.save(path=_out("should_not_exist.owl"),
                             document_format="not_a_real_format")

    def test_rdflib_temp_file_is_deleted(self):
        """The intermediate RDF/XML temp file must not be left on disk."""
        before = set(glob.glob("/tmp/_owlapy_tmp_*.owl"))
        path = _out("father_trig_cleanup.trig")
        self.source.save(path=path, document_format="trig")
        after = set(glob.glob("/tmp/_owlapy_tmp_*.owl"))
        leftover = after - before
        self.assertEqual(set(), leftover,
                         f"Temp file(s) not cleaned up: {leftover}")


if __name__ == "__main__":
    unittest.main()

