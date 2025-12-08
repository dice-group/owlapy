"""Test cases for owl_hierarchy module to increase coverage."""
import unittest
from owlapy.owl_hierarchy import (
    ClassHierarchy, ObjectPropertyHierarchy, DatatypePropertyHierarchy,
    _children_transitive, _reduce_transitive
)
from owlapy.class_expression import OWLClass, OWLThing, OWLNothing
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty
from owlapy.owl_literal import (
    OWLTopObjectProperty, OWLBottomObjectProperty,
    OWLTopDataProperty, OWLBottomDataProperty
)
from owlapy.iri import IRI
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner import SyncReasoner


class TestClassHierarchy(unittest.TestCase):
    """Test class hierarchy functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.ns = "http://example.com/test#"
        
        # Create test classes
        self.person = OWLClass(IRI.create(self.ns, "Person"))
        self.male = OWLClass(IRI.create(self.ns, "Male"))
        self.female = OWLClass(IRI.create(self.ns, "Female"))
        self.father = OWLClass(IRI.create(self.ns, "Father"))
        self.mother = OWLClass(IRI.create(self.ns, "Mother"))
        
    def test_class_hierarchy_from_tuples(self):
        """Test creating class hierarchy from tuples."""
        hierarchy_data = [
            (self.person, [self.male, self.female]),
            (self.male, [self.father]),
            (self.female, [self.mother]),
            (self.father, []),
            (self.mother, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Test basic functionality
        self.assertIn(self.person, hierarchy)
        self.assertIn(self.male, hierarchy)
        self.assertEqual(len(hierarchy), 5)
        
    def test_parents_direct(self):
        """Test getting direct parents."""
        hierarchy_data = [
            (self.person, [self.male, self.female]),
            (self.male, [self.father]),
            (self.female, [self.mother]),
            (self.father, []),
            (self.mother, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Test direct parents
        parents = list(hierarchy.parents(self.father, direct=True))
        self.assertIn(self.male, parents)
        
    def test_parents_transitive(self):
        """Test getting transitive parents."""
        hierarchy_data = [
            (self.person, [self.male, self.female]),
            (self.male, [self.father]),
            (self.female, [self.mother]),
            (self.father, []),
            (self.mother, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Test transitive parents
        parents = list(hierarchy.parents(self.father, direct=False))
        self.assertIn(self.male, parents)
        self.assertIn(self.person, parents)
        
    def test_children_direct(self):
        """Test getting direct children."""
        hierarchy_data = [
            (self.person, [self.male, self.female]),
            (self.male, [self.father]),
            (self.female, [self.mother]),
            (self.father, []),
            (self.mother, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Test direct children
        children = list(hierarchy.children(self.person, direct=True))
        self.assertIn(self.male, children)
        self.assertIn(self.female, children)
        
    def test_children_transitive(self):
        """Test getting transitive children."""
        hierarchy_data = [
            (self.person, [self.male, self.female]),
            (self.male, [self.father]),
            (self.female, [self.mother]),
            (self.father, []),
            (self.mother, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Test transitive children
        children = list(hierarchy.children(self.person, direct=False))
        self.assertIn(self.male, children)
        self.assertIn(self.female, children)
        self.assertIn(self.father, children)
        self.assertIn(self.mother, children)
        
    def test_roots(self):
        """Test getting root classes."""
        hierarchy_data = [
            (self.person, [self.male, self.female]),
            (self.male, [self.father]),
            (self.female, [self.mother]),
            (self.father, []),
            (self.mother, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Test roots
        roots = list(hierarchy.roots())
        self.assertIn(self.person, roots)
        
    def test_roots_of_entity(self):
        """Test getting roots of specific entity."""
        hierarchy_data = [
            (self.person, [self.male, self.female]),
            (self.male, [self.father]),
            (self.female, [self.mother]),
            (self.father, []),
            (self.mother, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Test roots of specific entity
        roots = list(hierarchy.roots(of=self.father))
        self.assertIn(self.person, roots)
        
    def test_leaves(self):
        """Test getting leaf classes."""
        hierarchy_data = [
            (self.person, [self.male, self.female]),
            (self.male, [self.father]),
            (self.female, [self.mother]),
            (self.father, []),
            (self.mother, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Test leaves
        leaves = list(hierarchy.leaves())
        self.assertIn(self.father, leaves)
        self.assertIn(self.mother, leaves)
        
    def test_leaves_of_entity(self):
        """Test getting leaves of specific entity."""
        hierarchy_data = [
            (self.person, [self.male, self.female]),
            (self.male, [self.father]),
            (self.female, [self.mother]),
            (self.father, []),
            (self.mother, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Test leaves of specific entity
        leaves = list(hierarchy.leaves(of=self.male))
        self.assertIn(self.father, leaves)
        
    def test_siblings(self):
        """Test getting siblings."""
        hierarchy_data = [
            (self.person, [self.male, self.female]),
            (self.male, [self.father]),
            (self.female, [self.mother]),
            (self.father, []),
            (self.mother, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Test siblings
        siblings = list(hierarchy.siblings(self.male))
        self.assertIn(self.female, siblings)
        
    def test_is_parent_of(self):
        """Test parent relationship."""
        hierarchy_data = [
            (self.person, [self.male]),
            (self.male, [self.father]),
            (self.father, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        self.assertTrue(hierarchy.is_parent_of(self.person, self.male))
        self.assertTrue(hierarchy.is_parent_of(self.person, self.father))
        self.assertTrue(hierarchy.is_parent_of(self.male, self.male))  # reflexive
        
    def test_is_child_of(self):
        """Test child relationship."""
        hierarchy_data = [
            (self.person, [self.male]),
            (self.male, [self.father]),
            (self.father, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        self.assertTrue(hierarchy.is_child_of(self.male, self.person))
        self.assertTrue(hierarchy.is_child_of(self.father, self.person))
        self.assertTrue(hierarchy.is_child_of(self.male, self.male))  # reflexive
        
    def test_sub_classes(self):
        """Test sub_classes method."""
        hierarchy_data = [
            (self.person, [self.male, self.female]),
            (self.male, []),
            (self.female, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        sub_classes = list(hierarchy.sub_classes(self.person))
        self.assertIn(self.male, sub_classes)
        self.assertIn(self.female, sub_classes)
        
    def test_super_classes(self):
        """Test super_classes method."""
        hierarchy_data = [
            (self.person, [self.male]),
            (self.male, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        super_classes = list(hierarchy.super_classes(self.male))
        self.assertIn(self.person, super_classes)
        
    def test_is_subclass_of(self):
        """Test is_subclass_of method."""
        hierarchy_data = [
            (self.person, [self.male]),
            (self.male, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        self.assertTrue(hierarchy.is_subclass_of(self.male, self.person))
        
    def test_top_entity(self):
        """Test top entity."""
        self.assertEqual(ClassHierarchy.get_top_entity(), OWLThing)
        
    def test_bottom_entity(self):
        """Test bottom entity."""
        self.assertEqual(ClassHierarchy.get_bottom_entity(), OWLNothing)
        
    def test_parents_of_bottom(self):
        """Test parents of bottom entity."""
        hierarchy_data = [
            (self.person, [self.male]),
            (self.male, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Bottom entity's parents should be all leaves
        parents = list(hierarchy.parents(OWLNothing, direct=True))
        self.assertIn(self.male, parents)
        
    def test_parents_of_top(self):
        """Test parents of top entity."""
        hierarchy_data = [
            (self.person, [self.male]),
            (self.male, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Top entity has no parents
        parents = list(hierarchy.parents(OWLThing, direct=True))
        self.assertEqual(len(parents), 0)
        
    def test_children_of_top(self):
        """Test children of top entity."""
        hierarchy_data = [
            (self.person, [self.male]),
            (self.male, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Top entity's children should be all roots
        children = list(hierarchy.children(OWLThing, direct=True))
        self.assertIn(self.person, children)
        
    def test_children_of_bottom(self):
        """Test children of bottom entity."""
        hierarchy_data = [
            (self.person, [self.male]),
            (self.male, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Bottom entity has no children
        children = list(hierarchy.children(OWLNothing, direct=True))
        self.assertEqual(len(children), 0)
        
    def test_restrict_hierarchy(self):
        """Test restricting hierarchy."""
        hierarchy_data = [
            (self.person, [self.male, self.female]),
            (self.male, [self.father]),
            (self.female, [self.mother]),
            (self.father, []),
            (self.mother, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Restrict to only male branch
        restricted = ClassHierarchy.restrict(hierarchy, allow=[self.person, self.male, self.father])
        
        self.assertIn(self.person, restricted)
        self.assertIn(self.male, restricted)
        self.assertIn(self.father, restricted)
        self.assertEqual(len(restricted), 3)
        
    def test_restrict_and_copy(self):
        """Test restrict_and_copy method."""
        hierarchy_data = [
            (self.person, [self.male, self.female]),
            (self.male, []),
            (self.female, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        # Remove female
        restricted = hierarchy.restrict_and_copy(remove=[self.female])
        
        self.assertIn(self.person, restricted)
        self.assertIn(self.male, restricted)
        self.assertEqual(len(restricted), 2)
        
    def test_items(self):
        """Test items method."""
        hierarchy_data = [
            (self.person, [self.male]),
            (self.male, [])
        ]
        
        hierarchy = ClassHierarchy(hierarchy_data)
        
        items = list(hierarchy.items())
        self.assertIn(self.person, items)
        self.assertIn(self.male, items)


class TestObjectPropertyHierarchy(unittest.TestCase):
    """Test object property hierarchy functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ns = "http://example.com/test#"
        
        # Create test properties
        self.has_relative = OWLObjectProperty(IRI.create(self.ns, "hasRelative"))
        self.has_parent = OWLObjectProperty(IRI.create(self.ns, "hasParent"))
        self.has_father = OWLObjectProperty(IRI.create(self.ns, "hasFather"))
        self.has_mother = OWLObjectProperty(IRI.create(self.ns, "hasMother"))
        
    def test_property_hierarchy_from_tuples(self):
        """Test creating property hierarchy from tuples."""
        hierarchy_data = [
            (self.has_relative, [self.has_parent]),
            (self.has_parent, [self.has_father, self.has_mother]),
            (self.has_father, []),
            (self.has_mother, [])
        ]
        
        hierarchy = ObjectPropertyHierarchy(hierarchy_data)
        
        self.assertIn(self.has_relative, hierarchy)
        self.assertIn(self.has_parent, hierarchy)
        self.assertEqual(len(hierarchy), 4)
        
    def test_sub_object_properties(self):
        """Test sub_object_properties method."""
        hierarchy_data = [
            (self.has_relative, [self.has_parent]),
            (self.has_parent, [self.has_father]),
            (self.has_father, [])
        ]
        
        hierarchy = ObjectPropertyHierarchy(hierarchy_data)
        
        sub_props = list(hierarchy.sub_object_properties(self.has_relative))
        self.assertIn(self.has_parent, sub_props)
        
    def test_super_object_properties(self):
        """Test super_object_properties method."""
        hierarchy_data = [
            (self.has_relative, [self.has_parent]),
            (self.has_parent, []),
        ]
        
        hierarchy = ObjectPropertyHierarchy(hierarchy_data)
        
        super_props = list(hierarchy.super_object_properties(self.has_parent))
        self.assertIn(self.has_relative, super_props)
        
    def test_more_general_roles(self):
        """Test more_general_roles method."""
        hierarchy_data = [
            (self.has_relative, [self.has_parent]),
            (self.has_parent, [self.has_father]),
            (self.has_father, [])
        ]
        
        hierarchy = ObjectPropertyHierarchy(hierarchy_data)
        
        general = list(hierarchy.more_general_roles(self.has_father))
        self.assertIn(self.has_parent, general)
        
    def test_more_special_roles(self):
        """Test more_special_roles method."""
        hierarchy_data = [
            (self.has_relative, [self.has_parent]),
            (self.has_parent, [self.has_father]),
            (self.has_father, [])
        ]
        
        hierarchy = ObjectPropertyHierarchy(hierarchy_data)
        
        special = list(hierarchy.more_special_roles(self.has_parent))
        self.assertIn(self.has_father, special)
        
    def test_is_sub_property_of(self):
        """Test is_sub_property_of method."""
        hierarchy_data = [
            (self.has_relative, [self.has_parent]),
            (self.has_parent, [self.has_father]),
            (self.has_father, [])
        ]
        
        hierarchy = ObjectPropertyHierarchy(hierarchy_data)
        
        self.assertTrue(hierarchy.is_sub_property_of(self.has_father, self.has_relative))
        
    def test_most_general_roles(self):
        """Test most_general_roles method."""
        hierarchy_data = [
            (self.has_relative, [self.has_parent]),
            (self.has_parent, []),
        ]
        
        hierarchy = ObjectPropertyHierarchy(hierarchy_data)
        
        most_general = list(hierarchy.most_general_roles())
        self.assertIn(self.has_relative, most_general)
        
    def test_most_special_roles(self):
        """Test most_special_roles method."""
        hierarchy_data = [
            (self.has_relative, [self.has_parent]),
            (self.has_parent, []),
        ]
        
        hierarchy = ObjectPropertyHierarchy(hierarchy_data)
        
        most_special = list(hierarchy.most_special_roles())
        self.assertIn(self.has_parent, most_special)
        
    def test_top_entity(self):
        """Test top entity."""
        self.assertEqual(ObjectPropertyHierarchy.get_top_entity(), OWLTopObjectProperty)
        
    def test_bottom_entity(self):
        """Test bottom entity."""
        self.assertEqual(ObjectPropertyHierarchy.get_bottom_entity(), OWLBottomObjectProperty)


class TestDatatypePropertyHierarchy(unittest.TestCase):
    """Test datatype property hierarchy functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ns = "http://example.com/test#"
        
        # Create test properties
        self.has_value = OWLDataProperty(IRI.create(self.ns, "hasValue"))
        self.has_age = OWLDataProperty(IRI.create(self.ns, "hasAge"))
        self.has_name = OWLDataProperty(IRI.create(self.ns, "hasName"))
        
    def test_data_property_hierarchy_from_tuples(self):
        """Test creating data property hierarchy from tuples."""
        hierarchy_data = [
            (self.has_value, [self.has_age, self.has_name]),
            (self.has_age, []),
            (self.has_name, [])
        ]
        
        hierarchy = DatatypePropertyHierarchy(hierarchy_data)
        
        self.assertIn(self.has_value, hierarchy)
        self.assertIn(self.has_age, hierarchy)
        self.assertEqual(len(hierarchy), 3)
        
    def test_sub_data_properties(self):
        """Test sub_data_properties method."""
        hierarchy_data = [
            (self.has_value, [self.has_age]),
            (self.has_age, [])
        ]
        
        hierarchy = DatatypePropertyHierarchy(hierarchy_data)
        
        sub_props = list(hierarchy.sub_data_properties(self.has_value))
        self.assertIn(self.has_age, sub_props)
        
    def test_super_data_properties(self):
        """Test super_data_properties method."""
        hierarchy_data = [
            (self.has_value, [self.has_age]),
            (self.has_age, [])
        ]
        
        hierarchy = DatatypePropertyHierarchy(hierarchy_data)
        
        super_props = list(hierarchy.super_data_properties(self.has_age))
        self.assertIn(self.has_value, super_props)
        
    def test_more_general_roles(self):
        """Test more_general_roles method."""
        hierarchy_data = [
            (self.has_value, [self.has_age]),
            (self.has_age, [])
        ]
        
        hierarchy = DatatypePropertyHierarchy(hierarchy_data)
        
        general = list(hierarchy.more_general_roles(self.has_age))
        self.assertIn(self.has_value, general)
        
    def test_more_special_roles(self):
        """Test more_special_roles method."""
        hierarchy_data = [
            (self.has_value, [self.has_age]),
            (self.has_age, [])
        ]
        
        hierarchy = DatatypePropertyHierarchy(hierarchy_data)
        
        special = list(hierarchy.more_special_roles(self.has_value))
        self.assertIn(self.has_age, special)
        
    def test_is_sub_property_of(self):
        """Test is_sub_property_of method."""
        hierarchy_data = [
            (self.has_value, [self.has_age]),
            (self.has_age, [])
        ]
        
        hierarchy = DatatypePropertyHierarchy(hierarchy_data)
        
        self.assertTrue(hierarchy.is_sub_property_of(self.has_age, self.has_value))
        
    def test_most_general_roles(self):
        """Test most_general_roles method."""
        hierarchy_data = [
            (self.has_value, [self.has_age]),
            (self.has_age, [])
        ]
        
        hierarchy = DatatypePropertyHierarchy(hierarchy_data)
        
        most_general = list(hierarchy.most_general_roles())
        self.assertIn(self.has_value, most_general)
        
    def test_most_special_roles(self):
        """Test most_special_roles method."""
        hierarchy_data = [
            (self.has_value, [self.has_age]),
            (self.has_age, [])
        ]
        
        hierarchy = DatatypePropertyHierarchy(hierarchy_data)
        
        most_special = list(hierarchy.most_special_roles())
        self.assertIn(self.has_age, most_special)
        
    def test_top_entity(self):
        """Test top entity."""
        self.assertEqual(DatatypePropertyHierarchy.get_top_entity(), OWLTopDataProperty)
        
    def test_bottom_entity(self):
        """Test bottom entity."""
        self.assertEqual(DatatypePropertyHierarchy.get_bottom_entity(), OWLBottomDataProperty)


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions."""
    
    def test_children_transitive(self):
        """Test _children_transitive function."""
        ns = "http://example.com/test#"
        person = OWLClass(IRI.create(ns, "Person"))
        male = OWLClass(IRI.create(ns, "Male"))
        father = OWLClass(IRI.create(ns, "Father"))
        
        hier_trans = {
            person: {male},
            male: {father},
            father: set()
        }
        
        _children_transitive(hier_trans, person, set())
        
        # After transitive closure, person should have both male and father
        self.assertIn(male, hier_trans[person])
        self.assertIn(father, hier_trans[person])
        
    def test_reduce_transitive(self):
        """Test _reduce_transitive function."""
        ns = "http://example.com/test#"
        person = OWLClass(IRI.create(ns, "Person"))
        male = OWLClass(IRI.create(ns, "Male"))
        father = OWLClass(IRI.create(ns, "Father"))
        
        # Transitive hierarchy
        hier_trans = {
            person: {male, father},
            male: {father},
            father: set()
        }
        
        hier_inverse_trans = {
            person: set(),
            male: {person},
            father: {person, male}
        }
        
        result_hier, leaf_set = _reduce_transitive(hier_trans, hier_inverse_trans)
        
        # Direct hierarchy should only have direct children
        self.assertIn(male, result_hier[person])
        self.assertNotIn(father, result_hier[person])  # Transitive link removed
        self.assertIn(father, result_hier[male])
        
        # Leaf set should contain father
        self.assertIn(father, leaf_set)


if __name__ == '__main__':
    unittest.main()

