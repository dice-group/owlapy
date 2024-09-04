from owlapy.owl_property import OWLObjectProperty
from owlapy.owl_reasoner import SyncReasoner
from owlapy.iri import IRI
from owlapy.class_expression import OWLClass, OWLObjectAllValuesFrom, OWLObjectComplementOf
import time
ontology_location = "../KGs/Carcinogenesis/carcinogenesis.owl"

i1 = set()
i2 = set()
i3 = set()
i4 = set()

for rsn in ["HermiT", "Pellet", "JFact", "Openllet"]:
    reasoner = SyncReasoner(ontology_location, rsn)
    # TODO AB: needs a more complex class expression to show the specific differences of the reasoners
    ce = OWLObjectAllValuesFrom(property=OWLObjectProperty(IRI('http://dl-learner.org/carcinogenesis#', 'hasAtom')),
                                filler=OWLObjectComplementOf(OWLClass(IRI('http://dl-learner.org/carcinogenesis#',
                                                                          'Sulfur-75'))))

    if rsn == "HermiT":
        i1 = set(reasoner.instances(ce))
    elif rsn == "Pellet":
        i2 = set(reasoner.instances(ce))
    elif rsn == "JFact":
        i3 = set(reasoner.instances(ce))
    elif rsn == "Openllet":
        i4 = set(reasoner.instances(ce))

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