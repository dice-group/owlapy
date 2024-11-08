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
        try:
            ontology.add_axiom(equivalent_classes_axiom)
        except AttributeError:
            print(traceback.format_exc())
            print("Exception at creating OWLEquivalentClassesAxiom")
            print(equivalent_classes_axiom)
            print(cls_a)
            print(i)
            print(expressions)
            exit(1)
    print(ontology)
    ontology.save(path=path, inplace=False, rdf_format=rdf_format)

    # ontology.save(IRI.create(path))
