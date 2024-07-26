"""Owlapi Adaptor

Part of the docstrings are taken directly from owlapi
"""
import jpype.imports
import os
import pkg_resources

from owlapy.class_expression import OWLClassExpression
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty
from typing import List


def to_list(stream_obj):
    """Converts Java Stream object to Python list"""
    return stream_obj.collect(jpype.JClass("java.util.stream.Collectors").toList())


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
        namespace: Namespace(IRI) of the OWL ontology.
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
            (f"'{name_reasoner}' is not implemented. Available reasoners: ['HermiT', 'Pellet', 'JFact', 'Openllet']. "
             f"This field is case sensitive.")
        self.name_reasoner = name_reasoner
        # Attributes are initialized as JVM is started
        # () Manager is needed to load an ontology
        self.manager = None
        # () Load a local ontology using the manager
        self.ontology = None
        # () Create a reasoner for the loaded ontology
        self.reasoner = None
        # () For mapping entities/expressions from/to owlapi
        self.mapper = None
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

        # Imports
        from owlapy.owlapi_mapper import OWLAPIMapper
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

        # () Manager is needed to load an ontology
        self.manager = OWLManager.createOWLOntologyManager()
        # () Load a local ontology using the manager
        self.ontology = self.manager.loadOntologyFromOntologyDocument(File(self.path))
        self.mapper = OWLAPIMapper(self.ontology)

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

    def has_consistent_ontology(self) -> bool:
        """
        Check if the used ontology is consistent.

        Returns:
            bool: True if the ontology is consistent, False otherwise.
        """
        return self.reasoner.isConsistent()

    def instances(self, ce: OWLClassExpression, direct=False) -> List[OWLNamedIndividual]:
        """
        Get the instances for a given class expression using HermiT.

        Args:
            ce (OWLClassExpression): The class expression in OWLAPY format.
            direct (bool): Whether to get direct instances or not. Defaults to False.

        Returns:
            list: A list of individuals classified by the given class expression.
        """
        inds = self.reasoner.getInstances(self.mapper.map_(ce), direct).getFlattened()
        return [self.mapper.map_(ind) for ind in inds]

    def equivalent_classes(self, ce: OWLClassExpression) -> List[OWLClassExpression]:
        """
        Gets the set of named classes that are equivalent to the specified class expression with
        respect to the set of reasoner axioms.

        Args:
            ce (OWLClassExpression): The class expression whose equivalent classes are to be retrieved.

        Returns:
            Equivalent classes of the given class expression.
        """
        classes = self.reasoner.getEquivalentClasses(self.mapper.map_(ce)).getEntities()
        yield from [self.mapper.map_(cls) for cls in classes]

    def disjoint_classes(self, ce: OWLClassExpression) -> List[OWLClassExpression]:
        """
        Gets the classes that are disjoint with the specified class expression.

        Args:
            ce (OWLClassExpression): The class expression whose disjoint classes are to be retrieved.

        Returns:
            Disjoint classes of the given class expression.
        """
        classes = self.reasoner.getDisjointClasses(self.mapper.map_(ce)).getFlattened()
        yield from [self.mapper.map_(cls) for cls in classes]

    def sub_classes(self, ce: OWLClassExpression, direct=False) -> List[OWLClassExpression]:
        """
         Gets the set of named classes that are the strict (potentially direct) subclasses of the
         specified class expression with respect to the reasoner axioms.

         Args:
             ce (OWLClassExpression): The class expression whose strict (direct) subclasses are to be retrieved.
             direct (bool, optional): Specifies if the direct subclasses should be retrieved (True) or if
                all subclasses (descendant) classes should be retrieved (False). Defaults to False.
        Returns:
            The subclasses of the given class expression depending on `direct` field.
        """
        classes = self.reasoner.getSubClasses(self.mapper.map_(ce), direct).getFlattened()
        yield from [self.mapper.map_(cls) for cls in classes]

    def super_classes(self, ce: OWLClassExpression, direct=False) -> List[OWLClassExpression]:
        """
        Gets the stream of named classes that are the strict (potentially direct) super classes of
        the specified class expression with respect to the imports closure of the root ontology.

        Args:
             ce (OWLClassExpression): The class expression whose strict (direct) subclasses are to be retrieved.
             direct (bool, optional): Specifies if the direct superclasses should be retrieved (True) or if
                all superclasses (descendant) classes should be retrieved (False). Defaults to False.

        Returns:
            The subclasses of the given class expression depending on `direct` field.
        """
        classes = self.reasoner.getSuperClasses(self.mapper.map_(ce), direct).getFlattened()
        yield from [self.mapper.map_(cls) for cls in classes]

    def data_property_domains(self, p: OWLDataProperty, direct: bool = False):
        """Gets the class expressions that are the direct or indirect domains of this property with respect to the
           imports closure of the root ontology.

        Args:
            p: The property expression whose domains are to be retrieved.
            direct: Specifies if the direct domains should be retrieved (True), or if all domains should be retrieved
                (False).

        Returns:
            :Let N = equivalent_classes(DataSomeValuesFrom(pe rdfs:Literal)). If direct is True: then if N is not
            empty then the return value is N, else the return value is the result of
            super_classes(DataSomeValuesFrom(pe rdfs:Literal), true). If direct is False: then the result of
            super_classes(DataSomeValuesFrom(pe rdfs:Literal), false) together with N if N is non-empty.
            (Note, rdfs:Literal is the top datatype).
        """
        yield from [self.mapper.map_(ce) for ce in
                    self.reasoner.getDataPropertyDomains(self.mapper.map_(p), direct).getFlattened()]

    def object_property_domains(self, p: OWLObjectProperty, direct: bool = False):
        """Gets the class expressions that are the direct or indirect domains of this property with respect to the
           imports closure of the root ontology.

        Args:
            p: The property expression whose domains are to be retrieved.
            direct: Specifies if the direct domains should be retrieved (True), or if all domains should be retrieved
                (False).

        Returns:
            :Let N = equivalent_classes(ObjectSomeValuesFrom(pe owl:Thing)). If direct is True: then if N is not empty
            then the return value is N, else the return value is the result of
            super_classes(ObjectSomeValuesFrom(pe owl:Thing), true). If direct is False: then the result of
            super_classes(ObjectSomeValuesFrom(pe owl:Thing), false) together with N if N is non-empty.
        """
        yield from [self.mapper.map_(ce) for ce in
                    self.reasoner.getObjectPropertyDomains(self.mapper.map_(p), direct).getFlattened()]

    def object_property_ranges(self, p: OWLObjectProperty, direct: bool = False):
        """Gets the class expressions that are the direct or indirect ranges of this property with respect to the
           imports closure of the root ontology.

        Args:
            p: The property expression whose ranges are to be retrieved.
            direct: Specifies if the direct ranges should be retrieved (True), or if all ranges should be retrieved
                (False).

        Returns:
            :Let N = equivalent_classes(ObjectSomeValuesFrom(ObjectInverseOf(pe) owl:Thing)). If direct is True: then
            if N is not empty then the return value is N, else the return value is the result of
            super_classes(ObjectSomeValuesFrom(ObjectInverseOf(pe) owl:Thing), true). If direct is False: then
            the result of super_classes(ObjectSomeValuesFrom(ObjectInverseOf(pe) owl:Thing), false) together with N
            if N is non-empty.
        """
        yield from [self.mapper.map_(ce) for ce in
                    self.reasoner.getObjectPropertyRanges(self.mapper.map_(p), direct).getFlattened()]

    def sub_object_properties(self, p: OWLObjectProperty, direct: bool = False):
        """Gets the stream of simplified object property expressions that are the strict (potentially direct)
        subproperties of the specified object property expression with respect to the imports closure of the root
        ontology.

        Args:
            p: The object property expression whose strict (direct) subproperties are to be retrieved.
            direct: Specifies if the direct subproperties should be retrieved (True) or if the all subproperties
                (descendants) should be retrieved (False).

        Returns:
            If direct is True, simplified object property expressions, such that for each simplified object property
            expression, P, the set of reasoner axioms entails DirectSubObjectPropertyOf(P, pe).
            If direct is False, simplified object property expressions, such that for each simplified object property
            expression, P, the set of reasoner axioms entails StrictSubObjectPropertyOf(P, pe).
            If pe is equivalent to owl:bottomObjectProperty then nothing will be returned.
        """
        yield from [self.mapper.map_(pe) for pe in
                    self.reasoner.getSubObjectProperties(self.mapper.map_(p), direct).getFlattened()]

    def super_object_properties(self, p: OWLObjectProperty, direct: bool = False):
        """Gets the stream of object properties that are the strict (potentially direct) super properties of the
         specified object property with respect to the imports closure of the root ontology.

         Args:
             p (OWLObjectPropertyExpression): The object property expression whose super properties are to be
                                                retrieved.
             direct (bool): Specifies if the direct super properties should be retrieved (True) or if the all
                            super properties (ancestors) should be retrieved (False).

         Returns:
             Iterable of super properties.
         """
        yield from [self.mapper.map_(pe) for pe in
                    self.reasoner.getSuperObjectProperties(self.mapper.map_(p), direct).getFlattened()]

    def sub_data_properties(self, p: OWLDataProperty, direct: bool = False):
        """Gets the set of named data properties that are the strict (potentially direct) subproperties of the
        specified data property expression with respect to the imports closure of the root ontology.

        Args:
            p: The data property whose strict (direct) subproperties are to be retrieved.
            direct: Specifies if the direct subproperties should be retrieved (True) or if the all subproperties
                (descendants) should be retrieved (False).

        Returns:
            If direct is True, each property P where the set of reasoner axioms entails DirectSubDataPropertyOf(P, pe).
            If direct is False, each property P where the set of reasoner axioms entails
            StrictSubDataPropertyOf(P, pe). If pe is equivalent to owl:bottomDataProperty then nothing will be
            returned.
        """
        yield from [self.mapper.map_(pe) for pe in
                    self.reasoner.getSubDataProperties(self.mapper.map_(p), direct).getFlattened()]

    def super_data_properties(self, p: OWLDataProperty, direct: bool = False):
        """Gets the stream of data properties that are the strict (potentially direct) super properties of the
         specified data property with respect to the imports closure of the root ontology.

         Args:
             p (OWLDataProperty): The data property whose super properties are to be retrieved.
             direct (bool): Specifies if the direct super properties should be retrieved (True) or if the all
                            super properties (ancestors) should be retrieved (False).

         Returns:
             Iterable of super properties.
         """
        yield from [self.mapper.map_(pe) for pe in
                    self.reasoner.getSuperDataProperties(self.mapper.map_(p), direct).getFlattened()]

    def different_individuals(self, i: OWLNamedIndividual):
        """Gets the individuals that are different from the specified individual with respect to the set of
        reasoner axioms.

        Args:
            i: The individual whose different individuals are to be retrieved.

        Returns:
            All individuals x where the set of reasoner axioms entails DifferentIndividuals(ind x).
        """
        yield from [self.mapper.map_(ind) for ind in
                    self.reasoner.getDifferentIndividuals(self.mapper.map_(i)).getFlattened()]

    def same_individuals(self, i: OWLNamedIndividual):
        """Gets the individuals that are the same as the specified individual with respect to the set of
        reasoner axioms.

        Args:
            i: The individual whose same individuals are to be retrieved.

        Returns:
            All individuals x where the root ontology imports closure entails SameIndividual(ind x).
        """
        yield from [self.mapper.map_(ind) for ind in
                    to_list(self.reasoner.sameIndividuals(self.mapper.map_(i)))]

    def equivalent_object_properties(self, p: OWLObjectProperty):
        """Gets the simplified object properties that are equivalent to the specified object property with respect
        to the set of reasoner axioms.

        Args:
            p: The object property whose equivalent object properties are to be retrieved.

        Returns:
            All simplified object properties e where the root ontology imports closure entails
            EquivalentObjectProperties(op e). If op is unsatisfiable with respect to the set of reasoner axioms
            then owl:bottomDataProperty will be returned.
        """
        yield from [self.mapper.map_(pe) for pe in
                    to_list(self.reasoner.equivalentObjectProperties(self.mapper.map_(p)))]

    def equivalent_data_properties(self, p: OWLDataProperty):
        """Gets the data properties that are equivalent to the specified data property with respect to the set of
        reasoner axioms.

        Args:
            p: The data property whose equivalent data properties are to be retrieved.

        Returns:
            All data properties e where the root ontology imports closure entails EquivalentDataProperties(dp e).
            If dp is unsatisfiable with respect to the set of reasoner axioms then owl:bottomDataProperty will
            be returned.
        """
        yield from [self.mapper.map_(pe) for pe in
                    to_list(self.reasoner.getEquivalentDataProperties(self.mapper.map_(p)))]

    def object_property_values(self, i: OWLNamedIndividual, p: OWLObjectProperty):
        """Gets the object property values for the specified individual and object property expression.

        Args:
            i: The individual that is the subject of the object property values.
            p: The object property expression whose values are to be retrieved for the specified individual.

        Returns:
            The named individuals such that for each individual j, the set of reasoner axioms entails
            ObjectPropertyAssertion(pe ind j).
        """
        yield from [self.mapper.map_(ind) for ind in
                    self.reasoner.getObjectPropertyValues(self.mapper.map_(i), self.mapper.map_(p)).getFlattened()]

    def data_property_values(self, i: OWLNamedIndividual, p: OWLDataProperty):
        """Gets the data property values for the specified individual and data property expression.

        Args:
            i: The individual that is the subject of the data property values.
            p: The data property expression whose values are to be retrieved for the specified individual.

        Returns:
            A set of OWLLiterals containing literals such that for each literal l in the set, the set of reasoner
            axioms entails DataPropertyAssertion(pe ind l).
        """
        yield from [self.mapper.map_(literal) for literal in
                    to_list(self.reasoner.dataPropertyValues(self.mapper.map_(i), self.mapper.map_(p)))]

    def disjoint_object_properties(self, p: OWLObjectProperty):
        """Gets the simplified object properties that are disjoint with the specified object property with respect
        to the set of reasoner axioms.

        Args:
            p: The object property whose disjoint object properties are to be retrieved.

        Returns:
            All simplified object properties e where the root ontology imports closure entails
            EquivalentObjectProperties(e ObjectPropertyComplementOf(op)) or
            StrictSubObjectPropertyOf(e ObjectPropertyComplementOf(op)).
        """
        yield from [self.mapper.map_(pe) for pe in
                    self.reasoner.getDisjointObjectProperties(self.mapper.map_(p)).getFlattened()]

    def disjoint_data_properties(self, p: OWLDataProperty):
        """Gets the data properties that are disjoint with the specified data property with respect
        to the set of reasoner axioms.

        Args:
            p: The data property whose disjoint data properties are to be retrieved.

        Returns:
            All data properties e where the root ontology imports closure entails
            EquivalentDataProperties(e DataPropertyComplementOf(dp)) or
            StrictSubDataPropertyOf(e DataPropertyComplementOf(dp)).
        """
        yield from [self.mapper.map_(pe) for pe in
                    self.reasoner.getDisjointDataProperties(self.mapper.map_(p)).getFlattened()]

    def types(self, i: OWLNamedIndividual, direct: bool = False):
        """Gets the named classes which are (potentially direct) types of the specified named individual.

        Args:
            i: The individual whose types are to be retrieved.
            direct: Specifies if the direct types should be retrieved (True), or if all types should be retrieved
                (False).

        Returns:
            If direct is True, each named class C where the set of reasoner axioms entails
            DirectClassAssertion(C, ind). If direct is False, each named class C where the set of reasoner axioms
            entails ClassAssertion(C, ind).
        """
        yield from [self.mapper.map_(ind) for ind in
                    self.reasoner.getTypes(self.mapper.map_(i), direct).getFlattened()]

    def infer_and_save(self, output_path: str = None, output_format: str = None, inference_types: list[str] = None):
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
        inferred_axioms_ontology = self.manager.createOntology()
        iog.fillOntology(self.manager.getOWLDataFactory(), inferred_axioms_ontology)
        inferred_ontology_file = File(output_path).getAbsoluteFile()
        output_stream = FileOutputStream(inferred_ontology_file)
        self.manager.saveOntology(inferred_axioms_ontology, document_format, output_stream)

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
        self.infer_and_save(output, output_format, ["InferredClassAssertionAxiomGenerator"])
