from abc import ABCMeta, abstractmethod
from owlapy.owl_ontology import OWLOntology
from owlapy.iri import IRI
from owlapy.meta_classes import HasIRI
from owlapy.owl_axiom import OWLAxiom


class OWLOntologyChange(metaclass=ABCMeta):
    """Represents an ontology change."""
    __slots__ = ()

    _ont: OWLOntology

    @abstractmethod
    def __init__(self, ontology: OWLOntology):
        self._ont = ontology

    def get_ontology(self) -> OWLOntology:
        """Gets the ontology that the change is/was applied to.

        Returns:
            The ontology that the change is applicable to.
        """
        return self._ont


class OWLOntologyManager(metaclass=ABCMeta):
    """An OWLOntologyManager manages a set of ontologies. It is the main point for creating, loading and accessing
    ontologies."""

    @abstractmethod
    def create_ontology(self, iri: IRI) -> OWLOntology:
        """Creates a new (empty) ontology that that has the specified ontology IRI (and no version IRI).

        Args:
            iri: The IRI of the ontology to be created.

        Returns:
            The newly created ontology, or if an ontology with the specified IRI already exists then this existing
            ontology will be returned.
        """
        pass

    @abstractmethod
    def load_ontology(self, iri: IRI) -> OWLOntology:
        """Loads an ontology that is assumed to have the specified ontology IRI as its IRI or version IRI. The ontology
        IRI will be mapped to an ontology document IRI.

        Args:
            iri: The IRI that identifies the ontology. It is expected that the ontology will also have this IRI
                (although the OWL API should tolerate situations where this is not the case).

        Returns:
            The OWLOntology representation of the ontology that was loaded.
        """
        pass

    @abstractmethod
    def apply_change(self, change: OWLOntologyChange):
        """A convenience method that applies just one change to an ontology. When this method is used through an
        OWLOntologyManager implementation, the instance used should be the one that the ontology returns through the
        get_owl_ontology_manager() call.

        Args:
            change: The change to be applied.

        Raises:
            ChangeApplied.UNSUCCESSFULLY: if the change was not applied successfully.
        """
        pass

    @abstractmethod
    def add_axiom(self, ontology: OWLOntology, axiom: OWLAxiom):
        """A convenience method that adds a single axiom to an ontology.

        Args:
            ontology: The ontology to add the axiom to.
            axiom: The axiom to be added.
        """
        pass

    @abstractmethod
    def remove_axiom(self, ontology: OWLOntology, axiom: OWLAxiom):
        """A convenience method that removes a single axiom from an ontology.

        Args:
            ontology: The ontology to remove the axiom from.
            axiom: The axiom to be removed.
        """
        pass

    @abstractmethod
    def save_ontology(self, ontology: OWLOntology, document_iri: IRI):
        """Saves the specified ontology, using the specified document IRI to determine where/how the ontology should be
        saved.

        Args:
            ontology: The ontology to be saved.
            document_iri: The document IRI where the ontology should be saved to.
        """
        pass


class OWLImportsDeclaration(HasIRI):
    """Represents an import statement in an ontology."""
    __slots__ = '_iri'

    def __init__(self, import_iri: IRI):
        """
        Args:
            import_iri: Imported ontology.

        Returns:
            An imports declaration.
        """
        self._iri = import_iri

    @property
    def iri(self) -> IRI:
        """Gets the import IRI.

        Returns:
            The import IRI that points to the ontology to be imported. The imported ontology might have this IRI as
            its ontology IRI but this is not mandated. For example, an ontology with a non-resolvable ontology IRI
            can be deployed at a resolvable URL.
        """
        return self._iri

    @property
    def str(self) -> str:
        return self._iri.as_str()


class AddImport(OWLOntologyChange):
    """Represents an ontology change where an import statement is added to an ontology."""
    __slots__ = '_ont', '_declaration'

    def __init__(self, ontology: OWLOntology, import_declaration: OWLImportsDeclaration):
        """
        Args:
            ontology: The ontology to which the change is to be applied.
            import_declaration: The import declaration.
        """
        super().__init__(ontology)
        self._declaration = import_declaration

    def get_import_declaration(self) -> OWLImportsDeclaration:
        """Gets the import declaration that the change pertains to.

        Returns:
            The import declaration.
        """
        return self._declaration
