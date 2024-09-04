"""OWL Datatype restriction constructors."""
from typing import Union
from datetime import datetime, date
from owlapy.owl_literal import OWLLiteral
from owlapy.class_expression import OWLDatatypeRestriction, OWLFacet, OWLFacetRestriction
from pandas import Timedelta

Restriction_Literals = Union[OWLLiteral, int, float, Timedelta, datetime, date]


def owl_datatype_max_exclusive_restriction(max_: Restriction_Literals) -> OWLDatatypeRestriction:
    """Create a max exclusive restriction."""
    r = OWLFacetRestriction(OWLFacet.MAX_EXCLUSIVE, max_)
    return OWLDatatypeRestriction(r.get_facet_value().get_datatype(), r)


def owl_datatype_min_exclusive_restriction(min_: Restriction_Literals) -> OWLDatatypeRestriction:
    """Create a min exclusive restriction."""
    r = OWLFacetRestriction(OWLFacet.MIN_EXCLUSIVE, min_)
    return OWLDatatypeRestriction(r.get_facet_value().get_datatype(), r)


def owl_datatype_max_inclusive_restriction(max_: Restriction_Literals) -> OWLDatatypeRestriction:
    """Create a max inclusive restriction."""
    r = OWLFacetRestriction(OWLFacet.MAX_INCLUSIVE, max_)
    return OWLDatatypeRestriction(r.get_facet_value().get_datatype(), r)


def owl_datatype_min_inclusive_restriction(min_: Restriction_Literals) -> OWLDatatypeRestriction:
    """Create a min inclusive restriction."""
    r = OWLFacetRestriction(OWLFacet.MIN_INCLUSIVE, min_)
    return OWLDatatypeRestriction(r.get_facet_value().get_datatype(), r)


def owl_datatype_min_max_exclusive_restriction(min_: Restriction_Literals,
                                               max_: Restriction_Literals) -> OWLDatatypeRestriction:
    """Create a min-max exclusive restriction."""
    if isinstance(min_, float) and isinstance(max_, int):
        max_ = float(max_)
    if isinstance(max_, float) and isinstance(min_, int):
        min_ = float(min_)
    assert type(min_) is type(max_)

    r_min = OWLFacetRestriction(OWLFacet.MIN_EXCLUSIVE, min_)
    r_max = OWLFacetRestriction(OWLFacet.MAX_EXCLUSIVE, max_)
    restrictions = (r_min, r_max)
    return OWLDatatypeRestriction(r_min.get_facet_value().get_datatype(), restrictions)


def owl_datatype_min_max_inclusive_restriction(min_: Restriction_Literals,
                                               max_: Restriction_Literals) -> OWLDatatypeRestriction:
    """Create a min-max inclusive restriction."""
    if isinstance(min_, float) and isinstance(max_, int):
        max_ = float(max_)
    if isinstance(max_, float) and isinstance(min_, int):
        min_ = float(min_)
    assert type(min_) is type(max_)

    r_min = OWLFacetRestriction(OWLFacet.MIN_INCLUSIVE, min_)
    r_max = OWLFacetRestriction(OWLFacet.MAX_INCLUSIVE, max_)
    restrictions = (r_min, r_max)
    return OWLDatatypeRestriction(r_min.get_facet_value().get_datatype(), restrictions)
