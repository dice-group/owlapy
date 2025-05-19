from typing import Iterable, Optional, Union
from owlapy.abstracts.abstract_owl_ontology import _OI, AbstractOWLOntology
from owlapy.class_expression.owl_class import OWLClass
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLAxiom, OWLClassAxiom, OWLDataPropertyDomainAxiom, OWLDataPropertyRangeAxiom, OWLEquivalentClassesAxiom, OWLObjectPropertyDomainAxiom, OWLObjectPropertyRangeAxiom
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty
from owlapy.owl_individual import OWLNamedIndividual
from dicee.knowledge_graph_embeddings import KGE

class NeuralOntology(AbstractOWLOntology):
	def __init__(self, path_neural_embedding: str):
		super().__init__()
		self.model = KGE(path=path_neural_embedding)

	def classes_in_signature(self) -> Iterable[OWLClass]:
		raise NotImplementedError("Not implemented")

	def data_properties_in_signature(self) -> Iterable[OWLDataProperty]:
		raise NotImplementedError("Not implemented")

	def object_properties_in_signature(self) -> Iterable[OWLObjectProperty]:
		raise NotImplementedError("Not implemented")

	def individuals_in_signature(self) -> Iterable[OWLNamedIndividual]:
		raise NotImplementedError("Not implemented")

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
	
	#LF: here we would need to retrain?
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
	
	
