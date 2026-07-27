"""Compute the DL (Description Logic) expressivity of a loaded ontology.

Feature detection is delegated to OWLAPI's ``DLExpressivityChecker``
(already bundled for the Java reasoners in ``owlapy/jar_dependencies/``),
since its subsumption handling (e.g. full existential subsuming limited
existential, qualified cardinality subsuming unqualified) is mature and
battle-tested. The canonical DL name (e.g. ``"ALC"``, ``"SHIQ(D)"``) is
assembled here rather than via OWLAPI's own ``getDescriptionLogicName()``,
whose ``Construct.toString()`` returns internal debug labels
(``"RRESTR"``, ``"CINT"``, ...) instead of standard DL letters.
"""
from owlapy.owl_ontology import SyncOntology

__all__ = ['get_dl_expressivity']


def get_dl_expressivity(ontology: SyncOntology) -> str:
    """Compute the DL expressivity name of an ontology, e.g. ``"ALCHN(D)"``.

    Args:
        ontology: A :class:`~owlapy.owl_ontology.SyncOntology` instance.

    Returns:
        The standard Description Logic name for the ontology's expressivity.

    Raises:
        TypeError: If ``ontology`` is not backed by OWLAPI (only
            :class:`~owlapy.owl_ontology.SyncOntology` is supported, since
            it is the only ontology backend that exposes RBox axioms).
    """
    if not isinstance(ontology, SyncOntology):
        raise TypeError(
            "get_dl_expressivity() requires a SyncOntology (OWLAPI-backed); "
            f"got {type(ontology).__name__}. Load the ontology with "
            "owlapy.owl_ontology.SyncOntology instead."
        )

    # noinspection PyUnresolvedReferences
    from org.semanticweb.owlapi.util import DLExpressivityChecker

    checker = DLExpressivityChecker([ontology.owlapi_ontology])
    constructs = {str(c.name()) for c in checker.getConstructs()}

    has_complex_negation = "CONCEPT_COMPLEX_NEGATION" in constructs
    has_union = "CONCEPT_UNION" in constructs
    has_full_existential = "FULL_EXISTENTIAL" in constructs
    has_role_hierarchy = "ROLE_HIERARCHY" in constructs
    has_transitive = "ROLE_TRANSITIVE" in constructs
    has_complex_roles = "ROLE_REFLEXIVITY_CHAINS" in constructs or "ROLE_COMPLEX" in constructs
    has_nominals = "NOMINALS" in constructs
    has_inverse = "ROLE_INVERSE" in constructs
    has_functional = "F" in constructs
    has_unqualified_cardinality = "N" in constructs
    has_qualified_cardinality = "Q" in constructs
    has_datatypes = "D" in constructs

    # S is shorthand for ALC + transitive roles and replaces the AL[C] prefix.
    if has_transitive:
        name = "S"
    else:
        name = "AL"
        if has_complex_negation:
            name += "C"
        else:
            # U and E are redundant once C is present (De Morgan's laws).
            if has_union:
                name += "U"
            if has_full_existential:
                name += "E"

    if has_role_hierarchy:
        name += "H"
    if has_complex_roles:
        name += "R"
    if has_nominals:
        name += "O"
    if has_inverse:
        name += "I"

    # Q (qualified cardinality) subsumes N (unqualified); show only one.
    if has_qualified_cardinality:
        name += "Q"
    elif has_unqualified_cardinality:
        name += "N"

    # F (functional) is redundant once N/Q is present (functional == <=1).
    if has_functional and not (has_unqualified_cardinality or has_qualified_cardinality):
        name += "F"

    if has_datatypes:
        name += "(D)"

    return name
