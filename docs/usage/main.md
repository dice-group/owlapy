# About owlapy

**Version:** owlapy 1.4.0

**GitHub repository:** [https://github.com/dice-group/owlapy](https://github.com/dice-group/owlapy)

**Publisher and maintainer:** [DICE](https://dice-research.org/) - data science research group of [Paderborn University](https://www.uni-paderborn.de/en/university).

**Contact**: [onto-learn@lists.uni-paderborn.de](mailto:onto-learn@lists.uni-paderborn.de)

**License:** MIT License

--------------------------------------------------------------------------------------------
## What is owlapy?

Owlapy is an open-source Python library designed for representing and manipulating OWL 2 ontologies, offering a robust 
foundation for knowledge graph and class expression learning projects in machine learning. Inspired by [OWLAPI](https://github.com/owlcs/owlapi)
(which is also available to use in this library via synchronisation), Owlapy enables ontology creation,
modification, and reasoning while supporting OWL 2 Structural Specification, Functional-Style Syntax, and advanced 
features such as parsing and rendering to Description Logics and Manchester syntax. With capabilities to convert OWL 
expressions into SPARQL queries and interfaces for ontology and reasoning, Owlapy is a powerful tool used in powerful 
libraries like [Ontolearn](https://github.com/dice-group/Ontolearn) and [OntoSample](https://github.com/alkidbaci/OntoSample).

---------------------------------------

## What does owlapy have to offer?
- Create, manipulate and save Ontologies.
- Retrieving information from the signature of the ontology.
- Reasoning over ontology.
- Represent every notation in 
[OWL 2 Structural Specification and Functional-Style Syntax](https://www.w3.org/TR/owl2-syntax/)
including: 
  - Entities, Literals, and Anonymous Individuals
  - Property Expressions
  - Data Ranges
  - Class Expressions
  - Axioms
  - Annotations
- Construct complex class expressions.
- Provide interfaces for OWL Ontology and Reasoner.
- Convert owl expression to SPARQL queries.
- Render owl expression to Description Logics or Manchester syntax.
- Parse Description Logics or Manchester expression to owl expression.
- **Makes _OWLAPI_ available to be easily used in Python.**


## How to install?

Installation from source:
``` bash
git clone https://github.com/dice-group/owlapy
conda create -n temp_owlapy python=3.10.13 --no-default-packages && conda activate temp_owlapy && pip3 install -e .
```

or using PyPI:
```bash
pip3 install owlapy
```