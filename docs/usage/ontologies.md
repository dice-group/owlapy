# Ontologies
To get started with Structured Machine Learning, the first thing
required is an [Ontology](https://www.w3.org/TR/owl2-overview/) with
[Named Individuals](https://www.w3.org/TR/owl-syntax/#Named_Individuals).
In this guide we show the basics of working with ontologies in Owlapy.
We will use the _father_ ontology for the following examples. 

## Loading an Ontology

To load an ontology you can use an implementor of 
[AbstractOWLOntology](owlapy.abstracts.abstract_owl_ontology).
An ontology can be loaded using the following Python code:

```python
from owlapy.iri import IRI
from owlapy.owl_ontology import Ontology

onto = Ontology(IRI.create("file://KGs/Family/father.owl"), load=True)
```

To load an ontology from your local machine, you can use the `IRI` class which 
should be created using a file path or just specify the path of the file storing
the ontology directly (`.owl` format is recommended). In the `Ontology` class you can
also specify the `load` argument which tells the system whether you are trying to load an
existing ontology or creating a new one.

Now, you can already inspect the contents of the ontology. For example,
list all individuals:

<!--pytest-codeblocks:cont-->
```python
for ind in onto.individuals_in_signature():
    print(ind)
```

You can get the object properties in the signature:

<!--pytest-codeblocks:cont-->
```python
onto.object_properties_in_signature()
```

For more methods, see the abstract class [AbstractOWLOntology](owlapy.abstracts.abstract_owl_ontology)
or one of the concrete implementation [Ontology](owlapy.owl_ontology.Ontology), [SyncOntology](owlapy.owl_ontology.SyncOntology),
[RDFLibOntology](owlapy.owl_ontology.RDFLibOntology).

## Modifying an Ontology

Axioms in ontology serve as the basis for defining the vocabulary of a domain and for 
making statements about the relationships between individuals and concepts in that domain.
They provide a formal and precise way to represent knowledge and allow for automated 
reasoning and inference. Axioms can be **added**, **modified**, or **removed** from an ontology, 
allowing the ontology to evolve and adapt as new knowledge is gained.

In owlapy we represent different axioms by different classes. You can check all
the axioms classes [here](owlapy.owl_axioms). Some frequently used axioms are:

- [OWLDeclarationAxiom](owlapy.owl_axiom.OWLDeclarationAxiom)
- [OWLObjectPropertyAssertionAxiom](owlapy.owl_axiom.OWLObjectPropertyAssertionAxiom)
- [OWLDataPropertyAssertionAxiom](owlapy.owl_axiom.OWLDataPropertyAssertionAxiom)
- [OWLClassAssertionAxiom](owlapy.owl_axiom.OWLClassAssertionAxiom)
- [OWLSubClassOfAxiom](owlapy.owl_axiom.OWLSubClassOfAxiom)
- [OWLEquivalentClassesAxiom](owlapy.owl_axiom.OWLEquivalentClassesAxiom)


#### Add a new Class

Let's suppose you want to add a new class in our example ontology `KGs/Family/father.owl` 
It can be done as follows:

<!--pytest-codeblocks:cont-->

```python
from owlapy.class_expression import OWLClass
from owlapy.owl_axiom import OWLDeclarationAxiom

iri = IRI('http://example.com/father#', 'child')
child_class = OWLClass(iri)
child_class_declaration_axiom = OWLDeclarationAxiom(child_class)

onto.add_axiom(child_class_declaration_axiom)
```
In this example, we added the class 'child' to the _father.owl_ ontology.
Firstly we create an instance of [OWLClass](owlapy.class_expression.owl_class.OWLClass) to represent the concept 
of 'child' by using an [IRI](owlapy.iri.IRI). 
On the other side, an instance of `IRI` is created by passing two arguments which are
the namespace of the ontology and the remainder 'child'. To declare this new class we need
an axiom of type `OWLDeclarationAxiom`. We simply pass the `child_class` to create an 
instance of this axiom. The final step is to add this axiom to the ontology
We use the `add_axiom` method to add into the ontology
`onto` the axiom `child_class_declaration_axiom`.

#### Add a new Object Property / Data Property

The idea is the same as adding a new class. Instead of `OWLClass`, for object properties,
you can use the class [OWLObjectProperty](owlapy.owl_property.OWLObjectProperty) and for data
properties you can use the class [OWLDataProperty](owlapy.owl_property.OWLDataProperty).

<!--pytest-codeblocks:cont-->

```python
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty

# adding the object property 'hasParent'
hasParent_op = OWLObjectProperty(IRI('http://example.com/father#', 'hasParent'))
hasParent_op_declaration_axiom = OWLDeclarationAxiom(hasParent_op)
onto.add_axiom(hasParent_op_declaration_axiom)

# adding the data property 'hasAge' 
hasAge_dp = OWLDataProperty(IRI('http://example.com/father#', 'hasAge'))
hasAge_dp_declaration_axiom = OWLDeclarationAxiom(hasAge_dp)
onto.add_axiom(hasAge_dp_declaration_axiom)
```

See the [owlapy](owlapy) API for more OWL entities that you can add as a declaration axiom.

#### Add an Assertion Axiom

To assign a class to a specific individual use the following code:

<!--pytest-codeblocks:cont-->

```python
from owlapy.owl_axiom import OWLClassAssertionAxiom

individuals = list(onto.individuals_in_signature())
heinz = individuals[1]  # get the 2nd individual in the list which is 'heinz'

class_assertion_axiom = OWLClassAssertionAxiom(heinz, child_class)

onto.add_axiom(class_assertion_axiom)
```
We have used the previous method `individuals_in_signature()` to get all the individuals 
and converted them to a list, so we can access them by using indexes. In this example, we
want to assert a class axiom for the individual `heinz`. 
We have used the class `OWLClassAssertionAxiom`
where the first argument is the 'individual' `heinz` and the second argument is 
the 'class_expression'. As the class expression, we used the previously defined class 
`child_Class`. Finally, add the axiom by using `add_axiom` method of the [AbstractOWLOntology](owlapy.abstracts.abstract_owl_ontology).

Let's show one more example using a `OWLDataPropertyAssertionAxiom` to assign the age of 17 to
heinz. 

<!--pytest-codeblocks:cont-->

```python
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_axiom import OWLDataPropertyAssertionAxiom

literal_17 = OWLLiteral(17)
dp_assertion_axiom = OWLDataPropertyAssertionAxiom(heinz, hasAge_dp, literal_17)

onto.add_axiom(dp_assertion_axiom)
```

[OWLLiteral](owlapy.owl_literal.OWLLiteral) is a class that represents the literal values in
Owlapy. We have stored the integer literal value of '17' in the variable `literal_17`.
Then we construct the `OWLDataPropertyAssertionAxiom` by passing as the first argument, the 
individual `heinz`, as the second argument the data property `hasAge_dp`, and the third 
argument the literal value `literal_17`. Finally, add it to the ontology by using `add_axiom` 
method.

Check the [owlapy](owlapy) to see all the OWL 
assertion axioms that you can use.


#### Remove an Axiom

To remove an axiom you can use the `remove_axiom` method as follows:

<!--pytest-codeblocks:cont-->
```python
onto.remove_axiom(dp_assertion_axiom)
```
The required argument is the axiom/axioms you want to remove.


## Save an Ontology

If you modified an ontology, you may want to save it as a new file. To do this
you can use the `save` method of the [AbstractOWLOntology](owlapy.abstracts.abstract_owl_ontology).
It requires one argument, the IRI of the new ontology.

<!--pytest-codeblocks:cont-->
```python
onto.save(IRI.create('file:/' + 'test' + '.owl'))
```
The above line of code will save the ontology `onto` in the file *test.owl* which will be
created in the same directory as the file you are running this code.


## Worlds

Owlready2 stores every triple in a ‘World’ object, and it can handle several Worlds in parallel.
Owlready2 uses an optimized quadstore to store the world. Each world object is stored in a separate quadstore and 
by default the quadstore is stored in memory,
but it can also be stored in an SQLite3 file. In owlapy we have deprecated OntologyManager
and when an ontology is created a new world is also created to be associated with it.
However, you can still load an ontology to a specific world using the method `load_ontology(iri)`.
-------------------------------------------------------------------------------------

It is essential to associate an ontology with a reasoner, which enables the inference of new knowledge through ontology
reasoning. In the next guide, we will explore how to use a reasoner in Owlapy.




