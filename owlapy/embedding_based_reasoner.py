"""Embedding-based reasoner"""

from collections import Counter
from functools import cached_property
from typing import Generator, Iterable, List, Set, Tuple

from owlapy.class_expression import OWLThing
from owlapy.class_expression.class_expression import OWLClassExpression, OWLObjectComplementOf
from owlapy.class_expression.nary_boolean_expression import OWLObjectIntersectionOf, OWLObjectUnionOf
from owlapy.class_expression.owl_class import OWLClass
from owlapy.class_expression.restriction import OWLObjectAllValuesFrom, OWLObjectMaxCardinality, OWLObjectMinCardinality, OWLObjectOneOf, OWLObjectSomeValuesFrom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_object import OWLEntity
from owlapy.owl_property import OWLDataProperty, OWLObjectInverseOf, OWLObjectProperty, OWLObjectPropertyExpression, OWLProperty
from owlapy.owl_reasoner import AbstractOWLReasoner
from owlapy.neural_ontology import NeuralOntology

class EBR(AbstractOWLReasoner):
    """The Embedding-Based Reasoner uses neural embeddings to retrieve concept instances from knowledge bases. """

    STR_IRI_SUBCLASSOF = "http://www.w3.org/2000/01/rdf-schema#subClassOf"
    STR_IRI_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
    STR_IRI_OWL_CLASS = "http://www.w3.org/2002/07/owl#Class"
    STR_IRI_OBJECT_PROPERTY = "http://www.w3.org/2002/07/owl#ObjectProperty"
    STR_IRI_RANGE = "http://www.w3.org/2000/01/rdf-schema#range"
    STR_IRI_DOMAIN = "http://www.w3.org/2000/01/rdf-schema#domain"
    STR_IRI_DOUBLE = "http://www.w3.org/2001/XMLSchema#double"
    STR_IRI_BOOLEAN = "http://www.w3.org/2001/XMLSchema#boolean"
    STR_IRI_DATA_PROPERTY = "http://www.w3.org/2002/07/owl#DatatypeProperty"
    STR_IRI_SUBPROPERTY = "http://www.w3.org/2000/01/rdf-schema#subPropertyOf"

    def __init__(self, ontology: NeuralOntology):
        super().__init__(ontology)
        self.gamma = ontology.gamma
        self.ontology = ontology
        self.model = ontology.model

    def __str__(self):
        return f"Embedding-Based Reasoner using: {self.model.model} with gamma: {self.gamma}"
    
    @cached_property
    def inferred_object_properties(self) -> set:
        return set(self.object_properties_in_signature())

    @cached_property
    def inferred_owl_classes(self) -> set:
        return set(self.classes_in_signature())

    def predict(self, h: List[str] = None, r: List[str] = None, t: List[str] = None) -> List[Tuple[str,float]]:
        return self.ontology.predict(h=h, r=r, t=t)

    def predict_individuals_of_owl_class(self, owl_class: OWLClass) -> List[OWLNamedIndividual]:
            top_entities=set()
            # Find all subconcepts
            owl_classes = [owl_class] + self.sub_classes(owl_class)
            top_entity:str
            for top_entity, score in self.predict(h=None,
                                                    r=self.STR_IRI_TYPE,
                                                    t=[c.iri.str for c in owl_classes]):
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
        for cl in self.types(subject_):
            yield subject_, OWLProperty(self.STR_IRI_TYPE), cl

        # Return a triple based on an object property.
        for op in self.object_properties_in_signature():
            for o in self.object_property_values(subject_, op):
                yield subject_, op, o
        #TODO: Data properties

    def classes_in_signature(self) -> List[OWLClass]:
        return self.ontology.classes_in_signature()

    def individuals_in_signature(self) -> List[OWLNamedIndividual]:
        return self.ontology.individuals_in_signature()

    def data_properties_in_signature(self) -> List[OWLDataProperty]:
        return self.ontology.data_properties_in_signature()

    def object_properties_in_signature(self) -> List[OWLObjectProperty]:
        return self.ontology.object_properties_in_signature()

    def direct_subconcepts(self, named_concept: OWLClass) -> List[OWLClass]:
        if self.STR_IRI_SUBCLASSOF not in self.model.relation_to_idx:
                return []
        return [OWLClass(top_entity) for top_entity, score in self.predict(h=None,
                                                                           r=self.STR_IRI_SUBCLASSOF,
                                                                           t=named_concept.str)]

    def sub_classes(self, named_concept: OWLClass, visited=None) -> List[OWLClass]:
        if visited is None:
            visited = set()
        all_subconcepts = []
        for subconcept in self.direct_subconcepts(named_concept):
            if subconcept not in self.classes_in_signature() or subconcept in visited:
                continue  
            visited.add(subconcept)
            all_subconcepts.append(subconcept)
            all_subconcepts.extend(self.sub_classes(subconcept, visited))
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
                for sub_c in self.sub_classes(named_concept=c):
                    owl_concepts_not_having_parents.add(sub_c)
                    break
        return [i for i in owl_concepts_not_having_parents]

    def least_general_named_concepts(self) -> Generator[OWLClass, None, None]:  # pragma: no cover
        """At least it has single superclass and there is no subclass"""
        for _class in self.classes_in_signature():
            for concept in self.sub_classes(
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
        return [OWLClass(entity) for entity, score in self.predict(h=named_concept.str, r=self.STR_IRI_SUBCLASSOF,
                                                                   t=None)]

    def super_classes(self, ce: OWLClassExpression, direct: bool = False) -> Iterable[OWLClassExpression]:
        if not isinstance(ce, OWLClass):
            raise NotImplementedError("Only named classes are supported in the embedding-based reasoner")
        
        if direct:
            return self.get_direct_parents(ce)
        else:
            visited = set()
            all_superclasses = []
            
            def collect_superclasses(concept):
                for parent in self.get_direct_parents(concept):
                    if parent not in visited:
                        visited.add(parent)
                        all_superclasses.append(parent)
                        collect_superclasses(parent)
            
            collect_superclasses(ce)
            return all_superclasses

    def types(self, individual: OWLNamedIndividual) -> List[OWLClass]:
        return [OWLClass(top_entity) for top_entity,score in self.predict(h=individual.str, r=self.STR_IRI_TYPE, t=None)]

    def boolean_data_properties(self) -> Generator[OWLDataProperty, None, None]:  # pragma: no cover
        return [OWLDataProperty(top_entity) for top_entity,score  in self.predict(h=None, r=self.STR_IRI_RANGE,
                                                                                  t=self.STR_IRI_BOOLEAN)]

    def double_data_properties(self) -> List[OWLDataProperty]:  # pragma: no cover
        return [OWLDataProperty(top_entity) for top_entity, score in self.predict(
                h=None,
                r=self.STR_IRI_RANGE,
                t=self.STR_IRI_DOUBLE)]
    def individuals(self, expression: OWLClassExpression = None, named_individuals: bool = False) -> Generator[OWLNamedIndividual, None, None]:
        if expression is None or expression.is_owl_thing():
            yield from self.individuals_in_signature()
        else:
            yield from self.instances(expression)

    def instances(self, expression: OWLClassExpression, direct: bool = False, timeout: int = 1000) -> Generator[OWLNamedIndividual, None, None]:
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
            result = Counter()
            subjects = self.get_individuals_with_object_property(
                objs=object_individuals,
                object_property=object_property)
            # Update the counter for all subjects found
            result.update(subjects)
            # Yield only those individuals who meet the cardinality requirement
            for individual, count in result.items():
                if count >= cardinality:
                    yield individual
        elif isinstance(expression, OWLObjectMaxCardinality):
            object_property = expression.get_property()
            filler_expression = expression.get_filler()
            cardinality = expression.get_cardinality()

            # Get all individuals that are instances of the filler expression.
            object_individuals = list(self.instances(filler_expression))

            # Initialize counts for every subject in the signature.
            counts = {ind.str: (ind, 0) for ind in self.individuals_in_signature()}

            # Retrieve all subjects related to any of the object individuals at once.
            subject_individuals = self.get_individuals_with_object_property(
                objs=object_individuals,
                object_property=object_property
            )

            # Increment counts for each related subject.
            for subj in subject_individuals:
                if subj.str in counts:
                    owl_obj, cnt = counts[subj.str]
                    counts[subj.str] = (owl_obj, cnt + 1)

            # Yield only those subjects whose count does not exceed the max cardinality.
            yield from {
                ind for _, (ind, cnt) in counts.items()
                if cnt <= cardinality
            }
        

        elif isinstance(expression, OWLObjectUnionOf):
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

    def object_property_values(
            self, subject: OWLNamedIndividual, object_property: OWLObjectProperty=None) -> List[OWLNamedIndividual]:
        assert isinstance(object_property, OWLObjectProperty) or isinstance(object_property, OWLObjectInverseOf)
        if is_inverse := isinstance(object_property, OWLObjectInverseOf):
            object_property = object_property.get_inverse()
        return [OWLNamedIndividual(top_entity) for top_entity, score in self.predict(
                h=None if is_inverse else subject.str,
                r=object_property.iri.str,
                t=subject.str if is_inverse else None)]

    def get_individuals_with_object_property(
            self,
            object_property: OWLObjectProperty, objs: List[OWLClass]) \
            -> Generator[OWLNamedIndividual, None, None]:
        is_inverse = isinstance(object_property, OWLObjectInverseOf)

        if is_inverse:
            object_property = object_property.get_inverse()
        return_subjects = list()
        for entity, score in self.predict(
                h=[obj.str for obj in objs] if is_inverse else None,
                r=object_property.str,
                t=None if is_inverse else [obj.str for obj in objs]):
            try:
                return_subjects.append(OWLNamedIndividual(entity))
            except Exception as e:  # pragma: no cover
                # Log the invalid IRI
                print(f"Invalid IRI detected: {entity}, error: {e}")
                continue

        return return_subjects

    
    def data_property_domains(self, pe: OWLDataProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        """Gets the class expressions that are the direct or indirect domains of this property with respect to the imports closure of the root ontology.

        Args:
            pe: The property expression whose domains are to be retrieved.
            direct: Specifies if the direct domains should be retrieved (True), or if all domains should be retrieved (False).

        Returns:
            The class expressions that are the domains of the specified property.
        """
        # Get all classes that are domains of this property
        domain_classes = [OWLClass(top_entity) for top_entity, score in self.predict(
            h=pe.str, 
            r=self.STR_IRI_DOMAIN,
            t=None
        )]
        
        if direct:
            # If only direct domains are requested, return them as is
            yield from domain_classes
        else:
            # If all domains are requested, also include all superclasses of each domain
            all_domains = set(domain_classes)
            for cls in domain_classes:
                all_domains.update(self.super_classes(cls))
            yield from all_domains
            
            # If no domain is found, yield OWLThing as the default domain
            if not all_domains:
                yield OWLThing

    def object_property_domains(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        # Check if the property is inverse
        is_inverse = isinstance(pe, OWLObjectInverseOf)
        if is_inverse:
            # For inverse properties, the domains are the ranges of the original property
            original_property = pe.get_inverse()
            yield from self.object_property_ranges(original_property, direct)
        else:
            # Get all classes that are domains of this property
            domain_classes = [OWLClass(top_entity) for top_entity, score in self.predict(
                h=pe.str, 
                r=self.STR_IRI_DOMAIN,
                t=None
            )]
            
            if direct:
                # If only direct domains are requested, return them as is
                yield from domain_classes
            else:
                # If all domains are requested, also include all superclasses of each domain
                all_domains = set(domain_classes)
                for cls in domain_classes:
                    all_domains.update(self.super_classes(cls))
                yield from all_domains
                
                # If no domain is found, yield OWLThing as the default domain
                if not all_domains:
                    yield OWLThing

    def object_property_ranges(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        # Check if the property is inverse
        is_inverse = isinstance(pe, OWLObjectInverseOf)
        if is_inverse:
            pe = pe.get_inverse()
            # For inverse properties, the ranges are the domains of the original property
            if direct:
                yield from [OWLClass(top_entity) for top_entity, score in self.predict(
                    h=pe.str, 
                    r=self.STR_IRI_DOMAIN,
                    t=None
                )]
            else:
                # Get all domains and their superclasses
                domain_classes = [OWLClass(top_entity) for top_entity, score in self.predict(
                    h=pe.str, 
                    r=self.STR_IRI_DOMAIN,
                    t=None
                )]
                all_domains = set(domain_classes)
                for cls in domain_classes:
                    all_domains.update(self.super_classes(cls))
                yield from all_domains
                
                # If no range is found, yield OWLThing as the default range
                if not all_domains:
                    yield OWLThing
        else:
            # For regular properties, get ranges directly
            range_classes = [OWLClass(top_entity) for top_entity, score in self.predict(
                h=pe.str, 
                r=self.STR_IRI_RANGE,
                t=None
            )]
            
            if direct:
                # If only direct ranges are requested, return them as is
                yield from range_classes
            else:
                # If all ranges are requested, also include all superclasses of each range
                all_ranges = set(range_classes)
                for cls in range_classes:
                    all_ranges.update(self.super_classes(cls))
                yield from all_ranges
                
                # If no range is found, yield OWLThing as the default range
                if not all_ranges:
                    yield OWLThing

    def equivalent_classes(self, ce: OWLClassExpression) -> Iterable[OWLClassExpression]:
        raise NotImplementedError("Equivalent classes are not implemented for the embedding-based reasoner")
    
    def disjoint_classes(self, ce: OWLClassExpression) -> Iterable[OWLClassExpression]:
        raise NotImplementedError("Disjoint classes are not implemented for the embedding-based reasoner")
    
    def different_individuals(self, ind: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        raise NotImplementedError("Different individuals are not implemented for the embedding-based reasoner")
    
    def same_individuals(self, ind: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        raise NotImplementedError("Same individuals are not implemented for the embedding-based reasoner")
    
    def equivalent_object_properties(self, op: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        raise NotImplementedError("Equivalent object properties are not implemented for the embedding-based reasoner")
    
    def equivalent_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        raise NotImplementedError("Equivalent data properties are not implemented for the embedding-based reasoner")
    
    def data_property_values(self, e: OWLEntity, pe: OWLDataProperty) -> Iterable['OWLLiteral']:
        raise NotImplementedError("Data property values are not implemented for the embedding-based reasoner")
    
    def disjoint_object_properties(self, op: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        raise NotImplementedError("Disjoint object properties are not implemented for the embedding-based reasoner")
    
    def disjoint_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        raise NotImplementedError("Disjoint data properties are not implemented for the embedding-based reasoner")
    
    def sub_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        # Get direct sub properties
        sub_properties = [OWLDataProperty(top_entity) for top_entity, score in self.predict(
            h=None,
            r=self.STR_IRI_SUBPROPERTY,
            t=dp.str
        )]
        
        if direct:
            # If only direct sub properties are requested, return them as is
            yield from sub_properties
        else:
            # If all sub properties are requested, also include all sub properties of each sub property
            visited = set()
            all_sub_properties = []
            
            def collect_sub_properties(property_):
                for sub_prop in [OWLDataProperty(top_entity) for top_entity, score in self.predict(
                        h=None,
                        r=self.STR_IRI_SUBPROPERTY,
                        t=property_.str
                    )]:
                    if sub_prop not in visited:
                        visited.add(sub_prop)
                        all_sub_properties.append(sub_prop)
                        collect_sub_properties(sub_prop)
            
            for prop in sub_properties:
                visited.add(prop)
                all_sub_properties.append(prop)
                collect_sub_properties(prop)
                
            yield from all_sub_properties
    
    def super_data_properties(self, dp: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataProperty]:
        # Get direct super properties
        super_properties = [OWLDataProperty(top_entity) for top_entity, score in self.predict(
            h=dp.str,
            r=self.STR_IRI_SUBPROPERTY,
            t=None
        )]
        
        if direct:
            # If only direct super properties are requested, return them as is
            yield from super_properties
        else:
            # If all super properties are requested, also include all super properties of each super property
            visited = set()
            all_super_properties = []
            
            def collect_super_properties(property_):
                for super_prop in [OWLDataProperty(top_entity) for top_entity, score in self.predict(
                        h=property_.str,
                        r=self.STR_IRI_SUBPROPERTY,
                        t=None
                    )]:
                    if super_prop not in visited:
                        visited.add(super_prop)
                        all_super_properties.append(super_prop)
                        collect_super_properties(super_prop)
            
            for prop in super_properties:
                visited.add(prop)
                all_super_properties.append(prop)
                collect_super_properties(prop)
                
            yield from all_super_properties
    
    def sub_object_properties(self, op: OWLObjectPropertyExpression, direct: bool = False) -> Iterable[OWLObjectPropertyExpression]:
        # Check if the property is inverse
        is_inverse = isinstance(op, OWLObjectInverseOf)
        if is_inverse:
            # For inverse properties, the sub properties are the inverse of the super properties of the original property
            original_property = op.get_inverse()
            for super_prop in self.super_object_properties(original_property, direct):
                yield OWLObjectInverseOf(super_prop)
        else:
            # Get direct sub properties
            sub_properties = [OWLObjectProperty(top_entity) for top_entity, score in self.predict(
                h=None,
                r=self.STR_IRI_SUBPROPERTY,
                t=op.str
            )]
            
            if direct:
                # If only direct sub properties are requested, return them as is
                yield from sub_properties
            else:
                # If all sub properties are requested, also include all sub properties of each sub property
                visited = set()
                all_sub_properties = []
                
                def collect_sub_properties(property_):
                    for sub_prop in [OWLObjectProperty(top_entity) for top_entity, score in self.predict(
                            h=None,
                            r=self.STR_IRI_SUBPROPERTY,
                            t=property_.str
                        )]:
                        if sub_prop not in visited:
                            visited.add(sub_prop)
                            all_sub_properties.append(sub_prop)
                            collect_sub_properties(sub_prop)
                
                for prop in sub_properties:
                    visited.add(prop)
                    all_sub_properties.append(prop)
                    collect_sub_properties(prop)
                    
                yield from all_sub_properties
    
    def super_object_properties(self, op: OWLObjectPropertyExpression, direct: bool = False) -> Iterable[OWLObjectPropertyExpression]:
        # Check if the property is inverse
        is_inverse = isinstance(op, OWLObjectInverseOf)
        if is_inverse:
            # For inverse properties, the super properties are the inverse of the sub properties of the original property
            original_property = op.get_inverse()
            for sub_prop in self.sub_object_properties(original_property, direct):
                yield OWLObjectInverseOf(sub_prop)
        else:
            # Get direct super properties
            super_properties = [OWLObjectProperty(top_entity) for top_entity, score in self.predict(
                h=op.str,
                r=self.STR_IRI_SUBPROPERTY,
                t=None
            )]
            
            if direct:
                # If only direct super properties are requested, return them as is
                yield from super_properties
            else:
                # If all super properties are requested, also include all super properties of each super property
                visited = set()
                all_super_properties = []
                
                def collect_super_properties(property_):
                    for super_prop in [OWLObjectProperty(top_entity) for top_entity, score in self.predict(
                            h=property_.str,
                            r=self.STR_IRI_SUBPROPERTY,
                            t=None
                        )]:
                        if super_prop not in visited:
                            visited.add(super_prop)
                            all_super_properties.append(super_prop)
                            collect_super_properties(super_prop)
                
                for prop in super_properties:
                    visited.add(prop)
                    all_super_properties.append(prop)
                    collect_super_properties(prop)
                    
                yield from all_super_properties
    
    def get_root_ontology(self) -> NeuralOntology:
        return self.ontology


if __name__ == "__main__":
    ontology = NeuralOntology(path_neural_embedding="KGs/Family/trained_model", train_if_not_exists=True, training_params={"num_epochs": 100, "batch_size": 128})

    reasoner = EBR(ontology=ontology, gamma=0.8)

    print(len(reasoner.model.entity_to_idx))
    print(reasoner.model.predict_topk(h=None, r="http://example.com/father#hasChild", t=["http://example.com/father#anna", "http://example.com/father#heinz", "http://example.com/father#michelle"]))
