from typing import List
import sys
import os
from owlapy.owl_ontology import SyncOntology
from owlapy.owl_reasoner import SyncReasoner
from owlapy.owl_axiom import OWLClass, OWLClassExpression
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.iri import IRI
from owlapy.class_expression import OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom, OWLObjectMinCardinality, OWLObjectMaxCardinality, OWLObjectExactCardinality
from owlapy.owl_property import OWLObjectProperty
from owlapy.parser import ManchesterOWLSyntaxParser


def parse_query_string(ns: str, query_str: str) -> OWLClassExpression:
    def split_top_level(expr: str, delimiter: str) -> List[str]:
        parts = []
        depth = 0
        last = 0
        i = 0
        while i < len(expr):
            if expr[i] == '(':
                depth += 1
            elif expr[i] == ')':
                depth -= 1
            elif depth == 0 and expr[i:i+len(delimiter)] == delimiter:
                parts.append(expr[last:i].strip())
                i += len(delimiter) - 1
                last = i + 1
            i += 1
        parts.append(expr[last:].strip())
        return parts

    query_str = query_str.strip()
    if query_str.startswith("(") and query_str.endswith(")"):
        query_str = query_str[1:-1].strip()

    # OR
    or_parts = split_top_level(query_str, " or ")
    if len(or_parts) > 1:
        return OWLClassExpression.or_([parse_query_string(ns, p) for p in or_parts])

    # AND
    and_parts = split_top_level(query_str, " and ")
    if len(and_parts) > 1:
        return OWLClassExpression.and_([parse_query_string(ns, p) for p in and_parts])

    # NOT
    if query_str.startswith("not "):
        return OWLClassExpression.not_(parse_query_string(ns, query_str[4:].strip()))

    # some
    if " some " in query_str:
        p, c = split_top_level(query_str, " some ")
        return OWLObjectSomeValuesFrom(
            OWLObjectProperty(IRI.create(ns + p.strip())),
            parse_query_string(ns, c.strip())
        )

    # only
    if " only " in query_str:
        p, c = split_top_level(query_str, " only ")
        return OWLObjectAllValuesFrom(
            OWLObjectProperty(IRI.create(ns + p.strip())),
            parse_query_string(ns, c.strip())
        )

    # exactly
    if " exactly " in query_str:
        p, n = split_top_level(query_str, " exactly ")
        return OWLObjectExactCardinality(
            int(n.strip()),
            OWLObjectProperty(IRI.create(ns + p.strip()))
        )

    # min
    if " min " in query_str:
        p, n = split_top_level(query_str, " min ")
        return OWLObjectMinCardinality(
            int(n.strip()),
            OWLObjectProperty(IRI.create(ns + p.strip()))
        )

    # max
    if " max " in query_str:
        p, n = split_top_level(query_str, " max ")
        return OWLObjectMaxCardinality(
            int(n.strip()),
            OWLObjectProperty(IRI.create(ns + p.strip()))
        )

    # simple class
    return OWLClass(IRI.create(ns + query_str.strip()))

def main():
    if len(sys.argv) < 5:
        print("Usage: python JustificationExample.py <ontology_path> <namespace> <individual_name> <class_expression>")
        sys.exit(1)

    ontology_path = sys.argv[1]
    ns = sys.argv[2]
    individual_name = sys.argv[3]
    class_expr_str = sys.argv[4]

    if not ns.endswith("#"):
        ns += "#"
    print(f"Loading ontology from: {ontology_path}")
    print("File exists:", os.path.exists(ontology_path))

    ontology = SyncOntology(ontology_path)
    reasoner = SyncReasoner(ontology, reasoner="Pellet")

    target_individual = OWLNamedIndividual(IRI.create(ns + individual_name))
    #parser = ManchesterOWLSyntaxClassExpressionParser()
    #parser.namespace = "http://example.org/"  # or whatever your base IRI is
    #parser = ManchesterOWLSyntaxParser()
    #expr = parser.parse_expression("hasChild some Male")

    target_class = parse_query_string(ns, class_expr_str)

    print("target_individual:", target_individual)
    print("target_class:", target_class)
   # print("expr:", expr)

    justifications = reasoner.create_justifications({target_individual}, target_class)

    print(f"\nJustifications for why '{individual_name}' is an instance of '{class_expr_str}':")
    if not justifications:
        print("  No justifications found.")
    else:
        for i, justification in enumerate(justifications, 1):
            print(f"\nJustification {i}:")
            for ax in justification:
                print("  ", ax)

if __name__ == "__main__":
    main()



#
#
# def parse_query_string(ns: str, query_str: str) -> OWLClassExpression:
#     def split_top_level(expr: str, delimiter: str) -> List[str]:
#         parts = []
#         depth = 0
#         last = 0
#         i = 0
#         while i < len(expr):
#             if expr[i] == '(':
#                 depth += 1
#             elif expr[i] == ')':
#                 depth -= 1
#             elif depth == 0 and expr[i:i+len(delimiter)] == delimiter:
#                 parts.append(expr[last:i].strip())
#                 i += len(delimiter) - 1
#                 last = i + 1
#             i += 1
#         parts.append(expr[last:].strip())
#         return parts
#
#     query_str = query_str.strip()
#     if query_str.startswith("(") and query_str.endswith(")"):
#         query_str = query_str[1:-1].strip()
#
#     # OR
#     or_parts = split_top_level(query_str, " or ")
#     if len(or_parts) > 1:
#         return OWLClassExpression.or_([parse_query_string(ns, p) for p in or_parts])
#
#     # AND
#     and_parts = split_top_level(query_str, " and ")
#     if len(and_parts) > 1:
#         return OWLClassExpression.and_([parse_query_string(ns, p) for p in and_parts])
#
#     # NOT
#     if query_str.startswith("not "):
#         return OWLClassExpression.not_(parse_query_string(ns, query_str[4:].strip()))
#
#     # some
#     if " some " in query_str:
#         p, c = split_top_level(query_str, " some ")
#         return OWLClassExpression.some(
#             OWLObjectProperty(IRI.create(ns + p.strip())),
#             parse_query_string(ns, c.strip())
#         )
#
#     # only
#     if " only " in query_str:
#         p, c = split_top_level(query_str, " only ")
#         return OWLClassExpression.only(
#             OWLObjectProperty(IRI.create(ns + p.strip())),
#             parse_query_string(ns, c.strip())
#         )
#
#     # exactly
#     if " exactly " in query_str:
#         p, n = split_top_level(query_str, " exactly ")
#         return OWLClassExpression.exactly(
#             OWLObjectProperty(IRI.create(ns + p.strip())),
#             int(n.strip())
#         )
#
#     # min
#     if " min " in query_str:
#         p, n = split_top_level(query_str, " min ")
#         return OWLClassExpression.min(
#             OWLObjectProperty(IRI.create(ns + p.strip())),
#             int(n.strip())
#         )
#
#     # max
#     if " max " in query_str:
#         p, n = split_top_level(query_str, " max ")
#         return OWLClassExpression.max(
#             OWLObjectProperty(IRI.create(ns + p.strip())),
#             int(n.strip())
#         )
#
#     # simple class
#     return OWLClass(IRI.create(ns + query_str.strip()))
#
# def main():
#     if len(sys.argv) < 5:
#         print("Usage: python JustificationExample.py <ontology_path> <namespace> <individual_name> <class_expression>")
#         sys.exit(1)
#
#     ontology_path = sys.argv[1]
#     ns = sys.argv[2]
#     individual_name = sys.argv[3]
#     class_expr_str = sys.argv[4]
#
#     if not ns.endswith("#"):
#         ns += "#"
#
#     print("JAVA_HOME:", os.environ.get("JAVA_HOME"))
#     print(f"Loading ontology from: {ontology_path}")
#     print("File exists:", os.path.exists(ontology_path))
#
#     ontology = SyncOntology(ontology_path)
#     reasoner = SyncReasoner(ontology, reasoner="Pellet")
#
#     target_individual = OWLNamedIndividual(IRI.create(ns + individual_name))
#     target_class = parse_query_string(ns, class_expr_str)
#
#     print("target_individual:", target_individual)
#     print("target_class:", target_class)
#
#     justifications = reasoner.create_justifications({target_individual}, target_class)
#
#     print(f"\nJustifications for why '{individual_name}' is an instance of '{class_expr_str}':")
#     if not justifications:
#         print("  No justifications found.")
#     else:
#         for i, justification in enumerate(justifications, 1):
#             print(f"\nJustification {i}:")
#             for ax in justification:
#                 print("  ", ax)
#
# if __name__ == "__main__":
#     main()
#
#
#
#
#
#
#
#
#
#
#
#
#





# from typing import Set, List
# import sys
# import owlready2
# import os
# from owlapy.owl_ontology import SyncOntology  # your class in owl_ontology.py that loads ontology
# from owlapy.owl_reasoner import SyncReasoner  # your reasoner wrapper with create_justification method
# from owlapy.owl_axiom import OWLClass, OWLClassExpression
# from owlapy.owl_individual import OWLNamedIndividual
# from owlapy.iri import IRI
#
# def main():
#     # Expecting 3 arguments: ontology_path, namespace, individual_name
#     if len(sys.argv) < 4:
#         print("Usage: python JustificationExample.py <ontology_path> <namespace> <individual_name>")
#         sys.exit(1)
#
#     ontology_path = sys.argv[1]
#     ns = sys.argv[2]
#     individual_name = sys.argv[3]
#
#     if not ns.endswith("#"):
#         ns += "#"
#
#     print("JAVA_HOME:", os.environ.get("JAVA_HOME"))
#     print(f"Loading ontology from: {ontology_path}")
#     print("File exists:", os.path.exists(ontology_path))
#
#     # Load ontology
#     ontology = SyncOntology(ontology_path)
#
#     # Reasoner setup
#     reasoner = SyncReasoner(ontology, reasoner="Pellet")
#
#     # Construct individual and class
#     # target_individual = "<http://www.benchmark.org/family#F10M171>"
#     # hasChild> <http://www.benchmark.org/family#Male>)
#     target_individual = OWLNamedIndividual(IRI.create(ns + individual_name))
#
#     print("target_individual:", target_individual)
#
#     #target_class = OWLClass(IRI.create(ns + "Interviewed"))
#     target_class = OWLClass(IRI.create(ns + "hasChild some Male"))
#     #target_class = "ObjectSomeValuesFrom(<http://www.benchmark.org/family#hasChild> <http://www.benchmark.org/family#Male>)"
#
#     print("ontology:", ontology)
#
#     print("target_class:", target_class)
#
#
#
#     # Get justifications
#     justifications = reasoner.create_justifications({target_individual}, target_class)
#
#     # Display results
#     print(f"\nJustifications for why '{individual_name}' is an instance of 'Interviewed':")
#     if not justifications:
#         print("  No justifications found.")
#     else:
#         for i, justification in enumerate(justifications, 1):
#             print(f"\nJustification {i}:")
#             for ax in justification:
#                 print("  ", ax)
#
# if __name__ == "__main__":
#     main()
#
#















# from typing import Set, List
# import sys
# import owlready2
# import os
# from owlapy.owl_ontology import Ontology, SyncOntology  # your class in owl_ontology.py that loads ontology
# from owlapy.owl_reasoner import SyncReasoner  # your reasoner wrapper with create_justification method
# from owlapy.owl_axiom import OWLClass, OWLClassExpression, OWLClassAssertionAxiom
# from owlapy.owl_individual import OWLNamedIndividual
#
#
# import sys
# from owlready2 import get_ontology
# from owlapy.iri import IRI
#
#
# def main():
#     # Command-line arguments: ontology_path ns
#     if len(sys.argv) < 3:
#         print("Usage: python JustificationExample.py <ontology_path> <namespace>")
#         sys.exit(1)
#
#     ontology_path = sys.argv[1]
#     ns = sys.argv[2]
#     if not ns.endswith("#"):
#         ns += "#"
#     print("java_home", os.environ.get("JAVA_HOME"))
#
#     print(f"Loading ontology from: {ontology_path}")
#     #ontology = Ontology('file://../KGs/Family/father.owl')
#     print("path exists:", os.path.exists(ontology_path))
#     ontology =  SyncOntology(ontology_path)
#
#     # Hardcoded individual and class
#     alice_individual = OWLNamedIndividual(IRI.create(ns + "Alice"))
#     interviewed_class = OWLClass(IRI.create(ns + "Interviewed"))
#
#     print("ontology:",ontology)
#     print("alice_individual",  alice_individual)
#     print("interviewed_class", interviewed_class)
#
#     # Create reasoner
#     reasoner = SyncReasoner(ontology, reasoner="Pellet")
#
#
#     # Get justifications
#     #justifications = reasoner.create_justifications(alice_individual, interviewed_class)
#     justifications = reasoner.create_justifications({alice_individual}, interviewed_class)
#
#     # Display justifications
#     print(f"\nJustifications for why 'Alice' is an instance of 'Interviewed':")
#     if not justifications:
#         print("  No justifications found.")
#     else:
#         for i, justification in enumerate(justifications, 1):
#             print(f"\nJustification {i}:")
#             for ax in justification:
#                 print("  ", ax)
#
#
# if __name__ == "__main__":
#     main()
