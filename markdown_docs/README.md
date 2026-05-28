# owlapy Documentation for LLMs

This directory contains comprehensive, LLM-friendly documentation for the owlapy framework (v1.6.5).

## About owlapy

owlapy is a production-ready Python framework for OWL ontology engineering, knowledge graph development, and semantic reasoning. Developed by the DICE Research Group at Paderborn University.

## Documentation Structure

### Getting Started
- [01_getting_started.md](01_getting_started.md) - Installation, dependencies, and quick start guide

### Core Concepts
- [02_core_concepts.md](02_core_concepts.md) - OWL fundamentals, ontologies, reasoners, class expressions
- [03_ontology_management.md](03_ontology_management.md) - Creating, loading, saving, and modifying ontologies
- [04_class_expressions.md](04_class_expressions.md) - Building and using OWL class expressions

### Advanced Features
- [05_reasoning.md](05_reasoning.md) - Semantic reasoning with StructuralReasoner, RDFLibReasoner, and SyncReasoner
- [06_syntax_conversion.md](06_syntax_conversion.md) - Converting between DL syntax, Manchester syntax, and SPARQL
- [07_knowledge_graph_generation.md](07_knowledge_graph_generation.md) - LLM-based ontology generation with AGenKG

### Practical Guides
- [08_common_patterns.md](08_common_patterns.md) - Common use cases, patterns, and anti-patterns
- [09_api_reference.md](09_api_reference.md) - Quick reference for all key classes and functions
- [10_migration_guide.md](10_migration_guide.md) - Migrating from other OWL libraries and upgrading owlapy

## Key Features

- **Pure Python OWL 2 implementation** - No Java dependencies for core functionality
- **Multiple reasoners** - StructuralReasoner (fast), RDFLibReasoner (pure Python), SyncReasoner (complete)
- **Syntax conversion** - DL ↔ Manchester ↔ SPARQL
- **LLM integration** - Generate ontologies from text using AGenKG
- **Rich class expressions** - Full OWL 2 DL support

## Quick Example

```python
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner import RDFLibReasoner
from owlapy.class_expression import OWLClass

# Load ontology
onto = SyncOntology("family.owl")

# Create reasoner
reasoner = RDFLibReasoner(onto)

# Query instances
male_class = OWLClass("http://example.com/family#Male")
males = set(reasoner.instances(male_class))
print(f"Found {len(males)} male individuals")
```

## Repository Structure

```
owlapy/
├── class_expression/       # OWL class expression types
├── owl_ontology.py         # SyncOntology, Ontology, NeuralOntology
├── owl_reasoner.py         # StructuralReasoner, SyncReasoner
├── owl_reasoner_rdflib.py  # RDFLibReasoner (pure Python)
├── converter.py            # OWL → SPARQL conversion
├── parser.py               # DL/Manchester → OWL parsing
├── render.py               # OWL → DL/Manchester rendering
├── agen_kg/                # LLM-based ontology generation
└── utils.py                # CESimplifier, NNF, similarity metrics
```

## Version Information

**Current Version:** 1.6.5  
**Python Requirement:** 3.11+  
**Main Dependencies:** owlready2, rdflib (6.0.2+), jpype1 (for Java reasoners)

## Additional Resources

- **GitHub:** https://github.com/dice-group/owlapy
- **PyPI:** https://pypi.org/project/owlapy/
- **Documentation:** https://owlapy.readthedocs.io/
- **Examples:** `examples/` directory in repository
- **Tests:** `tests/` directory in repository
