"""Signature extraction: the set of named entities referenced by an axiom or class expression/data range."""
from functools import singledispatchmethod
from typing import Set

from owlapy.class_expression import OWLDataOneOf, OWLDatatypeRestriction, OWLHasValueRestriction, OWLNaryBooleanClassExpression, OWLObjectComplementOf, OWLObjectOneOf, OWLQuantifiedRestriction
from owlapy.owl_axiom import (
    OWLAnnotationAssertionAxiom,
    OWLAnnotationProperty,
    OWLAnnotationPropertyDomainAxiom,
    OWLAnnotationPropertyRangeAxiom,
    OWLClassAssertionAxiom,
    OWLDatatypeDefinitionAxiom,
    OWLDeclarationAxiom,
    OWLDisjointUnionAxiom,
    OWLHasKeyAxiom,
    OWLNaryClassAxiom,
    OWLNaryIndividualAxiom,
    OWLNaryPropertyAxiom,
    OWLPropertyAssertionAxiom,
    OWLPropertyDomainAxiom,
    OWLPropertyRangeAxiom,
    OWLSubAnnotationPropertyOfAxiom,
    OWLSubClassOfAxiom,
    OWLSubPropertyAxiom,
    OWLSubPropertyChainAxiom,
    OWLUnaryPropertyAxiom,
)
from owlapy.owl_individual import OWLAnonymousIndividual, OWLNamedIndividual

from ..class_expression import OWLClass, OWLObjectHasSelf
from ..iri import IRI
from ..owl_data_ranges import OWLDataComplementOf, OWLNaryDataRange
from ..owl_datatype import OWLDatatype
from ..owl_literal import OWLLiteral
from ..owl_object import OWLEntity, OWLObject
from ..owl_property import OWLDataProperty, OWLObjectInverseOf, OWLObjectProperty


class SignatureExtractor:
    """Computes the signature of an axiom or class expression/data range: the set of named entities
    (:class:`OWLClass`, :class:`OWLObjectProperty`, :class:`OWLDataProperty`, :class:`OWLNamedIndividual`,
    :class:`OWLDatatype`) that it references, collected recursively.

    Mirrors the ``signature()`` method of OWLAPI's ``OWLObject`` interface. :class:`OWLAnonymousIndividual`
    is intentionally excluded (it is not an :class:`OWLEntity`, per the OWL 2 specification). Likewise, a
    bare :class:`~owlapy.iri.IRI` (used as an annotation subject/value or as the domain/range of an
    annotation property axiom) contributes nothing to the signature unless it has been resolved to a
    concrete entity elsewhere in the expression.

    Covers the full set of class expression/data range constructs plus all :class:`OWLAxiom` subtypes,
    including property characteristics, sub-property (and property chain) axioms, has-key, disjoint union,
    datatype definition, (un)equal individuals and annotation axioms. See
    https://github.com/dice-group/owlapy/issues/231.
    """

    @singledispatchmethod
    def get_signature(self, o: OWLObject) -> Set[OWLEntity]:
        """Compute the signature of *o*.

        Args:
            o: An axiom, class expression, data range, property expression, individual or literal.

        Returns:
            The set of named entities referenced by *o*.
        """
        raise NotImplementedError(
            f"signature() is not yet implemented for {type(o).__name__}. See "
            "https://github.com/dice-group/owlapy/issues/231 to track extending coverage."
        )

    # -- entities (leaves) -----------------------------------------------------

    @get_signature.register
    def _(self, o: OWLClass) -> Set[OWLEntity]:
        return {o}

    @get_signature.register
    def _(self, o: OWLObjectProperty) -> Set[OWLEntity]:
        return {o}

    @get_signature.register
    def _(self, o: OWLDataProperty) -> Set[OWLEntity]:
        return {o}

    @get_signature.register
    def _(self, o: OWLObjectInverseOf) -> Set[OWLEntity]:
        return self.get_signature(o.get_inverse())

    @get_signature.register
    def _(self, o: OWLNamedIndividual) -> Set[OWLEntity]:
        return {o}

    @get_signature.register
    def _(self, o: OWLAnonymousIndividual) -> Set[OWLEntity]:
        return set()

    @get_signature.register
    def _(self, o: OWLDatatype) -> Set[OWLEntity]:
        return {o}

    @get_signature.register
    def _(self, o: OWLAnnotationProperty) -> Set[OWLEntity]:
        return {o}

    @get_signature.register
    def _(self, o: OWLLiteral) -> Set[OWLEntity]:
        return self.get_signature(o.get_datatype())

    @get_signature.register
    def _(self, o: IRI) -> Set[OWLEntity]:
        # A raw IRI (annotation subject/value, annotation property domain/range) is not itself an
        # OWLEntity -- it is only a name, not a resolved reference to one.
        return set()

    # -- class expressions / data ranges ---------------------------------------

    @get_signature.register(OWLNaryBooleanClassExpression)
    @get_signature.register(OWLObjectComplementOf)
    @get_signature.register(OWLObjectOneOf)
    @get_signature.register(OWLNaryDataRange)
    @get_signature.register(OWLDataOneOf)
    def _(self, o) -> Set[OWLEntity]:
        result: Set[OWLEntity] = set()
        for op in o.operands():
            result |= self.get_signature(op)
        return result

    @get_signature.register
    def _(self, o: OWLDataComplementOf) -> Set[OWLEntity]:
        return self.get_signature(o.get_data_range())

    @get_signature.register(OWLQuantifiedRestriction)
    @get_signature.register(OWLHasValueRestriction)
    def _(self, o) -> Set[OWLEntity]:
        return self.get_signature(o.get_property()) | self.get_signature(o.get_filler())

    @get_signature.register
    def _(self, o: OWLObjectHasSelf) -> Set[OWLEntity]:
        return self.get_signature(o.get_property())

    @get_signature.register
    def _(self, o: OWLDatatypeRestriction) -> Set[OWLEntity]:
        return self.get_signature(o.get_datatype())

    # -- axioms ------------------------------------------------------------

    @get_signature.register
    def _(self, o: OWLDeclarationAxiom) -> Set[OWLEntity]:
        return self.get_signature(o.get_entity())

    @get_signature.register
    def _(self, o: OWLClassAssertionAxiom) -> Set[OWLEntity]:
        return self.get_signature(o.get_individual()) | self.get_signature(o.get_class_expression())

    @get_signature.register
    def _(self, o: OWLPropertyAssertionAxiom) -> Set[OWLEntity]:
        return (self.get_signature(o.get_subject()) | self.get_signature(o.get_property())
                | self.get_signature(o.get_object()))

    @get_signature.register
    def _(self, o: OWLSubClassOfAxiom) -> Set[OWLEntity]:
        return self.get_signature(o.get_sub_class()) | self.get_signature(o.get_super_class())

    @get_signature.register
    def _(self, o: OWLNaryClassAxiom) -> Set[OWLEntity]:
        result: Set[OWLEntity] = set()
        for ce in o.class_expressions():
            result |= self.get_signature(ce)
        return result

    @get_signature.register
    def _(self, o: OWLPropertyDomainAxiom) -> Set[OWLEntity]:
        return self.get_signature(o.get_property()) | self.get_signature(o.get_domain())

    @get_signature.register
    def _(self, o: OWLPropertyRangeAxiom) -> Set[OWLEntity]:
        return self.get_signature(o.get_property()) | self.get_signature(o.get_range())

    @get_signature.register
    def _(self, o: OWLUnaryPropertyAxiom) -> Set[OWLEntity]:
        # Property characteristic axioms (Functional/InverseFunctional/Symmetric/Asymmetric/
        # Transitive/Reflexive/Irreflexive ObjectProperty, FunctionalDataProperty). Domain/range axioms
        # are handled by the more specific registrations above.
        return self.get_signature(o.get_property())

    @get_signature.register
    def _(self, o: OWLSubPropertyAxiom) -> Set[OWLEntity]:
        return self.get_signature(o.get_sub_property()) | self.get_signature(o.get_super_property())

    @get_signature.register
    def _(self, o: OWLSubPropertyChainAxiom) -> Set[OWLEntity]:
        result: Set[OWLEntity] = self.get_signature(o.get_super_property())
        for p in o.get_property_chain():
            result |= self.get_signature(p)
        return result

    @get_signature.register
    def _(self, o: OWLNaryIndividualAxiom) -> Set[OWLEntity]:
        result: Set[OWLEntity] = set()
        for ind in o.individuals():
            result |= self.get_signature(ind)
        return result

    @get_signature.register
    def _(self, o: OWLNaryPropertyAxiom) -> Set[OWLEntity]:
        result: Set[OWLEntity] = set()
        for p in o.properties():
            result |= self.get_signature(p)
        return result

    @get_signature.register
    def _(self, o: OWLDisjointUnionAxiom) -> Set[OWLEntity]:
        result = self.get_signature(o.get_owl_class())
        for ce in o.get_class_expressions():
            result |= self.get_signature(ce)
        return result

    @get_signature.register
    def _(self, o: OWLHasKeyAxiom) -> Set[OWLEntity]:
        result = self.get_signature(o.get_class_expression())
        for p in o.get_property_expressions():
            result |= self.get_signature(p)
        return result

    @get_signature.register
    def _(self, o: OWLDatatypeDefinitionAxiom) -> Set[OWLEntity]:
        return self.get_signature(o.get_datatype()) | self.get_signature(o.get_datarange())

    @get_signature.register
    def _(self, o: OWLAnnotationAssertionAxiom) -> Set[OWLEntity]:
        return (self.get_signature(o.get_subject()) | self.get_signature(o.get_property())
                | self.get_signature(o.get_value()))

    @get_signature.register
    def _(self, o: OWLSubAnnotationPropertyOfAxiom) -> Set[OWLEntity]:
        return self.get_signature(o.get_sub_property()) | self.get_signature(o.get_super_property())

    @get_signature.register
    def _(self, o: OWLAnnotationPropertyDomainAxiom) -> Set[OWLEntity]:
        return self.get_signature(o.get_property()) | self.get_signature(o.get_domain())

    @get_signature.register
    def _(self, o: OWLAnnotationPropertyRangeAxiom) -> Set[OWLEntity]:
        return self.get_signature(o.get_property()) | self.get_signature(o.get_range())
