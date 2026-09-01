"""NIR (Neural Instance Retrieval) reasoner.

TBox / hierarchy / role queries are delegated to a symbolic fallback
(:class:`~owlapy.owl_reasoner.StructuralReasoner` on an owlready2
:class:`~owlapy.owl_ontology.Ontology`, otherwise
:class:`~owlapy.owl_reasoner_rdflib.RDFLibReasoner`). Instance retrieval for
class expressions longer than ``symbolic_max_length`` is answered by a
pretrained NIR encoder (Transformer / LSTM / GRU / Composite) implemented in
:mod:`owlapy.nir`.

This is the neural counterpart of :class:`~owlapy.owl_reasoner.EBR`, but it
does **not** use ``NeuralOntology`` / ``dicee``. It scores class expressions
in DL syntax against DeCaL (or any CSV) entity embeddings.

Requires ``torch``, ``transformers``, and ``pandas``. Those are imported lazily
so installing owlapy without them still works.

Example
-------
::

    from owlapy.owl_ontology import Ontology
    from owlapy.owl_reasoner import NIRReasoner

    onto = Ontology("KGs/Family/family-benchmark_rich_background.owl")
    reasoner = NIRReasoner(
        onto,
        model_path="trained_models/nir_pretrained_models/NIR_Transformer_family",
        embeddings_path="trained_models/embeddings/family/DeCaL_entity_embeddings.csv",
    )
    instances = set(reasoner.instances(named_class))
"""

from __future__ import annotations

import glob
import json
import logging
import os
import re
from typing import Dict, FrozenSet, Iterable, List, Optional, Union

from owlapy.abstracts.abstract_owl_ontology import AbstractOWLOntology
from owlapy.abstracts.abstract_owl_reasoner import AbstractOWLReasoner
from owlapy.class_expression import OWLClassExpression, OWLNothing, OWLThing
from owlapy.owl_data_ranges import OWLDataRange
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_literal import OWLLiteral
from owlapy.owl_object import OWLEntity
from owlapy.owl_property import OWLDataProperty, OWLObjectProperty, OWLObjectPropertyExpression
from owlapy.render import DLSyntaxObjectRenderer
from owlapy.utils import get_expression_length

logger = logging.getLogger(__name__)

_ARCH_TO_CLASS = {
    "NIRTransformer": "NIRTransformer",
    "transformer": "NIRTransformer",
    "NIRLSTM": "NIRLSTM",
    "lstm": "NIRLSTM",
    "NIRGRU": "NIRGRU",
    "gru": "NIRGRU",
    "NIRComposite": "NIRComposite",
    "composite": "NIRComposite",
}


def _short_name(iri: str) -> str:
    text = str(iri)
    if "/" in text:
        return text.split("/")[-1]
    return text


def _load_entity_embeddings(embeddings_path: Optional[str], dataset_dir: Optional[str]):
    """Load a DeCaL-style ``*entity_embeddings.csv`` (index = entity IRI or short name)."""
    import pandas as pd

    csv_path = None
    search_roots: List[str] = []
    if embeddings_path:
        search_roots.append(embeddings_path)
    if dataset_dir:
        search_roots.append(dataset_dir)

    for root in search_roots:
        if not root:
            continue
        if os.path.isfile(root) and root.endswith(".csv"):
            csv_path = root
            break
        if os.path.isdir(root):
            hits = glob.glob(os.path.join(root, "*entity_embeddings.csv"))
            if not hits:
                hits = glob.glob(os.path.join(root, "embeddings", "*entity_embeddings.csv"))
            if hits:
                csv_path = hits[0]
                break

    if csv_path is None:
        raise FileNotFoundError(
            "No *entity_embeddings.csv found. Pass embeddings_path to a CSV file "
            "or a dataset directory that contains embeddings/."
        )

    df = pd.read_csv(csv_path, index_col=0)
    # Paper loader drops duplicate rows on the first embedding column ("0").
    if "0" in df.columns:
        df = df.drop_duplicates(subset="0")
    elif 0 in df.columns:
        df = df.drop_duplicates(subset=0)
    df.index = df.index.map(_short_name)
    df = df[~df.index.duplicated(keep="first")]
    return df, csv_path


def _find_relation_embeddings_csv(entity_csv_path: str, embeddings_path: Optional[str], dataset_dir: Optional[str]):
    """Locate ``*relation_embeddings.csv`` next to the entity CSV or under the search roots."""
    candidates: List[str] = []
    sibling = entity_csv_path.replace("entity_embeddings.csv", "relation_embeddings.csv")
    if sibling != entity_csv_path:
        candidates.append(sibling)
    search_roots: List[str] = [os.path.dirname(entity_csv_path)]
    if embeddings_path:
        search_roots.append(embeddings_path)
    if dataset_dir:
        search_roots.append(dataset_dir)
    for root in search_roots:
        if not root:
            continue
        if os.path.isfile(root) and root.endswith("relation_embeddings.csv"):
            candidates.append(root)
            continue
        if os.path.isdir(root):
            candidates.extend(glob.glob(os.path.join(root, "*relation_embeddings.csv")))
            candidates.extend(glob.glob(os.path.join(root, "embeddings", "*relation_embeddings.csv")))
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def _merge_relation_embeddings(entity_df, entity_csv_path: str, embeddings_path: Optional[str], dataset_dir: Optional[str]):
    """Append relation rows (needed by Composite to look up roles in DL strings)."""
    import pandas as pd

    rel_path = _find_relation_embeddings_csv(entity_csv_path, embeddings_path, dataset_dir)
    if rel_path is None:
        return entity_df
    rel = pd.read_csv(rel_path, index_col=0)
    rel.index = rel.index.map(_short_name)
    rel = rel[~rel.index.duplicated(keep="first")]
    combined = pd.concat([entity_df, rel], axis=0)
    return combined[~combined.index.duplicated(keep="first")]


def _mean_pool_named_class_embeddings(embeddings, ontology, fallback):
    """Replace class rows with the mean of their instances (paper ``read_embs_and_apply_agg`` without PMA)."""
    named = {_short_name(c.str): c for c in ontology.classes_in_signature()}
    for short, cls in named.items():
        if short not in embeddings.index:
            continue
        inst_shorts = [_short_name(i.str) for i in fallback.instances(cls)]
        inst_shorts = [s for s in inst_shorts if s in embeddings.index]
        if inst_shorts:
            embeddings.loc[short] = embeddings.loc[inst_shorts].mean(axis=0)
    return embeddings


def _component_embeddings_for_expr(expr: str, embeddings, device):
    """Map each atomic token of a DL string to an embedding row (paper ``InferenceDataset``)."""
    import torch

    dtype = torch.float32
    cardinality = re.search(r"\[(≤|≥)\s-?\d+(\.\d+)?\]", expr)
    if cardinality:
        expr_modified = expr.replace(cardinality.group(), " ⊤")
        expr_modified = re.sub(r"[ \(\)⊔.∃∀⊓¬⁻≤:\[]+", "|", expr_modified)
    else:
        expr_modified = re.sub(r"[ \(\)⊔.∃∀⊓¬⁻≤:\[]+", "|", expr)
    components = list({comp.strip() for comp in expr_modified.split("|") if comp.strip()})
    if "⊥" in components:
        components.remove("⊥")
        components.append("⊤")
    elif "{True}" in components:
        components.remove("{True}")
        components.append("⊤")
    elif "{False}" in components:
        components.remove("{False}")
        components.append("⊤")

    index_str = embeddings.index.astype(str)
    top_tensor = torch.tensor(embeddings.loc[embeddings.index == "⊤"].values, dtype=dtype).squeeze()
    component_embeddings = {}
    for comp in components:
        if comp == "⊤":
            tensor = top_tensor
        else:
            mask = index_str.str.match(rf".*(?<![\-\s+])\b{re.escape(comp)}\b\s*$")
            matched = embeddings.loc[mask]
            if matched.empty and comp in embeddings.index:
                matched = embeddings.loc[[comp]]
            tensor = torch.tensor(matched.values, dtype=dtype).squeeze()
        component_embeddings[comp] = tensor
    if "⊤" not in component_embeddings:
        component_embeddings["⊤"] = top_tensor
    for comp, tensor in component_embeddings.items():
        if tensor.dim() > 1 and tensor.size(0) > 1:
            tensor = tensor[0]
        component_embeddings[comp] = tensor.to(device)
    return component_embeddings


def _score_all_inds(model, tokenizer, all_ind_embs, exprs, hidden_size, chunk_size=1024):
    """Membership scores for every individual vs. each DL expression (copied from nir.utils)."""
    import numpy as np

    outputs = []
    inputs = tokenizer(
        exprs,
        padding="max_length",
        truncation=True,
        max_length=model.max_length,
        return_tensors="pt",
    )
    input_ids = inputs["input_ids"].to(model.device)
    attention_mask = inputs["attention_mask"].to(model.device)
    for i in range(0, all_ind_embs.shape[0], chunk_size):
        ind_embs = all_ind_embs[i : i + chunk_size]
        ind_embs_reshaped = ind_embs.reshape(-1, hidden_size).repeat(len(exprs), 1)
        out = model(input_ids, attention_mask, ind_embs_reshaped)
        out = out.detach().cpu().numpy().squeeze()
        out = out.reshape(-1, ind_embs.shape[0])
        outputs.append(out)
    return np.concatenate(outputs, axis=1)


def _resolve_architecture(model_path: str, model_name: Optional[str]) -> str:
    if model_name:
        return model_name
    config_path = os.path.join(model_path, "config.json")
    if os.path.isfile(config_path):
        with open(config_path) as f:
            cfg = json.load(f)
        archs = cfg.get("architectures") or []
        if archs:
            return archs[0]
    return "NIRTransformer"


def _register_and_load(model_path: str, architecture: str, device):
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise ImportError(
            "NIRReasoner requires torch and transformers. Install with: pip install torch transformers"
        ) from exc

    from owlapy.nir import NIRComposite, NIRGRU, NIRLSTM, NIRTransformer

    key = architecture.strip()
    class_name = _ARCH_TO_CLASS.get(key)
    if class_name is None:
        raise ValueError(
            f"Unsupported NIR architecture {architecture!r}. "
            f"Supported: {sorted(_ARCH_TO_CLASS)}"
        )
    cls = {
        "NIRTransformer": NIRTransformer,
        "NIRLSTM": NIRLSTM,
        "NIRGRU": NIRGRU,
        "NIRComposite": NIRComposite,
    }[class_name]
    model = cls.from_pretrained(model_path).to(device)
    model.eval()
    if class_name == "NIRComposite":
        return model, None
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    return model, tokenizer


def _score_all_inds_composite(model, exprs, all_ind_embs, component_embeddings_dict, chunk_size=1024):
    """Membership scores for Composite (no tokenizer; DL string is parsed inside the model)."""
    import numpy as np

    outputs = []
    for i in range(0, all_ind_embs.shape[0], chunk_size):
        ind_embs = all_ind_embs[i : i + chunk_size]
        ind_embs_expanded = ind_embs.repeat(len(exprs), 1, 1).to(model.device)
        out = model(exprs, ind_embs_expanded, component_embeddings_dict)
        out = out.detach().cpu().numpy().squeeze()
        out = out.reshape(-1, ind_embs.shape[0])
        outputs.append(out)
    return np.concatenate(outputs, axis=1)


def _make_fallback(ontology: AbstractOWLOntology, fallback: Optional[AbstractOWLReasoner]) -> AbstractOWLReasoner:
    if fallback is not None:
        return fallback
    from owlapy.owl_ontology import Ontology
    from owlapy.owl_reasoner import StructuralReasoner
    from owlapy.owl_reasoner_rdflib import RDFLibReasoner

    if isinstance(ontology, Ontology):
        return StructuralReasoner(ontology)
    return RDFLibReasoner(ontology)


class NIRReasoner(AbstractOWLReasoner):
    """Neural instance retriever as an :class:`~owlapy.abstracts.AbstractOWLReasoner`.

    Args:
        ontology: Ontology whose named individuals are scored.
        model_path: Directory of a pretrained NIR encoder (``config.json`` + weights + tokenizer).
        embeddings_path: Path to ``*entity_embeddings.csv``, or a dataset / embeddings directory.
            Composite also loads a sibling ``*relation_embeddings.csv`` when present.
        dataset_dir: Alternative to ``embeddings_path``: a NIR dataset folder (``kb/``, ``embeddings/``).
        th: Membership threshold (paper default 0.5).
        chunksize: Individuals scored per forward pass.
        symbolic_max_length: Concepts of this length or shorter are answered by the fallback
            symbolic reasoner. Encoders were trained on longer expressions; named classes
            (length 1) should stay symbolic.
        model: Optional architecture name (``transformer`` / ``lstm`` / ``gru`` / ``composite``).
            Inferred from ``config.json`` when omitted.
        device: Torch device. Defaults to CUDA when available.
        fallback_reasoner: Optional TBox reasoner. Defaults to StructuralReasoner / RDFLibReasoner.
    """

    def __init__(
        self,
        ontology: Union[AbstractOWLOntology, str],
        *,
        model_path: str,
        embeddings_path: Optional[str] = None,
        dataset_dir: Optional[str] = None,
        th: float = 0.5,
        chunksize: int = 1024,
        symbolic_max_length: int = 1,
        model: Optional[str] = None,
        device: Optional[str] = None,
        fallback_reasoner: Optional[AbstractOWLReasoner] = None,
    ):
        import numpy as np
        import torch

        if isinstance(ontology, str):
            from owlapy.iri import IRI
            from owlapy.owl_ontology import Ontology

            if os.path.exists(ontology):
                ontology = Ontology(IRI.create("file://" + os.path.abspath(ontology)))
            else:
                ontology = Ontology(ontology)

        super().__init__(ontology)
        self.ontology = ontology
        self._fallback = _make_fallback(ontology, fallback_reasoner)
        self.th = th
        self.chunksize = chunksize
        self.symbolic_max_length = symbolic_max_length
        self.dls_renderer = DLSyntaxObjectRenderer()
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        if not os.path.isdir(model_path):
            raise FileNotFoundError(f"NIR model directory not found: {model_path}")
        architecture = _resolve_architecture(model_path, model)
        self.model_name = architecture
        self._encoder, self.tokenizer = _register_and_load(model_path, architecture, self.device)

        embeddings, entity_csv = _load_entity_embeddings(embeddings_path, dataset_dir)
        self._is_composite = type(self._encoder).__name__ == "NIRComposite"
        if self._is_composite:
            embeddings = _merge_relation_embeddings(embeddings, entity_csv, embeddings_path, dataset_dir)
            embeddings = _mean_pool_named_class_embeddings(embeddings, ontology, self._fallback)
        self._embeddings = embeddings
        self._short_to_ind: Dict[str, OWLNamedIndividual] = {}
        scored_shorts: List[str] = []
        for ind in ontology.individuals_in_signature():
            short = _short_name(ind.str)
            self._short_to_ind[short] = ind
            if short in embeddings.index:
                scored_shorts.append(short)
        if not scored_shorts:
            raise RuntimeError(
                "No overlapping individuals between the ontology signature and the embedding index."
            )
        self.all_individuals_arr = np.array(sorted(set(scored_shorts)), dtype=object)
        self.all_ind_embs = torch.as_tensor(
            np.ascontiguousarray(embeddings.loc[self.all_individuals_arr].values, dtype=np.float32),
            device=self.device,
        )
        if self._is_composite and "⊤" not in embeddings.index:
            embeddings.loc["⊤"] = embeddings.loc[self.all_individuals_arr].mean(axis=0)
            self._embeddings = embeddings
        self.reset_retrieval_stats()

    def reset_retrieval_stats(self) -> None:
        self.n_retrieval_calls = 0
        self.n_nir_calls = 0
        self.n_symbolic_calls = 0
        self.n_cache_hits = 0
        self.queried_lengths: List[int] = []
        self._score_cache: Dict[str, object] = {}
        self._symbolic_cache: Dict[str, FrozenSet[OWLNamedIndividual]] = {}

    def retrieval_stats(self) -> dict:
        lengths = self.queried_lengths
        return {
            "n_retrieval_calls": self.n_retrieval_calls,
            "n_nir_calls": self.n_nir_calls,
            "n_pellet_calls": self.n_symbolic_calls,
            "n_symbolic_calls": self.n_symbolic_calls,
            "n_cache_hits": self.n_cache_hits,
            "n_unique_queries": len(self._score_cache) + len(self._symbolic_cache),
            "mean_query_length": float(sum(lengths) / len(lengths)) if lengths else 0.0,
            "max_query_length": int(max(lengths)) if lengths else 0,
            "symbolic_max_length": self.symbolic_max_length,
        }

    def _render(self, concept: Union[str, OWLClassExpression]) -> str:
        if isinstance(concept, str):
            return concept
        return self.dls_renderer.render(concept)

    def membership_scores(self, expr: Union[str, OWLClassExpression]):
        import numpy as np
        import torch

        if not isinstance(expr, str):
            expr = self._render(expr)
        cached = self._score_cache.get(expr)
        if cached is not None:
            self.n_cache_hits += 1
            return cached
        with torch.no_grad():
            if self._is_composite:
                component_embeddings = _component_embeddings_for_expr(expr, self._embeddings, self.device)
                scores = _score_all_inds_composite(
                    self._encoder,
                    [expr],
                    self.all_ind_embs,
                    [component_embeddings],
                    chunk_size=self.chunksize,
                ).squeeze()
            else:
                scores = _score_all_inds(
                    self._encoder,
                    self.tokenizer,
                    self.all_ind_embs,
                    [expr],
                    hidden_size=self.all_ind_embs.shape[1],
                    chunk_size=self.chunksize,
                ).squeeze()
        scores = np.asarray(scores).reshape(-1)
        self._score_cache[expr] = scores
        return scores

    def _nir_instances(self, expr: str) -> FrozenSet[OWLNamedIndividual]:
        scores = self.membership_scores(expr)
        retrieved_short = self.all_individuals_arr[scores > self.th]
        return frozenset(self._short_to_ind[s] for s in retrieved_short if s in self._short_to_ind)

    def instances(
        self, ce: OWLClassExpression, direct: bool = False, timeout: int = 1000
    ) -> Iterable[OWLNamedIndividual]:
        if ce is None or (hasattr(ce, "is_owl_thing") and ce.is_owl_thing()) or ce is OWLThing:
            yield from self.ontology.individuals_in_signature()
            return
        if ce is OWLNothing or (hasattr(ce, "is_owl_nothing") and ce.is_owl_nothing()):
            return

        try:
            length = get_expression_length(ce)
        except Exception:
            length = 0
        expr = self._render(ce)
        self.n_retrieval_calls += 1
        self.queried_lengths.append(length)

        if 0 < length <= self.symbolic_max_length:
            cached = self._symbolic_cache.get(expr)
            if cached is not None:
                self.n_cache_hits += 1
                self.n_symbolic_calls += 1
                yield from cached
                return
            result = frozenset(self._fallback.instances(ce, direct=direct, timeout=timeout))
            self._symbolic_cache[expr] = result
            self.n_symbolic_calls += 1
            yield from result
            return

        self.n_nir_calls += 1
        yield from self._nir_instances(expr)

    def get_root_ontology(self) -> AbstractOWLOntology:
        return self.ontology

    def __str__(self) -> str:
        return (
            f"NIRReasoner(model={self.model_name}, th={self.th}, "
            f"symbolic_max_length={self.symbolic_max_length})"
        )

    # --- TBox / ABox delegated to the symbolic fallback ---------------------------------

    def data_property_domains(self, pe: OWLDataProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        return self._fallback.data_property_domains(pe, direct)

    def object_property_domains(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        return self._fallback.object_property_domains(pe, direct)

    def object_property_ranges(self, pe: OWLObjectProperty, direct: bool = False) -> Iterable[OWLClassExpression]:
        return self._fallback.object_property_ranges(pe, direct)

    def equivalent_classes(self, ce: OWLClassExpression, *args, **kwargs) -> Iterable[OWLClassExpression]:
        return self._fallback.equivalent_classes(ce, *args, **kwargs)

    def disjoint_classes(self, ce: OWLClassExpression, *args, **kwargs) -> Iterable[OWLClassExpression]:
        return self._fallback.disjoint_classes(ce, *args, **kwargs)

    def different_individuals(self, ind: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        return self._fallback.different_individuals(ind)

    def same_individuals(self, ind: OWLNamedIndividual) -> Iterable[OWLNamedIndividual]:
        return self._fallback.same_individuals(ind)

    def equivalent_object_properties(self, op: OWLObjectPropertyExpression) -> Iterable[OWLObjectPropertyExpression]:
        return self._fallback.equivalent_object_properties(op)

    def equivalent_data_properties(self, dp: OWLDataProperty) -> Iterable[OWLDataProperty]:
        return self._fallback.equivalent_data_properties(dp)

    def data_property_values(self, e: OWLEntity, pe: OWLDataProperty, *args, **kwargs) -> Iterable[OWLLiteral]:
        return self._fallback.data_property_values(e, pe, *args, **kwargs)

    def object_property_values(
        self, ind: OWLNamedIndividual, pe: OWLObjectPropertyExpression, *args, **kwargs
    ) -> Iterable[OWLNamedIndividual]:
        return self._fallback.object_property_values(ind, pe, *args, **kwargs)

    def sub_classes(self, ce: OWLClassExpression, direct: bool = False, *args, **kwargs) -> Iterable[OWLClassExpression]:
        return self._fallback.sub_classes(ce, direct, *args, **kwargs)

    def super_classes(self, ce: OWLClassExpression, direct: bool = False, *args, **kwargs) -> Iterable[OWLClassExpression]:
        return self._fallback.super_classes(ce, direct, *args, **kwargs)

    def disjoint_object_properties(self, op: OWLObjectPropertyExpression, *args, **kwargs) -> Iterable[OWLObjectPropertyExpression]:
        return self._fallback.disjoint_object_properties(op, *args, **kwargs)

    def disjoint_data_properties(self, dp: OWLDataProperty, *args, **kwargs) -> Iterable[OWLDataProperty]:
        return self._fallback.disjoint_data_properties(dp, *args, **kwargs)

    def sub_data_properties(self, dp: OWLDataProperty, direct: bool = False, *args, **kwargs) -> Iterable[OWLDataProperty]:
        return self._fallback.sub_data_properties(dp, direct, *args, **kwargs)

    def super_data_properties(self, dp: OWLDataProperty, direct: bool = False, *args, **kwargs) -> Iterable[OWLDataProperty]:
        return self._fallback.super_data_properties(dp, direct, *args, **kwargs)

    def sub_object_properties(
        self, op: OWLObjectPropertyExpression, direct: bool = False, *args, **kwargs
    ) -> Iterable[OWLObjectPropertyExpression]:
        return self._fallback.sub_object_properties(op, direct, *args, **kwargs)

    def super_object_properties(
        self, op: OWLObjectPropertyExpression, direct: bool = False, *args, **kwargs
    ) -> Iterable[OWLObjectPropertyExpression]:
        return self._fallback.super_object_properties(op, direct, *args, **kwargs)

    def types(self, ind: OWLNamedIndividual, direct: bool = False) -> Iterable:
        return self._fallback.types(ind, direct)

    def data_property_ranges(self, pe: OWLDataProperty, direct: bool = False) -> Iterable[OWLDataRange]:
        return self._fallback.data_property_ranges(pe, direct)
