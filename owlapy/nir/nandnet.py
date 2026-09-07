"""Neural operators used by :class:`~owlapy.nir.composite.NIRComposite`."""

import torch
import torch.nn as nn
from transformers import PreTrainedModel

from owlapy.nir.config import NIRConfig


class NAND(PreTrainedModel):
    config_class = NIRConfig

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.linear1 = nn.Linear(config.input_size, config.individual_size)
        self.linear2 = nn.Linear(config.individual_size, config.individual_size)
        self.head = nn.Linear(config.individual_size * 2, config.output_size)
        self.activation = nn.ReLU()

    def encode(self, C, D):
        x1 = self.activation(self.linear1(C))
        x2 = self.activation(self.linear1(D))
        x = self.activation(self.linear2(x1 + x2))
        return x

    def forward(self, C, D, individual):
        x = self.encode(C, D)
        if x.ndim == 1:
            x = x.unsqueeze(0)
        if individual.ndim == 1:
            individual = individual.unsqueeze(0)
        x = torch.cat((x.repeat(individual.shape[0], 1), individual), dim=-1)
        x = torch.sigmoid(self.head(x))
        return x.squeeze()


class Le(PreTrainedModel):
    config_class = NIRConfig

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.linear1 = nn.Linear(config.input_size, config.individual_size)
        self.linear2 = nn.Linear(config.input_size, config.individual_size)
        self.linear3 = nn.Linear(config.individual_size * 2, config.individual_size)
        self.head = nn.Linear(config.individual_size * 2, config.output_size)
        self.activation = nn.ReLU()

    def encode(self, r, C):
        x1 = self.activation(self.linear1(C))
        x2 = self.activation(self.linear2(r))
        if x1.ndim < x2.ndim:
            x1 = x1.unsqueeze(0)
        if x2.ndim < x1.ndim:
            x2 = x2.unsqueeze(0)
        x = self.activation(self.linear3(torch.cat((x1, x2), dim=-1)))
        return x

    def forward(self, n, r, C, individual):
        x = self.encode(r, C)
        if x.ndim == 1:
            x = x.unsqueeze(0)
        if individual.ndim == 1:
            individual = individual.unsqueeze(0)
        x = torch.cat((x.repeat(individual.shape[0], 1), individual), dim=-1)
        x = torch.sigmoid(torch.sigmoid(n) + self.head(x))
        return x


class Inverse(PreTrainedModel):
    config_class = NIRConfig

    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.linear1 = nn.Linear(config.input_size, config.individual_size)
        self.linear2 = nn.Linear(config.individual_size, config.individual_size)
        self.linear3 = nn.Linear(config.individual_size, config.individual_size)
        self.head = nn.Linear(config.individual_size, config.input_size)
        self.activation = nn.ReLU()

    def encode(self, r):
        x1 = self.activation(self.linear1(r))
        x2 = self.activation(self.linear2(x1))
        x3 = self.activation(self.linear3(x2))
        return torch.tanh(self.head(x3))

    def forward(self, r):
        return self.encode(r)


class Self(PreTrainedModel):
    def __init__(self, config):
        super().__init__(config)
        self.config = config
        self.linear1 = nn.Linear(config.individual_size, config.individual_size)
        self.head = nn.Linear(config.individual_size, config.output_size)
        self.activation = nn.ReLU()

    def forward(self, individual):
        x = self.activation(self.linear1(individual))
        return torch.sigmoid(self.head(x))
