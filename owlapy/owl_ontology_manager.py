from abc import ABCMeta, abstractmethod
from functools import singledispatch
from itertools import islice, combinations
import types
from typing import cast

import owlready2

from owlapy.iri import IRI
from owlapy.meta_classes import HasIRI
from owlapy.owl_object import OWLObject
from owlready2 import destroy_entity, AllDisjoint, AllDifferent, GeneralClassAxiom
from owlapy.class_expression import OWLThing, OWLClass, \
    OWLQuantifiedDataRestriction, OWLDataHasValue, OWLNaryBooleanClassExpression, OWLObjectOneOf, OWLObjectComplementOf, \
    OWLObjectHasValue, OWLQuantifiedObjectRestriction
from owlapy.owl_axiom import OWLObjectPropertyRangeAxiom, OWLAxiom, OWLSubClassOfAxiom, OWLEquivalentClassesAxiom, \
    OWLDisjointUnionAxiom, OWLAnnotationAssertionAxiom, OWLAnnotationProperty, OWLSubPropertyAxiom, \
    OWLPropertyRangeAxiom, OWLClassAssertionAxiom, OWLDeclarationAxiom, OWLObjectPropertyAssertionAxiom, \
    OWLSymmetricObjectPropertyAxiom, OWLTransitiveObjectPropertyAxiom, OWLPropertyDomainAxiom, \
    OWLAsymmetricObjectPropertyAxiom, OWLDataPropertyCharacteristicAxiom, OWLFunctionalDataPropertyAxiom, \
    OWLReflexiveObjectPropertyAxiom, OWLDataPropertyAssertionAxiom, OWLFunctionalObjectPropertyAxiom, \
    OWLObjectPropertyCharacteristicAxiom, OWLIrreflexiveObjectPropertyAxiom, OWLInverseFunctionalObjectPropertyAxiom, \
    OWLDisjointDataPropertiesAxiom, OWLDisjointObjectPropertiesAxiom, OWLEquivalentDataPropertiesAxiom, \
    OWLEquivalentObjectPropertiesAxiom, OWLInverseObjectPropertiesAxiom, OWLNaryPropertyAxiom, OWLNaryIndividualAxiom, \
    OWLDifferentIndividualsAxiom, OWLDisjointClassesAxiom, OWLSameIndividualAxiom
from owlapy.owl_individual import OWLNamedIndividual, OWLIndividual
from owlapy.owl_ontology import OWLOntology, OWLOntology_Owlready2, ToOwlready2
from owlapy.owl_property import OWLDataProperty, OWLObjectInverseOf, OWLObjectProperty, \
    OWLProperty


class OWLOntologyChange(metaclass=ABCMeta):
    """Represents an ontology change."""
    __slots__ = ()

    _ont: OWLOntology

    @abstractmethod
    def __init__(self, ontology: OWLOntology):
        self._ont = ontology

    def get_ontology(self) -> OWLOntology:
        """Gets the ontology that the change is/was applied to.

        Returns:
            The ontology that the change is applicable to.
        """
        return self._ont


class OWLOntologyManager(metaclass=ABCMeta):
    """An OWLOntologyManager manages a set of ontologies. It is the main point for creating, loading and accessing
    ontologies."""

    @abstractmethod
    def create_ontology(self, iri: IRI) -> OWLOntology:
        """Creates a new (empty) ontology that that has the specified ontology IRI (and no version IRI).

        Args:
            iri: The IRI of the ontology to be created.

        Returns:
            The newly created ontology, or if an ontology with the specified IRI already exists then this existing
            ontology will be returned.
        """
        pass

    @abstractmethod
    def load_ontology(self, iri: IRI) -> OWLOntology:
        """Loads an ontology that is assumed to have the specified ontology IRI as its IRI or version IRI. The ontology
        IRI will be mapped to an ontology document IRI.

        Args:
            iri: The IRI that identifies the ontology. It is expected that the ontology will also have this IRI
                (although the OWL API should tolerate situations where this is not the case).

        Returns:
            The OWLOntology representation of the ontology that was loaded.
        """
        pass

    @abstractmethod
    def apply_change(self, change: OWLOntologyChange):
        """A convenience method that applies just one change to an ontology. When this method is used through an
        OWLOntologyManager implementation, the instance used should be the one that the ontology returns through the
        get_owl_ontology_manager() call.

        Args:
            change: The change to be applied.

        Raises:
            ChangeApplied.UNSUCCESSFULLY: if the change was not applied successfully.
        """
        pass

    @abstractmethod
    def add_axiom(self, ontology: OWLOntology, axiom: OWLAxiom):
        """A convenience method that adds a single axiom to an ontology.

        Args:
            ontology: The ontology to add the axiom to.
            axiom: The axiom to be added.
        """
        pass

    @abstractmethod
    def remove_axiom(self, ontology: OWLOntology, axiom: OWLAxiom):
        """A convenience method that removes a single axiom from an ontology.

        Args:
            ontology: The ontology to remove the axiom from.
            axiom: The axiom to be removed.
        """
        pass

    @abstractmethod
    def save_ontology(self, ontology: OWLOntology, document_iri: IRI):
        """Saves the specified ontology, using the specified document IRI to determine where/how the ontology should be
        saved.

        Args:
            ontology: The ontology to be saved.
            document_iri: The document IRI where the ontology should be saved to.
        """
        pass


class OWLImportsDeclaration(HasIRI):
    """Represents an import statement in an ontology."""
    __slots__ = '_iri'

    def __init__(self, import_iri: IRI):
        """
        Args:
            import_iri: Imported ontology.

        Returns:
            An imports declaration.
        """
        self._iri = import_iri

    @property
    def iri(self) -> IRI:
        """Gets the import IRI.

        Returns:
            The import IRI that points to the ontology to be imported. The imported ontology might have this IRI as
            its ontology IRI but this is not mandated. For example, an ontology with a non-resolvable ontology IRI
            can be deployed at a resolvable URL.
        """
        return self._iri

    @property
    def str(self) -> str:
        return self._iri.as_str()


class AddImport(OWLOntologyChange):
    """Represents an ontology change where an import statement is added to an ontology."""
    __slots__ = '_ont', '_declaration'

    def __init__(self, ontology: OWLOntology, import_declaration: OWLImportsDeclaration):
        """
        Args:
            ontology: The ontology to which the change is to be applied.
            import_declaration: The import declaration.
        """
        super().__init__(ontology)
        self._declaration = import_declaration

    def get_import_declaration(self) -> OWLImportsDeclaration:
        """Gets the import declaration that the change pertains to.

        Returns:
            The import declaration.
        """
        return self._declaration


@singledispatch
def _add_axiom(axiom: OWLAxiom):
    raise NotImplementedError(f'Axiom type {axiom} is not implemented yet.')


@_add_axiom.register
def _(axiom: OWLDeclarationAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    entity = axiom.get_entity()
    with ont_x:
        entity_x = world[entity.to_string_id()]
        # Entity already exists
        if entity_x is not None:
            return

        thing_x: owlready2.entity.ThingClass = conv.map_concept(OWLThing)
        if isinstance(entity, OWLClass):
            if entity.is_owl_thing() or entity.is_owl_nothing():
                return
            entity_x = types.new_class(name=entity.iri.get_remainder(), bases=(thing_x,))
        elif isinstance(entity, OWLIndividual):
            entity_x = thing_x(entity.iri.get_remainder())
        elif isinstance(entity, OWLObjectProperty):
            entity_x = types.new_class(name=entity.iri.get_remainder(), bases=(owlready2.ObjectProperty,))
        elif isinstance(entity, OWLDataProperty):
            entity_x = types.new_class(name=entity.iri.get_remainder(), bases=(owlready2.DatatypeProperty,))
        elif isinstance(entity, OWLAnnotationProperty):
            entity_x = types.new_class(name=entity.iri.get_remainder(), bases=(owlready2.AnnotationProperty,))
        else:
            raise ValueError(f'Cannot add ({entity}). Not an atomic class, property, or individual.')
        entity_x.namespace = ont_x.get_namespace(entity.iri.get_namespace())
        entity_x.namespace.world._refactor(entity_x.storid, entity_x.iri)


@_add_axiom.register
def _(axiom: OWLClassAssertionAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    individual = axiom.get_individual()
    cls_ = axiom.get_class_expression()
    _check_expression(cls_, ontology, world)
    _add_axiom(OWLDeclarationAxiom(individual), ontology, world)
    with ont_x:
        cls_x = conv.map_concept(cls_)
        ind_x = conv._to_owlready2_individual(individual)
        thing_x = conv.map_concept(OWLThing)
        if thing_x in ind_x.is_a:
            ind_x.is_a.remove(thing_x)
        ind_x.is_a.append(cls_x)


@_add_axiom.register
def _(axiom: OWLObjectPropertyAssertionAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    subject = axiom.get_subject()
    property_ = axiom.get_property()
    object_ = axiom.get_object()
    _add_axiom(OWLDeclarationAxiom(subject), ontology, world)
    _add_axiom(OWLDeclarationAxiom(property_), ontology, world)
    _add_axiom(OWLDeclarationAxiom(object_), ontology, world)
    with ont_x:
        subject_x = conv._to_owlready2_individual(subject)
        property_x = conv._to_owlready2_property(property_)
        object_x = conv._to_owlready2_individual(object_)
        property_x[subject_x].append(object_x)


@_add_axiom.register
def _(axiom: OWLDataPropertyAssertionAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    subject = axiom.get_subject()
    property_ = axiom.get_property()
    _add_axiom(OWLDeclarationAxiom(subject), ontology, world)
    _add_axiom(OWLDeclarationAxiom(property_), ontology, world)
    with ont_x:
        subject_x = conv._to_owlready2_individual(subject)
        property_x = conv._to_owlready2_property(property_)
        property_x[subject_x].append(axiom.get_object().to_python())


@_add_axiom.register
def _(axiom: OWLSubClassOfAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    sub_class = axiom.get_sub_class()
    super_class = axiom.get_super_class()

    _check_expression(sub_class, ontology, world)
    _check_expression(super_class, ontology, world)
    with ont_x:
        thing_x = conv.map_concept(OWLThing)
        sub_class_x = conv.map_concept(sub_class)
        super_class_x = conv.map_concept(super_class)
        if isinstance(sub_class, OWLClass):
            if thing_x in sub_class_x.is_a:
                sub_class_x.is_a.remove(thing_x)
        else:
            # Currently owlready2 seems to expect that we make a new GeneralClassAxiom object each time.
            # Another option would be to check whether a GeneralClassAxiom with the sub_class_x already exists and just
            # add the super_class_x to its is_a attribute
            sub_class_x = GeneralClassAxiom(sub_class_x)
        sub_class_x.is_a.append(super_class_x)


# TODO: Update as soon as owlready2 adds support for EquivalentClasses general class axioms
@_add_axiom.register
def _(axiom: OWLEquivalentClassesAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x = conv.map_object(ontology)

    assert axiom.contains_named_equivalent_class(), 'Owlready2 does not support general' \
                                                    'class axioms for equivalent classes.'
    for ce in axiom.class_expressions():
        _check_expression(ce, ontology, world)
    with ont_x:
        for ce_1, ce_2 in combinations(axiom.class_expressions(), 2):
            assert ce_1 is not None, f"ce_1 cannot be None: {ce_1}, {type(ce_1)}"
            assert ce_2 is not None, f"ce_2_x cannot be None: {ce_2}, {type(ce_2)}"

            ce_1_x = conv.map_concept(ce_1)
            ce_2_x = conv.map_concept(ce_2)
            try:
                assert ce_1_x is not None, f"ce_1_x cannot be None: {ce_1_x}, {type(ce_1_x)}"
                assert ce_2_x is not None, f"ce_2_x cannot be None: {ce_2_x}, {type(ce_2_x)}"
            except AssertionError:
                print("function of ToOwlready2.map_concept() returns None")
                print(ce_1, ce_1_x)
                print(ce_2, ce_2_x)
                print("Axiom:", axiom)
                print("Temporary solution is reinitializing ce_1_x=ce_2_x\n\n")
                ce_1_x=ce_2_x

            if isinstance(ce_1_x, owlready2.ThingClass):
                ce_1_x.equivalent_to.append(ce_2_x)
            if isinstance(ce_2_x, owlready2.ThingClass):
                ce_2_x.equivalent_to.append(ce_1_x)


@_add_axiom.register
def _(axiom: OWLDisjointClassesAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    for cls_ in axiom.class_expressions():
        _check_expression(cls_, ontology, world)
    with ont_x:
        # TODO: If the first element in the list is a complex class expression owlready2 is bugged
        # and creates an AllDifferent axiom
        AllDisjoint(list(map(conv.map_concept, axiom.class_expressions())))


@_add_axiom.register
def _(axiom: OWLDisjointUnionAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    assert isinstance(axiom.get_owl_class(), OWLClass), f'({axiom.get_owl_class()}) is not a named class.'
    _add_axiom(OWLDeclarationAxiom(axiom.get_owl_class()), ontology, world)
    for cls_ in axiom.get_class_expressions():
        _check_expression(cls_, ontology, world)
    with ont_x:
        cls_x = conv.map_concept(axiom.get_owl_class())
        cls_x.disjoint_unions.append(list(map(conv.map_concept, axiom.get_class_expressions())))


@_add_axiom.register
def _(axiom: OWLAnnotationAssertionAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    prop_x = conv.map_object(axiom.get_property())
    if prop_x is None:
        with ont_x:
            prop_x: owlready2.annotation.AnnotationPropertyClass = cast(
                owlready2.AnnotationProperty,
                types.new_class(
                    name=axiom.get_property().iri.get_remainder(),
                    bases=(owlready2.AnnotationProperty,)))
            prop_x.namespace = ont_x.get_namespace(axiom.get_property().iri.get_namespace())
    sub_x = world[axiom.get_subject().as_iri().as_str()]
    assert sub_x is not None, f'{axiom.get_subject} not found in {ontology}'
    with ont_x:
        if axiom.get_value().is_literal():
            literal = axiom.get_value().as_literal()
            setattr(sub_x, prop_x.python_name, literal.to_python())
        else:
            o_x = world[axiom.get_value().as_iri().as_str()]
            assert o_x is not None, f'{axiom.get_value()} not found in {ontology}'
            setattr(sub_x, prop_x.python_name, o_x)


@_add_axiom.register
def _(axiom: OWLNaryIndividualAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    for ind in axiom.individuals():
        _add_axiom(OWLDeclarationAxiom(ind), ontology, world)
    with ont_x:
        if isinstance(axiom, OWLSameIndividualAxiom):
            for idx, ind in enumerate(axiom.individuals()):
                ind_x = conv._to_owlready2_individual(ind)
                for ind_2 in islice(axiom.individuals(), idx + 1, None):
                    ind_2_x = conv._to_owlready2_individual(ind_2)
                    ind_x.equivalent_to.append(ind_2_x)
        elif isinstance(axiom, OWLDifferentIndividualsAxiom):
            AllDifferent(list(map(conv._to_owlready2_individual, axiom.individuals())))
        else:
            raise ValueError(f'OWLNaryIndividualAxiom ({axiom}) is not defined.')


@_add_axiom.register
def _(axiom: OWLSubPropertyAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    sub_property = axiom.get_sub_property()
    super_property = axiom.get_super_property()
    _add_axiom(OWLDeclarationAxiom(sub_property), ontology, world)
    _add_axiom(OWLDeclarationAxiom(super_property), ontology, world)
    with ont_x:
        sub_property_x = conv._to_owlready2_property(sub_property)
        super_property_x = conv._to_owlready2_property(super_property)
        sub_property_x.is_a.append(super_property_x)


@_add_axiom.register
def _(axiom: OWLPropertyDomainAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    property_ = axiom.get_property()
    domain = axiom.get_domain()
    _add_axiom(OWLDeclarationAxiom(property_), ontology, world)
    _check_expression(domain, ontology, world)
    with ont_x:
        property_x = conv._to_owlready2_property(property_)
        domain_x = conv.map_concept(domain)
        property_x.domain.append(domain_x)


@_add_axiom.register
def _(axiom: OWLPropertyRangeAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    property_ = axiom.get_property()
    range_ = axiom.get_range()
    _add_axiom(OWLDeclarationAxiom(property_), ontology, world)
    if isinstance(axiom, OWLObjectPropertyRangeAxiom):
        _check_expression(range_, ontology, world)
    with ont_x:
        property_x = conv._to_owlready2_property(property_)
        range_x = conv.map_concept(range_) if isinstance(axiom, OWLObjectPropertyRangeAxiom) \
            else conv.map_datarange(range_)
        property_x.range.append(range_x)


@_add_axiom.register
def _(axiom: OWLNaryPropertyAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    for property_ in axiom.properties():
        _add_axiom(OWLDeclarationAxiom(property_), ontology, world)
    with ont_x:
        if isinstance(axiom, (OWLEquivalentObjectPropertiesAxiom, OWLEquivalentDataPropertiesAxiom,)):
            for idx, property_ in enumerate(axiom.properties()):
                property_x = conv._to_owlready2_property(property_)
                for property_2 in islice(axiom.properties(), idx + 1, None):
                    property_2_x = conv._to_owlready2_property(property_2)
                    property_x.equivalent_to.append(property_2_x)
        elif isinstance(axiom, (OWLDisjointObjectPropertiesAxiom, OWLDisjointDataPropertiesAxiom,)):
            AllDisjoint(list(map(conv._to_owlready2_property, axiom.properties())))
        elif isinstance(axiom, OWLInverseObjectPropertiesAxiom):
            property_first_x = conv._to_owlready2_property(axiom.get_first_property())
            property_second_x = conv._to_owlready2_property(axiom.get_second_property())
            if property_second_x.inverse_property is not None:
                property_second_x.inverse_property = None
            property_first_x.inverse_property = property_second_x
        else:
            raise ValueError(f'OWLNaryPropertyAxiom ({axiom}) is not defined.')


@_add_axiom.register
def _(axiom: OWLObjectPropertyCharacteristicAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    property_ = axiom.get_property()
    _add_axiom(OWLDeclarationAxiom(property_), ontology, world)
    with ont_x:
        property_x = conv._to_owlready2_property(property_)
        if isinstance(axiom, OWLFunctionalObjectPropertyAxiom):
            property_x.is_a.append(owlready2.FunctionalProperty)
        elif isinstance(axiom, OWLAsymmetricObjectPropertyAxiom):
            property_x.is_a.append(owlready2.AsymmetricProperty)
        elif isinstance(axiom, OWLInverseFunctionalObjectPropertyAxiom):
            property_x.is_a.append(owlready2.InverseFunctionalProperty)
        elif isinstance(axiom, OWLIrreflexiveObjectPropertyAxiom):
            property_x.is_a.append(owlready2.IrreflexiveProperty)
        elif isinstance(axiom, OWLReflexiveObjectPropertyAxiom):
            property_x.is_a.append(owlready2.ReflexiveProperty)
        elif isinstance(axiom, OWLSymmetricObjectPropertyAxiom):
            property_x.is_a.append(owlready2.SymmetricProperty)
        elif isinstance(axiom, OWLTransitiveObjectPropertyAxiom):
            property_x.is_a.append(owlready2.TransitiveProperty)
        else:
            raise ValueError(f'ObjectPropertyCharacteristicAxiom ({axiom}) is not defined.')


@_add_axiom.register
def _(axiom: OWLDataPropertyCharacteristicAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    property_ = axiom.get_property()
    _add_axiom(OWLDeclarationAxiom(property_), ontology, world)
    with ont_x:
        property_x = conv._to_owlready2_property(property_)
        if isinstance(axiom, OWLFunctionalDataPropertyAxiom):
            property_x.is_a.append(owlready2.FunctionalProperty)
        else:
            raise ValueError(f'DataPropertyCharacteristicAxiom ({axiom}) is not defined.')


@singledispatch
def _remove_axiom(axiom: OWLAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    raise NotImplementedError(f'Axiom type {axiom} is not implemented yet.')


@_remove_axiom.register
def _(axiom: OWLDeclarationAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)
    with ont_x:
        entity_x = world[axiom.get_entity().to_string_id()]
        if entity_x is not None:
            # TODO: owlready2 seems to be bugged for properties here
            destroy_entity(entity_x)


@_remove_axiom.register
def _(axiom: OWLClassAssertionAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    with ont_x:
        cls_x = conv.map_concept(axiom.get_class_expression())
        ind_x = conv._to_owlready2_individual(axiom.get_individual())
        if cls_x is None or ind_x is None:
            return
        if cls_x in ind_x.is_a:
            ind_x.is_a.remove(cls_x)
        elif isinstance(axiom.get_class_expression(), OWLClass):
            ont_x._del_obj_triple_spo(ind_x.storid, owlready2.rdf_type, cls_x.storid)


@_remove_axiom.register
def _(axiom: OWLObjectPropertyAssertionAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    with ont_x:
        subject_x = conv._to_owlready2_individual(axiom.get_subject())
        property_x = conv._to_owlready2_property(axiom.get_property())
        object_x = conv._to_owlready2_individual(axiom.get_object())
        if all([subject_x, property_x, object_x]) and object_x in property_x[subject_x]:
            property_x[subject_x].remove(object_x)


@_remove_axiom.register
def _(axiom: OWLDataPropertyAssertionAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    with ont_x:
        subject_x = conv._to_owlready2_individual(axiom.get_subject())
        property_x = conv._to_owlready2_property(axiom.get_property())
        object_ = axiom.get_object().to_python()
        if subject_x is not None and property_x is not None and object_ in property_x[subject_x]:
            property_x[subject_x].remove(object_)


@_remove_axiom.register
def _(axiom: OWLSubClassOfAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)
    sub_class = axiom.get_sub_class()
    super_class = axiom.get_super_class()

    with ont_x:
        sub_class_x = conv.map_concept(sub_class)
        super_class_x = conv.map_concept(super_class)
        if sub_class_x is None or super_class_x is None:
            return

        if isinstance(sub_class, OWLClass):
            if super_class_x in sub_class_x.is_a:
                sub_class_x.is_a.remove(super_class_x)
            elif isinstance(axiom.get_sub_class(), OWLClass) and isinstance(axiom.get_super_class(), OWLClass):
                ont_x._del_obj_triple_spo(sub_class_x.storid, owlready2.rdfs_subclassof, super_class_x.storid)
        else:
            for ca in ont_x.general_class_axioms():
                if ca.left_side == sub_class_x and super_class_x in ca.is_a:
                    ca.is_a.remove(super_class_x)


# TODO: Update as soons as owlready2 adds support for EquivalentClasses general class axioms
@_remove_axiom.register
def _(axiom: OWLEquivalentClassesAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x = conv.map_object(ontology)

    if not axiom.contains_named_equivalent_class():
        return

    with ont_x:
        ces_x = list(map(conv.map_concept, axiom.class_expressions()))
        if len(ces_x) < 2 or not all(ces_x):
            return

        for ce_1_x, ce_2_x in combinations(ces_x, 2):
            if isinstance(ce_2_x, owlready2.ThingClass) and ce_1_x in ce_2_x.equivalent_to:
                ce_2_x.equivalent_to.remove(ce_1_x)
            if isinstance(ce_1_x, owlready2.ThingClass) and ce_2_x in ce_1_x.equivalent_to:
                ce_1_x.equivalent_to.remove(ce_2_x)


@_remove_axiom.register
def _(axiom: OWLDisjointClassesAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    with ont_x:
        class_expressions_x = set(map(conv.map_concept, axiom.class_expressions()))
        if len(class_expressions_x) < 2 or not all(class_expressions_x):
            return
        for disjoints_x in ont_x.disjoint_classes():
            if set(disjoints_x.entities) == class_expressions_x:
                del disjoints_x.entities[:-1]
                break


@_remove_axiom.register
def _(axiom: OWLDisjointUnionAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)
    assert isinstance(axiom.get_owl_class(), OWLClass), f'({axiom.get_owl_class()}) is not a named class.'

    with ont_x:
        cls_x = conv.map_concept(axiom.get_owl_class())
        union_expressions_x = set(map(conv.map_concept, axiom.get_class_expressions()))
        if cls_x is not None and all(union_expressions_x):
            for union_x in cls_x.disjoint_unions:
                if union_expressions_x == set(union_x):
                    cls_x.disjoint_unions.remove(union_x)
                    break


@_remove_axiom.register
def _(axiom: OWLAnnotationAssertionAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    sub_x = world[axiom.get_subject().as_iri().as_str()]
    if sub_x is None:
        return
    name = axiom.get_property().iri.get_remainder()
    with ont_x:
        if axiom.get_value().is_literal():
            o_x = axiom.get_value().as_literal().to_python()
        else:
            o_x = world[axiom.get_value().as_iri().as_str()]

        value = getattr(sub_x, name, None)
        if value is not None and o_x in value:
            value.remove(o_x)


@_remove_axiom.register
def _(axiom: OWLNaryIndividualAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    with ont_x:
        individuals_x = list(map(conv._to_owlready2_individual, axiom.individuals()))
        if len(individuals_x) < 2 or not all(individuals_x):
            return
        if isinstance(axiom, OWLSameIndividualAxiom):
            if set(individuals_x[1:-1]) <= set(individuals_x[0].INDIRECT_equivalent_to):
                for individual_1_x, individual_2_x in combinations(individuals_x, 2):
                    if individual_1_x in individual_2_x.equivalent_to:
                        individual_2_x.equivalent_to.remove(individual_1_x)
                    if individual_2_x in individual_1_x.equivalent_to:
                        individual_1_x.equivalent_to.remove(individual_2_x)
        elif isinstance(axiom, OWLDifferentIndividualsAxiom):
            individuals_x = set(individuals_x)
            for different_x in ont_x.different_individuals():
                if set(different_x.entities) == individuals_x:
                    del different_x.entities[:-1]
                    break
        else:
            raise ValueError(f'OWLNaryIndividualAxiom ({axiom}) is not defined.')


@_remove_axiom.register
def _(axiom: OWLSubPropertyAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.namespace.Ontology = conv.map_object(ontology)

    with ont_x:
        sub_property_x = conv._to_owlready2_property(axiom.get_sub_property())
        super_property_x = conv._to_owlready2_property(axiom.get_super_property())
        if sub_property_x is None or super_property_x is None:
            return
        if super_property_x in sub_property_x.is_a:
            sub_property_x.is_a.remove(super_property_x)
        else:
            ont_x._del_obj_triple_spo(sub_property_x.storid, owlready2.rdfs_subpropertyof, super_property_x.storid)


@_remove_axiom.register
def _(axiom: OWLPropertyDomainAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    with ont_x:
        property_x = conv._to_owlready2_property(axiom.get_property())
        domain_x = conv.map_concept(axiom.get_domain())
        if domain_x is not None and property_x is not None and domain_x in property_x.domain:
            property_x.domain.remove(domain_x)


@_remove_axiom.register
def _(axiom: OWLPropertyRangeAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    with ont_x:
        property_x = conv._to_owlready2_property(axiom.get_property())
        range_x = conv.map_concept(axiom.get_range()) \
            if isinstance(axiom, OWLObjectPropertyRangeAxiom) else conv.map_datarange(axiom.get_range())
        if range_x is not None and property_x is not None and range_x in property_x.range:
            property_x.range.remove(range_x)


@_remove_axiom.register
def _(axiom: OWLNaryPropertyAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    with ont_x:
        properties_x = list(map(conv._to_owlready2_property, axiom.properties()))
        if len(properties_x) < 2 or not all(properties_x):
            return
        if isinstance(axiom, (OWLEquivalentObjectPropertiesAxiom, OWLEquivalentDataPropertiesAxiom,)):
            # Check if all equivalent properties are defined in the ontology
            if set(properties_x[1:-1]) <= set(properties_x[0].INDIRECT_equivalent_to):
                for property_1_x, property_2_x in combinations(properties_x, 2):
                    if property_1_x in property_2_x.equivalent_to:
                        property_2_x.equivalent_to.remove(property_1_x)
                    if property_2_x in property_1_x.equivalent_to:
                        property_1_x.equivalent_to.remove(property_2_x)
        elif isinstance(axiom, (OWLDisjointObjectPropertiesAxiom, OWLDisjointDataPropertiesAxiom,)):
            properties_x = set(properties_x)
            for disjoints_x in ont_x.disjoint_properties():
                if set(disjoints_x.entities) == properties_x:
                    del disjoints_x.entities[:-1]
                    break
        elif isinstance(axiom, OWLInverseObjectPropertiesAxiom):
            if len(properties_x) != 2:
                return
            first = properties_x[0]
            second = properties_x[1]
            if first.inverse_property == second and second.inverse_property == first:
                first.inverse_property = None
        else:
            raise ValueError(f'OWLNaryPropertyAxiom ({axiom}) is not defined.')


@_remove_axiom.register
def _(axiom: OWLObjectPropertyCharacteristicAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    with ont_x:
        property_x = conv._to_owlready2_property(axiom.get_property())
        if property_x is None:
            return

        if isinstance(axiom, OWLFunctionalObjectPropertyAxiom) and owlready2.FunctionalProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.FunctionalProperty)
        elif isinstance(axiom, OWLAsymmetricObjectPropertyAxiom) and owlready2.AsymmetricProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.AsymmetricProperty)
        elif isinstance(axiom, OWLInverseFunctionalObjectPropertyAxiom) \
                and owlready2.InverseFunctionalProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.InverseFunctionalProperty)
        elif isinstance(axiom, OWLIrreflexiveObjectPropertyAxiom) and owlready2.IrreflexiveProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.IrreflexiveProperty)
        elif isinstance(axiom, OWLReflexiveObjectPropertyAxiom) and owlready2.ReflexiveProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.ReflexiveProperty)
        elif isinstance(axiom, OWLSymmetricObjectPropertyAxiom) and owlready2.SymmetricProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.SymmetricProperty)
        elif isinstance(axiom, OWLTransitiveObjectPropertyAxiom) and owlready2.TransitiveProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.TransitiveProperty)
        else:
            raise ValueError(f'OWLObjectPropertyCharacteristicAxiom ({axiom}) is not defined.')


@_remove_axiom.register
def _(axiom: OWLDataPropertyCharacteristicAxiom, ontology: OWLOntology, world: owlready2.namespace.World):
    conv = ToOwlready2(world)
    ont_x: owlready2.Ontology = conv.map_object(ontology)

    with ont_x:
        property_x = conv._to_owlready2_property(axiom.get_property())
        if property_x is not None and isinstance(axiom, OWLFunctionalDataPropertyAxiom) \
                and owlready2.FunctionalProperty in property_x.is_a:
            property_x.is_a.remove(owlready2.FunctionalProperty)


def _check_expression(expr: OWLObject, ontology: OWLOntology, world: owlready2.namespace.World):
    """
    @TODO:CD: Documentation
    Creates all entities (individuals, classes, properties) that appear in the given (complex) class expression
    and do not exist in the given ontology yet

    """
    if isinstance(expr, (OWLClass, OWLProperty, OWLNamedIndividual,)):
        _add_axiom(OWLDeclarationAxiom(expr), ontology, world)
    elif isinstance(expr, (OWLNaryBooleanClassExpression, OWLObjectComplementOf, OWLObjectOneOf,)):
        for op in expr.operands():
            _check_expression(op, ontology, world)
    elif isinstance(expr, (OWLQuantifiedObjectRestriction, OWLObjectHasValue,)):
        _check_expression(expr.get_property(), ontology, world)
        _check_expression(expr.get_filler(), ontology, world)
    elif isinstance(expr, OWLObjectInverseOf):
        _check_expression(expr.get_named_property(), ontology, world)
        _check_expression(expr.get_inverse_property(), ontology, world)
    elif isinstance(expr, (OWLQuantifiedDataRestriction, OWLDataHasValue,)):
        _check_expression(expr.get_property(), ontology, world)
    elif not isinstance(expr, OWLObject):
        raise ValueError(f'({expr}) is not an OWLObject.')


class OWLOntologyManager_Owlready2(OWLOntologyManager):
    __slots__ = '_world'

    _world: owlready2.namespace.World

    def __init__(self, world_store=None):
        """Ontology manager in Ontolearn.
        Creates a world where ontology is loaded.
        Used to make changes in the ontology.

        Args:
            world_store: The file name of the world store. Leave to default value to create a new world.
        """
        if world_store is None:
            self._world = owlready2.World()
        else:
            self._world = owlready2.World(filename=world_store)

    def create_ontology(self, iri: IRI) -> 'OWLOntology_Owlready2':
        return OWLOntology_Owlready2(self, iri, load=False)

    def load_ontology(self, iri: IRI) -> 'OWLOntology_Owlready2':
        return OWLOntology_Owlready2(self, iri, load=True)

    def apply_change(self, change: OWLOntologyChange):
        if isinstance(change, AddImport):
            ont_x: owlready2.namespace.Ontology = self._world.get_ontology(
                change.get_ontology().get_ontology_id().get_ontology_iri().as_str())
            ont_x.imported_ontologies.append(
                self._world.get_ontology(change.get_import_declaration().str))
        else:
            # TODO XXX
            raise NotImplementedError

    def add_axiom(self, ontology: OWLOntology, axiom: OWLAxiom):
        _add_axiom(axiom, ontology, self._world)

    def remove_axiom(self, ontology: OWLOntology, axiom: OWLAxiom):
        _remove_axiom(axiom, ontology, self._world)

    def save_ontology(self, ontology: OWLOntology, document_iri: IRI):
        ont_x: owlready2.namespace.Ontology = self._world.get_ontology(
            ontology.get_ontology_id().get_ontology_iri().as_str()
        )
        if document_iri.get_namespace().startswith('file:/'):
            filename = document_iri.as_str()[len('file:/'):]
            ont_x.save(file=filename)
        else:
            # TODO XXX
            raise NotImplementedError

    def save_world(self):
        """Saves the actual state of the quadstore in the SQLite3 file.
        """
        self._world.save()

