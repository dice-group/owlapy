"""Test script for Embedding Based Reasoner (EBR) retrieval evaluation.

This test is based on the retrieval_eval.py script and evaluates the performance
of the EBR against the symbolic reasoner on various OWL class expressions.
It trains a model on KGs/Family/father.owl and asserts perfect scores.
"""

import pytest
import os
import random
import itertools
import time
from typing import Tuple, Set
from itertools import chain

from owlapy.owl_reasoner import StructuralReasoner, EBR
from owlapy.owl_ontology import Ontology, NeuralOntology
from owlapy.class_expression import (
    OWLObjectUnionOf,
    OWLObjectIntersectionOf,
    OWLObjectSomeValuesFrom,
    OWLObjectAllValuesFrom,
    OWLObjectMinCardinality,
    OWLObjectMaxCardinality,
    OWLObjectOneOf,
)


class TestEmbeddingBasedReasonerRetrieval:
    """Test class for EBR retrieval performance evaluation."""
    
    @classmethod
    def setup_class(cls):
        """Set up the test class with reasoners and ontology."""
        cls.path_kg = "KGs/Family/father.owl"
        cls.gamma = 0.9
        cls.seed = 42
        cls.num_nominals = 10  
        
        # Fix random seed for reproducibility
        random.seed(cls.seed)
        
        # Initialize symbolic reasoner
        assert os.path.isfile(cls.path_kg), f"Ontology file not found: {cls.path_kg}"
        ontology = Ontology(ontology_iri=cls.path_kg)
        cls.symbolic_kb = StructuralReasoner(ontology)
        
        # Initialize Neural OWL Reasoner (train if not exists)
        neural_ontology = NeuralOntology(
            path_neural_embedding=cls.path_kg, 
            train_if_not_exists=True,
            gamma=cls.gamma,
            batch_size=2,
            device="cpu"
        )
        cls.neural_owl_reasoner = EBR(ontology=neural_ontology)
        
        # Generate test concepts
        cls._generate_test_concepts()
    
    @classmethod
    def _generate_test_concepts(cls):
        """Generate various OWL class expressions for testing."""
        # Extract object properties
        object_properties = set(cls.symbolic_kb.get_root_ontology().object_properties_in_signature())
        
        # Inverse object properties
        object_properties_inverse = {prop.get_inverse_property() for prop in object_properties}
        
        # R*: R UNION R⁻
        cls.object_properties_and_inverse = object_properties.union(object_properties_inverse)
        
        # Named concepts (NC)
        cls.nc = set(cls.symbolic_kb.get_root_ontology().classes_in_signature())
        
        # Negated named concepts (NC⁻)
        cls.nnc = {concept.get_object_complement_of() for concept in cls.nc}
        
        # NC*: NC UNION NC⁻
        cls.nc_star = cls.nc.union(cls.nnc)
        
        # Generate nominals
        individuals = list(cls.symbolic_kb.get_root_ontology().individuals_in_signature())
        if len(individuals) > cls.num_nominals:
            nominals = set(random.sample(individuals, cls.num_nominals))
        else:
            nominals = set(individuals)
        
        # Nominal combinations (3-tuples)
        cls.nominal_combinations = set(
            OWLObjectOneOf(combination) 
            for combination in itertools.combinations(nominals, min(3, len(nominals)))
        )
        
        # Generate concept combinations
        cls.unions_nc = cls._concept_reducer(cls.nc, OWLObjectUnionOf)
        cls.intersections_nc = cls._concept_reducer(cls.nc, OWLObjectIntersectionOf)
        cls.unions_nc_star = cls._concept_reducer(cls.nc_star, OWLObjectUnionOf)
        cls.intersections_nc_star = cls._concept_reducer(cls.nc_star, OWLObjectIntersectionOf)
        
        # Existential and universal restrictions
        cls.exist_nc_star = cls._concept_reducer_properties(
            cls.nc_star, cls.object_properties_and_inverse, OWLObjectSomeValuesFrom
        )
        cls.for_all_nc_star = cls._concept_reducer_properties(
            cls.nc_star, cls.object_properties_and_inverse, OWLObjectAllValuesFrom
        )
        
        # Cardinality restrictions
        cls.min_cardinality_nc_star = cls._concept_reducer_properties(
            cls.nc_star, cls.object_properties_and_inverse, OWLObjectMinCardinality, cardinality=1
        )
        cls.max_cardinality_nc_star = cls._concept_reducer_properties(
            cls.nc_star, cls.object_properties_and_inverse, OWLObjectMaxCardinality, cardinality=1
        )
        
        # Existential restrictions with nominals
        cls.exist_nominals = cls._concept_reducer_properties(
            cls.nominal_combinations, cls.object_properties_and_inverse, OWLObjectSomeValuesFrom
        )
    
    @staticmethod
    def _concept_reducer(concepts, operator_class):
        """Create all binary combinations of concepts with the given operator."""
        return {
            operator_class(operands=frozenset([c1, c2])) 
            for c1 in concepts for c2 in concepts if c1 != c2
        }
    
    @staticmethod
    def _concept_reducer_properties(concepts, properties, restriction_class, cardinality=None):
        """Create combinations of concepts with properties using the given restriction class."""
        if cardinality is not None:
            return {
                restriction_class(filler=c, property=p, cardinality=cardinality) 
                for c in concepts for p in properties
            }
        else:
            return {
                restriction_class(filler=c, property=p) 
                for c in concepts for p in properties
            }
    
    @staticmethod
    def _jaccard_similarity(set1: Set, set2: Set) -> float:
        """Calculate Jaccard similarity between two sets."""
        if len(set1) == 0 and len(set2) == 0:
            return 1.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def _f1_set_similarity(set1: Set, set2: Set) -> float:
        """Calculate F1 score between two sets."""
        if len(set1) == 0 and len(set2) == 0:
            return 1.0
        
        if len(set2) == 0:
            return 0.0
        
        true_positives = len(set1.intersection(set2))
        precision = true_positives / len(set2) if len(set2) > 0 else 0
        recall = true_positives / len(set1) if len(set1) > 0 else 0
        
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)
    
    def _concept_retrieval(self, retriever, concept) -> Tuple[Set[str], float]:
        """Perform concept retrieval and measure runtime."""
        start_time = time.time()
        instances = {individual.str for individual in retriever.instances(concept)}
        runtime = time.time() - start_time
        return instances, runtime
    
    def _test_concept_group(self, concepts, group_name):
        """Test a group of concepts and assert perfect scores."""
        if not concepts:
            pytest.skip(f"No {group_name} concepts to test")
        
        for concept in concepts:
            # Get symbolic retrieval results
            symbolic_results, symbolic_time = self._concept_retrieval(self.symbolic_kb, concept)
            
            # Get neural retrieval results
            neural_results, neural_time = self._concept_retrieval(self.neural_owl_reasoner, concept)
            
            # Calculate similarities
            jaccard_sim = self._jaccard_similarity(symbolic_results, neural_results)
            f1_sim = self._f1_set_similarity(symbolic_results, neural_results)
            
            # Assert perfect scores
            assert jaccard_sim == 1.0, (
                f"Jaccard similarity for {group_name} concept {concept} is {jaccard_sim}, "
                f"expected 1.0. Symbolic: {symbolic_results}, Neural: {neural_results}"
            )
            assert f1_sim == 1.0, (
                f"F1 score for {group_name} concept {concept} is {f1_sim}, "
                f"expected 1.0. Symbolic: {symbolic_results}, Neural: {neural_results}"
            )
    
    def test_named_concepts(self):
        """Test retrieval performance on named concepts."""
        self._test_concept_group(self.nc, "named concepts")
    
    def test_negated_named_concepts(self):
        """Test retrieval performance on negated named concepts."""
        self._test_concept_group(self.nnc, "negated named concepts")
    
    def test_union_concepts(self):
        """Test retrieval performance on union concepts."""
        self._test_concept_group(self.unions_nc_star, "union concepts")
    
    def test_intersection_concepts(self):
        """Test retrieval performance on intersection concepts."""
        self._test_concept_group(self.intersections_nc_star, "intersection concepts")
    
    def test_existential_restrictions(self):
        """Test retrieval performance on existential restrictions."""
        self._test_concept_group(self.exist_nc_star, "existential restrictions")
    
    def test_universal_restrictions(self):
        """Test retrieval performance on universal restrictions."""
        self._test_concept_group(self.for_all_nc_star, "universal restrictions")
    
    def test_min_cardinality_restrictions(self):
        """Test retrieval performance on minimum cardinality restrictions."""
        self._test_concept_group(self.min_cardinality_nc_star, "minimum cardinality restrictions")
    
    def test_max_cardinality_restrictions(self):
        """Test retrieval performance on maximum cardinality restrictions."""
        self._test_concept_group(self.max_cardinality_nc_star, "maximum cardinality restrictions")
    
    def test_existential_with_nominals(self):
        """Test retrieval performance on existential restrictions with nominals."""
        self._test_concept_group(self.exist_nominals, "existential restrictions with nominals")
    
    def test_overall_performance(self):
        """Test overall performance across all concept types."""
        # Collect all concepts
        all_concepts = list(chain(
            self.nc,
            self.nnc,
            self.unions_nc_star,
            self.intersections_nc_star,
            self.exist_nc_star,
            self.for_all_nc_star,
            self.min_cardinality_nc_star,
            self.max_cardinality_nc_star,
            self.exist_nominals
        ))
        
        total_jaccard = 0.0
        total_f1 = 0.0
        count = 0
        
        for concept in all_concepts:
            # Get retrieval results
            symbolic_results, _ = self._concept_retrieval(self.symbolic_kb, concept)
            neural_results, _ = self._concept_retrieval(self.neural_owl_reasoner, concept)
            
            # Calculate similarities
            jaccard_sim = self._jaccard_similarity(symbolic_results, neural_results)
            f1_sim = self._f1_set_similarity(symbolic_results, neural_results)
            
            total_jaccard += jaccard_sim
            total_f1 += f1_sim
            count += 1
        
        # Calculate averages
        avg_jaccard = total_jaccard / count if count > 0 else 0.0
        avg_f1 = total_f1 / count if count > 0 else 0.0
        
        # Assert perfect average scores
        assert avg_jaccard == 1.0, f"Average Jaccard similarity is {avg_jaccard}, expected 1.0"
        assert avg_f1 == 1.0, f"Average F1 score is {avg_f1}, expected 1.0"
        
        print(f"\nOverall Performance Summary:")
        print(f"Tested {count} concepts")
        print(f"Average Jaccard Similarity: {avg_jaccard:.4f}")
        print(f"Average F1 Score: {avg_f1:.4f}")