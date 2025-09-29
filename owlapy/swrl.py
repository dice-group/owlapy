from abc import ABCMeta, abstractmethod
from typing import List, Union
import re

from owlapy.class_expression import OWLClass
from owlapy.iri import IRI
from owlapy.owl_datatype import OWLDatatype
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_property import OWLObjectProperty, OWLDataProperty


BUILTINS = ["add", "subtract", "multiply", "divide", "mod", "pow", "abs", "round", "floor", "ceiling",
            "equal", "notEqual", "greaterThan", "lessThan", "greaterThanOrEqual", "lessThanOrEqual",
            "stringConcat", "substring", "contains", "startsWith", "endsWith", "stringLength",
            "matches", "normalizeSpace", "lowerCase", "upperCase", "dateTime", "addDayTimeDuration",
            "subtractDateTimes", "year", "month", "day", "hour", "isInteger", "isString", "isDateTime",
            "isBoolean", "isNumeric"]

DATATYPES = ["decimal", "integer", "nonNegativeInteger", "nonPositiveInteger", "positiveInteger", "negativeInteger",
             "long", "double", "float", "boolean", "string", "date", "dateTime", "dateTimeStamp", "duration",
             "time", "gYearMonth", "gMonthDay", "gYear", "gMonth", "gDay"]

SWRL = "http://www.w3.org/2003/11/swrl#"
SWRLB = "http://www.w3.org/2003/11/swrlb#"

class Variable(metaclass=ABCMeta):
    """Represents a variable in SWRL syntax"""
    iri: IRI # should have the correct namespace, e.g: http://www.w3.org/2003/11/swrl#x

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
        return "?" + self.iri.remainder

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

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__repr__() == other.__repr__()

    @staticmethod
    def from_string(atom_str: str, namespace: str, dp_predicates: List[str] = None):
        """
        Parses a SWRL atom like 'parent(?x, ?y)' or 'person(?x)'.

        Returns:
            An Atom object.
        """
        # Regular expression to extract predicate and variable list from a string atom
        pattern = r'^\s*([a-zA-Z_][\w\-]*)\s*\(\s*([^\)]*)\s*\)\s*$'
        match = re.match(pattern, atom_str)

        if not match:
            raise ValueError(f"Invalid SWRL atom: {atom_str}")

        predicate = match.group(1)
        raw_args = match.group(2)

        args = [arg.strip() for arg in raw_args.split(',') if arg.strip()]

        if len(args) == 1:
            if predicate in DATATYPES:
                if "?" in args[0]:
                    argument = DVariable(SWRL + args[0][1:])
                else:
                    argument = OWLLiteral(args[0])
                return DataRangeAtom(OWLDatatype("http://www.w3.org/2001/XMLSchema#" + predicate), argument)
            else:
                if "?" in args[0]:
                    argument = IVariable(SWRL + args[0][1:])
                else:
                    argument = OWLNamedIndividual(namespace + args[0])
                return ClassAtom(OWLClass(namespace + predicate), argument)

        elif len(args) == 2 and predicate not in BUILTINS + ["sameAs", "differentFrom"]:
            if dp_predicates is not None and predicate in dp_predicates:
                if "?" in args[0]:
                    args[0] = IVariable(SWRL + args[0][1:])
                else:
                    args[0] = OWLNamedIndividual(args[0])
                if "?" in args[1]:
                    args[1] = DVariable(SWRL + args[1][1:])
                else:
                    args[1] = OWLLiteral(args[1])
                return DataPropertyAtom(OWLDataProperty(namespace + predicate), args[0], args[1])
            else:
                for i in range(0, 2):
                    if "?" in args[i]:
                        args[i] = IVariable(SWRL + args[i][1:])
                    else:
                        args[i] = OWLNamedIndividual(namespace + args[i])
                return ObjectPropertyAtom(OWLObjectProperty(namespace + predicate), args[0], args[1])
        elif len(args) == 2 and predicate == "sameAs":
            for i in range(0, 2):
                if "?" in args[i]:
                    args[i] = IVariable(SWRL + args[i][1:])
                else:
                    args[i] = OWLNamedIndividual(namespace + args[i])
            return SameAsAtom(args[0], args[1])
        elif len(args) == 2 and predicate == "differentFrom":
            for i in range(0, 2):
                if "?" in args[i]:
                    args[i] = IVariable(namespace + args[i][1:])
                else:
                    args[i] = OWLNamedIndividual(namespace + args[i])
            return DifferentFromAtom(args[0], args[1])
        elif predicate in BUILTINS:
            for i in range(0, len(args)):
                if "?" in args[i]:
                    args[i] = DVariable(SWRL + args[i][1:])
                else:
                    args[i] = OWLNamedIndividual(namespace + args[i])
                return BuiltInAtom(IRI.create(SWRLB + predicate), args)
        else:
            raise ValueError(f"Invalid SWRL atom: {atom_str}")

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

    @abstractmethod
    def is_builtin(self):
        pass

def r(argument):
    """Returns the right string format of a given argument depending on its type"""
    if isinstance(argument, Variable):
        return str(argument)
    return argument.iri.remainder

def t(argument):
    """Returns the representation for a given argument"""
    return f"{type(argument).__name__}({argument.iri.str})"

class ClassAtom(Atom):
    """Represents a class atom in SWRL syntax"""
    argument1: Union[IVariable, OWLNamedIndividual]
    cls: OWLClass

    def __init__(self, cls: OWLClass, argument1: Union[IVariable, OWLNamedIndividual]):
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

    def is_builtin(self):
        return False

    def __str__(self):
        return f"{r(self.cls)}({r(self.argument1)})"

    def __repr__(self):
        return f"ClassAtom({t(self.cls)}, {t(self.argument1)})"

    def __hash__(self):
        return hash(f"ClassAtom({str(self.cls)}, {str(self.argument1)})")


class DataRangeAtom(Atom):
    """Represents a data range atom in SWRL syntax"""
    argument1: DVariable
    datatype: OWLDatatype

    def __init__(self, datatype: OWLDatatype, argument1: DVariable):
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

    def is_builtin(self):
        return False

    def __str__(self):
        return f"{r(self.datatype)}({r(self.argument1)})"

    def __repr__(self):
        return f"DataRangeAtom({t(self.datatype)} {t(self.argument1)})"

    def __hash__(self):
        return hash(f"DataRangeAtom({str(self.datatype)}, {str(self.argument1)})")


class PropertyAtom(Atom, metaclass=ABCMeta):
    """Represents a property atom in SWRL syntax"""
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

    def is_builtin(self):
        return False

    def __str__(self):
        return f"{r(self.prop)}({r(self.argument1)}, {r(self.argument2)})"


class ObjectPropertyAtom(PropertyAtom):
    """Represents an object property atom in SWRL syntax"""
    argument1: Union[OWLNamedIndividual, IVariable]
    argument2: Union[OWLNamedIndividual, IVariable]
    prop: OWLObjectProperty

    def __init__(self, prop: OWLObjectProperty, argument1: Union[OWLNamedIndividual, IVariable],
                 argument2: Union[OWLNamedIndividual, IVariable]):
        super().__init__(prop, argument1, argument2)

    def __repr__(self):
        return f"ObjectPropertyAtom({t(self.prop)}, {t(self.argument1)}, {t(self.argument2)})"

    def __hash__(self):
        return hash(f"ObjectPropertyAtom({str(self.prop)}, {str(self.argument1)}, {str(self.argument2)})")


class DataPropertyAtom(PropertyAtom):
    """Represents a data property atom in SWRL syntax"""
    argument1: Union[OWLNamedIndividual, IVariable]
    argument2: Union[OWLLiteral, DVariable]
    prop: OWLDataProperty

    def __init__(self, prop: OWLDataProperty, argument1: Union[OWLNamedIndividual, IVariable],
                 argument2: Union[OWLLiteral, DVariable]):
        super().__init__(prop, argument1, argument2)

    def __repr__(self):
        return f"DataPropertyAtom({t(self.prop)}, {t(self.argument1)}, {t(self.argument2)})"

    def __hash__(self):
        return hash(f"DataPropertyAtom({str(self.prop)}, {str(self.argument1)}, {str(self.argument2)})")

class SameAsAtom(Atom):
    """Represents a 'same-as' atom in SWRL syntax"""
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

    def is_builtin(self):
        return False

    def __str__(self):
        return f"sameAs({r(self.argument1)}, {r(self.argument2)})"

    def __repr__(self):
        return f"SameAs({t(self.argument1)}, {t(self.argument2)})"

    def __hash__(self):
        return hash(f"SameAs({str(self.argument1)}, {str(self.argument2)})")


class DifferentFromAtom(Atom):
    """Represents a 'different-from' atom in SWRL syntax"""
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

    def is_builtin(self):
        return False

    def __str__(self):
        return f"differentFrom({r(self.argument1)}, {r(self.argument2)})"

    def __repr__(self):
        return f"DifferentFrom({t(self.argument1)}, {t(self.argument2)})"

    def __hash__(self):
        return hash(f"DifferentFrom({str(self.argument1)}, {str(self.argument2)})")


class BuiltInAtom(Atom):
    """Represents a built-in atom in SWRL syntax"""
    predicate: IRI # should have the correct prefix, e.g: http://www.w3.org/2003/11/swrlb#divide
    arguments: List[Union[DVariable, OWLLiteral]]

    def __init__(self, predicate: IRI, arguments: List[Union[DVariable, OWLLiteral]]):
        self.predicate = predicate
        self.arguments = arguments


    def is_class_assertion(self):
        return False

    def is_property_assertion(self):
        return False

    def is_same_as(self):
        return False

    def is_different_from(self):
        return False

    def is_builtin(self):
        return True

    def __str__(self):
        args_to_print = ""
        for arg in self.arguments:
            if isinstance(arg, OWLLiteral):
                args_to_print += str(arg._v) + ", "
            else:
                args_to_print += str(arg) + ", "
        return f"{str(self.predicate.remainder)}({args_to_print[:-2]})"

    def __repr__(self):
        args_list ='['
        for arg in self.arguments:
            args_list = arg.__repr__()
        args_list += ']'
        return f'BuiltInAtom(IRI.create({self.predicate.str}), {args_list})'


class Rule:
    """Represents a rule in SWRL syntax"""
    body_atoms: Union[Atom, List[Atom]]
    head_atoms: Union[Atom, List[Atom]]

    def __init__(self, body_atoms: Union[Atom, List[Atom]], head_atoms: Union[Atom, List[Atom]]):
        self.body = body_atoms
        self.head = head_atoms

    @staticmethod
    def from_string(rule: str, namespace: str, dp_predicates: List[str] = None):
        """
        Parses a SWRL rule given as a string.
        Use '^' for composition of atoms and '->' for consequent implication.
        E.g. of a valid rule: 'parent(?x,?y) ^ brother(?y,?z) -> uncle(?x,?z)'

        Args:
            rule: The SWRL rule in string format that is to be parsed
            namespace: The namespace of the ontology
            dp_predicates: (optional) List of data property predicates that will help in the correct mapping of
                        property type (by default property atoms are considered as object property atoms except when
                        specifying data property predicates in this argument)

        Returns:
            A SWRL Rule object.
        """
        body_str = rule.split("->")[0]
        head_str = rule.split("->")[1]
        body_atoms_str = body_str.split("^")
        head_atoms_str = head_str.split("^")

        body_atoms = [Atom.from_string(atom_str, namespace, dp_predicates) for atom_str in body_atoms_str]
        head_atoms = [Atom.from_string(atom_str, namespace, dp_predicates) for atom_str in head_atoms_str]

        return Rule(body_atoms, head_atoms)

    def __str__(self):
        body = self.body
        head = self.head
        if isinstance(self.body, List):
            body = " ^ ".join(map(str, self.body))
        if isinstance(self.head, List):
            head = " ^ ".join(map(str, self.head))
        return f"{body} -> {head}"

    def __repr__(self):
        return f"Rule({[a.__repr__() for a in self.body]}, {[a.__repr__() for a in self.head]})"
