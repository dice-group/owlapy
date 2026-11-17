"""Optional owlready2 dependency shim.

owlready2 backs the legacy, owlready2-specific parts of owlapy (the `Ontology` class in
`owl_ontology.py`, `StructuralReasoner` in `owl_reasoner.py`, and a few helpers in
`util_owl_static_funcs.py`). owlapy is migrating away from it in favor of the pure-Python
`RDFLibOntology`/`RDFLibReasoner` (see issue #205), so it's no longer a hard install-time
dependency: `pip install owlapy` works without it, and only code paths that actually construct or
call owlready2 functionality raise, at the point of use, with an actionable install hint.
"""
import os
from typing import Any


class _MissingOwlready2Meta(type):
    """Metaclass for placeholder classes standing in for anything under the (possibly
    uninstalled) ``owlready2`` package.

    Every placeholder is itself a class (a ``type`` instance), so it works anywhere a *class* is
    syntactically required -- as a type annotation (including as the first parameter of a
    ``functools.singledispatch``-registered function, which validates that the resolved
    annotation is an actual class, not just any object -- a plain sentinel *instance* fails that
    check), or as the second argument to ``isinstance``/``issubclass``. Attribute access on a
    placeholder (e.g. chaining ``owlready2.namespace.World``) returns another placeholder, so
    arbitrarily deep attribute chains resolve without error too. Only *calling* one -- i.e.
    actually trying to construct/invoke owlready2 functionality -- raises.
    """

    def __getattr__(cls, item: str) -> "_MissingOwlready2Meta":
        return _placeholder(item)

    def __call__(cls, *args: Any, **kwargs: Any):
        raise ImportError(
            "owlready2 is required for this operation but is not installed. owlready2 is an "
            "optional dependency -- owlapy is migrating away from it in favor of the "
            "owlready2-free RDFLibOntology/RDFLibReasoner (see issue #205). Install it with "
            "`pip install owlready2>=0.40` or `pip install owlapy[owlready2]` to use "
            "Ontology/StructuralReasoner/util_owl_static_funcs' owlready2-backed helpers."
        )


def _placeholder(name: str) -> _MissingOwlready2Meta:
    return _MissingOwlready2Meta(name, (), {})


_MISSING_OWLREADY2 = _placeholder("owlready2")


def import_owlready2():
    """Import ``owlready2`` if installed, else return a placeholder that behaves like the real
    module for every *syntactic* purpose (attribute access, type annotations, isinstance checks)
    but raises a clear, actionable ``ImportError`` the moment anything actually tries to
    construct/call into it."""
    try:
        import owlready2
        return owlready2
    except ImportError:
        return _MISSING_OWLREADY2


class _UnnamedReader:
    """Read-only file proxy that hides the wrapped file's ``name`` attribute (see `load_ontology`)."""

    def __init__(self, f):
        self._f = f

    def __getattr__(self, item: str):
        if item == "name":
            raise AttributeError(item)
        return getattr(self._f, item)

    def __iter__(self):
        return iter(self._f)


def load_ontology(onto, **kwargs):
    """Load an owlready2 ontology like ``onto.load(**kwargs)``, but always parse in this process.

    owlready2 (0.4x/0.50) parses files of 8 MB or more in a ``multiprocessing`` child created with
    ``fork`` and waits on a queue without a timeout for the result. Forking a process that already
    runs other threads (owlapy starts the JVM on import of ``owlapy.owl_reasoner``) can leave the
    child stuck on a lock held by a thread that does not exist in the child, so the parent hangs
    forever. owlready2 decides on the forked parse from the file object's ``name``, so local files
    are handed over as an unnamed file object, which makes owlready2 take its in-process path.

    Anything that is not a plain local file on first load (predefined ontologies, http(s) IRIs, an
    ontology already cached in a persistent ``World``, ``reload``/``fileobj`` arguments) is passed
    to ``onto.load`` unchanged.
    """
    if kwargs or onto.loaded:
        return onto.load(**kwargs)
    from owlready2 import namespace as owlready2_namespace

    base_iri = onto._orig_base_iri
    if (owlready2_namespace.PREDEFINED_ONTOLOGIES.get(base_iri)
            or owlready2_namespace.PREDEFINED_ONTOLOGIES.get(base_iri[:-1])
            or onto.graph.get_last_update_time() != 0.0):
        return onto.load()
    try:
        path = owlready2_namespace._get_onto_file(base_iri, onto.name, "r")
    except FileNotFoundError:
        return onto.load()
    if path.startswith(("http:", "https:")) or not os.path.isfile(path):
        return onto.load()
    # onto.load(fileobj=...) closes the file object itself
    return onto.load(fileobj=_UnnamedReader(open(path, "rb")))
