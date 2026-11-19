---
paths:
  - "owlapy/owl_ontology.py"
  - "owlapy/util_owl_static_funcs.py"
  - "owlapy/owl_axiom.py"
  - "tests/test_ontology.py"
  - "tests/test_sync_ontology*.py"
  - "tests/test_owlapy_ontology_management.py"
  - "tests/test_owl_static_funcs.py"
  - "tests/test_owl_hierarchy.py"
---

# Ontology Management

```python
from owlapy.owl_ontology import SyncOntology, RDFLibOntology, NeuralOntology
from owlapy.util_owl_static_funcs import csv_to_rdf_kg, save_owl_class_expressions

onto = SyncOntology("path/to/ontology.owl")            # thread-safe, Java OWL API-backed (needs the JVM); full read/write
onto = RDFLibOntology("path/to/ontology.owl")            # pure Python (rdflib), no JVM/owlready2; reads and writes complex class expressions too (#205, #310)
onto = NeuralOntology("path/to/pretrained_kge_model")     # embedding-backed (requires `dicee`); pairs with the EBR reasoner, see .claude/rules/reasoning.md
onto = RDFLibOntology("http://example.com/my_ontology", load=False)  # new, empty ontology (SyncOntology(iri, load=False) for the OWL API)
```

## Signature and Axioms

```python
onto.classes_in_signature() / individuals_in_signature() / object_properties_in_signature() / data_properties_in_signature()
onto.get_tbox_axioms()   # schema/class-level
onto.get_abox_axioms()   # assertions/individual-level
onto.equivalent_classes_axioms(cls); onto.general_class_axioms()
onto.data_property_domain_axioms(prop); onto.data_property_range_axioms(prop)
onto.object_property_domain_axioms(prop); onto.object_property_range_axioms(prop)
onto.annotation_assertion_axioms(entity)  # rdfs:label/rdfs:comment/etc. on entity (or its IRI directly); SyncOntology and RDFLibOntology only
```

## Membership Checks (SyncOntology only)

Java-side OWL API checks exposed on Python side (#278) -- prefer these over scanning
`*_in_signature()`/`get_*_axioms()` by hand:

```python
onto.get_axioms()            # all axioms (vs. get_abox/tbox/rbox_axioms() for a subset)
onto.contains_axiom(axiom)   # bool, imports excluded

# each accepts either the named entity (OWLClass/OWLObjectProperty/...) or its IRI/IRI string
onto.contains_class_in_signature(cls_or_iri)
onto.contains_object_property_in_signature(prop_or_iri)
onto.contains_data_property_in_signature(prop_or_iri)
onto.contains_annotation_property_in_signature(prop_or_iri)
onto.contains_individual_in_signature(ind_or_iri)

onto.is_declared(entity)     # has a declaration axiom for this entity
onto.get_punned_iris()       # IRIs used as more than one entity type
```

All of the above take `include_imports_closure: bool = True`, matching `get_abox_axioms()` et al.

Add/remove axioms with `onto.add_axiom([...])` / `onto.remove_axiom(axiom)`. Common axiom types
(`owlapy.owl_axiom`): `OWLDeclarationAxiom`, `OWLClassAssertionAxiom(ind, cls)`,
`OWLObjectPropertyAssertionAxiom(subj, prop, obj)`, `OWLDataPropertyAssertionAxiom(subj, prop, literal)`,
`OWLSubClassOfAxiom(sub, super)`, `OWLEquivalentClassesAxiom([...])`, `OWLDisjointClassesAxiom([...])`,
`OWLObjectPropertyDomainAxiom`/`RangeAxiom`, `OWLSubPropertyAxiom`.

## Saving

```python
onto.save(inplace=True)
onto.save(path="output.owl", inplace=False)
onto.save(path="output.ttl", document_format="ttl", inplace=False)
```

## Prefix Management (SyncOntology only)

```python
onto.get_prefixes()                              # -> {"owl": "...", "rdf": "...", ...}
onto.set_prefix("foaf", "http://xmlns.com/foaf/0.1/")
onto.remove_prefix("foaf")
```

Custom prefixes are honoured by `save()` for both OWL API–backed formats that support them
(RDF/XML, OWL/XML, Turtle, Functional Syntax, Manchester Syntax) and the rdflib-backed formats
(`turtle2`, `n3`, `trig`, `json-ld`); without a registered prefix, entities from that namespace
serialize as full IRIs.

## CSV -> RDF and Saving Class Expressions

```python
csv_to_rdf_kg(path_csv="data.csv", path_kg="kg.owl", namespace="http://myproject.com/kg")
save_owl_class_expressions(expressions=[expr1, expr2], path="predictions.owl",
                            rdf_format="rdfxml", namespace="https://dice-research.org/predictions#")
```

## Constraints

- Use full IRIs or `IRI.create(namespace, remainder)` when constructing entities — never bare strings
- `SyncOntology` is preferred when you need Java-backed reasoning; `RDFLibOntology` is preferred for pure-Python read/write use (no JVM/owlready2) -- never write new code against the owlready2-backed `Ontology`/`StructuralReasoner`/`ToOwlready2`/`FromOwlready2`: deprecated, removed in 2.0, replacements in `markdown_docs/10_migrating_from_owlready2.md` (#310)
- `RDFLibOntology.add_axiom()` writes complex class expressions/data ranges (restrictions, boolean combinations, cardinalities, nominals, datatype restrictions) via the W3C OWL 2 -> RDF mapping, and the read API (`get_tbox_axioms()`, `equivalent_classes_axioms()`, `general_class_axioms()`, domain/range, class assertions) rebuilds them from the blank-node structures (#310); unreadable ones (anonymous individuals) are skipped with one logged warning per call. `remove_axiom()` raises `NotImplementedError` on an axiom with a complex operand. Both also raise on a handful of axiom types not yet covered (e.g. `OWLSameIndividualAxiom`, `OWLDisjointUnionAxiom`) -- the error message states what's supported. Annotation axioms (`OWLAnnotationAssertionAxiom` on an IRI with an IRI/literal value, `OWLSubAnnotationPropertyOfAxiom`, `OWLAnnotationProperty{Domain,Range}Axiom`) are written and removed; custom annotation properties are auto-declared, built-ins like `rdfs:label` are not; anonymous individuals raise `NotImplementedError`; annotations *on an axiom* are silently dropped (true for every axiom type). `RDFLibOntology(iri, load=False)` creates a blank ontology at the given IRI
- `create_ontology(iri)` (without `with_owlapi=True`) returns the deprecated `Ontology` and emits a `FutureWarning`; construct `RDFLibOntology(iri, load=False)` directly instead
- Don't pass `with_owlapi=True` unless Java/OWLAPI interop is explicitly needed — it starts a JVM (see `.claude/rules/owlapi-swrl.md`)
- `owlready2` is an optional install extra (`pip install owlapy[owlready2]`), not a hard dependency (#205) — constructing an `Ontology` (or a `StructuralReasoner`) without it installed raises a clear `ImportError`; `SyncOntology`/`RDFLibOntology` are unaffected either way
