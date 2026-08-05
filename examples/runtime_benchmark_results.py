import argparse
import threading
import time

from owlapy import dl_to_owl_expression
from owlapy.owl_ontology import Ontology
from owlapy.owl_reasoner import StructuralReasoner, SyncReasoner
from owlapy.owl_reasoner_rdflib import RDFLibReasoner

# Every reasoner benchmarked, in table-column order. "Structural" (last) is the Java OWL API's
# own structural reasoner, requested via SyncReasoner(reasoner="Structural") -- distinct from the
# pure-Python StructuralReasoner/RDFLibReasoner above it.
ALL_REASONERS = ["StructuralReasoner", "RDFLibReasoner", "HermiT", "Pellet", "Openllet", "JFact", "ELK", "Structural"]
JVM_REASONERS = {"HermiT", "Pellet", "Openllet", "JFact", "ELK", "Structural"}

FAMILY_PATH = "../KGs/Family/family-benchmark_rich_background.owl"
CARCINOGENESIS_PATH = "../KGs/Carcinogenesis/carcinogenesis.owl"

# Hard upper bound (seconds) on how long a single reasoner may spend on a single class
# expression before this script gives up on it and moves on, rather than waiting for a reasoner
# that may never terminate. Enforced here at the script level (a daemon thread we stop waiting
# on after this many seconds) rather than relying solely on each reasoner's own `timeout`
# parameter: StructuralReasoner's `instances(timeout=...)` does not actually bound anything,
# since `_instances()` is a generator function -- wrapping the (near-instant) call that creates
# the generator in a timeout never bounds the real work, which only happens once the generator
# is iterated/materialized. RDFLibReasoner's `timeout` parameter is documented as accepted "for
# compatibility, not enforced". Only SyncReasoner's `timeout` genuinely cancels the underlying
# Java computation; it's still passed through here as a (real) best-effort second layer.
HARD_TIMEOUT_SECONDS = 1000


def _progress(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def _run_bounded(fn, timeout_seconds):
    """
    Run fn() in a daemon thread and wait at most timeout_seconds for it to finish.

    Returns (elapsed_seconds, timed_out). If fn() hasn't finished within timeout_seconds, this
    gives up and returns immediately WITHOUT waiting any further for the abandoned thread --
    which may keep running in the background; Python threads (and, transitively, the JVM calls
    some of them make via JPype) cannot be forcibly killed, only abandoned.
    """
    done = threading.Event()

    def _target():
        try:
            fn()
        finally:
            done.set()

    start = time.time()
    t = threading.Thread(target=_target, daemon=True)
    t.start()
    finished = done.wait(timeout_seconds)
    elapsed = time.time() - start
    return elapsed, not finished


def _construct_reasoner(name, path):
    if name == "StructuralReasoner":
        return StructuralReasoner(Ontology(path))
    if name == "RDFLibReasoner":
        return RDFLibReasoner(path)
    return SyncReasoner(ontology=path, reasoner=name)


def record_runtime(ces, path, namespace, single_reasoner, timeout_seconds=HARD_TIMEOUT_SECONDS):
    reasoner_names = [single_reasoner] if single_reasoner is not None else list(ALL_REASONERS)
    timeout_label = f"TIMEOUT(>{timeout_seconds}s)"

    runtime = dict()
    for name in reasoner_names:
        _progress(f"{name}: constructing reasoner + loading ontology...")
        reasoner = _construct_reasoner(name, path)

        runtime[name] = []
        _progress(f"{name}: 0/{len(ces)} class expressions")
        for i, ce in enumerate(ces, 1):
            ce_in_owl = dl_to_owl_expression(dl_expression=ce, namespace=namespace)
            # set(...) forces full materialization -- required for correct timing, since
            # StructuralReasoner/RDFLibReasoner's instances() are lazy for at least part of
            # their result construction.
            def query_fn(r=reasoner, c=ce_in_owl, n=name):
                if n in JVM_REASONERS:
                    return set(r.instances(c, timeout=timeout_seconds))
                return set(r.instances(c))

            elapsed, timed_out = _run_bounded(query_fn, timeout_seconds)
            value = timeout_label if timed_out else float("{:.4f}".format(elapsed))
            runtime[name].append(value)
            _progress(f"{name}: {i}/{len(ces)} done ({value}) -- {ce}")

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


def print_results_on_family(pretty_print: bool = False, single_reasoner: str = None,
                             timeout_seconds: int = HARD_TIMEOUT_SECONDS):
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
    runtime = record_runtime(ces, FAMILY_PATH, NS, single_reasoner, timeout_seconds)
    print(generate_md_table(runtime, ces, pretty_print))


def print_results_on_carcinogenesis(pretty_print: bool = False, single_reasoner: str = None,
                                     timeout_seconds: int = HARD_TIMEOUT_SECONDS):
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

    runtime = record_runtime(ces, CARCINOGENESIS_PATH, NS, single_reasoner, timeout_seconds)
    print(generate_md_table(runtime, ces, pretty_print))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pretty_print', action="store_true", help='If you want to pretty-print the table.')
    parser.add_argument('--single_reasoner', type=str, default=None,
                        choices=ALL_REASONERS,
                        help="Specify the reasoner you want to test. Leave to None if you want to test them all.")
    parser.add_argument('--timeout_seconds', type=int, default=HARD_TIMEOUT_SECONDS,
                        help="Hard upper bound (seconds) per class expression per reasoner. A reasoner that "
                             "hasn't returned within this many seconds is reported as TIMEOUT instead of being "
                             "waited on further.")
    parser.add_argument('--only_family', action="store_true", help='If you want to run it only on the '
                                                                   'family dataset.')
    parser.add_argument('--only_carcinogenesis', action="store_true", help='If you want to run it only on '
                                                                           'the Carcinogenesis dataset.')
    args = parser.parse_args()

    if args.only_family and not args.only_carcinogenesis:
        print_results_on_family(args.pretty_print, args.single_reasoner, args.timeout_seconds)
    elif args.only_carcinogenesis and not args.only_family:
        print_results_on_carcinogenesis(args.pretty_print, args.single_reasoner, args.timeout_seconds)
    elif not args.only_family and not args.only_carcinogenesis:
        print_results_on_family(args.pretty_print, args.single_reasoner, args.timeout_seconds)
        print_results_on_carcinogenesis(args.pretty_print, args.single_reasoner, args.timeout_seconds)
    else:
        print("ERROR: These two flags cannot occur at the same time: '--only_family', '--only_carcinogenesis'")
