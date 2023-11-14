"""Extra classes."""
import logging
from abc import ABCMeta
from typing import Iterable

from owlapy.model import OWLNamedIndividual, OWLObjectProperty, OWLReasoner, OWLDataProperty, OWLDataRange, \
    OWLLiteral


logger = logging.getLogger(__name__)


class OWLReasonerEx(OWLReasoner, metaclass=ABCMeta):
    """Extra convenience methods for OWL Reasoners

    (Not part of OWLAPI)"""

    # default
    def data_property_ranges(self, pe: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataRange]:
        """Gets the data ranges that are the direct or indirect ranges of this property with respect to the imports
        closure of the root ontology.

        Args:
            pe: The property expression whose ranges are to be retrieved.
            direct: Specifies if the direct ranges should be retrieved (True), or if all ranges should be retrieved
                (False).

        Returns:
        """
        for ax in self.get_root_ontology().data_property_range_axioms(pe):
            yield ax.get_range()
            if not direct:
                logger.warning("indirect not implemented")
                # TODO:

    # default
    def all_data_property_values(self, pe: OWLDataProperty, direct: bool = True) -> Iterable[OWLLiteral]:
        """Gets all values for the given data property expression that appear in the knowledge base.

        Args:
            pe: The data property expression whose values are to be retrieved
            direct: Specifies if only the direct values of the data property pe should be retrieved (True), or if
                    the values of sub properties of pe should be taken into account (False).

        Returns:
            A set of OWLLiterals containing literals such that for each literal l in the set, the set of reasoner
            axioms entails DataPropertyAssertion(pe ind l) for any ind.
        """
        onto = self.get_root_ontology()
        for ind in onto.individuals_in_signature():
            for lit in self.data_property_values(ind, pe, direct):
                yield lit

    # default
    def ind_data_properties(self, ind: OWLNamedIndividual, direct: bool = True) -> Iterable[OWLDataProperty]:
        """Gets all data properties for the given individual that appear in the knowledge base.

        Args:
            ind: The named individual whose data properties are to be retrieved
            direct: Specifies if the direct data properties should be retrieved (True), or if all
                data properties should be retrieved (False), so that sub properties are taken into account.

        Returns:
            All data properties pe where the set of reasoner axioms entails DataPropertyAssertion(pe ind l)
            for atleast one l.
        """
        onto = self.get_root_ontology()
        for dp in onto.data_properties_in_signature():
            try:
                next(iter(self.data_property_values(ind, dp, direct)))
                yield dp
            except StopIteration:
                pass

    # default
    def ind_object_properties(self, ind: OWLNamedIndividual, direct: bool = True) -> Iterable[OWLObjectProperty]:
        """Gets all object properties for the given individual that appear in the knowledge base.

        Args:
            ind: The named individual whose object properties are to be retrieved
            direct: Specifies if the direct object properties should be retrieved (True), or if all
                object properties should be retrieved (False), so that sub properties are taken into account.

        Returns:
            All data properties pe where the set of reasoner axioms entails ObjectPropertyAssertion(pe ind ind2)
            for atleast one ind2.
        """
        onto = self.get_root_ontology()
        for op in onto.object_properties_in_signature():
            try:
                next(iter(self.object_property_values(ind, op, direct)))
                yield op
            except StopIteration:
                pass
