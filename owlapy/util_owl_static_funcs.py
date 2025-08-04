from .owl_ontology import Ontology, SyncOntology
from .class_expression import OWLClassExpression, OWLClass
from .owl_individual import OWLNamedIndividual
from .iri import IRI
from .owl_axiom import OWLEquivalentClassesAxiom, OWLDataPropertyAssertionAxiom
from .owl_property import OWLDataProperty
from .owl_literal import OWLLiteral
import os
import json
import random
from typing import List, Set
from tqdm import tqdm
import pandas as pd
from rdflib import Graph, URIRef, Literal, RDFS, OWL, Namespace, RDF
from rdflib.namespace import XSD
from owlready2 import get_ontology, destroy_entity


def save_owl_class_expressions(expressions: OWLClassExpression | List[OWLClassExpression],
                               path: str = 'predictions',
                               rdf_format: str = 'rdfxml',
                               namespace: str = None) -> None:
    """
    Saves a set of OWL class expressions to an ontology file in RDF/XML format.

    This function takes one or more OWL class expressions, creates an ontology,
    and saves the expressions as OWL equivalent class axioms in the specified RDF format.
    By default, it saves the file to the specified path using the 'rdfxml' format.

    Args:
        expressions (OWLClassExpression | List[OWLClassExpression]): A single or a list of OWL class expressions
            to be saved as equivalent class axioms.
        path (str, optional): The file path where the ontology will be saved. Defaults to 'predictions'.
        rdf_format (str, optional): RDF serialization format for saving the ontology. Currently only
            supports 'rdfxml'. Defaults to 'rdfxml'.
        namespace (str, optional): The namespace URI used for the ontology. If None, defaults to
            'https://dice-research.org/predictions#'. Must end with '#'.

    Raises:
        AssertionError: If `expressions` is neither an OWLClassExpression nor a list of OWLClassExpression.
        AssertionError: If `rdf_format` is not 'rdfxml'.
        AssertionError: If `namespace` does not end with a '#'.

    Example:
        >>> from some_module import OWLClassExpression
        >>> expr1 = OWLClassExpression("SomeExpression1")
        >>> expr2 = OWLClassExpression("SomeExpression2")
        >>> save_owl_class_expressions([expr1, expr2], path="my_ontology.owl", rdf_format="rdfxml")
    """
    assert isinstance(expressions, OWLClassExpression) or isinstance(expressions[0],
                                                                     OWLClassExpression), "expressions must be either OWLClassExpression or a list of OWLClassExpression"
    assert rdf_format == 'rdfxml', f'Format {rdf_format} not implemented. Please use rdfxml'

    if isinstance(expressions, OWLClassExpression):
        expressions = [expressions]

    namespace = 'https://dice-research.org/predictions#' if namespace is None else namespace
    assert "#" == namespace[-1], "namespace must end with #"

    # Create an ontology given the namespace.
    ontology: Ontology = Ontology(namespace, load=False)
    # () Iterate over concepts
    for th, i in enumerate(expressions):
        cls_a = OWLClass(IRI.create(namespace, str(th)))
        equivalent_classes_axiom = OWLEquivalentClassesAxiom([cls_a, i])
        ontology.add_axiom(equivalent_classes_axiom)
    ontology.save(path=path, inplace=False, rdf_format=rdf_format)


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
                print(f"Skipping {axiom} as it has a NaN value")
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
    print(f"CSV reconstructed and saved to {path_csv}")


def create_ontology(iri, with_owlapi=False):
    """ A convenient function"""
    if with_owlapi:
        return SyncOntology(iri, load=False)
    else:
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
            print("Could not detect the openai module. Please install using `pip install openai`")
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


def make_kb_incomplete_ass(kb_path, output_path, rate, seed):
    """
    Makes the knowledge base incomplete by removing a certain percentage of statements (triples).

    Inputs:
    ---------------

    kb_path: Path to the input knowledge base.
    output_path: Path to save the modified (incomplete) knowledge base.
    rate: Percentage of statements to remove (0-100).
    seed: random seed for reproducibility.

    Output:
    ---------------

    Incomplete KB at level rate %
    """
    random.seed(seed)

    # Load the ontology
    kb = get_ontology(kb_path).load()

    # Get all individuals in the ontology
    all_individuals = list(kb.individuals())

    # Collect all triples (subject-predicate-object) related to the individuals
    all_triples = []
    for individual in all_individuals:
        for prop in individual.get_properties():
            for value in prop[individual]:
                all_triples.append((individual, prop, value))

    # Calculate the number of triples to remove based on the rate
    num_to_remove = int(len(all_triples) * (rate / 100))

    # Randomly select triples to remove
    triples_to_remove = random.sample(all_triples, num_to_remove)

    # Remove the selected triples
    for subject, predicate, obj in triples_to_remove:
        predicate[subject].remove(obj)

    # Save the modified ontology to a new file
    kb.save(file=output_path, format="rdfxml")


def make_kb_incomplete(kb_path, output_path, rate, seed) -> Set[str]:
    """
    Makes the knowledge base incomplete by removing a certain percentage of individuals.

    Inputs:
    ---------------

    kb_path: Path to the input knowledge base.
    output_path: Path to save the modified (incomplete) knowledge base.
    rate: Percentage of individuals to remove (0-100).
    seed: random seed for reproducibility.

    Output:
    ---------------

    Incomplete KB at level rate %
    """
    random.seed(seed)

    # Load the ontology
    kb = get_ontology(kb_path).load()

    # Get all individuals (instances) in the ABox
    all_individuals = list(kb.individuals())

    # Calculate the number of individuals to remove based on the rate
    num_to_remove = int(len(all_individuals) * (rate / 100))

    # Randomly select individuals to remove
    individuals_to_remove = random.sample(all_individuals, num_to_remove)

    # Remove the selected individuals
    for individual in individuals_to_remove:
        destroy_entity(individual)

    # Save the modified ontology to a new file
    kb.save(file=output_path, format="rdfxml")


def make_kb_inconsistent(kb_path, output_path, rate, seed, max_attempts=100):
    """
    This function makes the knowledge base (KB) inconsistent by introducing incorrect statements.

    Parameters:
    kb_path (str): Path to the original OWL ontology file.
    output_path (str): Path to save the inconsistent ontology file.
    rate (float): Percentage of incorrect statements to introduce (0-100).
    seed (int): Seed for reproducibility.
    max_attempts (int): Maximum attempts to find a valid incorrect statement.
    """

    # Set the random seed for reproducibility
    random.seed(seed)

    # Load the ontology
    onto = get_ontology(kb_path).load()

    # Get all individuals, classes, and properties
    all_individuals = list(onto.individuals())
    all_classes = list(onto.classes())
    all_object_properties = list(onto.object_properties())
    all_data_properties = list(onto.data_properties())

    def count_triples():
        """Count the number of triples (statements) in the ontology."""
        return len(list(onto.world.sparql("""
            SELECT ?s ?p ?o
            WHERE {
                ?s ?p ?o .
            }
        """)))

    def generate_incorrect_class_assertion(individual):
        """Generate an incorrect class assertion by adding a disjoint or contradictory class."""
        class_candidates = [cls for cls in all_classes if cls not in individual.is_a]
        if not class_candidates:
            return None

        selected_class = random.choice(class_candidates)
        individual.is_a.append(selected_class)
        print(f"Added incorrect class assertion: {individual} rdf:type {selected_class}")
        return f"Added incorrect class assertion: {individual} rdf:type {selected_class}"

    def generate_incorrect_object_property(individual):
        """Generate an incorrect object property assertion."""
        prop = random.choice(all_object_properties)
        incorrect_object = random.choice(all_individuals)

        if incorrect_object not in prop[individual]:
            prop[individual].append(incorrect_object)
            print(f"Added incorrect object property assertion: {individual} {prop.name} {incorrect_object}")
            return f"Added incorrect object property assertion: {individual} {prop.name} {incorrect_object}"

    def generate_incorrect_data_property(individual):
        """Generate an incorrect data property assertion (if exist in the KB)."""
        if len(all_data_properties) != 0:
            prop = random.choice(all_data_properties)
            incorrect_value = "inconsistent_value"  # Example of an incorrect data value

            if incorrect_value not in prop[individual]:
                setattr(individual, prop.name, incorrect_value)
                print(f"Added incorrect data property assertion: {individual} {prop.name} {incorrect_value}")
                return f"Added incorrect data property assertion: {individual} {prop.name} {incorrect_value}"

    def insert_incorrect_statements():
        """Insert incorrect statements based on the specified rate."""
        num_triples = count_triples()  # Use the total number of triples in the KB
        num_incorrect = int(num_triples * (rate / 100))

        incorrect_statements = []

        for _ in range(num_incorrect):
            attempts = 0
            while attempts < max_attempts:
                individual = random.choice(all_individuals)
                statement_type = random.choice(['class', 'object_property'])  # could also add data properties later on

                if statement_type == 'class':
                    result = generate_incorrect_class_assertion(individual)
                elif statement_type == 'object_property':
                    result = generate_incorrect_object_property(individual)

                if result:
                    incorrect_statements.append(result)
                    break

                attempts += 1

        return incorrect_statements

    # Insert incorrect statements
    inconsistencies = insert_incorrect_statements()

    # Save the modified ontology
    onto.save(file=output_path, format="rdfxml")

    # Return the list of inconsistencies added
    return inconsistencies

