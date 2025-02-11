from .owl_ontology import Ontology, SyncOntology
from .owl_ontology_manager import OntologyManager
from .class_expression import OWLClassExpression, OWLClass
from .owl_individual import OWLNamedIndividual
from .iri import IRI
from .owl_axiom import OWLEquivalentClassesAxiom, OWLDataPropertyAssertionAxiom
from .owl_property import OWLDataProperty
from .owl_literal import OWLLiteral
import os
from typing import List
from tqdm import tqdm
import pandas as pd

def save_owl_class_expressions(expressions: OWLClassExpression | List[OWLClassExpression],
                               path: str = 'predictions',
                               rdf_format: str = 'rdfxml',
                               namespace:str=None) -> None:
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

    namespace= 'https://dice-research.org/predictions#' if namespace is None else namespace
    assert "#" == namespace[-1], "namespace must end with #"
    # Initialize an Ontology Manager.
    manager = OntologyManager()
    # Create an ontology given an ontology manager.
    ontology:Ontology = manager.create_ontology(namespace)
    # () Iterate over concepts
    for th, i in enumerate(expressions):
        cls_a = OWLClass(IRI.create(namespace, str(th)))
        equivalent_classes_axiom = OWLEquivalentClassesAxiom([cls_a, i])
        ontology.add_axiom(equivalent_classes_axiom)
    ontology.save(path=path, inplace=False, rdf_format=rdf_format)

def csv_to_rdf_kg(path_csv:str=None,path_kg:str=None,namespace:str=None):
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
    from owlapy.owl_ontology_manager import SyncOntologyManager
    assert path_csv is not None, "path cannot be None"
    assert os.path.exists(path_csv), f"path **{path_csv}**does not exist."
    assert path_kg is not None, f"path_kg cannot be None.Currently {path_kg}"
    assert namespace is not None, "namespace cannot be None"
    assert namespace[:7]=="http://", "First characters of namespace must be 'http://'"

    # Initialize an Ontology Manager.
    manager = SyncOntologyManager()
    # Create an ontology given an ontology manager.
    ontology:SyncOntology = manager.create_ontology(namespace)

    # Read the CSV file
    df = pd.read_csv(path_csv)

    # () Iterate over rows
    for index, row in (tqdm_bar := tqdm(df.iterrows()) ):
        individual=OWLNamedIndividual(f"{namespace}#{str(index)}".replace(" ","_"))
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
    from owlapy.owl_ontology_manager import SyncOntologyManager

    # Validate arguments
    assert path_kg is not None, "path_kg cannot be None"
    assert path_csv is not None, "path_csv cannot be None"
    assert os.path.exists(path_kg), f"RDF Knowledge Graph file {path_kg} does not exist."

    # Load the ontology
    manager = SyncOntologyManager()
    ontology = manager.load_ontology(path_kg)
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
                row_index = int(subject_ind.reminder)
            except ValueError:
                row_index = subject_ind.reminder

            # Extract column fragment from property IRI: namespace#<column_name>
            column_fragment = property_exp.iri.reminder.rsplit('#', 1)[-1]
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
