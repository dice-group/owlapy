from owlapy.class_expression import OWLClass
from owlapy.owl_axiom import OWLDeclarationAxiom, OWLClassAssertionAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import Ontology
from owlapy.iri import IRI
from owlapy.static_funcs import download_external_files
# (1) Download the datasets if KGs does not exist.
download_external_files("https://files.dice-research.org/projects/Ontolearn/KGs.zip")
# (2) Load the father ontology.
onto = Ontology('file://../KGs/Family/father.owl')
# (3) Iterate over defined OWL classes, object properties.
print("OWL Classes:")
for c in onto.classes_in_signature():
    print(c)
print("\nOWL Properties:")
for p in onto.properties_in_signature():
    print(p)
print("\nOWL Individuals:")
for i in onto.individuals_in_signature():
    print(i)
print("\nOWL Class Axioms:")
for a in onto.general_class_axioms():
    print(a)
"""
@TODO: Will be implemented.
for a in onto.tbox_axioms():
    print(a)
for a in onto.abox_axioms_between_individuals():
    print(a)
for a in onto.abox_axioms_between_individuals_and_classes():
    print(a)
"""
# (4) Create a new class (father)
father = OWLClass(IRI.create('http://example.com/father#child'))
# (5) Add a declaration axiom for this class,
onto.add_axiom(axiom=OWLDeclarationAxiom(father))
# (6) Check whether the newly defined class is in the signature.
assert father in [ c for c in onto.classes_in_signature()]
# (7) Iterate over owl individuals
print("\nOWL Individuals:")
for i in onto.individuals_in_signature():
    print(i)
# (8) Create an owl individual and used it in an axiom.
cdemir = OWLNamedIndividual('http://example.com/father#cdemir')
onto.add_axiom(OWLClassAssertionAxiom(cdemir, father))
# (9) Check whether cdemir is in the signature.
assert cdemir in [c for c in onto.individuals_in_signature()]
# (10) Save the modified ontology locally.
onto.save(path="babo.owl", rdf_format="rdfxml")


