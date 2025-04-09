from owlapy.owl_reasoner import SyncReasoner
from owlapy.owl_ontology import Ontology
from owlapy.class_expression import OWLClassExpression
from typing import Dict
ontology_path = "../KGs/Family/family-benchmark_rich_background.owl"
# () Load ontology
onto = Ontology(ontology_path, load=True)

# () Initialize Reasoners
reasoners = dict()
reasoners["HermiT"] = SyncReasoner(ontology=ontology_path, reasoner="HermiT")
reasoners["Pellet"] = SyncReasoner(ontology=ontology_path, reasoner="Pellet")
reasoners["JFact"] = SyncReasoner(ontology=ontology_path, reasoner="JFact")
reasoners["Openllet"] = SyncReasoner(ontology=ontology_path, reasoner="Openllet")


def compute_agreements(owl_reasoners:Dict[str,SyncReasoner], expression: OWLClassExpression, verbose=False):
    if verbose:
        print(f"Computing agreements between Reasoners on {expression}...",end="\t")
    retrieval_result = None
    flag = False
    for __, reasoner in owl_reasoners.items():
        if retrieval_result:
            flag = retrieval_result == {_.str for _ in reasoner.instances(expression)}
        else:
            retrieval_result = {_.str for _ in reasoner.instances(expression)}
    if verbose:
        print(f"Successful:{flag}")
    return flag


# () Iterate over named classes
for c in onto.classes_in_signature():
    # reasoners must agree
    assert compute_agreements(reasoners, c, True)