"""Classes representing hierarchy in OWL."""

import operator
from abc import ABCMeta, abstractmethod
from functools import reduce
from typing import Dict, Iterable, Tuple, overload, TypeVar, Generic, Type, cast, Optional, FrozenSet, Set

from owlapy.class_expression import OWLClass, OWLThing, OWLNothing
from owlapy.meta_classes import HasIRI
from owlapy.owl_literal import OWLTopObjectProperty, OWLBottomObjectProperty, OWLTopDataProperty, OWLBottomDataProperty
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty
from owlapy.owl_reasoner import OWLReasoner

_S = TypeVar('_S', bound=HasIRI)  #:
_U = TypeVar('_U', bound='AbstractHierarchy')  #:


class AbstractHierarchy(Generic[_S], metaclass=ABCMeta):
    """Representation of an abstract hierarchy which can be used for classes or properties.

    Args:
        hierarchy_down: A downwards hierarchy given as a mapping of Entities to sub-entities.
        reasoner: Alternatively, a reasoner whose root_ontology is queried for entities.
        """
    __slots__ = '_Type', '_ent_set', '_parents_map', '_parents_map_trans', '_children_map', '_children_map_trans', \
                '_leaf_set', '_root_set', \
        # '_eq_set'

    _ent_set: FrozenSet[_S]
    _parents_map: Dict[_S, Set[_S]]  # Entity => parent entities
    _parents_map_trans: Dict[_S, Set[_S]]  # Entity => parent entities
    _children_map: Dict[_S, Set[_S]]  # Entity => child entities
    _children_map_trans: Dict[_S, Set[_S]]  # Entity => child entities
    # _eq_set: Dict[_S, Set[_S]]  # Entity => equivalent entities  # TODO
    _root_set: Set[_S]  # root entities
    _leaf_set: Set[_S]  # leaf entities

    @overload
    def __init__(self, factory: Type[_S], hierarchy_down: Iterable[Tuple[_S, Iterable[_S]]]):
        ...

    @overload
    def __init__(self, factory: Type[_S], reasoner: OWLReasoner):
        ...

    @abstractmethod
    def __init__(self, factory: Type[_S], arg):
        self._Type = factory
        if isinstance(arg, OWLReasoner):
            hier_down_gen = self._hierarchy_down_generator(arg)
            self._init(hier_down_gen)
        else:
            self._init(arg)

    @abstractmethod
    def _hierarchy_down_generator(self, reasoner: OWLReasoner) -> Iterable[Tuple[_S, Iterable[_S]]]:
        """Generate the suitable downwards hierarchy based on the reasoner."""
        pass

    @classmethod
    @abstractmethod
    def get_top_entity(cls) -> _S:
        """The most general entity in this hierarchy, which contains all the entities."""
        pass

    @classmethod
    @abstractmethod
    def get_bottom_entity(cls) -> _S:
        """The most specific entity in this hierarchy, which contains none of the entities."""
        pass

    @staticmethod
    def restrict(hierarchy: _U, *, remove: Iterable[_S] = None, allow: Iterable[_S] = None) \
            -> _U:
        """Restrict a given hierarchy to a set of allowed/removed entities.

        Args:
            hierarchy: An existing Entity hierarchy to restrict.
            remove: Set of entities which should be ignored.
            allow: Set of entities which should be used.

        Returns:
            The restricted hierarchy.

        """
        remove_set = frozenset(remove) if remove is not None else None
        allow_set = frozenset(allow) if allow is not None else None

        def _filter(_: _S):
            if remove_set is None or _ not in remove_set:
                if allow_set is None or _ in allow_set:
                    return True
            return False

        _gen = ((_, filter(_filter, hierarchy.children(_, direct=False)))
                for _ in filter(_filter, hierarchy.items()))

        return type(hierarchy)(_gen)

    def restrict_and_copy(self: _U, *, remove: Iterable[_S] = None, allow: Iterable[_S] = None) \
            -> _U:
        """Restrict this hierarchy.

        See restrict for more info.
        """
        return type(self).restrict(self, remove=remove, allow=allow)

    def _init(self, hierarchy_down: Iterable[Tuple[_S, Iterable[_S]]]) -> None:
        self._parents_map_trans = dict()
        self._children_map_trans = dict()
        # self._eq_set = dict()

        ent_to_sub_entities = dict(hierarchy_down)
        self._ent_set = frozenset(ent_to_sub_entities.keys())

        for ent, sub_it in ent_to_sub_entities.items():
            self._children_map_trans[ent] = set(sub_it)
            self._parents_map_trans[ent] = set()  # create empty parent entry for all classes

        del ent_to_sub_entities  # exhausted

        # calculate transitive children
        for ent in self._children_map_trans:
            _children_transitive(self._children_map_trans, ent=ent, seen_set=set())

        # TODO handling of eq_sets
        # sccs = list(_strongly_connected_components(self._children_map_trans))
        # for scc in sccs:
        #     sub_entities = 0
        #     for ent_enc in iter_bits(scc):
        #         self._eq_set[ent_enc] = scc
        #         sub_entities |= self._children_map_trans[ent_enc]
        #         del self._children_map_trans[ent_enc]
        #         del self._parents_map_trans[ent_enc]
        #     self._children_map_trans[scc] = sub_entities
        #     self._parents_map_trans[scc] = 0

        # fill transitive parents
        for ent, sub_entities in self._children_map_trans.items():
            for sub in sub_entities:
                self._parents_map_trans[sub] |= {ent}

        self._children_map, self._leaf_set = _reduce_transitive(self._children_map_trans, self._parents_map_trans)
        self._parents_map, self._root_set = _reduce_transitive(self._parents_map_trans, self._children_map_trans)

    def parents(self, entity: _S, direct: bool = True) -> Iterable[_S]:
        """Parents of an entity.

        Args:
            entity: Entity for which to query parent entities.
            direct: False to return transitive parents.

        Returns:
            Super-entities.

        """
        if entity == type(self).get_bottom_entity():
            if not direct:
                yield from self.items()
            else:
                yield from self.leaves()
        elif entity == type(self).get_top_entity():
            yield from {}
        else:
            if not direct:
                yield from self._parents_map_trans[entity]
            else:
                yield from self._parents_map[entity]

    def is_parent_of(self, a: _S, b: _S) -> bool:
        """if A is a parent of B.

        Note:
              A is always a parent of A."""
        if a == b:
            return True
        if a == type(self).get_top_entity():
            return True
        if {a} & self._parents_map_trans[b]:
            return True
        return False

    def is_child_of(self, a: _S, b: _S) -> bool:
        """If A is a child of B.

        Note:
              A is always a child of A."""
        if a == b:
            return True
        if a == type(self).get_bottom_entity():
            return True
        if {a} & self._children_map_trans[b]:
            return True
        return False

    def children(self, entity: _S, direct: bool = True) -> Iterable[_S]:
        """Children of an entity.

        Args:
            entity: Entity for which to query child entities.
            direct: False to return transitive children.

        Returns:
            Sub-entities.

        """
        if entity == type(self).get_top_entity():
            if not direct:
                yield from self.items()
            else:
                yield from self.roots()
        elif entity == type(self).get_bottom_entity():
            yield from {}
        else:
            if not direct:
                yield from self._children_map_trans[entity]
            else:
                yield from self._children_map[entity]

    def siblings(self, entity: _S) -> Iterable[_S]:
        seen_set = {entity}
        for parent in self.parents(entity, direct=True):
            for sibling in self.children(parent, direct=True):
                if sibling not in seen_set:
                    yield sibling
                    seen_set.add(sibling)

    def items(self) -> Iterable[_S]:
        yield from self._ent_set

    def roots(self, of: Optional[_S] = None) -> Iterable[_S]:
        if of is not None and of != type(self).get_bottom_entity():
            yield from self._root_set & self._parents_map_trans[of]
        else:
            yield from self._root_set

    def leaves(self, of: Optional[_S] = None) -> Iterable[_S]:
        if of is not None and of != type(self).get_top_entity():
            yield from self._leaf_set & self._children_map_trans[of]
        else:
            yield from self._leaf_set

    def __contains__(self, item: _S) -> bool:
        return item in self._ent_set

    def __len__(self):
        return len(self._ent_set)


class ClassHierarchy(AbstractHierarchy[OWLClass]):
    """Representation of a class hierarchy.

    Args:
        hierarchy_down: A downwards hierarchy given as a mapping of Class to sub-classes.
        reasoner: Alternatively, a reasoner whose root_ontology is queried for classes and sub-classes.
        """

    @classmethod
    def get_top_entity(cls) -> OWLClass:
        return OWLThing

    @classmethod
    def get_bottom_entity(cls) -> OWLClass:
        return OWLNothing

    def _hierarchy_down_generator(self, reasoner: OWLReasoner) -> Iterable[Tuple[OWLClass, Iterable[OWLClass]]]:
        yield from ((_, reasoner.sub_classes(_, direct=True))
                    for _ in reasoner.get_root_ontology().classes_in_signature())

    def sub_classes(self, entity: OWLClass, direct: bool = True) -> Iterable[OWLClass]:
        yield from self.children(entity, direct)

    def super_classes(self, entity: OWLClass, direct: bool = True) -> Iterable[OWLClass]:
        yield from self.parents(entity, direct)

    def is_subclass_of(self, subclass: OWLClass, superclass: OWLClass) -> bool:
        return self.is_child_of(subclass, superclass)

    @overload
    def __init__(self, hierarchy_down: Iterable[Tuple[OWLClass, Iterable[OWLClass]]]): ...

    @overload
    def __init__(self, reasoner: OWLReasoner): ...

    def __init__(self, arg):
        super().__init__(OWLClass, arg)


class ObjectPropertyHierarchy(AbstractHierarchy[OWLObjectProperty]):
    """Representation of an objet property hierarchy."""
    @classmethod
    def get_top_entity(cls) -> OWLObjectProperty:
        return OWLTopObjectProperty

    @classmethod
    def get_bottom_entity(cls) -> OWLObjectProperty:
        return OWLBottomObjectProperty

    def _hierarchy_down_generator(self, reasoner: OWLReasoner) \
            -> Iterable[Tuple[OWLObjectProperty, Iterable[OWLObjectProperty]]]:
        return ((_, map(lambda _: cast(OWLObjectProperty, _),
                        filter(lambda _: isinstance(_, OWLObjectProperty),
                               reasoner.sub_object_properties(_, direct=True))))
                for _ in reasoner.get_root_ontology().object_properties_in_signature())

    def sub_object_properties(self, entity: OWLObjectProperty, direct: bool = True) -> Iterable[OWLObjectProperty]:
        yield from self.children(entity, direct)

    def super_object_properties(self, entity: OWLObjectProperty, direct: bool = True) -> Iterable[OWLObjectProperty]:
        yield from self.parents(entity, direct)

    def more_general_roles(self, role: OWLObjectProperty, direct: bool = True) -> Iterable[OWLObjectProperty]:
        yield from self.parents(role, direct=direct)

    def more_special_roles(self, role: OWLObjectProperty, direct: bool = True) -> Iterable[OWLObjectProperty]:
        yield from self.children(role, direct=direct)

    def is_sub_property_of(self, sub_property: OWLObjectProperty, super_property: OWLObjectProperty) -> bool:
        return self.is_child_of(sub_property, super_property)

    def most_general_roles(self) -> Iterable[OWLObjectProperty]:
        yield from self.roots()

    def most_special_roles(self) -> Iterable[OWLObjectProperty]:
        yield from self.leaves()

    @overload
    def __init__(self, hierarchy_down: Iterable[Tuple[OWLObjectProperty, Iterable[OWLObjectProperty]]]): ...

    @overload
    def __init__(self, reasoner: OWLReasoner): ...

    def __init__(self, arg):
        super().__init__(OWLObjectProperty, arg)


class DatatypePropertyHierarchy(AbstractHierarchy[OWLDataProperty]):
    """Representation of a data property hierarchy."""
    @classmethod
    def get_top_entity(cls) -> OWLDataProperty:
        return OWLTopDataProperty

    @classmethod
    def get_bottom_entity(cls) -> OWLDataProperty:
        return OWLBottomDataProperty

    def _hierarchy_down_generator(self, reasoner: OWLReasoner) \
            -> Iterable[Tuple[OWLDataProperty, Iterable[OWLDataProperty]]]:
        return ((_, reasoner.sub_data_properties(_, direct=True))
                for _ in reasoner.get_root_ontology().data_properties_in_signature())

    def sub_data_properties(self, entity: OWLDataProperty, direct: bool = True):
        yield from self.children(entity, direct)

    def super_data_properties(self, entity: OWLDataProperty, direct: bool = True):
        yield from self.parents(entity, direct)

    def more_general_roles(self, role: OWLDataProperty, direct: bool = True) -> Iterable[OWLDataProperty]:
        yield from self.parents(role, direct=direct)

    def more_special_roles(self, role: OWLDataProperty, direct: bool = True) -> Iterable[OWLDataProperty]:
        yield from self.children(role, direct=direct)

    def is_sub_property_of(self, sub_property: OWLDataProperty, super_property: OWLDataProperty) -> bool:
        return self.is_child_of(sub_property, super_property)

    def most_general_roles(self) -> Iterable[OWLDataProperty]:
        yield from self.roots()

    def most_special_roles(self) -> Iterable[OWLDataProperty]:
        yield from self.leaves()

    @overload
    def __init__(self, hierarchy_down: Iterable[Tuple[OWLDataProperty, Iterable[OWLDataProperty]]]): ...

    @overload
    def __init__(self, reasoner: OWLReasoner): ...

    def __init__(self, arg):
        super().__init__(OWLDataProperty, arg)


def _children_transitive(hier_trans: Dict[_S, Set[_S]], ent: _S, seen_set: Set[_S]):
    """Add transitive links to map_trans.

    Note:
        Changes map_trans.

    Args:
        hier_trans: Map to which transitive links are added.
        ent: Class in map_trans for which to add transitive sub-classes.

    """
    sub_classes_ent = frozenset(hier_trans[ent])
    for sub_ent in sub_classes_ent:
        if not {sub_ent} & seen_set:
            _children_transitive(hier_trans, sub_ent, seen_set | {ent})
            seen_set = seen_set | {sub_ent} | hier_trans[sub_ent]
            hier_trans[ent] |= hier_trans[sub_ent]


def _reduce_transitive(hier: Dict[_S, Set[_S]], hier_inverse: Dict[_S, Set[_S]]) \
        -> Tuple[Dict[_S, Set[_S]], FrozenSet[_S]]:
    """Remove all transitive links.

    Takes a downward hierarchy and an upward hierarchy with transitive links, and removes all links that can be
    implicitly detected since they are transitive.

    Args:
         hier: downward hierarchy with all transitive links, from Class => sub-classes.
         hier_inverse: upward hierarchy with all transitive links, from Class => super-classes.

    Returns:
        Thin map with only direct sub-classes.
        Set of classes without sub-classes.

    """
    result_hier: Dict[_S, Set[_S]] = dict()
    leaf_set = set()
    for ent, set_ent in hier.items():
        direct_set = set()
        for item_ent in set_ent:
            if not hier_inverse[item_ent] & (set_ent ^ {item_ent}):
                direct_set |= {item_ent}
        result_hier[ent] = direct_set
        if not direct_set:
            leaf_set |= {ent}
    return result_hier, frozenset(leaf_set)


def _strongly_connected_components(graph: Dict[_S, Set[_S]]) -> Iterable[FrozenSet[_S]]:
    """Strongly connected component algorithm.

    Args:
        graph: Directed Graph dictionary, vertex => set of vertices (there is an edge from v to each V).

    Returns:
        The strongly connected components.

    Author: Mario Alviano
    Source: https://github.com/alviano/python/blob/master/rewrite_aggregates/scc.py
    Licence: GPL-3.0
    """
    identified = set()
    stack = []
    index = {}
    boundaries = []

    def dfs(v):
        nonlocal identified
        index[v] = len(stack)
        stack.append({v})
        boundaries.append(index[v])

        for w in graph[v]:
            if w not in index:
                yield from dfs(w)
            elif not {w} & identified:
                while index[w] < boundaries[-1]:
                    boundaries.pop()

        if boundaries[-1] == index[v]:
            boundaries.pop()
            scc = reduce(operator.or_, stack[index[v]:])
            del stack[index[v]:]
            identified |= scc
            yield frozenset(scc)

    for v in graph:
        if v not in index:
            yield from dfs(v)
