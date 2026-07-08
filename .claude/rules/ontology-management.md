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
from owlapy.owl_ontology import SyncOntology, Ontology, NeuralOntology
from owlapy.util_owl_static_funcs import create_ontology, csv_to_rdf_kg, save_owl_class_expressions

onto = SyncOntology("path/to/ontology.owl")            # preferred: thread-safe owlready2 wrapper
onto = Ontology("path/to/ontology.owl")                  # lower-level owlready2-backed
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
onto.save(path="output.ttl", rdf_format="ttl", inplace=False)
```

## CSV -> RDF and Saving Class Expressions

```python
csv_to_rdf_kg(path_csv="data.csv", path_kg="kg.owl", namespace="http://myproject.com/kg")
save_owl_class_expressions(expressions=[expr1, expr2], path="predictions.owl",
                            rdf_format="rdfxml", namespace="https://dice-research.org/predictions#")
```

## Constraints

- Use full IRIs or `IRI.create(namespace, remainder)` when constructing entities — never bare strings
- `SyncOntology` is preferred for most use cases; `Ontology` is the lower-level class
- `create_ontology` paths need a valid file URI scheme (e.g. `"file:/path.owl"`)
- Don't pass `with_owlapi=True` unless Java/OWLAPI interop is explicitly needed — it starts a JVM (see `.claude/rules/owlapi-swrl.md`)
