"""Shared pytest configuration.

`requires_owlready2` marks tests that exercise the legacy owlready2-backed classes (`Ontology`,
`StructuralReasoner`, `ToOwlready2`, `FromOwlready2`). They are skipped when owlready2 is not
installed; CI runs the suite once that way to prove nothing else needs owlready2 (#310, 1.5).
Deliberately, only *marked* tests are skipped: an unmarked test that hits owlapy's
"owlready2 is required" ImportError fails, because that means non-legacy code needs owlready2.
"""

import pytest

try:
    import owlready2  # noqa: F401
    OWLREADY2_INSTALLED = True
except ImportError:
    OWLREADY2_INSTALLED = False


def pytest_collection_modifyitems(config, items):
    if OWLREADY2_INSTALLED:
        return
    skip = pytest.mark.skip(reason="owlready2 is not installed (legacy owlready2-backed classes, see #310)")
    for item in items:
        if item.get_closest_marker("requires_owlready2"):
            item.add_marker(skip)
