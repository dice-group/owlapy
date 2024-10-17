"""Format converter."""
from collections import defaultdict
from contextlib import contextmanager
from functools import singledispatchmethod
from types import MappingProxyType
from typing import Set, List, Dict, Optional, Iterable

from rdflib.plugins.sparql.parser import parseQuery

from owlapy.class_expression import OWLObjectHasValue, OWLObjectOneOf, OWLDatatypeRestriction, OWLDataMinCardinality, \
    OWLDataMaxCardinality, OWLDataExactCardinality, OWLClass, OWLClassExpression, OWLObjectIntersectionOf, \
    OWLObjectUnionOf, OWLObjectComplementOf, OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom, \
    OWLObjectCardinalityRestriction, OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality, \
    OWLDataCardinalityRestriction, OWLObjectHasSelf, OWLDataSomeValuesFrom, OWLDataAllValuesFrom, OWLDataHasValue, \
    OWLDataOneOf
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral, TopOWLDatatype
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty
from owlapy.owl_object import OWLEntity
from owlapy.owl_datatype import OWLDatatype
from owlapy.vocab import OWLFacet, OWLRDFVocabulary

_Variable_facet_comp = MappingProxyType({
    OWLFacet.MIN_INCLUSIVE: ">=",
    OWLFacet.MIN_EXCLUSIVE: ">",
    OWLFacet.MAX_INCLUSIVE: "<=",
    OWLFacet.MAX_EXCLUSIVE: "<"
})


def peek(x):
    """Peek the last element of an array.

    Returns:
        The last element arr[-1].

    """
    return x[-1]


class VariablesMapping:
    """Helper class for owl-to-sparql conversion."""
    __slots__ = 'class_cnt', 'prop_cnt', 'ind_cnt', 'dict'

    def __init__(self):
        self.class_cnt = 0
        self.prop_cnt = 0
        self.ind_cnt = 0
        self.dict = dict()

    def get_variable(self, e: OWLEntity) -> str:
        if e in self.dict:
            return self.dict[e]

        if isinstance(e, OWLClass):
            self.class_cnt += 1
            var = f"?cls_{self.class_cnt}"
        elif isinstance(e, OWLObjectProperty) or isinstance(e, OWLDataProperty):
            self.prop_cnt += 1
            var = f"?p_{self.prop_cnt}"
        elif isinstance(e, OWLNamedIndividual):
            self.ind_cnt += 1
            var = f"?ind_{self.ind_cnt}"
        else:
            raise ValueError(e)

        self.dict[e] = var
        return var

    def new_individual_variable(self) -> str:
        self.ind_cnt += 1
        return f"?s_{self.ind_cnt}"

    def new_property_variable(self) -> str:
        self.prop_cnt += 1
        return f"?p_{self.prop_cnt}"

    def __contains__(self, item: OWLEntity) -> bool:
        return item in self.dict

    def __getitem__(self, item: OWLEntity) -> str:
        return self.dict[item]


class Owl2SparqlConverter:
    """Convert owl (owlapy model class expressions) to SPARQL."""
    __slots__ = 'ce', 'sparql', 'variables', 'parent', 'parent_var', 'properties', 'variable_entities', 'cnt', \
                'mapping', 'grouping_vars', 'having_conditions', 'for_all_de_morgan', 'named_individuals', '_intersection'
    # @TODO:CD: We need to document this class. The computation behind the mapping is not clear.

    ce: OWLClassExpression
    sparql: List[str]
    variables: List[str]
    parent: List[OWLClassExpression]
    parent_var: List[str]
    variable_entities: Set[OWLEntity]
    properties: Dict[int, List[OWLEntity]]
    _intersection: Dict[int, bool]
    mapping: VariablesMapping
    grouping_vars: Dict[OWLClassExpression, Set[str]]
    having_conditions: Dict[OWLClassExpression, Set[str]]
    cnt: int
    for_all_de_morgan: bool
    named_individuals: bool

    def convert(self, root_variable: str,
                ce: OWLClassExpression,
                for_all_de_morgan: bool = True,
                named_individuals: bool = False):
        """Used to convert owl class expression to SPARQL syntax.

        Args:
            root_variable (str): Root variable name that will be used in SPARQL query.
            ce (OWLClassExpression): The owl class expression to convert.
            named_individuals (bool): If 'True' return only entities that are instances of owl:NamedIndividual.

        Returns:
            list[str]: The SPARQL query.
        """
        self.ce = ce
        self.sparql = []
        self.variables = []
        self.parent = []
        self.parent_var = []
        self.properties = defaultdict(list)
        self.variable_entities = set()
        self._intersection = defaultdict(bool)
        self.cnt = 0
        self.mapping = VariablesMapping()
        self.grouping_vars = defaultdict(set)
        self.having_conditions = defaultdict(set)
        self.for_all_de_morgan = for_all_de_morgan
        self.named_individuals = named_individuals
        # # if named_individuals is True, we return only entities that are instances of owl:NamedIndividual
        # if named_individuals:
        #     self.append_triple(root_variable, 'a', f"<{OWLRDFVocabulary.OWL_NAMED_INDIVIDUAL.as_str()}>")
        with self.stack_variable(root_variable):
            with self.stack_parent(ce):
                self.process(ce)
        return self.sparql

    @property
    def modal_depth(self):
        return len(self.variables)

    @singledispatchmethod
    def render(self, e):
        raise NotImplementedError(e)

    @render.register
    def _(self, lit: OWLLiteral):
        return f'"{lit.get_literal()}"^^<{lit.get_datatype().to_string_id()}>'

    @render.register
    def _(self, e: OWLEntity):
        if e in self.variable_entities:
            s = self.mapping.get_variable(e)
        else:
            s = f"<{e.to_string_id()}>"
        if isinstance(e, OWLObjectProperty):
            self.properties[self.modal_depth].append(e)
        return s

    def _maybe_quote(self, e):
        assert isinstance(e, str)
        if e.startswith("?"):
            return e
        else:
            return f"<{e}>"

    def _maybe_quote_p(self, p):
        if isinstance(p, str):
            if p.startswith("?") or p == "a" or p.startswith("<"):
                return p
            else:
                return f"<{p}>"
        else:
            return self.render(p)

    def _maybe_render(self, o):
        if isinstance(o, str):
            return o
        else:
            return self.render(o)


    @contextmanager
    def stack_variable(self, var):
        self.variables.append(var)
        try:
            yield
        finally:
            self.variables.pop()

    @contextmanager
    def stack_parent(self, parent: OWLClassExpression):
        self.parent.append(parent)
        self.parent_var.append(self.current_variable)
        try:
            yield
        finally:
            self.parent.pop()
            self.parent_var.pop()

    @property
    def current_variable(self):
        return peek(self.variables)

    # this method is responsible for translating class expressions to SPARQL queries
    # the decorator "@singledispatchmethod" denotes that the method is overload
    # each overload of the method is responsible for processing a different type of class expressions (e.g., ⊔ or ⊓)
    @singledispatchmethod
    def process(self, ce: OWLClassExpression):
        raise NotImplementedError(f"We cannot create SPARQL query based on the following owl class {ce}")

    # an overload of process function
    # this overload is responsible for handling single concepts (e.g., Brother)
    # general case: C
    # this is the final step of the recursion
    @process.register
    def _(self, ce: OWLClass):
        if self.ce == ce or not ce.is_owl_thing():
            self.append_triple(self.current_variable, "a", self.render(ce))
            # old_var = self.current_variable
            # new_var = self.mapping.new_individual_variable()
            # with self.stack_variable(new_var):
            #     self.append_triple(old_var, "a", new_var)
            #     self.append_triple(new_var, "<http://www.w3.org/2000/01/rdf-schema#subClassOf>*", self.render(ce))
        elif ce.is_owl_thing():
            self.append_triple(self.current_variable, "a", "<http://www.w3.org/2002/07/owl#Thing>")

    # an overload of process function
    # this overload is responsible for handling intersections of concepts (e.g., Brother ⊓ Father)
    # general case: C1 ⊓ ... ⊓ Cn
    @process.register
    def _(self, ce: OWLObjectIntersectionOf):
        # we iterate over the concepts that appear in the intersection
        for op in ce.operands():
            self.process(op)

    # an overload of process function
    # this overload is responsible for handling unions of concepts (e.g., Brother ⊔ Sister)
    # general case: C1 ⊔ ... ⊔ Cn
    @process.register
    def _(self, ce: OWLObjectUnionOf):
        first = True
        # we iterate over the concepts that appear in the union
        for op in ce.operands():
            # SPARQL's UNION comes after the first concept
            if first:
                first = False
            else:
                self.append(" UNION ")
            self.append("{ ")
            with self.stack_parent(op):
                self.process(op)
            self.append(" }")

    # an overload of process function
    # this overload is responsible for handling complements of concepts (e.g., ¬Brother)
    # general case: ¬C
    @process.register
    def _(self, ce: OWLObjectComplementOf):
        subject = self.current_variable
        # the conversion was trying here to optimize the query
        # but the proposed optimization alters the semantics of some queries
        # example: ( A ⊓ ( B ⊔ ( ¬C ) ) )
        # with the proposed optimization, the group graph pattern for (¬C) will be { FILTER NOT EXISTS { ?x a C } }
        # however, the expected pattern is { ?x ?p ?o . FILTER NOT EXISTS { ?x a C } }
        # the exclusion of "?x ?p ?o" results in the group graph pattern to just return true or false (not bindings)
        # as a result, we need to comment out the if-clause of the following line
        # if not self.in_intersection and self.modal_depth == 1:
        # if namedIndividual is set to True, do not use variables --> restrict the subject to instances of NamedIndividual
        if self.named_individuals:
            self.append_triple(subject, "a", f"<{OWLRDFVocabulary.OWL_NAMED_INDIVIDUAL.as_str()}>")
        else:
            self.append_triple(subject, self.mapping.new_individual_variable(), self.mapping.new_individual_variable())

        self.append("FILTER NOT EXISTS { ")
        # process the concept after the ¬
        self.process(ce.get_operand())
        self.append(" }")

    # an overload of process function
    # this overload is responsible for handling the exists operator (e.g., ∃hasChild.Male)
    # general case: ∃r.C
    @process.register
    def _(self, ce: OWLObjectSomeValuesFrom):
        object_variable = self.mapping.new_individual_variable()
        # property expression holds the role of the class expression (hasChild in our example)
        property_expression = ce.get_property()
        if property_expression.is_anonymous():
            # property expression is inverse of a property
            self.append_triple(object_variable, property_expression.get_named_property(), self.current_variable)
        else:
            self.append_triple(self.current_variable, property_expression.get_named_property(), object_variable)
        # filler holds the concept of the expression (Male in our example) and is processed recursively
        filler = ce.get_filler()
        with self.stack_variable(object_variable):
            self.process(filler)

    @process.register
    def _(self, ce: OWLObjectAllValuesFrom):
        if self.for_all_de_morgan is True:
            self.forAllDeMorgan(ce)
        else:
            self.forAll(ce)

    # an overload of process function
    # this overload is responsible for handling the forAll operator (e.g., ∀hasChild.Male)
    # general case: ∀r.C
    def forAll(self, ce: OWLObjectAllValuesFrom):
        subject = self.current_variable
        object_variable = self.mapping.new_individual_variable()
        # property expression holds the role of the class expression (hasChild in our example)
        property_expression = ce.get_property()
        predicate = property_expression.get_named_property()
        # filler holds the concept of the expression (Male in our example) and is processed recursively
        filler = ce.get_filler()

        self.append("{")

        if property_expression.is_anonymous():
            # property expression is inverse of a property
            self.append_triple(object_variable, predicate, self.current_variable)
        else:
            self.append_triple(self.current_variable, predicate, object_variable)

        # restrict filler
        var = self.mapping.new_individual_variable()
        cnt_var1 = self.new_count_var()
        # the count needs to use distinct
        self.append(f"{{ SELECT {subject} ( COUNT( DISTINCT {var} ) AS {cnt_var1} ) WHERE {{ ")
        self.append_triple(subject, predicate, var)
        # here, we recursively process the filler (Male in our example)
        with self.stack_variable(var):
            self.process(filler)
        self.append(f" }} GROUP BY {subject} }}")

        var = self.mapping.new_individual_variable()
        cnt_var2 = self.new_count_var()
        # the count needs to use distinct
        self.append(f"{{ SELECT {subject} ( COUNT( DISTINCT {var} ) AS {cnt_var2} ) WHERE {{ ")
        self.append_triple(subject, predicate, var)
        self.append(f" }} GROUP BY {subject} }}")

        self.append(f" FILTER( {cnt_var1} = {cnt_var2} )")
        self.append("} UNION { ")

        # here, the second group graph pattern starts
        # the second group graph pattern returns all those entities that do not appear in a triple with the property
        self.append_triple(subject, self.mapping.new_individual_variable(), self.mapping.new_individual_variable())
        self.append("FILTER NOT EXISTS { ")
        if property_expression.is_anonymous():
            # property expression is inverse of a property
            self.append_triple(self.mapping.new_individual_variable(), predicate, self.current_variable)
        else:
            self.append_triple(self.current_variable, predicate, self.mapping.new_individual_variable())
        self.append(" } }")

    # an overload of process function
    # this overload is responsible for handling the forAll operator but as if the DeMorgan law was applied
    # (e.g., ∀hasChild.Male == ¬(∃hasChild.¬Male))
    # general case: ∀r.C == ¬(∃r.¬C)
    def forAllDeMorgan(self, ce: OWLObjectAllValuesFrom):
        subject = self.current_variable
        # here, we need to apply the complement rule twice
        # the first filter not exists covers the outer ¬
        self.append_triple(subject, self.mapping.new_individual_variable(), self.mapping.new_individual_variable())
        self.append("FILTER NOT EXISTS { ")
        object_variable = self.mapping.new_individual_variable()
        # property expression holds the role of the class expression (hasChild in our example)
        property_expression = ce.get_property()
        if property_expression.is_anonymous():
            # property expression is inverse of a property
            self.append_triple(object_variable, property_expression.get_named_property(), self.current_variable)
        else:
            self.append_triple(self.current_variable, property_expression.get_named_property(), object_variable)

        # the second filter not exists covers the inner ¬
        # filler holds the concept of the expression (Male in our example) and is processed recursively
        self.append("FILTER NOT EXISTS { ")
        filler = ce.get_filler()
        with self.stack_variable(object_variable):
            self.process(filler)
        self.append(" }")
        self.append(" }")

    # an overload of process function
    # this overload is responsible for handling the exists operator combined with an individual (e.g., ∃hasChild.{john})
    # general case: ∃r.{a}
    @process.register
    def _(self, ce: OWLObjectHasValue):
        property_expression = ce.get_property()
        value = ce.get_filler()
        # we ensure that the value is an individual
        assert isinstance(value, OWLNamedIndividual)
        if property_expression.is_anonymous():
            self.append_triple(value.to_string_id(), property_expression.get_named_property(), self.current_variable)
        else:
            self.append_triple(self.current_variable, property_expression.get_named_property(), value)

    # an overload of process function
    # this overload is responsible for handling the exists operator combined with an individual(e.g., >=3 hasChild.Male)
    # general case: \theta n r.C
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

        # if the comparator is ≤ or the cardinality is 0, we need an additional group graph pattern
        # the additional group graph pattern will take care the cases where an individual is not associated with the
        # property expression
        if comparator == "<=" or cardinality == 0:
            self.append("{")

        self.append(f"{{ SELECT {subject_variable} WHERE {{ ")
        if property_expression.is_anonymous():
            # property expression is inverse of a property
            self.append_triple(object_variable, property_expression.get_named_property(), subject_variable)
        else:
            self.append_triple(subject_variable, property_expression.get_named_property(), object_variable)

        filler = ce.get_filler()
        with self.stack_variable(object_variable):
            self.process(filler)

        self.append(f" }} GROUP BY {subject_variable}"
                    f" HAVING ( COUNT ( {object_variable} ) {comparator} {cardinality} ) }}")

        # here, the second group graph pattern starts
        if comparator == "<=" or cardinality == 0:
            self.append("} UNION {")
            self.append_triple(subject_variable, self.mapping.new_individual_variable(),
                               self.mapping.new_individual_variable())
            self.append("FILTER NOT EXISTS { ")
            object_variable = self.mapping.new_individual_variable()
            if property_expression.is_anonymous():
                # property expression is inverse of a property
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

    # an overload of process function
    # this overload is responsible for handling the exists operator combined with SELF
    # general case: ∃r.SELF
    @process.register
    def _(self, ce: OWLObjectHasSelf):
        subject = self.current_variable
        property = ce.get_property()
        self.append_triple(subject, property.get_named_property(), subject)

    # an overload of process function
    # this overload is responsible for handling the one of case (e.g., { john, jane }
    # general case: { a1, ..., an }
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
        frs = node.get_facet_restrictions()

        for fr in frs:
            facet = fr.get_facet()
            value = fr.get_facet_value()

            if facet in _Variable_facet_comp:
                self.append(f' FILTER ( {self.current_variable} {_Variable_facet_comp[facet]}'
                            f' "{value.get_literal()}"^^<{value.get_datatype().to_string_id()}> ) ')

    def new_count_var(self) -> str:
        self.cnt += 1
        return f"?cnt_{self.cnt}"

    def append_triple(self, subject, predicate, object_):
        self.append(self.triple(subject, predicate, object_))

    def append(self, frag):
        self.sparql.append(frag)

    def triple(self, subject, predicate, object_):
        return f"{self._maybe_quote(subject)} {self._maybe_quote_p(predicate)} {self._maybe_render(object_)} . "

    def as_query(self,
                 root_variable: str,
                 ce: OWLClassExpression,
                 for_all_de_morgan: bool = True,
                 count: bool = False,
                 values: Optional[Iterable[OWLNamedIndividual]] = None,
                 named_individuals: bool = False) -> str:
        assert isinstance(ce,OWLClassExpression), f"ce must be an instance of OWLClassExpression. Currently {type(ce)}"
        # root variable: the variable that will be projected
        # ce: the class expression to be transformed to a SPARQL query
        # for_all_de_morgan: true -> ¬(∃r.¬C), false -> (∀r.C)
        # count: True, counts the results ; False, projects the individuals
        # values: positive or negative examples from a class expression problem
        # named_individuals: if set to True, the generated SPARQL query will return only entities that are instances
        #                    of owl:NamedIndividual
        qs = ["SELECT"]
        tp = self.convert(root_variable, ce, for_all_de_morgan=for_all_de_morgan, named_individuals=named_individuals)
        if count:
            qs.append(f" ( COUNT ( DISTINCT {root_variable} ) AS ?cnt ) WHERE {{ ")
        else:
            qs.append(f" DISTINCT {root_variable} WHERE {{ ")
        if values is not None and root_variable.startswith("?"):
            q = [f"VALUES {root_variable} {{ "]
            for x in values:
                q.append(f"<{x.to_string_id()}>")
            q.append("} . ")
            qs.extend(q)
        qs.extend(tp)
        qs.append(" }")


        query = "\n".join(qs)
        parseQuery(query)
        return query

    def as_confusion_matrix_query(self,
                                  root_variable: str,
                                  ce: OWLClassExpression,
                                  positive_examples: Iterable[OWLNamedIndividual],
                                  negative_examples: Iterable[OWLNamedIndividual],
                                  for_all_de_morgan: bool = True,
                                  named_individuals: bool = False) -> str:
        # get the graph pattern corresponding to the provided class expression (ce)
        graph_pattern_str = "".join(self.convert(root_variable,
                                                 ce,
                                                 for_all_de_morgan=for_all_de_morgan,
                                                 named_individuals=named_individuals))
        # preparation for the final query

        # required to compute false negatives
        number_of_positive_examples = 0
        # required to compute true negatives
        number_of_negative_examples = 0
        # string representation of the positive examples (to be passed to the first VALUES clause)
        positive_examples_as_str = ""
        # iterate over the positive examples
        for positive_example in positive_examples:
            number_of_positive_examples += 1
            positive_examples_as_str += f"<{positive_example.to_string_id()}> "
        assert (len(positive_examples_as_str) > 0)

        # string representation of the positive examples (to be passed to the first VALUES clause)
        negative_examples_as_str = ""
        # iterate over the negative examples
        for negative_example in negative_examples:
            number_of_negative_examples += 1
            negative_examples_as_str += f"<{negative_example.to_string_id()}> "
        assert(len(negative_examples_as_str) > 0)

        # create the sparql query
        sparql_str= f"""
                    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                    SELECT * WHERE {{
                       {{
                          SELECT (COUNT(DISTINCT {root_variable}) as ?tp) (({number_of_positive_examples} - COUNT(DISTINCT {root_variable})) as ?fn) WHERE {{
                             VALUES {root_variable} {{ {positive_examples_as_str} }}
                             {graph_pattern_str}
                          }}
                       }}
                       {{
                          SELECT (COUNT(DISTINCT {root_variable}) as ?fp) (({number_of_negative_examples} - COUNT(DISTINCT {root_variable})) as ?tn) WHERE {{
                             VALUES {root_variable} {{ {negative_examples_as_str} }}
                             {graph_pattern_str}
                          }}
                       }}
                    }}
                    """
        parseQuery(sparql_str)
        return sparql_str


converter = Owl2SparqlConverter()


def owl_expression_to_sparql(expression: OWLClassExpression = None,
                             root_variable: str = "?x",
                             values: Optional[Iterable[OWLNamedIndividual]] = None,
                             for_all_de_morgan: bool = True,
                             named_individuals: bool = False) -> str:
    """Convert an OWL Class Expression (https://www.w3.org/TR/owl2-syntax/#Class_Expressions) into a SPARQL query
     root variable: the variable that will be projected
     expression: the class expression to be transformed to a SPARQL query

     values: positive or negative examples from a class expression problem. Unclear
     for_all_de_morgan: if set to True, the SPARQL mapping will use the mapping containing the nested FILTER NOT EXISTS
     patterns for the universal quantifier (¬(∃r.¬C)), instead of the counting query
     named_individuals: if set to True, the generated SPARQL query will return only entities
     that are instances of owl:NamedIndividual
    """
    assert expression is not None, "expression cannot be None"
    return converter.as_query(root_variable, expression, count=False, values=values,
                              named_individuals=named_individuals, for_all_de_morgan=for_all_de_morgan)


def owl_expression_to_sparql_with_confusion_matrix(expression: OWLClassExpression,
                                                   positive_examples: Optional[Iterable[OWLNamedIndividual]],
                                                   negative_examples: Optional[Iterable[OWLNamedIndividual]],
                                                   root_variable: str = "?x",
                                                   for_all_de_morgan: bool = True,
                                                   named_individuals: bool = False) -> str:
    """Convert an OWL Class Expression (https://www.w3.org/TR/owl2-syntax/#Class_Expressions) into a SPARQL query
     root variable: the variable that will be projected
     expression: the class expression to be transformed to a SPARQL query
     positive_examples: positive examples from a class expression problem
     negative_examples: positive examples from a class expression problem
     for_all_de_morgan: if set to True, the SPARQL mapping will use the mapping containing the nested FILTER NOT EXISTS
     patterns for the universal quantifier (¬(∃r.¬C)), instead of the counting query
     named_individuals: if set to True, the generated SPARQL query will return only entities
     that are instances of owl:NamedIndividual
    """
    assert expression is not None, "expression cannot be None"
    assert positive_examples is not None, "positive examples cannot be None"
    assert negative_examples is not None, "negative examples cannot be None"
    return converter.as_confusion_matrix_query(root_variable,
                                               expression,
                                               positive_examples=positive_examples,
                                               negative_examples=negative_examples,
                                               named_individuals=named_individuals,
                                               for_all_de_morgan=for_all_de_morgan)
