import jpype.imports
import os

from owlapy import manchester_to_owl_expression
from owlapy.class_expression import OWLClassExpression
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.render import owl_expression_to_manchester


# TODO:What are the downsides of start() close() fashion ?:
class OWLAPIAdaptor:

    def __init__(self, path: str, reasoner: str = "HermiT"):
        self.path = path
        assert reasoner in ["HermiT"], f"{reasoner} is not implemented. Please use HermiT"
        self.reasoner = reasoner

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Shuts down the java virtual machine hosted by jpype."""
        if jpype.isJVMStarted() and not jpype.isThreadAttachedToJVM():
            jpype.shutdownJVM()

    def __enter__(self):
        """Initialization via the `with` statement"""
        if not jpype.isJVMStarted():
            # Start a java virtual machine using the dependencies in the respective folder:
            if os.getcwd()[-6:] == "owlapy":
                jar_folder = "jar_dependencies"
            else:
                jar_folder = "../jar_dependencies"
            jar_files = [os.path.join(jar_folder, f) for f in os.listdir(jar_folder) if f.endswith('.jar')]
            # Starting JVM.
            jpype.startJVM(classpath=jar_files)

        # Import Java classes
        from org.semanticweb.owlapi.apibinding import OWLManager
        from java.io import File
        if self.reasoner == "HermiT":
            from org.semanticweb.HermiT import ReasonerFactory
        else:
            raise NotImplementedError("Not implemented")

        from org.semanticweb.owlapi.manchestersyntax.parser import ManchesterOWLSyntaxClassExpressionParser
        from org.semanticweb.owlapi.util import BidirectionalShortFormProviderAdapter, SimpleShortFormProvider
        from org.semanticweb.owlapi.expression import ShortFormEntityChecker
        from java.util import HashSet
        from org.semanticweb.owlapi.manchestersyntax.renderer import ManchesterOWLSyntaxOWLObjectRendererImpl

        # () Manager is needed to load an ontology
        self.manager = OWLManager.createOWLOntologyManager()
        # () Load a local ontology using the manager
        self.ontology = self.manager.loadOntologyFromOntologyDocument(File(self.path))
        # () Create a HermiT reasoner for the loaded ontology
        self.reasoner = ReasonerFactory().createReasoner(self.ontology)

        # () Create a manchester parser and all the necessary attributes for parsing manchester syntax string to owlapi ce
        ontology_set = HashSet()
        ontology_set.add(self.ontology)
        bidi_provider = BidirectionalShortFormProviderAdapter(self.manager, ontology_set, SimpleShortFormProvider())
        entity_checker = ShortFormEntityChecker(bidi_provider)
        self.parser = ManchesterOWLSyntaxClassExpressionParser(self.manager.getOWLDataFactory(), entity_checker)

        # A manchester renderer to render owlapi ce to manchester syntax
        self.renderer = ManchesterOWLSyntaxOWLObjectRendererImpl()

        return self

    def convert_to_owlapi(self, ce: OWLClassExpression):
        """ Converts an owlapy ce to an owlapi ce.

            Args:
                ce (OWLClassExpression): class expression in owlapy format to be converted.

            Return:
                Class expression in owlapi format.
        """
        return self.parser.parse(owl_expression_to_manchester(ce))

    def convert_from_owlapi(self, ce, namespace: str) -> OWLClassExpression:
        """Converts an owlapi ce to an owlapy ce.

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
                Individuals which are classified by the given class expression.
        """
        inds = self.reasoner.getInstances(self.convert_to_owlapi(ce), False).getFlattened()
        return [OWLNamedIndividual(IRI.create(str(ind)[1:-1])) for ind in inds]

    def has_consistent_ontology(self) -> bool:
        """ Check if the used ontology is consistent."""
        return self.reasoner.isConsistent()


class DemoOWLAPIAdaptor(OWLAPIAdaptor):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.__start()

    @staticmethod
    def close(*args, **kwargs):
        """Shuts down the java virtual machine hosted by jpype."""
        if jpype.isJVMStarted() and not jpype.isThreadAttachedToJVM():
            jpype.shutdownJVM()

    def __start(self):
        """Initialization via the `with` statement"""
        if not jpype.isJVMStarted():
            # Start a java virtual machine using the dependencies in the respective folder:
            if os.getcwd()[-6:] == "owlapy":
                jar_folder = "jar_dependencies"
            else:
                jar_folder = "../jar_dependencies"
            jar_files = [os.path.join(jar_folder, f) for f in os.listdir(jar_folder) if f.endswith('.jar')]
            # Starting JVM.
            jpype.startJVM(classpath=jar_files)

        # Import Java classes
        from org.semanticweb.owlapi.apibinding import OWLManager
        from java.io import File
        if self.reasoner == "HermiT":
            from org.semanticweb.HermiT import ReasonerFactory
        else:
            raise NotImplementedError("Not implemented")

        from org.semanticweb.owlapi.manchestersyntax.parser import ManchesterOWLSyntaxClassExpressionParser
        from org.semanticweb.owlapi.util import BidirectionalShortFormProviderAdapter, SimpleShortFormProvider
        from org.semanticweb.owlapi.expression import ShortFormEntityChecker
        from java.util import HashSet
        from org.semanticweb.owlapi.manchestersyntax.renderer import ManchesterOWLSyntaxOWLObjectRendererImpl

        # () Manager is needed to load an ontology
        self.manager = OWLManager.createOWLOntologyManager()
        # () Load a local ontology using the manager
        self.ontology = self.manager.loadOntologyFromOntologyDocument(File(self.path))
        # () Create a HermiT reasoner for the loaded ontology
        self.reasoner = ReasonerFactory().createReasoner(self.ontology)

        # () Create a manchester parser and all the necessary attributes for parsing manchester syntax string to owlapi ce
        ontology_set = HashSet()
        ontology_set.add(self.ontology)
        bidi_provider = BidirectionalShortFormProviderAdapter(self.manager, ontology_set, SimpleShortFormProvider())
        entity_checker = ShortFormEntityChecker(bidi_provider)
        self.parser = ManchesterOWLSyntaxClassExpressionParser(self.manager.getOWLDataFactory(), entity_checker)

        # A manchester renderer to render owlapi ce to manchester syntax
        self.renderer = ManchesterOWLSyntaxOWLObjectRendererImpl()

        return self
