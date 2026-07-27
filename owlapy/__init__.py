import logging

from .converter import owl_expression_to_sparql, owl_expression_to_sparql_with_confusion_matrix
from .expressivity import get_dl_expressivity
from .owl_reasoner_rdflib import RDFLibReasoner
from .parser import dl_to_owl_expression, manchester_to_owl_expression
from .render import owl_expression_to_dl, owl_expression_to_manchester

__version__ = '1.6.6'

# Library best practice: attach a no-op handler to the package's top-level logger
# so owlapy never emits log output unless the host application configures logging.
# Consumers opt in via e.g. logging.getLogger("owlapy").setLevel(logging.INFO).
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    'owl_expression_to_dl', 'owl_expression_to_manchester',
    'dl_to_owl_expression', 'manchester_to_owl_expression',
    'owl_expression_to_sparql', 'owl_expression_to_sparql_with_confusion_matrix',
    'get_dl_expressivity',
    'RDFLibReasoner'
]
