"""RDFLib-based OWL Reasoner - Pure Python implementation."""
import logging
from typing import Dict, FrozenSet, Iterable, Optional, Set, Union

from rdflib import Graph, URIRef

from owlapy.abstracts.abstract_owl_ontology import AbstractOWLOntology
from owlapy.abstracts.abstract_owl_reasoner import AbstractOWLReasoner
from owlapy.class_expression import (
    OWLClass,
    OWLClassExpression,
    OWLObjectCardinalityRestriction,
    OWLObjectExactCardinality,
    OWLObjectMaxCardinality,
    OWLObjectMinCardinality,
)
from owlapy.converter import owl_expression_to_sparql
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral, StringOWLDatatype
from owlapy.owl_ontology import Ontology, RDFLibOntology, SyncOntology
from owlapy.owl_property import OWLDataProperty, OWLObjectInverseOf, OWLObjectProperty, OWLObjectPropertyExpression

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
    - Direct and indirect hierarchy navigation for classes, object properties and data properties
    - Domain/range, equivalence, disjointness and same/different-individual queries, including the
      RDF-list-based owl:AllDisjointProperties/owl:AllDifferent axiom forms

    Limitations:
    - Does not perform OWL 2 DL inference/entailment (use HermiT/Pellet via SyncReasoner for that) —
      results reflect asserted axioms plus simple transitive closure over sub-class/sub-property
      hierarchies, not full description logic reasoning
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
        negation_default: bool = True,
        sub_properties: bool = False,
    ):
        """
        Initialize the RDFLib-based reasoner.

        Args:
            ontology: The ontology to reason over (RDFLibOntology, SyncOntology, Ontology, or a
                path to an OWL file). A path or an `RDFLibOntology` is ingested directly via
                rdflib, without touching owlready2 or starting the JVM.
            class_cache: Whether to cache class-instance mappings for faster retrieval.
            property_cache: Whether to cache property assertions.
            infer_property_values: Whether to infer property values from sub-properties.
            infer_data_property_values: Whether to infer data property values.
            negation_default: Whether to assume a missing fact means it is false ("closed world
                view", the default) when evaluating OWLObjectComplementOf in instances(). If
                False (open world), a complement never contributes any results, since nothing can
                be inferred to NOT be a member of a class without an explicit negative assertion.
            sub_properties: Whether instances() should also match individuals connected via a
                sub-property of the property used in someValuesFrom/allValuesFrom/hasValue/
                cardinality restrictions, mirroring StructuralReasoner's sub_properties flag.
        """
        if isinstance(ontology, str):
            # Parse straight into rdflib -- no owlready2 objects, no JVM.
            ontology = RDFLibOntology(ontology)

        super().__init__(ontology)
        self._ontology = ontology
        self._graph: Optional[Graph] = None
        self._class_cache_enabled = class_cache
        self._property_cache_enabled = property_cache
        self._infer_property_values = infer_property_values
        self._infer_data_property_values = infer_data_property_values
        self._negation_default = negation_default
        self._sub_properties = sub_properties

        # Cache structures
        self._cls_to_ind: Dict[OWLClass, FrozenSet[OWLNamedIndividual]] = {}
        self._subclass_cache: Dict[OWLClass, Set[OWLClass]] = {}
        self._superclass_cache: Dict[OWLClass, Set[OWLClass]] = {}
        self._sub_obj_prop_cache: Dict[OWLObjectProperty, Set[OWLObjectProperty]] = {}
        self._super_obj_prop_cache: Dict[OWLObjectProperty, Set[OWLObjectProperty]] = {}
        self._sub_data_prop_cache: Dict[OWLDataProperty, Set[OWLDataProperty]] = {}
        self._super_data_prop_cache: Dict[OWLDataProperty, Set[OWLDataProperty]] = {}

        self._init_graph()

    def _init_graph(self):
        """Initialize or reload the RDF graph from the ontology."""
        if isinstance(self._ontology, RDFLibOntology):
            # Already backed by an rdflib graph -- reuse it directly. No owlready2/JVM involved.
            self._graph = self._ontology.rdflib_graph
        else:
            self._graph = Graph()

            # Back-compat: JVM-backed (SyncOntology) or owlready2-backed (Ontology) instances
            # have no rdflib graph of their own, so round-trip through a serialized file.
            if isinstance(self._ontology, SyncOntology):
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

        # OWLObjectMaxCardinality / cardinality==0 restrictions need special-casing: see
        # _at_most_cardinality_instances for why.
        if isinstance(ce, OWLObjectCardinalityRestriction) and (
                isinstance(ce, OWLObjectMaxCardinality) or ce.get_cardinality() == 0):
            return self._at_most_cardinality_instances(ce)

        # For complex class expressions, use SPARQL conversion
        try:
            sparql_query = owl_expression_to_sparql(
                ce, named_individuals=True,
                negation_default=self._negation_default,
                sub_property_resolver=self._sub_property_resolver if self._sub_properties else None,
                inverse_property_resolver=self._inverse_properties,
                subclass_resolver=lambda c: self.sub_classes(c, direct=False),
            )
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

    def _at_most_cardinality_instances(self, ce: OWLObjectCardinalityRestriction) -> Iterable[OWLNamedIndividual]:
        """Special-cased handling for OWLObjectMaxCardinality (any N) and cardinality==0 (any
        restriction type).

        The natural SPARQL translation of these needs to identify individuals with ZERO matching
        relations, via a FILTER NOT EXISTS/OPTIONAL+!BOUND pattern correlated per candidate
        individual. rdflib's SPARQL engine evaluates that as an expensive per-candidate check
        (not a proper join), which is catastrophically slow on non-trivial ontologies -- confirmed
        via profiling on KGs/Mutagenesis/mutagenesis.owl (14k+ candidate individuals). Instead,
        compute set-theoretically in Python using only the fast, uncorrelated
        OWLObjectMinCardinality path (which never needs a "zero match" branch, since >=1 and
        >=N+1 both require at least one match to even appear as a GROUP BY row).
        """
        prop = ce.get_property()
        n = ce.get_cardinality()
        filler = ce.get_filler()

        if isinstance(ce, OWLObjectMinCardinality):
            # Only reached when n == 0: ">= 0" is trivially satisfied by every individual.
            return iter(set(self._ontology.individuals_in_signature()))

        at_least_one = OWLObjectMinCardinality(cardinality=1, property=prop, filler=filler)
        s_any = set(self.instances(at_least_one))
        s_zero = set(self._ontology.individuals_in_signature()) - s_any

        if n == 0:
            # Max/Exact cardinality 0: satisfied only by individuals with no matching relation.
            return iter(s_zero)

        at_least_n_plus_one = OWLObjectMinCardinality(cardinality=n + 1, property=prop, filler=filler)
        s_too_many = set(self.instances(at_least_n_plus_one))
        s_in_range = s_any - s_too_many

        if isinstance(ce, OWLObjectExactCardinality):
            return iter(s_in_range)
        return iter(s_in_range | s_zero)  # OWLObjectMaxCardinality

    def _instances_of_class(self, cls: OWLClass) -> Iterable[OWLNamedIndividual]:
        """Get instances of a named class using SPARQL."""
        # Check cache first
        if self._class_cache_enabled and cls in self._cls_to_ind:
            return iter(self._cls_to_ind[cls])

        if cls.is_owl_thing():
            # owl:Thing matches every individual; individuals are essentially never explicitly
            # asserted rdf:type owl:Thing, so a `?ind a owl:Thing` SPARQL query would wrongly
            # return nothing. individuals_in_signature() is the reliable source of truth here.
            individuals = frozenset(self._ontology.individuals_in_signature())
            if self._class_cache_enabled:
                self._cls_to_ind[cls] = individuals
            return iter(individuals)

        # Individuals may be typed only at a subclass of cls (e.g. a specific atom-type subclass
        # rather than the general `Atom` class) -- expand via a bounded VALUES list rather than a
        # flat `?ind a <cls>` triple, which would silently miss them.
        classes = [cls] + list(self.sub_classes(cls, direct=False))
        values = " ".join(f"<{c.str}>" for c in classes)

        # SPARQL query for instances
        query = f"""
        SELECT DISTINCT ?ind
        WHERE {{
            ?ind a ?type .
            VALUES ?type {{ {values} }}
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

    def _sub_property_resolver(self, prop):
        """Resolver passed to owl_expression_to_sparql when sub_properties=True."""
        if isinstance(prop, OWLObjectProperty):
            return self.sub_object_properties(prop, direct=False)
        return self.sub_data_properties(prop, direct=False)

    def _inverse_properties(self, prop: OWLObjectProperty) -> Iterable[OWLObjectProperty]:
        """Declared owl:inverseOf partner(s) of prop (bidirectional -- only one direction may be
        physically asserted). Always passed as inverse_property_resolver to owl_expression_to_sparql
        -- this fills in missing OWL entailment, it isn't an opt-in StructuralReasoner-parity flag."""
        prop_uri = URIRef(prop.str)
        query = f"""
        SELECT DISTINCT ?inv
        WHERE {{
            {{ <{prop_uri}> owl:inverseOf ?inv }}
            UNION
            {{ ?inv owl:inverseOf <{prop_uri}> }}
            FILTER(isIRI(?inv) && ?inv != <{prop_uri}>)
        }}
        """
        results = self._graph.query(query)
        return [OWLObjectProperty(IRI.create(str(row.inv))) for row in results]

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
        if isinstance(pe, OWLObjectInverseOf):
            return self._object_property_values_query(ind, pe.get_named_property(), forward=False)
        if not isinstance(pe, OWLObjectProperty):
            logger.warning("Complex property expressions not fully supported")
            return iter([])

        return self._object_property_values_query(ind, pe, forward=True)

    def _object_property_values_query(self, ind: OWLNamedIndividual, prop: OWLObjectProperty, forward: bool) \
            -> Iterable[OWLNamedIndividual]:
        ind_uri = URIRef(ind.str)
        # Expand the predicate with a reverse (`^`) alternative for each declared owl:inverseOf
        # partner, so prop is matched even if it has no physically-asserted triples of its own but
        # a declared inverse does (mirrors the same expansion done in converter.py's render()).
        alternatives = [f"<{prop.str}>"] + [f"^<{inv.str}>" for inv in self._inverse_properties(prop)]
        predicate = "(" + "|".join(alternatives) + ")"
        triple = f"<{ind_uri}> {predicate} ?value ." if forward else f"?value {predicate} <{ind_uri}> ."

        query = f"""
        SELECT DISTINCT ?value
        WHERE {{
            {triple}
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
        self._sub_obj_prop_cache.clear()
        self._super_obj_prop_cache.clear()
        self._sub_data_prop_cache.clear()
        self._super_data_prop_cache.clear()
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

    def _property_domains_or_ranges(self, pe, direct: bool, predicate: str) -> Iterable[OWLClassExpression]:
        """Shared SPARQL/semantics for {data,object}_property_domains and object_property_ranges.

        Mirrors StructuralReasoner's actual behavior (owl_reasoner.py): direct=True yields only the
        asserted domain/range classes that are not themselves a subclass of another asserted class;
        direct=False additionally yields every subclass of each asserted class.
        """
        prop_uri = URIRef(pe.str)
        query = f"""
        SELECT DISTINCT ?cls
        WHERE {{
            <{prop_uri}> {predicate} ?cls .
            FILTER(isIRI(?cls))
        }}
        """
        results = self._graph.query(query)
        asserted = {OWLClass(IRI.create(str(row.cls))) for row in results}

        sub_of_asserted = set()
        for c in asserted:
            sub_of_asserted.update(self.sub_classes(c, direct=False))

        yield from asserted - sub_of_asserted
        if not direct:
            yield from sub_of_asserted

    def data_property_domains(self, pe: OWLDataProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are the domains of this data property."""
        return self._property_domains_or_ranges(pe, direct, "rdfs:domain")

    def object_property_domains(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are the domains of this object property."""
        return self._property_domains_or_ranges(pe, direct, "rdfs:domain")

    def object_property_ranges(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are the ranges of this object property."""
        return self._property_domains_or_ranges(pe, direct, "rdfs:range")

    def data_property_values(self, e: OWLNamedIndividual, pe: OWLDataProperty) -> Iterable[OWLLiteral]:
        """Gets the data property values for the specified entity and data property."""
        e_uri = URIRef(e.str)
        prop_uri = URIRef(pe.str)

        query = f"""
        SELECT DISTINCT ?value
        WHERE {{
            <{e_uri}> <{prop_uri}> ?value .
            FILTER(isLiteral(?value))
        }}
        """
        results = self._graph.query(query)
        for row in results:
            lit = row.value
            try:
                yield OWLLiteral(lit.toPython())
            except NotImplementedError:
                # Datatypes rdflib can't map to a native Python type (e.g. xsd:duration, or a
                # custom/unrecognized datatype URI, which toPython() returns unchanged) fall back
                # to a plain string literal rather than dropping the value.
                yield OWLLiteral(str(lit), StringOWLDatatype)

    def different_individuals(self, ind: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        """Gets the individuals that are different from the specified individual."""
        ind_uri = URIRef(ind.str)

        query = f"""
        SELECT DISTINCT ?other
        WHERE {{
            {{ <{ind_uri}> owl:differentFrom ?other }}
            UNION
            {{ ?other owl:differentFrom <{ind_uri}> }}
            UNION
            {{
                ?axiom a owl:AllDifferent ;
                       owl:distinctMembers ?list .
                ?list rdf:rest*/rdf:first <{ind_uri}> .
                ?list rdf:rest*/rdf:first ?other .
            }}
            UNION
            {{
                ?axiom a owl:AllDifferent ;
                       owl:members ?list .
                ?list rdf:rest*/rdf:first <{ind_uri}> .
                ?list rdf:rest*/rdf:first ?other .
            }}
            FILTER(isIRI(?other) && ?other != <{ind_uri}>)
        }}
        """

        results = self._graph.query(query)
        return (OWLNamedIndividual(IRI.create(str(row.other))) for row in results)

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

    def _equivalent_properties(self, pe, wrap_cls) -> Iterable:
        """Shared SPARQL for equivalent_object_properties/equivalent_data_properties."""
        if not isinstance(pe, wrap_cls):
            logger.warning("equivalent properties for non-named property expressions not fully implemented")
            return iter([])

        prop_uri = URIRef(pe.str)
        query = f"""
        SELECT DISTINCT ?equiv
        WHERE {{
            {{ <{prop_uri}> owl:equivalentProperty ?equiv }}
            UNION
            {{ ?equiv owl:equivalentProperty <{prop_uri}> }}
            FILTER(isIRI(?equiv) && ?equiv != <{prop_uri}>)
        }}
        """
        results = self._graph.query(query)
        return (wrap_cls(IRI.create(str(row.equiv))) for row in results)

    def equivalent_object_properties(self, op: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        """Gets the object properties that are equivalent to the specified object property."""
        return self._equivalent_properties(op, OWLObjectProperty)

    def equivalent_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        """Gets the data properties that are equivalent to the specified data property."""
        return self._equivalent_properties(dp, OWLDataProperty)

    def _disjoint_properties(self, pe, wrap_cls) -> Iterable:
        """Shared SPARQL for disjoint_object_properties/disjoint_data_properties.

        Handles both pairwise owl:propertyDisjointWith triples and the RDF-list-based
        owl:AllDisjointProperties/owl:members form (the only form seen in this repo's test
        ontologies), using the `rdf:rest*/rdf:first` property-path trick to test list membership
        without walking the RDF collection in Python.
        """
        if not isinstance(pe, wrap_cls):
            logger.warning("disjoint properties for non-named property expressions not fully implemented")
            return iter([])

        prop_uri = URIRef(pe.str)
        query = f"""
        SELECT DISTINCT ?other
        WHERE {{
            {{ <{prop_uri}> owl:propertyDisjointWith ?other }}
            UNION
            {{ ?other owl:propertyDisjointWith <{prop_uri}> }}
            UNION
            {{
                ?axiom a owl:AllDisjointProperties ;
                       owl:members ?list .
                ?list rdf:rest*/rdf:first <{prop_uri}> .
                ?list rdf:rest*/rdf:first ?other .
            }}
            FILTER(isIRI(?other) && ?other != <{prop_uri}>)
        }}
        """
        results = self._graph.query(query)
        return (wrap_cls(IRI.create(str(row.other))) for row in results)

    def disjoint_object_properties(self, op: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        """Gets the object properties that are disjoint with the specified object property."""
        return self._disjoint_properties(op, OWLObjectProperty)

    def disjoint_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        """Gets the data properties that are disjoint with the specified data property."""
        return self._disjoint_properties(dp, OWLDataProperty)

    def _direct_sub_properties(self, prop, wrap_cls, cache: Dict) -> Set:
        """Direct rdfs:subPropertyOf children of prop, using cache."""
        if self._property_cache_enabled and prop in cache:
            return cache[prop]

        prop_uri = URIRef(prop.str)
        query = f"""
        SELECT DISTINCT ?sub
        WHERE {{
            ?sub rdfs:subPropertyOf <{prop_uri}> .
            FILTER(isIRI(?sub))
        }}
        """
        results = self._graph.query(query)
        subs = {wrap_cls(IRI.create(str(row.sub))) for row in results}

        if self._property_cache_enabled:
            cache[prop] = subs
        return subs

    def _direct_super_properties(self, prop, wrap_cls, cache: Dict) -> Set:
        """Direct rdfs:subPropertyOf parents of prop, using cache."""
        if self._property_cache_enabled and prop in cache:
            return cache[prop]

        prop_uri = URIRef(prop.str)
        query = f"""
        SELECT DISTINCT ?super
        WHERE {{
            <{prop_uri}> rdfs:subPropertyOf ?super .
            FILTER(isIRI(?super))
        }}
        """
        results = self._graph.query(query)
        supers = {wrap_cls(IRI.create(str(row.super))) for row in results}

        if self._property_cache_enabled:
            cache[prop] = supers
        return supers

    def _all_related_properties(self, prop, direct_fn) -> Iterable:
        """Iterative (non-recursive) transitive closure over a direct sub/super relation.

        Mirrors _all_subclasses/_all_superclasses: no recursion (avoids stack-overflow/circular
        dependency issues), and de-duplicates yielded results.
        """
        seen = set()
        yielded = set()
        to_process = {prop}

        while to_process:
            current = to_process.pop()
            if current in seen:
                continue
            seen.add(current)

            direct = direct_fn(current)
            to_process.update(direct - seen)

            for item in direct:
                if item != prop and item not in yielded:
                    yielded.add(item)
                    yield item

    def sub_object_properties(self, op: OWLObjectPropertyExpression, direct: bool = False) \
            -> Iterable[OWLObjectPropertyExpression]:
        """Gets the sub object properties of the specified object property."""
        if not isinstance(op, OWLObjectProperty):
            logger.warning("sub_object_properties for non-named property expressions not fully implemented")
            return iter([])

        def direct_fn(p):
            return self._direct_sub_properties(p, OWLObjectProperty, self._sub_obj_prop_cache)

        return iter(direct_fn(op)) if direct else self._all_related_properties(op, direct_fn)

    def super_object_properties(self, op: OWLObjectPropertyExpression, direct: bool = False) \
            -> Iterable[OWLObjectPropertyExpression]:
        """Gets the super object properties of the specified object property."""
        if not isinstance(op, OWLObjectProperty):
            logger.warning("super_object_properties for non-named property expressions not fully implemented")
            return iter([])

        def direct_fn(p):
            return self._direct_super_properties(p, OWLObjectProperty, self._super_obj_prop_cache)

        return iter(direct_fn(op)) if direct else self._all_related_properties(op, direct_fn)

    def sub_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        """Gets the sub data properties of the specified data property."""
        def direct_fn(p):
            return self._direct_sub_properties(p, OWLDataProperty, self._sub_data_prop_cache)

        return iter(direct_fn(dp)) if direct else self._all_related_properties(dp, direct_fn)

    def super_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        """Gets the super data properties of the specified data property."""
        def direct_fn(p):
            return self._direct_super_properties(p, OWLDataProperty, self._super_data_prop_cache)

        return iter(direct_fn(dp)) if direct else self._all_related_properties(dp, direct_fn)

    def __repr__(self):
        return f"RDFLibReasoner({self._ontology})"
