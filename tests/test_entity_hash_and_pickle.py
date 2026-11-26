"""IRIs, classes and named individuals cache their hash and survive pickling.

Unpickling an IRI used to restore its slots directly, leaving the namespace string un-interned,
and IRI.__eq__ compares namespaces by identity: the copy was unequal to the original. The cached
hashes must also be recomputed on unpickling, since str hashes differ between processes.
"""
import copy
import os
import pickle
import subprocess
import sys

import pytest

from owlapy.class_expression import OWLClass, OWLObjectIntersectionOf, OWLObjectSomeValuesFrom
from owlapy.iri import IRI
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_property import OWLObjectProperty

NS = "http://example.org/hash-test/ns#"

OBJECTS = [
    IRI(NS, "a"),
    IRI.create("file.owl", is_file_path=True),
    OWLClass(IRI(NS, "A")),
    OWLClass("http://www.w3.org/2002/07/owl#Thing"),
    OWLNamedIndividual(IRI(NS, "i")),
    OWLObjectSomeValuesFrom(OWLObjectProperty(NS + "r"),
                            OWLObjectIntersectionOf([OWLClass(NS + "A"), OWLClass(NS + "B")])),
]


@pytest.mark.parametrize("obj", OBJECTS, ids=lambda o: type(o).__name__)
@pytest.mark.parametrize("roundtrip", [lambda o: pickle.loads(pickle.dumps(o)), copy.copy, copy.deepcopy],
                         ids=["pickle", "copy", "deepcopy"])
def test_roundtrip_is_equal_with_same_hash(obj, roundtrip):
    clone = roundtrip(obj)
    assert clone == obj
    assert hash(clone) == hash(obj)
    assert clone in {obj}


def test_unpickled_iri_is_the_interned_instance():
    iri = IRI(NS, "interned")
    assert pickle.loads(pickle.dumps(iri)) is iri


def test_cached_hash_matches_named_object_formula():
    iri = IRI(NS, "x")
    assert hash(iri) == hash(("IRI", NS, "x"))
    assert hash(OWLClass(iri)) == hash(("OWLClass", iri))
    assert hash(OWLNamedIndividual(iri)) == hash(("OWLNamedIndividual", iri))


def test_unpickled_in_process_with_other_hash_seed():
    payload = pickle.dumps(OBJECTS[:5])
    code = (
        "import pickle, sys\n"
        "from owlapy.class_expression import OWLClass\n"
        "from owlapy.iri import IRI\n"
        "from owlapy.owl_individual import OWLNamedIndividual\n"
        f"NS = {NS!r}\n"
        "objs = pickle.loads(sys.stdin.buffer.read())\n"
        "fresh = [IRI(NS, 'a'), IRI.create('file.owl', is_file_path=True), OWLClass(IRI(NS, 'A')),\n"
        "         OWLClass('http://www.w3.org/2002/07/owl#Thing'), OWLNamedIndividual(IRI(NS, 'i'))]\n"
        "assert objs == fresh, (objs, fresh)\n"
        "assert all(o in set(fresh) for o in objs)\n"
    )
    seeds = {"0", "12345"} - {os.environ.get("PYTHONHASHSEED")}
    for seed in seeds:
        env = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONPATH": os.pathsep.join(sys.path)}
        subprocess.run([sys.executable, "-c", code], input=payload, env=env, check=True, timeout=120)
