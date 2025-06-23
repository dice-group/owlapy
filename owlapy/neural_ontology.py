from typing import Iterable, List, Optional, Tuple, Union, Dict, Any
from pathlib import Path
import os
from owlapy.abstracts.abstract_owl_ontology import _OI, AbstractOWLOntology
from owlapy.class_expression.owl_class import OWLClass
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLAxiom, OWLClassAxiom, OWLDataPropertyDomainAxiom, OWLDataPropertyRangeAxiom, OWLEquivalentClassesAxiom, OWLObjectPropertyDomainAxiom, OWLObjectPropertyRangeAxiom
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty
from owlapy.owl_individual import OWLNamedIndividual
from dicee.knowledge_graph_embeddings import KGE
from dicee.executer import Execute
from dicee.config import Namespace
import torch

def is_valid_entity(text_input: str):
    return True if "/" in text_input else False
class NeuralOntology(AbstractOWLOntology):
    STR_IRI_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    STR_IRI_OWL_CLASS = "http://www.w3.org/2002/07/owl#Class"
    STR_IRI_OBJECT_PROPERTY = "http://www.w3.org/2002/07/owl#ObjectProperty"
    STR_IRI_DATA_PROPERTY = "http://www.w3.org/2002/07/owl#DatatypeProperty"

    def __init__(self, path_neural_embedding: str, train_if_not_exists: bool = False, training_params: Optional[Dict[str, Any]] = None, batch_size: int = 1024, device: str = "gpu", gamma: float = 0.5):
        """
        Initialize a Neural Ontology from a KGE model.
        
        Args:
            path_neural_embedding: Path to a pretrained KGE model, a directory containing a train.txt file or a .owl file
            train_if_not_exists: If True, train a new model if no pretrained model is found at the given path
            training_params: Optional dictionary of training parameters to override defaults
        """ 

        super().__init__()
        self.gamma = gamma
        
        path = Path(path_neural_embedding)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, "configuration.json")):
            # Path leads to a folder containing pretrained model
            self.model = KGE(path=path_neural_embedding)
        elif train_if_not_exists:
            # Train a new model
            self._train_model(path_neural_embedding, training_params)
        else:
            raise ValueError(f"No pretrained KGE model found at {path_neural_embedding} and train_if_not_exists is False")
        self.batch_size = batch_size

        if device == "gpu" and torch.cuda.is_available():
            self.model.to("cuda")
            print("EBR inference on GPU")
        elif device == "cpu":
            self.model.to("cpu")
            print("EBR inference on CPU")
        else:
            # warning 
            print(f"Device {device} not supported, EBR will use CPU")

    def _train_model(self, path: str, training_params: Optional[Dict[str, Any]] = None):
        """
        Train a new KGE model with the given parameters.
        
        Args:
            path: Path to a directory containing train.txt or to the dataset directory
            training_params: Optional dictionary of training parameters
        """
        args = Namespace()
        
        # Set default parameters
        args.model = 'Keci'
        args.scoring_technique = "AllvsAll"
        if os.path.isdir(path):
            args.dataset_dir = path
            args.path_single_kg = None
        else:
            args.path_single_kg = path
            if path.endswith(".owl"):
                args.backend = "rdflib"
            path = os.path.dirname(path)
        
        args.trainer = "PL"
        # Always include the file name in the path
        file_name = os.path.basename(args.path_single_kg).replace(".owl", "")
        args.path_to_store_single_run = os.path.join(path, f"{file_name}_trained_model")
        args.num_epochs = 500
        args.embedding_dim = 512
        args.batch_size = 64
        
        # Override with user-provided parameters if any
        if training_params is not None:
            for key, value in training_params.items():
                setattr(args, key, value)
        
        # Train the model
        Execute(args).start()
        
        # Load the trained model
        self.model = KGE(path=args.path_to_store_single_run)

    def predict(self, h: List[str] = None, r: List[str] = None, t: List[str] = None) -> List[Tuple[str,float]]:
        if r is None:
            topk = len(self.model.relation_to_idx)
        else:
            topk = len(self.model.entity_to_idx)

        return [ (top_entity, score) for row in self.model.predict_topk(h=h, r=r, t=t, topk=topk, batch_size=self.batch_size) for top_entity, score in row if score >= self.gamma and is_valid_entity(top_entity)]

    def classes_in_signature(self) -> List[OWLClass]:
        return [OWLClass(top_entity) for top_entity, score in self.predict(h=None,
                                                                   r=self.STR_IRI_TYPE,
                                                                   t=self.STR_IRI_OWL_CLASS)]
    
    def individuals_in_signature(self) -> List[OWLNamedIndividual]:
        set_str_entities=set()
        for top_entity, score in self.predict(h=None,
                                                  r=self.STR_IRI_TYPE,
                                                  t=[owl_class.iri.str for owl_class in self.classes_in_signature()]):
            set_str_entities.add(top_entity)
        return [OWLNamedIndividual(entity) for entity in set_str_entities]

    def data_properties_in_signature(self) -> List[OWLDataProperty]:
        return [OWLDataProperty(top_entity) for top_entity, score in self.predict(h=None,
                                                     r=self.STR_IRI_TYPE,
                                                     t=self.STR_IRI_DATA_PROPERTY)]

    def object_properties_in_signature(self) -> List[OWLObjectProperty]:
        return [OWLObjectProperty(top_entity) for top_entity, score in self.predict(h=None,
                                                     r=self.STR_IRI_TYPE,
                                                     t=self.STR_IRI_OBJECT_PROPERTY)]

    def equivalent_classes_axioms(self, c: OWLClass) -> Iterable[OWLEquivalentClassesAxiom]:
        raise NotImplementedError("Not implemented")
    
    def general_class_axioms(self) -> Iterable[OWLClassAxiom]:
        raise NotImplementedError("Not implemented")
    
    def data_property_domain_axioms(self, property: OWLDataProperty) -> Iterable[OWLDataPropertyDomainAxiom]:
        raise NotImplementedError("Not implemented")
    
    def data_property_range_axioms(self, property: OWLDataProperty) -> Iterable[OWLDataPropertyRangeAxiom]:
        raise NotImplementedError("Not implemented")
    
    def object_property_domain_axioms(self, property: OWLObjectProperty) -> Iterable[OWLObjectPropertyDomainAxiom]:
        raise NotImplementedError("Not implemented")

    def get_ontology_id(self) -> _OI:
        raise NotImplementedError("Not implemented")
    
    #LF: here we would need to retrain? -> ie we would need to store / have the path for the underlying ontology?
    def add_axiom(self, axiom: Union[OWLAxiom, Iterable[OWLAxiom]]):
        raise NotImplementedError("Not implemented")
    
    def remove_axiom(self, axiom: Union[OWLAxiom, Iterable[OWLAxiom]]):
        raise NotImplementedError("Not implemented")

    def save(self, document_iri: Optional[IRI] = None):
        raise NotImplementedError("Not implemented")
    
    def __eq__(self, other):
        return self.model == other.model
    
    def __hash__(self):
        return hash(self.model)
    
    def __repr__(self):
        return f"NeuralOntology(model={self.model})"
    
    def object_property_range_axioms(self, property: OWLObjectProperty) -> Iterable[OWLObjectPropertyRangeAxiom]:
        raise NotImplementedError("Not implemented")
    

