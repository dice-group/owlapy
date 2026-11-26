"""The "index" engine of RDFLibReasoner.instances() (#310, 2.1).

rdflib's SPARQL engine evaluates joins as nested loops, so the queries owl_expression_to_sparql
produces -- every one joins `?x a owl:NamedIndividual` with the expression's pattern -- grow with the
product of both sides: `Bond-7 ⊔ Bond-3` on Carcinogenesis takes ~50 s. This engine instead indexes
the graph once and evaluates class expressions with set algebra, like StructuralReasoner.

It returns what the "sparql" engine returns: each case below follows the pattern the converter
emits for it (noted per case). Data ranges are the exception that proves the rule: rather than
re-implementing SPARQL's literal comparison, datatype and facet semantics, each data restriction is
answered by running the converter's own query for just that restriction -- a single triple pattern
plus a FILTER, which rdflib evaluates in one linear scan.
"""
from collections import defaultdict
from typing import Callable, Dict, FrozenSet, Iterable, Optional, Set, Tuple, Union

from rdflib import OWL, RDF, Graph, URIRef
from rdflib.term import Node

from owlapy.class_expression import (
    OWLClass,
    OWLClassExpression,
    OWLDataAllValuesFrom,
    OWLDataCardinalityRestriction,
    OWLDataExactCardinality,
    OWLDataHasValue,
    OWLDataMaxCardinality,
    OWLDataMinCardinality,
    OWLDataSomeValuesFrom,
    OWLObjectAllValuesFrom,
    OWLObjectCardinalityRestriction,
    OWLObjectComplementOf,
    OWLObjectExactCardinality,
    OWLObjectHasSelf,
    OWLObjectHasValue,
    OWLObjectIntersectionOf,
    OWLObjectMaxCardinality,
    OWLObjectMinCardinality,
    OWLObjectOneOf,
    OWLObjectSomeValuesFrom,
    OWLObjectUnionOf,
)
from owlapy.converter import owl_expression_to_sparql
from owlapy.iri import IRI
from owlapy.owl_data_ranges import OWLDataComplementOf
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_property import OWLObjectInverseOf, OWLObjectProperty


class _AllBut:
    """Every RDF node except `excluded` -- what a pattern that only filters (owl:Thing as a filler,
    owl:allValuesFrom on a data property) matches before an enclosing pattern binds the variable."""
    __slots__ = ("excluded",)

    def __init__(self, excluded: FrozenSet[Node]):
        self.excluded = excluded


_Nodes = Union[FrozenSet[Node], _AllBut]
_ALL = _AllBut(frozenset())
_EMPTY: FrozenSet[Node] = frozenset()


def _contains(nodes: _Nodes, node: Node) -> bool:
    return node not in nodes.excluded if isinstance(nodes, _AllBut) else node in nodes


def _and(a: _Nodes, b: _Nodes) -> _Nodes:
    if isinstance(a, _AllBut):
        a, b = b, a
    if isinstance(a, _AllBut):
        return _AllBut(a.excluded | b.excluded)
    return a - b.excluded if isinstance(b, _AllBut) else a & b


def _or(a: _Nodes, b: _Nodes) -> _Nodes:
    if isinstance(a, _AllBut):
        a, b = b, a
    if isinstance(a, _AllBut):
        return _AllBut(a.excluded & b.excluded)
    return _AllBut(b.excluded - a) if isinstance(b, _AllBut) else a | b


class InstanceIndex:
    """Indexes of one snapshot of the reasoner's graph, built once and queried many times."""

    def __init__(self, graph: Graph, *, negation_default: bool,
                 sub_classes: Callable[[OWLClass], Iterable[OWLClass]],
                 inverse_properties: Callable[[OWLObjectProperty], Iterable[OWLObjectProperty]],
                 sub_properties: Optional[Callable] = None):
        self._graph = graph
        self.size = len(graph)
        self._negation_default = negation_default
        self._sub_classes = sub_classes
        self._inverse_properties = inverse_properties
        self._sub_properties = sub_properties

        self._types: Dict[Node, Set[Node]] = defaultdict(set)
        for s, o in graph.subject_objects(RDF.type):
            self._types[o].add(s)
        # `?x a ?t` -- the second branch of an at-most cardinality binds the subject this way
        self._typed: FrozenSet[Node] = frozenset(s for members in self._types.values() for s in members)
        # `?x ?p ?o` -- the converter binds a complement / allValuesFrom subject this way
        self._subjects: FrozenSet[Node] = frozenset(graph.subjects(unique=True))
        # `?x a owl:NamedIndividual` -- the root pattern of every instances() query
        self._named_individuals: FrozenSet[Node] = frozenset(self._types.get(OWL.NamedIndividual, ()))

        self._classes: Dict[OWLClass, FrozenSet[Node]] = {}
        self._relations: Dict[Tuple[OWLObjectProperty, bool, bool], Dict[Node, Set[Node]]] = {}
        self._data_atoms: Dict[OWLClassExpression, FrozenSet[Node]] = {}
        self._individuals: Dict[Node, OWLNamedIndividual] = {}

    # ---- public -------------------------------------------------------------------------------

    def instances(self, ce: OWLClassExpression) -> Set[OWLNamedIndividual]:
        """Named individuals of a complex class expression (root pattern `?x a owl:NamedIndividual`)."""
        nodes = _and(self._named_individuals, self._eval(ce))
        return {self._individual(n) for n in nodes}

    def property_values(self, individual: OWLNamedIndividual, pe) -> Set[OWLNamedIndividual]:
        """What RDFLibReasoner.object_property_values returns: the IRI values of the property and of its
        declared inverses reversed (never its sub-properties); an OWLObjectInverseOf swaps direction."""
        objects = self._relation(pe, with_sub_properties=False).get(URIRef(individual.str), ())
        return {self._individual(o) for o in objects if isinstance(o, URIRef)}

    def class_instances(self, cls: OWLClass) -> FrozenSet[OWLNamedIndividual]:
        """What RDFLibReasoner._instances_of_class returns for a named class other than owl:Thing:
        IRIs typed with the class or one of its subclasses."""
        return frozenset(self._individual(n) for n in self._class(cls) if isinstance(n, URIRef))

    # ---- evaluation ---------------------------------------------------------------------------

    def _eval(self, ce: OWLClassExpression) -> _Nodes:
        if isinstance(ce, OWLClass):
            # Nested owl:Thing emits no pattern: it matches whatever the enclosing pattern bound.
            return _ALL if ce.is_owl_thing() else self._class(ce)
        if isinstance(ce, OWLObjectIntersectionOf):
            result: _Nodes = _ALL
            for op in ce.operands():
                result = _and(result, self._eval(op))
            return result
        if isinstance(ce, OWLObjectUnionOf):
            result = _EMPTY
            for op in ce.operands():
                result = _or(result, self._eval(op))
            return result
        if isinstance(ce, OWLObjectComplementOf):
            if not self._negation_default:
                return _EMPTY  # FILTER(1=0)
            # `?x ?p ?o . FILTER NOT EXISTS { C }`: subjects of any triple, except those in C
            return self._complement(self._eval(ce.get_operand()))
        if isinstance(ce, OWLObjectSomeValuesFrom):
            return self._some(self._relation(ce.get_property()), self._eval(ce.get_filler()))
        if isinstance(ce, OWLObjectAllValuesFrom):
            # De Morgan form: `?x ?p ?o . FILTER NOT EXISTS { ?x r ?y . FILTER NOT EXISTS { C(?y) } }`
            relation, filler = self._relation(ce.get_property()), self._eval(ce.get_filler())
            violating = frozenset(s for s, objects in relation.items() if any(not _contains(filler, o) for o in objects))
            return self._subjects - violating
        if isinstance(ce, OWLObjectHasValue):
            relation = self._relation(ce.get_property())
            value = URIRef(ce.get_filler().str)
            return frozenset(s for s, objects in relation.items() if value in objects)
        if isinstance(ce, OWLObjectCardinalityRestriction):
            relation, filler = self._relation(ce.get_property()), self._eval(ce.get_filler())
            counts = {s: n for s, objects in relation.items() if (n := sum(1 for o in objects if _contains(filler, o)))}
            return self._cardinality(ce, counts)
        if isinstance(ce, OWLObjectHasSelf):
            relation = self._relation(ce.get_property())
            return frozenset(s for s, objects in relation.items() if s in objects)
        if isinstance(ce, OWLObjectOneOf):
            return frozenset(URIRef(i.str) for i in ce.individuals())
        if isinstance(ce, (OWLDataSomeValuesFrom, OWLDataHasValue)):
            return self._data_atom(ce)
        if isinstance(ce, OWLDataAllValuesFrom):
            # `FILTER NOT EXISTS { ?x d ?v . FILTER(!D(?v)) }`
            return _AllBut(self._data_atom(OWLDataSomeValuesFrom(ce.get_property(), OWLDataComplementOf(ce.get_filler()))))
        if isinstance(ce, OWLDataCardinalityRestriction):
            return self._data_cardinality(ce)
        raise NotImplementedError(f"The index engine does not support {type(ce).__name__}")

    def _complement(self, nodes: _Nodes) -> FrozenSet[Node]:
        return self._subjects & nodes.excluded if isinstance(nodes, _AllBut) else self._subjects - nodes

    @staticmethod
    def _some(relation: Dict[Node, Set[Node]], filler: _Nodes) -> FrozenSet[Node]:
        if isinstance(filler, _AllBut):
            excluded = filler.excluded
            return frozenset(s for s, objects in relation.items() if not objects <= excluded)
        return frozenset(s for s, objects in relation.items() if not objects.isdisjoint(filler))

    def _cardinality(self, ce, counts: Dict[Node, int]) -> FrozenSet[Node]:
        """`{ SELECT ?x ... GROUP BY ?x HAVING (COUNT(DISTINCT ?y) op n) }`, plus -- for ≤ and for
        cardinality 0 -- `UNION { ?x a ?t OPTIONAL { ?x r ?y . C(?y) } FILTER(!BOUND(?y)) }`."""
        n = ce.get_cardinality()
        if isinstance(ce, (OWLObjectMinCardinality, OWLDataMinCardinality)):
            matched = {s for s, c in counts.items() if c >= n}
        elif isinstance(ce, (OWLObjectMaxCardinality, OWLDataMaxCardinality)):
            matched = {s for s, c in counts.items() if c <= n}
        elif isinstance(ce, (OWLObjectExactCardinality, OWLDataExactCardinality)):
            matched = {s for s, c in counts.items() if c == n}
        else:
            raise NotImplementedError(type(ce).__name__)
        if isinstance(ce, (OWLObjectMaxCardinality, OWLDataMaxCardinality)) or n == 0:
            matched |= self._typed.difference(counts)
        return frozenset(matched)

    # ---- indexes ------------------------------------------------------------------------------

    def _class(self, cls: OWLClass) -> FrozenSet[Node]:
        # `?x a ?t . VALUES ?t { C, subclasses of C }`
        members = self._classes.get(cls)
        if members is None:
            members = frozenset().union(*(self._types.get(URIRef(c.str), ()) for c in [cls, *self._sub_classes(cls)]))
            self._classes[cls] = members
        return members

    def _relation(self, pe, with_sub_properties: bool = True) -> Dict[Node, Set[Node]]:
        """subject -> objects of the property path the converter renders for `pe`: the property, its
        sub-properties (when sub_properties=True), and its declared inverses (and their sub-properties)
        reversed; an OWLObjectInverseOf swaps subject and object."""
        inverse = isinstance(pe, OWLObjectInverseOf)
        prop = pe.get_named_property()
        sub_properties = self._sub_properties if with_sub_properties else None
        key = (prop, inverse, sub_properties is not None)
        relation = self._relations.get(key)
        if relation is not None:
            return relation
        if inverse:
            relation = defaultdict(set)
            for s, objects in self._relation(prop, with_sub_properties).items():
                for o in objects:
                    relation[o].add(s)
        else:
            subs = list(sub_properties(prop)) if sub_properties is not None else []
            inverses = list(self._inverse_properties(prop))
            reversed_ = list(inverses)
            if sub_properties is not None:
                for inv in inverses:
                    reversed_.extend(sub_properties(inv))
                for sub in subs:
                    reversed_.extend(self._inverse_properties(sub))
            relation = defaultdict(set)
            for p in [prop, *subs]:
                for s, o in self._graph.subject_objects(URIRef(p.str)):
                    relation[s].add(o)
            for p in reversed_:
                for s, o in self._graph.subject_objects(URIRef(p.str)):
                    relation[o].add(s)
        relation = dict(relation)
        self._relations[key] = relation
        return relation

    def _data_atom(self, ce: OWLClassExpression) -> FrozenSet[Node]:
        """Subjects matching a data restriction, by the converter's own single-pattern query."""
        nodes = self._data_atoms.get(ce)
        if nodes is None:
            query = owl_expression_to_sparql(ce, named_individuals=False, negation_default=self._negation_default,
                                             sub_property_resolver=self._sub_properties,
                                             inverse_property_resolver=self._inverse_properties)
            nodes = frozenset(row[0] for row in self._graph.query(query) if row[0] is not None)
            self._data_atoms[ce] = nodes
        return nodes

    def _data_cardinality(self, ce: OWLDataCardinalityRestriction) -> FrozenSet[Node]:
        prop, filler, n = ce.get_property(), ce.get_filler(), ce.get_cardinality()

        def at_least(k: int) -> FrozenSet[Node]:
            return self._data_atom(OWLDataMinCardinality(k, prop, filler))

        if isinstance(ce, OWLDataMinCardinality) and n > 0:
            return at_least(n)
        if isinstance(ce, OWLDataExactCardinality) and n > 0:
            return at_least(n) - at_least(n + 1)
        # ≤ n, ≥ 0, = 0: the counted branch, plus typed subjects with no matching value
        some = at_least(1)
        if isinstance(ce, OWLDataMaxCardinality):
            counted = some - at_least(n + 1)
        elif isinstance(ce, OWLDataMinCardinality):  # ≥ 0
            counted = some
        else:  # = 0
            counted = _EMPTY
        return counted | (self._typed - some)

    def _individual(self, node: Node) -> OWLNamedIndividual:
        individual = self._individuals.get(node)
        if individual is None:
            individual = OWLNamedIndividual(IRI.create(str(node)))
            self._individuals[node] = individual
        return individual
