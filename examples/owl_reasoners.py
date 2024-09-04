""" A script to show that OWL Reasoners return the same retrieval results in different runtimes """
import time

from owlapy.class_expression import OWLClass, OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom
from owlapy.owl_ontology_manager import OntologyManager
from owlapy.owl_reasoner import SyncReasoner
from owlapy.utils import concept_reducer_properties

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

ontology_path = "../KGs/Family/family-benchmark_rich_background.owl"

owl_reasoners = dict()
owl_reasoners["HermiT"] = SyncReasoner(ontology=ontology_path, reasoner="HermiT")
owl_reasoners["Pellet"] = SyncReasoner(ontology=ontology_path, reasoner="Pellet")
owl_reasoners["JFact"] = SyncReasoner(ontology=ontology_path, reasoner="JFact")
owl_reasoners["Openllet"] = SyncReasoner(ontology=ontology_path, reasoner="Openllet")
onto = OntologyManager().load_ontology(ontology_path)
c: OWLClass
###################################################################
# GENERATE ALCQ CONCEPTS TO EVALUATE RETRIEVAL PERFORMANCES
# (3) R: Extract object properties.
object_properties = {i for i in onto.object_properties_in_signature()}
# (4) R⁻: Inverse of object properties.
object_properties_inverse = {i.get_inverse_property() for i in object_properties}
# (5) R*: R UNION R⁻.
object_properties_and_inverse = object_properties.union(object_properties_inverse)
# (6) NC: Named owl concepts.
nc = {i for i in onto.classes_in_signature()}
# (7) NC⁻: Complement of NC.
nnc = {i.get_object_complement_of() for i in nc}
# (8) \exist r. C s.t. C \in NC and r \in R* .
exist_nc = concept_reducer_properties(
    concepts=nc,
    properties=object_properties_and_inverse,
    cls=OWLObjectSomeValuesFrom)
# (9) \forall r. C s.t. C \in NC and r \in R* .
forall_nc = concept_reducer_properties(
    concepts=nc,
    properties=object_properties_and_inverse,
    cls=OWLObjectAllValuesFrom,
)


def eval_reasoners(iter_owl_exp, mapping):
    print("Number of expressions:", len(iter_owl_exp))
    results = dict()
    runtime_results = dict()
    for c in iter_owl_exp:
        for name_i, reasoner_i in mapping.items():
            start_time_i = time.time()
            result_reasoner_i = {i.str for i in reasoner_i.instances(c)}
            runtime_results.setdefault(name_i, []).append(time.time() - start_time_i)
            for name_j, reasoner_j in mapping.items():
                if name_i == name_j:
                    continue  # Skip self-comparison
                start_time_j = time.time()
                result_reasoner_j = {i.str for i in reasoner_j.instances(c)}
                runtime_results.setdefault(name_i, []).append(time.time() - start_time_j)
                # Compute intersection and union
                size_intersection = len(result_reasoner_i.intersection(result_reasoner_j))
                size_of_union = len(result_reasoner_i.union(result_reasoner_j))

                # Compute Jaccard similarity
                sim = 1.0 if size_of_union == 0 else size_intersection / size_of_union
                results.setdefault(name_i, {}).setdefault(name_j, []).append(sim)
    # Calculate average runtime for each reasoner
    average_runtime = {name: sum(times) / len(times) for name, times in runtime_results.items()}
    return results, average_runtime


def plot_runtimes(average_runtime, title='Average Runtime of OWL Reasoners'):
    # Plotting the bar plot
    plt.bar(average_runtime.keys(), average_runtime.values(), color='skyblue')
    plt.title(title)
    plt.ylabel('Average Runtime (seconds)')
    plt.xticks(rotation=45)
    max_rt = max(average_runtime.values())
    plt.ylim(0, max_rt * 1.1)
    plt.tight_layout()
    # Display the plot
    plt.show()


def plot_similarity_btw_reasoners(results):
    # Compute average Jaccard similarity for each pair of reasoners
    average_jaccard = {name_i: {name_j: sum(sim_list) / len(sim_list) for name_j, sim_list in comparisons.items()} for
                       name_i, comparisons in results.items()}

    # Convert the dictionary into a matrix for heatmap plotting
    reasoners = list(owl_reasoners.keys())
    matrix = np.zeros((len(reasoners), len(reasoners)))

    for i, name_i in enumerate(reasoners):
        for j, name_j in enumerate(reasoners):
            if name_i == name_j:
                matrix[i][j] = 1.0
            else:
                matrix[i][j] = average_jaccard.get(name_i, {}).get(name_j, 0.0)

    # Plotting the heatmap
    sns.heatmap(matrix, xticklabels=reasoners, yticklabels=reasoners, annot=True, cmap="coolwarm", cbar=True, vmin=0,
                vmax=1)
    plt.title('Jaccard Similarity Between OWL Reasoners')
    plt.xlabel('Reasoner')
    plt.ylabel('Reasoner')
    plt.show()


# EVAL Named Concepts
similarity_results, average_runtime_owl_reasoners = eval_reasoners(nc, owl_reasoners)
plot_similarity_btw_reasoners(similarity_results)
plot_runtimes(average_runtime_owl_reasoners, title="Avg Runtime of Reasoners on Named Concepts")
# EVAL Negated Concepts
similarity_results, average_runtime_owl_reasoners = eval_reasoners(nnc, owl_reasoners)
plot_similarity_btw_reasoners(similarity_results)
plot_runtimes(average_runtime_owl_reasoners, title="Avg Runtime of Reasoners on Negated Named Concepts")

# EVAL Exist R. NC
similarity_results, average_runtime_owl_reasoners = eval_reasoners(exist_nc, owl_reasoners)
plot_similarity_btw_reasoners(similarity_results)
plot_runtimes(average_runtime_owl_reasoners, title="Avg Runtime of Reasoners on OWLObjectSomeValuesFrom")
