import os
import argparse
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from owlapy.owl_ontology_manager import SyncOntologyManager
from owlapy.owl_reasoner import SyncReasoner
from owlapy.class_expression import OWLClass
from owlapy.static_funcs import stopJVM
from contextlib import asynccontextmanager
from enum import Enum

ontology = None
reasoner = None

class InferenceType(str, Enum):
    InferredClassAssertionAxiomGenerator = "InferredClassAssertionAxiomGenerator"
    InferredSubClassAxiomGenerator = "InferredSubClassAxiomGenerator"
    InferredDisjointClassesAxiomGenerator = "InferredDisjointClassesAxiomGenerator"
    InferredEquivalentClassAxiomGenerator = "InferredEquivalentClassAxiomGenerator"
    InferredEquivalentDataPropertiesAxiomGenerator = "InferredEquivalentDataPropertiesAxiomGenerator"
    InferredEquivalentObjectPropertyAxiomGenerator = "InferredEquivalentObjectPropertyAxiomGenerator"
    InferredInverseObjectPropertiesAxiomGenerator = "InferredInverseObjectPropertiesAxiomGenerator"
    InferredSubDataPropertyAxiomGenerator = "InferredSubDataPropertyAxiomGenerator"
    InferredSubObjectPropertyAxiomGenerator = "InferredSubObjectPropertyAxiomGenerator"
    InferredDataPropertyCharacteristicAxiomGenerator = "InferredDataPropertyCharacteristicAxiomGenerator"
    InferredObjectPropertyCharacteristicAxiomGenerator = "InferredObjectPropertyCharacteristicAxiomGenerator"
    All = "all"

class InfrenceTypeRequest(BaseModel):
    inference_type: InferenceType

class ClassIRIRequest(BaseModel):
    class_iri: str

def create_app(ontology_path: str, reasoner_name: str):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global ontology, reasoner
        # Startup logic
        # Load the ontology
        if not os.path.exists(ontology_path):
            raise FileNotFoundError(f"Ontology file not found at {ontology_path}")
        ontology = SyncOntologyManager().load_ontology(ontology_path)

        # Validate and initialize the reasoner
        valid_reasoners = ['Pellet', 'HermiT', 'JFact', 'Openllet']
        if reasoner_name not in valid_reasoners:
            raise ValueError(f"Invalid reasoner '{reasoner_name}'. Valid options are: {', '.join(valid_reasoners)}")
        reasoner = SyncReasoner(ontology=ontology, reasoner=reasoner_name)

        yield
        stopJVM()

    app = FastAPI(title="OWLAPY API", lifespan=lifespan)

    @app.post("/instances")
    async def get_instances(request: ClassIRIRequest):
        class_iri = request.class_iri
        owl_class = OWLClass(class_iri)
        instances = reasoner.instances(owl_class, direct=False)
        instance_iris = [ind.__str__() for ind in instances]
        return {"instances": instance_iris}

    @app.get("/classes")
    async def get_classes():
        classes = [cls.__str__() for cls in ontology.classes_in_signature()]
        return {"classes": classes}

    @app.get("/individuals")
    async def get_individuals():
        individuals = [ind.__str__() for ind in ontology.individuals_in_signature()]
        return {"individuals": individuals}

    @app.get("/abox")
    async def get_abox():
        abox = ontology.get_abox_axioms()
        return {"abox": [axiom.__str__() for axiom in abox]}

    @app.get("/tbox")
    async def get_tbox():
        tbox = ontology.get_tbox_axioms()
        return {"tbox": [axiom.__str__() for axiom in tbox]}
        
    @app.post("/infer_axioms")
    async def infer_axioms(request: InfrenceTypeRequest):
        inference_type = request.inference_type
        if inference_type == InferenceType.All:
            inferred_axioms = []
            for inference_type in {it for it in InferenceType if it != InferenceType.All}:
                inferred_axioms.extend(reasoner.infer_axioms(inference_type.value))
        else:
            inferred_axioms = reasoner.infer_axioms(request.inference_type.value)

        return {"inferred_axioms": [axiom.__str__() for axiom in inferred_axioms]}

    return app

def main():
    parser = argparse.ArgumentParser(description='Start OWLAPY API server.')
    parser.add_argument('--path_kb', type=str, required=True,
                        help='Path to the ontology file')
    parser.add_argument('--reasoner', type=str, default='HermiT',
                        help='Reasoner to use (Pellet, HermiT, JFact, Openllet)')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                        help='Host to listen on')
    parser.add_argument('--port', type=int, default=8000,
                        help='Port to listen on')
    args = parser.parse_args()

    app = create_app(args.path_kb, args.reasoner)
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == '__main__':
    main()
