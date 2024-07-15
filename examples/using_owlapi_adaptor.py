from owlapy.owlapi_adaptor import OWLAPIAdaptor
from owlapy.iri import IRI
from owlapy.class_expression import OWLClass, OWLObjectIntersectionOf

ontology_location = "../KGs/Family/family-benchmark_rich_background.owl"

# Start an adaptor session and perform your operations.
adaptor = OWLAPIAdaptor(ontology_location, "HermiT")
# Check ontology consistency
print(f"Is the given ontology consistent? --> {adaptor.has_consistent_ontology()}")

# Construct an owlapy class expression
brother = OWLClass(IRI.create("http://www.benchmark.org/family#Brother"))
father = OWLClass(IRI.create("http://www.benchmark.org/family#Father"))
brother_and_father = OWLObjectIntersectionOf([brother, father])

# Find individual belonging to that class expression
instances = adaptor.instances(brother_and_father)
print("----------------------")
print("Individuals that are brother and father at the same time:")
[print(_) for _ in instances]

# Convert from owlapy to owlapi
py_to_pi = adaptor.convert_to_owlapi(brother_and_father)

# Convert from owlapi to owlapy
pi_to_py = adaptor.convert_from_owlapi(py_to_pi, "http://www.benchmark.org/family#")
print("----------------------")
print(f"Owlapy ce: {pi_to_py}")

# Stop the JVM to free the associated resources.
adaptor.stopJVM()  # or jpype.shutdownJVM()

