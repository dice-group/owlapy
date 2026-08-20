---
paths:
  - "owlapy/owl_reasoner.py"
  - "owlapy/owl_reasoner_rdflib.py"
  - "owlapy/parallel_reasoner.py"
  - "owlapy/static_funcs.py"
  - "tests/test_owlapy_structural_reasoner.py"
  - "tests/test_sync_reasoner.py"
  - "tests/test_rdflib_reasoner*.py"
  - "tests/test_reasoner_*.py"
  - "tests/test_parallel_reasoner.py"
  - "tests/test_ontology_justification.py"
---

# OWL Reasoning

| Reasoner | Class | Backend | Notes |
|---|---|---|---|
| `RDFLibReasoner` | `owlapy.owl_reasoner_rdflib.RDFLibReasoner` | rdflib (pure Python) | No JVM, no owlready2. **Preferred over `StructuralReasoner`** (#205) |
| `StructuralReasoner` | `owlapy.owl_reasoner.StructuralReasoner` | owlready2 (pure Python) | **Legacy**, being phased out (#205). Fast, incomplete, no JVM. Constructing one emits `DeprecationWarning` |
| `SyncReasoner("HermiT"\|"Pellet"\|"JFact"\|"Openllet"\|"Structural")` | `owlapy.owl_reasoner.SyncReasoner` | Java/OWLAPI | Complete DL reasoning |
| `SyncReasoner("ELK")` | same | Java/OWLAPI | EL fragment only, very fast, no universals/nominals/inverses |
| `EBR` | `owlapy.owl_reasoner.EBR` | `dicee`/PyTorch (pure Python) | Neural embedding-based instance prediction, not DL-complete; needs a `NeuralOntology` (pretrained KGE model) |
| `ParallelReasoner` | `owlapy.parallel_reasoner.ParallelReasoner` | Java/OWLAPI, multiprocessing | Fans out one query's individuals across a process pool. `direct=False` only. Usually *slower* than `SyncReasoner` -- see caveat below |
| `BatchParallelReasoner` | `owlapy.parallel_reasoner.BatchParallelReasoner` | Java/OWLAPI, multiprocessing | Fans out many *different* queries across a process pool, each running its own bulk call. Wins with slow-bulk-call reasoners (e.g. HermiT), loses with fast ones (e.g. Pellet) -- see caveat below |

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

## EBR (embedding-based, no JVM, requires `dicee`)

```python
from owlapy.owl_ontology import NeuralOntology
from owlapy.owl_reasoner import EBR
from owlapy.class_expression import OWLClass

neural_onto = NeuralOntology("path/to/pretrained_kge_model")  # or train_if_not_exists=True from a KG/.owl path
reasoner = EBR(ontology=neural_onto)
predicted = set(reasoner.instances(OWLClass("http://example.com/father#male")))  # score-thresholded by gamma (default 0.5)
predictions = reasoner.predict(h=["http://example.com/father#john"], r=None, t=None)  # raw (h, r, t) predictions w/ scores
```

## ParallelReasoner (Java, multiprocessing, no ontology partitioning)

```python
from owlapy.parallel_reasoner import ParallelReasoner

with ParallelReasoner("KGs/Family/father.owl", reasoner="Pellet", num_workers=8) as pr:
    result = pr.instances(ce)  # set[OWLNamedIndividual]
```

Each worker process loads the full, unpartitioned ontology and starts its own JVM +
`SyncReasoner`. `KB |= ce(a)` is checked per individual (via `is_entailed` on a
`ClassAssertionAxiom`) and results are unioned, so the answer is identical to a
single-process `SyncReasoner.instances(ce, direct=False)` call -- just computed
concurrently. `direct=True` raises `NotImplementedError` (a "direct" instance requires
comparing against every other candidate type, which isn't a single entailment check).
No `stopJVM()` call needed in the caller's process -- each worker tears down its own
JVM on exit; call `.close()` (or exit the `with` block) to shut the pool down.

**Performance: do not reach for this by default.** Benchmarked in `benchmarks/parallel_reasoner/`
(100 generated complex-DL expressions per dataset, HermiT + Pellet, small + large ABox): it was
*slower* than plain `SyncReasoner.instances()` in 3 of 4 tested configurations -- up to 670x
slower on a 14K-individual ABox with Pellet -- because Pellet/HermiT's bulk `getInstances()`
already reuses shared internal structure (classified TBox, completion-graph state) across
individuals far more efficiently than N independent `is_entailed()` calls can, and per-worker
parallelism didn't come close to closing that gap. It only won (1.33x) on a small ABox (~200
individuals) with HermiT specifically, where bulk retrieval happened to be inefficient enough
relative to per-individual checking that decomposition was already a sequential win before
parallelism was applied. Profile your specific (ontology, reasoner) pair before using this in
place of `SyncReasoner`; see the benchmark report for the full results and root-cause analysis.

## BatchParallelReasoner (Java, multiprocessing, parallel across queries not individuals)

```python
from owlapy.parallel_reasoner import BatchParallelReasoner

with BatchParallelReasoner("KGs/Family/father.owl", reasoner="Pellet", num_workers=8) as bpr:
    results = bpr.instances_batch([ce1, ce2, ce3])  # list[set[OWLNamedIndividual]], same order as input
```

Sibling to `ParallelReasoner`, same worker-pool lifecycle (own JVM + `SyncReasoner` per
worker, lazy pool startup, `.close()`/context manager teardown), but parallelizes across the
*query set* instead of one query's individuals: each worker runs its own full, un-decomposed
`SyncReasoner.instances(ce)` bulk call for a different expression. A per-expression reasoner
failure (e.g. a Java-internal reasoner bug) is caught and logged, returning an empty set for
that expression rather than aborting the whole batch.

**Performance: a real win, but only when the reasoner's bulk calls are individually expensive.**
Benchmarked the same way as `ParallelReasoner` (`benchmarks/parallel_reasoner/`): 2.03x-5.04x
faster than sequential `SyncReasoner` calls with HermiT (both a 202- and a 14K-individual
ABox), but 0.16x-0.69x (i.e. *slower*) with Pellet on the same two datasets, because Pellet's
bulk calls are already fast enough (tens to hundreds of ms) that starting 22 JVMs, plus
resource contention among that many concurrently-reasoning JVMs, isn't amortized. Profile a
handful of sequential bulk calls first -- well under ~100ms average means sequential
`SyncReasoner` calls in a loop are very likely faster than either parallel strategy here.

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

- **Always call `stopJVM()`** after any Java-backed reasoner (`SyncReasoner`); `StructuralReasoner`, `RDFLibReasoner`, and `EBR` never need it
- `instances()` returns a generator — wrap in `set()`/`list()`
- ELK only supports the EL fragment
- Prefer `RDFLibReasoner` for speed on large ontologies when incompleteness is acceptable — it has no owlready2/JVM dependency and no circular sub/super-class dependency issue, unlike `StructuralReasoner` (legacy, #205). Use `SyncReasoner` with HermiT/Pellet for DL-complete results and SWRL
- `EBR` isn't a symbolic/DL reasoner — its results are probabilistic embedding predictions, not logical entailments; equivalence/disjointness/same-individuals queries raise `NotImplementedError`
