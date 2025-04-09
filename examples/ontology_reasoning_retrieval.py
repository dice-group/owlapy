"""

KB = { (A subclass B), (B subclass C), (x type A) }

KB = { (A subclass B), (B subclass C), (x type A), (x type B), (x type C) }

Missing types are inferred due to subclass hierarchy.
"""
from owlapy.class_expression import OWLClass
from owlapy.owl_axiom import OWLDeclarationAxiom, OWLClassAssertionAxiom, OWLSubClassOfAxiom
from owlapy.owl_ontology import Ontology
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.iri import IRI
from owlapy.owl_reasoner import SyncReasoner
# () Define a base IRI.
base_iri = IRI(namespace="https://github.com/dice-group/owlapy#")
# () Create an empty ontology.
onto = Ontology(base_iri, load=False)
# () Define classes and individuals.
A = OWLClass(iri=base_iri.get_namespace() + "A")
B = OWLClass(iri=base_iri.get_namespace() + "B")
C = OWLClass(iri=base_iri.get_namespace() + "C")
x = OWLNamedIndividual(iri=base_iri.get_namespace() + "x")
# () Add axioms.
onto.add_axiom([OWLDeclarationAxiom(A),
                OWLDeclarationAxiom(B),
                OWLDeclarationAxiom(C),
                OWLDeclarationAxiom(x),
                OWLSubClassOfAxiom(A,B),
                OWLSubClassOfAxiom(B,C),
                OWLClassAssertionAxiom(x,A)])
# () Save axioms [ (A subclass B), (B subclass C), (x type A) ].
onto.save("new_ontology.owl")
# () Initialize reasoner.
reasoner = SyncReasoner(ontology="new_ontology.owl", reasoner="Pellet")
# () Infer instances.
for i in reasoner.ontology.classes_in_signature():
    print(f"Retrieve {i}:", end=" ")
    print(" ".join([_.str for _ in reasoner.instances(i)]))
