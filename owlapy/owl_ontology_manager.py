from typing import Union

import jpype
import owlready2

from owlapy.abstracts.abstract_owl_ontology_manager import AbstractOWLOntologyChange, AbstractOWLOntologyManager
from owlapy.iri import IRI
from owlapy.meta_classes import HasIRI
from owlapy.owl_ontology import Ontology, SyncOntology
from owlapy.abstracts.abstract_owl_ontology import AbstractOWLOntology
from owlapy.static_funcs import startJVM


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


class AddImport(AbstractOWLOntologyChange):
    """Represents an ontology change where an import statement is added to an ontology."""
    __slots__ = '_ont', '_declaration'

    def __init__(self, ontology: AbstractOWLOntology, import_declaration: OWLImportsDeclaration):
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


class OntologyManager(AbstractOWLOntologyManager):
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

    def load_ontology(self, path: Union[IRI, str] = None) -> Ontology:
        if isinstance(path, str):
            path_iri = IRI.create(path)
        else:
            assert isinstance(path, IRI), "iri either must be string or an instance of IRI Class"
            path_iri=path
        return Ontology(self, path_iri, load=True)

    def apply_change(self, change: AbstractOWLOntologyChange):
        if isinstance(change, AddImport):
            ont_x: owlready2.namespace.Ontology = self._world.get_ontology(
                change.get_ontology().get_ontology_id().get_ontology_iri().as_str())
            ont_x.imported_ontologies.append(
                self._world.get_ontology(change.get_import_declaration().str))
        else:
            raise NotImplementedError("Change is not yet implemented.")

    def save_world(self):
        """Saves the actual state of the quadstore in the SQLite3 file.
        """
        self._world.save()


class SyncOntologyManager(AbstractOWLOntologyManager):
    """
    Create OWLManager in Python
    https://owlcs.github.io/owlapi/apidocs_5/org/semanticweb/owlapi/apibinding/OWLManager.html
    """

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

    def apply_change(self, change: AbstractOWLOntologyChange):
        raise NotImplementedError("A change cannot be applied at the moment.")
