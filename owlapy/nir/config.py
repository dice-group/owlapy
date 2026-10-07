"""HuggingFace config for NIR encoders."""

from transformers import PretrainedConfig


class NIRConfig(PretrainedConfig):
    model_type = "nir"

    def __init__(
        self,
        num_attention_heads=4,
        num_encoder_layers=3,
        num_rnn_layers=3,
        embedding_dim=256,
        pe_dropout=0.1,
        max_length=128,
        vocab_size=512,
        **kwargs,
    ):
        super().__init__(**kwargs)
        import torch

        self.num_attention_heads = num_attention_heads
        self.num_encoder_layers = num_encoder_layers
        self.num_rnn_layers = num_rnn_layers
        self.embedding_dim = embedding_dim
        self.pe_dropout = pe_dropout
        self.max_length = max_length
        self.vocab_size = vocab_size
        self.pad_token_id = 0
        self.input_size = embedding_dim
        self.individual_size = embedding_dim
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.output_size = 1
        self.batch_training = True
        self.hidden_size = 128
