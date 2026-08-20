"""Parallel open-world class-expression retrieval, fanned out across OS processes.

Two different, independent parallelization axes live here -- see
`benchmarks/parallel_reasoner/README.md` for the benchmark data behind why both exist:

- `ParallelReasoner`: parallelizes *within one query*, by sharding the individuals it
  checks membership for across workers. Benchmarks showed this is usually a net loss
  (up to 670x slower observed) because it discards the shared-work reuse that Pellet/
  HermiT's own bulk `getInstances()` already does across individuals internally. It
  only wins when that internal reuse is weak relative to per-individual overhead
  (observed: a small ABox with HermiT).
- `BatchParallelReasoner`: parallelizes *across many different queries* against the
  same ontology, e.g. scoring many candidate class expressions during a concept-
  learning refinement search. Each worker runs its own full, un-decomposed
  `SyncReasoner.instances(ce)` bulk call per expression it's assigned, so every
  worker keeps the reasoner's internal optimizations intact -- only the *set of
  queries*, not the ABox, is split across cores.

In both cases the knowledge base itself is not partitioned: every worker process loads
the same, complete ontology and starts its own JVM and its own Java-backed
`SyncReasoner` (HermiT, Pellet, JFact, Openllet, ELK, or OWLAPI's "Structural" -- any
name `SyncReasoner` accepts).
"""
import atexit
import logging
import multiprocessing as mp
import os
from typing import Iterable, List, Optional, Set

from owlapy.class_expression import OWLClassExpression
from owlapy.owl_individual import OWLNamedIndividual

logger = logging.getLogger(__name__)

# Keep in sync with the reasoner names validated by owlapy.owl_reasoner.SyncReasoner.
_VALID_REASONERS = ("HermiT", "Pellet", "ELK", "JFact", "Openllet", "Structural")

# Set once per worker process by _init_worker. Worker processes never share
# memory (spawned, not forked -- starting a JVM and then fork()-ing is unsafe),
# so this being module-level global state is safe: each process gets its own.
_worker_reasoner = None


def _init_worker(ontology_path: str, reasoner_name: str) -> None:
    """Pool initializer. Runs once per worker process: starts that worker's own
    JVM and loads its own SyncReasoner over the (unpartitioned) ontology."""
    global _worker_reasoner
    from owlapy.owl_reasoner import SyncReasoner
    _worker_reasoner = SyncReasoner(ontology=ontology_path, reasoner=reasoner_name)
    atexit.register(_teardown_worker)


def _teardown_worker() -> None:
    """Runs once per worker process on exit: releases the reasoner and shuts
    down that worker's own JVM. Other workers' JVMs are unaffected."""
    global _worker_reasoner
    from owlapy.static_funcs import stopJVM
    if _worker_reasoner is not None:
        _worker_reasoner.close()
        _worker_reasoner = None
    stopJVM()


def _check_individual(args) -> Optional[str]:
    """Runs in the worker process. Returns the individual's IRI string if the
    worker's KB entails ce(individual), else None.

    Unlike `SyncReasoner.instances()` (which swallows a Java-level timeout and
    returns an empty set), `SyncReasoner.is_entailed()` raises `TimeoutError` on
    timeout. A single slow individual must not abort the whole retrieval, so a
    per-individual timeout is treated the same way `instances()` treats a global
    one: that individual is excluded rather than the exception propagating.
    """
    ce, individual_iri, timeout = args
    from owlapy.owl_axiom import OWLClassAssertionAxiom
    axiom = OWLClassAssertionAxiom(OWLNamedIndividual(individual_iri), ce)
    try:
        return individual_iri if _worker_reasoner.is_entailed(axiom, timeout=timeout) else None
    except TimeoutError:
        return None


class _PooledReasonerBase:
    """Shared JVM-worker-pool lifecycle for `ParallelReasoner` and `BatchParallelReasoner`:
    validates the reasoner name, lazily starts a `spawn`-context `multiprocessing.Pool`
    where each worker runs `_init_worker` (its own JVM + `SyncReasoner`), and tears it
    down via `close()`/context-manager/`__del__`. Subclasses add only the task-dispatch
    method (`instances()` or `instances_batch()`) and the worker-side task function it uses.
    """

    def __init__(self, ontology_path: str, reasoner: str = "HermiT", num_workers: Optional[int] = None):
        """
        Args:
            ontology_path: Path to the ontology file. Loaded independently (and fully,
                unpartitioned) by every worker process.
            reasoner: Name of the Java-backed reasoner each worker should run. Any value
                accepted by `owlapy.owl_reasoner.SyncReasoner` works here too: "HermiT",
                "Pellet", "ELK", "JFact", "Openllet", "Structural". Default: "HermiT".
            num_workers: Number of worker processes (and JVMs) to start. Defaults to
                `os.cpu_count()`.
        """
        assert reasoner in _VALID_REASONERS, (
            f"'{reasoner}' is not implemented. Available reasoners: {list(_VALID_REASONERS)}. "
            f"This field is case sensitive.")
        self.ontology_path = ontology_path
        self.reasoner_name = reasoner
        self.num_workers = num_workers or os.cpu_count() or 1
        self._pool = None

    def _ensure_pool(self):
        if self._pool is None:
            ctx = mp.get_context("spawn")
            self._pool = ctx.Pool(
                processes=self.num_workers,
                initializer=_init_worker,
                initargs=(self.ontology_path, self.reasoner_name),
            )
        return self._pool

    def close(self) -> None:
        """Tear down the worker pool. Each worker's `atexit` hook closes its own
        reasoner and shuts down its own JVM as that worker process exits."""
        if self._pool is not None:
            self._pool.close()
            self._pool.join()
            self._pool = None

    def __enter__(self):
        self._ensure_pool()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class ParallelReasoner(_PooledReasonerBase):
    """Fans out open-world instance retrieval for one ontology across a pool of
    worker processes, each running its own copy of a Java-backed reasoner.

    Reuse one `ParallelReasoner` across multiple `instances()` calls against
    the same ontology: the worker pool (and each worker's JVM + loaded
    reasoner) is started lazily on first use and kept alive, so only the
    first call pays JVM startup cost per worker.

    Example:
        >>> with ParallelReasoner("KGs/Family/father.owl", reasoner="Pellet", num_workers=8) as pr:
        ...     result = pr.instances(male_and_has_child)  # set[OWLNamedIndividual]

    `num_workers` processes are started immediately once the pool is created
    (not lazily per task), so size it to the workload you intend to run
    through this instance rather than to a single call -- it defaults to
    `os.cpu_count()`.
    """

    def instances(self, ce: OWLClassExpression, direct: bool = False, timeout: int = 1000,
                  individuals: Optional[Iterable[OWLNamedIndividual]] = None,
                  chunksize: Optional[int] = None) -> Set[OWLNamedIndividual]:
        """Retrieve Instances(ce) = { a | KB |= ce(a) }, computed across the worker pool.

        Args:
            ce: The class expression to retrieve instances of.
            direct: Must be False -- see module docstring for why direct retrieval isn't
                supported by this strategy.
            timeout: Per-individual entailment-check timeout in seconds, forwarded to
                `SyncReasoner.is_entailed`.
            individuals: The domain to check membership against. Defaults to every named
                individual in the ontology's signature, enumerated once via `RDFLibReasoner`'s
                root ontology (no JVM needed for this step).
            chunksize: Individuals handed to a worker per IPC round-trip. The default (1)
                favors load balancing across workers with uneven per-individual reasoning
                cost; raise it to cut IPC overhead when checks are all cheap.

        Returns:
            The set of individuals for which membership was entailed. Identical to what
            `SyncReasoner(ontology_path, reasoner).instances(ce, direct=False)` returns.
        """
        if direct:
            raise NotImplementedError(
                "ParallelReasoner.instances() only supports direct=False: 'direct' instance "
                "retrieval requires identifying each individual's most-specific type, which "
                "isn't expressible as a single per-individual entailment check.")

        if individuals is None:
            from owlapy.owl_reasoner_rdflib import RDFLibReasoner
            individuals = list(RDFLibReasoner(self.ontology_path).get_root_ontology().individuals_in_signature())
        else:
            individuals = list(individuals)

        if not individuals:
            return set()

        pool = self._ensure_pool()
        tasks = [(ce, ind.str, timeout) for ind in individuals]
        found = {iri for iri in pool.imap_unordered(_check_individual, tasks, chunksize=chunksize or 1)
                 if iri is not None}
        return {OWLNamedIndividual(iri) for iri in found}


def _run_expression(args):
    """Runs in the worker process. Returns (index, iri_list_or_None, error_message_or_None).

    Unlike `_check_individual`, this calls `SyncReasoner.instances()` (bulk, per-worker,
    un-decomposed) rather than `is_entailed()` per individual -- each task here is one
    whole class-expression query, not one individual.
    """
    idx, ce, timeout = args
    try:
        result = sorted(i.str for i in _worker_reasoner.instances(ce, timeout=timeout))
        return idx, result, None
    except Exception as e:  # noqa: BLE001 -- a bad expression must not abort the whole batch
        return idx, None, f"{type(e).__name__}: {e}"


class BatchParallelReasoner(_PooledReasonerBase):
    """Fans out MANY DIFFERENT class-expression retrieval queries across a pool of worker
    processes, each running its own JVM and its own copy of a Java-backed reasoner.

    Unlike `ParallelReasoner` (which shards *one* query's individuals across workers,
    and was found to usually be slower than the reasoner's own bulk retrieval -- see
    `benchmarks/parallel_reasoner/README.md`), this shards the *query set*: each worker
    runs its own full, un-decomposed `SyncReasoner.instances(ce)` call per expression it's
    assigned. Every worker keeps the reasoner's internal realization/reuse optimizations
    intact, so this should scale close to linearly with `num_workers` for a batch of
    independent queries -- e.g. scoring many candidate concepts during a concept-learning
    refinement search.

    Example:
        >>> with BatchParallelReasoner("KGs/Family/father.owl", reasoner="Pellet", num_workers=8) as bpr:
        ...     results = bpr.instances_batch([ce1, ce2, ce3])  # list[set[OWLNamedIndividual]]

    Reuse one `BatchParallelReasoner` across multiple `instances_batch()` calls against
    the same ontology: the worker pool is started lazily on first use and kept alive, so
    only the first call pays JVM startup cost per worker. `num_workers` processes are
    started immediately once the pool is created (not lazily per task); it defaults to
    `os.cpu_count()`.
    """

    def instances_batch(self, expressions: Iterable[OWLClassExpression],
                         timeout: int = 1000, chunksize: Optional[int] = None) -> List[Set[OWLNamedIndividual]]:
        """Retrieve Instances(ce) for every ce in `expressions`, one bulk call per
        expression, dispatched across the worker pool.

        Args:
            expressions: The class expressions to retrieve instances of. `direct=False`
                semantics throughout (same as `SyncReasoner.instances()`'s default).
            timeout: Per-expression bulk-call timeout in seconds, forwarded to
                `SyncReasoner.instances()`. Unlike `ParallelReasoner.instances()`'s
                `timeout`, this bounds a whole query, not a single individual -- it means
                the same thing here as it does for `SyncReasoner` directly.
            chunksize: Expressions handed to a worker per IPC round-trip. The default (1)
                favors load balancing across workers with uneven per-query cost.

        Returns:
            A list aligned with `expressions` (same order, same length): result[i] is the
            instance set for expressions[i]. If a given expression's reasoning task raises
            (a reasoner-internal error, not a timeout -- `SyncReasoner.instances()` itself
            degrades to an empty set on timeout) that expression's slot is an empty set and
            a warning is logged, rather than the whole batch aborting.
        """
        expressions = list(expressions)
        if not expressions:
            return []

        pool = self._ensure_pool()
        tasks = [(idx, ce, timeout) for idx, ce in enumerate(expressions)]
        results: List[Optional[Set[OWLNamedIndividual]]] = [None] * len(expressions)
        for idx, iris, err in pool.imap_unordered(_run_expression, tasks, chunksize=chunksize or 1):
            if err is not None:
                logger.warning(f"BatchParallelReasoner: expression {idx} ({expressions[idx]}) failed: {err}")
                results[idx] = set()
            else:
                results[idx] = {OWLNamedIndividual(iri) for iri in iris}
        return results
