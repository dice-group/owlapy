from abc import ABC, abstractmethod
from typing import List, Tuple, Generator, Union
from owlapy.class_expression import OWLClassExpression
from owlapy.owl_neural_reasoners.neural_ontology_manager import NeuralOntologyManager
from owlapy.owl_ontology import AbstractOWLOntology

class AbstractNeuralReasoner(ABC):
    """Abstract class for Neural Reasoners that operate on OWL Class Expressions using embeddings."""
    @abstractmethod
    def __init__(self, ontology: Union[NeuralOntologyManager, AbstractOWLOntology], **kwargs):
        pass 

    @abstractmethod
    def predict(self, h: str = None, r: str = None, t: str = None) -> List[Tuple[str, float]]:
        """Predict triples (h, r, t) with a likelihood score."""
        pass
    
    @abstractmethod
    def instances(self, expression: OWLClassExpression, **kwargs) -> Generator:
        """Retrieve instances of a given OWL class expression."""
        pass

    @abstractmethod
    def classes_in_signature(self) -> List:
        """Retrieve all OWL classes in the knowledge base."""
        pass

    @abstractmethod
    def individuals_in_signature(self) -> List:
        """Retrieve all individuals in the knowledge base."""
        pass

    @abstractmethod
    def object_properties_in_signature(self) -> List:
        """Retrieve all object properties in the knowledge base."""
        pass

    @abstractmethod
    def data_properties_in_signature(self) -> List:
        """Retrieve all data properties in the knowledge base."""
        pass
    #TODO LF: Maybe we can define more methods or remove some of them -> depending on concrete implementations.