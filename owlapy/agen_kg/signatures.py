import dspy

class Entity(dspy.Signature):
    __doc__ = """Given a piece of text as input identify key entities extracted form the text. The result 
    should be a list of capitalized entities. E.g., ["ENTITY1", "ENTITY2", ...]"""
    text: str = dspy.InputField(desc="A textual input about some topic.")
    few_shot_examples: str = dspy.InputField(desc="Few shot examples for this task.")
    task_instructions: str = dspy.InputField(desc="Specific instructions that must be considered.")
    entities: list[str] = dspy.OutputField(desc="List of key entities, capitalized.")

class Triple(dspy.Signature):
    __doc__ = """Given a piece of text and entities, identify triples of type source_entity-relation-target_entity
    where source_entity and target_entity are strictly part of the given entities."""
    text: str = dspy.InputField(desc="A textual input about some topic.")
    entities: list[str] = dspy.InputField(desc="List of entities to consider.")
    task_instructions: str = dspy.InputField(desc="Specific instructions that must be considered.")
    few_shot_examples: str = dspy.InputField(desc="Few shot examples for this task.")
    triples: list[tuple[str,str,str]] = dspy.OutputField(desc="List of source_entity-relation-target_entity, capitalized.")

class TypeAssertion(dspy.Signature):
    __doc__ = """Given a list of entities, a list of types and textual contex, assign types to the entities."""
    text: str = dspy.InputField(desc="A textual input about some topic.")
    entities: list[str] = dspy.InputField(desc="List of entities to assign a type to.")
    entity_types: list[str] = dspy.InputField(desc="List of types to be assigned to entities.")
    few_shot_examples: str = dspy.InputField(desc="Few shot examples for this task.")
    task_instructions: str = dspy.InputField(desc="Specific instructions that must be considered.")
    pairs: list[tuple[str, str]] = dspy.OutputField(desc="List of entity-entity_type pairs.")

class TypeGeneration(dspy.Signature):
    __doc__ = """Given a list of entities and textual contex, assign meaningful general types to the entities."""
    text: str = dspy.InputField(desc="A textual input about some topic.")
    entities: list[str] = dspy.InputField(desc="List of entities to assign a type to.")
    few_shot_examples: str = dspy.InputField(desc="Few shot examples for this task.")
    task_instructions: str = dspy.InputField(desc="Specific instructions that must be considered.")
    pairs: list[tuple[str, str]] = dspy.OutputField(desc="List of entity-entity_type pairs.")

class Literal(dspy.Signature):
    __doc__ = """Given a piece of text as input identify key numerical values extracted form the text. The result
    should be a list of numerical literals. E.g., ["123", "45.67", "50%", ...]"""
    text: str = dspy.InputField(desc="A textual input about some topic.")
    task_instructions: str = dspy.InputField(desc="Specific instructions that must be considered.")
    few_shot_examples: str = dspy.InputField(desc="Few shot examples for this task.")
    l_values: list[str] = dspy.OutputField(desc="List of key numerical values.")

class SPLTriples(dspy.Signature):
    __doc__ = """Given a piece of text, entities and numeric literals, identify triples of type 
    source_entity-relation-target_value where source_entity is strictly part of the given entities and the target_value 
    is strictly part of the given numeric literals."""
    text: str = dspy.InputField(desc="A textual input about some topic.")
    entities: list[str] = dspy.InputField(desc="List of entities to consider.")
    numeric_literals: list[str] = dspy.InputField(desc="List of literals to consider.")
    task_instructions: str = dspy.InputField(desc="Specific instructions that must be considered.")
    few_shot_examples: str = dspy.InputField(desc="Few shot examples for this task.")
    triples: list[tuple[str, str, str]] = dspy.OutputField(
        desc="List of source_entity-relation-target_value triples.")

class Domain(dspy.Signature):
    __doc__ = """Given a piece of text, identify the primary domain or topic of the text.
    Example domains: 'biology', 'chemistry', 'finance', 'sports', 'politics', 'medicine', 'computer science'.
    """
    text: str = dspy.InputField(desc="A textual input whose domain should be identified.")
    domain: str = dspy.OutputField(desc="Detected domain/category of the text, normalized (lowercase).")

class DomainSpecificFewShotGenerator(dspy.Signature):
    __doc__ = """Given a domain (e.g., 'biology', 'finance', 'sports'), generate few-shot examples tailored to that domain 
    for a specific task (entity extraction, triple extraction, type assertion, etc.). The examples should follow the same 
    format as the general few-shot examples but with domain-specific content."""
    domain: str = dspy.InputField(desc="The domain for which to generate few-shot examples (e.g., 'biology', 'finance').")
    task_type: str = dspy.InputField(desc="The task type: 'entity_extraction', 'triples_extraction', 'type_assertion', 'type_generation', 'literal_extraction', or 'triples_with_numeric_literals_extraction'.")
    num_examples: int = dspy.InputField(desc="Number of examples to generate.", default=2)
    examples_example_structure: str = dspy.InputField(
        desc="The example structure to use as a guiding template for generating few-shot examples.")
    few_shot_examples: str = dspy.OutputField(desc="Generated few-shot examples formatted as a string, following the standard format with Example 1, Example 2, etc.")

class EntityDeduplication(dspy.Signature):
    __doc__ = """Given a list of entities, identify and remove redundant near-duplicates that refer to the same real-world entity.
    Consider variations in spelling, abbreviations, and naming conventions. For example, given ['Ben Smith', 'B. Smith'], 
    remove 'B. Smith' and keep 'Ben Smith'. Preserve most entities - only filter out those that are very closely resembled or 
    abbreviated versions of more complete entities. Return a filtered list with redundant entities removed."""
    entities: list[str] = dspy.InputField(desc="List of entities to deduplicate.")
    text: str = dspy.InputField(desc="The original text context to help understand entity relationships.")
    filtered_entities: list[str] = dspy.OutputField(desc="Filtered list of entities with redundant near-duplicates removed.")

class CoherenceChecker(dspy.Signature):
    __doc__ = """Given a batch of triples, textual context and optional instructions, evaluate the logical coherence and factual consistency 
    of the triples. Rate each triple's coherence on a scale of 1-5, where 1 means incoherent, contradictory or trivial and 5 means highly 
    coherent and consistent. Identify any contradictions or logical inconsistencies between triples."""
    triples: list[tuple[str, str, str]] = dspy.InputField(desc="List of triples to evaluate for coherence (source-relation-target).")
    text: str = dspy.InputField(desc="The original text context to verify triples against.")
    task_instructions: str = dspy.InputField(desc="Specific instructions that must be considered.")
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


class TextSummarizer(dspy.Signature):
    __doc__ = """Given a piece of text, generate a concise summary that preserves all key entities, relationships,
    types, and factual information mentioned. The summary should capture the essential semantic content without 
    losing important details needed for knowledge graph extraction."""
    text: str = dspy.InputField(desc="A textual input to summarize.")
    summary: str = dspy.OutputField(desc="A concise summary preserving entities, relationships, types, and key facts.")

class ChunkSummarizer(dspy.Signature):
    __doc__ = """Given multiple text chunk summaries, combine them into a unified comprehensive summary.
    The combined summary should deduplicate information, preserve all unique entities and relationships,
    and maintain coherence across the merged content."""
    chunk_summaries: list[str] = dspy.InputField(desc="List of summaries from different text chunks.")
    combined_summary: str = dspy.OutputField(desc="A unified summary that combines and deduplicates information from all chunks.")

class EntityDeduplicationWithSummary(dspy.Signature):
    __doc__ = """Given a list of entities and a summary of the source text, identify and remove redundant near-duplicates 
    that refer to the same real-world entity. Consider variations in spelling, abbreviations, and naming conventions. 
    For example, given ['Ben Smith', 'B. Smith'], remove 'B. Smith' and keep 'Ben Smith'. Preserve most entities - only 
    filter out those that are very closely resembled or abbreviated versions of more complete entities. 
    Return a filtered list with redundant entities removed."""
    entities: list[str] = dspy.InputField(desc="List of entities to deduplicate.")
    summary: str = dspy.InputField(desc="A summary of the original text context to help understand entity relationships.")
    filtered_entities: list[str] = dspy.OutputField(desc="Filtered list of entities with redundant near-duplicates removed.")

class TypeClusteringWithSummary(dspy.Signature):
    __doc__ = """Given a list of entity types and a summary of the source text, identify duplicates and near-duplicates 
    that refer to the same conceptual type. Consider variations in spelling, singular/plural forms, synonyms, 
    and different naming conventions. Return clusters of types that should be merged together, 
    along with the canonical type name to use for each cluster."""
    types: list[str] = dspy.InputField(desc="List of entity types to cluster and identify duplicates.")
    summary: str = dspy.InputField(desc="A summary of the original text context to help understand type relationships.")
    clusters: list[tuple[list[str], str]] = dspy.OutputField(desc="List of tuples where each tuple contains (list_of_duplicate_types, canonical_type_name).")

class RelationClusteringWithSummary(dspy.Signature):
    __doc__ = """Given a list of relations and a summary of the source text, identify duplicates and near-duplicates 
    that refer to the same relationship. Consider variations in spelling, synonyms, different phrasings, 
    and naming conventions. Return clusters of relations that should be merged together, 
    along with the canonical relation name to use for each cluster."""
    relations: list[str] = dspy.InputField(desc="List of relations to cluster and identify duplicates.")
    summary: str = dspy.InputField(desc="A summary of the original text context to help understand relation meanings.")
    clusters: list[tuple[list[str], str]] = dspy.OutputField(desc="List of tuples where each tuple contains (list_of_duplicate_relations, canonical_relation_name).")

class IncrementalEntityMerger(dspy.Signature):
    __doc__ = """Given two sets of entities from different text chunks along with context, merge them into a unified 
    list. Identify entities that refer to the same real-world entity across chunks and produce a canonical list.
    Consider different mentions, abbreviations, and naming conventions that may appear across chunks."""
    entities_a: list[str] = dspy.InputField(desc="First list of entities from chunk A.")
    entities_b: list[str] = dspy.InputField(desc="Second list of entities from chunk B.")
    context_a: str = dspy.InputField(desc="Summary/context from chunk A to understand entity meanings.")
    context_b: str = dspy.InputField(desc="Summary/context from chunk B to understand entity meanings.")
    merged_entities: list[str] = dspy.OutputField(desc="Unified list of entities with duplicates merged to canonical forms.")
    entity_mapping: list[tuple[str, str]] = dspy.OutputField(desc="List of (original_entity, canonical_entity) mappings for entities that were merged.")

class IncrementalTripleMerger(dspy.Signature):
    __doc__ = """Given two sets of triples from different text chunks along with context, merge them into a unified 
    list. Identify triples that represent the same relationship (possibly with different wording) and produce
    a canonical list. Handle variations in entity names and relation phrasings across chunks."""
    triples_a: list[tuple[str, str, str]] = dspy.InputField(desc="First list of triples from chunk A.")
    triples_b: list[tuple[str, str, str]] = dspy.InputField(desc="Second list of triples from chunk B.")
    context_a: str = dspy.InputField(desc="Summary/context from chunk A.")
    context_b: str = dspy.InputField(desc="Summary/context from chunk B.")
    merged_triples: list[tuple[str, str, str]] = dspy.OutputField(desc="Unified list of triples with semantic duplicates merged.")

class IncrementalTypeMerger(dspy.Signature):
    __doc__ = """Given two sets of entity-type pairs from different text chunks, merge them into a unified list.
    Resolve any conflicting type assignments for the same entity, preferring more specific types.
    Handle variations in type naming across chunks."""
    types_a: list[tuple[str, str]] = dspy.InputField(desc="First list of (entity, type) pairs from chunk A.")
    types_b: list[tuple[str, str]] = dspy.InputField(desc="Second list of (entity, type) pairs from chunk B.")
    context_a: str = dspy.InputField(desc="Summary/context from chunk A.")
    context_b: str = dspy.InputField(desc="Summary/context from chunk B.")
    merged_types: list[tuple[str, str]] = dspy.OutputField(desc="Unified list of entity-type pairs with conflicts resolved.")

class PlanDecomposer(dspy.Signature):
    __doc__ = """We want to extract knowledge from text in triples format. The pipeline follows these steps:
    entity extraction, triple extraction, type assertion, literal extraction, triple extraction with numeric literals.
    Given the user's query about the knowledge graph to be extracted, decompose it into sub-tasks that can be used
    as instructions for each step of the pipeline."""
    user_request: str = dspy.InputField(desc="The user request to be decomposed into sub-tasks.")
    entity_extraction_task: str = dspy.OutputField(desc="Sub-task description for entity extraction.")
    triple_extraction_task: str = dspy.OutputField(desc="Sub-task description for triple extraction.")
    type_generation_task: str = dspy.OutputField(desc="Sub-task description for generating types for entities.")
    type_assertion_task: str = dspy.OutputField(desc="Sub-task description for asserting types to entities.")
    literal_extraction_task: str = dspy.OutputField(desc="Sub-task description for literal extraction.")
    triple_with_literal_extraction_task: str = dspy.OutputField(desc="Sub-task description for triple extraction with numeric literals.")
    fact_checking_task: str = dspy.OutputField(desc="Sub-task description for fact checking and coherence verification of extracted triples.")
