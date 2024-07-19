import jpype.imports
import os
import pkg_resources

from owlapy import manchester_to_owl_expression
from owlapy.class_expression import OWLClassExpression
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.render import owl_expression_to_manchester
from typing import List


class OWLAPIAdaptor:
    """
    A class to interface with the OWL API using the HermiT reasoner, enabling ontology management,
    reasoning, and parsing class expressions in Manchester OWL Syntax.

    Attributes:
        path (str): The file path to the ontology.
        name_reasoner (str): The reasoner to be used, default is "HermiT".
        manager: The OWL ontology manager.
        ontology: The loaded OWL ontology.
        reasoner: Choose from (case-sensitive): ["HermiT", "Pellet", "JFact", "Openllet"]. Default: "HermiT".
        parser: The Manchester OWL Syntax parser.
        renderer: The Manchester OWL Syntax renderer.
    """

    def __init__(self, path: str, name_reasoner: str = "HermiT"):
        """
        Initialize the OWLAPIAdaptor with a path to an ontology and a reasoner name.

        Args:
            path (str): The file path to the ontology.
            name_reasoner (str, optional): The reasoner to be used.
                    Available options are: ['HermiT' (default), 'Pellet', 'JFact', 'Openllet'].

        Raises:
            AssertionError: If the provided reasoner name is not implemented.
        """
        self.path = path
        assert name_reasoner in ["HermiT", "Pellet", "JFact", "Openllet"], \
            f"'{name_reasoner}' is not implemented. Available reasoners: ['HermiT', 'Pellet', 'JFact', 'Openllet']"
        self.name_reasoner = name_reasoner
        # Attributes are initialized as JVM is started
        # () Manager is needed to load an ontology
        self.manager = None
        # () Load a local ontology using the manager
        self.ontology = None
        # () Create a reasoner for the loaded ontology
        self.reasoner = None
        self.parser = None
        # () A manchester renderer to render owlapi ce to manchester syntax
        self.renderer = None
        # () Set up the necessary attributes by making use of the java packages
        self._setup()

    def _startJVM(self):
        """Start the JVM with jar dependencies. This method is called automatically on object initialization, if the
        JVM is not started yet."""
        # Start a java virtual machine using the dependencies in the respective folder:
        jar_folder = pkg_resources.resource_filename('owlapy', 'jar_dependencies')
        jar_files = [os.path.join(jar_folder, f) for f in os.listdir(jar_folder) if f.endswith('.jar')]
        # Starting JVM.
        jpype.startJVM(classpath=jar_files)

    def stopJVM(self, *args, **kwargs) -> None:
        """Detaches the thread from Java packages and shuts down the java virtual machine hosted by jpype."""
        if jpype.isJVMStarted():
            jpype.detachThreadFromJVM()
            jpype.shutdownJVM()

    def _setup(self):
        """
        Start the JVM if not already, import necessary OWL API dependencies, and initialize attributes.
        """
        if not jpype.isJVMStarted():
            self._startJVM()

        # Import Java classes
        from org.semanticweb.owlapi.apibinding import OWLManager
        from java.io import File
        if self.name_reasoner == "HermiT":
            from org.semanticweb.HermiT import ReasonerFactory
        elif self.name_reasoner == "Pellet":
            from openllet.owlapi import PelletReasonerFactory
        elif self.name_reasoner == "JFact":
            from uk.ac.manchester.cs.jfact import JFactFactory
        elif self.name_reasoner == "Openllet":
            from openllet.owlapi import OpenlletReasonerFactory
        else:
            raise NotImplementedError("Not implemented")

        from org.semanticweb.owlapi.manchestersyntax.parser import ManchesterOWLSyntaxClassExpressionParser
        from org.semanticweb.owlapi.util import BidirectionalShortFormProviderAdapter, SimpleShortFormProvider, \
            InferredSubClassAxiomGenerator, InferredClassAssertionAxiomGenerator

        from org.semanticweb.owlapi.expression import ShortFormEntityChecker
        from java.util import HashSet, ArrayList
        from org.semanticweb.owlapi.manchestersyntax.renderer import ManchesterOWLSyntaxOWLObjectRendererImpl

        # () Manager is needed to load an ontology
        self.manager = OWLManager.createOWLOntologyManager()
        # () Load a local ontology using the manager
        self.ontology = self.manager.loadOntologyFromOntologyDocument(File(self.path))
        # () Create a reasoner for the loaded ontology
        if self.name_reasoner == "HermiT":
            self.reasoner = ReasonerFactory().createReasoner(self.ontology)
            assert self.reasoner.getReasonerName() == "HermiT"
        elif self.name_reasoner == "JFact":
            self.reasoner = JFactFactory().createReasoner(self.ontology)
        elif self.name_reasoner == "Pellet":
            self.reasoner = PelletReasonerFactory().createReasoner(self.ontology)
        elif self.name_reasoner == "Openllet":
            self.reasoner = OpenlletReasonerFactory().getInstance().createReasoner(self.ontology)

        # () Create a manchester parser and all the necessary attributes for parsing a manchester string to owlapi ce
        ontology_set = HashSet()
        ontology_set.add(self.ontology)
        bidi_provider = BidirectionalShortFormProviderAdapter(self.manager, ontology_set, SimpleShortFormProvider())
        entity_checker = ShortFormEntityChecker(bidi_provider)
        self.parser = ManchesterOWLSyntaxClassExpressionParser(self.manager.getOWLDataFactory(), entity_checker)
        # A manchester renderer to render owlapi ce to manchester syntax
        self.renderer = ManchesterOWLSyntaxOWLObjectRendererImpl()

    def infer_and_save(self, output_path:str=None, output_format:str=None, inference_types:list[str]=None):
        from java.io import File, FileOutputStream
        from java.util import ArrayList
        from org.semanticweb.owlapi.util import InferredSubClassAxiomGenerator, InferredClassAssertionAxiomGenerator
        from org.semanticweb.owlapi.util import InferredOntologyGenerator, InferredEquivalentClassAxiomGenerator,InferredInverseObjectPropertiesAxiomGenerator
        from org.semanticweb.owlapi.util import InferredDisjointClassesAxiomGenerator
        from org.semanticweb.owlapi.formats import TurtleDocumentFormat, RDFXMLDocumentFormat, OWLXMLDocumentFormat

        if output_format == "ttl" or output_format == "turtle":
            document_format = TurtleDocumentFormat()
        elif output_format == "rdf/xml":
            document_format = RDFXMLDocumentFormat()
        elif output_format == "owl/xml":
            document_format = OWLXMLDocumentFormat()
        else:
            document_format = self.manager.getOntologyFormat(self.ontology)
        generators = ArrayList()
        inference_types_mapping = {"InferredClassAssertionAxiomGenerator": InferredClassAssertionAxiomGenerator(),
                                   "InferredSubClassAxiomGenerator": InferredSubClassAxiomGenerator(),
                                   "InferredDisjointClassesAxiomGenerator":InferredDisjointClassesAxiomGenerator(),
                                   "InferredEquivalentClassAxiomGenerator":InferredEquivalentClassAxiomGenerator(),
                                   "InferredInverseObjectPropertiesAxiomGenerator":InferredInverseObjectPropertiesAxiomGenerator(),
                                   "InferredEquivalentClassAxiomGenerator":InferredEquivalentClassAxiomGenerator()}
        for i in inference_types:
            if java_object := inference_types_mapping.get(i, None):
                generators.add(java_object)

        iog = InferredOntologyGenerator(self.reasoner, generators)
        inferredAxiomsOntology = self.manager.createOntology()
        iog.fillOntology(self.manager.getOWLDataFactory(), inferredAxiomsOntology);
        inferredOntologyFile = File(output_path)
        inferredOntologyFile = inferredOntologyFile.getAbsoluteFile()
        outputStream = FileOutputStream(inferredOntologyFile)
        self.manager.saveOntology(inferredAxiomsOntology, document_format, outputStream);

    def generate_inferred_class_assertion_axioms(self, output="temp.ttl", output_format: str = None):
        """
        Generates inferred class assertion axioms for the ontology managed by this instance's reasoner and saves them to a file.

        This function uses the OWL API to generate inferred class assertion axioms based on the ontology and reasoner
        associated with this instance. The inferred axioms are saved to the specified output file in the desired format.

        Parameters:
        -----------
        output : str, optional
            The name of the file where the inferred axioms will be saved. Default is "temp.ttl".

        output_format : str, optional
            The format in which to save the inferred axioms. Supported formats are:
            - "ttl" or "turtle" for Turtle format
            - "rdf/xml" for RDF/XML format
            - "owl/xml" for OWL/XML format
            If not specified, the format of the original ontology is used.

        Notes:
        ------
        - The function supports saving in multiple formats: Turtle, RDF/XML, and OWL/XML.
        - The inferred axioms are generated using the reasoner associated with this instance and the OWL API's
          InferredClassAssertionAxiomGenerator.
        - The inferred axioms are added to a new ontology which is then saved in the specified format.

        Example:
        --------
        >>> instance.generate_inferred_class_assertion_axioms(output="inferred_axioms.ttl", format="ttl")

        This will save the inferred class assertion axioms to the file "inferred_axioms.ttl" in Turtle format.

        """
        from java.io import File, FileOutputStream
        from java.util import ArrayList
        from org.semanticweb.owlapi.util import InferredSubClassAxiomGenerator, InferredClassAssertionAxiomGenerator
        from org.semanticweb.owlapi.util import InferredOntologyGenerator
        from org.semanticweb.owlapi.formats import TurtleDocumentFormat, RDFXMLDocumentFormat, OWLXMLDocumentFormat
        if format == "ttl" or format == "turtle":
            document_format = TurtleDocumentFormat()
        elif format == "rdf/xml":
            document_format = RDFXMLDocumentFormat()
        elif format == "owl/xml":
            document_format = OWLXMLDocumentFormat()
        else:
            document_format = self.manager.getOntologyFormat(self.ontology)

        generators = ArrayList()

        # generators.add(InferredSubClassAxiomGenerator())
        generators.add(InferredClassAssertionAxiomGenerator())

        iog = InferredOntologyGenerator(self.reasoner, generators)
        inferredAxiomsOntology = self.manager.createOntology()
        iog.fillOntology(self.manager.getOWLDataFactory(), inferredAxiomsOntology);
        inferredOntologyFile = File(output)
        inferredOntologyFile = inferredOntologyFile.getAbsoluteFile()
        outputStream = FileOutputStream(inferredOntologyFile)
        self.manager.saveOntology(inferredAxiomsOntology, document_format, outputStream);

    def convert_to_owlapi(self, ce: OWLClassExpression):
        """
        Converts an OWLAPY class expression to an OWLAPI class expression.

        Args:
            ce (OWLClassExpression): The class expression in OWLAPY format to be converted.

        Returns:
            The class expression in OWLAPI format.
        """
        return self.parser.parse(owl_expression_to_manchester(ce))

    def convert_from_owlapi(self, ce, namespace: str) -> OWLClassExpression:
        """
        Converts an OWLAPI class expression to an OWLAPY class expression.

        Args:
            ce: The class expression in OWLAPI format.
            namespace (str): The ontology's namespace where the class expression belongs.

        Returns:
            OWLClassExpression: The class expression in OWLAPY format.
        """
        return manchester_to_owl_expression(str(self.renderer.render(ce)), namespace)

    def instances(self, ce: OWLClassExpression) -> List[OWLNamedIndividual]:
        """
        Get the instances for a given class expression using HermiT.

        Args:
            ce (OWLClassExpression): The class expression in OWLAPY format.

        Returns:
            list: A list of individuals classified by the given class expression.
        """
        inds = self.reasoner.getInstances(self.convert_to_owlapi(ce), False).getFlattened()
        return [OWLNamedIndividual(IRI.create(str(ind)[1:-1])) for ind in inds]

    def has_consistent_ontology(self) -> bool:
        """
        Check if the used ontology is consistent.

        Returns:
            bool: True if the ontology is consistent, False otherwise.
        """
        return self.reasoner.isConsistent()
