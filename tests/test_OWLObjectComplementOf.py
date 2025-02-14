from owlapy.class_expression import (
    OWLClass,
    OWLObjectComplementOf,
)
from owlapy.iri import IRI
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner import SyncReasoner


def test_complement_of_owl_thing_is_owl_nothing():
    owl_thing = OWLClass(IRI.create('http://www.w3.org/2002/07/owl#Thing'))
    owl_nothing = OWLClass(IRI.create('http://www.w3.org/2002/07/owl#Nothing'))
    complement_of_thing = OWLObjectComplementOf(owl_thing)
    complement_of_nothing = OWLObjectComplementOf(owl_nothing)
    onto = SyncOntology("KGs/Mutagenesis/mutagenesis.owl", load=True)
    reasoner = SyncReasoner(onto, "HermiT")
    equivalent_classes = reasoner.equivalent_classes(complement_of_thing)
    assert owl_nothing in equivalent_classes
    individuals_thing = reasoner.instances(owl_thing)
    individuals_complement_of_nothing = reasoner.instances(complement_of_nothing)
    assert individuals_thing == individuals_complement_of_nothing


def test_complement_of_owl_nothing_is_owl_thing():
    owl_thing = OWLClass(IRI.create('http://www.w3.org/2002/07/owl#Thing'))
    owl_nothing = OWLClass(IRI.create('http://www.w3.org/2002/07/owl#Nothing'))
    complement_of_nothing = OWLObjectComplementOf(owl_nothing)
    onto = SyncOntology("KGs/Mutagenesis/mutagenesis.owl", load=True)
    reasoner = SyncReasoner(onto, "HermiT")
    individuals_thing = reasoner.instances(owl_thing)
    individuals_complement_of_nothing = reasoner.instances(complement_of_nothing)
    assert individuals_thing == individuals_complement_of_nothing


def test_double_complement_is_identity():
    class_iri = IRI.create('http://example.org/MyClass')
    my_class = OWLClass(class_iri)
    complement = OWLObjectComplementOf(my_class)
    double_complement = OWLObjectComplementOf(complement)
    assert my_class == double_complement

