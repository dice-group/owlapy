"""Python-side type-check coverage for owlapy.iri.IRI (#271 follow-up).

IRI backs the identity of virtually every OWL entity and is mapped straight to Java's
org.semanticweb.owlapi.model.IRI in owlapi_mapper.py, so a bad argument here used to
either succeed silently (str-like duck typing) or fail with a bare, -O-strippable
AssertionError rather than a clear TypeError/ValueError.
"""
import pytest

from owlapy.iri import IRI
from owlapy.namespaces import Namespaces


def test_init_rejects_non_str_non_namespaces_namespace():
    with pytest.raises(TypeError):
        IRI(123, "x")


def test_init_rejects_non_str_remainder():
    with pytest.raises(TypeError):
        IRI("http://example.com/", 456)


def test_init_rejects_namespace_without_valid_suffix():
    with pytest.raises(ValueError):
        IRI("noSlashOrHashOrColon")


def test_init_accepts_namespaces_instance():
    ns = Namespaces("ex", "http://example.com/")
    iri = IRI(ns, "x")
    assert iri.get_namespace() == "http://example.com/"
    assert iri.remainder == "x"


def test_init_accepts_file_path_without_suffix_check():
    iri = IRI("some/file.owl", is_file_path=True)
    assert iri.get_namespace() == "some/file.owl"


def test_create_rejects_non_str_non_namespaces_iri():
    with pytest.raises(TypeError):
        IRI.create(123)


def test_create_rejects_non_str_remainder():
    with pytest.raises(TypeError):
        IRI.create("http://example.com/", 456)


def test_create_rejects_iri_without_slash():
    with pytest.raises(ValueError):
        IRI.create("no-slash-here")


def test_create_rejects_whitespace():
    with pytest.raises(ValueError):
        IRI.create("http://example.com/has space")


def test_create_splits_namespace_and_remainder():
    iri = IRI.create("http://example.com/onto#Class")
    assert iri.get_namespace() == "http://example.com/onto#"
    assert iri.remainder == "Class"
