from owlapy.owl_property import OWLObjectProperty
from owlapy.owlapi_adaptor import OWLAPIAdaptor
from owlapy.iri import IRI
from owlapy.class_expression import OWLClass, OWLObjectIntersectionOf, OWLObjectAllValuesFrom, OWLObjectComplementOf
from owlapy.providers import owl_datatype_min_exclusive_restriction
import time
ontology_location = "../KGs/Carcinogenesis/carcinogenesis.owl"

i1 = set()
i2 = set()
i3 = set()
i4 = set()

for reasoner in ["HermiT", "Pellet", "JFact", "Openllet"]:
    adaptor = OWLAPIAdaptor(ontology_location, reasoner)

    ce = OWLObjectAllValuesFrom(property=OWLObjectProperty(IRI('http://dl-learner.org/carcinogenesis#','hasAtom')),
                                filler=OWLObjectComplementOf(OWLClass(IRI('http://dl-learner.org/carcinogenesis#',
                                                                          'Sulfur-75'))))

    if reasoner == "HermiT":
        i1 = set(adaptor.instances(ce))
    elif reasoner == "Pellet":
        i2 = set(adaptor.instances(ce))
    elif reasoner == "JFact":
        i3 = set(adaptor.instances(ce))
    elif reasoner == "Openllet":
        i4 = set(adaptor.instances(ce))

print("Hermit-Pellet:")
[print(_) for _ in i1-i2]
time.sleep(10)
print("Hermit-JFact:")
[print(_) for _ in i1-i3]
time.sleep(10)
print("Hermit-Openllet:")
[print(_) for _ in i1-i4]
time.sleep(10)
print("Pellet-JFact:")
[print(_) for _ in i2-i3]
time.sleep(10)
print("Pellet-Openllet:")
[print(_) for _ in i2-i4]
time.sleep(10)
print("JFact-Openllet:")
[print(_) for _ in i3-i4]