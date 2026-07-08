---
paths:
  - "owlapy/class_expression/**/*.py"
  - "owlapy/utils.py"
  - "tests/test_ce_simplifier.py"
  - "tests/test_class_expression_semantics.py"
  - "tests/test_owlapy_nnf.py"
  - "tests/test_OWLObjectComplementOf.py"
  - "tests/test_data_cardinality_restrictions.py"
---

# OWL Class Expressions

All class expressions inherit from `OWLClassExpression` (`owlapy.class_expression`).

```python
from owlapy.class_expression import (
    OWLClass, OWLThing, OWLNothing,
    OWLObjectIntersectionOf, OWLObjectUnionOf, OWLObjectComplementOf,
    OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom,
    OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality,
    OWLObjectHasValue, OWLObjectHasSelf, OWLObjectOneOf,
    OWLDataSomeValuesFrom, OWLDataAllValuesFrom,
    OWLDataMinCardinality, OWLDataMaxCardinality, OWLDataExactCardinality,
    OWLDataHasValue, OWLDataOneOf, OWLDatatypeRestriction, OWLFacetRestriction,
)
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty, OWLObjectInverseOf
```

## Constraints

- `OWLObjectIntersectionOf` / `OWLObjectUnionOf` take a **list** of operands, not varargs
- `OWLObjectMinCardinality(n, property, filler)` — cardinality is the first argument
- Data restrictions use `OWLDataProperty`; object restrictions use `OWLObjectProperty` — don't mix up `OWLDataSomeValuesFrom` vs `OWLObjectSomeValuesFrom`
- `OWLObjectOneOf` takes a list of `OWLNamedIndividual` (nominals)
- Facets: `OWLFacet.MIN_INCLUSIVE` / `MAX_INCLUSIVE` / `MIN_EXCLUSIVE` / `MAX_EXCLUSIVE` (`owlapy.vocab`)
- Inverse object property: `OWLObjectInverseOf(prop)`

## Simplification and Normal Forms

```python
from owlapy.utils import simplify_class_expression, get_expression_length, CESimplifier, NNF

simplified = simplify_class_expression(ce)
length = get_expression_length(ce)          # structural complexity
nnf_ce = ce.get_nnf()                        # or NNF().get_class_nnf(ce)
neg_ce = ce.get_object_complement_of()
```

Only NNF is implemented — there is no CNF/DNF transformer; don't invent one without checking `owlapy/utils.py` first.

Utility methods available on any expression: `ce.is_owl_thing()`, `ce.is_owl_nothing()`, `ce.get_nnf()`, `ce.get_object_complement_of()`.
