from owlapy.owl_reasoner import SyncReasoner
from owlapy.class_expression import OWLClass, OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.iri import IRI
from owlapy.owl_property import OWLObjectProperty


class TestHermitFather:
    def test_readme(self):

        ontology_path = "KGs/Family/father.owl"
        hermit = SyncReasoner(ontology=ontology_path, reasoner="HermiT")

        # Thing
        thing = OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing'))
        # Nothing
        nothing = OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Nothing'))

        # Person OWL Class
        person = eval("OWLClass(IRI('http://example.com/father#', 'person'))")
        # Female OWL CLass
        female = eval("OWLClass(IRI('http://example.com/father#', 'female'))")
        # hasChild object property
        hasChild = OWLObjectProperty(IRI('http://example.com/father#', 'hasChild'))

        # Sanity checking = Things
        assert hermit.instances(thing) == {OWLNamedIndividual(IRI('http://example.com/father#', 'anna')), OWLNamedIndividual(IRI('http://example.com/father#', 'martin')), OWLNamedIndividual(IRI('http://example.com/father#', 'heinz')), OWLNamedIndividual(IRI('http://example.com/father#', 'stefan')), OWLNamedIndividual(IRI('http://example.com/father#', 'michelle')), OWLNamedIndividual(IRI('http://example.com/father#', 'markus'))}
        # De Morgen Rules : Thing \equiv \neg Bottom
        assert hermit.instances(thing) == hermit.instances(nothing.get_object_complement_of())

        # Sanity checking = \exist hasChild Thing.
        assert hermit.instances(OWLObjectSomeValuesFrom(property=hasChild, filler=thing)) == eval(
            "{OWLNamedIndividual(IRI('http://example.com/father#', 'markus')), OWLNamedIndividual(IRI('http://example.com/father#', 'martin')), OWLNamedIndividual(IRI('http://example.com/father#', 'stefan')), OWLNamedIndividual(IRI('http://example.com/father#', 'anna'))}")
        # Sanity checking \exist hasChild Person.
        assert hermit.instances(OWLObjectSomeValuesFrom(property=hasChild, filler=person)) == eval(
            "{OWLNamedIndividual(IRI('http://example.com/father#', 'markus')), OWLNamedIndividual(IRI('http://example.com/father#', 'martin')), OWLNamedIndividual(IRI('http://example.com/father#', 'stefan')), OWLNamedIndividual(IRI('http://example.com/father#', 'anna'))}")
        # \exist hasChild a person = \exist hasChild a thing
        assert hermit.instances(OWLObjectSomeValuesFrom(property=hasChild, filler=thing)) == hermit.instances(
            OWLObjectSomeValuesFrom(property=hasChild, filler=person))

        # Sanity checking: \exist hasChild a female.
        assert hermit.instances(OWLObjectSomeValuesFrom(property=hasChild, filler=female)) == eval(
            "{OWLNamedIndividual(IRI('http://example.com/father#', 'markus'))}")
        # Question: hasChild something that hasChild a female.
        # Answer: stefan: (stefan haschild markus) and (markus haschild anna)
        assert hermit.instances(OWLObjectSomeValuesFrom(property=hasChild,
                                                        filler=OWLObjectSomeValuesFrom(property=hasChild,
                                                                                       filler=female))) == eval(
            "{OWLNamedIndividual(IRI('http://example.com/father#', 'stefan'))}")
        # De morgen rule: \neg \exist r \neg T  = \forall  r T
        c = thing
        forall_r_c = OWLObjectAllValuesFrom(hasChild, c)
        neg_exist_r_neg_c = OWLObjectSomeValuesFrom(hasChild, c.get_object_complement_of()).get_object_complement_of()
        assert hermit.instances(neg_exist_r_neg_c) == hermit.instances(forall_r_c)
        # De morgen rule: \neg \exist r \neg bottom  = \forall  r bottom
        c = nothing
        forall_r_c = OWLObjectAllValuesFrom(hasChild, c)
        neg_exist_r_neg_c = OWLObjectSomeValuesFrom(hasChild, c.get_object_complement_of()).get_object_complement_of()
        assert hermit.instances(neg_exist_r_neg_c) == hermit.instances(forall_r_c)