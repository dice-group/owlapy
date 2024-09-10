import unittest

import rdflib.plugins.sparql.sparql


from owlapy.class_expression import OWLObjectSomeValuesFrom, OWLThing, \
                                     OWLObjectMaxCardinality, OWLObjectMinCardinality, OWLObjectIntersectionOf
from owlapy.iri import IRI
from owlapy.owl_property import OWLObjectProperty

from owlapy.owl_ontology_manager import OntologyManager
from owlapy.owl_reasoner import OntologyReasoner, FastInstanceCheckerReasoner
from owlapy.parser import DLSyntaxParser
from rdflib import Graph
from owlapy.converter import Owl2SparqlConverter


PATH_FAMILY = 'KGs/Family/family-benchmark_rich_background.owl'


# checks whether all individuals returned by the reasoner are found in results generated by the sparql query
def check_reasoner_instances_in_sparql_results(sparql_results: rdflib.query.Result,
                                               reasoner_results: set) -> bool:
    sparql_results_set = set()
    for row in sparql_results:
        individual_iri = row[rdflib.Variable('x')]
        individual_iri_str = individual_iri.toPython()
        if "#" in individual_iri_str:
            sparql_results_set.add(individual_iri_str.split('#')[-1])
        else:
            sparql_results_set.add(individual_iri_str.split('/')[-1])
    for result in reasoner_results:
        if result.iri.reminder not in sparql_results_set:
            print()
            print(result.iri.reminder, "Not found in SPARQL results set")
            return False
    return True


class Test_Owl2SparqlConverter(unittest.TestCase):
    _root_var_ = '?x'
    maxDiff = None

    def test_as_query(self):
        prop_s = OWLObjectProperty(IRI.create("http://dl-learner.org/carcinogenesis#hasBond"))
        ce = OWLObjectSomeValuesFrom(
            prop_s,
            OWLObjectIntersectionOf((
                OWLObjectMaxCardinality(
                    4,
                    OWLObjectProperty(IRI.create("http://dl-learner.org/carcinogenesis#hasAtom")),
                    OWLThing
                ),
                OWLObjectMinCardinality(
                    1,
                    OWLObjectProperty(IRI.create("http://dl-learner.org/carcinogenesis#hasAtom")),
                    OWLThing
                )
            ))
        )
        cnv = Owl2SparqlConverter()
        root_var = "?x"
        query = cnv.as_query(root_var, ce, False)
        print(query)
        query_t = """SELECT
 DISTINCT ?x WHERE { 
?x <http://dl-learner.org/carcinogenesis#hasBond> ?s_1 . 
{
{ SELECT ?s_1 WHERE { 
?s_1 <http://dl-learner.org/carcinogenesis#hasAtom> ?s_2 . 
?s_2 a <http://www.w3.org/2002/07/owl#Thing> . 
 } GROUP BY ?s_1 HAVING ( COUNT ( ?s_2 ) <= 4 ) }
} UNION {
?s_1 ?s_3 ?s_4 . 
FILTER NOT EXISTS { 
?s_1 <http://dl-learner.org/carcinogenesis#hasAtom> ?s_5 . 
?s_5 a <http://www.w3.org/2002/07/owl#Thing> . 
 } }
{ SELECT ?s_1 WHERE { 
?s_1 <http://dl-learner.org/carcinogenesis#hasAtom> ?s_6 . 
?s_6 a <http://www.w3.org/2002/07/owl#Thing> . 
 } GROUP BY ?s_1 HAVING ( COUNT ( ?s_6 ) >= 1 ) }
 }"""
#         query_t = """SELECT
#  DISTINCT ?x WHERE {
# ?x <http://dl-learner.org/carcinogenesis#hasBond> ?s_1 .
# ?s_1 <http://dl-learner.org/carcinogenesis#hasAtom> ?s_2 .
# ?s_1 <http://dl-learner.org/carcinogenesis#hasAtom> ?s_3 .
#  }
# GROUP BY ?x
#  HAVING (
# COUNT ( ?s_2 ) <= 4 && COUNT ( ?s_3 ) >= 1
#  )"""
        self.assertEqual(query, query_t)  # add assertion here

    def test_Single(self):
        # rdf graph - using rdflib
        family_rdf_graph = Graph()
        family_rdf_graph.parse(location=PATH_FAMILY)
        # knowledge base - using OWLReasoner
        mgr = OntologyManager()
        onto = mgr.load_ontology(IRI.create(PATH_FAMILY))
        base_reasoner = OntologyReasoner(onto)
        family_kb_reasoner = FastInstanceCheckerReasoner(onto, base_reasoner=base_reasoner, negation_default=True)

        ce_str = "Brother"
        ce_parsed = DLSyntaxParser(namespace="http://www.benchmark.org/family#").parse_expression(expression_str=ce_str)
        actual_query = Owl2SparqlConverter().as_query(root_variable=self._root_var_, ce=ce_parsed, count=False,
                                                      values=None, named_individuals=True)
        expected_query = """SELECT DISTINCT ?x
                            WHERE {
                                ?x <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.benchmark.org/family#Brother> .
                            }"""

        sparql_results_actual = family_rdf_graph.query(actual_query)
        sparql_results_expected = family_rdf_graph.query(expected_query)
        reasoner_results = set(family_kb_reasoner.instances(ce_parsed))

        self.assertEqual(len(sparql_results_actual), len(sparql_results_expected))
        self.assertEqual(len(sparql_results_actual), len(reasoner_results))
        self.assertTrue(check_reasoner_instances_in_sparql_results(sparql_results_actual, reasoner_results))

        ce_str = "Male"
        ce_parsed = DLSyntaxParser(namespace="http://www.benchmark.org/family#").parse_expression(expression_str=ce_str)
        actual_query = Owl2SparqlConverter().as_query(root_variable=self._root_var_, ce=ce_parsed, count=False,
                                                      values=None, named_individuals=True)
        expected_query = """SELECT DISTINCT ?x
                                    WHERE {
                                        ?x <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.benchmark.org/family#Male> .
                                    }"""

        sparql_results_actual = family_rdf_graph.query(actual_query)
        sparql_results_expected = family_rdf_graph.query(expected_query)
        reasoner_results = set(family_kb_reasoner.instances(ce_parsed))

        self.assertEqual(len(sparql_results_actual), len(sparql_results_expected))
        self.assertEqual(len(sparql_results_actual), len(reasoner_results))
        self.assertTrue(check_reasoner_instances_in_sparql_results(sparql_results_actual, reasoner_results))

    def test_Intersection(self):
        # rdf graph - using rdflib
        family_rdf_graph = Graph()
        family_rdf_graph.parse(location=PATH_FAMILY)
        # knowledge base - using OWLReasoner
        mgr = OntologyManager()
        onto = mgr.load_ontology(IRI.create(PATH_FAMILY))
        base_reasoner = OntologyReasoner(onto)
        family_kb_reasoner = FastInstanceCheckerReasoner(onto, base_reasoner=base_reasoner, negation_default=True)

        ce_str = "Brother ⊓ Father"
        ce_parsed = DLSyntaxParser(namespace="http://www.benchmark.org/family#").parse_expression(expression_str=ce_str)
        actual_query = Owl2SparqlConverter().as_query(root_variable=self._root_var_, ce=ce_parsed, count=False,
                                                      values=None, named_individuals=True)
        expected_query = """SELECT DISTINCT ?x
                            WHERE {
                                ?x <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.benchmark.org/family#Brother> .
                                ?x <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.benchmark.org/family#Father> .
                            }"""

        sparql_results_actual = family_rdf_graph.query(actual_query)
        sparql_results_expected = family_rdf_graph.query(expected_query)
        reasoner_results = set(family_kb_reasoner.instances(ce_parsed))

        self.assertEqual(len(sparql_results_actual), len(sparql_results_expected))
        self.assertEqual(len(sparql_results_actual), len(reasoner_results))
        self.assertTrue(check_reasoner_instances_in_sparql_results(sparql_results_actual, reasoner_results))

    def test_Union(self):
        # rdf graph - using rdflib
        family_rdf_graph = Graph()
        family_rdf_graph.parse(location=PATH_FAMILY)
        # knowledge base - using OWLReasoner
        mgr = OntologyManager()
        onto = mgr.load_ontology(IRI.create(PATH_FAMILY))
        base_reasoner = OntologyReasoner(onto)
        family_kb_reasoner = FastInstanceCheckerReasoner(onto, base_reasoner=base_reasoner, negation_default=True)

        ce_str = "Sister ⊔ Mother"
        ce_parsed = DLSyntaxParser(namespace="http://www.benchmark.org/family#").parse_expression(expression_str=ce_str)
        actual_query = Owl2SparqlConverter().as_query(root_variable=self._root_var_, ce=ce_parsed, count=False,
                                                      values=None, named_individuals=True)
        expected_query = """SELECT DISTINCT ?x
                            WHERE {
                                { ?x <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.benchmark.org/family#Sister> . }
                                UNION
                                { ?x <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.benchmark.org/family#Mother> . }
                            }"""

        sparql_results_actual = family_rdf_graph.query(actual_query)
        sparql_results_expected = family_rdf_graph.query(expected_query)
        reasoner_results = set(family_kb_reasoner.instances(ce_parsed))

        self.assertEqual(len(sparql_results_actual), len(sparql_results_expected))
        self.assertEqual(len(sparql_results_actual), len(reasoner_results))
        self.assertTrue(check_reasoner_instances_in_sparql_results(sparql_results_actual, reasoner_results))

    def test_Complement(self):
        # rdf graph - using rdflib
        family_rdf_graph = Graph()
        family_rdf_graph.parse(location=PATH_FAMILY)
        # knowledge base - using OWLReasoner
        mgr = OntologyManager()
        onto = mgr.load_ontology(IRI.create(PATH_FAMILY))
        base_reasoner = OntologyReasoner(onto)
        family_kb_reasoner = FastInstanceCheckerReasoner(onto, base_reasoner=base_reasoner, negation_default=True)

        ce_str = "¬Mother"
        ce_parsed = DLSyntaxParser(namespace="http://www.benchmark.org/family#").parse_expression(expression_str=ce_str)
        actual_query = Owl2SparqlConverter().as_query(root_variable=self._root_var_, ce=ce_parsed, count=False,
                                                      values=None, named_individuals=True)
        expected_query = """SELECT DISTINCT ?x
                            WHERE {
                                    ?x a <http://www.w3.org/2002/07/owl#NamedIndividual> .
                                    ?x ?p ?o .
                                    FILTER NOT EXISTS { ?x a <http://www.benchmark.org/family#Mother> . }
                            }"""

        sparql_results_actual = family_rdf_graph.query(actual_query)
        sparql_results_expected = family_rdf_graph.query(expected_query)
        reasoner_results = set(family_kb_reasoner.instances(ce_parsed))

        self.assertEqual(len(sparql_results_actual), len(sparql_results_expected))
        self.assertEqual(len(sparql_results_actual), len(reasoner_results))
        self.assertTrue(check_reasoner_instances_in_sparql_results(sparql_results_actual, reasoner_results))

    def test_Exists(self):
        # rdf graph - using rdflib
        family_rdf_graph = Graph()
        family_rdf_graph.parse(location=PATH_FAMILY)
        # knowledge base - using OWLReasoner
        mgr = OntologyManager()
        onto = mgr.load_ontology(IRI.create(PATH_FAMILY))
        base_reasoner = OntologyReasoner(onto)
        family_kb_reasoner = FastInstanceCheckerReasoner(onto, base_reasoner=base_reasoner, negation_default=True)

        ce_str = "∃hasChild.Male"
        ce_parsed = DLSyntaxParser(namespace="http://www.benchmark.org/family#").parse_expression(expression_str=ce_str)
        actual_query = Owl2SparqlConverter().as_query(root_variable=self._root_var_, ce=ce_parsed, count=False,
                                                      values=None, named_individuals=True)
        expected_query = """SELECT DISTINCT ?x
                            WHERE {
                                ?x <http://www.benchmark.org/family#hasChild> ?s .
                                ?s a <http://www.benchmark.org/family#Male> .
                            }"""

        sparql_results_actual = family_rdf_graph.query(actual_query)
        sparql_results_expected = family_rdf_graph.query(expected_query)
        reasoner_results = set(family_kb_reasoner.instances(ce_parsed))

        self.assertEqual(len(sparql_results_actual), len(sparql_results_expected))
        self.assertEqual(len(sparql_results_actual), len(reasoner_results))
        self.assertTrue(check_reasoner_instances_in_sparql_results(sparql_results_actual, reasoner_results))

    # def test_ForAll(self):
    #     # rdf graph - using rdflib
    #     family_rdf_graph = Graph()
    #     family_rdf_graph.parse(location=PATH_FAMILY)
    #     # knowledge base - using OWLReasoner
    #     mgr = OntologyManager()
    #     onto = mgr.load_ontology(IRI.create(PATH_FAMILY))
    #     base_reasoner = OntologyReasoner(onto)
    #     family_kb_reasoner = FastInstanceCheckerReasoner(onto, base_reasoner=base_reasoner, negation_default=True)
    #
    #     ce_str = "∀hasChild.Male"
    #     ce_parsed = DLSyntaxParser(namespace="http://www.benchmark.org/family#").parse_expression(expression_str=ce_str)
    #     actual_query = Owl2SparqlConverter().as_query(root_variable=self._root_var_, ce=ce_parsed, count=False,
    #                                                   values=None, named_individuals=True)
    #     expected_query = """SELECT DISTINCT ?x
    #                         WHERE {
    #                             ?x a <http://www.w3.org/2002/07/owl#NamedIndividual> .
    #                             {
    #                                 ?x <http://www.benchmark.org/family#hasChild> ?s0 .
    #                                 {
    #                                     SELECT ?x (COUNT(DISTINCT ?s1) as ?c1)
    #                                     WHERE {
    #                                         ?x <http://www.benchmark.org/family#hasChild> ?s1 .
    #                                         ?s1 a <http://www.benchmark.org/family#Male> .
    #                                     }
    #                                     GROUP BY ?x
    #                                 }
    #                                 {
    #                                     SELECT ?x (COUNT(DISTINCT ?s2) as ?c2)
    #                                     WHERE {
    #                                         ?x <http://www.benchmark.org/family#hasChild> ?s2 .
    #                                     }
    #                                     GROUP BY ?x
    #                                 }
    #                                 FILTER (?c1 = ?c2)
    #                             }
    #                             UNION
    #                             {
    #                                 ?x ?p1 ?o1 FILTER NOT EXISTS { ?x <http://www.benchmark.org/family#hasChild> ?o2 . }
    #                             }
    #                         }"""
    #
    #     sparql_results_actual = family_rdf_graph.query(actual_query)
    #     sparql_results_expected = family_rdf_graph.query(expected_query)
    #     reasoner_results = set(family_kb_reasoner.instances(ce_parsed))
    #
    #     self.assertEqual(len(sparql_results_actual), len(sparql_results_expected))
    #     self.assertEqual(len(sparql_results_actual), len(reasoner_results))
    #     self.assertTrue(check_reasoner_instances_in_sparql_results(sparql_results_actual, reasoner_results))
    #
    # def test_ExistsForAllDeMorgan(self):
    #     # rdf graph - using rdflib
    #     family_rdf_graph = Graph()
    #     family_rdf_graph.parse(location=PATH_FAMILY)
    #     # knowledge base - using OWLReasoner
    #     mgr = OntologyManager()
    #     onto = mgr.load_ontology(IRI.create(PATH_FAMILY))
    #     base_reasoner = OntologyReasoner(onto)
    #     family_kb_reasoner = FastInstanceCheckerReasoner(onto, base_reasoner=base_reasoner, negation_default=True)
    #
    #     ce_str = "∀hasChild.Male"
    #     ce_parsed = DLSyntaxParser(namespace="http://www.benchmark.org/family#").parse_expression(expression_str=ce_str)
    #     actual_query = Owl2SparqlConverter().as_query(root_variable=self._root_var_, ce=ce_parsed, count=False,
    #                                                   values=None, named_individuals=True)
    #     ce_str_neg = "¬∃hasChild.¬Male"
    #     ce_parsed_neg = DLSyntaxParser(namespace="http://www.benchmark.org/family#").parse_expression(
    #         expression_str=ce_str_neg)
    #     # actual_query_neg = Owl2SparqlConverter().as_query(root_variable=self._root_var_, ce=ce_parsed_neg,
    #     #                                                   count=False, values=None, named_individuals=True)
    #
    #     sparql_results = family_rdf_graph.query(actual_query)
    #     # sparql_results_neg = family_rdf_graph.query(actual_query_neg)
    #     reasoner_results = set(family_kb_reasoner.instances(ce_parsed))
    #     reasoner_results_neg = set(family_kb_reasoner.instances(ce_parsed_neg))
    #
    #     self.assertEqual(len(sparql_results), len(reasoner_results))
    #     self.assertEqual(len(sparql_results), len(reasoner_results_neg))
    #
    #     self.assertTrue(check_reasoner_instances_in_sparql_results(sparql_results, reasoner_results))
    #     self.assertTrue(check_reasoner_instances_in_sparql_results(sparql_results, reasoner_results_neg))
    #
    #     # the commented out assertion fails because of a bug in rdf_lib (https://github.com/RDFLib/rdflib/issues/2484).
    #     # in apache jena, the queries return results of the same size
    #     # self.assertTrue(len(sparql_results_neg), len(sparql_results))
    #
    # def test_LengthyConcepts(self):
    #     # rdf graph - using rdflib
    #     family_rdf_graph = Graph()
    #     family_rdf_graph.parse(location=PATH_FAMILY)
    #     # knowledge base - using OWLReasoner
    #     mgr = OntologyManager()
    #     onto = mgr.load_ontology(IRI.create(PATH_FAMILY))
    #     base_reasoner = OntologyReasoner(onto)
    #     family_kb_reasoner = FastInstanceCheckerReasoner(onto, base_reasoner=base_reasoner, negation_default=True)
    #
    #     concepts = [
    #         "∀hasChild.(∃hasChild.¬Male)",
    #         "∀hasChild.(∃hasChild.(Brother ⊔ Sister))",
    #         "(Male ⊔ Male) ⊓ (Male ⊓ Male)",
    #         "(Male ⊓ Male) ⊔ (Male ⊓ Male)",
    #         "(Male ⊓ Male) ⊓ (Male ⊓ Male)",
    #         "(Male ⊓ Male) ⊔ ((≥ 2 hasChild.(Male ⊔ Female)) ⊓ (≥ 3 hasChild.(Male ⊔ Female)))",
    #     ]
    #
    #     for ce_str in concepts:
    #         ce_parsed = DLSyntaxParser(namespace="http://www.benchmark.org/family#").parse_expression(
    #             expression_str=ce_str)
    #         actual_query = Owl2SparqlConverter().as_query(root_variable=self._root_var_, ce=ce_parsed, count=False,
    #                                                       values=None, named_individuals=True)
    #
    #         sparql_results_actual = family_rdf_graph.query(actual_query)
    #         reasoner_results = set(family_kb_reasoner.instances(ce_parsed))
    #
    #         self.assertEqual(len(sparql_results_actual), len(reasoner_results), ce_str)
    #         self.assertTrue(check_reasoner_instances_in_sparql_results(sparql_results_actual, reasoner_results), ce_str)
    #
    # def test_QualifiedCardinalityRestriction(self):
    #     # rdf graph - using rdflib
    #     family_rdf_graph = Graph()
    #     family_rdf_graph.parse(location=PATH_FAMILY)
    #     # knowledge base - using OWLReasoner
    #     mgr = OntologyManager()
    #     onto = mgr.load_ontology(IRI.create(PATH_FAMILY))
    #     base_reasoner = OntologyReasoner(onto)
    #     family_kb_reasoner = FastInstanceCheckerReasoner(onto, base_reasoner=base_reasoner, negation_default=True)
    #
    #     concepts = [
    #         "≥ 2 hasChild.(Male ⊔ Female)",
    #         "≥ 2 hasChild.(Male ⊔ Female)",
    #         "≤ 3 hasChild.Female"
    #     ]
    #
    #     for ce_str in concepts:
    #         ce_parsed = DLSyntaxParser(namespace="http://www.benchmark.org/family#").parse_expression(
    #             expression_str=ce_str)
    #         actual_query = Owl2SparqlConverter().as_query(root_variable=self._root_var_, ce=ce_parsed, count=False,
    #                                                       values=None, named_individuals=True)
    #
    #         sparql_results_actual = family_rdf_graph.query(actual_query)
    #         reasoner_results = set(family_kb_reasoner.instances(ce_parsed))
    #
    #         self.assertEqual(len(sparql_results_actual), len(reasoner_results), ce_str)
    #         self.assertTrue(check_reasoner_instances_in_sparql_results(sparql_results_actual, reasoner_results), ce_str)
    #
    #     # need to further investigate the case for 0
    #     # ce_str = "≥ 0 hasChild.Male"
    #     # ce_parsed = DLSyntaxParser(namespace="http://www.benchmark.org/family#").parse_expression(expression_str=
    #     #                                                                                           ce_str)
    #     # actual_query = Owl2SparqlConverter().as_query(root_variable=self._root_var_, ce=ce_parsed, count=False,
    #     #                                               values=None, named_individuals=True)
    #     #
    #     # sparql_results_actual = family_rdf_graph.query(actual_query)
    #     # reasoner_results = set(family_kb_reasoner.instances(ce_parsed))
    #     #
    #     # self.assertEqual(len(sparql_results_actual), len(reasoner_results))
    #     # self.assertTrue(check_reasoner_instances_in_sparql_results(sparql_results_actual, reasoner_results))


if __name__ == '__main__':
    unittest.main()
