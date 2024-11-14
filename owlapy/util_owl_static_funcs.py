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
    for index, row in tqdm(df.iterrows()):
        individual=OWLNamedIndividual(f"{namespace}#{str(index)}".replace(" ","_"))
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
