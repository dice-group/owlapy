from typing import List
import os
import dspy

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.ontogen.few_shot_examples import EXAMPLES_FOR_ENTITY_EXTRACTION, EXAMPLES_FOR_TRIPLES_EXTRACTION, \
    EXAMPLES_FOR_TYPE_ASSERTION, EXAMPLES_FOR_TYPE_GENERATION, EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION, \
    EXAMPLES_FOR_LITERAL_EXTRACTION
from owlapy.owl_axiom import OWLObjectPropertyAssertionAxiom, OWLClassAssertionAxiom, OWLDataPropertyAssertionAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral, StringOWLDatatype
from owlapy.owl_ontology import Ontology
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty


class Entity(dspy.Signature):
    __doc__ = """Given a piece of text as input identify key entities extracted form the text."""
    text: str = dspy.InputField(desc="A textual input about some topic.")
    few_shot_examples: str = dspy.InputField(desc="Few shot examples for this task.")
    entities: list[str] = dspy.OutputField(desc="List of key entities, capitalized.")

class Triple(dspy.Signature):
    __doc__ = """Given a piece of text and entities, identify triples of type source_entity-relation-target_entity
    where source_entity and target_entity are strictly part of the given entities."""
    text: str = dspy.InputField(desc="A textual input about some topic.")
    entities: list[str] = dspy.InputField(desc="List of entities to consider.")
    few_shot_examples: str = dspy.InputField(desc="Few shot examples for this task.")
    triples: list[tuple[str,str,str]] = dspy.OutputField(desc="List of source_entity-relation-target_entity, capitalized.")

class TypeAssertion(dspy.Signature):
    __doc__ = """Given a list of entities, a list of types and textual contex, assign types to the entities."""
    text: str = dspy.InputField(desc="A textual input about some topic.")
    entities: list[str] = dspy.InputField(desc="List of entities to assign a type to.")
    entity_types: list[str] = dspy.InputField(desc="List of types to be assigned to entities.")
    few_shot_examples: str = dspy.InputField(desc="Few shot examples for this task.")
    pairs: list[tuple[str, str]] = dspy.OutputField(desc="List of entity-entity_type pairs.")


class TypeGeneration(dspy.Signature):
    __doc__ = """Given a list of entities and textual contex, assign meaningful general types to the entities."""
    text: str = dspy.InputField(desc="A textual input about some topic.")
    entities: list[str] = dspy.InputField(desc="List of entities to assign a type to.")
    few_shot_examples: str = dspy.InputField(desc="Few shot examples for this task.")
    pairs: list[tuple[str, str]] = dspy.OutputField(desc="List of entity-entity_type pairs.")


class Literal(dspy.Signature):
    __doc__ = """Given a piece of text as input identify key numerical values extracted form the text."""
    text: str = dspy.InputField(desc="A textual input about some topic.")
    few_shot_examples: str = dspy.InputField(desc="Few shot examples for this task.")
    l_values: list[str] = dspy.OutputField(desc="List of key numerical values.")

class SPLTriples(dspy.Signature):
    __doc__ = """Given a piece of text, entities and numeric literals, identify triples of type 
    source_entity-relation-target_value where source_entity is strictly part of the given entities and the target_value 
    is strictly part of the given numeric literals."""
    text: str = dspy.InputField(desc="A textual input about some topic.")
    entities: list[str] = dspy.InputField(desc="List of entities to consider.")
    numeric_literals: list[str] = dspy.InputField(desc="List of literals to consider.")
    few_shot_examples: str = dspy.InputField(desc="Few shot examples for this task.")
    triples: list[tuple[str, str, str]] = dspy.OutputField(
        desc="List of source_entity-relation-target_value triples.")


def configure_dspy(signature):
    lm = dspy.LM(model="openai/gpt-4o", api_key="<ENTER_API_KEY>",
                 api_base=None,
                 temperature=0.1, seed=42, cache=True, cache_in_memory=True)
    dspy.configure(lm=lm)
    model = dspy.Predict(signature)
    return model

def get_entities(text, few_shot_examples=EXAMPLES_FOR_ENTITY_EXTRACTION):
    model = configure_dspy(Entity)
    result = model(text=text, few_shot_examples=few_shot_examples)
    return result.entities

def get_triples(text, entities, few_shot_examples=EXAMPLES_FOR_TRIPLES_EXTRACTION):
    model = configure_dspy(Triple)
    result = model(text=text, entities=entities, few_shot_examples=few_shot_examples)
    return result.triples

def assign_types(text, entities, entity_types, few_shot_examples=EXAMPLES_FOR_TYPE_ASSERTION):
    model = configure_dspy(TypeAssertion)
    result = model(text=text, entities=entities, entity_types=entity_types, few_shot_examples=few_shot_examples)
    return result.pairs

def generate_types(text, entities, few_shot_examples= EXAMPLES_FOR_TYPE_GENERATION):
    model = configure_dspy(TypeGeneration)
    result = model(text=text, entities=entities, few_shot_examples=few_shot_examples)
    return result.pairs

def get_numeric_literals(text, few_shot_examples=EXAMPLES_FOR_LITERAL_EXTRACTION):
    model = configure_dspy(Literal)
    result = model(text=text, few_shot_examples=few_shot_examples)
    return result.l_values

def get_spl_triples(text, entities, literals, few_shot_examples=EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION):
    model = configure_dspy(SPLTriples)
    result = model(text=text, entities=entities, numeric_literals=literals, few_shot_examples=few_shot_examples)
    return result.triples

class GraphExtractor(dspy.Module):
    def __init__(self,model, api_key, api_base, temperature=0.1, seed=42, cache=False, cache_in_memory=False,
                 enable_logging=False):
        """
        A module to extract an RDF graph from a given text input.
        Args:
            model: Model name for the LLM.
            api_key: API key.
            api_base: API base URL.
            temperature: The sampling temperature to use when generating responses.
            seed: Seed for the LLM.
            cache: Whether to cache the model responses for reuse to improve performance and reduce costs.
            cache_in_memory: To enable additional caching with LRU in memory.
        """
        super().__init__()
        lm = dspy.LM(model=f"openai/{model}", api_key=api_key,
                     api_base=api_base,
                     temperature=temperature, seed=seed, cache=cache, cache_in_memory=cache_in_memory)
        dspy.configure(lm=lm)
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

    def forward(self, text: str,
                ontology_namespace = "http://example.com/ontogen#",
                entity_types: List[str]=None,
                generate_types=False,
                extract_spl_triples=False,
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
            ontology_namespace (str): Namespace to use for the ontology.
            entity_types (List[str]): List of entity types to assign to extracted entities.
                Leave empty if generate_types is True.
            generate_types (bool): Whether to generate types for extracted entities.
            extract_spl_triples (bool): Whether to extract triples of type s-p-l where l is a numeric literal. This
                triples will be represented using data properties and a literal value of type string (although they
                are numeric values).
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

        onto.save(path=save_path)
        if self.logging:
            print(f"GraphExtractor: INFO  :: Successfully saved the ontology at {os.path.join(os.getcwd(),save_path)}")

        return onto