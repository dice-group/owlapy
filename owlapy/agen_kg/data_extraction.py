from typing import List
import os
import dspy

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
from owlapy.agen_kg.signatures import Entity, Triple, TypeAssertion, TypeGeneration, Literal, SPLTriples, Domain, DomainSpecificFewShotGenerator
from owlapy.agen_kg.helper import extract_hierarchy_from_dbpedia


# Todo: Add different workflows for different ontology type: 1. Domain-specific, 2. Cross-domain, 3. Enterprise, 4. Open-world
# Todo: Entity clustering
# Todo: Maybe fact-checking of extracted triples for coherence
# Todo: Construct more sophisticated TBoxes



class AGenKG:
    def __init__(self, model="gpt-4o", api_key="<YOUR_GITHUB_PAT>",
                 api_base="https://models.github.ai/inference",
                 temperature=0.1, seed=42, cache=False,
                 enable_logging=False, max_tokens=4000):
        """
                A module to extract an RDF graph from a given text input.
                Args:
                    model: Model name for the LLM.
                    api_key: API key.
                    api_base: API base URL.
                    temperature: The sampling temperature to use when generating responses.
                    seed: Seed for the LLM.
                    cache: Whether to cache the model responses for reuse to improve performance and reduce costs.
                """
        super().__init__()
        lm = dspy.LM(model=f"openai/{model}", api_key=api_key,
                     api_base=api_base,
                     temperature=temperature, seed=seed, cache=cache, max_tokens=max_tokens)
        dspy.configure(lm=lm)
        self.logging = enable_logging
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.temperature = temperature
        self.seed = seed
        self.cache = cache
        self.enable_logging = enable_logging
        self.max_tokens = max_tokens

        self.open_graph_extractor = OpenGraphExtractor(self.logging)
        self.domain_graph_extractor = DomainGraphExtractor(self.logging)


    def generate_ontology(self, text, ontology_type, **kwargs):

        assert ontology_type in ["domain", "cross-domain", "enterprise", "open"], \
            "ontology_type must be one of 'domain', 'cross-domain', 'enterprise', or 'open'"

        if ontology_type == "open":
            return self.open_graph_extractor(text=text, ontology_type=ontology_type, **kwargs)
        elif ontology_type == "domain":
            return self.domain_graph_extractor(text=text, **kwargs)
        return None


class OpenGraphExtractor(dspy.Module):
    def __init__(self, enable_logging=False):
        """
        A module to extract an RDF graph from a given text input.
        Args:
            enable_logging: Whether to enable logging.
        """
        super().__init__()
        self.logging = enable_logging
        self.entity_extractor = dspy.Predict(Entity)
        self.triples_extractor = dspy.Predict(Triple)
        self.type_asserter = dspy.Predict(TypeAssertion)
        self.type_generator = dspy.Predict(TypeGeneration)
        self.literal_extractor = dspy.Predict(Literal)
        self.spl_triples_extractor = dspy.Predict(SPLTriples)

    @staticmethod
    def snake_case(text):
        return text.strip().lower().replace(" ","_")

    def generate_ontology(self, text: str, ontology_namespace = "http://example.com/ontogen#",
                entity_types: List[str]=None,
                generate_types=False,
                extract_spl_triples=False,
                create_class_hierarchy=False,
                examples_for_entity_extraction=EXAMPLES_FOR_ENTITY_EXTRACTION,
                examples_for_triples_extraction=EXAMPLES_FOR_TRIPLES_EXTRACTION,
                examples_for_type_assertion=EXAMPLES_FOR_TYPE_ASSERTION,
                examples_for_type_generation=EXAMPLES_FOR_TYPE_GENERATION,
                examples_for_literal_extraction=EXAMPLES_FOR_LITERAL_EXTRACTION,
                examples_for_spl_triples_extraction=EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION,
                save_path="generated_ontology.owl") -> Ontology:
        if self.logging:
            print("GraphExtractor: INFO  :: In the generated triples, you may see entities or literals that were not"
                  "part of the extracted entities or literals. They are filtered before added to the ontology.")
        entities = self.entity_extractor(text=text, few_shot_examples= examples_for_entity_extraction).entities
        if self.logging:
            print(f"GraphExtractor: INFO  :: Generated the following entities: {entities}")
        triples = self.triples_extractor(text=text, entities=entities, few_shot_examples= examples_for_triples_extraction).triples
        if self.logging:
            print(f"GraphExtractor: INFO  :: Generated the following triples: {triples}")

        # Create an ontology and load it with extracted triples
        onto = Ontology(ontology_iri=IRI.create("http://example.com/ontogen") ,load=False)
        for triple in triples:
            subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
            prop = OWLObjectProperty(ontology_namespace + self.snake_case(triple[1]))
            object = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[2]))
            if triple[0] in entities and triple[2] in entities:
                ax = OWLObjectPropertyAssertionAxiom(subject, prop, object)
                onto.add_axiom(ax)

        # If user wants to set types, do so depending on the arguments
        if entity_types is not None or generate_types:
            type_assertions = None
            # The user has specified a preset list of types
            if entity_types is not None and not generate_types:
                type_assertions = self.type_asserter(text=text, entities=entities, entity_types=entity_types,
                                                     few_shot_examples=examples_for_type_assertion).pairs
                if self.logging:
                    print(f"GraphExtractor: INFO  :: Assigned types for entities as following: {type_assertions}")
            # The user wishes to leave it to the LLM to generate and assign types
            elif generate_types:
                type_assertions = self.type_generator(text=text, entities=entities,
                                                      few_shot_examples=examples_for_type_generation).pairs
                if self.logging:
                    print(f"GraphExtractor: INFO  :: Finished generating types and assigned them to entities as following: {type_assertions}")

            # Add class assertion axioms
            for pair in type_assertions:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(pair[0]))
                entity_type = OWLClass(ontology_namespace + self.snake_case(pair[1]))
                ax = OWLClassAssertionAxiom(subject, entity_type)
                onto.add_axiom(ax)

        # Extract triples of type s-p-l where l is a numeric literal, including dates.
        if extract_spl_triples:
            literals = self.literal_extractor(text=text, few_shot_examples=examples_for_literal_extraction).l_values
            if self.logging:
                print(f"GraphExtractor: INFO  :: Generated the following numeric literals: {literals}")
            spl_triples = self.spl_triples_extractor(text=text, entities=entities, numeric_literals=literals,
                                                     few_shot_examples= examples_for_spl_triples_extraction).triples
            if self.logging:
                print(f"GraphExtractor: INFO  :: Generated the following s-p-l triples: {spl_triples}")

            for triple in spl_triples:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
                prop = OWLDataProperty(ontology_namespace + self.snake_case(triple[1]))
                literal = OWLLiteral(str(self.snake_case(triple[2])), type_=StringOWLDatatype) # for now every literal will be represented as a string
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
                    print(f"GraphExtractor: INFO  :: For class {cls.remainder} found superclasses: {[IRI.create(s).remainder for s in superclasses]} and subclasses: {[IRI.create(s).remainder for s in subclasses]}")

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
            print(f"GraphExtractor: INFO  :: Successfully saved the ontology at {os.path.join(os.getcwd(),save_path)}")

        return onto

    def forward(self, text: str,
                ontology_type: str = "open",
                ontology_namespace = "http://example.com/ontogen#",
                entity_types: List[str]=None,
                generate_types=False,
                extract_spl_triples=False,
                create_class_hierarchy=False,
                examples_for_entity_extraction=EXAMPLES_FOR_ENTITY_EXTRACTION,
                examples_for_triples_extraction=EXAMPLES_FOR_TRIPLES_EXTRACTION,
                examples_for_type_assertion=EXAMPLES_FOR_TYPE_ASSERTION,
                examples_for_type_generation=EXAMPLES_FOR_TYPE_GENERATION,
                examples_for_literal_extraction=EXAMPLES_FOR_LITERAL_EXTRACTION,
                examples_for_spl_triples_extraction=EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION,
                save_path="generated_ontology.owl"
                ) -> Ontology:

        """
        Extract an ontology from a given textual input.

        Args:
            text (str): Text input from which the ontology will be extracted.
            ontology_type (str): The ontology type to use. Options are:
                                1. 'domain': Focused on a specific domain (e.g., healthcare, finance),
                                2. 'cross-domain': Spans multiple related domains,
                                3. 'enterprise': Tailored for organizational knowledge representation,
                                4. 'open': General-purpose ontology covering a wide range of topics, similar to Wikidata.
            ontology_namespace (str): Namespace to use for the ontology.
            entity_types (List[str]): List of entity types to assign to extracted entities.
                Leave empty if generate_types is True.
            generate_types (bool): Whether to generate types for extracted entities.
            extract_spl_triples (bool): Whether to extract triples of type s-p-l where l is a numeric literal. This
                triples will be represented using data properties and a literal value of type string (although they
                are numeric values).
            create_class_hierarchy (bool): Whether to create a class hierarchy for the extracted entities.
            examples_for_entity_extraction (str): Few-shot examples for entity extraction.
            examples_for_triples_extraction (str): Few-shot examples for triple extraction.
            examples_for_type_assertion (str): Few-shot examples for type assertion.
            examples_for_type_generation (str): Few-shot examples for type generation and assertion.
            examples_for_literal_extraction (str): Few-shot examples for literal extraction.
            examples_for_spl_triples_extraction (str): Few-shot examples for s-p-l triples extraction.
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
                examples_for_entity_extraction=examples_for_entity_extraction,
                examples_for_triples_extraction=examples_for_triples_extraction,
                examples_for_type_assertion=examples_for_type_assertion,
                examples_for_type_generation=examples_for_type_generation,
                examples_for_literal_extraction=examples_for_literal_extraction,
                examples_for_spl_triples_extraction=examples_for_spl_triples_extraction,
                save_path=save_path
            )
        elif ontology_type == "domain":
            # Placeholder for domain-specific ontology generation
            raise NotImplementedError("Domain-specific ontology generation is not yet implemented.")
        elif ontology_type == "cross-domain":
            # Placeholder for cross-domain ontology generation
            raise NotImplementedError("Cross-domain ontology generation is not yet implemented.")
        elif ontology_type == "enterprise":
            # Placeholder for enterprise ontology generation
            raise NotImplementedError("Enterprise ontology generation is not yet implemented.")


class DomainGraphExtractor(dspy.Module):
    def __init__(self, enable_logging=False):
        """
        A module to extract an RDF graph from domain-specific text input.
        Args:
            enable_logging: Whether to enable logging.
        """
        super().__init__()
        self.logging = enable_logging
        self.domain_detector = dspy.Predict(Domain)
        self.few_shot_generator = dspy.Predict(DomainSpecificFewShotGenerator)
        self.entity_extractor = dspy.Predict(Entity)
        self.triples_extractor = dspy.Predict(Triple)
        self.type_asserter = dspy.Predict(TypeAssertion)
        self.type_generator = dspy.Predict(TypeGeneration)
        self.literal_extractor = dspy.Predict(Literal)
        self.spl_triples_extractor = dspy.Predict(SPLTriples)

    @staticmethod
    def snake_case(text):
        return text.strip().lower().replace(" ","_")

    def generate_domain_specific_examples(self, domain: str):
        """
        Generate domain-specific few-shot examples for all task types.

        Args:
            domain: The domain for which to generate examples.

        Returns:
            Dictionary containing few-shot examples for each task type.
        """
        examples = {}
        task_types = [
            'entity_extraction',
            'triples_extraction',
            'type_assertion',
            'type_generation',
            'literal_extraction',
            'spl_triples_extraction'
        ]

        if self.logging:
            print(f"DomainGraphExtractor: INFO :: Generating domain-specific few-shot examples for domain: {domain}")

        for task_type in task_types:
            result = self.few_shot_generator(
                domain=domain,
                task_type=task_type,
                num_examples=2
            )
            examples[task_type] = result.few_shot_examples
            if self.logging:
                print(f"DomainGraphExtractor: INFO :: Generated examples for {task_type}")

        return examples

    def generate_ontology(self, text: str,
                          domain: str = None,
                          ontology_namespace = "http://example.com/ontogen#",
                          entity_types: List[str]=None,
                          generate_types=False,
                          extract_spl_triples=False,
                          create_class_hierarchy=False,
                          examples_for_entity_extraction=None,
                          examples_for_triples_extraction=None,
                          examples_for_type_assertion=None,
                          examples_for_type_generation=None,
                          examples_for_literal_extraction=None,
                          examples_for_spl_triples_extraction=None,
                          save_path="generated_ontology.owl") -> Ontology:
        """
        Generate a domain-specific ontology from text.

        Args:
            text: Input text to extract ontology from.
            domain: The domain of the text. If None, will be detected automatically.
            ontology_namespace: Namespace for the ontology.
            entity_types: List of entity types to assign.
            generate_types: Whether to generate types automatically.
            extract_spl_triples: Whether to extract subject-property-literal triples.
            create_class_hierarchy: Whether to create class hierarchy from DBpedia.
            examples_for_*: Custom few-shot examples. If None, domain-specific examples will be generated.
            save_path: Path to save the ontology.

        Returns:
            Generated Ontology object.
        """
        # Step 1: Detect domain if not provided
        if domain is None:
            domain_result = self.domain_detector(text=text)
            domain = domain_result.domain
            if self.logging:
                print(f"DomainGraphExtractor: INFO :: Detected domain: {domain}")
        else:
            if self.logging:
                print(f"DomainGraphExtractor: INFO :: Using provided domain: {domain}")

        # Step 2: Generate domain-specific few-shot examples if not provided
        use_generated_examples = (
            examples_for_entity_extraction is None or
            examples_for_triples_extraction is None or
            examples_for_type_assertion is None or
            examples_for_type_generation is None or
            examples_for_literal_extraction is None or
            examples_for_spl_triples_extraction is None
        )

        if use_generated_examples:
            generated_examples = self.generate_domain_specific_examples(domain)

            # Use generated examples only if user hasn't provided their own
            examples_for_entity_extraction = examples_for_entity_extraction or generated_examples['entity_extraction']
            examples_for_triples_extraction = examples_for_triples_extraction or generated_examples['triples_extraction']
            examples_for_type_assertion = examples_for_type_assertion or generated_examples['type_assertion']
            examples_for_type_generation = examples_for_type_generation or generated_examples['type_generation']
            examples_for_literal_extraction = examples_for_literal_extraction or generated_examples['literal_extraction']
            examples_for_spl_triples_extraction = examples_for_spl_triples_extraction or generated_examples['spl_triples_extraction']

        # Step 3: Extract entities
        if self.logging:
            print("DomainGraphExtractor: INFO :: In the generated triples, you may see entities or literals that were not "
                  "part of the extracted entities or literals. They are filtered before added to the ontology.")

        entities = self.entity_extractor(text=text, few_shot_examples=examples_for_entity_extraction).entities
        if self.logging:
            print(f"DomainGraphExtractor: INFO :: Generated the following entities: {entities}")

        # Step 4: Extract triples
        triples = self.triples_extractor(text=text, entities=entities, few_shot_examples=examples_for_triples_extraction).triples
        if self.logging:
            print(f"DomainGraphExtractor: INFO :: Generated the following triples: {triples}")

        # Step 5: Create ontology and add triples
        onto = Ontology(ontology_iri=IRI.create("http://example.com/ontogen"), load=False)
        for triple in triples:
            subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
            prop = OWLObjectProperty(ontology_namespace + self.snake_case(triple[1]))
            object = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[2]))
            if triple[0] in entities and triple[2] in entities:
                ax = OWLObjectPropertyAssertionAxiom(subject, prop, object)
                onto.add_axiom(ax)

        # Step 6: Handle type assertions
        if entity_types is not None or generate_types:
            type_assertions = None
            if entity_types is not None and not generate_types:
                type_assertions = self.type_asserter(text=text, entities=entities, entity_types=entity_types,
                                                     few_shot_examples=examples_for_type_assertion).pairs
                if self.logging:
                    print(f"DomainGraphExtractor: INFO :: Assigned types for entities as following: {type_assertions}")
            elif generate_types:
                type_assertions = self.type_generator(text=text, entities=entities,
                                                      few_shot_examples=examples_for_type_generation).pairs
                if self.logging:
                    print(f"DomainGraphExtractor: INFO :: Finished generating types and assigned them to entities as following: {type_assertions}")

            for pair in type_assertions:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(pair[0]))
                entity_type = OWLClass(ontology_namespace + self.snake_case(pair[1]))
                ax = OWLClassAssertionAxiom(subject, entity_type)
                onto.add_axiom(ax)

        # Step 7: Extract SPL triples if requested
        if extract_spl_triples:
            literals = self.literal_extractor(text=text, few_shot_examples=examples_for_literal_extraction).l_values
            if self.logging:
                print(f"DomainGraphExtractor: INFO :: Generated the following numeric literals: {literals}")
            spl_triples = self.spl_triples_extractor(text=text, entities=entities, numeric_literals=literals,
                                                     few_shot_examples=examples_for_spl_triples_extraction).triples
            if self.logging:
                print(f"DomainGraphExtractor: INFO :: Generated the following s-p-l triples: {spl_triples}")

            for triple in spl_triples:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
                prop = OWLDataProperty(ontology_namespace + self.snake_case(triple[1]))
                literal = OWLLiteral(str(self.snake_case(triple[2])), type_=StringOWLDatatype)
                if triple[2] in literals:
                    ax = OWLDataPropertyAssertionAxiom(subject, prop, literal)
                    onto.add_axiom(ax)

        # Step 8: Create class hierarchy if requested
        if create_class_hierarchy:
            for cls in onto.classes_in_signature():
                try:
                    superclasses, subclasses = extract_hierarchy_from_dbpedia(cls.remainder)
                except Exception:
                    continue
                if self.logging:
                    print(f"DomainGraphExtractor: INFO :: For class {cls.remainder} found superclasses: {[IRI.create(s).remainder for s in superclasses]} and subclasses: {[IRI.create(s).remainder for s in subclasses]}")

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

        # Step 9: Save ontology
        onto.save(path=save_path)
        if self.logging:
            print(f"DomainGraphExtractor: INFO :: Successfully saved the ontology at {os.path.join(os.getcwd(),save_path)}")

        return onto

    def forward(self, text: str,
                domain: str = None,
                ontology_namespace = "http://example.com/ontogen#",
                entity_types: List[str]=None,
                generate_types=False,
                extract_spl_triples=False,
                create_class_hierarchy=False,
                examples_for_entity_extraction=None,
                examples_for_triples_extraction=None,
                examples_for_type_assertion=None,
                examples_for_type_generation=None,
                examples_for_literal_extraction=None,
                examples_for_spl_triples_extraction=None,
                save_path="generated_ontology.owl") -> Ontology:
        """
        Extract a domain-specific ontology from a given textual input.

        Args:
            text (str): Text input from which the ontology will be extracted.
            domain (str): The domain of the text. If None, will be detected automatically.
            ontology_namespace (str): Namespace to use for the ontology.
            entity_types (List[str]): List of entity types to assign to extracted entities.
                Leave empty if generate_types is True.
            generate_types (bool): Whether to generate types for extracted entities.
            extract_spl_triples (bool): Whether to extract triples of type s-p-l where l is a numeric literal.
            create_class_hierarchy (bool): Whether to create a class hierarchy for the extracted entities.
            examples_for_entity_extraction (str): Few-shot examples for entity extraction. If None, domain-specific examples will be generated.
            examples_for_triples_extraction (str): Few-shot examples for triple extraction. If None, domain-specific examples will be generated.
            examples_for_type_assertion (str): Few-shot examples for type assertion. If None, domain-specific examples will be generated.
            examples_for_type_generation (str): Few-shot examples for type generation. If None, domain-specific examples will be generated.
            examples_for_literal_extraction (str): Few-shot examples for literal extraction. If None, domain-specific examples will be generated.
            examples_for_spl_triples_extraction (str): Few-shot examples for s-p-l triples extraction. If None, domain-specific examples will be generated.
            save_path (str): Path to save the generated ontology.

        Returns (Ontology): An ontology object.
        """
        if generate_types:
            assert entity_types is None, ("entity_types argument should be None "
                                          "when you want to generate types (i.e. when generate_types = True)")

        return self.generate_ontology(
            text=text,
            domain=domain,
            ontology_namespace=ontology_namespace,
            entity_types=entity_types,
            generate_types=generate_types,
            extract_spl_triples=extract_spl_triples,
            create_class_hierarchy=create_class_hierarchy,
            examples_for_entity_extraction=examples_for_entity_extraction,
            examples_for_triples_extraction=examples_for_triples_extraction,
            examples_for_type_assertion=examples_for_type_assertion,
            examples_for_type_generation=examples_for_type_generation,
            examples_for_literal_extraction=examples_for_literal_extraction,
            examples_for_spl_triples_extraction=examples_for_spl_triples_extraction,
            save_path=save_path
        )


class CrossDomainGraphExtractor(dspy.Module):
    pass

class EnterpriseGraphExtractor(dspy.Module):
    pass

