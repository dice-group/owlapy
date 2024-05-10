from owlapy.static_funcs import download_external_files
from owlapy.class_expression import OWLClass, OWLObjectIntersectionOf
from owlapy.iri import IRI
from owlapy.owl_property import OWLObjectProperty
from owlapy.class_expression import OWLObjectMinCardinality
from owlapy import owl_expression_to_sparql, owl_expression_to_dl, owl_expression_to_manchester

"""Full documentation on this example: https://dice-group.github.io/owlapy/usage/usage_examples.html#"""

# Download the ontologies from our ftp server if not already:
# - this is just for you to see the structure of KGs/Family/father.owl ontology
# - the datasets are not required in the script (you can comment the following line out if you want)
download_external_files("https://files.dice-research.org/projects/Ontolearn/KGs.zip")

# Create instance of atomic concepts:
namespace = "http://example.com/family#"
male = OWLClass(IRI(namespace, "male"))
female = OWLClass(IRI(namespace, "female"))
person = OWLClass(IRI(namespace, "person"))

# Create instance of an object property:
hasChild = OWLObjectProperty("http://example.com/family#hasChild")

# Create a complex class expression:
# - here a minimum cardinality restriction is created (https://www.w3.org/TR/owl2-syntax/#Minimum_Cardinality)
has_at_least_one_child = OWLObjectMinCardinality(
    cardinality=1,
    property=hasChild,
    filler=person
)

# Create an even more complex class expression:
# - here an intersection of 2 class expressions (https://www.w3.org/TR/owl2-syntax/#Intersection_of_Class_Expressions)
ce = OWLObjectIntersectionOf([male, has_at_least_one_child])

# Convert to Description Logics expression
print(f"----DL---- \n{owl_expression_to_dl(ce)}\n")

# Convert to SPARQL query
print(f"----SPARQL---- \n{owl_expression_to_sparql(ce)}\n")

# Convert to Manchester expression
print(f"----Manchester---- \n{owl_expression_to_manchester(ce)}\n")
