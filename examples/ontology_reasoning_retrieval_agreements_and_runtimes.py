""" A script to show that OWL Reasoners return the same retrieval results in different runtimes """
import time

from owlapy.class_expression import (OWLClass, OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom,
                                     OWLObjectIntersectionOf, OWLObjectUnionOf)
from owlapy.owl_ontology_manager import OntologyManager
from owlapy.owl_reasoner import SyncReasoner
from owlapy.utils import concept_reducer_properties, concept_reducer
from owlapy import owl_expression_to_dl
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from tqdm import tqdm

def eval_reasoners(iter_owl_exp, mapping,info:str=""):
    results = dict()
    runtime_results = dict()
    for c in (tqdm_bar:=tqdm(iter_owl_exp)):
        for name_i, reasoner_i in mapping.items():
            start_time_i = time.time()
            result_reasoner_i = {i.str for i in reasoner_i.instances(c)}
            runtime_results.setdefault(name_i, []).append(time.time() - start_time_i)

            tqdm_bar.set_description_str(f"{owl_expression_to_dl(c)}\t")

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

ontology_path = "../KGs/Family/father.owl"

owl_reasoners = dict()
owl_reasoners["HermiT"] = SyncReasoner(ontology=ontology_path, reasoner="HermiT")
owl_reasoners["Pellet"] = SyncReasoner(ontology=ontology_path, reasoner="Pellet")
owl_reasoners["JFact"] = SyncReasoner(ontology=ontology_path, reasoner="JFact")
owl_reasoners["Openllet"] = SyncReasoner(ontology=ontology_path, reasoner="Openllet")
onto = OntologyManager().load_ontology(ontology_path)
c: OWLClass
# () C: OWL Class.
c = {i for i in onto.classes_in_signature()}
similarity_results, average_runtime_owl_reasoners = eval_reasoners(c, owl_reasoners)
plot_similarity_btw_reasoners(similarity_results)
plot_runtimes(average_runtime_owl_reasoners, title="Avg Runtime of Reasoners on Classes")

# () Negated OWL CLasses.
nc = {i.get_object_complement_of() for i in c}
similarity_results, average_runtime_owl_reasoners = eval_reasoners(nc, owl_reasoners)
plot_similarity_btw_reasoners(similarity_results)
plot_runtimes(average_runtime_owl_reasoners, title="Avg Runtime of Reasoners on Negated Classes")
# () Intersection of OWL Classes
intersections_classes = concept_reducer(c, opt=OWLObjectIntersectionOf)
similarity_results, average_runtime_owl_reasoners = eval_reasoners(intersections_classes, owl_reasoners)
plot_similarity_btw_reasoners(similarity_results)
plot_runtimes(average_runtime_owl_reasoners, title="Avg Runtime of Reasoners on Intersection of Classes")
# () Union  of OWL Classes
unions_classes = concept_reducer(c, opt=OWLObjectUnionOf)
similarity_results, average_runtime_owl_reasoners = eval_reasoners(unions_classes, owl_reasoners)
plot_similarity_btw_reasoners(similarity_results)
plot_runtimes(average_runtime_owl_reasoners, title="Avg Runtime of Reasoners on Union of Classes")
# () Object Property Restrictions - Existential Quantification
object_properties = {i for i in onto.object_properties_in_signature()}
exist_c = concept_reducer_properties(concepts=c, properties=object_properties, cls=OWLObjectSomeValuesFrom)
similarity_results, average_runtime_owl_reasoners = eval_reasoners(exist_c, owl_reasoners)
plot_similarity_btw_reasoners(similarity_results)
plot_runtimes(average_runtime_owl_reasoners, title="Avg Runtime of Reasoners on Existential Quantifiers")
# () Object Property Restrictions - Universal Quantification
forall_c = concept_reducer_properties(concepts=c, properties=object_properties, cls=OWLObjectAllValuesFrom)
similarity_results, average_runtime_owl_reasoners = eval_reasoners(forall_c, owl_reasoners)
plot_similarity_btw_reasoners(similarity_results)
plot_runtimes(average_runtime_owl_reasoners, title="Avg Runtime of Reasoners on Universal Quantifiers")

# () Object Property Restrictions - Existential Quantification
inverse_object_properties = {i.get_inverse_property() for i in onto.object_properties_in_signature()}
exist_inverse_c = concept_reducer_properties(concepts=c, properties=inverse_object_properties, cls=OWLObjectSomeValuesFrom)
similarity_results, average_runtime_owl_reasoners = eval_reasoners(exist_inverse_c, owl_reasoners)
plot_similarity_btw_reasoners(similarity_results)
plot_runtimes(average_runtime_owl_reasoners, title="Avg Runtime of Reasoners on Existential Quantifiers with inverse properties")
# () Object Property Restrictions - Universal Quantification
forall_inverse_c = concept_reducer_properties(concepts=c, properties=inverse_object_properties, cls=OWLObjectAllValuesFrom)
similarity_results, average_runtime_owl_reasoners = eval_reasoners(forall_inverse_c, owl_reasoners)
plot_similarity_btw_reasoners(similarity_results)
plot_runtimes(average_runtime_owl_reasoners, title="Avg Runtime of Reasoners on Universal Quantifiers with inverse properties")

