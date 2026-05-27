"""RDFLib-based OWL Reasoner - Pure Python implementation."""
import logging
from typing import Dict, FrozenSet, Iterable, Optional, Set, Union

from rdflib import Graph, URIRef

from owlapy.abstracts.abstract_owl_ontology import AbstractOWLOntology
from owlapy.abstracts.abstract_owl_reasoner import AbstractOWLReasoner
from owlapy.class_expression import (
    OWLClass,
    OWLClassExpression,
)
from owlapy.converter import owl_expression_to_sparql
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import Ontology, SyncOntology
from owlapy.owl_property import OWLObjectProperty, OWLObjectPropertyExpression

logger = logging.getLogger(__name__)


class RDFLibReasoner(AbstractOWLReasoner):
    """
    A pure Python OWL reasoner based on RDFLib.

    This reasoner uses SPARQL queries over an RDF graph to perform reasoning tasks.
    It's designed as a drop-in replacement for StructuralReasoner with better
    predictability and no owlready2/Java dependencies for basic operations.

    Features:
    - Pure Python implementation using RDFLib
    - SPARQL-based reasoning
    - Efficient graph traversal with caching
    - Support for basic OWL 2 class expressions
    - Direct and indirect hierarchy navigation

    Limitations:
    - Does not perform OWL 2 DL inference (use HermiT/Pellet via SyncReasoner for that)
    - Best suited for ontology navigation and simple instance retrieval
    - Does not handle all complex class expressions (nominals, cardinalities may be limited)
    """

    def __init__(
        self,
        ontology: Union[AbstractOWLOntology, str],
        *,
        class_cache: bool = True,
        property_cache: bool = True,
        infer_property_values: bool = False,
        infer_data_property_values: bool = False,
    ):
        """
        Initialize the RDFLib-based reasoner.

        Args:
            ontology: The ontology to reason over (SyncOntology, Ontology, or path to OWL file).
            class_cache: Whether to cache class-instance mappings for faster retrieval.
            property_cache: Whether to cache property assertions.
            infer_property_values: Whether to infer property values from sub-properties.
            infer_data_property_values: Whether to infer data property values.
        """
        if isinstance(ontology, str):
            ontology = SyncOntology(ontology)

        super().__init__(ontology)
        self._ontology = ontology
        self._graph: Optional[Graph] = None
        self._class_cache_enabled = class_cache
        self._property_cache_enabled = property_cache
        self._infer_property_values = infer_property_values
        self._infer_data_property_values = infer_data_property_values

        # Cache structures
        self._cls_to_ind: Dict[OWLClass, FrozenSet[OWLNamedIndividual]] = {}
        self._subclass_cache: Dict[OWLClass, Set[OWLClass]] = {}
        self._superclass_cache: Dict[OWLClass, Set[OWLClass]] = {}

        self._init_graph()

    def _init_graph(self):
        """Initialize or reload the RDF graph from the ontology."""
        self._graph = Graph()

        # Load ontology into RDFLib graph
        if isinstance(self._ontology, SyncOntology):
            # Convert SyncOntology to RDF
            # Use the ontology's save method to export to a temp file, then load
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.owl', delete=False) as tmp:
                tmp_path = tmp.name
            try:
                self._ontology.save(tmp_path)
                self._graph.parse(tmp_path, format='xml')
            finally:
                import os
                os.unlink(tmp_path)
        elif isinstance(self._ontology, Ontology):
            # Similar approach for Ontology
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.owl', delete=False) as tmp:
                tmp_path = tmp.name
            try:
                self._ontology.save(tmp_path)
                self._graph.parse(tmp_path, format='xml')
            finally:
                import os
                os.unlink(tmp_path)
        elif hasattr(self._ontology, 'get_iri'):
            # Try loading from IRI/path
            ontology_iri = str(self._ontology.get_iri())
            self._graph.parse(ontology_iri, format='xml')

        # Build caches if enabled
        if self._class_cache_enabled:
            self._build_class_hierarchy_cache()

    def _build_class_hierarchy_cache(self):
        """Build subclass/superclass hierarchy cache using SPARQL."""
        # Query for all rdfs:subClassOf relationships
        query = """
        SELECT ?sub ?super
        WHERE {
            ?sub rdfs:subClassOf ?super .
            FILTER(isIRI(?sub) && isIRI(?super))
        }
        """
        results = self._graph.query(query)

        for row in results:
            sub_iri = str(row.sub)
            super_iri = str(row.super)

            sub_class = OWLClass(IRI.create(sub_iri))
            super_class = OWLClass(IRI.create(super_iri))

            # Build direct subclass relationships
            if super_class not in self._subclass_cache:
                self._subclass_cache[super_class] = set()
            self._subclass_cache[super_class].add(sub_class)

            # Build direct superclass relationships
            if sub_class not in self._superclass_cache:
                self._superclass_cache[sub_class] = set()
            self._superclass_cache[sub_class].add(super_class)

    def instances(
        self,
        ce: OWLClassExpression,
        direct: bool = False,
        timeout: int = 1000
    ) -> Iterable[OWLNamedIndividual]:
        """
        Get individuals that are instances of the specified class expression.

        Args:
            ce: The class expression whose instances are to be retrieved.
            direct: If True, retrieve only direct instances (not implemented - returns all).
            timeout: Timeout in milliseconds (for compatibility, not enforced).

        Returns:
            Iterable of named individuals that are instances of ce.
        """
        if direct:
            logger.warning("direct=True not fully implemented, returning all instances")

        # Handle simple named classes efficiently
        if isinstance(ce, OWLClass):
            return self._instances_of_class(ce)

        # For complex class expressions, use SPARQL conversion
        try:
            sparql_query = owl_expression_to_sparql(ce, named_individuals=True)
            results = self._graph.query(sparql_query)

            individuals = set()
            for row in results:
                # The SPARQL query should bind ?x to individuals
                ind_uri = str(row[0]) if row else None
                if ind_uri:
                    individuals.add(OWLNamedIndividual(IRI.create(ind_uri)))

            return iter(individuals)
        except Exception as e:
            logger.warning(f"Failed to convert class expression to SPARQL: {e}")
            # Fallback to manual filtering (slower)
            return self._instances_manual(ce)

    def _instances_of_class(self, cls: OWLClass) -> Iterable[OWLNamedIndividual]:
        """Get instances of a named class using SPARQL."""
        # Check cache first
        if self._class_cache_enabled and cls in self._cls_to_ind:
            return iter(self._cls_to_ind[cls])

        cls_uri = URIRef(cls.str)

        # SPARQL query for instances
        query = f"""
        SELECT DISTINCT ?ind
        WHERE {{
            ?ind a <{cls_uri}> .
            FILTER(isIRI(?ind))
        }}
        """

        results = self._graph.query(query)
        individuals = frozenset(
            OWLNamedIndividual(IRI.create(str(row.ind)))
            for row in results
        )

        # Cache results
        if self._class_cache_enabled:
            self._cls_to_ind[cls] = individuals

        return iter(individuals)

    def _instances_manual(self, ce: OWLClassExpression) -> Iterable[OWLNamedIndividual]:
        """Manual instance checking for complex expressions (fallback)."""
        # Get all individuals and filter
        query = """
        SELECT DISTINCT ?ind
        WHERE {
            ?ind a ?type .
            FILTER(isIRI(?ind))
        }
        """
        self._graph.query(query)

        # This is a placeholder - proper implementation would check
        # each individual against the class expression semantics
        # For now, return empty to avoid incorrect results
        logger.warning("Manual instance checking not fully implemented for complex expressions")
        return iter([])

    def sub_classes(
        self,
        ce: OWLClassExpression,
        direct: bool = False,
        only_named: bool = True
    ) -> Iterable[OWLClassExpression]:
        """
        Get subclasses of the specified class expression.

        Args:
            ce: The class expression whose subclasses are to be retrieved.
            direct: If True, only direct subclasses; if False, all descendant subclasses.
            only_named: If True, only return named classes (OWLClass instances).

        Returns:
            Iterable of subclass expressions.
        """
        if not isinstance(ce, OWLClass):
            logger.warning("sub_classes for complex expressions not fully implemented")
            return iter([])

        if direct:
            return self._direct_subclasses(ce)
        else:
            return self._all_subclasses(ce)

    def _direct_subclasses(self, cls: OWLClass) -> Iterable[OWLClass]:
        """Get direct subclasses using cache or SPARQL."""
        # Check cache
        if cls in self._subclass_cache:
            return iter(self._subclass_cache[cls])

        cls_uri = URIRef(cls.str)

        query = f"""
        SELECT DISTINCT ?sub
        WHERE {{
            ?sub rdfs:subClassOf <{cls_uri}> .
            FILTER(isIRI(?sub))
        }}
        """

        results = self._graph.query(query)
        subclasses = {
            OWLClass(IRI.create(str(row.sub)))
            for row in results
        }

        # Update cache
        self._subclass_cache[cls] = subclasses

        return iter(subclasses)

    def _all_subclasses(self, cls: OWLClass) -> Iterable[OWLClass]:
        """Get all descendant subclasses recursively."""
        seen = set()
        yielded = set()  # Track what we've already yielded to prevent duplicates
        to_process = {cls}

        while to_process:
            current = to_process.pop()
            if current in seen:
                continue
            seen.add(current)

            # Get direct subclasses
            direct_subs = set(self._direct_subclasses(current))

            # Add to processing queue
            to_process.update(direct_subs - seen)

            # Yield subclasses (excluding the original class) only once
            for sub in direct_subs:
                if sub != cls and sub not in yielded:
                    yielded.add(sub)
                    yield sub

    def super_classes(
        self,
        ce: OWLClassExpression,
        direct: bool = False,
        only_named: bool = True
    ) -> Iterable[OWLClassExpression]:
        """
        Get superclasses of the specified class expression.

        Args:
            ce: The class expression whose superclasses are to be retrieved.
            direct: If True, only direct superclasses; if False, all ancestor superclasses.
            only_named: If True, only return named classes (OWLClass instances).

        Returns:
            Iterable of superclass expressions.
        """
        if not isinstance(ce, OWLClass):
            logger.warning("super_classes for complex expressions not fully implemented")
            return iter([])

        if direct:
            return self._direct_superclasses(ce)
        else:
            return self._all_superclasses(ce)

    def _direct_superclasses(self, cls: OWLClass) -> Iterable[OWLClass]:
        """Get direct superclasses using cache or SPARQL."""
        # Check cache
        if cls in self._superclass_cache:
            return iter(self._superclass_cache[cls])

        cls_uri = URIRef(cls.str)

        query = f"""
        SELECT DISTINCT ?super
        WHERE {{
            <{cls_uri}> rdfs:subClassOf ?super .
            FILTER(isIRI(?super))
        }}
        """

        results = self._graph.query(query)
        superclasses = {
            OWLClass(IRI.create(str(row.super)))
            for row in results
        }

        # Update cache
        self._superclass_cache[cls] = superclasses

        return iter(superclasses)

    def _all_superclasses(self, cls: OWLClass) -> Iterable[OWLClass]:
        """Get all ancestor superclasses recursively."""
        seen = set()
        yielded = set()  # Track what we've already yielded to prevent duplicates
        to_process = {cls}

        while to_process:
            current = to_process.pop()
            if current in seen:
                continue
            seen.add(current)

            # Get direct superclasses
            direct_supers = set(self._direct_superclasses(current))

            # Add to processing queue
            to_process.update(direct_supers - seen)

            # Yield superclasses (excluding the original class) only once
            for sup in direct_supers:
                if sup != cls and sup not in yielded:
                    yielded.add(sup)
                    yield sup

    def equivalent_classes(
        self,
        ce: OWLClassExpression,
        only_named: bool = True
    ) -> Iterable[OWLClassExpression]:
        """
        Get classes equivalent to the specified class expression.

        Args:
            ce: The class expression.
            only_named: If True, only return named classes.

        Returns:
            Iterable of equivalent class expressions.
        """
        if not isinstance(ce, OWLClass):
            return iter([])

        cls_uri = URIRef(ce.str)

        query = f"""
        SELECT DISTINCT ?equiv
        WHERE {{
            {{ <{cls_uri}> owl:equivalentClass ?equiv }}
            UNION
            {{ ?equiv owl:equivalentClass <{cls_uri}> }}
            FILTER(isIRI(?equiv) && ?equiv != <{cls_uri}>)
        }}
        """

        results = self._graph.query(query)
        return (
            OWLClass(IRI.create(str(row.equiv)))
            for row in results
        )

    def disjoint_classes(
        self,
        ce: OWLClassExpression,
        only_named: bool = True
    ) -> Iterable[OWLClassExpression]:
        """
        Get classes disjoint with the specified class expression.

        Args:
            ce: The class expression.
            only_named: If True, only return named classes.

        Returns:
            Iterable of disjoint class expressions.
        """
        if not isinstance(ce, OWLClass):
            return iter([])

        cls_uri = URIRef(ce.str)

        query = f"""
        SELECT DISTINCT ?disjoint
        WHERE {{
            {{ <{cls_uri}> owl:disjointWith ?disjoint }}
            UNION
            {{ ?disjoint owl:disjointWith <{cls_uri}> }}
            FILTER(isIRI(?disjoint) && ?disjoint != <{cls_uri}>)
        }}
        """

        results = self._graph.query(query)
        return (
            OWLClass(IRI.create(str(row.disjoint)))
            for row in results
        )

    def object_property_values(
        self,
        ind: OWLNamedIndividual,
        pe: OWLObjectPropertyExpression,
        direct: bool = True
    ) -> Iterable[OWLNamedIndividual]:
        """
        Get object property values for an individual.

        Args:
            ind: The individual.
            pe: The object property expression.
            direct: Whether to consider only direct assertions.

        Returns:
            Iterable of individuals that are values of the property for ind.
        """
        if not isinstance(pe, OWLObjectProperty):
            logger.warning("Complex property expressions not fully supported")
            return iter([])

        ind_uri = URIRef(ind.str)
        prop_uri = URIRef(pe.str)

        query = f"""
        SELECT DISTINCT ?value
        WHERE {{
            <{ind_uri}> <{prop_uri}> ?value .
            FILTER(isIRI(?value))
        }}
        """

        results = self._graph.query(query)
        return (
            OWLNamedIndividual(IRI.create(str(row.value)))
            for row in results
        )

    def flush(self) -> None:
        """Flush all cached data and reload the ontology."""
        self._cls_to_ind.clear()
        self._subclass_cache.clear()
        self._superclass_cache.clear()
        self._init_graph()

    def get_root_ontology(self) -> AbstractOWLOntology:
        """Gets the root ontology that is loaded into this reasoner."""
        return self._ontology

    def types(self, ind: OWLNamedIndividual, direct: bool = False) -> Iterable[OWLClass]:
        """
        Gets the named classes which are (potentially direct) types of the specified named individual.

        Args:
            ind: The individual whose types are to be retrieved.
            direct: If True, only direct types; if False, all types.

        Returns:
            Iterable of OWLClass representing the types of the individual.
        """
        ind_uri = URIRef(ind.str)

        query = f"""
        SELECT DISTINCT ?type
        WHERE {{
            <{ind_uri}> a ?type .
            FILTER(isIRI(?type))
        }}
        """

        results = self._graph.query(query)
        types_list = [OWLClass(IRI.create(str(row.type))) for row in results]

        if direct:
            # For direct types, filter out those that have subclass relationships
            direct_types = []
            for t in types_list:
                is_direct = True
                for other in types_list:
                    if t != other and other in self.sub_classes(t, direct=False):
                        is_direct = False
                        break
                if is_direct:
                    direct_types.append(t)
            return iter(direct_types)

        return iter(types_list)

    def data_property_domains(self, pe, direct: bool = False):
        """Gets the class expressions that are the domains of this data property."""
        logger.warning("data_property_domains not fully implemented")
        return iter([])

    def object_property_domains(self, pe, direct: bool = False):
        """Gets the class expressions that are the domains of this object property."""
        logger.warning("object_property_domains not fully implemented")
        return iter([])

    def object_property_ranges(self, pe, direct: bool = False):
        """Gets the class expressions that are the ranges of this object property."""
        logger.warning("object_property_ranges not fully implemented")
        return iter([])

    def data_property_values(self, e, pe):
        """Gets the data property values for the specified entity and data property."""
        logger.warning("data_property_values not fully implemented")
        return iter([])

    def different_individuals(self, ind: OWLNamedIndividual):
        """Gets the individuals that are different from the specified individual."""
        logger.warning("different_individuals not fully implemented")
        return iter([])

    def same_individuals(self, ind: OWLNamedIndividual):
        """Gets the individuals that are the same as the specified individual."""
        ind_uri = URIRef(ind.str)

        query = f"""
        SELECT DISTINCT ?same
        WHERE {{
            {{ <{ind_uri}> owl:sameAs ?same }}
            UNION
            {{ ?same owl:sameAs <{ind_uri}> }}
            FILTER(isIRI(?same) && ?same != <{ind_uri}>)
        }}
        """

        results = self._graph.query(query)
        return (OWLNamedIndividual(IRI.create(str(row.same))) for row in results)

    def equivalent_object_properties(self, op):
        """Gets the object properties that are equivalent to the specified object property."""
        logger.warning("equivalent_object_properties not fully implemented")
        return iter([])

    def equivalent_data_properties(self, dp):
        """Gets the data properties that are equivalent to the specified data property."""
        logger.warning("equivalent_data_properties not fully implemented")
        return iter([])

    def disjoint_object_properties(self, op):
        """Gets the object properties that are disjoint with the specified object property."""
        logger.warning("disjoint_object_properties not fully implemented")
        return iter([])

    def disjoint_data_properties(self, dp):
        """Gets the data properties that are disjoint with the specified data property."""
        logger.warning("disjoint_data_properties not fully implemented")
        return iter([])

    def sub_data_properties(self, dp, direct: bool = False):
        """Gets the sub data properties of the specified data property."""
        logger.warning("sub_data_properties not fully implemented")
        return iter([])

    def super_data_properties(self, dp, direct: bool = False):
        """Gets the super data properties of the specified data property."""
        logger.warning("super_data_properties not fully implemented")
        return iter([])

    def sub_object_properties(self, op, direct: bool = False):
        """Gets the sub object properties of the specified object property."""
        logger.warning("sub_object_properties not fully implemented")
        return iter([])

    def super_object_properties(self, op, direct: bool = False):
        """Gets the super object properties of the specified object property."""
        logger.warning("super_object_properties not fully implemented")
        return iter([])

    def __repr__(self):
        return f"RDFLibReasoner({self._ontology})"
