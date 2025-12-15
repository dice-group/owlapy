from typing import List, Union
import os
import dspy
import uuid
from pathlib import Path

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.ontogen.few_shot_examples import EXAMPLES_FOR_ENTITY_EXTRACTION, EXAMPLES_FOR_TRIPLES_EXTRACTION, \
    EXAMPLES_FOR_TYPE_ASSERTION, EXAMPLES_FOR_TYPE_GENERATION, EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION, \
    EXAMPLES_FOR_LITERAL_EXTRACTION
from owlapy.owl_axiom import OWLObjectPropertyAssertionAxiom, OWLClassAssertionAxiom, OWLDataPropertyAssertionAxiom, \
    OWLSubClassOfAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral, StringOWLDatatype
from owlapy.owl_ontology import Ontology
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty
from owlapy.agen_kg.signatures import Entity, Triple, TypeAssertion, TypeGeneration, Literal, SPLTriples
from owlapy.agen_kg.helper import extract_hierarchy_from_dbpedia
from owlapy.agen_kg.graph_extractor import GraphExtractor


class OpenGraphExtractor(GraphExtractor):
    def __init__(self, enable_logging=False):
        """
        A module to extract an RDF graph from a given text input.
        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            enable_logging: Whether to enable logging.
        """
        super().__init__(enable_logging)
        self.entity_extractor = dspy.Predict(Entity)
        self.triples_extractor = dspy.Predict(Triple)
        self.type_asserter = dspy.Predict(TypeAssertion)
        self.type_generator = dspy.Predict(TypeGeneration)
        self.literal_extractor = dspy.Predict(Literal)
        self.spl_triples_extractor = dspy.Predict(SPLTriples)

    def generate_ontology(self, text: Union[str, Path], ontology_namespace=f"http://ontology.local/{uuid.uuid4()}#",
                          entity_types: List[str] = None,
                          generate_types=False,
                          extract_spl_triples=False,
                          create_class_hierarchy=False,
                          entity_clustering=True,
                          use_chunking: bool = None,
                          examples_for_entity_extraction=EXAMPLES_FOR_ENTITY_EXTRACTION,
                          examples_for_triples_extraction=EXAMPLES_FOR_TRIPLES_EXTRACTION,
                          examples_for_type_assertion=EXAMPLES_FOR_TYPE_ASSERTION,
                          examples_for_type_generation=EXAMPLES_FOR_TYPE_GENERATION,
                          examples_for_literal_extraction=EXAMPLES_FOR_LITERAL_EXTRACTION,
                          examples_for_spl_triples_extraction=EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION,
                          fact_reassurance=True,
                          save_path="generated_ontology.owl") -> Ontology:
        """
        Generate an ontology from the given text or file.

        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            text: Input text or file path.
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
            examples_for_entity_extraction: Few-shot examples for entity extraction.
            examples_for_triples_extraction: Few-shot examples for triple extraction.
            examples_for_type_assertion: Few-shot examples for type assertion.
            examples_for_type_generation: Few-shot examples for type generation and assertion.
            examples_for_literal_extraction: Few-shot examples for literal extraction.
            examples_for_spl_triples_extraction: Few-shot examples for s-p-l triples extraction.
            fact_reassurance: Whether to enforce as step of fact checking after triple extraction.
            save_path: Path to save the ontology.

        Returns:
            Generated Ontology object.
        """
        # Load text from file if necessary
        if isinstance(text, (str, Path)):
            # Check if it's a file path
            source_path = Path(text) if not isinstance(text, Path) else text
            if source_path.is_file():
                text = self.load_text(text)
            # else: treat as raw text string

        # Determine whether to use chunking
        if use_chunking is None:
            use_chunking = self.should_chunk_text(text)

        if use_chunking:
            chunks = self.chunk_text(text)
            if self.logging:
                chunk_info = self.get_chunking_info(text)
                print(f"OpenGraphExtractor: INFO :: Text will be processed in {chunk_info['num_chunks']} chunks")
                print(f"OpenGraphExtractor: INFO :: Total chars: {chunk_info['total_chars']}, "
                      f"Est. tokens: {chunk_info['estimated_tokens']}")
        else:
            chunks = [text]

        if self.logging:
            print("GraphExtractor: INFO  :: In the generated triples, you may see entities or literals that were not"
                  "part of the extracted entities or literals. They are filtered before added to the ontology.")

        # Step 1: Extract entities (from chunks if needed)
        chunk_summaries = None  # Will be populated during chunked extraction
        if use_chunking and len(chunks) > 1:
            entities, chunk_summaries = self._extract_entities_from_chunks(chunks, examples_for_entity_extraction)
        else:
            entities = self.entity_extractor(text=text, few_shot_examples=examples_for_entity_extraction).entities

        if self.logging:
            print(f"GraphExtractor: INFO  :: Generated the following entities: {entities}")

        # Step 2: Cluster entities to identify and merge duplicates
        # For chunked processing, use combined summary or generate clustering context
        if chunk_summaries:
            clustering_context = self.create_combined_summary(chunk_summaries)
        else:
            clustering_context = self.get_clustering_context(text)

        if entity_clustering:
            entity_mapping = self.cluster_entities(entities, clustering_context)
            canonical_entities = list(set(entity_mapping.values()))
        else:
            canonical_entities = entities
        if self.logging and len(entities) != len(canonical_entities):
            print(f"GraphExtractor: INFO  :: After clustering: {canonical_entities}")

        # Step 3: Extract triples using canonical entities (from chunks if needed)
        if use_chunking and len(chunks) > 1:
            triples = self._extract_triples_from_chunks(chunks, canonical_entities, examples_for_triples_extraction,
                                                        chunk_summaries=chunk_summaries)
        else:
            triples = self.triples_extractor(text=text, entities=canonical_entities,
                                             few_shot_examples=examples_for_triples_extraction).triples

        if self.logging:
            print(f"GraphExtractor: INFO  :: Generated the following triples: {triples}")

        # Step 3.5: Cluster relations (object properties) and update triples programmatically BEFORE coherence check
        relations = list(set([triple[1] for triple in triples]))
        relation_mapping = self.cluster_relations(relations, clustering_context)
        # Update triples with canonical relations
        updated_triples = [(triple[0], relation_mapping.get(triple[1], triple[1]), triple[2]) for triple in triples]
        if self.logging and len(relations) != len(set(relation_mapping.values())):
            print(f"GraphExtractor: INFO  :: After relation clustering: {list(set(relation_mapping.values()))}")

        # Step 4: Check coherence of the relation-normalized triples
        # For chunked text, use a summary for coherence checking
        if fact_reassurance:
            coherent_triples = self.check_coherence(updated_triples, clustering_context)
            if self.logging:
                print(f"OpenGraphExtractor: INFO :: After coherence check, kept {len(coherent_triples)} triples")
        else:
            coherent_triples = updated_triples
            if self.logging:
                print(f"OpenGraphExtractor: INFO :: Skipped coherence check, using all {len(coherent_triples)} triples")


        # Step 5: Create an ontology and load it with extracted triples
        onto = Ontology(ontology_iri=IRI.create("http://example.com/ontogen"), load=False)
        for triple in coherent_triples:
            subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
            prop = OWLObjectProperty(ontology_namespace + self.snake_case(triple[1]))
            object = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[2]))
            if triple[0] in canonical_entities and triple[2] in canonical_entities:
                ax = OWLObjectPropertyAssertionAxiom(subject, prop, object)
                onto.add_axiom(ax)

        # If user wants to set types, do so depending on the arguments
        if entity_types is not None or generate_types:
            type_assertions = None

            # Extract types (from chunks if needed)
            if use_chunking and len(chunks) > 1:
                type_assertions = self._extract_types_from_chunks(
                    chunks, canonical_entities, entity_types, generate_types,
                    examples_for_type_assertion, examples_for_type_generation,
                    chunk_summaries=chunk_summaries
                )
            else:
                # The user has specified a preset list of types
                if entity_types is not None and not generate_types:
                    type_assertions = self.type_asserter(text=text, entities=canonical_entities,
                                                         entity_types=entity_types,
                                                         few_shot_examples=examples_for_type_assertion).pairs
                    if self.logging:
                        print(f"GraphExtractor: INFO  :: Assigned types for entities as following: {type_assertions}")
                # The user wishes to leave it to the LLM to generate and assign types
                elif generate_types:
                    type_assertions = self.type_generator(text=text, entities=canonical_entities,
                                                          few_shot_examples=examples_for_type_generation).pairs
                    if self.logging:
                        print(
                            f"GraphExtractor: INFO  :: Finished generating types and assigned them to entities as following: {type_assertions}")

            # Cluster types and update type assertions programmatically
            types = list(set([pair[1] for pair in type_assertions]))
            type_mapping = self.cluster_types(types, clustering_context)
            # Update type assertions with canonical types
            type_assertions = [(pair[0], type_mapping.get(pair[1], pair[1])) for pair in type_assertions]
            if self.logging and len(types) != len(set(type_mapping.values())):
                print(f"GraphExtractor: INFO  :: After type clustering: {list(set(type_mapping.values()))}")

            # Add class assertion axioms
            for pair in type_assertions:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(pair[0]))
                entity_type = OWLClass(ontology_namespace + self.snake_case(pair[1]))
                ax = OWLClassAssertionAxiom(subject, entity_type)
                try:
                    onto.add_axiom(ax)
                except Exception as e:
                    print(e)
                    print(f"Subject: {subject}, Entity Type: {entity_type}")

        # Extract triples of type s-p-l where l is a numeric literal, including dates.
        if extract_spl_triples:
            # Extract literals (from chunks if needed)
            if use_chunking and len(chunks) > 1:
                literals = self._extract_literals_from_chunks(chunks, examples_for_literal_extraction)
            else:
                literals = self.literal_extractor(text=text, few_shot_examples=examples_for_literal_extraction).l_values

            if self.logging:
                print(f"GraphExtractor: INFO  :: Generated the following numeric literals: {literals}")

            # Extract SPL triples (from chunks if needed)
            if use_chunking and len(chunks) > 1:
                spl_triples = self._extract_spl_triples_from_chunks(
                    chunks, canonical_entities, literals, examples_for_spl_triples_extraction
                )
            else:
                spl_triples = self.spl_triples_extractor(text=text, entities=canonical_entities,
                                                         numeric_literals=literals,
                                                         few_shot_examples=examples_for_spl_triples_extraction).triples

            if self.logging:
                print(f"GraphExtractor: INFO  :: Generated the following s-p-l triples: {spl_triples}")

            # Cluster relations (data properties) in SPL triples and update programmatically
            spl_relations = list(set([triple[1] for triple in spl_triples]))
            spl_relation_mapping = self.cluster_relations(spl_relations, clustering_context)
            # Update SPL triples with canonical relations
            spl_triples = [(triple[0], spl_relation_mapping.get(triple[1], triple[1]), triple[2])
                           for triple in spl_triples]
            if self.logging and len(spl_relations) != len(set(spl_relation_mapping.values())):
                print(
                    f"GraphExtractor: INFO  :: After SPL relation clustering: {list(set(spl_relation_mapping.values()))}")

            for triple in spl_triples:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
                prop = OWLDataProperty(ontology_namespace + self.snake_case(triple[1]))
                literal = OWLLiteral(str(self.snake_case(triple[2])),
                                     type_=StringOWLDatatype)  # for now every literal will be represented as a string
                if triple[2] in literals:
                    ax = OWLDataPropertyAssertionAxiom(subject, prop, literal)
                    onto.add_axiom(ax)

        if create_class_hierarchy:
            for cls in onto.classes_in_signature():
                try:
                    superclasses, subclasses = extract_hierarchy_from_dbpedia(cls.remainder)
                except Exception:
                    continue
                if self.logging:
                    print(
                        f"GraphExtractor: INFO  :: For class {cls.remainder} found superclasses: {[IRI.create(s).remainder for s in superclasses]} and subclasses: {[IRI.create(s).remainder for s in subclasses]}")

                for superclass in superclasses:
                    dbpedia_class_remainder = IRI.create(superclass).remainder
                    sup_cls = OWLClass(ontology_namespace + dbpedia_class_remainder)
                    ax = OWLSubClassOfAxiom(cls, sup_cls)
                    onto.add_axiom(ax)
                for subclass in subclasses:
                    dbpedia_class_remainder = IRI.create(subclass).remainder
                    sub_cls = OWLClass(ontology_namespace + dbpedia_class_remainder)
                    ax = OWLSubClassOfAxiom(sub_cls, cls)
                    onto.add_axiom(ax)

        onto.save(path=save_path)
        if self.logging:
            print(f"GraphExtractor: INFO  :: Successfully saved the ontology at {os.path.join(os.getcwd(), save_path)}")

        return onto

    def forward(self, text: Union[str, Path],
                ontology_namespace=f"http://ontology.local/{uuid.uuid4()}#",
                entity_types: List[str] = None,
                generate_types=False,
                extract_spl_triples=False,
                create_class_hierarchy=False,
                entity_clustering=True,
                use_chunking: bool = None,
                examples_for_entity_extraction=EXAMPLES_FOR_ENTITY_EXTRACTION,
                examples_for_triples_extraction=EXAMPLES_FOR_TRIPLES_EXTRACTION,
                examples_for_type_assertion=EXAMPLES_FOR_TYPE_ASSERTION,
                examples_for_type_generation=EXAMPLES_FOR_TYPE_GENERATION,
                examples_for_literal_extraction=EXAMPLES_FOR_LITERAL_EXTRACTION,
                examples_for_spl_triples_extraction=EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION,
                fact_reassurance=True,
                save_path="generated_ontology.owl") -> Ontology:

        """
        Extract an ontology from a given textual input or file.

        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            text (str or Path): Text input or file path from which the ontology will be extracted.
                Supports files: .txt, .pdf, .docx, .doc, .rtf, .html, .htm
            ontology_namespace (str): Namespace to use for the ontology.
            entity_types (List[str]): List of entity types to assign.
                Leave empty if generate_types is True.
            generate_types (bool): Whether to generate types for extracted entities.
            extract_spl_triples (bool): Whether to extract triples of type s-p-l where l is a numeric literal. This
                triples will be represented using data properties and a literal value of type string (although they
                are numeric values).
            create_class_hierarchy (bool): Whether to create a class hierarchy for the extracted entities.
            entity_clustering (bool): Whether to perform entity clustering to merge duplicate entities.
            use_chunking (bool): Whether to use text chunking for large documents.
                - None (default): Auto-detect based on text size (uses auto_chunk_threshold).
                - True: Force chunking even for smaller texts.
                - False: Disable chunking (may fail for very large texts).
            examples_for_entity_extraction (str): Few-shot examples for entity extraction.
            examples_for_triples_extraction (str): Few-shot examples for triple extraction.
            examples_for_type_assertion (str): Few-shot examples for type assertion.
            examples_for_type_generation (str): Few-shot examples for type generation and assertion.
            examples_for_literal_extraction (str): Few-shot examples for literal extraction.
            examples_for_spl_triples_extraction (str): Few-shot examples for s-p-l triples extraction.
            fact_reassurance: Whether to enforce as step of fact checking after triple extraction.
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
            examples_for_entity_extraction=examples_for_entity_extraction,
            examples_for_triples_extraction=examples_for_triples_extraction,
            examples_for_type_assertion=examples_for_type_assertion,
            examples_for_type_generation=examples_for_type_generation,
            examples_for_literal_extraction=examples_for_literal_extraction,
            examples_for_spl_triples_extraction=examples_for_spl_triples_extraction,
            save_path=save_path
        )