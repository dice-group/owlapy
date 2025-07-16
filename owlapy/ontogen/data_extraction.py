from typing import List

import dspy

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.ontogen.few_shot_examples import EXAMPLES_FOR_ENTITY_EXTRACTION, EXAMPLES_FOR_TRIPLES_EXTRACTION, \
    EXAMPLES_FOR_TYPE_ASSERTION
from owlapy.owl_axiom import OWLObjectPropertyAssertionAxiom, OWLClassAssertionAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import Ontology
from owlapy.owl_property import OWLObjectProperty


# todo: Idea: Enable possibility to generate types (complex: can assure accuracy)
# todo: Idea: Enable possibility to extract triples with a data property as the relation and a literal value as
#             object (complex: a lot of datatypes to consider)

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

# class DPTriples(dspy.Signature):
#     __doc__ = """Given a piece of text and entities, identify triples of type source_entity-relation-target_literal
#         where source_entity is strictly part of the given entities and the target_literal can be a numerical literal or
#         a string which describes some attribute."""
#     text: str = dspy.InputField(desc="A textual input about some topic.")
#     entities: list[str] = dspy.InputField(desc="List of entities to consider.")
#     few_shot_examples: str = dspy.InputField(desc="Few shot examples for this task.")
#     triples: list[tuple[str, str, str]] = dspy.OutputField(
#         desc="List of source_entity-relation-target_literal, capitalized.")


def configure_dspy(signature):
    lm = dspy.LM(model=f"openai/Qwen/Qwen3-32B-AWQ", api_key="<KEY>",
                 api_base="http://tentris-ml.cs.upb.de:8501/v1",
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

class GraphExtractor(dspy.Module):
    def __init__(self,model, api_key, api_base, temperature=0.1, seed=42, cache=False, cache_in_memory=False):
        super().__init__()
        lm = dspy.LM(model=f"openai/{model}", api_key=api_key,
                     api_base=api_base,
                     temperature=temperature, seed=seed, cache=cache, cache_in_memory=cache_in_memory)
        dspy.configure(lm=lm)
        self.entity_extractor = dspy.Predict(Entity)
        self.triples_extractor = dspy.Predict(Triple)
        self.type_asserter = dspy.Predict(TypeAssertion)

    @staticmethod
    def snake_case(text):
        return text.strip().lower().replace(" ","_")

    def forward(self, text: str, examples_for_entity_extraction=EXAMPLES_FOR_ENTITY_EXTRACTION,
                examples_for_triples_extraction=EXAMPLES_FOR_TRIPLES_EXTRACTION,
                examples_for_type_assertion=EXAMPLES_FOR_TYPE_ASSERTION,
                ontology_namespace = "http://example.com/ontogen#", entity_types: List[str]=None):

        entities = self.entity_extractor(text=text, few_shot_examples= examples_for_entity_extraction).entities
        triples = self.triples_extractor(text=text, entities=entities, few_shot_examples= examples_for_triples_extraction).triples


        onto = Ontology(ontology_iri=IRI.create("http://example.com/ontogen") ,load=False)
        for triple in triples:
            subject = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[0]))
            prop = OWLObjectProperty(ontology_namespace + self.snake_case(triple[1]))
            object = OWLNamedIndividual(ontology_namespace + self.snake_case(triple[2]))
            ax = OWLObjectPropertyAssertionAxiom(subject, prop, object)
            onto.add_axiom(ax)

        if entity_types is not None:
            type_assertions = self.type_asserter(text=text, entities=entities, entity_types=entity_types,
                                                 few_shot_examples=examples_for_type_assertion).pairs
            print(type_assertions)
            for pair in type_assertions:
                subject = OWLNamedIndividual(ontology_namespace + self.snake_case(pair[0]))
                entity_type = OWLClass(ontology_namespace + self.snake_case(pair[1]))
                ax = OWLClassAssertionAxiom(subject, entity_type)
                onto.add_axiom(ax)


        onto.save(path="generated_ontology.owl")

        return onto