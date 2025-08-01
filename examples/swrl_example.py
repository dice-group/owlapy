from owlapy.class_expression import OWLClass
from owlapy.owl_property import OWLObjectProperty
from owlapy.swrl import IVariable, ClassAtom, ObjectPropertyAtom, Rule

x_var = IVariable("http://www.w3.org/2003/11/swrl#x")
y_var = IVariable("http://www.w3.org/2003/11/swrl#y")
male = OWLClass("http://example.com/father#male")
has_child = OWLObjectProperty("http://example.com/father#hasChild")
has_father = OWLObjectProperty("http://example.com/father#hasFather")

atom1 = ClassAtom(male, x_var)
atom2 = ObjectPropertyAtom(has_child, x_var, y_var)
atom3 = ObjectPropertyAtom(has_father, y_var, x_var)

rule1 = Rule([atom1, atom2], [atom3])

print(rule1)

rule2 = Rule.from_string(rule = "parent(felix,?y) ^ brother(?y,?z) -> uncle(?felix,?z)",
                         namespace="http://example.com/family#")

print(rule2.__repr__())