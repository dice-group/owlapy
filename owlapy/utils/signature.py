"""Signature extraction: the set of named entities referenced by an axiom or class expression/data range."""
from functools import singledispatchmethod
from typing import Set

from owlapy.class_expression import OWLDataOneOf, OWLDatatypeRestriction, OWLHasValueRestriction, OWLNaryBooleanClassExpression, OWLObjectComplementOf, OWLObjectOneOf, OWLQuantifiedRestriction
from owlapy.owl_axiom import (
    OWLClassAssertionAxiom,
    OWLDeclarationAxiom,
    OWLNaryClassAxiom,
    OWLPropertyAssertionAxiom,
    OWLPropertyDomainAxiom,
    OWLPropertyRangeAxiom,
    OWLSubClassOfAxiom,
)
from owlapy.owl_individual import OWLAnonymousIndividual, OWLNamedIndividual

from ..class_expression import OWLClass, OWLObjectHasSelf
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
    is intentionally excluded (it is not an :class:`OWLEntity`, per the OWL 2 specification).

    Coverage is currently limited to the axiom types listed below (chosen to cover what
    ``SyncOntology.get_tbox_axioms()``/``get_abox_axioms()`` return for the ontologies in this repo's test
    suite) plus the full set of class expression/data range constructs. Extending coverage to the remaining
    :class:`OWLAxiom` subtypes (property characteristics, property chains, has-key, disjoint union, datatype
    definition, (un)equal individuals, annotation assertions, ...) is tracked in
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
    def _(self, o: OWLLiteral) -> Set[OWLEntity]:
        return self.get_signature(o.get_datatype())

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

    # -- axioms (core set, see class docstring) --------------------------------

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
