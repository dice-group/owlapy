from owlapy.owl_property import (
    OWLDataProperty,
    OWLObjectInverseOf,
    OWLObjectProperty,
    OWLProperty,
)
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
from owlapy.class_expression import OWLClass, OWLClassExpression, OWLObjectComplementOf, OWLObjectIntersectionOf, OWLObjectAllValuesFrom, OWLObjectSomeValuesFrom, OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectUnionOf, OWLObjectOneOf
from typing import Generator, Tuple, List, Set
from dicee.knowledge_graph_embeddings import KGE
import os
import re
from collections import Counter, OrderedDict
from functools import lru_cache
from owlapy.owl_neural_reasoners.abstract import AbstractNeuralReasoner

# TODO:
def is_valid_entity(text_input: str):
    return True if "/" in text_input else False

class OWLNeuralReasoner(AbstractNeuralReasoner):
    """ OWL Neural Reasoner uses a neural link predictor to retrieve instances of an OWL Class Expression"""
    def __init__(self, path_of_kb: str = None, path_neural_embedding: str = None, gamma: float = 0.25, max_cache_size: int = 2**20):
        assert gamma is None or 0 <= gamma <= 1, "Confidence threshold (gamma) must be in the range [0, 1]."
        self.gamma = gamma
        self._prediction_cache = OrderedDict()
        self._max_cache_size = max_cache_size
        self.str_iri_subclassof="http://www.w3.org/2000/01/rdf-schema#subClassOf"
        self.str_iri_type="http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
        self.str_iri_owl_class = "http://www.w3.org/2002/07/owl#Class"
        self.str_iri_object_property="http://www.w3.org/2002/07/owl#ObjectProperty"
        self.str_iri_range="http://www.w3.org/2000/01/rdf-schema#range"
        self.str_iri_double = "http://www.w3.org/2001/XMLSchema#double"
        self.str_iri_boolean = "http://www.w3.org/2001/XMLSchema#boolean"
        self.str_iri_data_property="http://www.w3.org/2002/07/owl#DatatypeProperty"

        if isinstance(max_cache_size,int) and max_cache_size>0:
           self.predict=lru_cache(maxsize=max_cache_size)(self.predict)

        if path_neural_embedding:  # pragma: no cover
            assert os.path.isdir(
                path_neural_embedding), f"The given path ({path_neural_embedding}) does not lead to a directory"
            self.model = KGE(path=path_neural_embedding)
        elif path_of_kb:
            assert os.path.isfile(path_of_kb), f"The given path ({path_of_kb}) does not lead to an RDF Knowledge Graph."
            # Check we have already a trained model for a given path of a knowledge base
            dir_of_potential_neural_embedding_model = path_of_kb.replace("/", "_").replace(".", "_")
            if os.path.isdir(dir_of_potential_neural_embedding_model):
                self.model = KGE(path=dir_of_potential_neural_embedding_model)
            else:  # pragma: no cover
                # Train a KGE on the fly
                from dicee.executer import Execute
                from dicee.config import Namespace
                args = Namespace()
                args.model = 'Keci'
                args.scoring_technique = "AllvsAll"
                args.path_single_kg = path_of_kb
                path_of_kb = path_of_kb.replace("/", "_")
                path_of_kb = path_of_kb.replace(".", "_")
                args.path_to_store_single_run = path_of_kb
                args.num_epochs = 100
                args.embedding_dim = 512
                args.batch_size = 1024
                args.backend = "rdflib"
                args.trainer = "PL"
                # args.save_embeddings_as_csv = "True"
                reports = Execute(args).start()
                path_neural_embedding = reports["path_experiment_folder"]
                self.model = KGE(path=path_neural_embedding)
        else:
            raise RuntimeError(
                f"path_neural_embedding {path_neural_embedding} and path_of_kb {path_of_kb} cannot be both None")

        self.inferred_object_properties = None
        self.inferred_named_owl_classes = None

    def __str__(self):
        return f"TripleStoreNeuralReasoner:{self.model} with likelihood threshold gamma : {self.gamma}"

    @property
    def set_inferred_object_properties(self):  # pragma: no cover
        return {i for i in self.object_properties_in_signature()} if self.inferred_object_properties is None else self.inferred_object_properties

    @property
    def set_inferred_owl_classes(self):  # pragma: no cover
        return {i for i in self.classes_in_signature()} if self.inferred_named_owl_classes is None else self.inferred_named_owl_classes

    def predict(self, h: str = None, r: str = None, t: str = None) -> List[Tuple[str,float]]:
        # sanity check
        assert h is not None or r is not None or t is not None, "At least one of h, r, or t must be provided."
        assert h is None or isinstance(h, str), "Head entity must be a string."
        assert r is None or isinstance(r, str), "Relation must be a string."
        assert t is None or isinstance(t, str), "Tail entity must be a string."

        if h is not None:
            if h not in self.model.entity_to_idx:
                # raise KeyError(f"Head entity '{h}' not found in model entity indices.")
                return []
            h = [h]

        if r is not None:
            if r not in self.model.relation_to_idx:
                #raise KeyError(f"Relation '{r}' not found in model relation indices.")
                return []
            r = [r]

        if t is not None:
            if t not in self.model.entity_to_idx:
                # raise KeyError(f"Tail entity '{t}' not found in model entity indices.")
                return []
            t = [t]

        if r is None:
            topk = len(self.model.relation_to_idx)
        else:
            topk = len(self.model.entity_to_idx)


        return [ (top_entity, score)  for top_entity, score in self.model.predict_topk(h=h, r=r, t=t, topk=topk) if score >= self.gamma and is_valid_entity(top_entity)]

    def predict_individuals_of_owl_class(self, owl_class: OWLClass) -> List[OWLNamedIndividual]:
        top_entities=set()
        # Find all subconcepts
        owl_classes = [owl_class] + self.subconcepts(owl_class)
        c:OWLClass
        for c in owl_classes:
            assert isinstance(c, OWLClass)
            top_entity:str
            for top_entity, _ in self.predict(h=None,
                                                  r=self.str_iri_type,
                                                  t=c.iri.str):
                top_entities.add(top_entity)
        return [OWLNamedIndividual(i) for i in top_entities]

    def abox(self, str_iri: str) -> Generator[
        Tuple[
            Tuple[OWLNamedIndividual, OWLProperty, OWLClass],
            Tuple[OWLObjectProperty, OWLObjectProperty, OWLNamedIndividual],
            Tuple[OWLObjectProperty, OWLDataProperty, OWLLiteral]], None,None ]:
        # Initialize an owl named individual object.
        subject_ = OWLNamedIndividual(str_iri)
        # Return a triple indicating the type.
        for cl in self.get_type_individuals(str_iri):
            yield subject_,OWLProperty("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), cl

        # Return a triple based on an object property.
        for op in self.object_properties_in_signature():
            for o in self.get_object_property_values(str_iri, op):
                yield subject_, op, o

        # Return a triple based on a data property. TODO: LF: fix if support for data properties is added.
        # for dp in self.data_properties_in_signature():  # pragma: no cover
        #     print("these data properties are in the signature: ", dp.str)
        #     for l in self.get_data_property_values(str_iri, dp):
        #         yield subject_, dp, l

    def classes_in_signature(self) -> List[OWLClass]:
        return [OWLClass(top_entity) for top_entity, _ in self.predict(h=None,
                                                                   r=self.str_iri_type,
                                                                   t=self.str_iri_owl_class)]
    def direct_subconcepts(self, named_concept: OWLClass) -> List[OWLClass]:
        return [OWLClass(top_entity) for top_entity, _ in self.predict(h=None,
                                                                           r=self.str_iri_subclassof,
                                                                           t=named_concept.str)]

    def subconcepts(self, named_concept: OWLClass, visited=None) -> List[OWLClass]:
        if visited is None:
            visited = set()
        all_subconcepts = []
        for subconcept in self.direct_subconcepts(named_concept):
            if subconcept not in self.classes_in_signature() or subconcept in visited:
                continue  # Skip to the next subconcept
            visited.add(subconcept)
            all_subconcepts.append(subconcept)
            all_subconcepts.extend(self.subconcepts(subconcept, visited))
        return all_subconcepts
    
    def most_general_classes(self) -> List[OWLClass]:  # pragma: no cover
        """At least it has single subclass and there is no superclass"""
        owl_concepts_not_having_parents=set()
        for c in self.classes_in_signature():
            direct_parents=set()
            for x in self.get_direct_parents(c):
                # Ignore c if (c subclass x) \in KG.
                direct_parents.add(x)
                break
            if len(direct_parents) ==0:
                # c does not have any parents
                # Check whether it has at least one sub
                # checks if subconcepts is not empty -> there is at least one subclass
                # c should have at least a single subclass.
                for sub_c in self.subconcepts(named_concept=c):
                    owl_concepts_not_having_parents.add(sub_c)
                    break
        return [i for i in owl_concepts_not_having_parents]

    def least_general_named_concepts(self) -> Generator[OWLClass, None, None]:  # pragma: no cover
        """At least it has single superclass and there is no subclass"""
        for _class in self.classes_in_signature():
            for _ in self.subconcepts(
                    named_concept=_class
            ):
                break
            else:
                # checks if superclasses is not empty -> there is at least one superclass
                if list(
                        self.get_direct_parents(_class)
                ):
                    yield _class

    def get_direct_parents(self, named_concept: OWLClass)-> List[OWLClass] :  # pragma: no cover
        return [OWLClass(entity) for entity, _ in self.predict(h=named_concept.str, r=self.str_iri_subclassof,
                                                                   t=None)]

    def get_type_individuals(self, individual: str) -> List[OWLClass]:
        return [OWLClass(top_entity) for top_entity, _ in self.predict(h=individual, r=self.str_iri_type, t=None)]
    def individuals_in_signature(self) -> List[OWLNamedIndividual]:
        set_str_entities=set()
        for owl_class in self.classes_in_signature():
            for top_entity, _ in self.predict(h=None,
                                                  r=self.str_iri_type,
                                                  t=owl_class.iri.str):
                set_str_entities.add(top_entity)
        return [OWLNamedIndividual(entity) for entity in set_str_entities]

    def data_properties_in_signature(self) -> List[OWLDataProperty]:
        return [OWLDataProperty(top_entity) for top_entity, _ in self.predict(h=None,
                                                     r=self.str_iri_type,
                                                     t=self.str_iri_data_property)]

    def object_properties_in_signature(self) -> List[OWLObjectProperty]:
        return [OWLObjectProperty(top_entity) for top_entity, _ in self.predict(h=None,
                                                     r=self.str_iri_type,
                                                     t=self.str_iri_object_property)]

    def boolean_data_properties(self) -> Generator[OWLDataProperty, None, None]:  # pragma: no cover
        return [OWLDataProperty(top_entity) for top_entity, _  in self.predict(h=None, r=self.str_iri_range,
                                                                                  t=self.str_iri_boolean)]

    def double_data_properties(self) -> List[OWLDataProperty]:  # pragma: no cover
        return [OWLDataProperty(top_entity) for top_entity, _ in self.predict(
                h=None,
                r=self.str_iri_range,
                t=self.str_iri_double)]
    def individuals(self, expression: OWLClassExpression = None, named_individuals: bool = False) -> Generator[OWLNamedIndividual, None, None]:
        if expression is None or expression.is_owl_thing():
            yield from self.individuals_in_signature()
        else:
            yield from self.instances(expression)

    def instances(self, expression: OWLClassExpression, named_individuals=False) -> Generator[OWLNamedIndividual, None, None]:
        if isinstance(expression, OWLClass):
            """ Given an OWLClass A, retrieve its instances Retrieval(A)={ x | phi(x, type, A) ≥ γ } """
            yield from self.predict_individuals_of_owl_class(expression)
        elif isinstance(expression, OWLObjectComplementOf):
            """ Handling complement of class expressions:
            Given an OWLObjectComplementOf ¬A, hence (A is an OWLClass),
            retrieve its instances => Retrieval(¬A)= All Instance Set-DIFF { x | phi(x, type, A) ≥ γ } """
            excluded_individuals:Set[OWLNamedIndividual]
            excluded_individuals = set(self.instances(expression.get_operand()))
            all_individuals= {i for i in self.individuals_in_signature()}
            yield from all_individuals - excluded_individuals
        elif isinstance(expression, OWLObjectIntersectionOf):
            """ Handling intersection of class expressions:
            Given an OWLObjectIntersectionOf (C ⊓ D),  
            retrieve its instances by intersecting the instance of each operands.
            {x | phi(x, type, C) ≥ γ} ∩ {x | phi(x, type, D) ≥ γ}
            """
            # Get the class expressions
            #
            result = None
            for op in expression.operands():
                retrieval_of_op = {_ for _ in self.instances(expression=op)}
                if result is None:
                    result = retrieval_of_op
                else:
                    result = result.intersection(retrieval_of_op)
            yield from result
        elif isinstance(expression, OWLObjectAllValuesFrom):
            """
            Given an OWLObjectAllValuesFrom ∀ r.C, retrieve its instances => 
            Retrieval(¬∃ r.¬C) =             
            Entities \setminus {x | ∃ y: \phi(y, type, C) < \gamma AND \phi(x,r,y)  ≥ \gamma } 
            """
            object_property = expression.get_property()
            filler_expression = expression.get_filler()
            yield from self.instances(OWLObjectComplementOf(OWLObjectSomeValuesFrom(object_property, OWLObjectComplementOf(filler_expression))))
            
        elif isinstance(expression, OWLObjectMinCardinality) or isinstance(expression, OWLObjectSomeValuesFrom):
            """
            Given an OWLObjectSomeValuesFrom ∃ r.C, retrieve its instances => 
            Retrieval(∃ r.C) = 
            {x | ∃ y : phi(y, type, C) ≥ \gamma AND phi(x, r, y) ≥ \gamma }  
            """
            object_property = expression.get_property()
            filler_expression = expression.get_filler()
            cardinality = 1
            if isinstance(expression, OWLObjectMinCardinality):
                cardinality = expression.get_cardinality()

            object_individuals = self.instances(filler_expression)

            # Initialize counter to keep track of individual occurrences
            result = Counter()

            # Iterate over each object individual to find and count subjects
            for object_individual in object_individuals:
                subjects = self.get_individuals_with_object_property(
                    obj=object_individual,
                    object_property=object_property)
                # Update the counter for all subjects found
                result.update(subjects)

            # Yield only those individuals who meet the cardinality requirement
            for individual, count in result.items():
                if count >= cardinality:
                    yield individual
        elif isinstance(expression, OWLObjectMaxCardinality):
            object_property: OWLObjectProperty
            object_property = expression.get_property()

            filler_expression:OWLClassExpression
            filler_expression = expression.get_filler()

            cardinality:int
            cardinality = expression.get_cardinality()

            # Get all individuals that are instances of the filler expression.
            object_individuals = { owl_individual for owl_individual
                                   in self.instances(filler_expression)}

            # Initialize a dictionary to keep track of counts of related individuals for each entity.
            str_subject_individuals_to_count = {owl_individual.str: (owl_individual,0) for owl_individual in self.individuals_in_signature()}

            for object_individual in object_individuals:
                # Get all individuals related to the object individual via the object property.
                subject_individuals = self.get_individuals_with_object_property(obj=object_individual,
                                                              object_property=object_property)

                # Update the count of related individuals for each object individual.
                for subject_individual in subject_individuals:
                    if subject_individual.str in str_subject_individuals_to_count:
                        owl_obj, count = str_subject_individuals_to_count[subject_individual.str]
                        # Increment the count.
                        str_subject_individuals_to_count[subject_individual.str] = (owl_obj, count+1)

            # Filter out individuals who exceed the specified cardinality.
            yield from  {ind for _, (ind, count) in str_subject_individuals_to_count.items() if count <= cardinality}

        # Handling union of class expressions
        elif isinstance(expression, OWLObjectUnionOf):
            # Get the class expressions

            result = None
            for op in expression.operands():
                retrieval_of_op = {_ for _ in self.instances(expression=op)}
                if result is None:
                    result = retrieval_of_op
                else:
                    result = result.union(retrieval_of_op)
            yield from result

        elif isinstance(expression, OWLObjectOneOf):
            yield from expression.individuals()
        else:
            raise NotImplementedError(f"Instances for {type(expression)} are not implemented yet")


    ### additional functions for neural reasoner

    def get_object_property_values(
            self, subject: str, object_property: OWLObjectProperty=None) -> List[OWLNamedIndividual]:
        assert isinstance(object_property, OWLObjectProperty) or isinstance(object_property, OWLObjectInverseOf)
        if is_inverse := isinstance(object_property, OWLObjectInverseOf):
            object_property = object_property.get_inverse()
        return [OWLNamedIndividual(top_entity) for top_entity, _ in self.predict(
                h=None if is_inverse else subject,
                r=object_property.iri.str,
                t=subject if is_inverse else None)]

    def get_data_property_values(self, subject: str, data_property: OWLDataProperty) -> Generator[OWLLiteral, None, None]:  # pragma: no cover
        for prediction in self.predict(
                h=subject,
                r=data_property.str,
                t=None):
            try:
                # TODO: check the datatype and convert it to the correct type
                # like in abox triplestore line 773ff

                # Extract the value from the IRI
                value = re.search(r"\"(.+?)\"", prediction[0]).group(1)
                owl_literal = OWLLiteral(value)
                yield owl_literal
            except Exception as e:
                # Log the invalid IRI
                print(f"Invalid IRI detected: {prediction[0]}, error: {e}")
                continue

    def get_individuals_with_object_property(
            self,
            object_property: OWLObjectProperty, obj: OWLClass) \
            -> Generator[OWLNamedIndividual, None, None]:
        is_inverse = isinstance(object_property, OWLObjectInverseOf)

        if is_inverse:
            object_property = object_property.get_inverse()

        for entity, _ in self.predict(
                h=obj.str if is_inverse else None,
                r=object_property.str,
                t=None if is_inverse else obj.str):

            try:
                yield OWLNamedIndividual(entity)
            except Exception as e:  # pragma: no cover
                # Log the invalid IRI
                print(f"Invalid IRI detected: {entity}, error: {e}")
                continue
