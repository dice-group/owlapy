from owlapy.owl_property import OWLObjectProperty
from owlapy.class_expression import OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom
from owlapy.converter import owl_expression_to_sparql
from owlapy.render import owl_expression_to_dl
from owlapy.iri import IRI
from owlapy.class_expression import OWLClass, OWLObjectUnionOf, OWLObjectIntersectionOf

class TestHashing:

    def test_el_description_logic_hash(self):
        """
        EL allows complex concepts of the following form:
        C := \top | A | C1 u C2 | \existr.C
        where A is a concept and r a role name.
        For more, refer to https://www.emse.fr/~zimmermann/Teaching/KRR/el.html
        """
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

            # This also works for intersections.
            intersections.add(OWLObjectIntersectionOf((k, v)))
            # Since the order doesn't matter in an OWLObjectUnionOf the following also holds
            assert OWLObjectIntersectionOf((v, k)) in intersections
        # OWLObjectUnionOf and OWLObjectIntersectionOf can also be used as keys
        for i in unions | intersections:
            memory[i]=i
        for k, v in memory.items():
            assert k == v

        atomic_concepts={OWLClass("http://example.com/father#A"),OWLClass("http://example.com/father#B")}
        properties={OWLObjectProperty("http://example.com/society#hasChild")}
        memory = dict()
        for ac in atomic_concepts:
            for op in properties:
                # OWLObjectSomeValuesFrom can be used as a key.
                memory[OWLObjectSomeValuesFrom(property=op, filler=ac)] = OWLObjectSomeValuesFrom(property=op, filler=ac)
                memory[OWLObjectAllValuesFrom(property=op, filler=ac)] = OWLObjectAllValuesFrom(property=op, filler=ac)

        for k, v in memory.items():
            assert k == v