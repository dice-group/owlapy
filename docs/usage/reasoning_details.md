# Reasoning Details

In the previous guide we explained how to [use reasoners](reasoner.md) in Owlapy. Here we cover a detailed explanation of 
the Owlapy reasoners, particularly [SyncReasoner](owlapy.owl_reasoner.SyncReasoner).
Before we continue to talk about its [capabilities](#capabilities) we have to explain briefly 
the term _sync_reasoner_.

## Sync Reasoner

_sync_reasoner_ is a definition used in owlready2 to run [HermiT](http://www.hermit-reasoner.com/) 
or [Pellet](https://github.com/stardog-union/pellet) and
automatically apply the facts deduced to the quadstore. In simple terms, by running HermiT or Pellet,
one can infer more knowledge from the ontology (the specification are not mentioned here). 
We make use of this functionality in Owlapy, and it is represented by SyncReasoner. 
We explained the concept of "Worlds" in [Working with Ontologies](ontologies.md#worlds). Having 
that in mind you need to know that sync_reasoner is applied to the World object.
After this particular reasoner is instantiated, because the facts are applied to the quadstore, changes made
in the ontology by using the ontology manager will not be reflected to the ontology. The reasoner will use the state of
the ontology at the moment it is instantiated.

There are 2 boolean parameters for sync_reasoner that you can specify when creating an instance of 
[SyncReasoner](owlapy.owl_reasoner.SyncReasoner).
The first one `infer_property_values` tells HermiT or Pellet whether to infer (or not) property values. The same idea but
for data properties is specified by the parameter `infer_data_property_values` which is only relevant to Pellet.

> Note: HermiT and Pellet are Java programs, so you will need to install
a Java virtual machine to use them. If you don’t have Java, you may install
it from www.java.com (for Windows and macOS) or from the packages
of your Linux distribution (the packages are often named “jre” or “jdk” for
Java Runtime Environment and Java Development Kit).

## Isolated World

In [_Working with Ontologies_](ontologies.md#worlds) we mentioned that we can have multiple reference of in different
worlds, which we can use to isolate an ontology to a specific World. For simplicity the terms "isolated world" and 
"isolated ontology" can be used interchangeably in this guide.
The isolation comes in handy when we use multiple reasoners in the same script. If we create
an instance of _SyncReasoner_ it will apply sync_reasoner in the world object
of the ontology and this will affect also the other reasoner/s which is/are using the same world. 
To overcome this issue you can set the argument `isolate=True` when
initializing a reasoner.
[FastInstanceCheckerReasoner](owlapy.owl_reasoner.FastInstanceCheckerReasoner) (FIC)
does not have this argument because it uses a base reasoner to delegate most of its methods. Therefore,
if the base reasoner has `isolate=True` then FIC will also operate in the isolated world of it's base reasoner.

### Modifying an isolated ontology

When a reasoner is operating in an isolated ontology, every axiom added to the original ontology before or after 
the initialization, will not be reflected to the isolated ontology. To update the isolated ontology and add
or remove any axiom, you can use `update_isolated_ontology(axioms_to_add, axioms_to_remove)`. This method accepts
a list of axioms for every argument (i.e. the axioms that you want to add and the axioms that you want to remove).

## Capabilities

_SyncReasoner_ provides full reasoning in 
_ALCH_. We have adapted and build upon 
[owlready2](https://owlready2.readthedocs.io/en/latest/) reasoner to provide 
our own implementation in python. Below we give more details about each
functionality of our reasoner:


- #### Sub and Super Classes

    You can retrieve sub (super) classes of a given class expression. Depending on
    your preferences you can retrieve the whole chain of sub (super) classes or only the
    direct sub (super) classes (`direct` argument). It is also possible to get anonymous classes in addition
    to named classes (`only_named` argument). Class equivalence entails subsumption of classes to each other.

- #### Equivalent Classes

    You are able to get the equivalent classes of a given class expression. It can be 
    decided whether only named classes should be returned 
    or anonymous classes as well. If two classes are subclasses of each other they
    are considered equivalent.

- #### Disjoint Classes

    Every class that is explicitly defined as disjoint with another class will be returned.
    In addition, every subclass and equivalent class of the disjoint classes will be
    returned. If a target class does not have explicitly-defined disjoint classes the search
    is transferred to the superclasses of that target class.

- #### Equivalent Properties

    You are able to get equivalent properties of a given object or data property.
    If two properties are sub-properties of each other, they are considered equivalent.

- #### Sub and Super Properties

    Our reasoner has support also for sub and super properties of a 
    given property. You can set the `direct` argument like in sub (super) classes.
    Properties equivalence entails subsumption of properties to each other.

- #### Disjoint Properties

    Similarly to disjoint classes, you can get the disjoint properties of a property.
    Same rules apply.

- #### Property values

    Given an individual(instance) and an object property you can get all the object values.
    Similarly, given an individual and a data property you can get all the literal values.
    You can set whether you want only the direct values or all of them.

- #### Property domain and range

    Easily retrieval available for domain and range for object properties and domain for data properties.

- #### Instances

    This functionality enables you to get instances for a given named(atomic) class or complex class expression.
    For the moment direct instances of complex class expressions is not possible.

- #### Types

    This functionality enables you to get the types of a given instance. It returns only
    named(atomic) classes. You can set the `direct` attribute.

- #### Same and Different Individuals

    Given an individual you can get the individuals that are explicitly defined as same or different to that individual.


## Concrete Example

You can find the associated [code](https://github.com/dice-group/owlapy/blob/develop/examples/ontology_reasoning.py) 
for the following examples inside `examples/example_reasoner`
(note that the naming of the classes/relations/individuals may change from the table below). 
We constructed an ontology for testing purposes. On the table we show for
each **method** of the reasoner _SyncReasoner_ the results
depending on a given **TBox** and **Abox**. The level of complexity of the TBox-es is low compared
to real world scenarios, but it's just to show the capabilities of the reasoner.

> **Note:** not every method of the reasoner is used in this example. You can check all the methods at the 
> [API documentation](owlapy.owl_reasoner).


| Method                                    | TBox                      | ABox                  | Returns<br>(T = Thing) |
|-------------------------------------------|---------------------------| --------------------- |------------------------|
| Equivalent_classes(A)                     | A ≡ B                     | \-                    | [B]                    |
| Equivalent_classes(B)                     | A ≡ B                     | \-                    | [A]                    |
| Instances(A)                              | A ≡ B                     | A(a),B(b)             | [a,b]                  |
| Instances(B)                              | A ≡ B                     | A(a),B(b)             | [a,b]                  |
| Types(a)                                  | A ≡ B                     | A(a),B(b)             | [T, A,B]               |
| Types(b)                                  | A ≡ B                     | A(a),B(b)             | [T, A,B]               |
| Sub_classes(A)                            | A ≡ B                     | \-                    | [B]                    |
| Sub_classes(B)                            | A ≡ B                     | \-                    | [A]                    |
| Super_classes(A)                          | A ≡ B                     | \-                    | [B,T]                  |
| Super_classes(B)                          | A ≡ B                     | \-                    | [A,T]                  |
| Equivalent_object_properties(r1)          | r1 ≡ r2                   | \-                    | [r2]                   |
| Equivalent_object_properties(r2)          | r1 ≡ r2                   | \-                    | [r1]                   |
| sub_object_properties(r1)                 | r1 ≡ r2                   | \-                    | [r2]                   |
| sub_object_properties(r2)                 | r1 ≡ r2                   | \-                    | [r1]                   |
| object_property_values(a, r1, direct=False) | r1 ≡ r2                   | r1(a,b) r2(a,c)       | [c]                    |
| object_property_values(a, r2, direct=False) | r1 ≡ r2                   | r1(a,b) r2(a,c)       | [c]                    |
| Sub_classes(B)                            | A ⊑ B                     | \-                    | [A]                    |
| Super_classes(A)                          | A ⊑ B                     | \-                    | [T, B]                 |
| Types(a)                                  | A ⊑ B                     | A(a),B(b)             | [A,B,T]                |
| Types(b)                                  | A ⊑ B                     | A(a),B(b)             | [B,T]                  |
| Instances(A)                              | A ⊑ B                     | A(a),B(b)             | [a]                    |
| Instances(B)                              | A ⊑ B                     | A(a),B(b)             | [a,b]                  |
| sub_object_properties(r1)                 | r2 ⊑ r1                   | \-                    | [r2]                   |
| object_property_values(a, r2)             | r2 ⊑ r1                   | r2(a,b)               | [b]                    |
| object_property_values(a, r1, direct=False) | r2 ⊑ r1                   | r2(a,b)               | [b]                    |
| Sub_classes(r1.T)                         | r2 ⊑ r1                   | \-                    | [r2.T]                 |
| Super_classes(D, only_named=False)        | D ⊑ ∃r.E                  | \-                    | [T, ∃r.E]               |
| Sub_classes(∃r.E)                          | D ⊑ ∃r.E                  | \-                    | [D]                    |
| Instances(D)                              | D ⊑ ∃r.E                  | D(d) r(i,e) E(e)      | [d]                    |
| Instances(∃r.E)                            | D ⊑ ∃r.E                  | D(d) r(i,e) E(e)      | [i, d]                 |
| types(d)                                  | D ⊑ ∃r.E                  | D(d) r(i,e) E(e)      | [D,T]                  |
| types(i)                                  | D ⊑ ∃r.E                  | D(d) r(i,e) E(e)      | [T]                    |
| object_property_values(i, r)              | D ⊑ ∃r.E                  | r(i,e) E(e)           | [e]                    |
| Sub_classes(D, only_named=False)          | ∃r.E ⊑ D                  | \-                    | [ ∃r.E]                 |
| Super_classes( ∃r.E)                       | ∃r.E ⊑ D                  | \-                    | [D, T]                 |
| Instances(D)                              | ∃r.E ⊑ D                  | D(d) r(i,e) E(e)      | [i, d]                 |
| Instances(∃r.E)                            | ∃r.E ⊑ D                  | D(d) r(i,e) E(e)      | [i]                    |
| types(d)                                  | ∃r.E ⊑ D                  | D(d) r(i,e) E(e)      | [D, T]                 |
| types(i)                                  | ∃r.E ⊑ D                  | D(d) r(i,e) E(e)      | [D, T]                 |
| object_property_values(i, r)              | ∃r.E ⊑ D                  | r(i,e) E(e)           | [e]                    |
| Sub_classes(A)                            | A ⊑ B, B ⊑ A              | \-                    | [A,B]                  |
| Sub_classes(B)                            | A ⊑ B, B ⊑ A              | \-                    | [A,B]                  |
| Super_classes(A)                          | A ⊑ B, B ⊑ A              | \-                    | [T, B]                 |
| Super_classes(B)                          | A ⊑ B, B ⊑ A              | \-                    | [T, A]                 |
| Types(a)                                  | A ⊑ B, B ⊑ A              | A(a),B(b)             | [A,B,T]                |
| Types(b)                                  | A ⊑ B, B ⊑ A              | A(a),B(b)             | [A,B,T]                |
| Instances(A)                              | A ⊑ B, B ⊑ A              | A(a),B(b)             | [a,b]                  |
| Instances(B)                              | A ⊑ B, B ⊑ A              | A(a),B(b)             | [a,b]                  |
| Equivalent_classes(A,only_named=False)    | A ⊑ B, B ⊑ A              | \-                    | [B]                    |
| Equivalent_classes(B,only_named=False)    | A ⊑ B, B ⊑ A              | \-                    | [A]                    |
| sub_object_properties(r1)                 | r2⊑ r1, r1⊑ r2            | \-                    | [r2,r1]                |
| sub_object_properties(r2)                 | r2⊑ r1, r1⊑ r2            | \-                    | [r1,r2]                |
| Equivalent_object_properties(r1)          | r2⊑ r1, r1⊑ r2            | \-                    | [r2]                   |
| Equivalent_object_properties(r2)          | r2⊑ r1, r1⊑ r2            | \-                    | [r1]                   |
| object_property_values(a, r1, direct=False) | r2 ⊑ r1, r1 ⊑ r2          | r1(a,b) r2(a,c)       | [b,c]                  |
| object_property_values(a, r2, direct=False) | r2 ⊑ r1, r1 ⊑ r2          | r1(a,b) r2(a,c)       | [b,c]                  |
| Sub_classes(J ⊓ K)                        | I ⊑ J ⊓ K                 | \-                    | [I]                    |
| Super_classes(I, only_named=False)        | I ⊑ J ⊓ K                 | \-                    | [J ⊓ K, J, K, T]       |
| Instances(J ⊓ K)                          | I ⊑ J ⊓ K                 | I(c)                  | [c]                    |
| types(c)                                  | I ⊑ J ⊓ K                 | I(c)                  | [J, K, I, T]           |
| Super_classes(J ⊓ K)                      | J ⊓ K ⊑ I                 | \-                    | [I, T]                 |
| Sub_classes(I, only_named=False)          | J ⊓ K ⊑ I                 | \-                    | [J ⊓ K]                |
| Instances(I)                              | J ⊓ K ⊑ I                 | J(s),K(s)             | [s]                    |
| Instances(J ⊓ K)                          | J ⊓ K ⊑ I                 | J(s),K(s)             | [s]                    |
| types(s)                                  | J ⊓ K ⊑ I                 | J(s),K(s)             | [J, K, I, T]           |
| Sub_classes( ∃r.E ⊓ B )                    | D ⊑ ∃r.E ⊓ B              | \-                    | [D]                    |
| Super_classes(D, only_named=False)        | D ⊑ ∃r.E ⊓ B              | \-                    | [T, ∃r.E ⊓ B, B]        |
| Instances(∃r.E ⊓ B)                        | D ⊑ ∃r.E ⊓ B              | D(d) r(b,f) E(f) B(b) | [d,b]                  |
| Sub_classes(H, only_named= False)         | F ≡ ∃r.G, F ⊑ H           | \-                    | [F, ∃r.G]               |
| Super_classes(F)                          | F ≡ ∃r.G, F ⊑ H           | \-                    | [H,∃r.G,T]              |
| Super_classes(∃r.G)                        | F ≡ ∃r.G, F ⊑ H           | \-                    | [F,H,T]                |
| Equivalent_classes(F, only_named=False)   | F ≡ ∃r.G, F ⊑ H           | \-                    | [∃r.G]                  |
| Equivalent_classes(∃r.G)                   | F ≡ ∃r.G, F ⊑ H           | \-                    | [F]                    |
| Instances(∃r.G)                            | F ≡ ∃r.G, F ⊑ H           | r(i,g) G(g)           | [i]                    |
| Instances(F)                              | F ≡ ∃r.G, F ⊑ H           | r(i,g) G(g)           | [i]                    |
| Instances(H)                              | F ≡ ∃r.G, F ⊑ H           | r(i,g) G(g)           | [i]                    |
| types(i)                                  | F ≡ ∃r.G, F ⊑ H           | r(i,g) G(g)           | [H,F,T]                |
| Sub_classes(C, only_named=False)          | A ⊓ B ≡ R, R ⊑ C          | \-                    | [R, A ⊓ B]             |
| Super_classes(A ⊓ B)                      | A ⊓ B ≡ R, R ⊑ C          | \-                    | [R, C,A,B,T]           |
| Equivalent_classes(R,<br>only_named=False) | A ⊓ B ≡ R, R ⊑ C          | \-                    | [A ⊓ B]                |
| Equivalent_classes(A ⊓ B)                 | A ⊓ B ≡ R, R ⊑ C          | \-                    | [R]                    |
| Instances(A ⊓ B)                          | A ⊓ B ≡ R, R ⊑ C          | R(e) A(a) B(a)        | [e,a]                  |
| Instances(R)                              | A ⊓ B ≡ R, R ⊑ C          | R(e) A(a) B(a)        | [a, e]                 |
| Instances(C)                              | A ⊓ B ≡ R, R ⊑ C          | R(e) A(a) B(a)        | [a, e]                 |
| Types(a)                                  | A ⊓ B ≡ R, R ⊑ C          | R(e) A(a) B(a)        | [A,B,R,C,T]            |
| Types(e)                                  | A ⊓ B ≡ R, R ⊑ C          | R(e) A(a) B(a)        | [A,B,R,C,T]            |
| Sub_classes(D, only_named=False)          | ∃r.P ⊓ C ≡ E, E ⊑ D       | \-                    | [E, ∃r.P  ⊓ C]          |
| Super_classes(∃r.P ⊓ C)                    | ∃r.P ⊓ C ≡ E, E ⊑ D       | \-                    | [E, D, T]              |
| Equivalent_classes(∃r.P ⊓ C)               | ∃r.P ⊓ C ≡ E, E ⊑ D       | \-                    | [E]                    |
| Equivalent_classes(E,<br>only_named=False) | ∃r.P ⊓ C ≡ E, E ⊑ D       | \-                    | [∃r.P ⊓ C]              |
| Instances(∃r.P ⊓ C)                        | ∃r.P ⊓ C ≡ E, E ⊑ D       | r(x,y) C(x) P(y)      | [x]                    |
| Instances(E)                              | ∃r.P ⊓ C ≡ E, E ⊑ D       | r(x,y) C(x) P(y)      | [x]                    |
| Instances(D)                              | ∃r.P ⊓ C ≡ E, E ⊑ D       | r(x,y) C(x) P(y)      | [x]                    |
| Types(x)                                  | ∃r.P ⊓ C ≡ E, E ⊑ D       | r(x,y) C(x) P(y)      | [C]                    |
| disjoint_classes(A)                       | A ⊔ B                     | \-                    | [B]                    |
| disjoint_classes(B)                       | A ⊔ B                     | \-                    | [A]                    |
| disjoint_classes(A)                       | A ⊔ B, B ≡ C              | \-                    | [B, C]                 |
| disjoint_classes(B)                       | A ⊔ B, B ≡ C              | \-                    | [A]                    |
| disjoint_classes(C)                       | A ⊔ B, B ≡ C              | \-                    | [A]                    |
| object_property_domains(r)                | Domain(r) = A             | \-                    | [A,T]                  |
| object_property_domains(r)                | Domain(r) = A<br>A ≡ B    | \-                    | [A,T]                  |
| object_property_domains(r2)               | Domain(r1) = A<br>r2 ⊑ r1 | \-                    | [A,T]                  |


