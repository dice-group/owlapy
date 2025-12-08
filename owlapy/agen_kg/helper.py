import dspy
import requests

from owlapy.agen_kg.signatures import american_to_british


def configure_dspy(signature):
    lm = dspy.LM(model="openai/gpt-4o", api_key="<ENTER_API_KEY>",
                 api_base=None,
                 temperature=0.1, seed=42, cache=True)
    dspy.configure(lm=lm)
    model = dspy.Predict(signature)
    return model


def run_query(query):
    """Runs a SPARQL query against the DBpedia SPARQL endpoint."""
    params = {
        "query": query,
        "format": "application/sparql-results+json"
    }
    response = requests.get("http://dbpedia.org/sparql", params=params)
    response.raise_for_status()
    data = response.json()
    return [binding['superclass' if 'superclass' in binding else 'subclass']['value']
            for binding in data['results']['bindings']]

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