"""Parallel open-world class-expression retrieval, fanned out across OS processes.

The knowledge base is *not* partitioned. Every worker process loads the same,
complete ontology and starts its own JVM and its own Java-backed
`SyncReasoner` (HermiT, Pellet, JFact, Openllet, ELK, or OWLAPI's
"Structural" -- any name `SyncReasoner` accepts). Retrieval of Instances(ce)
is embarrassingly parallel at the level of individuals: for a fixed KB,
"KB |= ce(a)" for different individuals `a` are independent decision
problems, so answers from any worker over any subset of individuals can be
unioned freely. This gives identical (sound + complete) results to a single
`SyncReasoner.instances(ce)` call, just computed concurrently -- it trades
redundant per-worker JVM startup/TBox-classification cost for wall-clock
throughput on the ABox side, so it pays off when the number of individuals
being checked is large relative to that startup cost.

Not supported: `direct=True` instance retrieval. A "direct" instance is one
whose *most specific* type is `ce`, which requires comparing against every
other candidate type and isn't expressible as a single per-individual
entailment check.
"""
import atexit
import multiprocessing as mp
import os
from typing import Iterable, Optional, Set

from owlapy.class_expression import OWLClassExpression
from owlapy.owl_individual import OWLNamedIndividual

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
    worker's KB entails ce(individual), else None."""
    ce, individual_iri, timeout = args
    from owlapy.owl_axiom import OWLClassAssertionAxiom
    axiom = OWLClassAssertionAxiom(OWLNamedIndividual(individual_iri), ce)
    return individual_iri if _worker_reasoner.is_entailed(axiom, timeout=timeout) else None


class ParallelReasoner:
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

    def close(self) -> None:
        """Tear down the worker pool. Each worker's `atexit` hook closes its own
        reasoner and shuts down its own JVM as that worker process exits."""
        if self._pool is not None:
            self._pool.close()
            self._pool.join()
            self._pool = None

    def __enter__(self) -> "ParallelReasoner":
        self._ensure_pool()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
