import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner import SyncReasoner
from owlapy.class_expression import OWLClass
from owlapy.scripts.owlapy_serve import create_app
from owlapy.scripts.owlapy_serve import InferenceType

ontology_path = "KGs/Family/family-benchmark_rich_background.owl"
reasoner_name = "HermiT"
ontology = SyncOntology(ontology_path)
reasoner = SyncReasoner(ontology=ontology, reasoner=reasoner_name)


@pytest.fixture()
def mock_stop_jvm():
    patcher = patch("owlapy.scripts.owlapy_serve.stopJVM")
    patcher.start()
    yield 
    patcher.stop()


def test_get_classes (mock_stop_jvm):
    with TestClient(create_app(ontology_path, reasoner_name)) as client:
        response = client.get("/classes")
        expected_classes = [cls.__str__() for cls in ontology.classes_in_signature()]
        assert response.status_code == 200
        assert set(response.json()["classes"]) == set(expected_classes)


def test_get_object_properties(mock_stop_jvm):
    with TestClient(create_app(ontology_path, reasoner_name)) as client:
        response = client.get("/object_properties")
        expected_object_properties = [op.__str__() for op in ontology.object_properties_in_signature()]
        assert response.status_code == 200
        assert set(response.json()["object_properties"]) == set(expected_object_properties)


def test_get_data_properties(mock_stop_jvm):
    with TestClient(create_app(ontology_path, reasoner_name)) as client:
        response = client.get("/data_properties")
        expected_data_properties = [dp.__str__() for dp in ontology.data_properties_in_signature()]
        assert response.status_code == 200
        assert set(response.json()["data_properties"]) == set(expected_data_properties)


def test_get_individuals(mock_stop_jvm):
    with TestClient(create_app(ontology_path, reasoner_name)) as client:
        response = client.get("/individuals")
        expected_individuals = [ind.__str__() for ind in ontology.individuals_in_signature()]
        assert response.status_code == 200
        assert set(response.json()["individuals"]) == set(expected_individuals)


def test_get_abox(mock_stop_jvm):
    with TestClient(create_app(ontology_path, reasoner_name)) as client:
        response = client.get("/abox")
        expected_abox = [axiom.__str__() for axiom in ontology.get_abox_axioms()]
        assert response.status_code == 200
        assert set(response.json()["abox"]) == set(expected_abox)


def test_get_tbox(mock_stop_jvm):
    with TestClient(create_app(ontology_path, reasoner_name)) as client:
        response = client.get("/tbox")
        expected_tbox = [axiom.__str__() for axiom in ontology.get_tbox_axioms()]
        assert response.status_code == 200
        assert set(response.json()["tbox"]) == set(expected_tbox)


def test_get_instances(mock_stop_jvm):
    with TestClient(create_app(ontology_path, reasoner_name)) as client:
        test_class_iri = "http://www.benchmark.org/family#Child"  
        owl_class = OWLClass(test_class_iri)
        expected_instances = [ind.__str__() for ind in reasoner.instances(owl_class, direct=False)]
        response = client.post("/instances", json={"class_iri": test_class_iri})
        assert response.status_code == 200
        assert set(response.json()["instances"]) == set(expected_instances)


def test_infer_axioms(mock_stop_jvm):
    with TestClient(create_app(ontology_path, reasoner_name)) as client:
        valid_inference_type = "InferredClassAssertionAxiomGenerator"
        response = client.post(
            "/infer_axioms", 
            json={"inference_type": valid_inference_type}
        )
        assert response.status_code == 200
        expected_axioms = [
            axiom.__str__() for axiom in reasoner.infer_axioms(valid_inference_type)
        ]
        assert set(response.json()["inferred_axioms"]) == set(expected_axioms)
        invalid_inference_type = "InvalidAxiomGenerator"
        response = client.post(
            "/infer_axioms", 
            json={"inference_type": invalid_inference_type}
        )
        assert response.status_code == 422


def test_infer_axioms_all(mock_stop_jvm):
    with TestClient(create_app(ontology_path, reasoner_name)) as client:
        response = client.post("/infer_axioms", json={"inference_type": "all"})
        assert response.status_code == 200
        
        expected_axioms = []
        for inference_type in InferenceType:
            if inference_type != InferenceType.All:
                expected_axioms.extend(reasoner.infer_axioms(inference_type.value))
        
        assert set(response.json()["inferred_axioms"]) == set([axiom.__str__() for axiom in expected_axioms])
