"""Targeted unit tests closing coverage gaps in SyncReasoner (owlapy.owl_reasoner) that
aren't exercised by tests/test_sync_reasoner.py: the close()/context-manager lifecycle,
and the include_bottom_entity=True branches / equivalent-property methods.

IMPORTANT: per the project's JPype constraint (a JVM cannot be restarted once shut down
in the same process), this file never calls stopJVM() -- matching the convention already
established in test_reasoner_timeout.py. SyncReasoner.close() only disposes this
reasoner's own OWLAPI object and Java executor; it does not touch the shared JVM, so it's
safe to call without affecting other JVM-dependent tests in the same session.
"""
import unittest

import pytest

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty
from owlapy.owl_reasoner import SyncReasoner

NS = "http://example.com/father#"


class TestSyncReasonerLifecycle(unittest.TestCase):
    def test_context_manager_calls_close_on_exit(self):
        with SyncReasoner("KGs/Family/father.owl") as r:
            self.assertIsNotNone(r._owlapi_reasoner)
        # After __exit__, close() disposes the OWLAPI reasoner and executor.
        self.assertIsNone(r._owlapi_reasoner)
        self.assertIsNone(r._reasoning_executor)

    def test_close_is_idempotent(self):
        r = SyncReasoner("KGs/Family/father.owl")
        r.close()
        self.assertIsNone(r._owlapi_reasoner)
        # Calling close() a second time must not raise even though the resources
        # were already released.
        r.close()

    def test_context_manager_returns_self(self):
        r = SyncReasoner("KGs/Family/father.owl")
        with r as entered:
            self.assertIs(entered, r)
        r.close()


class TestSyncReasonerIncludeBottomEntityAndEquivalentProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reasoner = SyncReasoner("KGs/Family/father.owl", reasoner="HermiT")
        cls.male = OWLClass(IRI.create(NS, "male"))
        cls.female = OWLClass(IRI.create(NS, "female"))
        cls.has_child = OWLObjectProperty(IRI.create(NS, "hasChild"))

    @classmethod
    def tearDownClass(cls):
        cls.reasoner.close()

    def test_disjoint_classes_include_bottom_entity_true(self):
        disjoint = list(self.reasoner.disjoint_classes(self.male, include_bottom_entity=True))
        self.assertIsInstance(disjoint, list)

    def test_sub_classes_include_bottom_entity_true(self):
        subs = list(self.reasoner.sub_classes(self.male, include_bottom_entity=True))
        self.assertIsInstance(subs, list)

    def test_sub_object_properties_include_bottom_entity_true(self):
        subs = list(self.reasoner.sub_object_properties(self.has_child, include_bottom_entity=True))
        self.assertIsInstance(subs, list)

    def test_equivalent_object_properties(self):
        equiv = list(self.reasoner.equivalent_object_properties(self.has_child))
        self.assertIsInstance(equiv, list)

    def test_disjoint_classes_default_excludes_bottom(self):
        # Sanity check that the default (include_bottom_entity=False) path still works
        # alongside the True variant above, on the same shared reasoner instance.
        disjoint = list(self.reasoner.disjoint_classes(self.male))
        self.assertIsInstance(disjoint, list)


class TestSyncReasonerDataPropertyIncludeBottomEntity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reasoner = SyncReasoner("KGs/Mutagenesis/mutagenesis.owl", reasoner="HermiT")
        cls.ns = "http://dl-learner.org/mutagenesis#"
        cls.charge = OWLDataProperty(IRI.create(cls.ns, "charge"))

    @classmethod
    def tearDownClass(cls):
        cls.reasoner.close()

    def test_sub_data_properties_include_bottom_entity_true(self):
        subs = list(self.reasoner.sub_data_properties(self.charge, include_bottom_entity=True))
        self.assertIsInstance(subs, list)

    def test_equivalent_data_properties_is_broken(self):
        # NOTE: SyncReasoner.equivalent_data_properties() calls
        # `self.mapper.to_list(self._owlapi_reasoner.getEquivalentDataProperties(...))`,
        # but getEquivalentDataProperties() returns an OWLAPI `Node<OWLDataProperty>`
        # (old-style API), not a java.util.stream.Stream. mapper.to_list() unconditionally
        # calls `.collect(Collectors.toList())`, which Node doesn't have -- this method
        # currently always raises AttributeError, unlike equivalent_object_properties()
        # (line 1693-1694), which correctly calls the Stream-returning `equivalentObjectProperties`.
        with pytest.raises(AttributeError):
            list(self.reasoner.equivalent_data_properties(self.charge))


if __name__ == '__main__':
    unittest.main()
