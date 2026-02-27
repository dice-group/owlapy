"""Ontology quality metrics for OWL ontologies.

This module provides classes for computing structural, schema-level, and
knowledge-base-level metrics that characterize the quality of an OWL ontology.
"""
from __future__ import annotations

import logging
from collections import deque
from typing import Dict, Optional, Union

from owlapy.abstracts import AbstractOWLOntology
from owlapy.abstracts.abstract_owl_reasoner import AbstractOWLReasoner
from owlapy.owl_hierarchy import ClassHierarchy

logger = logging.getLogger(__name__)


class BasicMetrics:
    """Compute basic size / count metrics for an OWL ontology.

    All counting methods rely only on the ``AbstractOWLOntology`` interface
    (``classes_in_signature``, ``object_properties_in_signature``, etc.) so
    they work with every backend (``Ontology``, ``SyncOntology``,
    ``RDFLibOntology``).

    Args:
        ontology: The ontology to measure.
    """

    def __init__(self, ontology: AbstractOWLOntology):
        self.ontology = ontology

    # ------------------------------------------------------------------
    # Signature counts
    # ------------------------------------------------------------------

    def num_classes(self) -> int:
        """Return the number of named classes in the ontology signature."""
        return sum(1 for _ in self.ontology.classes_in_signature())

    def num_object_properties(self) -> int:
        """Return the number of object properties in the ontology signature."""
        return sum(1 for _ in self.ontology.object_properties_in_signature())

    def num_data_properties(self) -> int:
        """Return the number of data properties in the ontology signature."""
        return sum(1 for _ in self.ontology.data_properties_in_signature())

    def num_individuals(self) -> int:
        """Return the number of named individuals in the ontology signature."""
        return sum(1 for _ in self.ontology.individuals_in_signature())

    def num_properties(self) -> int:
        """Return the total number of properties (object + data)."""
        return self.num_object_properties() + self.num_data_properties()

    # ------------------------------------------------------------------
    # Axiom counts
    # ------------------------------------------------------------------

    def num_axioms(self) -> Optional[int]:
        """Return the total number of axioms (via ``__len__`` on the ontology).

        Returns ``None`` when the ontology backend does not support ``__len__``.
        """
        try:
            return len(self.ontology)
        except (TypeError, NotImplementedError):
            return None

    def num_tbox_axioms(self) -> Optional[int]:
        """Return the number of TBox axioms.

        Returns ``None`` when the backend does not implement ``get_tbox_axioms``.
        """
        try:
            return sum(1 for _ in self.ontology.get_tbox_axioms())
        except (NotImplementedError, AttributeError):
            return None

    def num_abox_axioms(self) -> Optional[int]:
        """Return the number of ABox axioms.

        Returns ``None`` when the backend does not implement ``get_abox_axioms``.
        """
        try:
            return sum(1 for _ in self.ontology.get_abox_axioms())
        except (NotImplementedError, AttributeError):
            return None

    def num_rbox_axioms(self) -> Optional[int]:
        """Return the number of RBox axioms.

        Returns ``None`` when the backend does not implement ``get_rbox_axioms``.
        """
        try:
            return sum(1 for _ in self.ontology.get_rbox_axioms())
        except (NotImplementedError, AttributeError):
            return None

    # ------------------------------------------------------------------
    # Ratios
    # ------------------------------------------------------------------

    def class_property_ratio(self) -> Optional[float]:
        """Return total properties / total classes.

        Returns ``None`` when the number of classes is 0.
        """
        nc = self.num_classes()
        if nc == 0:
            return None
        return self.num_properties() / nc

    def avg_population(self) -> Optional[float]:
        """Return total individuals / total classes (average population per class).

        Returns ``None`` when the number of classes is 0.
        """
        nc = self.num_classes()
        if nc == 0:
            return None
        return self.num_individuals() / nc

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Optional[Union[int, float]]]:
        """Return a dictionary of all basic metrics."""
        return {
            "num_classes": self.num_classes(),
            "num_object_properties": self.num_object_properties(),
            "num_data_properties": self.num_data_properties(),
            "num_individuals": self.num_individuals(),
            "num_properties": self.num_properties(),
            "num_axioms": self.num_axioms(),
            "num_tbox_axioms": self.num_tbox_axioms(),
            "num_abox_axioms": self.num_abox_axioms(),
            "num_rbox_axioms": self.num_rbox_axioms(),
            "class_property_ratio": self.class_property_ratio(),
            "avg_population": self.avg_population(),
        }


class HierarchyMetrics:
    """Compute structural metrics that depend on a class/property hierarchy.

    The hierarchy can be supplied directly (as a ``ClassHierarchy``) or built
    from a reasoner.  When a reasoner is given, the class hierarchy is
    constructed lazily on first access.

    Args:
        class_hierarchy: A pre-built class hierarchy.
        reasoner: A reasoner to build the hierarchy from (used when
            ``class_hierarchy`` is not given).
    """

    def __init__(
        self,
        class_hierarchy: Optional[ClassHierarchy] = None,
        reasoner: Optional[AbstractOWLReasoner] = None,
    ):
        if class_hierarchy is None and reasoner is None:
            raise ValueError("Either class_hierarchy or reasoner must be provided.")
        self._class_hierarchy = class_hierarchy
        self._reasoner = reasoner

    @property
    def class_hierarchy(self) -> ClassHierarchy:
        """Lazily build and return the class hierarchy."""
        if self._class_hierarchy is None:
            self._class_hierarchy = ClassHierarchy(self._reasoner)
        return self._class_hierarchy

    # ------------------------------------------------------------------
    # Depth / breadth
    # ------------------------------------------------------------------
    #
    # def class_hierarchy_depth(self) -> int:
    #     """Return the maximum depth of the class hierarchy.
    #
    #     Depth is measured as the length of the longest path from any root
    #     class to any leaf class. An ontology with only root classes (no
    #     sub-class relationships) has depth 0.
    #     """
    #     hierarchy = self.class_hierarchy
    #     roots = set(hierarchy.roots())
    #     if not roots:
    #         return 0
    #
    #     max_depth = 0
    #     # BFS from every root
    #     queue: deque = deque()
    #     for root in roots:
    #         queue.append((root, 0))
    #
    #     while queue:
    #         node, depth = queue.popleft()
    #         children = set(hierarchy.children(node, direct=True))
    #         if not children:
    #             max_depth = max(max_depth, depth)
    #         else:
    #             for child in children:
    #                 queue.append((child, depth + 1))
    #     return max_depth
    #
    # def avg_breadth(self) -> Optional[float]:
    #     """Return the average number of direct sub-classes per non-leaf class.
    #
    #     Returns ``None`` when there are no non-leaf classes.
    #     """
    #     hierarchy = self.class_hierarchy
    #     total_children = 0
    #     non_leaf_count = 0
    #     for entity in hierarchy.items():
    #         children = set(hierarchy.children(entity, direct=True))
    #         if children:
    #             total_children += len(children)
    #             non_leaf_count += 1
    #     if non_leaf_count == 0:
    #         return None
    #     return total_children / non_leaf_count
    #
    # def max_breadth(self) -> int:
    #     """Return the maximum number of direct sub-classes of any single class."""
    #     hierarchy = self.class_hierarchy
    #     max_b = 0
    #     for entity in hierarchy.items():
    #         children = set(hierarchy.children(entity, direct=True))
    #         max_b = max(max_b, len(children))
    #     return max_b
    #
    # def num_leaf_classes(self) -> int:
    #     """Return the number of leaf classes (classes with no sub-classes)."""
    #     return sum(1 for _ in self.class_hierarchy.leaves())
    #
    # def num_root_classes(self) -> int:
    #     """Return the number of root classes (classes with no super-classes)."""
    #     return sum(1 for _ in self.class_hierarchy.roots())
    #
    # def leaf_class_ratio(self) -> Optional[float]:
    #     """Return the fraction of classes that are leaf classes.
    #
    #     Returns ``None`` when the hierarchy is empty.
    #     """
    #     total = len(self.class_hierarchy)
    #     if total == 0:
    #         return None
    #     return self.num_leaf_classes() / total
    #
    # # ------------------------------------------------------------------
    # # Summary
    # # ------------------------------------------------------------------
    #
    # def summary(self) -> Dict[str, Optional[Union[int, float]]]:
    #     """Return a dictionary of all hierarchy metrics."""
    #     return {
    #         "class_hierarchy_depth": self.class_hierarchy_depth(),
    #         "avg_breadth": self.avg_breadth(),
    #         "max_breadth": self.max_breadth(),
    #         "num_leaf_classes": self.num_leaf_classes(),
    #         "num_root_classes": self.num_root_classes(),
    #         "leaf_class_ratio": self.leaf_class_ratio(),
    #     }


class KBMetrics:
    """Knowledge-base level metrics that require a reasoner to compute.

    These metrics assess how well the ABox (individuals) is covered by the
    TBox (schema).

    Args:
        ontology: The ontology to measure.
        reasoner: A reasoner for type/instance queries.
    """

    def __init__(self, ontology: AbstractOWLOntology, reasoner: AbstractOWLReasoner):
        self.ontology = ontology
        self.reasoner = reasoner

    def class_richness(self) -> Optional[float]:
        """Return the fraction of classes that have at least one instance.

        Uses ``reasoner.instances(cls, direct=True)`` to check each class.
        Returns ``None`` when the number of classes is 0.
        """
        classes = list(self.ontology.classes_in_signature())
        if not classes:
            return None
        populated = 0
        for cls in classes:
            if any(True for _ in self.reasoner.instances(cls, direct=True)):
                populated += 1
        return populated / len(classes)

    def avg_instances_per_class(self) -> Optional[float]:
        """Return the average number of (direct) instances per class.

        Returns ``None`` when the number of classes is 0.
        """
        classes = list(self.ontology.classes_in_signature())
        if not classes:
            return None
        total_instances = 0
        for cls in classes:
            total_instances += sum(1 for _ in self.reasoner.instances(cls, direct=True))
        return total_instances / len(classes)

    def individual_type_richness(self) -> Optional[float]:
        """Return the average number of (direct) types per individual.

        Uses ``reasoner.types(ind, direct=True)`` for each individual.
        Returns ``None`` when there are no individuals.
        """
        individuals = list(self.ontology.individuals_in_signature())
        if not individuals:
            return None
        total_types = 0
        for ind in individuals:
            total_types += sum(1 for _ in self.reasoner.types(ind, direct=True))
        return total_types / len(individuals)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Optional[float]]:
        """Return a dictionary of all knowledge-base metrics."""
        return {
            "class_richness": self.class_richness(),
            "avg_instances_per_class": self.avg_instances_per_class(),
            "individual_type_richness": self.individual_type_richness(),
        }
