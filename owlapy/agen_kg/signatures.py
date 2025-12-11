import dspy

# DBpedia often uses British English, so we define a mapping for common American to British English terms.
american_to_british = {
    "organization": "organisation",
    "color": "colour",
    "honor": "honour",
    "analyze": "analyse",
    "center": "centre",
    "meter": "metre",
    "theater": "theatre",
    "catalog": "catalogue",
    "defense": "defence",
    "offense": "offence",
    "license": "licence",  # noun in UK
    "practice": "practise",  # verb in UK
    "traveled": "travelled",
    "canceled": "cancelled",
    "labeled": "labelled",
    "modeling": "modelling",
    "program": "programme",  # when referring to TV/show
    "check": "cheque",  # bank sense
    "gray": "grey",
    "plow": "plough"
}

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

class Domain(dspy.Signature):
    __doc__ = """Given a piece of text, identify the primary domain or topic of the text.
    Example domains: 'biology', 'chemistry', 'finance', 'sports', 'politics', 'medicine', 'computer science'.
    """
    text: str = dspy.InputField(desc="A textual input whose domain should be identified.")
    domain: str = dspy.OutputField(desc="Detected domain/category of the text, normalized (lowercase).")

class CrossDomain(dspy.Signature):
    __doc__ = """Given a piece of text, identify all the domains or topics of the text.
    Example domains: 'biology', 'chemistry', 'finance', 'sports', 'politics', 'medicine', 'computer science'.
    """
    text: str = dspy.InputField(desc="A textual input whose domains should be identified.")
    domains: list[str] = dspy.OutputField(desc="Detected domains/categories of the text, normalized (lowercase).")

class DomainSpecificFewShotGenerator(dspy.Signature):
    __doc__ = """Given a domain (e.g., 'biology', 'finance', 'sports'), generate few-shot examples tailored to that domain 
    for a specific task (entity extraction, triple extraction, type assertion, etc.). The examples should follow the same 
    format as the general few-shot examples but with domain-specific content."""
    domain: str = dspy.InputField(desc="The domain for which to generate few-shot examples (e.g., 'biology', 'finance').")
    task_type: str = dspy.InputField(desc="The task type: 'entity_extraction', 'triples_extraction', 'type_assertion', 'type_generation', 'literal_extraction', or 'spl_triples_extraction'.")
    num_examples: int = dspy.InputField(desc="Number of examples to generate.", default=2)
    few_shot_examples: str = dspy.OutputField(desc="Generated few-shot examples formatted as a string, following the standard format with Example 1, Example 2, etc.")

class EntityClustering(dspy.Signature):
    __doc__ = """Given a list of entities, identify duplicates and near-duplicates that refer to the same real-world entity.
    Consider variations in spelling, abbreviations, synonyms, and different naming conventions. Return clusters of entities 
    that should be merged together, along with the canonical name to use for each cluster."""
    entities: list[str] = dspy.InputField(desc="List of entities to cluster and identify duplicates.")
    text: str = dspy.InputField(desc="The original text context to help understand entity relationships.")
    clusters: list[tuple[list[str], str]] = dspy.OutputField(desc="List of tuples where each tuple contains (list_of_duplicate_entities, canonical_entity_name).")

class CoherenceChecker(dspy.Signature):
    __doc__ = """Given a batch of triples and optional textual context, evaluate the logical coherence and factual consistency 
    of the triples. Rate each triple's coherence on a scale of 1-5, where 1 means incoherent, contradictory or trivial and 5 means highly 
    coherent and consistent. Identify any contradictions or logical inconsistencies between triples."""
    triples: list[tuple[str, str, str]] = dspy.InputField(desc="List of triples to evaluate for coherence (source-relation-target).")
    text: str = dspy.InputField(desc="The original text context to verify triples against.")
    coherence_scores: list[tuple[tuple[str, str, str], int, str]] = dspy.OutputField(desc="List of tuples: (triple, coherence_score_1_to_5, explanation).")

class TypeClustering(dspy.Signature):
    __doc__ = """Given a list of entity types, identify duplicates and near-duplicates that refer to the same conceptual type.
    Consider variations in spelling, singular/plural forms, synonyms, and different naming conventions. Return clusters of types 
    that should be merged together, along with the canonical type name to use for each cluster."""
    types: list[str] = dspy.InputField(desc="List of entity types to cluster and identify duplicates.")
    text: str = dspy.InputField(desc="The original text context to help understand type relationships.")
    clusters: list[tuple[list[str], str]] = dspy.OutputField(desc="List of tuples where each tuple contains (list_of_duplicate_types, canonical_type_name).")

class RelationClustering(dspy.Signature):
    __doc__ = """Given a list of relations, identify duplicates and near-duplicates that refer to the same relationship.
    Consider variations in spelling, synonyms, different phrasings, and naming conventions. Return clusters of relations 
    that should be merged together, along with the canonical relation name to use for each cluster."""
    relations: list[str] = dspy.InputField(desc="List of relations to cluster and identify duplicates.")
    text: str = dspy.InputField(desc="The original text context to help understand relation meanings.")
    clusters: list[tuple[list[str], str]] = dspy.OutputField(desc="List of tuples where each tuple contains (list_of_duplicate_relations, canonical_relation_name).")

