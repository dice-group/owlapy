from owlapy import dl_to_owl_expression, manchester_to_owl_expression

# Define the namespace of your ontology
namespace = "http://example.com/family#"

# Convert dl or manchester expressions (as string) to owl expressions.
print(dl_to_owl_expression("∃ hasChild.male", namespace))

print(manchester_to_owl_expression("female and (hasChild max 2 person)", namespace))

# It's that simple :)
