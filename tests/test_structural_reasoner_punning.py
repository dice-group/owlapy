"""Regression tests for issue #242: StructuralReasoner must not crash on ontologies
with illegally punned properties (e.g. KGs/Biopax/biopax.owl, where glycolysis#DELTA-G
is declared as both an ObjectProperty and an AnnotationProperty)."""
import logging

from owlapy.class_expression import OWLThing
from owlapy.owl_ontology import Ontology
from owlapy.owl_property import OWLObjectProperty
from owlapy.owl_reasoner import StructuralReasoner

NS = "http://www.biopax.org/examples/glycolysis#"


class TestStructuralReasonerPunnedProperties:

    def test_object_property_values_skips_malformed_values(self, caplog):
        reasoner = StructuralReasoner(Ontology("KGs/Biopax/biopax.owl"))
        participants = OWLObjectProperty(NS + "PARTICIPANTS")
        individuals = list(reasoner.instances(OWLThing))
        assert len(individuals) == 323

        total_values = 0
        with caplog.at_level(logging.WARNING, logger="owlapy.owl_reasoner"):
            for ind in individuals:
                for val in reasoner.object_property_values(ind, participants):
                    assert val.iri is not None
                    total_values += 1
        assert total_values > 0

        warnings = [r for r in caplog.records if "malformed" in r.getMessage()]
        assert len(warnings) == 1, "should warn exactly once per property, not once per value"
        assert "PARTICIPANTS" in warnings[0].getMessage()

    def test_all_property_individual_pairs_do_not_crash(self):
        onto = Ontology("KGs/Biopax/biopax.owl")
        reasoner = StructuralReasoner(onto)
        individuals = list(reasoner.instances(OWLThing))
        for prop in onto.object_properties_in_signature():
            for ind in individuals:
                for direct in (True, False):
                    for val in reasoner.object_property_values(ind, prop, direct=direct):
                        assert val.iri is not None
