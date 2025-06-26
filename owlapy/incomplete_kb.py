from owlready2 import get_ontology, destroy_entity
import random
from typing import Set

def make_kb_incomplete_ass(kb_path, output_path, rate, seed):
    """
    Makes the knowledge base incomplete by removing a certain percentage of statements (triples).

    Inputs:
    ---------------

    kb_path: Path to the input knowledge base.
    output_path: Path to save the modified (incomplete) knowledge base.
    rate: Percentage of statements to remove (0-100).
    seed: random seed for reproducibility.

    Output:
    ---------------

    Incomplete KB at level rate %
    """
    random.seed(seed)

    # Load the ontology
    kb = get_ontology(kb_path).load()
    
    # Get all individuals in the ontology
    all_individuals = list(kb.individuals())
    
    # Collect all triples (subject-predicate-object) related to the individuals
    all_triples = []
    for individual in all_individuals:
        for prop in individual.get_properties():
            for value in prop[individual]:
                all_triples.append((individual, prop, value))
    
    # Calculate the number of triples to remove based on the rate
    num_to_remove = int(len(all_triples) * (rate / 100))
    
    # Randomly select triples to remove
    triples_to_remove = random.sample(all_triples, num_to_remove)
    
    # Remove the selected triples
    for subject, predicate, obj in triples_to_remove:

        predicate[subject].remove(obj)
        
    # Save the modified ontology to a new file
    kb.save(file=output_path, format="rdfxml")

def make_kb_incomplete(kb_path, output_path, rate, seed)-> Set[str]:
    """
    Makes the knowledge base incomplete by removing a certain percentage of individuals.

    Inputs:
    ---------------

    kb_path: Path to the input knowledge base.
    output_path: Path to save the modified (incomplete) knowledge base.
    rate: Percentage of individuals to remove (0-100).
    seed: random seed for reproducibility.

    Output:
    ---------------

    Incomplete KB at level rate %
    """
    random.seed(seed)

    # Load the ontology
    kb = get_ontology(kb_path).load()
    
    # Get all individuals (instances) in the ABox
    all_individuals = list(kb.individuals())
    
    # Calculate the number of individuals to remove based on the rate
    num_to_remove = int(len(all_individuals) * (rate / 100))
    
    # Randomly select individuals to remove
    individuals_to_remove = random.sample(all_individuals, num_to_remove)
    
    # Remove the selected individuals
    for individual in individuals_to_remove:
        destroy_entity(individual)
    
    # Save the modified ontology to a new file
    kb.save(file=output_path, format="rdfxml")


def make_kb_inconsistent(kb_path, output_path, rate, seed, max_attempts=100):
    """
    This function makes the knowledge base (KB) inconsistent by introducing incorrect statements.
    
    Parameters:
    kb_path (str): Path to the original OWL ontology file.
    output_path (str): Path to save the inconsistent ontology file.
    rate (float): Percentage of incorrect statements to introduce (0-100).
    seed (int): Seed for reproducibility.
    max_attempts (int): Maximum attempts to find a valid incorrect statement.
    """
    
    # Set the random seed for reproducibility
    random.seed(seed)
    
    # Load the ontology
    onto = get_ontology(kb_path).load()

    # Get all individuals, classes, and properties
    all_individuals = list(onto.individuals())
    all_classes = list(onto.classes())
    all_object_properties = list(onto.object_properties())
    all_data_properties = list(onto.data_properties())

    def count_triples():
        """Count the number of triples (statements) in the ontology."""
        return len(list(onto.world.sparql("""
            SELECT ?s ?p ?o
            WHERE {
                ?s ?p ?o .
            }
        """)))

    def generate_incorrect_class_assertion(individual):
        """Generate an incorrect class assertion by adding a disjoint or contradictory class."""
        class_candidates = [cls for cls in all_classes if cls not in individual.is_a]
        if not class_candidates:
            return None
        
        selected_class = random.choice(class_candidates)
        individual.is_a.append(selected_class)
        print(f"Added incorrect class assertion: {individual} rdf:type {selected_class}")
        return f"Added incorrect class assertion: {individual} rdf:type {selected_class}"

    def generate_incorrect_object_property(individual):
        """Generate an incorrect object property assertion."""
        prop = random.choice(all_object_properties)
        incorrect_object = random.choice(all_individuals)
        
        if incorrect_object not in prop[individual]:
            prop[individual].append(incorrect_object)
            print(f"Added incorrect object property assertion: {individual} {prop.name} {incorrect_object}")
            return f"Added incorrect object property assertion: {individual} {prop.name} {incorrect_object}"

    def generate_incorrect_data_property(individual):
        """Generate an incorrect data property assertion (if exist in the KB)."""
        if len(all_data_properties) != 0:
            prop = random.choice(all_data_properties)
            incorrect_value = "inconsistent_value"  # Example of an incorrect data value
            
            if incorrect_value not in prop[individual]:
                setattr(individual, prop.name, incorrect_value)
                print(f"Added incorrect data property assertion: {individual} {prop.name} {incorrect_value}")
                return f"Added incorrect data property assertion: {individual} {prop.name} {incorrect_value}"
    
    def insert_incorrect_statements():
        """Insert incorrect statements based on the specified rate."""
        num_triples = count_triples()  # Use the total number of triples in the KB
        num_incorrect = int(num_triples * (rate / 100))

        incorrect_statements = []
        
        for _ in range(num_incorrect):
            attempts = 0
            while attempts < max_attempts:
                individual = random.choice(all_individuals)
                statement_type = random.choice(['class', 'object_property']) #could also add data properties later on
                
                if statement_type == 'class':
                    result = generate_incorrect_class_assertion(individual)
                elif statement_type == 'object_property':
                    result = generate_incorrect_object_property(individual)
                
                if result:
                    incorrect_statements.append(result)
                    break
                
                attempts += 1

        return incorrect_statements
    
    # Insert incorrect statements
    inconsistencies = insert_incorrect_statements()
    
    # Save the modified ontology
    onto.save(file=output_path, format="rdfxml")
    
    # Return the list of inconsistencies added
    return inconsistencies
