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


    

