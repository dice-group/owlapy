"""Inference-only NIR encoders used by :class:`~owlapy.owl_reasoner.NIRReasoner`.

Architectures match the pretrained HuggingFace checkpoints from
https://github.com/fosterreproducibleresearch/NIR
(Transformer / LSTM / GRU / Composite).
``torch`` and ``transformers`` are imported when the classes are loaded.
"""

from owlapy.nir.composite import NIRComposite
from owlapy.nir.config import NIRConfig
from owlapy.nir.models import NIRGRU, NIRLSTM, NIRTransformer

__all__ = ["NIRConfig", "NIRTransformer", "NIRLSTM", "NIRGRU", "NIRComposite"]
