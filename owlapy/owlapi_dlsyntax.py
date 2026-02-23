"""OWLAPI-based DL Syntax parser and renderer.

This module provides DL (Description Logic) syntax parsing and rendering
using the OWLAPI Java library via JPype. It leverages OWLAPI's
``DLSyntaxObjectRenderer`` and ``DLSyntaxParser`` to handle both OWL class
expressions and OWL axioms in DL notation, and uses :class:`OWLAPIMapper`
to convert between owlapi Java objects and owlapy Python objects.

Usage example::

    from owlapy.owlapi_dlsyntax import OWLAPIDLSyntaxParser, OWLAPIDLSyntaxRenderer

    renderer = OWLAPIDLSyntaxRenderer()
    parser = OWLAPIDLSyntaxParser(namespace="http://example.org/")

    # Render an owlapy object to DL syntax string
    dl_string = renderer.render(some_owlapy_class_expression)
    dl_axiom_string = renderer.render(some_owlapy_axiom)

    # Parse a DL syntax string to an owlapy object
    ce = parser.parse_expression("∃ r.A ⊓ B")
    axiom = parser.parse_axiom("A ⊑ ∃ r.B")
"""
from typing import Optional, List

import jpype
import jpype.imports

from owlapy.class_expression import OWLClassExpression
from owlapy.owl_axiom import OWLAxiom
from owlapy.owl_object import OWLObject
from owlapy.owlapi_mapper import OWLAPIMapper
from owlapy.static_funcs import startJVM

if not jpype.isJVMStarted():
    startJVM()

from org.semanticweb.owlapi.dlsyntax.renderer import \
    DLSyntaxObjectRenderer as _OWLAPI_DLSyntaxObjectRenderer
from org.semanticweb.owlapi.dlsyntax.parser import \
    DLSyntaxParser as _OWLAPI_DLSyntaxParser
from org.semanticweb.owlapi.apibinding import OWLManager as _OWLManager

# Shared data factory for creating OWLAPI objects
_manager = _OWLManager.createOWLOntologyManager()
_data_factory = _manager.getOWLDataFactory()


class OWLAPIDLSyntaxRenderer:
    """DL Syntax renderer backed by OWLAPI's ``DLSyntaxObjectRenderer``.

    Renders owlapy OWL objects (class expressions and axioms) into
    Description Logic syntax strings by first mapping them to OWLAPI Java
    objects, then delegating to the OWLAPI renderer.

    Examples:
        >>> from owlapy.owlapi_dlsyntax import OWLAPIDLSyntaxRenderer
        >>> from owlapy.class_expression import OWLClass, OWLObjectSomeValuesFrom
        >>> from owlapy.owl_property import OWLObjectProperty
        >>> from owlapy.iri import IRI
        >>> renderer = OWLAPIDLSyntaxRenderer()
        >>> A = OWLClass(IRI.create("http://example.org/", "A"))
        >>> r = OWLObjectProperty(IRI.create("http://example.org/", "r"))
        >>> expr = OWLObjectSomeValuesFrom(r, A)
        >>> renderer.render(expr)
        '∃ r.A'
    """

    def __init__(self):
        self._mapper = OWLAPIMapper()
        self._renderer = _OWLAPI_DLSyntaxObjectRenderer()

    def render(self, obj: OWLObject) -> str:
        """Render an owlapy OWL object to a DL syntax string.

        Args:
            obj: An owlapy OWL object — can be an ``OWLClassExpression``,
                ``OWLAxiom``, or any other ``OWLObject`` supported by the
                OWLAPI DL renderer.

        Returns:
            The DL syntax string representation.

        Raises:
            NotImplementedError: If the object type is not supported by
                the mapper.
        """
        owlapi_obj = self._mapper.map_(obj)
        return str(self._renderer.render(owlapi_obj))


class OWLAPIDLSyntaxParser:
    """DL Syntax parser backed by OWLAPI's ``DLSyntaxParser``.

    Parses DL syntax strings into owlapy OWL objects (class expressions
    and axioms) by delegating to the OWLAPI Java parser, then mapping
    the result back using :class:`OWLAPIMapper`.

    Args:
        namespace: Default namespace for resolving unqualified names.
            For example ``"http://example.org/"`` will resolve ``A`` to
            ``<http://example.org/#A>``. Note that OWLAPI's DL parser
            appends ``#`` between the namespace and local name.

    Examples:
        >>> from owlapy.owlapi_dlsyntax import OWLAPIDLSyntaxParser
        >>> parser = OWLAPIDLSyntaxParser(namespace="http://example.org/")
        >>> ce = parser.parse_expression("∃ r.A ⊓ B")
        >>> axiom = parser.parse_axiom("A ⊑ ∃ r.B")
    """

    def __init__(self, namespace: Optional[str] = None):
        self._mapper = OWLAPIMapper()
        self._namespace = namespace

    @property
    def namespace(self) -> Optional[str]:
        """The default namespace used for resolving unqualified names."""
        return self._namespace

    @namespace.setter
    def namespace(self, value: Optional[str]):
        self._namespace = value

    def _create_parser(self, expression_str: str) -> '_OWLAPI_DLSyntaxParser':
        """Create a fresh OWLAPI DLSyntaxParser for the given string.

        The OWLAPI ``DLSyntaxParser`` is stateful (token-stream based),
        so a new instance is created for each parse operation.
        """
        parser = _OWLAPI_DLSyntaxParser(jpype.JString(expression_str))
        parser.setOWLDataFactory(_data_factory)
        if self._namespace is not None:
            parser.setDefaultNamespace(self._namespace)
        return parser

    def parse_expression(self, expression_str: str) -> OWLClassExpression:
        """Parse a DL syntax string into an owlapy ``OWLClassExpression``.

        Args:
            expression_str: DL syntax string representing a class expression.
                Examples: ``"A"``, ``"∃ r.A ⊓ B"``, ``"¬A ⊔ (∀ r.B)"``.

        Returns:
            The corresponding owlapy ``OWLClassExpression``.

        Raises:
            Exception: If the string cannot be parsed as a valid DL class
                expression (wraps OWLAPI's ``ParseException``).
        """
        parser = self._create_parser(expression_str)
        owlapi_ce = parser.parseDescription()
        return self._mapper.map_(owlapi_ce)

    def parse_axiom(self, axiom_str: str) -> OWLAxiom:
        """Parse a DL syntax string into an owlapy ``OWLAxiom``.

        Args:
            axiom_str: DL syntax string representing an axiom.
                Examples: ``"A ⊑ ∃ r.B"`` (subclass), ``"A ≡ B ⊓ C"``
                (equivalent classes).

        Returns:
            The corresponding owlapy ``OWLAxiom``.

        Raises:
            Exception: If the string cannot be parsed as a valid DL axiom
                (wraps OWLAPI's ``ParseException``).
        """
        parser = self._create_parser(axiom_str)
        owlapi_axiom = parser.parseAxiom()
        return self._mapper.map_(owlapi_axiom)

    def parse_axioms(self, axioms_str: str) -> List[OWLAxiom]:
        """Parse a DL syntax string containing multiple axioms.

        The OWLAPI ``DLSyntaxParser.parseAxioms()`` expects axioms to be
        newline-separated.

        Args:
            axioms_str: DL syntax string with multiple axioms separated
                by newlines.

        Returns:
            A list of owlapy ``OWLAxiom`` objects.

        Raises:
            Exception: If any axiom cannot be parsed (wraps OWLAPI's
                ``ParseException``).
        """
        parser = self._create_parser(axioms_str)
        owlapi_axiom_set = parser.parseAxioms()
        return [self._mapper.map_(ax) for ax in owlapi_axiom_set]


