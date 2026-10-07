"""NIR encoder architectures (inference). Weight-compatible with the original NIR checkpoints."""

from __future__ import annotations

import math

import torch
import torch.nn as nn
from torch import Tensor
from transformers import PreTrainedModel

from owlapy.nir.config import NIRConfig


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding used by :class:`NIRTransformer`."""

    def __init__(self, d_model: int, dropout: float = 0.1, max_length: int = 128):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        position = torch.arange(max_length).unsqueeze(0)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        pe = torch.zeros(1, max_length, d_model)
        pe[0, :, 0::2] = torch.sin(position * div_term)
        pe[0, :, 1::2] = torch.cos(position * div_term)
        self.register_buffer("pe", pe)

    def forward(self, x: Tensor) -> Tensor:
        x = x + self.pe[: x.size(1)]
        return self.dropout(x)


class NIRTransformer(PreTrainedModel):
    config_class = NIRConfig
    _tied_weights_keys = {}

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.loss_fn = nn.BCELoss()
        self.max_length = config.max_length
        self.embedding = nn.Sequential(
            nn.Embedding(config.vocab_size, config.embedding_dim, padding_idx=self.config.pad_token_id),
            PositionalEncoding(d_model=config.embedding_dim, dropout=config.pe_dropout, max_length=config.max_length),
        )
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.embedding_dim, nhead=config.num_attention_heads, dim_feedforward=256, batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=config.num_encoder_layers)
        self.fc = nn.Sequential(
            nn.Linear(2 * config.embedding_dim, config.embedding_dim),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(config.embedding_dim, 1),
        )
        self.activation = nn.Sigmoid()
        self.post_init()

    def forward(self, input_ids, attention_mask, label_features, labels=None):
        embeddings = self.embedding(input_ids)
        transformer_output = self.encoder(embeddings).mean(1)
        n = label_features.shape[0]
        n_repeats = n // transformer_output.shape[0]
        transformer_output = torch.repeat_interleave(transformer_output, repeats=n_repeats, dim=0)
        final_representation = torch.cat((transformer_output, label_features), dim=1)
        logits = self.fc(final_representation)
        probabilities = self.activation(logits).squeeze()
        if labels is not None:
            loss = self.loss_fn(probabilities, labels)
            return probabilities, loss
        return probabilities


class NIRLSTM(PreTrainedModel):
    config_class = NIRConfig
    _tied_weights_keys = {}

    def __init__(self, config, batch_training=True):
        super().__init__(config)
        self.config = config
        self.batch_training = batch_training
        self.loss_fn = nn.BCELoss()
        self.max_length = config.max_length
        self.embedding = nn.Embedding(config.vocab_size, config.individual_size, padding_idx=self.config.pad_token_id)
        self.lstm = nn.LSTM(
            input_size=config.individual_size,
            hidden_size=config.hidden_size,
            num_layers=config.num_rnn_layers,
            batch_first=True,
        )
        self.fc = nn.Sequential(
            nn.Linear(config.hidden_size + config.individual_size, config.hidden_size),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(config.hidden_size, config.output_size),
        )
        self.sigmoid = nn.Sigmoid()
        self.post_init()

    def forward(self, input_ids, attention_mask, label_features, labels=None, mask=None):
        individual_embeddings = label_features
        embeddings = self.embedding(input_ids)
        seq, _ = self.lstm(embeddings)
        final_hidden_state = seq.mean(1)
        if self.batch_training:
            batch_size = final_hidden_state.shape[0]
            n = individual_embeddings.shape[0]
            n_repeats = n // batch_size
            final_hidden_state = torch.repeat_interleave(final_hidden_state, repeats=n_repeats, dim=0)
            combined = torch.cat((final_hidden_state, individual_embeddings), dim=1)
            if mask is not None:
                mask = mask.to(self.config.device)
                inverted_mask = ~mask
                combined = combined.masked_fill(inverted_mask.unsqueeze(2), -1e9)
        else:
            n = individual_embeddings.shape[0]
            final_hidden_state = final_hidden_state.expand(n, -1)
            combined = torch.cat((final_hidden_state, individual_embeddings), dim=1)
        output = self.fc(combined)
        probabilities = self.sigmoid(output)
        if labels is not None:
            probabilities = probabilities.squeeze() if n > 1 else probabilities.squeeze(0)
            if self.batch_training and batch_size == 1:
                labels = labels.squeeze()
            if self.batch_training and mask is not None:
                probabilities = probabilities.masked_select(mask)
                labels = labels.masked_select(mask)
            loss = self.loss_fn(probabilities, labels)
            return probabilities, loss
        return probabilities


class NIRGRU(PreTrainedModel):
    config_class = NIRConfig
    _tied_weights_keys = {}

    def __init__(self, config, batch_training=True):
        super().__init__(config)
        self.config = config
        self.batch_training = batch_training
        self.loss_fn = nn.BCELoss()
        self.max_length = config.max_length
        self.embedding = nn.Embedding(config.vocab_size, config.individual_size, padding_idx=self.config.pad_token_id)
        self.gru = nn.GRU(
            input_size=config.individual_size,
            hidden_size=config.hidden_size,
            num_layers=config.num_rnn_layers,
            batch_first=True,
        )
        self.fc = nn.Sequential(
            nn.Linear(config.hidden_size + config.individual_size, config.hidden_size),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(config.hidden_size, config.output_size),
        )
        self.sigmoid = nn.Sigmoid()
        self.post_init()

    def forward(self, input_ids, attention_mask, label_features, labels=None, mask=None):
        individual_embeddings = label_features
        embeddings = self.embedding(input_ids)
        seq, _ = self.gru(embeddings)
        final_hidden_state = seq.mean(1)
        if self.batch_training:
            batch_size = final_hidden_state.shape[0]
            n = individual_embeddings.shape[0]
            n_repeats = n // batch_size
            final_hidden_state = torch.repeat_interleave(final_hidden_state, repeats=n_repeats, dim=0)
            combined = torch.cat((final_hidden_state, individual_embeddings), dim=1)
            if mask is not None:
                mask = mask.to(self.config.device)
                inverted_mask = ~mask
                combined = combined.masked_fill(inverted_mask.unsqueeze(2), -1e9)
        else:
            n = individual_embeddings.shape[0]
            final_hidden_state = final_hidden_state.expand(n, -1)
            combined = torch.cat((final_hidden_state, individual_embeddings), dim=1)
        output = self.fc(combined)
        probabilities = self.sigmoid(output)
        if labels is not None:
            probabilities = probabilities.squeeze() if n > 1 else probabilities.squeeze(0)
            if self.batch_training and batch_size == 1:
                labels = labels.squeeze()
            if self.batch_training and mask is not None:
                probabilities = probabilities.masked_select(mask)
                labels = labels.masked_select(mask)
            loss = self.loss_fn(probabilities, labels)
            return probabilities, loss
        return probabilities
