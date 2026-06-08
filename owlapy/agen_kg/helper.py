from itertools import islice
from typing import Iterable, Iterator, TypeVar

import dspy
import requests

from owlapy.agen_kg.few_shot_examples import (
    EXAMPLES_FOR_ENTITY_EXTRACTION,
    EXAMPLES_FOR_LITERAL_EXTRACTION,
    EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION,
    EXAMPLES_FOR_TRIPLES_EXTRACTION,
    EXAMPLES_FOR_TYPE_ASSERTION,
    EXAMPLES_FOR_TYPE_GENERATION,
)

RDFS_COMMENT_IRI = "http://www.w3.org/2000/01/rdf-schema#comment"
RDFS_LABEL_IRI = "http://www.w3.org/2000/01/rdf-schema#label"

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
    "plow": "plough",
}

task_example_mapping = {
    "entity_extraction": EXAMPLES_FOR_ENTITY_EXTRACTION,
    "triples_extraction": EXAMPLES_FOR_TRIPLES_EXTRACTION,
    "type_assertion": EXAMPLES_FOR_TYPE_ASSERTION,
    "type_generation": EXAMPLES_FOR_TYPE_GENERATION,
    "literal_extraction": EXAMPLES_FOR_LITERAL_EXTRACTION,
    "triples_with_numeric_literals_extraction": EXAMPLES_FOR_SPL_TRIPLES_EXTRACTION,
}


def configure_dspy(signature):
    lm = dspy.LM(model="openai/gpt-4o", api_key="<ENTER_API_KEY>", api_base=None, temperature=0.1, seed=42, cache=True)
    dspy.configure(lm=lm)
    model = dspy.Predict(signature)
    return model


def run_query(query):
    """Runs a SPARQL query against the DBpedia SPARQL endpoint."""
    params = {"query": query, "format": "application/sparql-results+json"}
    response = requests.get("http://dbpedia.org/sparql", params=params)
    response.raise_for_status()
    data = response.json()
    return [binding["superclass" if "superclass" in binding else "subclass"]["value"] for binding in data["results"]["bindings"]]


def extract_hierarchy_from_dbpedia(cls):
    """
    Extracts the hierarchy of an entity from DBpedia using the SPARQL endpoint.

    Args:
        cls (str): The DBpedia class remainder.

    Returns:
        tuple: A tuple containing two lists:
            - superclasses: List of superclasses of the entity.
            - subclasses: List of subclasses of the entity.
    """

    if cls.lower() in american_to_british:
        cls = american_to_british[cls.lower()]
    dbpedia_class_uri = f"http://dbpedia.org/ontology/{cls.capitalize()}"
    superclass_query = f"""SELECT ?superclass WHERE {{<{dbpedia_class_uri}> rdfs:subClassOf ?superclass .}}"""
    subclass_query = f"""SELECT ?subclass WHERE {{?subclass rdfs:subClassOf <{dbpedia_class_uri}> .}}"""
    superclasses = run_query(superclass_query)
    subclasses = run_query(subclass_query)

    return superclasses, subclasses


T = TypeVar("T")


def chunked_iterator(seq: Iterable[T], size: int = 20) -> Iterator[list[T]]:
    """
    Splits an iterable into fixed-size chunks and yields them sequentially.

    This function consumes the input iterable lazily and groups its elements
    into lists of a maximum given size. It is useful for batching data for
    processing, such as API calls or LLM requests.

    Args:
        seq (Iterable[T]): The input iterable to be chunked.
        size (int): The maximum number of elements per chunk. Defaults to 50.

    Returns:
        Iterator[list[T]]: An iterator over lists, where each list contains
        up to `size` elements from the input iterable.
    """
    it = iter(seq)

    while chunk := list(islice(it, size)):
        yield chunk
