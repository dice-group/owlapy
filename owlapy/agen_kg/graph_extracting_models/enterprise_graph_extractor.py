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
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_ontology import Ontology
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty
from owlapy.agen_kg.signatures import (
    Entity, Triple, TypeAssertion, TypeGeneration, Literal, SPLTriples,  Enterprise, EnterpriseSpecificFewShotGenerator
)
from owlapy.agen_kg.helper import extract_hierarchy_from_dbpedia
from owlapy.agen_kg.graph_extractor import GraphExtractor

# TODO: Problems to fix
#      - Entity extraction is bad, most things that are considered entities (individuals) are not fit to be called an
#        entity but rather just string values for data properties.
#      - In enterprise graphs we should therefore focus more on data properties than object properties.

class EnterpriseGraphExtractor(GraphExtractor):
    """
    A module to extract enterprise RDF graphs from text input.
    Tailored for organizational knowledge representation.
    Supports automatic chunking for large texts that exceed the LLM's context window.
    """
    def __init__(self, enable_logging=False, enterprise_context: str = None):
        """
        Initialize the EnterpriseGraphExtractor.

        Args:
            enable_logging: Whether to enable logging.
        """
        super().__init__(enable_logging)
        self.enterprise_detector = dspy.Predict(Enterprise)
        self.few_shot_generator = dspy.Predict(EnterpriseSpecificFewShotGenerator)
        self.entity_extractor = dspy.Predict(Entity)
        self.triples_extractor = dspy.Predict(Triple)
        self.type_asserter = dspy.Predict(TypeAssertion)
        self.type_generator = dspy.Predict(TypeGeneration)
        self.literal_extractor = dspy.Predict(Literal)
        self.spl_triples_extractor = dspy.Predict(SPLTriples)
        self.context = enterprise_context


    def generate_enterprise_specific_examples(self, enterprise: str):
        """
        Generate enterprise-specific few-shot examples for all task types.

        Args:
            enterprise: The enterprise context for which to generate examples.

        Returns:
            Dictionary containing few-shot examples for each task type, keyed by:
            'entity_extraction', 'triples_extraction', 'type_assertion', 'type_generation',
            'literal_extraction', 'triples_with_numeric_literals_extraction'
        """
        examples = {}
        task_types = [
            'entity_extraction',
            'triples_extraction',
            'type_assertion',
            'type_generation',
            'literal_extraction',
            'triples_with_numeric_literals_extraction'
        ]

        if self.logging:
            print("EnterpriseGraphExtractor: INFO :: Generating enterprise-specific few-shot examples")

        for task_type in task_types:
            result = self.few_shot_generator(
                enterprise=enterprise,
                task_type=task_type,
                num_examples=2
            )
            examples[task_type] = result.few_shot_examples
            if self.logging:
                print(f"EnterpriseGraphExtractor: INFO :: Generated examples for {task_type}")

        return examples


    def generate_ontology(self, text: Union[str, Path],
                          context: str = None,
                          ontology_namespace = f"http://ontology.local/{uuid.uuid4()}#",
                          entity_types: List[str]=None,
                          generate_types=False,
                          extract_spl_triples=False,
                          create_class_hierarchy=False,
                          entity_clustering=True,
                          use_chunking: bool = None,
                          fact_reassurance: bool = True,
                          save_path="generated_ontology.owl") -> Ontology:
        """
        Generate an enterprise ontology from text.

        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            text: Input text or file path to extract ontology from.
                Supports files: .txt, .pdf, .docx, .doc, .rtf, .html, .htm
            context: The enterprise context. If None, will be detected automatically.
            ontology_namespace: Namespace for the ontology.
            entity_types: List of entity types to assign (e.g., Department, Employee, Project).
            generate_types: Whether to generate types automatically.
            extract_spl_triples: Whether to extract subject-property-literal triples.
            create_class_hierarchy: Whether to create class hierarchy from DBpedia.
            entity_clustering: Whether to perform entity clustering.
            use_chunking: Whether to use text chunking for large documents.
            fact_reassurance: Whether to enforce as step of fact checking after triple extraction.
                - None (default): Auto-detect based on text size (uses auto_chunk_threshold).
                - True: Force chunking even for smaller texts.
                - False: Disable chunking (may fail for very large texts).
            save_path: Path to save the ontology.


        Returns:
            Generated Ontology object.
        """
        # Load text from file if necessary
        if isinstance(text, (str, Path)):
            source_path = Path(text) if not isinstance(text, Path) else text
            if source_path.is_file():
                text = self.load_text(text)

        # Determine whether to use chunking
        if use_chunking is None:
            use_chunking = self.should_chunk_text(text)

        if use_chunking:
            chunks = self.chunk_text(text)
            if self.logging:
                chunk_info = self.get_chunking_info(text)
                print(f"EnterpriseGraphExtractor: INFO :: Text will be processed in {chunk_info['num_chunks']} chunks")
                print(f"EnterpriseGraphExtractor: INFO :: Total chars: {chunk_info['total_chars']}, "
                      f"Est. tokens: {chunk_info['estimated_tokens']}")
        else:
            chunks = [text]

        # Use a representative sample for enterprise detection
        enterprise_detection_text = text[:self.auto_chunk_threshold] if len(text) > self.auto_chunk_threshold else text

        # Step 1: Detect enterprise if not provided
        if context is None:
            enterprise_result = self.enterprise_detector(text=enterprise_detection_text)
            context = enterprise_result.context
            if self.logging:
                print(f"EnterpriseGraphExtractor: INFO :: Extracted enterprise context: {context}")
        else:
            if self.logging:
                print(f"EnterpriseGraphExtractor: INFO :: Using provided enterprise context: {context}")


        generated_examples = self.generate_enterprise_specific_examples(context)

        # Use generated examples only if user hasn't provided their own
        examples_for_entity_extraction = generated_examples['entity_extraction']
        examples_for_triples_extraction = generated_examples['triples_extraction']
        examples_for_type_assertion = generated_examples['type_assertion']
        examples_for_type_generation = generated_examples['type_generation']
        examples_for_literal_extraction = generated_examples['literal_extraction']
        examples_for_spl_triples_extraction = generated_examples['triples_with_numeric_literals_extraction']

        # Step 3: Extract entities (from chunks if needed)
        if self.logging:
            print("EnterpriseGraphExtractor: INFO :: Extracting enterprise ontology from organizational text")

        chunk_summaries = None
        if use_chunking and len(chunks) > 1:
            entities, chunk_summaries = self._extract_entities_from_chunks(
                chunks, examples_for_entity_extraction, "EnterpriseGraphExtractor"
            )
        else:
            entities = self.entity_extractor(text=text, few_shot_examples=examples_for_entity_extraction).entities

        if self.logging:
            print(f"EnterpriseGraphExtractor: INFO :: Generated the following entities: {entities}")

        # Step 4: Cluster entities
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
            print(f"EnterpriseGraphExtractor: INFO :: After clustering: {canonical_entities}")

        # Step 5: Extract triples (from chunks if needed)
        if use_chunking and len(chunks) > 1:
            triples = self._extract_triples_from_chunks(
                chunks, canonical_entities, examples_for_triples_extraction,
                "EnterpriseGraphExtractor", chunk_summaries
            )
        else:
            triples = self.triples_extractor(text=text, entities=canonical_entities,
                                            few_shot_examples=examples_for_triples_extraction).triples

        if self.logging:
            print(f"EnterpriseGraphExtractor: INFO :: Generated the following triples: {triples}")

        # Step 6: Cluster relations
        relations = list(set([triple[1] for triple in triples]))
        relation_mapping = self.cluster_relations(relations, clustering_context)
        updated_triples = [(triple[0], relation_mapping.get(triple[1], triple[1]), triple[2]) for triple in triples]

        if self.logging and len(relations) != len(set(relation_mapping.values())):
            print(f"EnterpriseGraphExtractor: INFO :: After relation clustering: {list(set(relation_mapping.values()))}")

        # Step 7: Check coherence (fact reassurance)
        if fact_reassurance:
            coherent_triples = self.check_coherence(updated_triples, clustering_context)
            if self.logging:
                print(f"EnterpriseGraphExtractor: INFO :: After coherence check, kept {len(coherent_triples)} triples")
        else:
            coherent_triples = updated_triples
            if self.logging:
                print(f"EnterpriseGraphExtractor: INFO :: Skipped coherence check, using all {len(coherent_triples)} triples")

        # Step 8: Create ontology
        onto = Ontology(ontology_iri=IRI.create("http://example.com/ontogen"), load=False)
        for triple in coherent_triples:
            subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
            prop = OWLObjectProperty(ontology_namespace + self.snake_case(triple[1]))
            object = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[2]))
            # Add triple if subject and object are canonical entities
            if triple[0] in canonical_entities and triple[2] in canonical_entities:
                ax = OWLObjectPropertyAssertionAxiom(subject, prop, object)
                onto.add_axiom(ax)

        for triple in coherent_triples:
            subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
            prop = OWLDataProperty(ontology_namespace + self.snake_case(triple[1]))
            literal = self.get_corresponding_literal(triple[2])
            if triple[0] in canonical_entities:
                ax = OWLDataPropertyAssertionAxiom(subject, prop, literal)
                try:
                    onto.add_axiom(ax)
                except Exception as e:
                    # if the property already exists as object property, skip adding as data property
                    pass

        # Step 9: Handle type assertions
        if entity_types is not None or generate_types:
            if use_chunking and len(chunks) > 1:
                type_assertions = self._extract_types_from_chunks(
                    chunks, canonical_entities, entity_types, generate_types,
                    examples_for_type_assertion, examples_for_type_generation,
                    "EnterpriseGraphExtractor", chunk_summaries
                )
            else:
                if entity_types is not None and not generate_types:
                    type_assertions = self.type_asserter(text=text, entities=canonical_entities,
                                                        entity_types=entity_types,
                                                        few_shot_examples=examples_for_type_assertion).pairs
                    if self.logging:
                        print(f"EnterpriseGraphExtractor: INFO :: Assigned types for entities: {type_assertions}")
                else:
                    type_assertions = self.type_generator(text=text, entities=canonical_entities,
                                                         few_shot_examples=examples_for_type_generation).pairs
                    if self.logging:
                        print(f"EnterpriseGraphExtractor: INFO :: Generated and assigned types: {type_assertions}")

            # Cluster types
            types = list(set([pair[1] for pair in type_assertions]))
            type_mapping = self.cluster_types(types, clustering_context)
            type_assertions = [(pair[0], type_mapping.get(pair[1], pair[1])) for pair in type_assertions]

            if self.logging and len(types) != len(set(type_mapping.values())):
                print(f"EnterpriseGraphExtractor: INFO :: After type clustering: {list(set(type_mapping.values()))}")

            for pair in type_assertions:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(pair[0]))
                entity_type = OWLClass(ontology_namespace + self.snake_case(pair[1]))
                ax = OWLClassAssertionAxiom(subject, entity_type)
                onto.add_axiom(ax)

        # Step 10: Extract SPL triples if requested
        if extract_spl_triples:
            if use_chunking and len(chunks) > 1:
                literals = self._extract_literals_from_chunks(
                    chunks, examples_for_literal_extraction, "EnterpriseGraphExtractor"
                )
            else:
                literals = self.literal_extractor(text=text, few_shot_examples=examples_for_literal_extraction).l_values

            if self.logging:
                print(f"EnterpriseGraphExtractor: INFO :: Generated the following numeric literals: {literals}")

            if use_chunking and len(chunks) > 1:
                spl_triples = self._extract_spl_triples_from_chunks(
                    chunks, canonical_entities, literals, examples_for_spl_triples_extraction,
                    "EnterpriseGraphExtractor"
                )
            else:
                spl_triples = self.spl_triples_extractor(text=text, entities=canonical_entities,
                                                        numeric_literals=literals,
                                                        few_shot_examples=examples_for_spl_triples_extraction).triples

            if self.logging:
                print(f"EnterpriseGraphExtractor: INFO :: Generated the following s-p-l triples: {spl_triples}")

            # Cluster SPL relations
            spl_relations = list(set([triple[1] for triple in spl_triples]))
            spl_relation_mapping = self.cluster_relations(spl_relations, clustering_context)
            spl_triples = [(triple[0], spl_relation_mapping.get(triple[1], triple[1]), triple[2])
                          for triple in spl_triples]

            if self.logging and len(spl_relations) != len(set(spl_relation_mapping.values())):
                print(f"EnterpriseGraphExtractor: INFO :: After SPL relation clustering: {list(set(spl_relation_mapping.values()))}")

            for triple in spl_triples:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
                prop = OWLDataProperty(ontology_namespace + self.snake_case(triple[1]))
                literal = self.get_corresponding_literal(triple[2])
                if triple[0] in canonical_entities and triple[2] in literals:
                    try:
                        ax = OWLDataPropertyAssertionAxiom(subject, prop, literal)
                        onto.add_axiom(ax)
                    except Exception:
                        pass

        # Step 11: Create class hierarchy if requested
        if create_class_hierarchy:
            for cls in onto.classes_in_signature():
                try:
                    superclasses, subclasses = extract_hierarchy_from_dbpedia(cls.remainder)
                except Exception:
                    continue
                if self.logging:
                    print(f"EnterpriseGraphExtractor: INFO :: For class {cls.remainder} found superclasses: "
                          f"{[IRI.create(s).remainder for s in superclasses]} and subclasses: "
                          f"{[IRI.create(s).remainder for s in subclasses]}")

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

        # Step 12: Save ontology
        onto.save(path=save_path)
        if self.logging:
            print(f"EnterpriseGraphExtractor: INFO :: Successfully saved the ontology at {os.path.join(os.getcwd(),save_path)}")

        return onto

    def forward(self, text: Union[str, Path],
                context: str = None,
                ontology_namespace = f"http://ontology.local/{uuid.uuid4()}#",
                entity_types: List[str]=None,
                generate_types=False,
                extract_spl_triples=False,
                create_class_hierarchy=False,
                entity_clustering=True,
                use_chunking: bool = None,
                fact_reassurance: bool = True,
                save_path="generated_enterprise_ontology.owl") -> Ontology:
        """
        Extract an enterprise ontology from a given textual input or file.

        Supports automatic chunking for large texts that exceed the LLM's context window.

        Args:
            text (str or Path): Text input or file path from which the ontology will be extracted.
                Supports files: .txt, .pdf, .docx, .doc, .rtf, .html, .htm
            context (str): The enterprise context (e.g., 'Acme Corp', 'healthcare').
                If None, will be detected automatically from the text.
            ontology_namespace (str): Namespace to use for the ontology.
            entity_types (List[str]): List of entity types to assign to extracted entities
                (e.g., Department, Employee, Project, Policy).
                Leave empty if generate_types is True.
            generate_types (bool): Whether to generate types for extracted entities.
            extract_spl_triples (bool): Whether to extract triples of type s-p-l where l is a numeric literal.
            create_class_hierarchy (bool): Whether to create a class hierarchy for the extracted entities.
            entity_clustering (bool): Whether to perform entity clustering to merge duplicate entities.
            use_chunking (bool): Whether to use text chunking for large documents.
                - None (default): Auto-detect based on text size (uses auto_chunk_threshold).
                - True: Force chunking even for smaller texts.
                - False: Disable chunking (may fail for very large texts).
            fact_reassurance: Whether to enforce as step of fact checking after triple extraction.
            save_path (str): Path to save the generated ontology.


        Returns (Ontology): An ontology object.
        """
        if generate_types:
            assert entity_types is None, ("entity_types argument should be None "
                                          "when you want to generate types (i.e. when generate_types = True)")

        return self.generate_ontology(
            text=text,
            context=context,
            ontology_namespace=ontology_namespace,
            entity_types=entity_types,
            generate_types=generate_types,
            extract_spl_triples=extract_spl_triples,
            create_class_hierarchy=create_class_hierarchy,
            entity_clustering=entity_clustering,
            use_chunking=use_chunking,
            save_path=save_path,
            fact_reassurance=fact_reassurance
        )