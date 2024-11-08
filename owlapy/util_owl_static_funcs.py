from .owl_ontology import Ontology
from .owl_ontology_manager import OntologyManager
from typing import List
from .class_expression import OWLClassExpression, OWLClass
from .iri import IRI
from .owl_axiom import OWLEquivalentClassesAxiom

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
    # ()
    manager = OntologyManager()
    # ()
    ontology:Ontology = manager.create_ontology(namespace)
    # () Iterate over concepts
    for th, i in enumerate(expressions):
        cls_a = OWLClass(IRI.create(namespace, str(th)))
        equivalent_classes_axiom = OWLEquivalentClassesAxiom([cls_a, i])
        ontology.add_axiom(equivalent_classes_axiom)
    ontology.save(path=path, inplace=False, rdf_format=rdf_format)