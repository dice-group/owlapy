"""Unit tests for owlapy.owl_ontology.OWLOntologyID -- a small, self-contained
value class that existing ontology-management tests only touch incidentally."""
from owlapy.iri import IRI
from owlapy.owl_ontology import OWLOntologyID

ONTOLOGY_IRI = IRI.create("http://example.com/onto#")
VERSION_IRI = IRI.create("http://example.com/onto/1.0#")


def test_anonymous_ontology_id():
    oid = OWLOntologyID()
    assert oid.get_ontology_iri() is None
    assert oid.get_version_iri() is None
    assert oid.get_default_document_iri() is None
    assert oid.is_anonymous() is True


def test_ontology_id_with_only_ontology_iri():
    oid = OWLOntologyID(ONTOLOGY_IRI)
    assert oid.get_ontology_iri() == ONTOLOGY_IRI
    assert oid.get_version_iri() is None
    # No version IRI -> default document IRI falls back to the ontology IRI.
    assert oid.get_default_document_iri() == ONTOLOGY_IRI
    assert oid.is_anonymous() is False


def test_ontology_id_with_ontology_and_version_iri():
    oid = OWLOntologyID(ONTOLOGY_IRI, VERSION_IRI)
    assert oid.get_ontology_iri() == ONTOLOGY_IRI
    assert oid.get_version_iri() == VERSION_IRI
    # Both present -> default document IRI prefers the version IRI.
    assert oid.get_default_document_iri() == VERSION_IRI
    assert oid.is_anonymous() is False


def test_ontology_id_repr():
    oid = OWLOntologyID(ONTOLOGY_IRI, VERSION_IRI)
    assert repr(oid) == f"OWLOntologyID({repr(ONTOLOGY_IRI)}, {repr(VERSION_IRI)})"


def test_ontology_id_equality():
    a = OWLOntologyID(ONTOLOGY_IRI, VERSION_IRI)
    b = OWLOntologyID(ONTOLOGY_IRI, VERSION_IRI)
    c = OWLOntologyID(ONTOLOGY_IRI)
    assert a == b
    assert a != c
    # Comparing against an unrelated type falls back to NotImplemented -> False via Python's protocol.
    assert (a == "not an ontology id") is False
