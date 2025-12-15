from typing import List, Union
import os
import dspy
import uuid
from pathlib import Path


from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLObjectPropertyAssertionAxiom, OWLClassAssertionAxiom, OWLDataPropertyAssertionAxiom, \
    OWLSubClassOfAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral, StringOWLDatatype
from owlapy.owl_ontology import Ontology
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty
from owlapy.agen_kg.signatures import (
    Entity, Triple, TypeAssertion, TypeGeneration, Literal, SPLTriples, Domain,
)
from owlapy.agen_kg.helper import extract_hierarchy_from_dbpedia
from owlapy.agen_kg.graph_extractor import GraphExtractor


class CrossDomainGraphExtractor(GraphExtractor):
    """
    A module to extract cross-domain RDF graphs from text input.
    Handles content that spans multiple related domains.
    Supports automatic chunking for large texts that exceed the LLM's context window.
    """
    def __init__(self, enable_logging=False):
        super().__init__(enable_logging)
        self.domain_detector = dspy.Predict(Domain)
        self.entity_extractor = dspy.Predict(Entity)
        self.triples_extractor = dspy.Predict(Triple)
        self.type_asserter = dspy.Predict(TypeAssertion)
        self.type_generator = dspy.Predict(TypeGeneration)
        self.literal_extractor = dspy.Predict(Literal)
        self.spl_triples_extractor = dspy.Predict(SPLTriples)

    def generate_ontology(self, text: Union[str, Path],
                          ontology_namespace = f"http://ontology.local/{uuid.uuid4()}#",
                          entity_types: List[str]=None,
                          generate_types=False,
                          extract_spl_triples=False,
                          create_class_hierarchy=False,
                          entity_clustering=True,
                          use_chunking: bool = None,
                          save_path="generated_ontology.owl") -> Ontology:
        """
        Generate a cross-domain ontology from text.

        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            text: Input text or file path to extract ontology from.
                Supports files: .txt, .pdf, .docx, .doc, .rtf, .html, .htm
            ontology_namespace: Namespace for the ontology.
            entity_types: List of entity types to assign.
            generate_types: Whether to generate types automatically.
            extract_spl_triples: Whether to extract subject-property-literal triples.
            create_class_hierarchy: Whether to create class hierarchy from DBpedia.
            entity_clustering: Whether to perform entity clustering.
            use_chunking: Whether to use text chunking for large documents.
                - None (default): Auto-detect based on text size (uses auto_chunk_threshold).
                - True: Force chunking even for smaller texts.
                - False: Disable chunking (may fail for very large texts).
            examples_for_*: Few-shot examples for various extraction tasks.
            save_path: Path to save the ontology.

        Returns:
            Generated Ontology object.
        """
        # TODO
        pass

    def forward(self, text: Union[str, Path],
                ontology_namespace = f"http://ontology.local/{uuid.uuid4()}#",
                entity_types: List[str]=None,
                generate_types=False,
                extract_spl_triples=False,
                create_class_hierarchy=False,
                entity_clustering=True,
                use_chunking: bool = None,
                save_path="generated_ontology.owl") -> Ontology:
        """
        Extract a cross-domain ontology from a given textual input or file.

        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            text (str or Path): Text input or file path from which the ontology will be extracted.
                Supports files: .txt, .pdf, .docx, .doc, .rtf, .html, .htm
            ontology_namespace (str): Namespace to use for the ontology.
            entity_types (List[str]): List of entity types to assign to extracted entities.
                Leave empty if generate_types is True.
            generate_types (bool): Whether to generate types for extracted entities.
            extract_spl_triples (bool): Whether to extract triples of type s-p-l where l is a numeric literal.
            create_class_hierarchy (bool): Whether to create a class hierarchy for the extracted entities.
            entity_clustering (bool): Whether to perform entity clustering to merge duplicate entities.
            use_chunking (bool): Whether to use text chunking for large documents.
                - None (default): Auto-detect based on text size (uses auto_chunk_threshold).
                - True: Force chunking even for smaller texts.
                - False: Disable chunking (may fail for very large texts).
            save_path (str): Path to save the generated ontology.

        Returns (Ontology): An ontology object.
        """
        if generate_types:
            assert entity_types is None, ("entity_types argument should be None "
                                          "when you want to generate types (i.e. when generate_types = True)")

        return self.generate_ontology(
            text=text,
            ontology_namespace=ontology_namespace,
            entity_types=entity_types,
            generate_types=generate_types,
            extract_spl_triples=extract_spl_triples,
            create_class_hierarchy=create_class_hierarchy,
            entity_clustering=entity_clustering,
            use_chunking=use_chunking,
            save_path=save_path
        )
