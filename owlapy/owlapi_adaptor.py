import jpype.imports
import os

from owlapy import manchester_to_owl_expression
from owlapy.class_expression import OWLClassExpression
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.render import owl_expression_to_manchester

jar_folder = "../jar_dependencies"
jar_files = [os.path.join(jar_folder, f) for f in os.listdir(jar_folder) if f.endswith('.jar')]
jpype.startJVM(classpath=jar_files)

# Import Java classes
from org.semanticweb.owlapi.apibinding import OWLManager
from java.io import File
from org.semanticweb.HermiT import ReasonerFactory
from org.semanticweb.owlapi.manchestersyntax.parser import ManchesterOWLSyntaxClassExpressionParser
from org.semanticweb.owlapi.util import BidirectionalShortFormProviderAdapter, SimpleShortFormProvider
from org.semanticweb.owlapi.expression import ShortFormEntityChecker
from java.util import HashSet
from org.semanticweb.owlapi.model import OWLClassExpression as OWLClassExpressionOwlapi
from org.semanticweb.owlapi.manchestersyntax.renderer import ManchesterOWLSyntaxOWLObjectRendererImpl


class OWLAPIAdaptor:

    def __init__(self, path: str):
        file = File(path)
        self.manager = OWLManager.createOWLOntologyManager()
        self.ontology = self.manager.loadOntologyFromOntologyDocument(file)
        self.data_factory = self.manager.getOWLDataFactory()
        reasoner_factory = ReasonerFactory()
        self.reasoner = reasoner_factory.createReasoner(self.ontology)

        short_form_provider = SimpleShortFormProvider()
        ontology_set = HashSet()
        ontology_set.add(self.ontology)
        bidi_provider = BidirectionalShortFormProviderAdapter(self.manager, ontology_set, short_form_provider)
        entity_checker = ShortFormEntityChecker(bidi_provider)
        self.parser = ManchesterOWLSyntaxClassExpressionParser(self.data_factory, entity_checker)
        self.renderer = ManchesterOWLSyntaxOWLObjectRendererImpl()

    def convert_to_owlapi(self, ce: OWLClassExpression):
        """ Converts an owlapy ce to an owlapi ce

            Args:
                ce (OWLClassExpression): class expression in owlapy format to be converted.

            Return:
                Class expression in owlapi format.
        """
        return self.parser.parse(owl_expression_to_manchester(ce))

    def convert_from_owlapi(self, ce: OWLClassExpressionOwlapi, namespace: str) -> OWLClassExpression:
        """Converts an owlapi ce to an owlapy ce

            Args:
                ce: Class expression in owlapi format.
                namespace: Ontology's namespace where class expression belongs.

            Return:
                Class expression in owlapy format.
        """
        return manchester_to_owl_expression(str(self.renderer.render(ce)), namespace)

    def instances(self, ce: OWLClassExpression):
        """ Get the instances for a given class expression using HermiT.
            Args:
                ce: Class expression in owlapy format.

            Return:
                Individuals which are classified by the given class expression
        """
        inds = self.reasoner.getInstances(self.convert_to_owlapi(ce), False).getFlattened()
        return [OWLNamedIndividual(IRI.create(str(ind)[1:-1])) for ind in inds]

    def has_consistent_ontology(self) -> bool:
        """ Check if the used ontology is consistent."""
        return self.reasoner.isConsistent()

    def exit(self):
        """Shuts down the java virtual machine hosted by jpype."""
        jpype.shutdownJVM()
