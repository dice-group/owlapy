# About owlapy

**Version:** owlapy 1.0.1

**GitHub repository:** [https://github.com/dice-group/owlapy](https://github.com/dice-group/owlapy)

**Publisher and maintainer:** [DICE](https://dice-research.org/) - data science research group of [Paderborn University](https://www.uni-paderborn.de/en/university).

**Contact**: [onto-learn@lists.uni-paderborn.de](mailto:onto-learn@lists.uni-paderborn.de)

**License:** GNU Affero General Public License v3 or later (AGPLv3+)

--------------------------------------------------------------------------------------------
## What is owlapy?
Owlapy is an open-source software library in python that is used to represent entities
in OWL 2 Web Ontology Language.

We identified the gap of having a library that will serve as a base structure 
for representing OWL entities in python and like that, owlapy was created. Owlapy 
is loosely based on its java-counterpart, _owlapi_. Owlapy is currently utilized 
by powerful libraries such as [Ontolearn](https://github.com/dice-group/Ontolearn)
and [OntoSample](https://github.com/alkidbaci/OntoSample). 

Owlapy is the perfect choice for machine learning projects that are built in python and
focus on knowledge graphs and class expression learnings. 

---------------------------------------

## What does owlapy have to offer?

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
- Provide interfaces for OWL Ontology, Ontology manager and Reasoner.
- Convert owl expression to SPARQL queries.
- Render owl expression to Description Logics or Manchester syntax.
- Parse Description Logics or Manchester expression to owl expression.


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