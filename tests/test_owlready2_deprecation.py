"""The owlready2-backed classes warn that they will be removed in owlapy 2.0 (#310).

Each warning is attributed to the caller (``stacklevel=2``): user code that uses a deprecated class gets
the warning, while owlapy's own internal uses (e.g. ``Ontology.add_axiom`` building a ``ToOwlready2`` per
call) are attributed to owlapy modules, which Python hides by default for ``DeprecationWarning``.
"""
import os
import warnings

import pytest

owlready2 = pytest.importorskip("owlready2")

from owlapy.class_expression import OWLClass  # noqa: E402
from owlapy.iri import IRI  # noqa: E402
from owlapy.owl_axiom import OWLDeclarationAxiom  # noqa: E402
from owlapy.owl_ontology import FromOwlready2, Ontology, ToOwlready2  # noqa: E402
from owlapy.owl_reasoner import StructuralReasoner  # noqa: E402

NS = "http://example.org/deprecation#"


def _deprecations(fn):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fn()
    return [w for w in caught if issubclass(w.category, DeprecationWarning)]


@pytest.mark.parametrize("make, name, replacement", [
    (lambda: Ontology(NS, load=False), "Ontology", "RDFLibOntology"),
    (lambda: StructuralReasoner(Ontology(NS, load=False)), "StructuralReasoner", "RDFLibReasoner"),
    (lambda: ToOwlready2(owlready2.World()), "ToOwlready2", None),
    (FromOwlready2, "FromOwlready2", None),
])
def test_owlready2_classes_warn_about_removal_in_2_0(make, name, replacement):
    messages = [str(w.message) for w in _deprecations(make) if str(w.message).startswith(name)]
    assert messages, f"{name} emitted no DeprecationWarning"
    assert "owlapy 2.0" in messages[0] and "#310" in messages[0]
    if replacement:
        assert replacement in messages[0]


def test_warning_points_at_the_callers_code():
    found = [w for w in _deprecations(lambda: Ontology(NS, load=False)) if str(w.message).startswith("Ontology")]
    assert os.path.abspath(found[0].filename) == os.path.abspath(__file__)


def test_internal_uses_are_attributed_to_owlapy_not_the_caller():
    onto = Ontology(NS, load=False)
    found = _deprecations(lambda: onto.add_axiom(OWLDeclarationAxiom(OWLClass(IRI.create(NS, "A")))))
    assert found, "expected add_axiom to construct a ToOwlready2 internally"
    assert all(os.path.abspath(w.filename) != os.path.abspath(__file__) for w in found)
    assert all(f"{os.sep}owlapy{os.sep}" in w.filename for w in found)
