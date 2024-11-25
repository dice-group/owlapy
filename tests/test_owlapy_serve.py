import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from owlapy.owl_ontology_manager import SyncOntologyManager
from owlapy.owl_reasoner import SyncReasoner
from owlapy.class_expression import OWLClass
from owlapy.scripts.owlapy_serve import create_app

ontology_path = "KGs/Family/family-benchmark_rich_background.owl"
reasoner_name = "HermiT"
ontology = SyncOntologyManager().load_ontology(ontology_path)
reasoner = SyncReasoner(ontology=ontology, reasoner=reasoner_name)

@patch("owlapy.scripts.owlapy_serve.stopJVM")
def test_get_classes (mock_stop_jvm):
    with TestClient(create_app(ontology_path, reasoner_name)) as client:
        response = client.get("/classes")
        expected_classes = [cls.__str__() for cls in ontology.classes_in_signature()]
        assert response.status_code == 200
        assert set(response.json()["classes"]) == set(expected_classes)

@patch("owlapy.scripts.owlapy_serve.stopJVM")
def test_get_individuals(mock_stop_jvm):
    with TestClient(create_app(ontology_path, reasoner_name)) as client:
        response = client.get("/individuals")
        expected_individuals = [ind.__str__() for ind in ontology.individuals_in_signature()]
        assert response.status_code == 200
        assert set(response.json()["individuals"]) == set(expected_individuals)

@patch("owlapy.scripts.owlapy_serve.stopJVM")
def test_get_abox(mock_stop_jvm):
    with TestClient(create_app(ontology_path, reasoner_name)) as client:
        response = client.get("/abox")
        expected_abox = [axiom.__str__() for axiom in ontology.get_abox_axioms()]
        assert response.status_code == 200
        assert set(response.json()["abox"]) == set(expected_abox)

@patch("owlapy.scripts.owlapy_serve.stopJVM")
def test_get_tbox(mock_stop_jvm):
    with TestClient(create_app(ontology_path, reasoner_name)) as client:
        response = client.get("/tbox")
        expected_tbox = [axiom.__str__() for axiom in ontology.get_tbox_axioms()]
        assert response.status_code == 200
        assert set(response.json()["tbox"]) == set(expected_tbox)

@patch("owlapy.scripts.owlapy_serve.stopJVM")
def test_get_instances(mock_stop_jvm):
    with TestClient(create_app(ontology_path, reasoner_name)) as client:
        test_class_iri = "http://www.benchmark.org/family#Child"  
        owl_class = OWLClass(test_class_iri)
        expected_instances = [ind.__str__() for ind in reasoner.instances(owl_class, direct=False)]
        response = client.post("/instances", json={"class_iri": test_class_iri})
        assert response.status_code == 200
        assert set(response.json()["instances"]) == set(expected_instances)
