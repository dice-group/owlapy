from owlapy.class_expression import OWLObjectSomeValuesFrom, OWLObjectIntersectionOf, OWLClass
from owlapy.iri import IRI
from owlapy.owl_axiom import OWLSubClassOfAxiom, OWLObjectPropertyDomainAxiom, OWLEquivalentObjectPropertiesAxiom
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology_manager import OntologyManager
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty
from owlapy.owl_reasoner import StructuralReasoner

data_file = '../KGs/Test/test_ontology.owl'
NS = 'http://www.semanticweb.org/stefan/ontologies/2023/1/untitled-ontology-11#'

"""
---------Object Properties---------
Domain(r1) = S ⊓ T, Range(r1) = G
r2 ⊑ r1
r3 ⊑ r4
r7
r5 ⊓ r1 = ∅
r5 ≡ r6

---------Data Properties---------
dp2 ⊑ dp1
dp3 ⊓ dp1 = ∅

---------Classes-----------
AB ≡ (A ⊓ B), AB ⊑ C
D ⊑ (r7.E ⊓ B)
F ≡ r2.G, F ⊑ H
I ⊑ (J ⊓ K)
L ⊓ M = ∅
N ≡ Q
O ⊑ P
R ⊑ r5.Q
(S ⊓ T) ⊑ U

---------Individuals-----------
o is O
p is P
a is A ^ B
b is B, b has r1.f
c is I
d is D
e is AB
f is E
g is G
n is N, n has r3.q, r4.l, r6.s, r5.Q
m is M
l is L
l ≠ m
q is Q
ind1 has r5.q, r2.g, r6.(S ⊓ T)
r is R
s is S ^ T
"""

# ---------------------------------------- Mapping to owlapy classes ----------------------------------------
a = OWLNamedIndividual(IRI(NS, "a"))
b = OWLNamedIndividual(IRI(NS, "b"))
c = OWLNamedIndividual(IRI(NS, "c"))
d = OWLNamedIndividual(IRI(NS, "d"))
e = OWLNamedIndividual(IRI(NS, "e"))
g = OWLNamedIndividual(IRI(NS, "g"))
m = OWLNamedIndividual(IRI(NS, "m"))
l = OWLNamedIndividual(IRI(NS, "l"))  # noqa: E741
n = OWLNamedIndividual(IRI(NS, "n"))
o = OWLNamedIndividual(IRI(NS, "o"))
p = OWLNamedIndividual(IRI(NS, "p"))
q = OWLNamedIndividual(IRI(NS, "q"))
r = OWLNamedIndividual(IRI(NS, "r"))
s = OWLNamedIndividual(IRI(NS, "s"))
ind1 = OWLNamedIndividual(IRI(NS, "ind1"))

r1 = OWLObjectProperty(IRI(NS, "r1"))
r2 = OWLObjectProperty(IRI(NS, "r2"))
r3 = OWLObjectProperty(IRI(NS, "r3"))
r4 = OWLObjectProperty(IRI(NS, "r4"))
r5 = OWLObjectProperty(IRI(NS, "r5"))
r6 = OWLObjectProperty(IRI(NS, "r6"))
r7 = OWLObjectProperty(IRI(NS, "r7"))

dp1 = OWLDataProperty(IRI(NS, "dp1"))
dp2 = OWLDataProperty(IRI(NS, "dp2"))
dp3 = OWLDataProperty(IRI(NS, "dp3"))

A = OWLClass(IRI(NS, 'A'))
B = OWLClass(IRI(NS, 'B'))
C = OWLClass(IRI(NS, 'C'))
AB = OWLClass(IRI(NS, 'AB'))
D = OWLClass(IRI(NS, 'D'))
E = OWLClass(IRI(NS, 'E'))
F = OWLClass(IRI(NS, 'F'))
G = OWLClass(IRI(NS, 'G'))
J = OWLClass(IRI(NS, 'J'))
K = OWLClass(IRI(NS, 'K'))
H = OWLClass(IRI(NS, 'H'))
I = OWLClass(IRI(NS, 'I'))  # noqa: E741
L = OWLClass(IRI(NS, 'L'))
M = OWLClass(IRI(NS, 'M'))
N = OWLClass(IRI(NS, 'N'))
O = OWLClass(IRI(NS, 'O'))  # noqa: E741
P = OWLClass(IRI(NS, 'P'))
Q = OWLClass(IRI(NS, 'Q'))
R = OWLClass(IRI(NS, 'R'))
S = OWLClass(IRI(NS, 'S'))
T = OWLClass(IRI(NS, 'T'))
U = OWLClass(IRI(NS, 'U'))

# ---------------------------------------- Adding some custom axioms ----------------------------------------

r2G = OWLObjectSomeValuesFrom(property=r2, filler=G)
r5Q = OWLObjectSomeValuesFrom(property=r5, filler=Q)
ST = OWLObjectIntersectionOf([S, T])
ABint = OWLObjectIntersectionOf([A, B])
r7E = OWLObjectSomeValuesFrom(property=r7, filler=E)
r7EB = OWLObjectIntersectionOf([r7E, B])
JK = OWLObjectIntersectionOf([J, K])
r1T = OWLObjectSomeValuesFrom(property=r1, filler=OWLClass(IRI('http://www.w3.org/2002/07/owl#', 'Thing')))

manager = OntologyManager()
onto = manager.load_ontology(IRI.create('file://' + data_file))

onto.add_axiom(OWLEquivalentObjectPropertiesAxiom([r6, r5]))
onto.add_axiom(OWLEquivalentObjectPropertiesAxiom([r5, r6]))
onto.add_axiom(OWLObjectPropertyDomainAxiom(r1, ST))

onto.add_axiom(OWLSubClassOfAxiom(R, r5Q))
onto.add_axiom(OWLSubClassOfAxiom(ST, U))


# ---------------------------------------- Reasoning ----------------------------------------

reasoner = StructuralReasoner(onto)

# Instances
t1 = list(reasoner.instances(N))
t2 = list(reasoner.instances(r7E))
t3 = list(reasoner.instances(D))
t4 = list(reasoner.instances(H))
t5 = list(reasoner.instances(JK))
t6 = list(reasoner.instances(C))
t7 = list(reasoner.instances(r2G))
t8 = list(reasoner.instances(F))
t9 = list(reasoner.instances(ABint))
t10 = list(reasoner.instances(AB))
t11 = list(reasoner.instances(r7EB))
t12 = list(reasoner.instances(P))
t13 = list(reasoner.instances(O))
t14 = list(reasoner.instances(N))
t15 = list(reasoner.instances(Q))
t16 = list(reasoner.instances(r5Q))
t17 = list(reasoner.instances(R))
t18 = list(reasoner.instances(ST))
t19 = list(reasoner.instances(U))
t20 = list(reasoner.instances(r2G))

# Equivalent classes
t21 = list(reasoner.equivalent_classes(A))
t22 = list(reasoner.equivalent_classes(L))
t23 = list(reasoner.equivalent_classes(AB, only_named=False))
t24 = list(reasoner.equivalent_classes(ABint))
t25 = list(reasoner.equivalent_classes(F, only_named=False))
t26 = list(reasoner.equivalent_classes(r2G))
t27 = list(reasoner.equivalent_classes(O))
t28 = list(reasoner.equivalent_classes(P, only_named=False))
t29 = list(reasoner.equivalent_classes(N, only_named=False))
t30 = list(reasoner.equivalent_classes(Q))

# Equivalent Object Properties
t31 = list(reasoner.equivalent_object_properties(r1))
t32 = list(reasoner.equivalent_object_properties(r2))
t33 = list(reasoner.equivalent_object_properties(r5))
t34 = list(reasoner.equivalent_object_properties(r6))
t35 = list(reasoner.equivalent_object_properties(r3))
t36 = list(reasoner.equivalent_object_properties(r4))

# Sup Classes
t37 = list(reasoner.sub_classes(r7E))
t38 = list(reasoner.sub_classes(r7EB))
t39 = list(reasoner.sub_classes(H, only_named=False))
t40 = list(reasoner.sub_classes(JK))
t41 = list(reasoner.sub_classes(C, only_named=False))
t42 = list(reasoner.sub_classes(A, only_named=False))
t43 = list(reasoner.sub_classes(P))
t44 = list(reasoner.sub_classes(O))
t45 = list(reasoner.sub_classes(N, only_named=False))
t46 = list(reasoner.sub_classes(Q, only_named=False))
t47 = list(reasoner.sub_classes(r5Q, only_named=False))
t48 = list(reasoner.sub_classes(R, only_named=False))
t49 = list(reasoner.sub_classes(U, only_named=False))
t50 = list(reasoner.sub_classes(r1T, only_named=False))

# Sub Object Properties
t51 = list(reasoner.sub_object_properties(r1))
t52 = list(reasoner.sub_object_properties(r2))
t59 = list(reasoner.sub_object_properties(r3))
t60 = list(reasoner.sub_object_properties(r4))
t85 = list(reasoner.sub_object_properties(r5))
t86 = list(reasoner.sub_object_properties(r6))

# Super Classes
t87 = list(reasoner.super_classes(D, only_named=False))
t88 = list(reasoner.super_classes(r2G))
t89 = list(reasoner.super_classes(I, only_named=False))
t90 = list(reasoner.super_classes(AB))
t91 = list(reasoner.super_classes(ABint))
t92 = list(reasoner.super_classes(P))
t93 = list(reasoner.super_classes(O))
t94 = list(reasoner.super_classes(N, only_named=False))
t95 = list(reasoner.super_classes(Q, only_named=False))
t96 = list(reasoner.super_classes(r5Q, only_named=False))
t97 = list(reasoner.super_classes(R, only_named=False))
t98 = list(reasoner.super_classes(ST, only_named=False))
t99 = list(reasoner.super_classes(F))

# Types
t100 = list(reasoner.types(a))
t101 = list(reasoner.types(d))
t102 = list(reasoner.types(g))
t103 = list(reasoner.types(p))
t104 = list(reasoner.types(o))
t105 = list(reasoner.types(n))
t106 = list(reasoner.types(q))
t107 = list(reasoner.types(r))
t108 = list(reasoner.types(ind1))
t109 = list(reasoner.types(e))
t110 = list(reasoner.types(c))
t111 = list(reasoner.types(s))

# Different Individuals
t112 = list(reasoner.different_individuals(a))
t113 = list(reasoner.different_individuals(b))
t114 = list(reasoner.different_individuals(l))
t115 = list(reasoner.different_individuals(n))

# Same Individuals
t116 = list(reasoner.same_individuals(o))
t117 = list(reasoner.same_individuals(p))
t118 = list(reasoner.same_individuals(r))
t119 = list(reasoner.same_individuals(q))
t120 = list(reasoner.same_individuals(s))

# Disjoint Classes
t121 = list(reasoner.disjoint_classes(M, only_named=False))
t122 = list(reasoner.disjoint_classes(N, only_named=False))
t123 = list(reasoner.disjoint_classes(L, only_named=False))
t124 = list(reasoner.disjoint_classes(O, only_named=False))
t125 = list(reasoner.disjoint_classes(P, only_named=False))
t126 = list(reasoner.disjoint_classes(Q, only_named=False))

# Disjoint Object Properties
t127 = list(reasoner.disjoint_object_properties(r3))
t128 = list(reasoner.disjoint_object_properties(r4))
t129 = list(reasoner.disjoint_object_properties(r1))
t130 = list(reasoner.disjoint_object_properties(r2))
t131 = list(reasoner.disjoint_object_properties(r5))
t132 = list(reasoner.disjoint_object_properties(r6))

# Disjoint Data Properties
t133 = list(reasoner.disjoint_data_properties(dp1))
t134 = list(reasoner.disjoint_data_properties(dp2))
t135 = list(reasoner.disjoint_data_properties(dp3))

# Object Properties Domains and Ranges
t136 = list(reasoner.object_property_domains(r1))
t137 = list(reasoner.object_property_domains(r2))
t138 = list(reasoner.object_property_ranges(r1))
t139 = list(reasoner.object_property_ranges(r2))

# Object Properties Values
t140 = list(reasoner.object_property_values(n, r3, direct=False))
t141 = list(reasoner.object_property_values(n, r4, direct=False))
t142 = list(reasoner.object_property_values(n, r5))
t143 = list(reasoner.object_property_values(n, r6))
t144 = list(reasoner.object_property_values(ind1, r6))
t145 = list(reasoner.object_property_values(ind1, r5))

# Super Object Properties
t146 = list(reasoner.super_object_properties(r1))
t147 = list(reasoner.super_object_properties(r2))
t148 = list(reasoner.super_object_properties(r5))
t149 = list(reasoner.super_object_properties(r6))

# Sub Object Properties
t150 = list(reasoner.sub_object_properties(r1))
t151 = list(reasoner.sub_object_properties(r2))
t152 = list(reasoner.sub_object_properties(r5))
t153 = list(reasoner.sub_object_properties(r6))

# Super Data Properties
t154 = list(reasoner.super_data_properties(dp1))
t155 = list(reasoner.super_data_properties(dp2))

# Sub Data Properties
t156 = list(reasoner.sub_data_properties(dp1))
t157 = list(reasoner.sub_data_properties(dp2))

# Display the results
for x in range(1, 157):
    var_name = f"t{x}"
    try:
        print(f" {var_name} = {globals()[var_name]}")
    except KeyError:
        continue
