from owlapy.class_expression import OWLClass, OWLObjectIntersectionOf
from owlapy.owl_property import OWLObjectProperty
from owlapy.class_expression import OWLObjectSomeValuesFrom
from owlapy.converter import owl_expression_to_sparql
from owlapy.render import owl_expression_to_dl
from owlapy.iri import IRI
from owlapy.class_expression import OWLObjectUnionOf, OWLObjectIntersectionOf
class TestHashing:
    def test_simple(self):
        memory = dict()
        # An OWL Class can be used as a key in a dictionary.
        memory[OWLClass("http://example.com/father#A")] = OWLClass("http://example.com/father#A")
        memory[OWLClass("http://example.com/father#B")] = OWLClass("http://example.com/father#B")
        memory[OWLClass("http://example.com/father#C")] = OWLClass("http://example.com/father#C")

        unions = set()
        intersections = set()
        for k, v in memory.items():
            assert k == v
            # An OWLObjectUnionOf over two OWL Classes can be added into a set.
            unions.add(OWLObjectUnionOf((k, v)))
            # Since the order doesn't matter in an OWLObjectUnionOf the following also holds
            assert OWLObjectUnionOf((v, k)) in unions

            # An OWLObjectUnionOf over two OWL Classes can be added into a set.
            intersections.add(OWLObjectIntersectionOf((k, v)))
            # Since the order doesn't matter in an OWLObjectUnionOf the following also holds
            assert OWLObjectIntersectionOf((v, k)) in intersections
        # OWLObjectUnionOf and OWLObjectIntersectionOf can also be used as keys
        for i in unions | intersections:
            memory[i]=i
        for k, v in memory.items():
            assert k == v
