"""Unit tests for owlapy.agen_kg.text_loader.

PyPDF2, python-docx, and striprtf are NOT installed in this environment (they're
optional deps for PDF/DOCX/RTF support), so the ImportError branches of
PDFLoader/DOCXLoader/RTFLoader are exercised for free -- no mocking needed there.
For the "happy path" content-extraction logic of those three loaders, fake modules
are injected into sys.modules (a standard technique for testing optional-dependency
code without actually installing the dependency) so every branch is still reachable.
"""
import sys
import unittest
from unittest.mock import MagicMock, patch

from owlapy.agen_kg.text_loader import (
    DOCXLoader,
    HTMLLoader,
    PDFLoader,
    RawTextLoader,
    RTFLoader,
    TXTLoader,
    UniversalTextLoader,
)


class TestTXTLoader(unittest.TestCase):
    def setUp(self):
        self.loader = TXTLoader()

    def test_load_reads_utf8_content(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Hello, world!")
            path = f.name
        try:
            self.assertEqual(self.loader.load(path), "Hello, world!")
        finally:
            import os
            os.remove(path)

    def test_load_missing_file_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.loader.load("/nonexistent/path/does_not_exist.txt")

    def test_load_falls_back_to_latin1_on_unicode_decode_error(self):
        import os
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, 'wb') as f:
                # 0xe9 is not valid UTF-8 on its own, but is valid latin-1 ('é').
                f.write(b"caf\xe9")
            content = self.loader.load(path)
            self.assertEqual(content, "caf\xe9")
        finally:
            os.remove(path)

    def test_load_raises_value_error_when_no_encoding_works(self):
        import os
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(b"\x00")
            with patch("builtins.open") as mock_open:
                # Force every attempted encoding (utf-8, latin-1, iso-8859-1, cp1252)
                # to fail, exercising the final `raise ValueError` branch.
                def _raise(*args, **kwargs):
                    raise UnicodeDecodeError("utf-8", b"\x00", 0, 1, "forced failure")
                mock_open.side_effect = _raise
                with self.assertRaises(ValueError):
                    self.loader.load(path)
        finally:
            os.remove(path)


class TestPDFDOCXRTFLoaderImportErrors(unittest.TestCase):
    """PyPDF2 / python-docx / striprtf are not installed, so these always hit the
    ImportError branch first -- no mocking required."""

    def test_pdf_loader_raises_import_error(self):
        with self.assertRaises(ImportError):
            PDFLoader().load("whatever.pdf")

    def test_docx_loader_raises_import_error(self):
        with self.assertRaises(ImportError):
            DOCXLoader().load("whatever.docx")

    def test_rtf_loader_raises_import_error(self):
        with self.assertRaises(ImportError):
            RTFLoader().load("whatever.rtf")


class TestPDFLoaderWithFakeDependency(unittest.TestCase):
    """Inject a fake PyPDF2 module to exercise the happy-path and error-handling
    logic below the import, without requiring the real optional dependency."""

    def test_pdf_loader_extracts_text_from_pages(self):
        fake_page1 = MagicMock()
        fake_page1.extract_text.return_value = "Page one text"
        fake_page2 = MagicMock()
        fake_page2.extract_text.return_value = "Page two text"

        fake_reader = MagicMock()
        fake_reader.pages = [fake_page1, fake_page2]

        fake_pypdf2 = MagicMock()
        fake_pypdf2.PdfReader.return_value = fake_reader

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            with patch.dict(sys.modules, {"PyPDF2": fake_pypdf2}):
                text = PDFLoader().load(path)
            self.assertEqual(text, "Page one text\nPage two text")
        finally:
            import os
            os.remove(path)

    def test_pdf_loader_missing_file_raises_file_not_found(self):
        fake_pypdf2 = MagicMock()
        with patch.dict(sys.modules, {"PyPDF2": fake_pypdf2}):
            with self.assertRaises(FileNotFoundError):
                PDFLoader().load("/nonexistent/file.pdf")

    def test_pdf_loader_wraps_extraction_errors_as_value_error(self):
        fake_pypdf2 = MagicMock()
        fake_pypdf2.PdfReader.side_effect = RuntimeError("corrupt pdf")

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            with patch.dict(sys.modules, {"PyPDF2": fake_pypdf2}):
                with self.assertRaises(ValueError):
                    PDFLoader().load(path)
        finally:
            import os
            os.remove(path)


class TestDOCXLoaderWithFakeDependency(unittest.TestCase):
    def test_docx_loader_extracts_paragraphs_and_tables(self):
        fake_para1 = MagicMock(text="Paragraph one")
        fake_cell = MagicMock(text="Cell text")
        fake_row = MagicMock(cells=[fake_cell])
        fake_table = MagicMock(rows=[fake_row])

        fake_doc = MagicMock()
        fake_doc.paragraphs = [fake_para1]
        fake_doc.tables = [fake_table]

        fake_docx_module = MagicMock()
        fake_docx_module.Document.return_value = fake_doc

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            path = f.name
        try:
            with patch.dict(sys.modules, {"docx": fake_docx_module}):
                text = DOCXLoader().load(path)
            self.assertEqual(text, "Paragraph one\nCell text")
        finally:
            import os
            os.remove(path)

    def test_docx_loader_missing_file_raises_file_not_found(self):
        fake_docx_module = MagicMock()
        with patch.dict(sys.modules, {"docx": fake_docx_module}):
            with self.assertRaises(FileNotFoundError):
                DOCXLoader().load("/nonexistent/file.docx")

    def test_docx_loader_wraps_extraction_errors_as_value_error(self):
        fake_docx_module = MagicMock()
        fake_docx_module.Document.side_effect = RuntimeError("corrupt docx")

        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            path = f.name
        try:
            with patch.dict(sys.modules, {"docx": fake_docx_module}):
                with self.assertRaises(ValueError):
                    DOCXLoader().load(path)
        finally:
            import os
            os.remove(path)


class TestRTFLoaderWithFakeDependency(unittest.TestCase):
    def test_rtf_loader_strips_rtf_markup(self):
        fake_striprtf_module = MagicMock()
        fake_striprtf_module.rtf_to_text.return_value = "Plain text"

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix=".rtf", delete=False, encoding='utf-8') as f:
            f.write(r"{\rtf1 Plain text}")
            path = f.name
        try:
            with patch.dict(sys.modules, {"striprtf.striprtf": fake_striprtf_module, "striprtf": MagicMock()}):
                text = RTFLoader().load(path)
            self.assertEqual(text, "Plain text")
        finally:
            import os
            os.remove(path)

    def test_rtf_loader_missing_file_raises_file_not_found(self):
        fake_striprtf_module = MagicMock()
        with patch.dict(sys.modules, {"striprtf.striprtf": fake_striprtf_module, "striprtf": MagicMock()}):
            with self.assertRaises(FileNotFoundError):
                RTFLoader().load("/nonexistent/file.rtf")

    def test_rtf_loader_wraps_extraction_errors_as_value_error(self):
        fake_striprtf_module = MagicMock()
        fake_striprtf_module.rtf_to_text.side_effect = RuntimeError("corrupt rtf")

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix=".rtf", delete=False, encoding='utf-8') as f:
            f.write(r"{\rtf1 broken}")
            path = f.name
        try:
            with patch.dict(sys.modules, {"striprtf.striprtf": fake_striprtf_module, "striprtf": MagicMock()}):
                with self.assertRaises(ValueError):
                    RTFLoader().load(path)
        finally:
            import os
            os.remove(path)


class TestHTMLLoader(unittest.TestCase):
    """No optional dependency -- uses only the built-in html.parser module."""

    def setUp(self):
        self.loader = HTMLLoader()

    def test_load_strips_html_tags(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix=".html", delete=False, encoding='utf-8') as f:
            f.write("<html><body><p>Hello <b>world</b>!</p></body></html>")
            path = f.name
        try:
            text = self.loader.load(path)
            self.assertEqual(text, "Hello world!")
        finally:
            import os
            os.remove(path)

    def test_load_missing_file_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.loader.load("/nonexistent/file.html")

    def test_load_wraps_read_errors_as_value_error(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix=".html", delete=False, encoding='utf-8') as f:
            f.write("<p>content</p>")
            path = f.name
        try:
            with patch("builtins.open", side_effect=OSError("disk read error")):
                with self.assertRaises(ValueError):
                    self.loader.load(path)
        finally:
            import os
            os.remove(path)


class TestRawTextLoader(unittest.TestCase):
    def test_load_returns_string_as_is(self):
        self.assertEqual(RawTextLoader().load("just some text"), "just some text")

    def test_load_stringifies_non_string_input(self):
        self.assertEqual(RawTextLoader().load(12345), "12345")


class TestUniversalTextLoader(unittest.TestCase):
    def setUp(self):
        self.loader = UniversalTextLoader()

    def test_treats_non_file_input_as_raw_text(self):
        text = self.loader.load("This is not a file path, just text.")
        self.assertEqual(text, "This is not a file path, just text.")

    def test_loads_txt_file_via_auto_detected_extension(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("auto-detected content")
            path = f.name
        try:
            self.assertEqual(self.loader.load(path), "auto-detected content")
        finally:
            import os
            os.remove(path)

    def test_loads_file_with_explicit_file_type_without_leading_dot(self):
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("explicit type content")
            path = f.name
        try:
            self.assertEqual(self.loader.load(path, file_type="txt"), "explicit type content")
        finally:
            import os
            os.remove(path)

    def test_unsupported_file_type_raises_value_error(self):
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            path = f.name
        try:
            with self.assertRaises(ValueError):
                self.loader.load(path)
        finally:
            import os
            os.remove(path)

    def test_loader_error_is_wrapped_as_value_error(self):
        # .pdf is a supported extension but PyPDF2 isn't installed, so the
        # underlying PDFLoader.load() raises ImportError, which
        # UniversalTextLoader.load() wraps as ValueError.
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            path = f.name
        try:
            with self.assertRaises(ValueError):
                self.loader.load(path)
        finally:
            import os
            os.remove(path)

    def test_logging_enabled_does_not_raise(self):
        logging_loader = UniversalTextLoader(enable_logging=True)
        text = logging_loader.load("Just raw text, logged.")
        self.assertEqual(text, "Just raw text, logged.")

        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("logged file content")
            path = f.name
        try:
            self.assertEqual(logging_loader.load(path), "logged file content")
        finally:
            import os
            os.remove(path)

    def test_supports_file_type_with_and_without_dot(self):
        self.assertTrue(self.loader.supports_file_type(".txt"))
        self.assertTrue(self.loader.supports_file_type("txt"))
        self.assertTrue(self.loader.supports_file_type("PDF"))
        self.assertFalse(self.loader.supports_file_type(".xyz"))

    def test_supported_formats_lists_all_registered_extensions(self):
        formats = self.loader.supported_formats
        self.assertIn(".txt", formats)
        self.assertIn(".pdf", formats)
        self.assertIn(".docx", formats)
        self.assertIn(".rtf", formats)
        self.assertIn(".html", formats)


if __name__ == '__main__':
    unittest.main()
