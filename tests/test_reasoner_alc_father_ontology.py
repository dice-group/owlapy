from owlapy.owl_reasoner import SyncReasoner
from owlapy.class_expression import OWLClass, OWLObjectSomeValuesFrom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.iri import IRI
from owlapy.owl_property import OWLObjectProperty


class TestHermitFather:
    def test_readme(self):

        ontology_path = "KGs/Family/father.owl"
        hermit = SyncReasoner(ontology=ontology_path, reasoner="HermiT")

        # Thing
        thing = OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing'))
        # Person OWL Class
        person = eval("OWLClass(IRI('http://example.com/father#', 'person'))")
        # Female OWL CLass
        female = eval("OWLClass(IRI('http://example.com/father#', 'female'))")
        # hasChild object property
        hasChild = OWLObjectProperty(IRI('http://example.com/father#', 'hasChild'))

        # Things
        assert hermit.instances(thing) == {OWLNamedIndividual(IRI('http://example.com/father#', 'anna')), OWLNamedIndividual(IRI('http://example.com/father#', 'martin')), OWLNamedIndividual(IRI('http://example.com/father#', 'heinz')), OWLNamedIndividual(IRI('http://example.com/father#', 'stefan')), OWLNamedIndividual(IRI('http://example.com/father#', 'michelle')), OWLNamedIndividual(IRI('http://example.com/father#', 'markus'))}

        # hasChild a thing.
        assert hermit.instances(OWLObjectSomeValuesFrom(property=hasChild, filler=thing)) == eval(
            "{OWLNamedIndividual(IRI('http://example.com/father#', 'markus')), OWLNamedIndividual(IRI('http://example.com/father#', 'martin')), OWLNamedIndividual(IRI('http://example.com/father#', 'stefan')), OWLNamedIndividual(IRI('http://example.com/father#', 'anna'))}")

        # hasChild a person.
        assert hermit.instances(OWLObjectSomeValuesFrom(property=hasChild, filler=person)) == eval(
            "{OWLNamedIndividual(IRI('http://example.com/father#', 'markus')), OWLNamedIndividual(IRI('http://example.com/father#', 'martin')), OWLNamedIndividual(IRI('http://example.com/father#', 'stefan')), OWLNamedIndividual(IRI('http://example.com/father#', 'anna'))}")

        # hasChild a female.
        assert hermit.instances(OWLObjectSomeValuesFrom(property=hasChild, filler=female)) == eval(
            "{OWLNamedIndividual(IRI('http://example.com/father#', 'markus'))}")
        # Question: hasChild something that hasChild a female.
        # Answer: stefan
        # (stefan haschild markus) and markus haschild anna
        assert hermit.instances(OWLObjectSomeValuesFrom(property=hasChild,
                                                        filler=OWLObjectSomeValuesFrom(property=hasChild,
                                                                                       filler=female))) == eval(
            "{OWLNamedIndividual(IRI('http://example.com/father#', 'stefan'))}")

