"""Regression check for the performance claim in benchmarks/parallel_reasoner/README.md
(Part 2): BatchParallelReasoner should be meaningfully faster than sequential SyncReasoner
calls when the reasoner backend's own bulk calls are individually expensive -- the full
benchmark measured 2.03x-5.04x for HermiT on both a small and a 14K-individual ABox. This
is a smaller, faster-running version of that same measurement (a subset of the same
checked-in expression corpus, fewer workers), asserting a much more conservative 1.2x
margin to leave headroom for slower/noisier machines.

Deliberately excluded from the default test run (see CLAUDE.md / .github/workflows/test.yml,
same convention as tests/test_z_do_last_ebr_retrieval.py): CI runs on small, shared GitHub-
hosted runners under `pytest -x` (fail-fast), where a wall-clock timing assertion is far more
prone to noise than on a dedicated machine, and a flaky failure here would block unrelated
PRs. Run explicitly with:

    PYTHONPATH=. pytest tests/test_parallel_reasoner_benchmark_regression.py -p no:warnings -v

This intentionally does NOT assert anything about ParallelReasoner (individual-level
sharding): benchmarks/parallel_reasoner/README.md (Part 1) found that strategy is usually
*slower* than sequential SyncReasoner, so there is no "works well" regression to guard there.
"""
import time
import unittest

from owlapy.owl_reasoner import SyncReasoner
from owlapy.parallel_reasoner import BatchParallelReasoner
from owlapy.parser import manchester_to_owl_expression

NS = "http://www.benchmark.org/family#"
PATH = "KGs/Family/family-benchmark_rich_background.owl"
# Subset of the exact, checked-in corpus benchmarks/parallel_reasoner/ used for the full
# (100-expression) measurement, so this test tracks the real benchmark rather than a
# hand-picked easy case.
EXPRESSIONS_PATH = "benchmarks/parallel_reasoner/expressions/family.txt"
N_EXPRESSIONS = 40
# Deliberately small and fixed rather than os.cpu_count(): keeps this test's behavior
# similar on a modest CI runner and a many-core dev machine alike, and avoids
# oversubscribing a small shared runner.
NUM_WORKERS = 2
# The full benchmark measured 2.03x on Family+HermiT at 100 expressions / 22 workers; this
# margin is deliberately far more conservative to absorb machine-to-machine noise while
# still catching a genuine regression (e.g. the win disappearing or flipping negative).
MIN_SPEEDUP = 1.2


def _load_expressions(limit):
    with open(EXPRESSIONS_PATH) as f:
        lines = [line.strip() for line in f if line.strip()][:limit]
    return [manchester_to_owl_expression(text, NS) for text in lines]


class TestBatchParallelReasonerHermitSpeedup(unittest.TestCase):
    """Simplified version of benchmarks/parallel_reasoner/run_batch_benchmark.py."""

    def test_batch_parallel_beats_sequential_with_hermit(self):
        expressions = _load_expressions(N_EXPRESSIONS)
        self.assertEqual(len(expressions), N_EXPRESSIONS)

        sync_reasoner = SyncReasoner(ontology=PATH, reasoner="HermiT")
        t0 = time.perf_counter()
        sequential_results = [set(sync_reasoner.instances(ce, timeout=30)) for ce in expressions]
        sequential_total = time.perf_counter() - t0
        sync_reasoner.close()

        with BatchParallelReasoner(PATH, reasoner="HermiT", num_workers=NUM_WORKERS) as bpr:
            t0 = time.perf_counter()
            batch_results = bpr.instances_batch(expressions, timeout=30)
            batch_total = time.perf_counter() - t0

        # Correctness is the primary claim -- checked before the performance claim, since a
        # speedup from wrong-but-fast answers would be worthless.
        self.assertEqual(batch_results, sequential_results)

        self.assertLess(
            batch_total, sequential_total / MIN_SPEEDUP,
            f"expected BatchParallelReasoner to be >={MIN_SPEEDUP}x faster than sequential "
            f"SyncReasoner calls with HermiT (full benchmark: 2.03x-5.04x, see "
            f"benchmarks/parallel_reasoner/README.md Part 2), but got "
            f"sequential={sequential_total:.2f}s vs batch_parallel={batch_total:.2f}s "
            f"({sequential_total / batch_total:.2f}x)")


if __name__ == "__main__":
    unittest.main()
