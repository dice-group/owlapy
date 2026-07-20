"""Class & property generator converter – port of the Java generateClassQuery /
generatePropertyQuery / SparqlBuildingVisitor.

This module provides a subclass of :class:`Owl2SparqlConverter` that supports a
*context position marker*.  When the marker appears in a class expression the
converter emits ``?variable a ?class .`` instead of a concrete class IRI, which
makes it possible to generate SPARQL queries that *discover* classes rather
than retrieving instances of a fixed class.

For property discovery the same marker triggers ``?variable ?prop [] .``
(or ``[] ?prop ?variable .`` when inverted), mirroring the Java
``Suggestor.generatePropertyQuery``.

The top-level helpers :func:`owl_expression_to_class_query` and
:func:`owl_expression_to_property_query` mirror :func:`owl_expression_to_sparql`
but produce queries of the form produced by the Java suggestor.
"""

from __future__ import annotations

import re
from functools import singledispatchmethod
from typing import Iterable, Optional

from rdflib.plugins.sparql.parser import parseQuery

from owlapy.class_expression import (
    OWLClass,
    OWLClassExpression,
    OWLObjectComplementOf,
    OWLObjectIntersectionOf,
    OWLObjectUnionOf,
    OWLObjectSomeValuesFrom,
    OWLObjectAllValuesFrom,
    OWLObjectCardinalityRestriction,
    OWLObjectMinCardinality,
    OWLObjectMaxCardinality,
    OWLObjectExactCardinality,
    OWLObjectHasValue,
    OWLObjectHasSelf,
    OWLObjectOneOf,
    OWLDataSomeValuesFrom,
    OWLDataAllValuesFrom,
    OWLDataHasValue,
    OWLDataCardinalityRestriction,
    OWLDataMinCardinality,
    OWLDataMaxCardinality,
    OWLDataExactCardinality,
    OWLDatatypeRestriction,
    OWLDataOneOf,
)
from owlapy.converter import Owl2SparqlConverter
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_literal import OWLLiteral, TopOWLDatatype
from owlapy.owl_property import OWLDataProperty
from owlapy.vocab import OWLRDFVocabulary

# ---------------------------------------------------------------------------
# Marker – a well-known OWLClass instance that will never collide with real
# ontology classes.  Use it in a class expression to mark the position where
# ``?variable a ?class .`` should be injected.
# ---------------------------------------------------------------------------
CONTEXT_POSITION_MARKER = OWLClass(IRI.create("http://owlapy.internal/CONTEXT_POSITION_MARKER"))


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _generate_values_stmt(variable: str, individuals: Iterable[OWLNamedIndividual]) -> str:
    """Return a SPARQL ``VALUES`` clause binding *variable* to *individuals*.

    Example output::

        VALUES ?pos { <http://ex.org/a> <http://ex.org/b> } .
    """
    iris = " ".join(f"<{ind.to_string_id()}>" for ind in individuals)
    return f"VALUES {variable} {{ {iris} }} . "


# ---------------------------------------------------------------------------
# Converter subclass
# ---------------------------------------------------------------------------

class QueryGenerator(Owl2SparqlConverter):
    """Extends :class:`Owl2SparqlConverter` with *marker-aware* conversion and
    the ability to generate ``generateClassQuery``-style SPARQL queries that
    discover OWL classes with their positive/negative hit counts.

    The marker concept :data:`CONTEXT_POSITION_MARKER` can be placed anywhere
    inside a class expression tree.  When the converter encounters it the
    emitted triple pattern becomes ``?currentVar a ?class .`` instead of the
    usual ``?currentVar a <SomeConcreteIRI> .``.  If the marker appears inside
    a negation (``OWLObjectComplementOf``) the triple pattern is additionally
    wrapped in ``FILTER NOT EXISTS { … }``, and a type axiom for ``?class`` is
    added (``?class a owl:Class .``).
    """

    __slots__ = (*Owl2SparqlConverter.__slots__, '_marker_mode', '_inside_filter',
                 '_property_marker_mode', '_data_property_discovery_marker_mode', '_inverted',
                 '_negated_class_marker_mode', '_data_property_marker_mode')

    _marker_mode: bool
    _inside_filter: bool
    _property_marker_mode: bool
    _data_property_discovery_marker_mode: bool
    _inverted: bool
    _negated_class_marker_mode: bool
    _data_property_marker_mode: bool

    # -- override convert to reset extra flags --------------------------------

    def convert(self, root_variable: str,
                ce: OWLClassExpression,
                for_all_de_morgan: bool = True,
                named_individuals: bool = False,
                marker_mode: bool = False,
                property_marker_mode: bool = False,
                data_property_discovery_marker_mode: bool = False,
                data_property_marker_mode: bool = False,
                inverted: bool = False,
                negated_class_marker_mode: bool = False):
        """Like the parent ``convert`` but accepts extra marker flags.

        When *marker_mode* is ``True`` the :data:`CONTEXT_POSITION_MARKER`
        class is treated specially – emitting ``?var a ?class .``.

        When *negated_class_marker_mode* is ``True`` the marker emits
        ``?class a owl:Class . FILTER NOT EXISTS { ?var a ?class . }``
        instead, which discovers classes that the individual is **not** a
        member of.  This mirrors the Java ``generateNegatedClassQuery``.

        When *property_marker_mode* is ``True`` the marker emits an object-
        property discovery pattern whose opposite endpoint is constrained to be
        an IRI, excluding datatype/literal-valued predicates.
        """
        self._marker_mode = marker_mode
        self._property_marker_mode = property_marker_mode
        self._data_property_discovery_marker_mode = data_property_discovery_marker_mode
        self._data_property_marker_mode = data_property_marker_mode
        self._negated_class_marker_mode = negated_class_marker_mode
        self._inverted = inverted
        self._inside_filter = False
        return super().convert(root_variable, ce,
                               for_all_de_morgan=for_all_de_morgan,
                               named_individuals=named_individuals)

    # -- process overloads ----------------------------------------------------
    # We need to re-register the singledispatchmethod overloads because
    # singledispatchmethod does not participate in normal inheritance; the
    # base-class registrations are inherited, but we override only the ones
    # that need marker-aware behaviour.

    @singledispatchmethod
    def process(self, ce: OWLClassExpression):
        # Delegate unknown types to the parent implementation.
        return super().process(ce)

    @process.register
    def _(self, ce: OWLClass):
        if (self._marker_mode or self._property_marker_mode or self._data_property_discovery_marker_mode
                or self._data_property_marker_mode
                or self._negated_class_marker_mode) and ce == CONTEXT_POSITION_MARKER:
            if self._property_marker_mode:
                # Property marker – discover only properties whose opposite
                # endpoint is an IRI, so datatype properties are excluded.
                object_variable = self.mapping.new_individual_variable()
                if self._inverted:
                    self.append(f"{object_variable} ?prop {self.current_variable} . FILTER(isIRI({object_variable})) ")
                else:
                    self.append(f"{self.current_variable} ?prop {object_variable} . FILTER(isIRI({object_variable})) ")
            elif self._data_property_discovery_marker_mode:
                # Data-property marker – discover only properties whose
                # opposite endpoint is a literal.
                object_variable = self.mapping.new_individual_variable()
                if self._inverted:
                    self.append(f"{object_variable} ?prop {self.current_variable} . FILTER(isLiteral({object_variable})) ")
                else:
                    self.append(f"{self.current_variable} ?prop {object_variable} . FILTER(isLiteral({object_variable})) ")
            elif self._data_property_marker_mode:
                # Datatype-value marker: use the current variable as discovered literal.
                # This avoids an extra property hop (e.g., with context ∃charge.μ we get
                # ?pos <...#charge> ?dvalue directly).
                self.append(f"BIND({self.current_variable} AS ?dvalue) FILTER(isLiteral(?dvalue)) ")
            elif self._negated_class_marker_mode:
                # Negated class marker – emit:
                #   ?class a owl:Class .
                #   FILTER NOT EXISTS { ?var a ?class . }
                # This discovers classes the individual is NOT a member of.
                self.append(
                    f"?class a <http://www.w3.org/2002/07/owl#Class> . "
                    f"FILTER NOT EXISTS {{ {self.current_variable} a ?class . }} "
                )
            else:
                # Class marker – emit ``?var a ?class .``
                self.append(f"{self.current_variable} a ?class . ")
        else:
            # Fall back to the base-class logic.
            # Inline the parent implementation because singledispatch doesn't
            # allow calling super() for a registered type directly.
            if self.ce == ce or not ce.is_owl_thing():
                self.append_triple(self.current_variable, "a", self.render(ce))
            elif ce.is_owl_thing():
                self.append_triple(self.current_variable, "a", "<http://www.w3.org/2002/07/owl#Thing>")

    @process.register
    def _(self, ce: OWLObjectComplementOf):
        subject = self.current_variable

        if self.named_individuals:
            self.append_triple(subject, "a", f"<{OWLRDFVocabulary.OWL_NAMED_INDIVIDUAL.as_str()}>")
        else:
            # self.append_triple(subject, self.mapping.new_individual_variable(),
            #                    self.mapping.new_individual_variable())
            if not (len(self.parent) > 0 and isinstance(self.parent[-1],
                                                        OWLObjectIntersectionOf) and self.modal_depth == 1):
                self.append_triple(subject, self.mapping.new_individual_variable(),
                                   self.mapping.new_individual_variable())

        old_inside = self._inside_filter
        self._inside_filter = True
        self.append("FILTER NOT EXISTS { ")
        self.process(ce.get_operand())
        self.append(" }")

        # If the marker was inside this negation, add type constraint
        if self._contains_marker(ce.get_operand()):
            if self._marker_mode or self._negated_class_marker_mode:
                self.append(" ?class a <http://www.w3.org/2002/07/owl#Class> . ")
            elif self._property_marker_mode or self._data_property_discovery_marker_mode:
                self.append(" ?prop a <http://www.w3.org/1999/02/22-rdf-syntax-ns#Property> . ")
            elif self._data_property_marker_mode:
                self.append(" FILTER(isLiteral(?dvalue)) ")

        self._inside_filter = old_inside

    # Re-register all other CE types so they are part of *this* singledispatch
    # family (otherwise Python would fall through to the base-class dispatch
    # which doesn't know about our overridden ``process`` root).

    @process.register
    def _(self, ce: OWLObjectIntersectionOf):
        for op in ce.operands():
            self.process(op)

    @process.register
    def _(self, ce: OWLObjectUnionOf):
        first = True
        for op in ce.operands():
            if first:
                first = False
            else:
                self.append(" UNION ")
            self.append("{ ")
            with self.stack_parent(op):
                self.process(op)
            self.append(" }")

    @process.register
    def _(self, ce: OWLObjectSomeValuesFrom):
        object_variable = self.mapping.new_individual_variable()
        property_expression = ce.get_property()
        if property_expression.is_anonymous():
            self.append_triple(object_variable, property_expression.get_named_property(), self.current_variable)
        else:
            self.append_triple(self.current_variable, property_expression.get_named_property(), object_variable)
        filler = ce.get_filler()
        with self.stack_variable(object_variable):
            self.process(filler)

    @process.register
    def _(self, ce: OWLObjectAllValuesFrom):
        if self.for_all_de_morgan is True:
            self.forAllDeMorgan(ce)
        else:
            self.forAll(ce)

    @process.register
    def _(self, ce: OWLObjectHasValue):
        property_expression = ce.get_property()
        value = ce.get_filler()
        assert isinstance(value, OWLNamedIndividual)
        if property_expression.is_anonymous():
            self.append_triple(value.to_string_id(), property_expression.get_named_property(), self.current_variable)
        else:
            self.append_triple(self.current_variable, property_expression.get_named_property(), value)

    @process.register
    def _(self, ce: OWLObjectCardinalityRestriction):
        subject_variable = self.current_variable
        object_variable = self.mapping.new_individual_variable()
        property_expression = ce.get_property()
        cardinality = ce.get_cardinality()

        if isinstance(ce, OWLObjectMinCardinality):
            comparator = ">="
        elif isinstance(ce, OWLObjectMaxCardinality):
            comparator = "<="
        elif isinstance(ce, OWLObjectExactCardinality):
            comparator = "="
        else:
            raise ValueError(ce)

        if comparator == "<=" or cardinality == 0:
            self.append("{")

        self.append(f"{{ SELECT {subject_variable} WHERE {{ ")
        if property_expression.is_anonymous():
            self.append_triple(object_variable, property_expression.get_named_property(), subject_variable)
        else:
            self.append_triple(subject_variable, property_expression.get_named_property(), object_variable)

        filler = ce.get_filler()
        with self.stack_variable(object_variable):
            self.process(filler)

        self.append(f" }} GROUP BY {subject_variable}"
                    f" HAVING ( COUNT ( {object_variable} ) {comparator} {cardinality} ) }}")

        if comparator == "<=" or cardinality == 0:
            self.append("} UNION {")
            self.append_triple(subject_variable, self.mapping.new_individual_variable(),
                               self.mapping.new_individual_variable())
            self.append("FILTER NOT EXISTS { ")
            object_variable = self.mapping.new_individual_variable()
            if property_expression.is_anonymous():
                self.append_triple(object_variable, property_expression.get_named_property(), self.current_variable)
            else:
                self.append_triple(self.current_variable, property_expression.get_named_property(), object_variable)
            with self.stack_variable(object_variable):
                self.process(filler)
            self.append(" } }")

    @process.register
    def _(self, ce: OWLDataCardinalityRestriction):
        subject_variable = self.current_variable
        object_variable = self.mapping.new_individual_variable()
        property_expression = ce.get_property()
        assert isinstance(property_expression, OWLDataProperty)
        cardinality = ce.get_cardinality()
        if isinstance(ce, OWLDataMinCardinality):
            comparator = ">="
        elif isinstance(ce, OWLDataMaxCardinality):
            comparator = "<="
        elif isinstance(ce, OWLDataExactCardinality):
            comparator = "="
        else:
            raise ValueError(ce)

        self.append(f"{{ SELECT {subject_variable} WHERE {{ ")
        self.append_triple(subject_variable, property_expression, object_variable)

        filler = ce.get_filler()
        with self.stack_variable(object_variable):
            self.process(filler)

        self.append(f" }} GROUP BY {subject_variable}"
                    f" HAVING ( COUNT ( {object_variable} ) {comparator} {cardinality} ) }}")

    @process.register
    def _(self, ce: OWLObjectHasSelf):
        subject = self.current_variable
        prop = ce.get_property()
        self.append_triple(subject, prop.get_named_property(), subject)

    @process.register
    def _(self, ce: OWLObjectOneOf):
        subject = self.current_variable
        if self.modal_depth == 1:
            self.append_triple(subject, "?p", "?o")
        self.append(f" FILTER ( {subject} IN ( ")
        first = True
        for ind in ce.individuals():
            if first:
                first = False
            else:
                self.append(",")
            assert isinstance(ind, OWLNamedIndividual)
            self.append(f"<{ind.to_string_id()}>")
        self.append(" ) )")

    @process.register
    def _(self, ce: OWLDataSomeValuesFrom):
        object_variable = self.mapping.new_individual_variable()
        property_expression = ce.get_property()
        assert isinstance(property_expression, OWLDataProperty)
        self.append_triple(self.current_variable, property_expression, object_variable)
        filler = ce.get_filler()
        with self.stack_variable(object_variable):
            self.process(filler)

    @process.register
    def _(self, ce: OWLDataAllValuesFrom):
        subject = self.current_variable
        object_variable = self.mapping.new_individual_variable()
        property_expression = ce.get_property()
        assert isinstance(property_expression, OWLDataProperty)
        predicate = property_expression.to_string_id()
        filler = ce.get_filler()

        self.append_triple(self.current_variable, predicate, object_variable)

        var = self.mapping.new_individual_variable()
        cnt_var1 = self.new_count_var()
        self.append(f"{{ SELECT {subject} ( COUNT( {var} ) AS {cnt_var1} ) WHERE {{ ")
        self.append_triple(subject, predicate, var)
        with self.stack_variable(var):
            self.process(filler)
        self.append(f" }} GROUP BY {subject} }}")

        var = self.mapping.new_individual_variable()
        cnt_var2 = self.new_count_var()
        self.append(f"{{ SELECT {subject} ( COUNT( {var} ) AS {cnt_var2} ) WHERE {{ ")
        self.append_triple(subject, predicate, var)
        self.append(f" }} GROUP BY {subject} }}")

        self.append(f" FILTER( {cnt_var1} = {cnt_var2} )")

    @process.register
    def _(self, ce: OWLDataHasValue):
        property_expression = ce.get_property()
        value = ce.get_filler()
        assert isinstance(value, OWLLiteral)
        self.append_triple(self.current_variable, property_expression, value)

    @process.register
    def _(self, node: OWLDatatype):
        if node != TopOWLDatatype:
            self.append(f" FILTER ( DATATYPE ( {self.current_variable} = <{node.to_string_id()}> ) ) ")
        else:
            self.append(f" FILTER ( isLiteral ( {self.current_variable} ) ) ")

    @process.register
    def _(self, node: OWLDataOneOf):
        subject = self.current_variable
        if self.modal_depth == 1:
            self.append_triple(subject, "?p", "?o")
        self.append(f" FILTER ( {subject} IN ( ")
        first = True
        for value in node.values():
            if first:
                first = False
            else:
                self.append(",")
            if value:
                self.append(self.render(value))
        self.append(" ) ) ")

    @process.register
    def _(self, node: OWLDatatypeRestriction):
        from owlapy.converter import _Variable_facet_comp
        frs = node.get_facet_restrictions()
        for fr in frs:
            facet = fr.get_facet()
            value = fr.get_facet_value()
            if facet in _Variable_facet_comp:
                self.append(f' FILTER ( {self.current_variable} {_Variable_facet_comp[facet]}'
                            f' "{value.get_literal()}"^^<{value.get_datatype().to_string_id()}> ) ')

    # -- helper: check whether a CE tree contains the marker ------------------

    @staticmethod
    def _contains_marker(ce: OWLClassExpression) -> bool:
        """Return ``True`` if *ce* (or any sub-expression) is the marker."""
        if isinstance(ce, OWLClass):
            return ce == CONTEXT_POSITION_MARKER
        if isinstance(ce, OWLObjectComplementOf):
            return QueryGenerator._contains_marker(ce.get_operand())
        if isinstance(ce, (OWLObjectIntersectionOf, OWLObjectUnionOf)):
            return any(QueryGenerator._contains_marker(op) for op in ce.operands())
        if isinstance(ce, (OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom)):
            return QueryGenerator._contains_marker(ce.get_filler())
        return False

    # -- main query builder ---------------------------------------------------

    def as_class_query(
        self,
        context: OWLClassExpression,
        positive_examples: Iterable[OWLNamedIndividual],
        negative_examples: Iterable[OWLNamedIndividual],
        root_variable_pos: str = "?pos",
        root_variable_neg: str = "?neg",
        for_all_de_morgan: bool = True,
        named_individuals: bool = False,
        filter_expression: Optional[OWLClassExpression] = None,
    ) -> str:
        """Generate a SPARQL query that discovers OWL classes with hit-counts.

        The generated query mirrors the Java ``Suggestor.generateClassQueryForGeneralNegation``:

        .. code-block:: sparql

            SELECT ?class (MAX(?tp) AS ?posHits) (MAX(?fp) AS ?negHits) WHERE {
                { SELECT ?class (COUNT(DISTINCT ?pos) AS ?tp) (0 AS ?fp) WHERE {
                    VALUES ?pos { ... }
                    <context pattern with ?pos as root and ?class at marker>
                } GROUP BY ?class }
                UNION {
                    SELECT ?class (0 AS ?tp) (COUNT(DISTINCT ?neg) AS ?fp) WHERE {
                        VALUES ?neg { ... }
                        <same context pattern but with ?neg>
                    } GROUP BY ?class
                }
            } GROUP BY ?class

        Args:
            context: A class expression that **must** contain
                :data:`CONTEXT_POSITION_MARKER` at the position where
                ``?variable a ?class .`` should be injected.
            positive_examples: Positive example individuals.
            negative_examples: Negative example individuals.
            root_variable_pos: Variable name for positive examples (default ``?pos``).
            root_variable_neg: Variable name for negative examples (default ``?neg``).
            for_all_de_morgan: Passed through to :meth:`convert`.
            named_individuals: Passed through to :meth:`convert`.
            filter_expression: Optional additional class expression used to
                create a ``FILTER NOT EXISTS`` constraint on the root variable.

        Returns:
            A valid SPARQL SELECT query string.
        """
        # -- 1. Build positive context string ---------------------------------
        positive_list = list(positive_examples)
        negative_list = list(negative_examples)

        values_pos = _generate_values_stmt(root_variable_pos, positive_list)

        # Convert the context CE with marker mode enabled
        tp = self.convert(root_variable_pos, context,
                          for_all_de_morgan=for_all_de_morgan,
                          named_individuals=named_individuals,
                          marker_mode=True)
        context_parts = [values_pos]

        # Optional filter expression (mirrors Java createNotExistsFilter)
        if filter_expression is not None:
            filter_tp = self.convert(root_variable_pos, filter_expression,
                                     for_all_de_morgan=for_all_de_morgan,
                                     named_individuals=named_individuals,
                                     marker_mode=False)
            context_parts.append(f"FILTER NOT EXISTS {{ {''.join(filter_tp)} }} ")

        context_parts.extend(tp)
        context_string = "".join(context_parts)

        # -- 2. Build negative context string (variable replacement) ----------
        values_neg = _generate_values_stmt(root_variable_neg, negative_list)
        neg_context = re.sub(
            r"VALUES\s+" + re.escape(root_variable_pos) + r"\s+\{[^}]*}",
            values_neg.rstrip(". "),
            context_string,
        )
        # Replace remaining occurrences of the positive variable
        neg_context = neg_context.replace(f"{root_variable_pos} ", f"{root_variable_neg} ")
        neg_context = neg_context.replace(f"{root_variable_pos})", f"{root_variable_neg})")

        # -- 3. Assemble final query (UNION pattern) --------------------------
        query_parts = [
            "SELECT ?class (MAX(?tp) AS ?posHits) (MAX(?fp) AS ?negHits) WHERE {\n",
            "  { SELECT ?class (COUNT(DISTINCT " + root_variable_pos + ") AS ?tp) (0 AS ?fp) WHERE {\n    ",
            context_string,
            "\n  } GROUP BY ?class }\n",
            "  UNION {\n",
            "    SELECT ?class (0 AS ?tp) (COUNT(DISTINCT " + root_variable_neg + ") AS ?fp) WHERE {\n    ",
            neg_context,
            "\n    } GROUP BY ?class\n",
            "  }\n",
            "} GROUP BY ?class",
        ]
        query = "".join(query_parts)

        # Validate
        # parseQuery(query)
        return query


    # -- negated class query builder ------------------------------------------

    def as_negated_class_query(
        self,
        context: OWLClassExpression,
        positive_examples: Iterable[OWLNamedIndividual],
        negative_examples: Iterable[OWLNamedIndividual],
        root_variable_pos: str = "?pos",
        root_variable_neg: str = "?neg",
        for_all_de_morgan: bool = True,
        named_individuals: bool = False,
        filter_expression: Optional[OWLClassExpression] = None,
    ) -> str:
        """Generate a SPARQL query that discovers OWL classes the positives
        are **not** members of, with hit-counts.

        The generated query mirrors the Java
        ``Suggestor.generateNegatedClassQuery``:

        .. code-block:: sparql

            SELECT ?class (MAX(?tp) AS ?posHits) (MAX(?fp) AS ?negHits) WHERE {
                { SELECT ?class (COUNT(DISTINCT ?pos) AS ?tp) (0 AS ?fp) WHERE {
                    VALUES ?pos { ... }
                    ?class a owl:Class .
                    FILTER NOT EXISTS { ?pos a ?class . }
                } GROUP BY ?class }
                UNION {
                    SELECT ?class (0 AS ?tp) (COUNT(DISTINCT ?neg) AS ?fp) WHERE {
                        VALUES ?neg { ... }
                        ?class a owl:Class .
                        FILTER NOT EXISTS { ?neg a ?class . }
                    } GROUP BY ?class
                }
            } GROUP BY ?class

        At the marker position the converter emits
        ``?class a owl:Class . FILTER NOT EXISTS { ?var a ?class . }``
        instead of ``?var a ?class .``.

        Args:
            context: A class expression containing :data:`CONTEXT_POSITION_MARKER`.
            positive_examples: Positive example individuals.
            negative_examples: Negative example individuals.
            root_variable_pos: Variable name for positive examples (default ``?pos``).
            root_variable_neg: Variable name for negative examples (default ``?neg``).
            for_all_de_morgan: Passed through to :meth:`convert`.
            named_individuals: Passed through to :meth:`convert`.
            filter_expression: Optional additional class expression for
                ``FILTER NOT EXISTS`` on the root variable.

        Returns:
            A valid SPARQL SELECT query string.
        """
        # -- 1. Build positive context string ---------------------------------
        positive_list = list(positive_examples)
        negative_list = list(negative_examples)

        values_pos = _generate_values_stmt(root_variable_pos, positive_list)

        tp = self.convert(root_variable_pos, context,
                          for_all_de_morgan=for_all_de_morgan,
                          named_individuals=named_individuals,
                          negated_class_marker_mode=True)
        context_parts = [values_pos]

        # Optional filter expression (mirrors Java createNotExistsFilter)
        if filter_expression is not None:
            filter_tp = self.convert(root_variable_pos, filter_expression,
                                     for_all_de_morgan=for_all_de_morgan,
                                     named_individuals=named_individuals)
            context_parts.append(f"FILTER NOT EXISTS {{ {''.join(filter_tp)} }} ")

        context_parts.extend(tp)
        context_string = "".join(context_parts)

        # -- 2. Build negative context string (variable replacement) ----------
        values_neg = _generate_values_stmt(root_variable_neg, negative_list)
        neg_context = re.sub(
            r"VALUES\s+" + re.escape(root_variable_pos) + r"\s+\{[^}]*}",
            values_neg.rstrip(". "),
            context_string,
        )
        neg_context = neg_context.replace(f"{root_variable_pos} ", f"{root_variable_neg} ")
        neg_context = neg_context.replace(f"{root_variable_pos})", f"{root_variable_neg})")

        # -- 3. Assemble final query (UNION pattern) --------------------------
        query_parts = [
            "SELECT ?class (MAX(?tp) AS ?posHits) (MAX(?fp) AS ?negHits) WHERE {\n",
            "  { SELECT ?class (COUNT(DISTINCT " + root_variable_pos + ") AS ?tp) (0 AS ?fp) WHERE {\n    ",
            context_string,
            "\n  } GROUP BY ?class }\n",
            "  UNION {\n",
            "    SELECT ?class (0 AS ?tp) (COUNT(DISTINCT " + root_variable_neg + ") AS ?fp) WHERE {\n    ",
            neg_context,
            "\n    } GROUP BY ?class\n",
            "  }\n",
            "} GROUP BY ?class",
        ]
        query = "".join(query_parts)

        # parseQuery(query)
        return query

    # -- property query builder -----------------------------------------------

    def as_property_query(
        self,
        context: OWLClassExpression,
        positive_examples: Iterable[OWLNamedIndividual],
        negative_examples: Iterable[OWLNamedIndividual],
        root_variable_pos: str = "?pos",
        root_variable_neg: str = "?neg",
        for_all_de_morgan: bool = True,
        named_individuals: bool = False,
        inverted: bool = False,
        filter_expression: Optional[OWLClassExpression] = None,
    ) -> str:
        """Generate a SPARQL query that discovers OWL properties with hit-counts.

        The generated query mirrors the Java ``Suggestor.generatePropertyQuery``
        (UNION pattern):

        .. code-block:: sparql

            SELECT ?prop (MAX(?tp) AS ?posHits) (MAX(?fp) AS ?negHits) WHERE {
                { SELECT ?prop (COUNT(DISTINCT ?pos) AS ?tp) (0 AS ?fp) WHERE {
                    VALUES ?pos { ... }
                    <context pattern with ?prop at marker>
                } GROUP BY ?prop }
                UNION {
                    SELECT ?prop (0 AS ?tp) (COUNT(DISTINCT ?neg) AS ?fp) WHERE {
                        VALUES ?neg { ... }
                        <same pattern with ?neg>
                    } GROUP BY ?prop
                }
            } GROUP BY ?prop

        Args:
            context: A class expression containing :data:`CONTEXT_POSITION_MARKER`
                at the position where an object-property pattern should be
                injected. The discovered opposite endpoint is constrained with
                ``FILTER(isIRI(...))`` so literal-valued predicates are
                excluded.
            positive_examples: Positive example individuals.
            negative_examples: Negative example individuals.
            root_variable_pos: Variable name for positive examples (default ``?pos``).
            root_variable_neg: Variable name for negative examples (default ``?neg``).
            for_all_de_morgan: Passed through to :meth:`convert`.
            named_individuals: Passed through to :meth:`convert`.
            inverted: If ``True``, emits ``?x ?prop ?var . FILTER(isIRI(?x))``
                instead of ``?var ?prop ?x . FILTER(isIRI(?x))`` at the marker
                position.
            filter_expression: Optional additional class expression for
                ``FILTER NOT EXISTS`` on the root variable.

        Returns:
            A valid SPARQL SELECT query string.
        """
        # -- 1. Build positive context string ---------------------------------
        positive_list = list(positive_examples)
        negative_list = list(negative_examples)

        values_pos = _generate_values_stmt(root_variable_pos, positive_list)

        tp = self.convert(root_variable_pos, context,
                          for_all_de_morgan=for_all_de_morgan,
                          named_individuals=named_individuals,
                          property_marker_mode=True,
                          inverted=inverted)
        context_parts = [values_pos]

        if filter_expression is not None:
            filter_tp = self.convert(root_variable_pos, filter_expression,
                                     for_all_de_morgan=for_all_de_morgan,
                                     named_individuals=named_individuals)
            context_parts.append(f"FILTER NOT EXISTS {{ {''.join(filter_tp)} }} ")

        context_parts.extend(tp)
        context_string = "".join(context_parts)

        # -- 2. Build negative context string (variable replacement) ----------
        values_neg = _generate_values_stmt(root_variable_neg, negative_list)
        neg_context = re.sub(
            r"VALUES\s+" + re.escape(root_variable_pos) + r"\s+\{[^}]*}",
            values_neg.rstrip(". "),
            context_string,
        )
        neg_context = neg_context.replace(f"{root_variable_pos} ", f"{root_variable_neg} ")
        neg_context = neg_context.replace(f"{root_variable_pos})", f"{root_variable_neg})")

        # -- 3. Assemble final query (UNION pattern) --------------------------
        query_parts = [
            "SELECT ?prop (MAX(?tp) AS ?posHits) (MAX(?fp) AS ?negHits) WHERE {\n",
            "  { SELECT ?prop (COUNT(DISTINCT " + root_variable_pos + ") AS ?tp) (0 AS ?fp) WHERE {\n    ",
            context_string,
            "\n  } GROUP BY ?prop }\n",
            "  UNION {\n",
            "    SELECT ?prop (0 AS ?tp) (COUNT(DISTINCT " + root_variable_neg + ") AS ?fp) WHERE {\n    ",
            neg_context,
            "\n    } GROUP BY ?prop\n",
            "  }\n",
            "} GROUP BY ?prop",
        ]
        return "".join(query_parts)

    def as_data_property_query(
        self,
        context: OWLClassExpression,
        positive_examples: Iterable[OWLNamedIndividual],
        negative_examples: Iterable[OWLNamedIndividual],
        root_variable_pos: str = "?pos",
        root_variable_neg: str = "?neg",
        for_all_de_morgan: bool = True,
        named_individuals: bool = False,
        inverted: bool = False,
        filter_expression: Optional[OWLClassExpression] = None,
    ) -> str:
        """Generate a SPARQL query that discovers data properties with hit-counts.

        Differs from :meth:`as_property_query` by requiring the connected
        endpoint at the marker to be a literal (``FILTER(isLiteral(...))``).
        """
        positive_list = list(positive_examples)
        negative_list = list(negative_examples)

        values_pos = _generate_values_stmt(root_variable_pos, positive_list)

        tp = self.convert(root_variable_pos, context,
                          for_all_de_morgan=for_all_de_morgan,
                          named_individuals=named_individuals,
                          data_property_discovery_marker_mode=True,
                          inverted=inverted)
        context_parts = [values_pos]

        if filter_expression is not None:
            filter_tp = self.convert(root_variable_pos, filter_expression,
                                     for_all_de_morgan=for_all_de_morgan,
                                     named_individuals=named_individuals)
            context_parts.append(f"FILTER NOT EXISTS {{ {''.join(filter_tp)} }} ")

        context_parts.extend(tp)
        context_string = "".join(context_parts)

        values_neg = _generate_values_stmt(root_variable_neg, negative_list)
        neg_context = re.sub(
            r"VALUES\s+" + re.escape(root_variable_pos) + r"\s+\{[^}]*}",
            values_neg.rstrip(". "),
            context_string,
        )
        neg_context = neg_context.replace(f"{root_variable_pos} ", f"{root_variable_neg} ")
        neg_context = neg_context.replace(f"{root_variable_pos})", f"{root_variable_neg})")

        query_parts = [
            "SELECT ?prop (MAX(?tp) AS ?posHits) (MAX(?fp) AS ?negHits) WHERE {\n",
            "  { SELECT ?prop (COUNT(DISTINCT " + root_variable_pos + ") AS ?tp) (0 AS ?fp) WHERE {\n    ",
            context_string,
            "\n  } GROUP BY ?prop }\n",
            "  UNION {\n",
            "    SELECT ?prop (0 AS ?tp) (COUNT(DISTINCT " + root_variable_neg + ") AS ?fp) WHERE {\n    ",
            neg_context,
            "\n    } GROUP BY ?prop\n",
            "  }\n",
            "} GROUP BY ?prop",
        ]
        return "".join(query_parts)



    def as_data_property_value_range_query(
        self,
        context: OWLClassExpression,
        positive_examples: Iterable[OWLNamedIndividual],
        negative_examples: Iterable[OWLNamedIndividual],
        individual_variable: str = "?ind",
        for_all_de_morgan: bool = True,
        named_individuals: bool = False,
        filter_expression: Optional[OWLClassExpression] = None,
    ) -> str:
        """Generate a query discovering datatype value ranges (min/max) per individual.

        Returns bindings with ``?ind``, ``?isPos``, ``?minVal``, ``?maxVal``.

        This query is useful for finding numeric separators in refinement operators.
        Each individual is returned with a boolean flag indicating if it's a positive
        example, along with the minimum and maximum values of the datatype property.
        """
        positive_list = list(positive_examples)
        negative_list = list(negative_examples)

        values_pos = _generate_values_stmt(individual_variable, positive_list)
        values_neg = _generate_values_stmt(individual_variable, negative_list)

        # Convert the context with data_property_marker_mode to get the pattern
        tp = self.convert(individual_variable, context,
                          for_all_de_morgan=for_all_de_morgan,
                          named_individuals=named_individuals,
                          data_property_marker_mode=True)

        context_parts = [values_pos, "BIND(true AS ?isPos)"]

        if filter_expression is not None:
            filter_tp = self.convert(individual_variable, filter_expression,
                                     for_all_de_morgan=for_all_de_morgan,
                                     named_individuals=named_individuals)
            context_parts.append(f"FILTER NOT EXISTS {{ {''.join(filter_tp)} }} ")

        context_parts.extend(tp)
        context_parts.append(
            "FILTER(datatype(?dvalue) IN ("
            "<http://www.w3.org/2001/XMLSchema#boolean>,"
            "<http://www.w3.org/2001/XMLSchema#integer>,"
            "<http://www.w3.org/2001/XMLSchema#int>,"
            "<http://www.w3.org/2001/XMLSchema#decimal>,"
            "<http://www.w3.org/2001/XMLSchema#double>,"
            "<http://www.w3.org/2001/XMLSchema#float>"
            ")) "
        )
        pos_context = "".join(context_parts)

        # Build negative context (variable and isPos replacement)
        neg_context = pos_context.replace(f"{individual_variable} ", f"{individual_variable} ")  # Keep same variable
        neg_context = neg_context.replace("BIND(true AS ?isPos)", "BIND(false AS ?isPos)")

        # Replace the VALUES clause for negatives
        neg_context = re.sub(
            r"VALUES\s+" + re.escape(individual_variable) + r"\s+\{[^}]*}",
            values_neg.rstrip(". "),
            neg_context,
        )

        # Build the final UNION query
        query_parts = [
            f"SELECT {individual_variable} ?isPos (MIN(?dvalue) AS ?minVal) (MAX(?dvalue) AS ?maxVal) WHERE {{\n",
            "  {\n",
            pos_context,
            "\n  }\n",
            "  UNION\n",
            "  {\n",
            neg_context,
            "\n  }\n",
            f"}} GROUP BY {individual_variable} ?isPos\n",
        ]
        return "".join(query_parts)

    def as_qualified_cardinality_query(
            self,
            context: OWLClassExpression,
            positive_examples: Iterable[OWLNamedIndividual],
            negative_examples: Iterable[OWLNamedIndividual],
            role: 'OWLObjectProperty' = None,
            filler: 'OWLClassExpression' = None,
            root_variable_pos: str = "?pos",
            root_variable_neg: str = "?neg",
            for_all_de_morgan: bool = True,
            named_individuals: bool = False,
            filter_expression: Optional[OWLClassExpression] = None,

    ) -> str:
        """Generate a SPARQL query discovering best cardinalities for role+filler.

        RESPECTS CONTEXT and counts only fillers matching the filler expression X.
        When facing nested ∃ r1 . ∃ r2 . X, this query finds best N for ≥N r1.X by:
        1. Converting context to build the first relation chain with CONTEXT_POSITION_MARKER
        2. Replacing ?prop with the second role to build nested triple patterns
        3. Converting filler to constrain the final object with class expressions
        4. Using nested GROUP BY to count cardinalities through intermediate variables
        5. Tracking cardinalities for positives/negatives separately

        Returns bindings: ?cardinality, ?posHits, ?negHits
        

        """
        positive_list = list(positive_examples)
        negative_list = list(negative_examples)
        values_pos = _generate_values_stmt(root_variable_pos, positive_list)

        if role is None or filler is None:
            return ""

        # Convert context to understand what must be satisfied
        context_pattern = self.convert(root_variable_pos, context,
                                       for_all_de_morgan=for_all_de_morgan,
                                       named_individuals=named_individuals,
                                       property_marker_mode=True)
        context_pattern_str = "".join(context_pattern)
        
        # NESTED RELATIONS FIX: Replace ?prop with actual role if provided
        # This handles complex nested relations like ∃r1.∃r2.X where both roles are known
        # Extract ALL intermediate variables from the context pattern path
        intermediate_variables = []  # All intermediate variables: [?s_1, ?s_2, ...]
        final_variable = None  # The object after the last role in context

        if role is not None:
            role_iri_str = role.to_string_id()

            # Extract all variables from the context pattern triples
            # Pattern: ?s_N <...> ?s_(N+1) captures all intermediate and final variables
            # We need all variables except the final one for GROUP BY
            var_matches = re.findall(r'\?s_\d+', context_pattern_str)
            if var_matches:
                # Remove duplicates while preserving order
                seen = set()
                unique_vars = []
                for var in var_matches:
                    if var not in seen:
                        unique_vars.append(var)
                        seen.add(var)

                if len(unique_vars) > 0:
                    final_variable = unique_vars[-1]  # Last variable is the final one
                    intermediate_variables = unique_vars[:-1]  # All others are intermediate

            # Replace ?prop with the role IRI in various contexts
            # Pattern 1: ?var ?prop ?obj
            context_pattern_str = re.sub(
                r'\?prop\s+',
                f'<{role_iri_str}> ',
                context_pattern_str
            )
            # Pattern 2: ?obj ?prop ?var (for inverted)
            context_pattern_str = re.sub(
                r'\s+\?prop\s+',
                f' <{role_iri_str}> ',
                context_pattern_str
            )
            # Pattern 3: (?prop) - in FILTER or other contexts
            context_pattern_str = re.sub(
                r'\(\?prop\)',
                f'(<{role_iri_str}>)',
                context_pattern_str
            )

        role_iri = role.to_string_id()
        
        # For nested relations, the filler_variable is the final object from context pattern
        # NOT a newly created variable, so it's properly bound through the context triples
        if final_variable is not None:
            # Use the final variable from context pattern
            filler_variable = final_variable
            # Convert filler pattern to constrain this variable
            filler_pattern = self.convert(filler_variable, filler,
                                          for_all_de_morgan=for_all_de_morgan,
                                          named_individuals=named_individuals)
            filler_pattern_str = "".join(filler_pattern)
        else:
            # Fallback for non-nested: create new variable as before
            filler_variable = self.mapping.new_individual_variable()
            filler_pattern = self.convert(filler_variable, filler,
                                          for_all_de_morgan=for_all_de_morgan,
                                          named_individuals=named_individuals)
            filler_pattern_str = "".join(filler_pattern)

        # For nested relations, use a different counting strategy:
        # Count distinct final objects per intermediate variable combination, then take MAX per root
        use_nested_counting = (role is not None and len(intermediate_variables) > 0 and final_variable is not None)

        if use_nested_counting:
            # Build query with nested GROUP BY for cardinality counting through intermediate variables
            # ALL intermediate variables must be in GROUP BY to isolate the count correctly
            # Pattern: GROUP BY ?pos ?s_1 ?s_2 ... (all intermediate, NOT the final being counted)

            # Build the GROUP BY clause with root + all intermediate variables
            group_by_vars = root_variable_pos + " " + " ".join(intermediate_variables)
            group_by_vars_neg = root_variable_neg + " " + " ".join(intermediate_variables)

            # Build SELECT clause with root + intermediate vars + count
            select_clause_pos = root_variable_pos + " " + " ".join(intermediate_variables) + " (COUNT(DISTINCT " + filler_variable + ") AS ?cnt)"
            select_clause_neg = root_variable_neg + " " + " ".join(intermediate_variables) + " (COUNT(DISTINCT " + filler_variable + ") AS ?cnt)"

            query_parts = [
                "PREFIX owl: <http://www.w3.org/2002/07/owl#>\n",
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n",
                "SELECT ?cardinality (MAX(?tp) AS ?posHits) (MAX(?fp) AS ?negHits) WHERE {\n",
                # POSITIVE EXAMPLES
                "  { SELECT ?cardinality (COUNT(DISTINCT " + root_variable_pos + ") AS ?tp) (0 AS ?fp) WHERE {\n",
                "    " + values_pos + "\n",
                "    { SELECT " + root_variable_pos + " (MAX(?cnt) AS ?cardinality) WHERE {\n",
                "      { SELECT " + select_clause_pos + " WHERE {\n",
                "        " + context_pattern_str + "\n",
                "        " + filler_pattern_str + "\n",
                "      } GROUP BY " + group_by_vars + " }\n",
                "    } GROUP BY " + root_variable_pos + " }\n",
                "  } GROUP BY ?cardinality }\n",
                # NEGATIVE EXAMPLES
                "  UNION {\n",
                "    SELECT ?cardinality (0 AS ?tp) (COUNT(DISTINCT " + root_variable_neg + ") AS ?fp) WHERE {\n",
                "      " + _generate_values_stmt(root_variable_neg, negative_list) + "\n",
                "      { SELECT " + root_variable_neg + " (MAX(?cnt) AS ?cardinality) WHERE {\n",
                "        { SELECT " + select_clause_neg + " WHERE {\n",
                "          " + context_pattern_str.replace(root_variable_pos, root_variable_neg) + "\n",
                "          " + filler_pattern_str + "\n",
                "        } GROUP BY " + group_by_vars_neg + " }\n",
                "      } GROUP BY " + root_variable_neg + " }\n",
                "    } GROUP BY ?cardinality\n",
                "  }\n",
                "} GROUP BY ?cardinality\n",
                "ORDER BY ?cardinality\n",
            ]
        else:
            # Original simple counting strategy for non-nested relations
            query_parts = [
                "PREFIX owl: <http://www.w3.org/2002/07/owl#>\n",
                "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n",
                "SELECT ?cardinality (MAX(?tp) AS ?posHits) (MAX(?fp) AS ?negHits) WHERE {\n",
                # POSITIVE EXAMPLES
                "  { SELECT ?cardinality (COUNT(DISTINCT " + root_variable_pos + ") AS ?tp) (0 AS ?fp) WHERE {\n",
                "    " + values_pos + "\n",
                "    { SELECT " + root_variable_pos + " (COUNT(DISTINCT " + filler_variable + ") AS ?cardinality) WHERE {\n",
                "      " + context_pattern_str + "\n",
                "      " + root_variable_pos + " <" + role_iri + "> " + filler_variable + " .\n",
                "      " + filler_pattern_str + "\n",
                "    } GROUP BY " + root_variable_pos + " }\n",
                "  } GROUP BY ?cardinality }\n",
                # NEGATIVE EXAMPLES
                "  UNION {\n",
                "    SELECT ?cardinality (0 AS ?tp) (COUNT(DISTINCT " + root_variable_neg + ") AS ?fp) WHERE {\n",
                "      " + _generate_values_stmt(root_variable_neg, negative_list) + "\n",
                "      { SELECT " + root_variable_neg + " (COUNT(DISTINCT " + filler_variable + ") AS ?cardinality) WHERE {\n",
                "        " + context_pattern_str.replace(root_variable_pos, root_variable_neg) + "\n",
                "        " + root_variable_neg + " <" + role_iri + "> " + filler_variable + " .\n",
                "        " + filler_pattern_str + "\n",
                "      } GROUP BY " + root_variable_neg + " }\n",
                "    } GROUP BY ?cardinality\n",
                "  }\n",
                "} GROUP BY ?cardinality\n",
            ]

        return "".join(query_parts)



generator = QueryGenerator()


def owl_expression_to_class_query(
    context: OWLClassExpression,
    positive_examples: Iterable[OWLNamedIndividual],
    negative_examples: Iterable[OWLNamedIndividual],
    root_variable_pos: str = "?pos",
    root_variable_neg: str = "?neg",
    for_all_de_morgan: bool = True,
    named_individuals: bool = False,
    filter_expression: Optional[OWLClassExpression] = None,
) -> str:
    """Convert an OWL class expression with a :data:`CONTEXT_POSITION_MARKER`
    into a SPARQL query that discovers OWL classes and counts how many
    positive / negative examples each class covers within the given context.

    This is the Python equivalent of the Java ``Suggestor.generateClassQuery``.

    Args:
        context: Class expression containing :data:`CONTEXT_POSITION_MARKER`.
        positive_examples: Positive example individuals.
        negative_examples: Negative example individuals.
        root_variable_pos: SPARQL variable for positives (default ``?pos``).
        root_variable_neg: SPARQL variable for negatives (default ``?neg``).
        for_all_de_morgan: Use De Morgan rewriting for universal quantifiers.
        named_individuals: Restrict to ``owl:NamedIndividual`` instances.
        filter_expression: Optional filter CE (wrapped in FILTER NOT EXISTS).

    Returns:
        A valid SPARQL SELECT query string.
    """
    return generator.as_class_query(
        context=context,
        positive_examples=positive_examples,
        negative_examples=negative_examples,
        root_variable_pos=root_variable_pos,
        root_variable_neg=root_variable_neg,
        for_all_de_morgan=for_all_de_morgan,
        named_individuals=named_individuals,
        filter_expression=filter_expression,
    )


def owl_expression_to_property_query(
    context: OWLClassExpression,
    positive_examples: Iterable[OWLNamedIndividual],
    negative_examples: Iterable[OWLNamedIndividual],
    root_variable_pos: str = "?pos",
    root_variable_neg: str = "?neg",
    for_all_de_morgan: bool = True,
    named_individuals: bool = False,
    inverted: bool = False,
    filter_expression: Optional[OWLClassExpression] = None,
) -> str:
    """Convert an OWL class expression with a :data:`CONTEXT_POSITION_MARKER`
    into a SPARQL query that discovers OWL properties and counts how many
    positive / negative examples each property covers within the given context.

    This is the Python equivalent of the Java ``Suggestor.generatePropertyQuery``.

    Args:
        context: Class expression containing :data:`CONTEXT_POSITION_MARKER`.
        positive_examples: Positive example individuals.
        negative_examples: Negative example individuals.
        root_variable_pos: SPARQL variable for positives (default ``?pos``).
        root_variable_neg: SPARQL variable for negatives (default ``?neg``).
        for_all_de_morgan: Use De Morgan rewriting for universal quantifiers.
        named_individuals: Restrict to ``owl:NamedIndividual`` instances.
        inverted: If ``True``, emits ``?x ?prop ?var . FILTER(isIRI(?x))``
            instead of ``?var ?prop ?x . FILTER(isIRI(?x))`` at the marker
            position.
        filter_expression: Optional additional class expression for
            ``FILTER NOT EXISTS`` on the root variable.

    Returns:
        A valid SPARQL SELECT query string.
    """
    return generator.as_property_query(
        context=context,
        positive_examples=positive_examples,
        negative_examples=negative_examples,
        root_variable_pos=root_variable_pos,
        root_variable_neg=root_variable_neg,
        for_all_de_morgan=for_all_de_morgan,
        named_individuals=named_individuals,
        inverted=inverted,
        filter_expression=filter_expression,
    )


def owl_expression_to_inverse_property_query(
    context: OWLClassExpression,
    positive_examples: Iterable[OWLNamedIndividual],
    negative_examples: Iterable[OWLNamedIndividual],
    root_variable_pos: str = "?pos",
    root_variable_neg: str = "?neg",
    for_all_de_morgan: bool = True,
    named_individuals: bool = False,
    filter_expression: Optional[OWLClassExpression] = None,
) -> str:
    """Convert an OWL class expression with a :data:`CONTEXT_POSITION_MARKER`
    into a SPARQL query that discovers OWL inverse properties and counts how many
    positive / negative examples each inverse property covers within the given context.

    This is similar to :func:`owl_expression_to_property_query` but discovers
    inverse properties (i.e., incoming edges) instead of outgoing edges.

    Args:
        context: Class expression containing :data:`CONTEXT_POSITION_MARKER`.
        positive_examples: Positive example individuals.
        negative_examples: Negative example individuals.
        root_variable_pos: SPARQL variable for positives (default ``?pos``).
        root_variable_neg: SPARQL variable for negatives (default ``?neg``).
        for_all_de_morgan: Use De Morgan rewriting for universal quantifiers.
        named_individuals: Restrict to ``owl:NamedIndividual`` instances.
        filter_expression: Optional filter CE (wrapped in FILTER NOT EXISTS).

    Returns:
        A valid SPARQL SELECT query string.
    """
    return generator.as_property_query(
        context=context,
        positive_examples=positive_examples,
        negative_examples=negative_examples,
        root_variable_pos=root_variable_pos,
        root_variable_neg=root_variable_neg,
        for_all_de_morgan=for_all_de_morgan,
        named_individuals=named_individuals,
        inverted=True,
        filter_expression=filter_expression,
    )


def owl_expression_to_data_property_query(
    context: OWLClassExpression,
    positive_examples: Iterable[OWLNamedIndividual],
    negative_examples: Iterable[OWLNamedIndividual],
    root_variable_pos: str = "?pos",
    root_variable_neg: str = "?neg",
    for_all_de_morgan: bool = True,
    named_individuals: bool = False,
    inverted: bool = False,
    filter_expression: Optional[OWLClassExpression] = None,
) -> str:
    """Discover data properties (literal-valued predicates) with hit counts."""
    return generator.as_data_property_query(
        context=context,
        positive_examples=positive_examples,
        negative_examples=negative_examples,
        root_variable_pos=root_variable_pos,
        root_variable_neg=root_variable_neg,
        for_all_de_morgan=for_all_de_morgan,
        named_individuals=named_individuals,
        inverted=inverted,
        filter_expression=filter_expression,
    )


def owl_expression_to_negated_class_query(
    context: OWLClassExpression,
    positive_examples: Iterable[OWLNamedIndividual],
    negative_examples: Iterable[OWLNamedIndividual],
    root_variable_pos: str = "?pos",
    root_variable_neg: str = "?neg",
    for_all_de_morgan: bool = True,
    named_individuals: bool = False,
    filter_expression: Optional[OWLClassExpression] = None,
) -> str:
    """Convert an OWL class expression with a :data:`CONTEXT_POSITION_MARKER`
    into a SPARQL query that discovers OWL classes that the positive examples
    are **not** members of, together with positive / negative hit counts.

    This is the Python equivalent of the Java
    ``Suggestor.generateNegatedClassQuery``.

    At the marker position the converter emits::

        ?class a owl:Class .
        FILTER NOT EXISTS { ?var a ?class . }

    instead of ``?var a ?class .``.

    Args:
        context: Class expression containing :data:`CONTEXT_POSITION_MARKER`.
        positive_examples: Positive example individuals.
        negative_examples: Negative example individuals.
        root_variable_pos: SPARQL variable for positives (default ``?pos``).
        root_variable_neg: SPARQL variable for negatives (default ``?neg``).
        for_all_de_morgan: Use De Morgan rewriting for universal quantifiers.
        named_individuals: Restrict to ``owl:NamedIndividual`` instances.
        filter_expression: Optional filter CE (wrapped in FILTER NOT EXISTS).

    Returns:
        A valid SPARQL SELECT query string.
    """
    return generator.as_negated_class_query(
        context=context,
        positive_examples=positive_examples,
        negative_examples=negative_examples,
        root_variable_pos=root_variable_pos,
        root_variable_neg=root_variable_neg,
        for_all_de_morgan=for_all_de_morgan,
        named_individuals=named_individuals,
        filter_expression=filter_expression,
    )





def owl_expression_to_qualified_cardinality_query(
    context: OWLClassExpression,
    positive_examples: Iterable[OWLNamedIndividual],
    negative_examples: Iterable[OWLNamedIndividual],
    role: Optional['OWLObjectProperty'] = None,
    filler: Optional[OWLClassExpression] = None,
    root_variable_pos: str = "?pos",
    root_variable_neg: str = "?neg",
    for_all_de_morgan: bool = True,
    named_individuals: bool = False,
    filter_expression: Optional[OWLClassExpression] = None,

) -> str:
    """Discover qualified cardinalities (≥n R.X, ≤n R.X) for a specific role and filler.
    
    When role and filler are provided, discovers best N for that role+filler combo.
    Returns bindings with: ?cardinality, ?posHits, ?negHits

    """
    return generator.as_qualified_cardinality_query(
        context=context,
        positive_examples=positive_examples,
        negative_examples=negative_examples,
        role=role,
        filler=filler,
        root_variable_pos=root_variable_pos,
        root_variable_neg=root_variable_neg,
        for_all_de_morgan=for_all_de_morgan,
        named_individuals=named_individuals,
        filter_expression=filter_expression,

    )


def owl_expression_to_data_property_value_range_query(
    context: OWLClassExpression,
    positive_examples: Iterable[OWLNamedIndividual],
    negative_examples: Iterable[OWLNamedIndividual],
    individual_variable: str = "?ind",
    for_all_de_morgan: bool = True,
    named_individuals: bool = False,
    filter_expression: Optional[OWLClassExpression] = None,
) -> str:
    """Discover datatype property value ranges (min/max) per individual with positive/negative flag.

    Useful for finding numeric separators in refinement operators. Returns bindings with:
    - ?ind: The individual
    - ?isPos: Boolean flag (true for positive examples, false for negative)
    - ?minVal: Minimum value of the datatype property for this individual
    - ?maxVal: Maximum value of the datatype property for this individual
    """
    return generator.as_data_property_value_range_query(
        context=context,
        positive_examples=positive_examples,
        negative_examples=negative_examples,
        individual_variable=individual_variable,
        for_all_de_morgan=for_all_de_morgan,
        named_individuals=named_individuals,
        filter_expression=filter_expression,
    )
