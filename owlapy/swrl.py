from abc import ABCMeta, abstractmethod
from typing import Tuple, List, Optional, Union
import re

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty


# TODO: add support for built-in Atoms

class Variable(metaclass=ABCMeta):
    """Represents a variable in SWRL syntax"""
    iri: IRI

    def __init__(self, iri:Union[IRI, str]):
        if isinstance(iri, str):
            self.iri = IRI.create(iri)
        else:
            self.iri = iri

    def is_i_variable(self):
        if isinstance(self, IVariable):
            return True
        return False

    def is_d_variable(self):
        if isinstance(self, DVariable):
            return True
        return False

    def __eq__(self, other):
        if type(other) is type(self):
            return self.iri == other.iri

    def __str__(self):
        return "?" + self.iri.reminder

    def __hash__(self):
        return hash(self.iri)




class DVariable(Variable):
    """Represents a data variable in SWRL syntax"""
    def __repr__(self):
        return f"DVariable({self.iri})"


class IVariable(Variable):
    """Represents a individual variable in SWRL syntax"""

    def __repr__(self):
        return f"IVariable({self.iri})"


class Atom(metaclass=ABCMeta):
    """Represents an Atom in SWRL syntax"""
    arguments: List[Variable]

    def __eq__(self, other):
        if type(other) is type(self):
            return self.arguments == other.arguments

    @abstractmethod
    def is_class_assertion(self):
        pass

    @abstractmethod
    def is_property_assertion(self):
        pass

    @abstractmethod
    def is_same_as(self):
        pass

    @abstractmethod
    def is_different_from(self):
        pass


def r(argument):
    """Returns the right string format of a given argument depending on its type"""
    if isinstance(argument, Variable):
        return str(argument)
    return argument.iri.reminder

def t(argument):
    """Returns the representation for a given argument"""
    return f"{type(argument).__name__}({argument.iri.str})"

class ClassAtom(Atom):
    """Returns the right string format of a given argument depending on its type"""
    argument1: Union[IVariable, OWLNamedIndividual]
    cls: OWLClass

    def __init__(self, cls: OWLClass, argument1: IVariable):
        self.cls = cls
        self.argument1 = argument1

    def is_class_assertion(self):
        return True

    def is_property_assertion(self):
        return False

    def is_same_as(self):
        return False

    def is_different_from(self):
        return False

    def __str__(self):
        return f"{r(self.cls)}({r(self.argument1)})"

    def __repr__(self):
        return f"ClassAtom({t(self.cls)}, {t(self.argument1)})"

    def __hash__(self):
        return hash(f"ClassAtom({str(self.cls)}, {str(self.argument1)})")


class DataRangeAtom(Atom):
    argument1: Union[DVariable, OWLLiteral]
    datatype: OWLDatatype

    def __init__(self, datatype: OWLDatatype, argument1: Union[DVariable, OWLLiteral]):
        self.datatype = datatype
        self.argument1 = argument1

    def is_class_assertion(self):
        return True

    def is_property_assertion(self):
        return False

    def is_same_as(self):
        return False

    def is_different_from(self):
        return False

    def __str__(self):
        return f"{r(self.datatype)}({r(self.argument1)})"

    def __repr__(self):
        return f"ClassAtom(t{self.datatype} {t(self.argument1)})"

    def __hash__(self):
        return hash(f"ClassAtom({str(self.datatype)}, {str(self.argument1)})")


class PropertyAtom(Atom, metaclass=ABCMeta):

    def __init__(self, prop: Union[OWLObjectProperty, OWLDataProperty], argument1, argument2):
        self.argument1 = argument1
        self.argument2 = argument2
        self.prop = prop

    def is_class_assertion(self):
        return False

    def is_property_assertion(self):
        return True

    def is_same_as(self):
        return False

    def is_different_from(self):
        return False

    def __str__(self):
        return f"{r(self.prop)}({r(self.argument1)}, {r(self.argument2)})"

    def __repr__(self):
        return f"PropertyAtom({t(self.prop)}, {t(self.argument1)}, {t(self.argument2)})"

    def __hash__(self):
        return hash(f"PropertyAtom({str(self.prop)}, {str(self.argument1)}, {str(self.argument2)})")


class ObjectPropertyAtom(PropertyAtom):
    argument1: Union[OWLNamedIndividual, IVariable]
    argument2: Union[OWLNamedIndividual, IVariable]
    prop: OWLObjectProperty

    def __init__(self, prop: OWLObjectProperty, argument1: Union[OWLNamedIndividual, IVariable],
                 argument2: Union[OWLNamedIndividual, IVariable]):
        super().__init__(prop, argument1, argument2)


class DataPropertyAtom(PropertyAtom):
    argument1: Union[OWLNamedIndividual, IVariable]
    argument2: Union[OWLLiteral, DVariable]
    prop: OWLDataProperty

    def __init__(self, prop: OWLDataProperty, argument1: Union[OWLNamedIndividual,IVariable],
                 argument2: Union[OWLLiteral, DVariable]):
        super().__init__(prop, argument1, argument2)

class SameAsAtom(Atom):
    argument1: Union[IVariable, OWLNamedIndividual]
    argument2: Union[IVariable, OWLNamedIndividual]

    def __init__(self, argument1: Union[IVariable, OWLNamedIndividual], argument2: Union[IVariable, OWLNamedIndividual]):
        self.argument1 = argument1
        self.argument2 = argument2

    def is_class_assertion(self):
        return False

    def is_property_assertion(self):
        return False

    def is_same_as(self):
        return True

    def is_different_from(self):
        return False

    def __str__(self):
        return f"sameAs({r(self.argument1)}, {r(self.argument2)})"

    def __repr__(self):
        return f"SameAs({t(self.argument1)}, {t(self.argument2)})"

    def __hash__(self):
        return hash(f"SameAs({str(self.argument1)}, {str(self.argument2)})")


class DifferentFromAtom(Atom):
    argument1: Union[IVariable, OWLNamedIndividual]
    argument2: Union[IVariable, OWLNamedIndividual]

    def __init__(self, argument1: Union[IVariable, OWLNamedIndividual], argument2: Union[IVariable, OWLNamedIndividual]):
        self.argument1 = argument1
        self.argument2 = argument2

    def is_class_assertion(self):
        return False

    def is_property_assertion(self):
        return False

    def is_same_as(self):
        return False

    def is_different_from(self):
        return True

    def __str__(self):
        return f"differentFrom({r(self.argument1)}, {r(self.argument2)})"

    def __repr__(self):
        return f"DifferentFrom({t(self.argument1)}, {t(self.argument2)})"

    def __hash__(self):
        return hash(f"DifferentFrom({str(self.argument1)}, {str(self.argument2)})")


class Rule:

    body_atoms: Union[Atom, List[Atom]]
    head_atoms: Union[Atom, List[Atom]]

    def __init__(self, body_atoms: Union[Atom, List[Atom]], head_atoms: Union[Atom, List[Atom]]):
        self.body = body_atoms
        self.head = head_atoms

    @staticmethod
    def set_as_rule(rule: str, namespace: str):
        body_str = rule.split("->")[0]
        head_str = rule.split("->")[1]
        body_atoms_str = body_str.split("^")
        head_atoms_str = head_str.split("^")

        body_atoms = [Rule.parse_swrl_atom(atom_str, namespace) for atom_str in body_atoms_str]
        head_atoms = [Rule.parse_swrl_atom(atom_str, namespace) for atom_str in head_atoms_str]

        return Rule(body_atoms, head_atoms)


    @staticmethod
    def parse_swrl_atom(atom_str: str, namespace: str) -> Atom:
        """
        Parses a SWRL atom like 'parent(?x, ?y)' or 'person(?x)'.

        Returns:
            An Atom
        """
        # Regular expression to extract predicate and variable list from a string atom
        pattern = r'^\s*([a-zA-Z_][\w\-]*)\s*\(\s*([^\)]*)\s*\)\s*$'
        match = re.match(pattern, atom_str)

        if not match:
            raise ValueError(f"Invalid SWRL atom: {atom_str}")

        predicate = match.group(1)
        raw_args = match.group(2)

        args = [arg.strip() for arg in raw_args.split(',') if arg.strip()]


        # TODO: Idea; a user can also pass the ontology and we can check the type of the predicate in the ontology
        #             so that we can map it to the correct atom type.

        # for now default to ClassAtom if only 1 argument is found (can be DataRangeAtom as well, should find a way to decide)
        if len(args) == 1:
            if "?" in args[0]:
                argument = IVariable(namespace + args[0][1:])
            else:
                argument = OWLNamedIndividual(namespace + args[0])
            return ClassAtom(OWLClass(namespace + predicate), argument)
        # should check for built-ins
        # for now defaulting to ObjectPropertyAtom
        elif len(args) == 2 and predicate not in ["sameAs", "differentFrom"]:
            for i in range(0,2):
                if "?" in args[i]:
                    args[i] = IVariable(namespace + args[i][1:])
                else:
                    args[i] = OWLNamedIndividual(namespace + args[i])
            return ObjectPropertyAtom(OWLObjectProperty(namespace + predicate) ,args[0], args[1])
        elif len(args) == 2 and predicate == "sameAs":
            for i in range(0,2):
                if "?" in args[i]:
                    args[i] = IVariable(namespace + args[i][1:])
                else:
                    args[i] = OWLNamedIndividual(namespace + args[i])
            return SameAsAtom(args[0], args[1])
        elif len(args) == 2 and predicate == "differentFrom":
            for i in range(0,2):
                if "?" in args[i]:
                    args[i] = IVariable(namespace + args[i][1:])
                else:
                    args[i] = OWLNamedIndividual(namespace + args[i])
            return DifferentFromAtom(args[0], args[1])
        else:
            raise ValueError(f"Invalid SWRL atom: {atom_str}")

    def __str__(self):
        body = self.body
        head = self.head
        if isinstance(self.body, List):
            body = " ^ ".join(map(str, self.body))
        if isinstance(self.head, List):
            head = " ^ ".join(map(str, self.head))
        return f"{body} -> {head}"


