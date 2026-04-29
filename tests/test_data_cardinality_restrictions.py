"""
Unit tests for OWLDataMinCardinality, OWLDataMaxCardinality, and OWLDataExactCardinality
_find_instances specializations in StructuralReasoner, using the Mutagenesis dataset.

Key dataset facts (Mutagenesis):
  - Total individuals: 14145
  - Individuals with 'charge' (xsd:double, exactly 1 per individual): 5894
  - Individuals with 'lumo'   (xsd:double, exactly 1 per individual): 230
  - Individuals with 'act'    (xsd:double, exactly 1 per individual): 230
  - No individual has more than 1 value for any single data property
"""
import unittest

from owlapy.class_expression import (
    OWLDataMinCardinality,
    OWLDataMaxCardinality,
    OWLDataExactCardinality,
    OWLDataSomeValuesFrom,
    OWLClass,
)
from owlapy.iri import IRI
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import Ontology
from owlapy.owl_property import OWLDataProperty
from owlapy.owl_reasoner import StructuralReasoner
from owlapy.providers import (
    owl_datatype_min_inclusive_restriction,
    owl_datatype_min_max_inclusive_restriction,
    owl_datatype_max_inclusive_restriction,
)
from owlapy.vocab import XSDVocabulary


NS = "http://dl-learner.org/mutagenesis#"
ONTOLOGY_PATH = "KGs/Mutagenesis/mutagenesis.owl"

# Known cardinalities derived from the dataset
TOTAL_INDIVIDUALS = 14145
INDIVIDUALS_WITH_CHARGE = 5894   # atoms that have a 'charge' double value
INDIVIDUALS_WITH_LUMO = 230      # compounds that have a 'lumo' double value
INDIVIDUALS_WITH_ACT = 230       # compounds that have an 'act' double value
INDIVIDUALS_WITH_POSITIVE_CHARGE = 2925   # charge >= 0.0


class TestDataCardinalityRestrictionsWithDatatype(unittest.TestCase):
    """
    Tests for OWLDataMinCardinality, OWLDataMaxCardinality, OWLDataExactCardinality
    using xsd:double as the filler (bare datatype).
    """

    @classmethod
    def setUpClass(cls):
        cls.onto = Ontology(ONTOLOGY_PATH)
        cls.reasoner = StructuralReasoner(cls.onto)
        cls.all_inds = frozenset(cls.onto.individuals_in_signature())

        cls.charge_dp = OWLDataProperty(IRI(NS, "charge"))
        cls.lumo_dp = OWLDataProperty(IRI(NS, "lumo"))
        cls.act_dp = OWLDataProperty(IRI(NS, "act"))
        cls.double_type = OWLDatatype(XSDVocabulary.DOUBLE)

    # ------------------------------------------------------------------
    # OWLDataMinCardinality – xsd:double filler
    # ------------------------------------------------------------------

    def test_min_cardinality_1_charge_double_returns_all_atoms_with_charge(self):
        """Min(1, charge, xsd:double) should match all atoms having a charge value."""
        ce = OWLDataMinCardinality(cardinality=1, property=self.charge_dp,
                                   filler=self.double_type)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), INDIVIDUALS_WITH_CHARGE)

    def test_min_cardinality_2_charge_double_returns_empty(self):
        """Min(2, charge, xsd:double) should be empty: no individual has 2+ charge values."""
        ce = OWLDataMinCardinality(cardinality=2, property=self.charge_dp,
                                   filler=self.double_type)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), 0)

    def test_min_cardinality_0_charge_double_returns_all_with_charge(self):
        """Min(0, charge, xsd:double) should match everything that has >=0 matching values.
        Because the cache only iterates individuals that have the property, this equals
        the set of individuals possessing a charge value."""
        ce = OWLDataMinCardinality(cardinality=0, property=self.charge_dp,
                                   filler=self.double_type)
        result = set(self.reasoner.instances(ce))
        # Every individual in dps satisfies count >= 0
        self.assertEqual(len(result), INDIVIDUALS_WITH_CHARGE)

    def test_min_cardinality_1_lumo_double(self):
        """Min(1, lumo, xsd:double) should match all compounds with a lumo value."""
        ce = OWLDataMinCardinality(cardinality=1, property=self.lumo_dp,
                                   filler=self.double_type)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), INDIVIDUALS_WITH_LUMO)

    def test_min_cardinality_1_act_double(self):
        """Min(1, act, xsd:double) should match all compounds with an act value."""
        ce = OWLDataMinCardinality(cardinality=1, property=self.act_dp,
                                   filler=self.double_type)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), INDIVIDUALS_WITH_ACT)

    # ------------------------------------------------------------------
    # OWLDataMaxCardinality – xsd:double filler
    # ------------------------------------------------------------------

    def test_max_cardinality_0_charge_double_is_complement_of_min1(self):
        """Max(0, charge, xsd:double) == all_individuals - Min(1, charge, xsd:double)."""
        min1_ce = OWLDataMinCardinality(cardinality=1, property=self.charge_dp,
                                        filler=self.double_type)
        max0_ce = OWLDataMaxCardinality(cardinality=0, property=self.charge_dp,
                                        filler=self.double_type)

        min1_result = set(self.reasoner.instances(min1_ce))
        max0_result = set(self.reasoner.instances(max0_ce))

        self.assertEqual(max0_result, self.all_inds - min1_result)

    def test_max_cardinality_0_charge_double_count(self):
        """Max(0, charge, xsd:double) should return individuals without a charge value."""
        ce = OWLDataMaxCardinality(cardinality=0, property=self.charge_dp,
                                   filler=self.double_type)
        result = set(self.reasoner.instances(ce))
        expected_count = TOTAL_INDIVIDUALS - INDIVIDUALS_WITH_CHARGE
        self.assertEqual(len(result), expected_count)

    def test_max_cardinality_1_charge_double_returns_all_individuals(self):
        """Max(1, charge, xsd:double) should return all individuals because none has 2+ values."""
        ce = OWLDataMaxCardinality(cardinality=1, property=self.charge_dp,
                                   filler=self.double_type)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), TOTAL_INDIVIDUALS)

    def test_max_cardinality_0_lumo_double_count(self):
        """Max(0, lumo, xsd:double) should return individuals without a lumo value."""
        ce = OWLDataMaxCardinality(cardinality=0, property=self.lumo_dp,
                                   filler=self.double_type)
        result = set(self.reasoner.instances(ce))
        expected_count = TOTAL_INDIVIDUALS - INDIVIDUALS_WITH_LUMO
        self.assertEqual(len(result), expected_count)

    # ------------------------------------------------------------------
    # OWLDataExactCardinality – xsd:double filler
    # ------------------------------------------------------------------

    def test_exact_cardinality_1_charge_double_equals_min1(self):
        """Exact(1, charge, xsd:double) == Min(1, charge, xsd:double) when every atom has exactly 1 charge."""
        min1_ce = OWLDataMinCardinality(cardinality=1, property=self.charge_dp,
                                        filler=self.double_type)
        exact1_ce = OWLDataExactCardinality(cardinality=1, property=self.charge_dp,
                                            filler=self.double_type)

        min1_result = set(self.reasoner.instances(min1_ce))
        exact1_result = set(self.reasoner.instances(exact1_ce))

        self.assertEqual(exact1_result, min1_result)

    def test_exact_cardinality_1_charge_double_count(self):
        """Exact(1, charge, xsd:double) should return exactly 5894 atoms."""
        ce = OWLDataExactCardinality(cardinality=1, property=self.charge_dp,
                                     filler=self.double_type)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), INDIVIDUALS_WITH_CHARGE)

    def test_exact_cardinality_2_charge_double_is_empty(self):
        """Exact(2, charge, xsd:double) should be empty because no individual has 2 charge values."""
        ce = OWLDataExactCardinality(cardinality=2, property=self.charge_dp,
                                     filler=self.double_type)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), 0)

    def test_exact_cardinality_1_lumo_double_count(self):
        """Exact(1, lumo, xsd:double) should return the 230 compounds with exactly 1 lumo value."""
        ce = OWLDataExactCardinality(cardinality=1, property=self.lumo_dp,
                                     filler=self.double_type)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), INDIVIDUALS_WITH_LUMO)

    # ------------------------------------------------------------------
    # Logical consistency checks
    # ------------------------------------------------------------------

    def test_min1_and_max0_are_disjoint(self):
        """Min(1, charge, double) and Max(0, charge, double) must be disjoint."""
        min1_ce = OWLDataMinCardinality(cardinality=1, property=self.charge_dp,
                                        filler=self.double_type)
        max0_ce = OWLDataMaxCardinality(cardinality=0, property=self.charge_dp,
                                        filler=self.double_type)
        min1_result = set(self.reasoner.instances(min1_ce))
        max0_result = set(self.reasoner.instances(max0_ce))
        self.assertEqual(min1_result & max0_result, set())

    def test_min1_and_max0_cover_all_individuals(self):
        """Min(1, charge, double) ∪ Max(0, charge, double) == all individuals."""
        min1_ce = OWLDataMinCardinality(cardinality=1, property=self.charge_dp,
                                        filler=self.double_type)
        max0_ce = OWLDataMaxCardinality(cardinality=0, property=self.charge_dp,
                                        filler=self.double_type)
        min1_result = set(self.reasoner.instances(min1_ce))
        max0_result = set(self.reasoner.instances(max0_ce))
        self.assertEqual(min1_result | max0_result, self.all_inds)

    def test_min1_and_max0_lumo_cover_all_individuals(self):
        """Min(1, lumo, double) ∪ Max(0, lumo, double) == all individuals."""
        min1_ce = OWLDataMinCardinality(cardinality=1, property=self.lumo_dp,
                                        filler=self.double_type)
        max0_ce = OWLDataMaxCardinality(cardinality=0, property=self.lumo_dp,
                                        filler=self.double_type)
        min1_result = set(self.reasoner.instances(min1_ce))
        max0_result = set(self.reasoner.instances(max0_ce))
        self.assertEqual(min1_result | max0_result, self.all_inds)

    def test_min1_subset_of_max1_for_charge(self):
        """Min(1, charge, double) ⊆ Max(1, charge, double) (both include individuals with 1 value)."""
        min1_ce = OWLDataMinCardinality(cardinality=1, property=self.charge_dp,
                                        filler=self.double_type)
        max1_ce = OWLDataMaxCardinality(cardinality=1, property=self.charge_dp,
                                        filler=self.double_type)
        min1_result = set(self.reasoner.instances(min1_ce))
        max1_result = set(self.reasoner.instances(max1_ce))
        self.assertTrue(min1_result.issubset(max1_result))


class TestDataCardinalityRestrictionsWithDatatypeRestriction(unittest.TestCase):
    """
    Tests using OWLDatatypeRestriction as filler (e.g., charge >= 0.0).
    """

    @classmethod
    def setUpClass(cls):
        cls.onto = Ontology(ONTOLOGY_PATH)
        cls.reasoner = StructuralReasoner(cls.onto)
        cls.all_inds = frozenset(cls.onto.individuals_in_signature())

        cls.charge_dp = OWLDataProperty(IRI(NS, "charge"))
        cls.lumo_dp = OWLDataProperty(IRI(NS, "lumo"))

        # Filler: charge >= 0.0 (positive or neutral charges)
        cls.positive_charge_filler = owl_datatype_min_inclusive_restriction(0.0)
        # Filler: lumo >= -1.5
        cls.lumo_gte_minus1_5 = owl_datatype_min_inclusive_restriction(-1.5)

    # ------------------------------------------------------------------
    # OWLDataMinCardinality – DatatypeRestriction filler
    # ------------------------------------------------------------------

    def test_min_cardinality_1_positive_charge(self):
        """Min(1, charge, charge>=0) should match atoms with at least 1 non-negative charge."""
        ce = OWLDataMinCardinality(cardinality=1, property=self.charge_dp,
                                   filler=self.positive_charge_filler)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), INDIVIDUALS_WITH_POSITIVE_CHARGE)

    def test_min_cardinality_2_positive_charge_is_empty(self):
        """Min(2, charge, charge>=0) should be empty because each atom has at most 1 charge value."""
        ce = OWLDataMinCardinality(cardinality=2, property=self.charge_dp,
                                   filler=self.positive_charge_filler)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), 0)

    def test_min_cardinality_1_lumo_gte_minus1_5(self):
        """Min(1, lumo, lumo>=-1.5) should match compounds whose lumo value is >= -1.5."""
        ce = OWLDataMinCardinality(cardinality=1, property=self.lumo_dp,
                                   filler=self.lumo_gte_minus1_5)
        result = set(self.reasoner.instances(ce))
        # Verify: same as OWLDataSomeValuesFrom(lumo, lumo>=-1.5)
        svf = OWLDataSomeValuesFrom(property=self.lumo_dp, filler=self.lumo_gte_minus1_5)
        svf_result = set(self.reasoner.instances(svf))
        self.assertEqual(result, svf_result)
        self.assertEqual(len(result), 99)  # 99 compounds have lumo >= -1.5

    # ------------------------------------------------------------------
    # OWLDataMaxCardinality – DatatypeRestriction filler
    # ------------------------------------------------------------------

    def test_max_cardinality_0_positive_charge_count(self):
        """Max(0, charge, charge>=0) should return individuals that have no non-negative charge value."""
        ce = OWLDataMaxCardinality(cardinality=0, property=self.charge_dp,
                                   filler=self.positive_charge_filler)
        result = set(self.reasoner.instances(ce))
        expected = TOTAL_INDIVIDUALS - INDIVIDUALS_WITH_POSITIVE_CHARGE
        self.assertEqual(len(result), expected)

    def test_max_cardinality_0_positive_charge_is_complement_of_min1(self):
        """Max(0, charge, >=0) == all_individuals - Min(1, charge, >=0)."""
        min1_ce = OWLDataMinCardinality(cardinality=1, property=self.charge_dp,
                                        filler=self.positive_charge_filler)
        max0_ce = OWLDataMaxCardinality(cardinality=0, property=self.charge_dp,
                                        filler=self.positive_charge_filler)
        min1_result = set(self.reasoner.instances(min1_ce))
        max0_result = set(self.reasoner.instances(max0_ce))
        self.assertEqual(max0_result, self.all_inds - min1_result)

    def test_max_cardinality_1_positive_charge_returns_all(self):
        """Max(1, charge, charge>=0) == all individuals because no atom has 2+ charge values."""
        ce = OWLDataMaxCardinality(cardinality=1, property=self.charge_dp,
                                   filler=self.positive_charge_filler)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), TOTAL_INDIVIDUALS)

    # ------------------------------------------------------------------
    # OWLDataExactCardinality – DatatypeRestriction filler
    # ------------------------------------------------------------------

    def test_exact_cardinality_1_positive_charge(self):
        """Exact(1, charge, charge>=0) should match atoms with exactly 1 non-negative charge."""
        ce = OWLDataExactCardinality(cardinality=1, property=self.charge_dp,
                                     filler=self.positive_charge_filler)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), INDIVIDUALS_WITH_POSITIVE_CHARGE)

    def test_exact_cardinality_1_positive_charge_equals_min1(self):
        """Exact(1, charge, >=0) == Min(1, charge, >=0) since each atom has at most 1 charge."""
        min1_ce = OWLDataMinCardinality(cardinality=1, property=self.charge_dp,
                                        filler=self.positive_charge_filler)
        exact1_ce = OWLDataExactCardinality(cardinality=1, property=self.charge_dp,
                                            filler=self.positive_charge_filler)
        self.assertEqual(set(self.reasoner.instances(min1_ce)),
                         set(self.reasoner.instances(exact1_ce)))

    def test_exact_cardinality_2_positive_charge_is_empty(self):
        """Exact(2, charge, charge>=0) should be empty."""
        ce = OWLDataExactCardinality(cardinality=2, property=self.charge_dp,
                                     filler=self.positive_charge_filler)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), 0)

    # ------------------------------------------------------------------
    # Logical consistency checks
    # ------------------------------------------------------------------

    def test_min1_and_max0_positive_charge_cover_all(self):
        """Min(1, charge, >=0) ∪ Max(0, charge, >=0) == all individuals."""
        min1_ce = OWLDataMinCardinality(cardinality=1, property=self.charge_dp,
                                        filler=self.positive_charge_filler)
        max0_ce = OWLDataMaxCardinality(cardinality=0, property=self.charge_dp,
                                        filler=self.positive_charge_filler)
        self.assertEqual(set(self.reasoner.instances(min1_ce)) |
                         set(self.reasoner.instances(max0_ce)),
                         self.all_inds)

    def test_min1_and_max0_positive_charge_are_disjoint(self):
        """Min(1, charge, >=0) ∩ Max(0, charge, >=0) == ∅."""
        min1_ce = OWLDataMinCardinality(cardinality=1, property=self.charge_dp,
                                        filler=self.positive_charge_filler)
        max0_ce = OWLDataMaxCardinality(cardinality=0, property=self.charge_dp,
                                        filler=self.positive_charge_filler)
        self.assertEqual(set(self.reasoner.instances(min1_ce)) &
                         set(self.reasoner.instances(max0_ce)),
                         set())


class TestDataCardinalityRestrictionsWithRangeRestriction(unittest.TestCase):
    """
    Tests using a bounded range (min_max inclusive) as the filler.
    """

    @classmethod
    def setUpClass(cls):
        cls.onto = Ontology(ONTOLOGY_PATH)
        cls.reasoner = StructuralReasoner(cls.onto)
        cls.all_inds = frozenset(cls.onto.individuals_in_signature())

        cls.charge_dp = OWLDataProperty(IRI(NS, "charge"))
        cls.lumo_dp = OWLDataProperty(IRI(NS, "lumo"))

        # Filler: -0.1 <= charge <= 0.1  (near-neutral charges)
        cls.near_neutral_filler = owl_datatype_min_max_inclusive_restriction(-0.1, 0.1)

    def test_min_cardinality_1_near_neutral_charge(self):
        """Min(1, charge, -0.1<=charge<=0.1) counts atoms with near-neutral charge."""
        ce = OWLDataMinCardinality(cardinality=1, property=self.charge_dp,
                                   filler=self.near_neutral_filler)
        result = set(self.reasoner.instances(ce))
        # Should equal OWLDataSomeValuesFrom with the same range restriction
        svf = OWLDataSomeValuesFrom(property=self.charge_dp, filler=self.near_neutral_filler)
        svf_result = set(self.reasoner.instances(svf))
        self.assertEqual(result, svf_result)
        self.assertGreater(len(result), 0)

    def test_max_cardinality_0_near_neutral_is_complement_of_min1(self):
        """Max(0, charge, -0.1<=c<=0.1) == all - Min(1, charge, -0.1<=c<=0.1)."""
        min1_ce = OWLDataMinCardinality(cardinality=1, property=self.charge_dp,
                                        filler=self.near_neutral_filler)
        max0_ce = OWLDataMaxCardinality(cardinality=0, property=self.charge_dp,
                                        filler=self.near_neutral_filler)
        min1_result = set(self.reasoner.instances(min1_ce))
        max0_result = set(self.reasoner.instances(max0_ce))
        self.assertEqual(max0_result, self.all_inds - min1_result)

    def test_exact_cardinality_1_near_neutral_equals_min1(self):
        """Exact(1, charge, range) == Min(1, charge, range) when no atom has 2+ matching values."""
        min1_ce = OWLDataMinCardinality(cardinality=1, property=self.charge_dp,
                                        filler=self.near_neutral_filler)
        exact1_ce = OWLDataExactCardinality(cardinality=1, property=self.charge_dp,
                                            filler=self.near_neutral_filler)
        self.assertEqual(set(self.reasoner.instances(min1_ce)),
                         set(self.reasoner.instances(exact1_ce)))

    def test_min1_and_max0_near_neutral_cover_all(self):
        """Min(1) ∪ Max(0) covers all individuals for any filler."""
        min1_ce = OWLDataMinCardinality(cardinality=1, property=self.charge_dp,
                                        filler=self.near_neutral_filler)
        max0_ce = OWLDataMaxCardinality(cardinality=0, property=self.charge_dp,
                                        filler=self.near_neutral_filler)
        self.assertEqual(set(self.reasoner.instances(min1_ce)) |
                         set(self.reasoner.instances(max0_ce)),
                         self.all_inds)


class TestDataCardinalityRestrictionsWithNoCacheReasoner(unittest.TestCase):
    """
    Same tests but with property_cache=False to exercise the non-cached code paths.
    Uses only `lumo` to keep runtime acceptable with the non-cached reasoner.
    """

    @classmethod
    def setUpClass(cls):
        cls.onto = Ontology(ONTOLOGY_PATH)
        # Disable caches to exercise the non-cached branch
        cls.reasoner = StructuralReasoner(cls.onto, property_cache=False, class_cache=False)
        cls.all_inds = frozenset(cls.onto.individuals_in_signature())

        cls.lumo_dp = OWLDataProperty(IRI(NS, "lumo"))
        cls.double_type = OWLDatatype(XSDVocabulary.DOUBLE)
        cls.lumo_filler = owl_datatype_min_inclusive_restriction(-1.5)

    def test_min_cardinality_1_lumo_no_cache(self):
        """Min(1, lumo, xsd:double) without cache returns the same count as with cache."""
        ce = OWLDataMinCardinality(cardinality=1, property=self.lumo_dp,
                                   filler=self.double_type)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), INDIVIDUALS_WITH_LUMO)

    def test_min_cardinality_2_lumo_no_cache_is_empty(self):
        """Min(2, lumo, xsd:double) without cache should be empty."""
        ce = OWLDataMinCardinality(cardinality=2, property=self.lumo_dp,
                                   filler=self.double_type)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), 0)

    def test_exact_cardinality_1_lumo_no_cache(self):
        """Exact(1, lumo, xsd:double) without cache should match all compounds with a lumo value."""
        ce = OWLDataExactCardinality(cardinality=1, property=self.lumo_dp,
                                     filler=self.double_type)
        result = set(self.reasoner.instances(ce))
        self.assertEqual(len(result), INDIVIDUALS_WITH_LUMO)

    def test_max_cardinality_0_lumo_no_cache_count(self):
        """Max(0, lumo, xsd:double) without cache returns individuals without a lumo value."""
        ce = OWLDataMaxCardinality(cardinality=0, property=self.lumo_dp,
                                   filler=self.double_type)
        result = set(self.reasoner.instances(ce))
        expected = TOTAL_INDIVIDUALS - INDIVIDUALS_WITH_LUMO
        self.assertEqual(len(result), expected)

    def test_min1_max0_lumo_cover_all_no_cache(self):
        """Min(1, lumo, double) ∪ Max(0, lumo, double) == all individuals (no-cache)."""
        min1_ce = OWLDataMinCardinality(cardinality=1, property=self.lumo_dp,
                                        filler=self.double_type)
        max0_ce = OWLDataMaxCardinality(cardinality=0, property=self.lumo_dp,
                                        filler=self.double_type)
        self.assertEqual(set(self.reasoner.instances(min1_ce)) |
                         set(self.reasoner.instances(max0_ce)),
                         self.all_inds)

    def test_min_cardinality_1_lumo_restriction_no_cache(self):
        """Min(1, lumo, lumo>=-1.5) without cache equals OWLDataSomeValuesFrom result."""
        ce = OWLDataMinCardinality(cardinality=1, property=self.lumo_dp,
                                   filler=self.lumo_filler)
        svf = OWLDataSomeValuesFrom(property=self.lumo_dp, filler=self.lumo_filler)
        self.assertEqual(set(self.reasoner.instances(ce)),
                         set(self.reasoner.instances(svf)))


if __name__ == "__main__":
    unittest.main()

