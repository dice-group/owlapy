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
from owlapy.owl_ontology import SyncOntology, RDFLibOntology, Ontology, NeuralOntology
from owlapy.util_owl_static_funcs import create_ontology, csv_to_rdf_kg, save_owl_class_expressions

onto = SyncOntology("path/to/ontology.owl")            # thread-safe, Java OWL API-backed (needs the JVM); full read/write
onto = RDFLibOntology("path/to/ontology.owl")            # pure Python (rdflib), no JVM/owlready2; read/write, named entities only (#205)
onto = Ontology("path/to/ontology.owl")                  # owlready2-backed; legacy, being phased out in favor of RDFLibOntology (#205)
onto = create_ontology("file:/my_ontology.owl", with_owlapi=False)
```

## Signature and Axioms

```python
onto.classes_in_signature() / individuals_in_signature() / object_properties_in_signature() / data_properties_in_signature()
onto.get_tbox_axioms()   # schema/class-level
onto.get_abox_axioms()   # assertions/individual-level
onto.equivalent_classes_axioms(cls); onto.general_class_axioms()
onto.data_property_domain_axioms(prop); onto.data_property_range_axioms(prop)
onto.object_property_domain_axioms(prop); onto.object_property_range_axioms(prop)
```

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
- `SyncOntology` is preferred when you need Java-backed reasoning; `RDFLibOntology` is preferred for pure-Python read/write use (no JVM/owlready2), but only between *named* entities -- `Ontology` (owlready2-backed) is legacy, being phased out (#205)
- `RDFLibOntology.add_axiom()`/`remove_axiom()`/`general_class_axioms()` raise `NotImplementedError` on axioms involving complex (blank-node) class/property expressions or general class axioms, and on a handful of axiom types not yet covered (e.g. `OWLSameIndividualAxiom`, `OWLAnnotationAssertionAxiom`) -- the error message states what's supported. `RDFLibOntology(iri, load=False)` creates a blank ontology at the given IRI
- `create_ontology` paths need a valid file URI scheme (e.g. `"file:/path.owl"`)
- Don't pass `with_owlapi=True` unless Java/OWLAPI interop is explicitly needed — it starts a JVM (see `.claude/rules/owlapi-swrl.md`)
- `owlready2` is an optional install extra (`pip install owlapy[owlready2]`), not a hard dependency (#205) — constructing an `Ontology` (or a `StructuralReasoner`) without it installed raises a clear `ImportError`; `SyncOntology`/`RDFLibOntology` are unaffected either way
