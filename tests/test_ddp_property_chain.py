"""
Regression test for distributed (DDP) reasoning with property chains.

Verifies that the distributed reasoner correctly handles property chain
axioms when reasoning is split across multiple shards.

Ontology Setup
--------------
- PropertyChain: r o s -> t  (If x has r to y, and y has s to z, then x has t to z)
- Individuals: a, b, c
- Assertions: r(a, b), s(b, c), C(c)

Expected Behavior
-----------------
Query: ∃ t.C
Ground Truth (single reasoner): {a}
    a -> r -> b -> s -> c implies a -> t -> c. Since c:C, a ∈ ∃ t.C ✓

Known Issue
-----------
With 3 shards, the property chain path is fractured:
- Shard-0 has r(a, b) but misses s(b, c)
- Shard-1 has s(b, c) but misses r(a, b)
- Shard-2 has C(c)
→ No shard can locally infer t(a, c), so the result may be incomplete.

Requirements
------------
- ``ray`` must be installed (``pip install ray``).
"""

import os
import sys
import unittest
from pathlib import Path

# Ensure the repository root is on sys.path so ddp_reasoning_eval can be
# imported regardless of the working directory pytest / unittest uses.
REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


# ---------------------------------------------------------------------------
# Inline ontology for the property chain counterexample
# ---------------------------------------------------------------------------
_CHAIN_NS = "http://example.org/test#"
_CHAIN_OWL = """\
<?xml version="1.0"?>
<rdf:RDF xmlns="http://example.org/test#"
     xml:base="http://example.org/test"
     xmlns:owl="http://www.w3.org/2002/07/owl#"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:xml="http://www.w3.org/XML/1998/namespace"
     xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
     xmlns:test="http://example.org/test#">
    
    <owl:Ontology rdf:about="http://example.org/test"/>
    <owl:Class rdf:about="http://example.org/test#C"/>
    
    <owl:ObjectProperty rdf:about="http://example.org/test#r"/>
    <owl:ObjectProperty rdf:about="http://example.org/test#s"/>
    <owl:ObjectProperty rdf:about="http://example.org/test#t">
        <owl:propertyChainAxiom rdf:parseType="Collection">
            <rdf:Description rdf:about="http://example.org/test#r"/>
            <rdf:Description rdf:about="http://example.org/test#s"/>
        </owl:propertyChainAxiom>
    </owl:ObjectProperty>
    
    <owl:NamedIndividual rdf:about="http://example.org/test#a">
        <test:r rdf:resource="http://example.org/test#b"/>
    </owl:NamedIndividual>
    
    <owl:NamedIndividual rdf:about="http://example.org/test#b">
        <test:s rdf:resource="http://example.org/test#c"/>
    </owl:NamedIndividual>
    
    <owl:NamedIndividual rdf:about="http://example.org/test#c">
        <rdf:type rdf:resource="http://example.org/test#C"/>
    </owl:NamedIndividual>
</rdf:RDF>
"""


class TestCrossShardPropertyChain(unittest.TestCase):
    """Verify that ∃ t.C is correctly resolved across shards with property chains.

    Ontology:  PropertyChain(r o s -> t), r(a, b), s(b, c), C(c)
    Query:     ∃ t.C
    Expected:  {a}

    With 3 shards the property assertions may land in different shards,
    preventing local inference of the derived t(a, c) assertion. This test
    documents the known limitation or verifies a fix if implemented.
    """

    _tmp_dir: str = ""

    @classmethod
    def setUpClass(cls):
        os.environ["PYTHONHASHSEED"] = "1"
        os.environ["RAY_DEDUP_LOGS"] = "0"

        cls._tmp_dir = os.path.join(REPO_ROOT, "debug_chain_test_unittest")
        os.makedirs(cls._tmp_dir, exist_ok=True)
        cls._owl_path = os.path.join(cls._tmp_dir, "chain_test.owl")
        with open(cls._owl_path, "w") as f:
            f.write(_CHAIN_OWL)

    def test_property_chain_cross_shard(self):
        """∃ t.C should return {a} when property chain r o s -> t is distributed."""
        try:
            import ray
        except ImportError:
            self.skipTest("ray is not installed — skipping DDP property chain test")

        from owlapy.class_expression import OWLClass, OWLObjectSomeValuesFrom
        from owlapy.owl_property import OWLObjectProperty
        from owlapy.iri import IRI
        from shard_ontology import shard_ontology
        from ddp_reasoning import ShardReasoner, ShardEnsembleReasoner

        num_shards = 3

        # Known ground truth from the inline ontology definition.
        # r(a, b), s(b, c), C(c), PropertyChain(r o s -> t) implies t(a, c).
        # Therefore, ∃ t.C should yield {a}.
        expected = {f"{_CHAIN_NS}a"}

        # Initialize Ray BEFORE any JVM operation (shard_ontology uses
        # JPype).  Starting a JVM before ray.init() can cause segfaults
        # when Ray spawns worker processes from a JVM-laden parent.
        if not ray.is_initialized():
            ray.init(
                num_cpus=os.cpu_count(),
                resources={f"shard_{i}": 1 for i in range(num_shards)},
            )

        shard_ontology(self._owl_path, num_shards, self._tmp_dir)
        C = OWLClass(IRI(_CHAIN_NS, "C"))
        t = OWLObjectProperty(IRI(_CHAIN_NS, "t"))
        exists_t_C = OWLObjectSomeValuesFrom(property=t, filler=C)

        stem = Path(self._owl_path).stem
        shards = [
            ShardReasoner.options(resources={f"shard_{i}": 1}).remote(
                f"Shard-{i}",
                os.path.join(self._tmp_dir, f"{stem}_shard_{i}.owl"),
                "Pellet",
                verbose=False,
            )
            for i in range(num_shards)
        ]
        dist = ShardEnsembleReasoner(shards, verbose=False)
        dist_exists = {i.str for i in dist.instances(exists_t_C)}

        # NOTE: This test may fail with the current implementation due to
        # the known limitation that property chains spanning multiple shards
        # cannot be locally inferred. If this assertion fails, it documents
        # the incompleteness issue. If it passes, congratulations! The
        # distributed reasoner has been enhanced to handle cross-shard chains.
        self.assertEqual(
            expected, dist_exists,
            f"∃ t.C mismatch — expected={expected}, Dist={dist_exists}. "
            f"Missing individuals: {expected - dist_exists}. "
            "This may indicate the known cross-shard property chain incompleteness."
        )

    @classmethod
    def tearDownClass(cls):
        import shutil
        if cls._tmp_dir and os.path.isdir(cls._tmp_dir):
            shutil.rmtree(cls._tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
