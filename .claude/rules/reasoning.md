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
| `EBR` | `owlapy.owl_reasoner.EBR` | `dicee`/PyTorch (pure Python) | Neural embedding-based instance prediction, not DL-complete; needs a `NeuralOntology` (pretrained KGE model) |
| `NIRReasoner` | `owlapy.owl_reasoner.NIRReasoner` | NIR encoder in `owlapy.nir` + entity embeddings (pure Python) | Neural instance retrieval for complex class expressions; TBox delegated to StructuralReasoner/RDFLibReasoner. Needs `torch` + `transformers`, a pretrained encoder directory, and an embeddings CSV |

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

## NIRReasoner (neural instance retrieval, no JVM)

```python
from owlapy.owl_ontology import Ontology
from owlapy.owl_reasoner import NIRReasoner
from owlapy.class_expression import OWLClass

onto = Ontology("KGs/Family/family-benchmark_rich_background.owl")
reasoner = NIRReasoner(
    onto,
    model_path="trained_models/nir_pretrained_models/NIR_Transformer_family",
    embeddings_path="trained_models/embeddings/family/DeCaL_entity_embeddings.csv",
    th=0.5,
)
instances = set(reasoner.instances(OWLClass("http://www.benchmark.org/family#Brother")))
```

Download pretrained encoders and DeCaL embeddings:

```shell
wget https://files.dice-research.org/datasets/CNIR/trained_models.zip -O ./trained_models.zip && unzip trained_models.zip
```

- Named / length-1 concepts go to the symbolic fallback; longer expressions are scored by the NIR encoder.
- Hierarchies and roles are always symbolic. Results are score-thresholded, not DL-entailed.
- No `stopJVM()`.

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
