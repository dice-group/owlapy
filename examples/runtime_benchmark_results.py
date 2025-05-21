import argparse
import time
from owlapy.owl_ontology import Ontology
from owlapy.owl_reasoner import SyncReasoner, StructuralReasoner
from owlapy import dl_to_owl_expression

sync_reasoners = ["HermiT", "Pellet", "Openllet", "JFact", "ELK", "Structural"]
FAMILY_PATH = "../KGs/Family/family-benchmark_rich_background.owl"
CARCINOGENESIS_PATH = "../KGs/Carcinogenesis/carcinogenesis.owl"


def record_runtime(ces, path, namespace, single_reasoner):
    global sync_reasoners

    runtime = dict()
    native_reasoner = None
    # Check if we are using a single reasoner
    if single_reasoner is not None:
        if single_reasoner == "StructuralReasoner":
            native_reasoner = StructuralReasoner(Ontology(path))
            sync_reasoners = []
        elif single_reasoner in sync_reasoners:
            sync_reasoners = [single_reasoner]

    if native_reasoner:
        # Results for StructuralReasoner
        runtime["StructuralReasoner"] = []
        for ce in ces:
            start = time.time()
            ce_in_owl = dl_to_owl_expression(dl_expression=ce, namespace=namespace)
            inds = native_reasoner.instances(ce_in_owl)
            runtime["StructuralReasoner"].append(float("{:.4f}".format(time.time() - start)))
    for reasoner in sync_reasoners:
        # Results for Sync reasoners
        runtime[reasoner] = []
        sync_reasoner = SyncReasoner(ontology=path, reasoner=reasoner)
        for ce in ces:
            start = time.time()
            ce_in_owl = dl_to_owl_expression(dl_expression=ce, namespace=namespace)
            inds = sync_reasoner.instances(ce_in_owl)
            runtime[reasoner].append(float("{:.4f}".format(time.time() - start)))

    return runtime


def generate_md_table(data, ce_labels, pretty_print):
    # Identify unique lists and assign column headers from the original dict
    unique_lists = {}
    for key, value in data.items():
        t = tuple(value)
        if t not in unique_lists:
            unique_lists[t] = key

    # Prepare the table columns and rows
    headers = list(unique_lists.values())
    columns = list(unique_lists.keys())
    max_len = max(len(col) for col in columns)

    # Check that CE labels match the number of rows
    if len(ce_labels) != max_len:
        raise ValueError(f"Length of ce_labels ({len(ce_labels)}) must match the number of table rows ({max_len}).")

    # Normalize column lengths (fill shorter ones with empty string)
    normalized_cols = [list(col) + [''] * (max_len - len(col)) for col in columns]

    # Add CE column at the beginning
    full_headers = ['Class Expressions'] + headers
    full_rows = [[ce_labels[i]] + [col[i] for col in normalized_cols] for i in range(max_len)]

    if not pretty_print:
        # Build the markdown table
        table = '| ' + ' | '.join(full_headers) + ' |\n'
        table += '| ' + ' | '.join(['---'] * len(full_headers)) + ' |\n'
        for row in full_rows:
            table += '| ' + ' | '.join(map(str, row)) + ' |\n'

        return table
    else:
        # Determine column widths
        col_widths = [max(len(str(item)) for item in [header] + [row[i] for row in full_rows]) for i, header in
                      enumerate(full_headers)]

        def format_row(r):
            return " | ".join(f"{str(item):<{w}}" for item, w in zip(r, col_widths))

        lines = [
                    format_row(full_headers),
                    "-+-".join('-' * w for w in col_widths),
                ] + [format_row(row) for row in full_rows]

        return "\n".join(lines)


def print_results_on_family(pretty_print: bool = False, single_reasoner: str = None):
    ces = ["Person",
           "(¬Parent)",
           "∀ hasParent.Father",
           '∃ hasSibling.Daughter',
           '∃ hasChild.(¬Parent)',
           '≥ 1 married.Male',
           "≤ 3 hasChild.Person",
           "Brother ⊓ Parent",
           "Mother ⊔ Father",
           "∃ hasParent.{F9M170 ⊔ F9M147 ⊔ F7M128}"
           ]
    NS = "http://www.benchmark.org/family#"
    runtime = record_runtime(ces, FAMILY_PATH, NS, single_reasoner)
    print(generate_md_table(runtime, ces, pretty_print))


def print_results_on_carcinogenesis(pretty_print: bool = False, single_reasoner: str = None):
    ces = ["Sulfur",
           "Structure",
           "¬Structure",
           "∀ hasAtom.Atom",
           "∃ hasStructure.Amino",
           "≥ 2 inBond.⊤",
           "≤ 3 hasAtom.⊤",
           "Ring_size_4 ⊓ Sulfur",
           "Bond-7 ⊔ Bond-3",
           "∃ hasBond.{bond1838 ⊔ bond1879 ⊔ bond1834}",
           "∃ isMutagenic.{True}",
           "∃ charge.xsd:double[> 0.1]",
           "Compound ⊓ ∃ isMutagenic.{True}",
           "Carbon ⊓ ∃ charge.xsd:double[> 0.1]"
           ]
    NS = "http://dl-learner.org/carcinogenesis#"

    runtime = record_runtime(ces, CARCINOGENESIS_PATH, NS, single_reasoner)
    print(generate_md_table(runtime, ces, pretty_print))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pretty_print', action="store_true", help='If you want to pretty-print the table.')
    parser.add_argument('--single_reasoner', type=str, default=None,
                        choices=["StructuralReasoner", "HermiT", "Pellet", "Openllet", "JFact", "ELK", "Structural"],
                        help="Specify the reasoner you want to test. Leave to None if you want to test them all.")
    parser.add_argument('--only_family', action="store_true", help='If you want to run it only on the '
                                                                   'family dataset.')
    parser.add_argument('--only_carcinogenesis', action="store_true", help='If you want to run it only on '
                                                                           'the Carcinogenesis dataset.')
    args = parser.parse_args()

    if args.only_family and not args.only_carcinogenesis:
        print_results_on_family(args.pretty_print, args.single_reasoner)
    elif args.only_carcinogenesis and not args.only_family:
        print_results_on_carcinogenesis(args.pretty_print, args.single_reasoner)
    elif not args.only_family and not args.only_carcinogenesis:
        print_results_on_family(args.pretty_print, args.single_reasoner)
        print_results_on_carcinogenesis(args.pretty_print, args.single_reasoner)
    else:
        print("ERROR: These two flags cannot occur at the same time: '--only_family', '--only_carcinogenesis'")