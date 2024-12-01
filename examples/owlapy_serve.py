# To start the FastAPI server with the 'family-benchmark_rich_background.owl' ontology,
# run the following command in your terminal:
# $ owlapy-serve --path_kb KGs/Family/family-benchmark_rich_background.owl --reasoner HermiT

# Optionally, you provide custom host and port for the FastAPI server:
# $ owlapy-serve --path_kb KGs/Family/family-benchmark_rich_background.owl --reasoner HermiT --host 0.0.0.0 --port 8000
import requests

# Base URL where your FastAPI server is running
BASE_URL = 'http://localhost:8000'

# 1. Get Classes in the Ontology
print("1. Get Classes:")
response = requests.get(f'{BASE_URL}/classes')
print('Classes:', response.json())

# 2. Get Object Properties in the Ontology
print("\n2. Get Object Properties:")
response = requests.get(f'{BASE_URL}/object_properties')
print('Object Properties:', response.json())

# 3. Get Data Properties in the Ontology
print("\n3. Get Data Properties:")
response = requests.get(f'{BASE_URL}/data_properties')
print('Data Properties:', response.json())

# 4. Get Individuals in the Ontology
print("\n4. Get Individuals:")
response = requests.get(f'{BASE_URL}/individuals')
print('Individuals:', response.json())

# 5. Get ABox Axioms (Assertions about individuals)
print("\n5. Get ABox Axioms:")
response = requests.get(f'{BASE_URL}/abox')
print('ABox Axioms:', response.json())

# 6. Get TBox Axioms (Class and property definitions)
print("\n6. Get TBox Axioms:")
response = requests.get(f'{BASE_URL}/tbox')
print('TBox Axioms:', response.json())

# 7. Get Instances of a Specific Class
print("\n7. Get Instances of a Class:")
class_iri_request = {
    "class_iri": "http://www.example.org/family#Person"
}
response = requests.post(f'{BASE_URL}/instances', json=class_iri_request)
print('Instances of Class:', response.json())

# 8. Infer Axioms of a Specific Type
print("\n8. Infer Subclass Axioms:")
inference_request = {
    "inference_type": "InferredSubClassAxiomGenerator"
}
response = requests.post(f'{BASE_URL}/infer_axioms', json=inference_request)
print('Inferred Subclass Axioms:', response.json())

# 9. Infer All Types of Axioms
print("\n9. Infer All Axioms:")
inference_request = {
    "inference_type": "all"
}
response = requests.post(f'{BASE_URL}/infer_axioms', json=inference_request)
print('All Inferred Axioms:', response.json())
