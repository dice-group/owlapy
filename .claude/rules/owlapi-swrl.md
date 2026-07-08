---
paths:
  - "owlapy/swrl.py"
  - "owlapy/owlapi_mapper.py"
  - "owlapy/owlapi_dlsyntax.py"
  - "owlapy/static_funcs.py"
  - "tests/test_swrl.py"
  - "tests/test_owlapi_dlsyntax.py"
  - "tests/test_owlapi_mapper.py"
---

# OWLAPI Bridge and SWRL Rules

## JVM Lifecycle

```python
from owlapy.static_funcs import startJVM, stopJVM
startJVM()   # usually automatic (SyncReasoner, Ontology(with_owlapi=True))
stopJVM()    # ALWAYS call when done — every path, including exceptions
```

```python
from owlapy.owlapi_mapper import OWLAPIMapper   # owlapy <-> OWLAPI Java object mapping
from owlapy.owlapi_dlsyntax import OWLAPIRenderer  # DL rendering via OWLAPI's own renderer
onto = SyncOntology("KGs/Family/father.owl", with_owlapi=True)  # starts JVM
```

## SWRL

```python
from owlapy.swrl import Rule, Atom, ClassAtom, ObjectPropertyAtom, DataPropertyAtom, BuiltInAtom, IVariable, DVariable
from owlapy.iri import IRI

x = IVariable(IRI.create("urn:swrl:var#", "x"))   # individual/object variable
v = DVariable(IRI.create("urn:swrl:var#", "v"))   # data/literal variable

person_atom = ClassAtom(OWLClass(NS + "Person"), x)
has_child_atom = ObjectPropertyAtom(OWLObjectProperty(NS + "hasChild"), x, y)
age_atom = DataPropertyAtom(OWLDataProperty(NS + "age"), x, v)
builtin_atom = BuiltInAtom(IRI.create("http://www.w3.org/2003/11/swrlb#", "greaterThan"), [v, OWLLiteral(18)])

# Person(?x) ∧ hasChild(?x,?y) ∧ Male(?y) -> Father(?x)
rule = Rule(body_atoms=[person_atom, has_child_atom, male_atom], head_atoms=[father_atom])
onto.add_axiom(rule)   # SWRL rules are added like any other axiom
onto.save(inplace=True)
```

Common built-ins (base `http://www.w3.org/2003/11/swrlb#`): `greaterThan`, `lessThan`,
`greaterThanOrEqual`, `lessThanOrEqual`, `equal`, `add`, `subtract`, `multiply`, `divide`,
`stringConcat`, `matches`.

Retrieving rules: they appear as axioms in `onto.get_tbox_axioms()`; check `isinstance(axiom, Rule)`.
`axiom.body` / `axiom.head` are properties, not methods.

## Constraints

- OWLAPI bridge always requires a JVM — call `stopJVM()` when done
- Variable IRIs must be unique within a rule; convention is `urn:swrl:var#<name>`
- `IVariable` for individuals/objects, `DVariable` for literals
- SWRL rules are only honored by complete reasoners (HermiT, Pellet), never `StructuralReasoner`
