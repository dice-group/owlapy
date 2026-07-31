---
paths:
  - "owlapy/owl_reasoner.py"
  - "owlapy/owl_reasoner_rdflib.py"
  - "owlapy/static_funcs.py"
  - "tests/test_owlapy_structural_reasoner.py"
  - "tests/test_sync_reasoner.py"
  - "tests/test_rdflib_reasoner*.py"
  - "tests/test_reasoner_*.py"
  - "tests/test_ontology_justification.py"
---

# OWL Reasoning

| Reasoner | Class | Backend | Notes |
|---|---|---|---|
| `RDFLibReasoner` | `owlapy.owl_reasoner_rdflib.RDFLibReasoner` | rdflib (pure Python) | No JVM, no owlready2. **Preferred over `StructuralReasoner`** (#205) |
| `StructuralReasoner` | `owlapy.owl_reasoner.StructuralReasoner` | owlready2 (pure Python) | **Legacy**, being phased out (#205). Fast, incomplete, no JVM. Constructing one emits `DeprecationWarning` |
| `SyncReasoner("HermiT"\|"Pellet"\|"JFact"\|"Openllet"\|"Structural")` | `owlapy.owl_reasoner.SyncReasoner` | Java/OWLAPI | Complete DL reasoning |
| `SyncReasoner("ELK")` | same | Java/OWLAPI | EL fragment only, very fast, no universals/nominals/inverses |

## RDFLibReasoner (no JVM, no owlready2 — preferred)

```python
from owlapy.owl_reasoner_rdflib import RDFLibReasoner
from owlapy.class_expression import OWLClass

reasoner = RDFLibReasoner("KGs/Family/father.owl")  # accepts a path, RDFLibOntology, or Ontology/SyncOntology directly
instances = set(reasoner.instances(OWLClass("http://example.com/father#male")))  # generator -> materialize
sub_classes = set(reasoner.sub_classes(cls, direct=True))
super_classes = set(reasoner.super_classes(cls, direct=False))
equiv = set(reasoner.equivalent_classes(cls))
disjoint = set(reasoner.disjoint_classes(cls))
children = set(reasoner.object_property_values(individual, prop))
values = set(reasoner.data_property_values(individual, data_prop))
```

## StructuralReasoner (no JVM, legacy — see #205)

```python
from owlapy.owl_reasoner import StructuralReasoner
from owlapy.owl_ontology import Ontology
from owlapy.class_expression import OWLClass

reasoner = StructuralReasoner(Ontology("KGs/Family/father.owl"))  # or pass a path directly
instances = set(reasoner.instances(OWLClass("http://example.com/father#male")))  # generator -> materialize
sub_classes = set(reasoner.sub_classes(cls, direct=True))
super_classes = set(reasoner.super_classes(cls, direct=False))
equiv = set(reasoner.equivalent_classes(cls))
disjoint = set(reasoner.disjoint_classes(cls))
children = set(reasoner.object_property_values(individual, prop))
values = set(reasoner.data_property_values(individual, data_prop))
```

## SyncReasoner (Java, requires JVM)

```python
from owlapy.owl_reasoner import SyncReasoner
from owlapy.static_funcs import stopJVM

sync_reasoner = SyncReasoner(ontology="KGs/Family/family-benchmark_rich_background.owl", reasoner="Pellet")
instances = sync_reasoner.instances(ce)
subs = sync_reasoner.sub_classes(cls, direct=False)
stopJVM()   # ALWAYS — every code path, including exceptions
```

## Ontology Enrichment

```python
sync_reasoner.infer_axioms_and_save(
    output_path="enriched.ttl", output_format="ttl",
    inference_types=["InferredClassAssertionAxiomGenerator", "InferredSubClassAxiomGenerator"],  # omit for all
)
stopJVM()
```

## Justifications

```python
from owlapy import manchester_to_owl_expression
target = manchester_to_owl_expression("hasChild some Female", namespace)
justifications = reasoner.create_justifications({individual}, target, save=True)
stopJVM()
```

## CLI

```bash
owlapy --path_ontology "KGs/Family/family-benchmark_rich_background.owl" --inference_types "all" --out_ontology "enriched_family.owl"
```

## Constraints

- **Always call `stopJVM()`** after any Java-backed reasoner (`SyncReasoner`); `StructuralReasoner` and `RDFLibReasoner` never need it
- `instances()` returns a generator — wrap in `set()`/`list()`
- ELK only supports the EL fragment
- Prefer `RDFLibReasoner` for speed on large ontologies when incompleteness is acceptable — it has no owlready2/JVM dependency and no circular sub/super-class dependency issue, unlike `StructuralReasoner` (legacy, #205). Use `SyncReasoner` with HermiT/Pellet for DL-complete results and SWRL
