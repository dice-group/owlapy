---
paths:
  - "owlapy/parser.py"
  - "owlapy/render.py"
  - "owlapy/converter.py"
  - "owlapy/__init__.py"
  - "tests/test_owlapy_conversions.py"
  - "tests/test_converter_extended.py"
  - "tests/test_owlapy_owl2sparql_converter.py"
---

# Syntax Conversion (DL / Manchester / SPARQL)

## Rendering (OWL object -> string)

```python
from owlapy import owl_expression_to_dl, owl_expression_to_manchester, owl_expression_to_sparql
from owlapy import owl_expression_to_sparql_with_confusion_matrix  # adds pos/neg vars for ML eval

owl_expression_to_dl(ce)          # "(∃ hasChild.male) ⊓ teacher"
owl_expression_to_manchester(ce)  # "hasChild some male and teacher"
owl_expression_to_sparql(ce)      # SELECT DISTINCT ?x WHERE { ... }
```

## Parsing (string -> OWL object)

```python
from owlapy import dl_to_owl_expression, manchester_to_owl_expression

ce = dl_to_owl_expression("∃ hasChild.Male", "http://example.com/family#")
ce = manchester_to_owl_expression("hasChild some Female", "http://www.benchmark.org/family#")
```

`namespace` is a base prefix string ending in `#` or `/`; parsers append the class/property name to it to build full IRIs.

### Prefixed names (`prefix:localName`)

`owl:`, `rdf:`, `rdfs:` and `xsd:` resolve out of the box; register any other prefix via
`prefixes=`:

```python
ce = dl_to_owl_expression("foaf:Agent ⊓ Person", "http://example.com/family#",
                          prefixes={"foaf": "http://xmlns.com/foaf/0.1/"})
```

An empty prefix (`:Person`) falls back to `namespace`. `DLSyntaxParser`/`ManchesterOWLSyntaxParser`
accept the same `prefixes=` constructor argument if you're instantiating a parser directly instead
of using the module-level singletons. Unregistered prefixes raise a `ValueError` (wrapped in
`parsimonious.exceptions.VisitationError` since it's raised from inside a grammar visitor method).

## Symbol Reference

| Symbol | Meaning | Class |
|---|---|---|
| `⊓` | AND | `OWLObjectIntersectionOf` |
| `⊔` | OR | `OWLObjectUnionOf` |
| `¬` | NOT | `OWLObjectComplementOf` |
| `∃` | some | `OWLObjectSomeValuesFrom` |
| `∀` | only | `OWLObjectAllValuesFrom` |
| `≥ n` / `≤ n` / `= n` | cardinality | `OWLObjectMinCardinality` / `Max` / `Exact` |
| `⊤` / `⊥` | Thing / Nothing | `OWLThing` / `OWLNothing` |
| `⊑` / `≡` | subclass / equivalent | `OWLSubClassOfAxiom` / `OWLEquivalentClassesAxiom` |
| `⁻` | inverse | `OWLObjectInverseOf` |
| `{a}` | nominal | `OWLObjectOneOf` |

## Constraints

- SPARQL output uses `SELECT DISTINCT ?x` where `?x` represents instances
- When verifying a conversion, round-trip it (parse -> render, or build -> render -> parse) rather than eyeballing the string
- Same functions are importable from `owlapy` directly or from their defining submodule (`owlapy.parser`, `owlapy.render`, `owlapy.converter`) — prefer the top-level `owlapy` import in new code
