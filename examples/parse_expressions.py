from owlapy import dl_to_owl_expression, manchester_to_owl_expression, owl_expression_to_sparql
# Define the namespace of your ontology
namespace = "http://example.com/family#"
# Map a description logic concept into OWLClassExpression object.
print(dl_to_owl_expression("∃ hasChild.male", namespace))
# Map an OWL class expression in the manchester syntax to into OWLClassExpression object .
print(manchester_to_owl_expression("female and (hasChild max 2 person)", namespace))
# Map a description logic concept into OWLClassExpression object and then to SPARQL query
print(owl_expression_to_sparql(dl_to_owl_expression("∃ hasChild.male", namespace)))