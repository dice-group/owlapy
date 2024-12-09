from owlapy.owl_ontology_manager import OntologyManager
from dicee.knowledge_graph_embeddings import KGE

# LF: for now functions same as normal OntologyManager (+ can return path)
class NeuralOntologyManager(OntologyManager):
	def __init__(self, world_store=None):
		super().__init__(world_store) 
	
	def load_ontology(self, path: str = None):
		self._path = path
		return super().load_ontology(path)

	def load_neural_embedding(self, path: str = None):
		self._path_neural_embedding = path	
		return KGE(path)

	def get_path(self) -> str:
		if hasattr(self, '_path'):
			return self._path
		else:
			return None
	
	def get_path_neural_embedding(self) -> str:
		if hasattr(self, '_path_neural_embedding'):
			return self._path_neural_embedding
		else:
			return None
