"""Tests for owlapy's optional owlready2 dependency (issue #205, Group B item 6).

owlready2 is no longer a hard install-time dependency: `pip install owlapy` (the "min" extra)
works without it, and only code paths that actually construct/call owlready2-backed
functionality (`Ontology`, `StructuralReasoner`, a couple of `util_owl_static_funcs` helpers)
raise a clear `ImportError` at the point of use.

The "owlready2 genuinely absent" checks below run in a *subprocess* with owlready2 imports
blocked, rather than patching `sys.modules`/`builtins.__import__` in-process: this test env has
owlready2 installed (it's still a `dev`-extra dependency, since most of the rest of the suite
exercises the owlready2-backed classes directly), so patching in-process would risk leaking a
blocked import across into the rest of the (owlready2-dependent) test session.
"""
import subprocess
import sys
import textwrap

import pytest

from owlapy._lazy_owlready2 import _MISSING_OWLREADY2, _MissingOwlready2Meta, _placeholder, import_owlready2

_IMPORT_BLOCKER = textwrap.dedent("""
    import builtins

    _real_import = builtins.__import__

    def _blocking_import(name, *args, **kwargs):
        if name == "owlready2" or name.startswith("owlready2."):
            raise ModuleNotFoundError(f"No module named {name!r} (blocked for test)")
        return _real_import(name, *args, **kwargs)

    builtins.__import__ = _blocking_import
""")


def _run_without_owlready2(script: str) -> subprocess.CompletedProcess:
    full_script = _IMPORT_BLOCKER + "\n" + textwrap.dedent(script)
    return subprocess.run([sys.executable, "-c", full_script], capture_output=True, text=True, timeout=60)


class TestMissingOwlready2Placeholder:
    """Unit tests for the shim itself -- these don't need owlready2 to actually be absent."""

    def test_attribute_chain_resolves_without_error(self):
        chained = _MISSING_OWLREADY2.namespace.World
        assert isinstance(chained, type)

    def test_attribute_chain_is_a_fresh_placeholder(self):
        chained = _placeholder("owlready2").SomeClass
        assert isinstance(chained, _MissingOwlready2Meta)

    def test_placeholder_is_a_valid_type_for_annotations_and_isinstance(self):
        # This is the property that makes it safe to sit behind `functools.singledispatch`-
        # registered functions' first-parameter type annotations, which require an actual class.
        assert isinstance(_MISSING_OWLREADY2, type)

        class Dummy:
            pass

        assert isinstance(Dummy(), _MISSING_OWLREADY2) is False  # never matches, doesn't raise

    def test_calling_placeholder_raises_import_error_with_install_hint(self):
        with pytest.raises(ImportError, match="owlready2"):
            _MISSING_OWLREADY2()

    def test_calling_chained_placeholder_raises_import_error(self):
        with pytest.raises(ImportError):
            _MISSING_OWLREADY2.World(filename="x")

    def test_import_owlready2_returns_real_module_when_installed(self):
        # owlready2 is a `dev`-extra dependency of this test environment.
        import owlready2 as real_owlready2

        assert import_owlready2() is real_owlready2


class TestOwlapyImportsWithoutOwlready2:
    def test_owlapy_top_level_imports(self):
        result = _run_without_owlready2("import owlapy; print('OK', owlapy.__version__)")
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout

    def test_owl_ontology_module_imports(self):
        result = _run_without_owlready2(
            "from owlapy.owl_ontology import RDFLibOntology, SyncOntology, Ontology, NeuralOntology; print('OK')")
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout

    def test_owl_reasoner_module_imports(self):
        result = _run_without_owlready2(
            "from owlapy.owl_reasoner import SyncReasoner, StructuralReasoner; print('OK')")
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout

    def test_util_owl_static_funcs_module_imports(self):
        result = _run_without_owlready2(
            "from owlapy.util_owl_static_funcs import create_ontology, csv_to_rdf_kg, save_owl_class_expressions; print('OK')")
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout

    def test_owl_reasoner_rdflib_module_imports(self):
        result = _run_without_owlready2("from owlapy.owl_reasoner_rdflib import RDFLibReasoner; print('OK')")
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout

    def test_scripts_entry_point_module_imports(self):
        result = _run_without_owlready2("from owlapy.scripts import run; print('OK')")
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout


class TestRDFLibOntologyUsableWithoutOwlready2:
    def test_full_read_write_round_trip(self, tmp_path):
        kg = tmp_path / "test.owl"
        from rdflib import OWL, RDF, Graph, URIRef
        g = Graph()
        g.add((URIRef("http://ex.com#Person"), RDF.type, OWL.Class))
        g.serialize(destination=str(kg), format="xml")

        script = f"""
            from owlapy.class_expression import OWLClass
            from owlapy.owl_axiom import OWLDeclarationAxiom
            from owlapy.owl_ontology import RDFLibOntology

            onto = RDFLibOntology({str(kg)!r})
            classes = list(onto.classes_in_signature())
            assert len(classes) == 1, classes

            onto.add_axiom(OWLDeclarationAxiom(OWLClass("http://ex.com#Agent")))
            assert len(list(onto.classes_in_signature())) == 2

            onto.save({str(tmp_path / "out.owl")!r})
            print("OK")
        """
        result = _run_without_owlready2(script)
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout
        assert (tmp_path / "out.owl").exists()

    def test_rdflib_reasoner_usable(self, tmp_path):
        kg = tmp_path / "test.owl"
        from rdflib import OWL, RDF, Graph, URIRef
        g = Graph()
        person = URIRef("http://ex.com#Person")
        alice = URIRef("http://ex.com#alice")
        g.add((person, RDF.type, OWL.Class))
        g.add((alice, RDF.type, OWL.NamedIndividual))
        g.add((alice, RDF.type, person))
        g.serialize(destination=str(kg), format="xml")

        script = f"""
            from owlapy.class_expression import OWLClass
            from owlapy.owl_reasoner_rdflib import RDFLibReasoner

            reasoner = RDFLibReasoner({str(kg)!r})
            instances = list(reasoner.instances(OWLClass("http://ex.com#Person")))
            assert len(instances) == 1, instances
            print("OK")
        """
        result = _run_without_owlready2(script)
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout


class TestOwlready2BackedClassesRaiseClearErrorWithoutOwlready2:
    def test_ontology_construction_raises(self):
        script = """
            from owlapy.owl_ontology import Ontology
            try:
                Ontology("http://example.com/test#", load=False)
                print("NOT_RAISED")
            except ImportError as e:
                assert "owlready2" in str(e)
                assert "pip install" in str(e)
                print("OK")
        """
        result = _run_without_owlready2(script)
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout

    def test_structural_reasoner_construction_raises(self):
        script = """
            import warnings
            from owlapy.owl_reasoner import StructuralReasoner
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                try:
                    StructuralReasoner("dummy.owl")
                    print("NOT_RAISED")
                except ImportError as e:
                    assert "owlready2" in str(e)
                    print("OK")
        """
        result = _run_without_owlready2(script)
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout

    def test_make_kb_incomplete_raises(self):
        script = """
            from owlapy.util_owl_static_funcs import make_kb_incomplete
            try:
                make_kb_incomplete("dummy.owl", "out.owl", 0.1, 1)
                print("NOT_RAISED")
            except ImportError as e:
                assert "owlready2" in str(e)
                print("OK")
        """
        result = _run_without_owlready2(script)
        assert result.returncode == 0, result.stderr
        assert "OK" in result.stdout
