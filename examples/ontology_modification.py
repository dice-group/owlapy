from owlapy.class_expression import OWLClass
from owlapy.owl_axiom import OWLDeclarationAxiom, OWLClassAssertionAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology_manager import OntologyManager
from owlapy.iri import IRI
from owlapy.static_funcs import download_external_files

# Download the datasets if KGs does not exist.
download_external_files("https://files.dice-research.org/projects/Ontolearn/KGs.zip")

# Load the 'father' ontology using a new ontology manager.
manager = OntologyManager()
onto = manager.load_ontology(IRI.create('file://../KGs/Family/father.owl'))

# Let's see what classes does this ontology has
[print(_) for _ in onto.classes_in_signature()]

# Create a new class
new_class = OWLClass(IRI.create('http://example.com/father#child'))

# Add a declaration axiom for this class using ontology manager
manager.add_axiom(ontology=onto, axiom=OWLDeclarationAxiom(new_class))

# Check whether the new class is added in the signature of the ontology
print("------------------------")
[print(_) for _ in onto.classes_in_signature()]

# Add an individual of type child in the ontology
new_ind = OWLNamedIndividual('http://example.com/father#lulu')
manager.add_axiom(onto, OWLClassAssertionAxiom(new_ind, new_class))

# Check if Lulu is added

print("----------------------")
[print(_) for _ in onto.individuals_in_signature()]

# Save the modified ontology locally (otherwise the changes will be lost)
manager.save_ontology(ontology=onto, document_iri=IRI.create("file:/../KGs/Family/father_modified.owl"))
# NOTE: using the same name will overwrite the current file with the new one.


"""
You can also remove axioms by using manage.remove_axiom.
There are countless axioms which you can add or remove from an ontology. 
Check them here: https://dice-group.github.io/owlapy/autoapi/owlapy/owl_axiom/index.html
"""