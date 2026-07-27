"""More targeted unit tests closing small remaining coverage gaps: owl_data_ranges.py
(__eq__ false-branches), class_expression/class_expression.py (OWLAnonymousClassExpression
default is_owl_nothing/is_owl_thing), and abstract_owl_ontology.py (default is_anonymous()).
"""
from owlapy.class_expression import OWLClass, OWLObjectSomeValuesFrom
from owlapy.iri import IRI
from owlapy.owl_data_ranges import OWLDataComplementOf, OWLDataIntersectionOf, OWLDataUnionOf
from owlapy.owl_literal import StringOWLDatatype
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_property import OWLObjectProperty

NS = "http://example.com/small_modules2#"


def test_nary_data_range_eq_false_for_different_type():
    a = OWLDataIntersectionOf([StringOWLDatatype])
    assert (a == "not a data range") is False
    assert a != OWLDataUnionOf([StringOWLDatatype])


def test_data_complement_of_eq_false_for_different_type():
    a = OWLDataComplementOf(StringOWLDatatype)
    assert (a == "not a data range") is False


def test_data_complement_of_equality_by_value():
    a = OWLDataComplementOf(StringOWLDatatype)
    b = OWLDataComplementOf(StringOWLDatatype)
    assert a == b
    assert a.get_data_range() == StringOWLDatatype


def test_anonymous_class_expression_default_is_owl_nothing_and_thing():
    prop = OWLObjectProperty(IRI.create(NS, "hasChild"))
    ce = OWLObjectSomeValuesFrom(prop, OWLClass(IRI.create(NS, "Person")))
    assert ce.is_owl_nothing() is False
    assert ce.is_owl_thing() is False


def test_ontology_default_is_anonymous_delegates_to_ontology_id(tmp_path):
    from owlapy.class_expression import OWLClass as _OWLClass
    from owlapy.owl_axiom import OWLDeclarationAxiom

    onto = SyncOntology(NS, load=False)
    onto.add_axiom(OWLDeclarationAxiom(_OWLClass(IRI.create(NS, "Person"))))
    path = str(tmp_path / "small.owl")
    onto.save(path=path)

    reloaded = SyncOntology(path)
    # AbstractOWLOntology.is_anonymous() default delegates to get_ontology_id().is_anonymous();
    # neither Ontology nor SyncOntology override it.
    assert reloaded.is_anonymous() is False
