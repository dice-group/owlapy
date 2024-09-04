from abc import ABCMeta, abstractmethod
from typing import Union

import jpype
import owlready2

from owlapy.iri import IRI
from owlapy.meta_classes import HasIRI
from owlapy.owl_ontology import OWLOntology, Ontology, SyncOntology
from owlapy.static_funcs import startJVM


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
    def create_ontology(self, iri: Union[str, IRI]) -> OWLOntology:
        """Creates a new (empty) ontology that that has the specified ontology IRI (and no version IRI).

        Args:
            iri: The IRI of the ontology to be created, can also be a string.

        Returns:
            The newly created ontology.
        """
        pass

    @abstractmethod
    def load_ontology(self, iri: Union[IRI, str]) -> OWLOntology:
        """Loads an ontology that is assumed to have the specified ontology IRI as its IRI or version IRI. The ontology
        IRI will be mapped to an ontology document IRI.

        Args:
            iri: The IRI that identifies the ontology, can also be a string.
                 It is expected that the ontology will also have this IRI
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


class OntologyManager(OWLOntologyManager):
    __slots__ = '_world'

    _world: owlready2.namespace.World

    def __init__(self, world_store=None):
        """Ontology manager in Ontolearn.
        Creates a world where ontology is loaded.
        Used to make changes in the ontology.

        Args:
            world_store: The file name of the world store. Leave to default value to create a new world.
        """
        if world_store is None:
            self._world = owlready2.World()
        else:
            self._world = owlready2.World(filename=world_store)

    def create_ontology(self, iri: Union[str, IRI] = None) -> Ontology:
        if isinstance(iri, str):
            iri = IRI.create(iri)
        else:
            assert isinstance(iri, IRI), "iri either must be string or an instance of IRI Class"
        return Ontology(self, iri, load=False)

    def load_ontology(self, iri: Union[IRI, str] = None) -> Ontology:
        if isinstance(iri, str):
            iri = IRI.create(iri)
        else:
            assert isinstance(iri, IRI), "iri either must be string or an instance of IRI Class"
        return Ontology(self, iri, load=True)

    def apply_change(self, change: OWLOntologyChange):
        if isinstance(change, AddImport):
            ont_x: owlready2.namespace.Ontology = self._world.get_ontology(
                change.get_ontology().get_ontology_id().get_ontology_iri().as_str())
            ont_x.imported_ontologies.append(
                self._world.get_ontology(change.get_import_declaration().str))
        else:
            # TODO XXX
            raise NotImplementedError

    def save_world(self):
        """Saves the actual state of the quadstore in the SQLite3 file.
        """
        self._world.save()


class SyncOntologyManager(OWLOntologyManager):

    # WARN: Do not move local imports to top of the module
    def __init__(self):
        if not jpype.isJVMStarted():
            startJVM()
        from org.semanticweb.owlapi.apibinding import OWLManager
        self.owlapi_manager = OWLManager.createOWLOntologyManager()

    def create_ontology(self, iri: Union[IRI, str]) -> SyncOntology:
        if isinstance(iri, str):
            iri = IRI.create(iri)
        else:
            assert isinstance(iri, IRI), "iri either must be string or an instance of IRI Class"
        return SyncOntology(self, iri, new=True)

    def load_ontology(self, iri: Union[IRI, str]) -> SyncOntology:
        return SyncOntology(self, iri, new=False)

    def get_owlapi_manager(self):
        return self.owlapi_manager

    def apply_change(self, change: OWLOntologyChange):
        raise NotImplementedError()
