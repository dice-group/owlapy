from owlapy.owl_neural_reasoners.owl_neural_reasoner import OWLNeuralReasoner
from owlapy.owl_reasoner import StructuralReasoner
from owlapy.owl_ontology_manager import OntologyManager
from owlapy.utils import concept_reducer, concept_reducer_properties, jaccard_similarity, f1_set_similarity
from owlapy.class_expression import (
    OWLObjectUnionOf,
    OWLObjectIntersectionOf,
    OWLObjectSomeValuesFrom,
    OWLObjectAllValuesFrom,
    OWLObjectMinCardinality,
    OWLObjectMaxCardinality,
    OWLObjectOneOf,
)
import time
from typing import Tuple, Set
import random
import itertools

def test_retrieval_performance():
    # Set up variables
    path_kg = "KGs/Family/family-benchmark_rich_background.owl"  
    path_kge_model = None       
    gamma = 0.8
    seed = 42
    ratio_sample_object_prop = 1.0
    ratio_sample_nc = 1.0
    num_nominals = 10
    min_jaccard_similarity = 1.0  
    min_f1_score = 1.0

    # (1) Initialize knowledge base.
    symbolic_kb = StructuralReasoner(ontology=OntologyManager().load_ontology(path=path_kg))

    # (2) Initialize Neural OWL Reasoner.
    if path_kge_model:
        neural_owl_reasoner = OWLNeuralReasoner(path_neural_embedding=path_kge_model, gamma=gamma)
    else:
        neural_owl_reasoner = OWLNeuralReasoner(path_of_kb=path_kg, gamma=gamma)

    # Fix the random seed.
    random.seed(seed)

    ###################################################################
    # GENERATE DL CONCEPTS TO EVALUATE RETRIEVAL PERFORMANCES

    # (3) R: Extract object properties.
    object_properties = {i for i in symbolic_kb.get_root_ontology().object_properties_in_signature()}

    # (3.1) Subsample if required.
    if ratio_sample_object_prop and len(object_properties) > 0:
        object_properties = {i for i in random.sample(population=list(object_properties),
                                                      k=max(1, int(len(object_properties) * ratio_sample_object_prop)))}

    # (4) R⁻: Inverse of object properties.
    object_properties_inverse = {i.get_inverse_property() for i in object_properties}

    # (5) R*: R UNION R⁻.
    object_properties_and_inverse = object_properties.union(object_properties_inverse)

    # (6) NC: Named owl concepts.
    nc = {i for i in symbolic_kb.get_root_ontology().classes_in_signature()}

    if ratio_sample_nc and len(nc) > 0:
        # (6.1) Subsample if required.
        nc = {i for i in random.sample(population=list(nc), k=max(1, int(len(nc) * ratio_sample_nc)))}

    # (7) NC⁻: Complement of NC.
    nnc = {i.get_object_complement_of() for i in nc}

    # (8) NC*: NC UNION NC⁻.
    nc_star = nc.union(nnc)

    # (9) Retrieve random Nominals.
    inds_in_sig = list(symbolic_kb.get_root_ontology().individuals_in_signature())
    if len(inds_in_sig) > num_nominals:
        nominals = set(random.sample(inds_in_sig, num_nominals))
    else:
        nominals = set(inds_in_sig)

    # (10) All combinations of 3 for Nominals.
    nominal_combinations = set(OWLObjectOneOf(combination) for combination in itertools.combinations(nominals, 3))

    # (13) NC* UNION NC*.
    unions_nc_star = concept_reducer(nc_star, opt=OWLObjectUnionOf)

    # (14) NC* INTERSECTION NC*.
    intersections_nc_star = concept_reducer(nc_star, opt=OWLObjectIntersectionOf)

    # (15) ∃ r. C s.t. C ∈ NC* and r ∈ R* .
    exist_nc_star = concept_reducer_properties(
        concepts=nc_star,
        properties=object_properties_and_inverse,
        cls=OWLObjectSomeValuesFrom,
    )

    # (16) ∀ r. C s.t. C ∈ NC* and r ∈ R* .
    for_all_nc_star = concept_reducer_properties(
        concepts=nc_star,
        properties=object_properties_and_inverse,
        cls=OWLObjectAllValuesFrom,
    )

    # (17) ≥ n r. C and ≤ n r. C, s.t. C ∈ NC* and r ∈ R* .
    min_cardinality_nc_star_1 = concept_reducer_properties(
        concepts=nc_star,
        properties=object_properties_and_inverse,
        cls=OWLObjectMinCardinality,
        cardinality=1,
    )
    min_cardinality_nc_star_2 = concept_reducer_properties(
        concepts=nc_star,
        properties=object_properties_and_inverse,
        cls=OWLObjectMinCardinality,
        cardinality=2,
    )
    min_cardinality_nc_star_3 = concept_reducer_properties(
        concepts=nc_star,
        properties=object_properties_and_inverse,
        cls=OWLObjectMinCardinality,
        cardinality=3,
    )

    max_cardinality_nc_star_1 = concept_reducer_properties(
        concepts=nc_star,
        properties=object_properties_and_inverse,
        cls=OWLObjectMaxCardinality,
        cardinality=1,
    )
    max_cardinality_nc_star_2 = concept_reducer_properties(
        concepts=nc_star,
        properties=object_properties_and_inverse,
        cls=OWLObjectMaxCardinality,
        cardinality=2,
    )
    max_cardinality_nc_star_3 = concept_reducer_properties(
        concepts=nc_star,
        properties=object_properties_and_inverse,
        cls=OWLObjectMaxCardinality,
        cardinality=3,
    )

    # (18) ∃ r. Nominal s.t. Nominal ∈ Nominals and r ∈ R* .
    exist_nominals = concept_reducer_properties(
        concepts=nominal_combinations,
        properties=object_properties_and_inverse,
        cls=OWLObjectSomeValuesFrom,
    )

    ###################################################################
    # Retrieval Results

    def concept_retrieval(retriever_func, c) -> Tuple[Set[str], float]:
        start_time = time.time()
        return {i.str for i in retriever_func.instances(c)}, time.time() - start_time

    # Combine all concepts
    concepts = list(
        itertools.chain(
            nc,
            nnc,
            unions_nc_star,
            intersections_nc_star,
            exist_nc_star,
            for_all_nc_star,
            min_cardinality_nc_star_1,
            min_cardinality_nc_star_2,
            min_cardinality_nc_star_3,
            max_cardinality_nc_star_1,
            max_cardinality_nc_star_2,
            max_cardinality_nc_star_3,
            exist_nominals,
        )
    )
    random.shuffle(concepts)

    total_jaccard_similarity = 0
    total_f1_score = 0

    for expression in concepts:
        retrieval_y, _ = concept_retrieval(symbolic_kb, expression)
        retrieval_neural_y, _ = concept_retrieval(neural_owl_reasoner, expression)
        total_jaccard_similarity += jaccard_similarity(retrieval_y, retrieval_neural_y)
        total_f1_score += f1_set_similarity(retrieval_y, retrieval_neural_y)

    mean_jaccard_similarity = total_jaccard_similarity / len(concepts)
    assert mean_jaccard_similarity >= min_jaccard_similarity, \
        f"Mean Jaccard Similarity {mean_jaccard_similarity} is less than the threshold {min_jaccard_similarity}"

    mean_f1_score = total_f1_score / len(concepts)
    assert mean_f1_score >= min_f1_score, \
        f"Mean F1 Score {mean_f1_score} is less than the threshold {min_f1_score}"


