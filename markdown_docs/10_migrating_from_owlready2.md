# Migrating from owlready2

owlapy's owlready2-backed classes are **deprecated and removed in owlapy 2.0** (tracked in
[#310](https://github.com/dice-group/owlapy/issues/310)). This page lists their replacements.

Why they are going away: owlready2 caused intermittent hangs when it parsed large files (it
forks a parser process and waits for it without a timeout), and some of its correctness bugs
(general class axioms, equivalent object properties) can't be fixed on owlapy's side. The
replacements below cover the same functionality without owlready2.

## What is deprecated

| Deprecated (removed in 2.0) | Warning today |
|---|---|
| `owlapy.owl_ontology.Ontology` | `DeprecationWarning` on construction |
| `owlapy.owl_reasoner.StructuralReasoner` | `DeprecationWarning` on construction; `FutureWarning` when given a path |
| `owlapy.owl_ontology.ToOwlready2` / `FromOwlready2` | `DeprecationWarning` on construction |
| `create_ontology(iri)` / `create_ontology(iri, with_owlapi=False)` | `FutureWarning`: returns `RDFLibOntology` in 2.0 |
| `NIRReasoner("path", ...)` | `FutureWarning`: loads an `RDFLibOntology` in 2.0 |
| The `owlready2` install extra (`pip install owlapy[owlready2]`) | removed in 2.0 |

Python hides `DeprecationWarning` outside `__main__` by default. To see every warning your code
triggers, run it with `python -W default::DeprecationWarning ...`.

## Mapping

| Before | After |
|---|---|
| `Ontology(path)` | `RDFLibOntology(path)` (pure Python), or `SyncOntology(path)` if you need OWL API features |
| `Ontology(iri, load=False)` | `RDFLibOntology(iri, load=False)` |
| `create_ontology(iri)` | `RDFLibOntology(iri, load=False)`, or `create_ontology(iri, with_owlapi=True)` for a `SyncOntology` |
| `StructuralReasoner(onto)` | `RDFLibReasoner(onto)` (pure Python), or `SyncReasoner(onto, reasoner="HermiT")` for complete OWL 2 DL reasoning |
| `StructuralReasoner("path")` | `RDFLibReasoner(RDFLibOntology("path"))`, or `RDFLibReasoner("path")` |
| `NIRReasoner("path", ...)` | `NIRReasoner(RDFLibOntology("path"), ...)` (its fallback is then an `RDFLibReasoner`) |
| `Ontology(..., world_store=...)` | none; persist with `RDFLibOntology.save()` and load the file again |
| `StructuralReasoner.reset()` / `reset_and_disable_cache()` | construct a new reasoner, or pass `class_cache=False` / `property_cache=False` |
| `ToOwlready2` / `FromOwlready2` | none; use owlapy objects directly, or `owlapy.owlapi_mapper` for OWL API objects |

`RDFLibReasoner` takes the same keyword arguments as `StructuralReasoner`: `class_cache`,
`property_cache`, `negation_default` and `sub_properties`.

### Before

```python
from owlapy.owl_ontology import Ontology
from owlapy.owl_reasoner import StructuralReasoner
from owlapy.class_expression import OWLClass

onto = Ontology("KGs/Family/family-benchmark_rich_background.owl")
reasoner = StructuralReasoner(onto, negation_default=True)
males = set(reasoner.instances(OWLClass("http://www.benchmark.org/family#Male")))
```

### After

```python
from owlapy.owl_ontology import RDFLibOntology
from owlapy.owl_reasoner_rdflib import RDFLibReasoner
from owlapy.class_expression import OWLClass

onto = RDFLibOntology("KGs/Family/family-benchmark_rich_background.owl")
reasoner = RDFLibReasoner(onto, negation_default=True)
males = set(reasoner.instances(OWLClass("http://www.benchmark.org/family#Male")))
```

Neither version needs the JVM or `stopJVM()`.

## Differences to check

- **Reading complex TBox axioms.** `RDFLibOntology` *writes* axioms with complex class
  expressions (e.g. `A ⊑ ∃r.B`), but its read API (`get_tbox_axioms()`,
  `equivalent_classes_axioms()`) still only reports axioms between named entities, and
  `general_class_axioms()` raises `NotImplementedError`. If you read TBox axioms from an
  `Ontology` today, use `SyncOntology` until this is added to `RDFLibOntology`.
- **Removing complex axioms.** `RDFLibOntology.remove_axiom()` raises `NotImplementedError` on an
  axiom with a complex operand.
- **Writing annotations.** `RDFLibOntology.annotation_assertion_axioms()` reads annotations, but
  `add_axiom(OWLAnnotationAssertionAxiom(...))` is not supported yet. Use `SyncOntology` for that.
- **Methods without a replacement.** `Ontology.get_original_iri()` and
  `StructuralReasoner.get_instances_from_owl_class()` have no counterpart.
- **Ontology changes after construction.** `RDFLibReasoner` takes a snapshot of the ontology when
  it is constructed. If you call `onto.add_axiom()`/`remove_axiom()` afterwards, call
  `reasoner.flush()` before the next query. `StructuralReasoner` read the live owlready2 world.
- **Reasoning results.** `RDFLibReasoner` is closed-world like `StructuralReasoner`, and
  `tests/test_rdflib_reasoner_structural_parity.py` runs `StructuralReasoner`'s test assertions
  against it. It is not bug-for-bug compatible: for example, it has no circular
  `sub_classes()`/`super_classes()` dependency, and that test file documents the known remaining
  gap. Compare results on your own data when you switch.
- **AGenKG.** `AGenKG.generate_ontology()` (via `DomainGraphExtractor`/`OpenGraphExtractor`)
  still returns an owlready2-backed `Ontology` and needs the `owlready2` extra. It will be moved
  to an owlready2-free ontology before 2.0.

## Related

- [Ontology Management](03_ontology_management.md)
- [Reasoning](05_reasoning.md)
- [API Reference](09_api_reference.md)
