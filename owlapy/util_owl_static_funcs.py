import json
import logging
import os
import random
import warnings
from typing import List, Set

import pandas as pd
from rdflib import OWL, RDF, RDFS, Graph, Literal, Namespace, URIRef
from rdflib.namespace import XSD
from tqdm import tqdm

from .class_expression import OWLClass, OWLClassExpression
from .iri import IRI
from .owl_axiom import OWLDataPropertyAssertionAxiom, OWLEquivalentClassesAxiom
from .owl_individual import OWLNamedIndividual
from .owl_literal import OWLLiteral
from .owl_ontology import Ontology, RDFLibOntology, SyncOntology
from .owl_property import OWLDataProperty

logger = logging.getLogger(__name__)



def save_owl_class_expressions(expressions: OWLClassExpression | List[OWLClassExpression],
                               path: str = 'predictions',
                               document_format: str = 'rdfxml',
                               namespace: str = None) -> None:
    """
    Saves a set of OWL class expressions to an ontology file in RDF/XML format.

    This function takes one or more OWL class expressions, creates an ontology,
    and saves the expressions as OWL equivalent class axioms in the specified format.
    The i-th expression becomes equivalent to the class ``<namespace>i``. The ontology is
    built and written with :class:`~owlapy.owl_ontology.RDFLibOntology`, so neither owlready2
    nor a JVM is needed. By default, it saves the file to the specified path using the
    'rdfxml' format.

    Args:
        expressions (OWLClassExpression | List[OWLClassExpression]): A single or a list of OWL class expressions
            to be saved as equivalent class axioms.
        path (str, optional): The file path where the ontology will be saved. Defaults to 'predictions'.
        document_format (str, optional): RDF serialization format for saving the ontology. Currently only
            supports 'rdfxml'. Defaults to 'rdfxml'.
        namespace (str, optional): The namespace URI used for the ontology. If None, defaults to
            'https://dice-research.org/predictions#'. Must end with '#'.

    Raises:
        AssertionError: If `expressions` is neither an OWLClassExpression nor a list of OWLClassExpression.
        AssertionError: If `document_format` is not 'rdfxml'.
        AssertionError: If `namespace` does not end with a '#'.

    Example:
        >>> from some_module import OWLClassExpression
        >>> expr1 = OWLClassExpression("SomeExpression1")
        >>> expr2 = OWLClassExpression("SomeExpression2")
        >>> save_owl_class_expressions([expr1, expr2], path="my_ontology.owl", document_format="rdfxml")
    """
    assert isinstance(expressions, OWLClassExpression) or isinstance(expressions[0],
                                                                     OWLClassExpression), "expressions must be either OWLClassExpression or a list of OWLClassExpression"
    assert document_format == 'rdfxml', f'Format {document_format} not implemented. Please use rdfxml'

    if isinstance(expressions, OWLClassExpression):
        expressions = [expressions]

    namespace = 'https://dice-research.org/predictions#' if namespace is None else namespace
    assert "#" == namespace[-1], "namespace must end with #"

    # Create a blank ontology whose IRI is the namespace without its trailing '#'. RDFLibOntology
    # writes complex class expressions following the OWL 2 -> RDF mapping, so no owlready2 is needed (#310).
    ontology = RDFLibOntology(namespace[:-1], load=False)
    # () Iterate over concepts
    for th, i in enumerate(expressions):
        cls_a = OWLClass(IRI.create(namespace, str(th)))
        equivalent_classes_axiom = OWLEquivalentClassesAxiom([cls_a, i])
        ontology.add_axiom(equivalent_classes_axiom)
    ontology.save(path=path, inplace=False, document_format=document_format)


def csv_to_rdf_kg(path_csv: str = None, path_kg: str = None, namespace: str = None):
    """
    Transfroms a CSV file to an RDF Knowledge Graph in RDF/XML format.

    Args:
        path_csv (str): X
        path_kg (str): X
        namespace (str): X

    Raises:
        AssertionError:

    Example:
        >>> from sklearn.datasets import load_iris
        >>> import pandas as pd
        # Load the dataset
        >>> data = load_iris()
        # Convert to DataFrame
        >>> df = pd.DataFrame(data.data, columns=data.feature_names)
        >>> df['target'] = data.target
        # Save as CSV
        >>> df.to_csv("iris_dataset.csv", index=False)
        >>> print("Dataset saved as iris_dataset.csv")
        >>> csv_to_rdf_kg("iris_dataset.csv")
    """
    assert path_csv is not None, "path cannot be None"
    assert os.path.exists(path_csv), f"path **{path_csv}**does not exist."
    assert path_kg is not None, f"path_kg cannot be None.Currently {path_kg}"
    assert namespace is not None, "namespace cannot be None"
    assert namespace[:7] == "http://", "First characters of namespace must be 'http://'"

    # Create an ontology given the namespace.
    ontology: SyncOntology = SyncOntology(namespace, load=False)

    # Read the CSV file
    df = pd.read_csv(path_csv)

    # () Iterate over rows
    for index, row in (tqdm_bar := tqdm(df.iterrows())):
        individual = OWLNamedIndividual(f"{namespace}#{str(index)}".replace(" ", "_"))
        tqdm_bar.set_description_str(f"Creating RDF Graph from Row:{index}")
        # column_name is considered as a predicate
        # value is considered as a data property
        for column_name, value in row.to_dict().items():
            # Create an IRI for the predicate
            str_property_iri = f"{namespace}#{column_name}".replace(" ", "_")
            str_property_iri = str_property_iri.replace("(", "/")
            str_property_iri = str_property_iri.replace(")", "")

            if isinstance(value, float) or isinstance(value, int) or isinstance(value, str):
                axiom = OWLDataPropertyAssertionAxiom(subject=individual,
                                                      property_=OWLDataProperty(iri=str_property_iri),
                                                      object_=OWLLiteral(value=value))
                ontology.add_axiom(axiom)
            else:
                raise NotImplementedError(f"How to represent\n"
                                          f"predicate=**{str_property_iri}**\n"
                                          f"value=**{value}**\n"
                                          f"has not been decided")
    ontology.save(path=path_kg)


def rdf_kg_to_csv(path_kg: str = None, path_csv: str = None):
    """
    Constructs a CSV file from an RDF Knowledge Graph (RDF/XML)

    Args:
        path_kg (str): Path to the RDF Knowledge Graph file (RDF/XML)
        path_csv (str): Path where the reconstructed CSV should be saved.

    Raises:
        AssertionError: If the provided paths are None or invalid.

    Example:
        >>> # Assuming you previously did:
        >>> # csv_to_rdf_kg("iris_dataset.csv", "iris_kg.owl", "http://example.com/iris")
        >>> rdf_kg_to_csv("iris_kg.owl", "reconstructed_iris_dataset.csv")
        >>> print("CSV reconstructed from RDF KG saved as reconstructed_iris_dataset.csv")
    """
    import os

    import pandas as pd

    # Validate arguments
    assert path_kg is not None, "path_kg cannot be None"
    assert path_csv is not None, "path_csv cannot be None"
    assert os.path.exists(path_kg), f"RDF Knowledge Graph file {path_kg} does not exist."

    # Load the ontology
    ontology = SyncOntology(path_kg, load=True)
    # Extract individuals and data property assertions
    rows = {}
    columns_list = []

    # We assume each individual corresponds to a row, and its IRI ends with '#<index>'.
    # Data properties correspond to columns, with IRIs ending in '#<modified_column_name>'.
    for axiom in ontology.get_abox_axioms():
        if isinstance(axiom, OWLDataPropertyAssertionAxiom):
            subject_ind = axiom.get_subject()
            property_exp = axiom.get_property()
            literal = axiom.get_object()
            literal_value = literal.get_literal()
            if literal_value == "nan":
                logger.warning(f"Skipping {axiom} as it has a NaN value")
                continue

            try:
                row_index = int(subject_ind.remainder)
            except ValueError:
                row_index = subject_ind.remainder

            # Extract column fragment from property IRI: namespace#<column_name>
            column_fragment = property_exp.iri.remainder.rsplit('#', 1)[-1]
            value = literal_value
            try:
                if '.' in literal_value:
                    value = float(literal_value)
                else:
                    value = int(literal_value)
            except ValueError:
                # keep as string if not numeric
                pass

            if row_index not in rows:
                rows[row_index] = {}
            rows[row_index][column_fragment] = value
            if column_fragment not in columns_list:
                columns_list.append(column_fragment)

    # Construct a DataFrame from the extracted data
    columns = columns_list
    row_indices = list(rows.keys())
    data_list = []

    for i in row_indices:
        row_data = [rows[i].get(col, None) for col in columns]
        data_list.append(row_data)

    df = pd.DataFrame(data_list, columns=columns)
    df.to_csv(path_csv, index=False, na_rep="")
    logger.info(f"CSV reconstructed and saved to {path_csv}")


def create_ontology(iri, with_owlapi=False):
    """Create a blank ontology with the given IRI.

    Args:
        iri: IRI of the new ontology.
        with_owlapi: If True, return an OWL API-backed :class:`SyncOntology` (starts the JVM).
            If False (default), return the owlready2-backed :class:`Ontology`.

    .. note::
        ``with_owlapi=False`` emits a ``FutureWarning``: in owlapy 2.0 it will return an
        :class:`RDFLibOntology` instead, because ``Ontology`` is removed (see #310). To opt in
        now, construct ``RDFLibOntology(iri, load=False)`` yourself.
    """
    if with_owlapi:
        return SyncOntology(iri, load=False)
    warnings.warn(
        "create_ontology(..., with_owlapi=False) returns the owlready2-backed Ontology, which is "
        "deprecated. In owlapy 2.0 it will return an RDFLibOntology instead. To opt in now, use "
        "RDFLibOntology(iri, load=False) directly (or with_owlapi=True for a SyncOntology). See issue #310.",
        FutureWarning,
        stacklevel=2,
    )
    return Ontology(iri, load=False)


def generate_ontology(graph_as_json: str = None,
                      output_path: str = "generated_ontology.owl",
                      output_format: str = "xml",
                      namespace: str = "http://example.org/",
                      generate_classes: bool = True,
                      base_url: str = None,
                      api_key: str = None,
                      model: str = None,
                      context: str = "",
                      temperature: float = 0.15
                      ):
    """
    Generates an ontology using quadruples from a given json file.

    Args:
        graph_as_json: Path to the json file that contains the nested data. Nested structure should look like following
            where a graph can have multiple quadruples and each quadruple can have multiple  subject-predicate-object
            triples:

                    {'graph':[
                        {
                            quadruples:[
                                {
                                    "subject": ...
                                    "predicate": ...
                                    "object": ...
                                },
                            ],
                        }
                    ]}
        output_path: Path to the output result (an ontology).
        output_format: The format the output should be written in. Chose from ["xml", "n3", "turtle", "nt",
            "pretty-xml", "trix", "trig", "nquads", "json-ld", "hext"].
        namespace: Namespace of the ontology.
        generate_classes: Whether you want to generate classes or not (should provide LLM arguments if True).
        base_url: Base URL for the OpenAI client.
        api_key: API key for the OpenAI client.
        model: Model name to use for class generation via OpenAI client.
        context: Additional context for the ontology. Used as assisting information during LLM prompts.
                Describe the ontology focus area, weak points that can help the LLM to understand the data better,
                including potential examples that may help identify entities better.
        temperature: Temperature to use for the LLM during class generation.
    """
    if generate_classes:
        assert base_url is not None and api_key is not None and model is not None,"Provide OpenAI client arguments: `base_url`, `api_key`, `model` or disable class generation."

    assert output_format in ["xml", "n3", "turtle", "nt", "pretty-xml", "trix", "trig", "nquads", "json-ld", "hext"], "Unsuported output format. Check docstrings."

    g = Graph()

    with open(graph_as_json) as json_file:
        data = json.load(json_file)

    ex = Namespace(namespace)
    g.bind("ex", ex)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("owl", OWL)
    seen_set = set()
    subjects = set()
    predicates = set()
    obj_for_pred = dict()
    triples_as_str = ""
    objects = set()
    graphs = data["graphs"]
    # First iteration to store data in memory for easy retrieval
    for graph in graphs:
        quadruples = graph["quadruples"]
        for quad in quadruples:
            sub = quad["subject"]
            pred = quad["predicate"]
            obj = quad["object"]
            if pred not in obj_for_pred.keys():
                obj_for_pred[pred] = set()
            subjects.add(sub)
            predicates.add(pred)
            objects.add(obj)
            obj_for_pred[pred].add(obj)
            triples_as_str += sub.replace(" ", "") + " " + pred.replace("_", "") + " " + obj.replace(" ", "") + "\n"

    # Second iteration to define the ontology
    for graph in graphs:
        quadruples = graph["quadruples"]
        for quad in quadruples:
            subj = quad["subject"].strip().replace(" ", "_")
            pred_original = quad["predicate"]
            pred = pred_original.strip().replace(" ", "_")
            obj = quad["object"].strip().replace(" ", "_")
            subject = URIRef(namespace + subj)
            predicate = URIRef(namespace + pred)
            obj_is_individual = len(obj_for_pred[pred_original].intersection(subjects)) > 0
            if pred_original not in seen_set:
                seen_set.add(pred_original)
                if obj_is_individual:
                    g.add((predicate, RDF.type, OWL.ObjectProperty))
                else:  # we consider it a literal since no occurrence in subjects set
                    g.add((predicate, RDF.type, OWL.DatatypeProperty))

            if obj_is_individual:
                g.add((subject, predicate, URIRef(namespace + obj)))
            else:
                try:
                    obj_val = int(quad["object"])  # noqa: F841
                    g.add((subject, predicate, Literal(quad["object"], datatype=XSD.integer)))
                except ValueError:
                    try:
                        obj_val = float(quad["object"])  # noqa: F841
                        g.add((subject, predicate, Literal(quad["object"], datatype=XSD.double)))
                    except ValueError:
                        g.add((subject, predicate, Literal(quad["object"], datatype=XSD.string)))

    if generate_classes:
        try:
            from openai import OpenAI
        except ModuleNotFoundError:
            logger.warning("Could not detect the openai module. Please install using `pip install openai`")
            exit(1)

        client = OpenAI(base_url=base_url, api_key=api_key)

        def generate_class_for_subject(s: str, triples: str):

            system = ("You are an expert in ontologies and semantic modeling. Your task is to analyze ontology triples "
                      "(in the form of subject-predicate-object) and generate a single named class (or type) for a given "
                      "subject. When answering, provide only the class name with no extra text, explanation, or formatting."
                      " For example, if the subject \"PaderbornUniversity\" corresponds to a university, respond with "
                      "\"University\" and nothing else. If you cant decide a class for a subject, search it on the internet"
                      " and try to come up with a class name.")
            query = ("I have the following ontology triples: \n"
                     f"{triples}"
                     f"Based on these triples, generate a named class for the subject {s}. Print only the class name.")

            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": query},
                          {"role": "assistant", "content": context}],
                temperature=temperature)
            generated_named_class = response.choices[0].message.content
            # print(f"Generated class '{generated_named_class}' for subject '{s}'")
            return generated_named_class

        generated_classes = set()
        # Class generation
        for sub in subjects:
            named_class = generate_class_for_subject(sub, triples_as_str)
            cls = URIRef(namespace + named_class.replace(" ", ""))
            if named_class == "Thing":
                cls = OWL.Thing
            elif named_class not in generated_classes:
                generated_classes.add(named_class)
                g.add((cls, RDF.type, OWL.Class))
            subj = sub.strip().replace(" ", "_")
            g.add((URIRef(namespace + subj), RDF.type, cls))

    g.serialize(destination=output_path, format=output_format)


def _load_rdflib_kb(kb_path):
    """Load ``kb_path`` with rdflib; returns the ontology wrapper and its graph."""
    onto = RDFLibOntology(kb_path)
    return onto, onto.rdflib_graph


def _iri(entity) -> URIRef:
    return URIRef(entity.str)


def make_kb_incomplete_ass(kb_path, output_path, rate, seed):
    """
    Makes the knowledge base incomplete by removing a certain percentage of property assertions.

    The candidate statements are all object and data property assertions whose subject is an
    individual of the knowledge base; ``rate`` percent of them are removed at random.

    Inputs:
    ---------------

    kb_path: Path to the input knowledge base.
    output_path: Path to save the modified (incomplete) knowledge base (RDF/XML).
    rate: Percentage of statements to remove (0-100).
    seed: random seed for reproducibility.

    Output:
    ---------------

    Incomplete KB at level rate %
    """
    rng = random.Random(seed)
    onto, g = _load_rdflib_kb(kb_path)

    properties = {_iri(p) for p in onto.object_properties_in_signature()} | {_iri(p) for p in onto.data_properties_in_signature()}
    all_triples = sorted(
        {(s, p, o) for ind in onto.individuals_in_signature() for s, p, o in g.triples((_iri(ind), None, None)) if p in properties},
        key=lambda t: (str(t[0]), str(t[1]), str(t[2])),
    )

    num_to_remove = int(len(all_triples) * (rate / 100))
    for triple in rng.sample(all_triples, num_to_remove):
        g.remove(triple)

    g.serialize(destination=output_path, format="xml")


def make_kb_incomplete(kb_path, output_path, rate, seed) -> Set[str]:
    """
    Makes the knowledge base incomplete by removing a certain percentage of individuals.

    A removed individual disappears completely: every triple that mentions it, as subject or as
    object, is deleted.

    Inputs:
    ---------------

    kb_path: Path to the input knowledge base.
    output_path: Path to save the modified (incomplete) knowledge base (RDF/XML).
    rate: Percentage of individuals to remove (0-100).
    seed: random seed for reproducibility.

    Output:
    ---------------

    The IRIs of the removed individuals.
    """
    rng = random.Random(seed)
    onto, g = _load_rdflib_kb(kb_path)

    all_individuals = sorted(_iri(i) for i in onto.individuals_in_signature())
    num_to_remove = int(len(all_individuals) * (rate / 100))
    individuals_to_remove = rng.sample(all_individuals, num_to_remove)

    for individual in individuals_to_remove:
        g.remove((individual, None, None))
        g.remove((None, None, individual))

    g.serialize(destination=output_path, format="xml")
    return {str(i) for i in individuals_to_remove}


def make_kb_inconsistent(kb_path, output_path, rate, seed, max_attempts=100):
    """
    This function makes the knowledge base (KB) inconsistent by introducing incorrect statements.

    ``rate`` percent of the number of triples in the KB are added as incorrect statements: either a
    class assertion to a class the individual does not belong to, or an object property assertion
    between two randomly chosen individuals that does not exist yet.

    Parameters:
    kb_path (str): Path to the original OWL ontology file.
    output_path (str): Path to save the inconsistent ontology file (RDF/XML).
    rate (float): Percentage of incorrect statements to introduce (0-100).
    seed (int): Seed for reproducibility.
    max_attempts (int): Maximum attempts to find a valid incorrect statement.

    Returns:
    list[str]: A description of every incorrect statement that was added.
    """
    rng = random.Random(seed)
    onto, g = _load_rdflib_kb(kb_path)

    all_individuals = sorted(_iri(i) for i in onto.individuals_in_signature())
    all_classes = sorted(_iri(c) for c in onto.classes_in_signature())
    all_object_properties = sorted(_iri(p) for p in onto.object_properties_in_signature())

    def generate_incorrect_class_assertion(individual):
        """Assert that the individual belongs to a class it does not belong to yet."""
        types = set(g.objects(individual, RDF.type))
        class_candidates = [cls for cls in all_classes if cls not in types]
        if not class_candidates:
            return None
        selected_class = rng.choice(class_candidates)
        g.add((individual, RDF.type, selected_class))
        message = f"Added incorrect class assertion: {individual} rdf:type {selected_class}"
        logger.info(message)
        return message

    def generate_incorrect_object_property(individual):
        """Assert an object property value the individual does not have yet."""
        if not all_object_properties:
            return None
        prop = rng.choice(all_object_properties)
        incorrect_object = rng.choice(all_individuals)
        if (individual, prop, incorrect_object) in g:
            return None
        g.add((individual, prop, incorrect_object))
        message = f"Added incorrect object property assertion: {individual} {prop} {incorrect_object}"
        logger.info(message)
        return message

    num_incorrect = int(len(g) * (rate / 100))
    inconsistencies = []
    if all_individuals:
        for _ in range(num_incorrect):
            for _attempt in range(max_attempts):
                individual = rng.choice(all_individuals)
                if rng.choice(["class", "object_property"]) == "class":
                    result = generate_incorrect_class_assertion(individual)
                else:
                    result = generate_incorrect_object_property(individual)
                if result:
                    inconsistencies.append(result)
                    break

    g.serialize(destination=output_path, format="xml")
    return inconsistencies
