import re

import torch
import torch.nn as nn
from transformers import PreTrainedModel

from owlapy.nir.config import NIRConfig
from owlapy.nir.nandnet import NAND, Inverse, Le, Self


class NIRComposite(PreTrainedModel):
    config_class = NIRConfig
    _tied_weights_keys = {}
    def __init__(self, config):
        #input_size, individual_size, device,
        super().__init__(config)
        self.config = config
        self.loss_fn = nn.BCELoss()
        self.input_size = self.config.input_size
        self.individual_size = self.config.individual_size
        self.NAND = NAND(config)
        self.Le = Le(config)
        self.Self = Self(config)
        self.Inverse = Inverse(config)
        self.loss_fn = nn.BCELoss()
        self.batch_training = config.batch_training
        self.projection_layer = nn.Linear(self.input_size * 2, self.input_size)
        self.head = nn.Linear(self.input_size, self.config.output_size)
        self.activation = nn.Tanh()
        self.post_init()

    @staticmethod
    def find_innermost_parentheses(expr):
        innermost_pattern = re.compile(r'\(([^()]+)\)')
        match = innermost_pattern.search(expr)
        return match.group(1) if match else None

    def process_negation(self, C, component_embeddings_dict, encodings, encodings_mapping,
                         individual=None, score=False):
        C = C.replace('¬', '').strip()
        if C in encodings_mapping:
            C = encodings_mapping[C]
            C = encodings[C]
        else:
            C = component_embeddings_dict.get(C)

        if score:
            C = self.NAND(C, C, individual)
        else:
            C = self.NAND.encode(C, C)

        return C

    def get_expression_embedding(self, innermost, component_embeddings_dict, encodings,
                                 encodings_mapping):
        # TODO:
        if '¬' in innermost:
            return self.process_negation(innermost, component_embeddings_dict, encodings,
                                         encodings_mapping)
        elif ' ⊓ ' in innermost:
            parts = innermost.split(' ⊓ ')

            C = parts[0].strip()

            C = self.process_negation(C, component_embeddings_dict, encodings,
                                      encodings_mapping) if '¬' in C else encodings.get(
                encodings_mapping.get(C, ''), component_embeddings_dict.get(C))

            for i in range(1, len(parts)):
                D = parts[i].strip()
                D = self.process_negation(D, component_embeddings_dict, encodings,
                                          encodings_mapping) if '¬' in D else encodings.get(
                    encodings_mapping.get(D, ''), component_embeddings_dict.get(D))
                C = self.NAND.encode(C, D)
                C = self.NAND.encode(C, C)

            return C

        elif ' ⊔ ' in innermost:
            parts = innermost.split(' ⊔ ')
            C = parts[0].strip()
            if '¬' in C:
                C = encodings.get(encodings_mapping.get(C.replace('¬', '').strip(), ''),
                                  component_embeddings_dict.get(C))
            else:
                C = self.process_negation('¬ ' + C, component_embeddings_dict, encodings,
                                          encodings_mapping)

            for i in range(1, len(parts)):
                D = parts[i].strip()
                if '¬' in D:
                    D = encodings.get(encodings_mapping.get(D.replace('¬', '').strip(), ''),
                                      component_embeddings_dict.get(D))
                else:
                    D = self.process_negation('¬ ' + D, component_embeddings_dict, encodings,
                                              encodings_mapping)

                C = self.NAND.encode(C, D)

            return C

        elif '≤' in innermost and '∃' not in innermost:
            innermost = innermost.replace('≤ ', '')
            parts = innermost.split(' ')
            n = int(parts[0])
            parts = parts[1].split('.')
            r, C = parts[0], parts[1]

            # r = self.process_negation(r, component_embeddings_dict, encodings, encodings_mapping) if '¬' in r else encodings.get(encodings_mapping.get(r, ''), component_embeddings_dict.get(r))
            if '⁻' not in r:
                r = encodings.get(encodings_mapping.get(r, ''), component_embeddings_dict.get(r))
            else:
                r = r.replace('⁻', '')
                r = encodings.get(encodings_mapping.get(r, ''), component_embeddings_dict.get(r))
                r = self.Inverse.encode(r)
            C = self.process_negation(C, component_embeddings_dict, encodings,
                                      encodings_mapping) if '¬' in C else encodings.get(
                encodings_mapping.get(C, ''), component_embeddings_dict.get(C))

            return self.Le.encode(r, C)
        elif '≥' in innermost and '∃' not in innermost:
            innermost = innermost.replace('≥ ', '')
            parts = innermost.split(' ')
            n = int(parts[0])
            parts = parts[1].split('.')
            r, C = parts[0], parts[1]

            n = torch.tensor([n - 1]).to(self.config.device)

            # r = self.process_negation(r, component_embeddings_dict, encodings, encodings_mapping) if '¬' in r else encodings.get(encodings_mapping.get(r, ''), component_embeddings_dict.get(r))
            if '⁻' not in r:
                r = encodings.get(encodings_mapping.get(r, ''), component_embeddings_dict.get(r))
            else:
                r = r.replace('⁻', '')
                r = encodings.get(encodings_mapping.get(r, ''), component_embeddings_dict.get(r))
                r = self.Inverse.encode(r)
            C = self.process_negation(C, component_embeddings_dict, encodings,
                                      encodings_mapping) if '¬' in C else encodings.get(
                encodings_mapping.get(C, ''), component_embeddings_dict.get(C))

            C = self.Le.encode(r, C)
            return self.NAND.encode(C, C)
        elif '∀' in innermost:
            innermost = innermost.replace('∀ ', '')
            parts = innermost.split('.')
            r, C = parts[0], parts[1]

            n = 0
            # r = self.process_negation(r, component_embeddings_dict, encodings, encodings_mapping) if '¬' in r else encodings.get(encodings_mapping.get(r, ''), component_embeddings_dict.get(r))
            if '⁻' not in r:
                r = encodings.get(encodings_mapping.get(r, ''), component_embeddings_dict.get(r))
            else:
                r = r.replace('⁻', '')
                r = encodings.get(encodings_mapping.get(r, ''), component_embeddings_dict.get(r))
                r = self.Inverse.encode(r)
            if '⊥' in C:
                C = component_embeddings_dict.get('⊤')
                C = self.NAND.encode(C, C)
            else:
                C = encodings.get(encodings_mapping.get(C, ''), component_embeddings_dict.get(
                    C)) if '¬' in C else self.process_negation('¬ ' + C, component_embeddings_dict,
                                                               encodings, encodings_mapping)
            emb = self.Le.encode(r, C)
            return emb

        elif '∃' in innermost:
            innermost = innermost.replace('∃ ', '')
            parts = innermost.split('.')
            r, C = parts[0], parts[1]

            n = 0
            if re.search(r'\[(≤|≥)\s-?\d+(\.\d+)?\]', innermost):
                constraint = (re.search(r'\[(≤|≥)\s-?\d+(\.\d+)?\]', innermost).group())
                n = constraint.split(' ')[1].replace(']', '')
                n = torch.tensor([float(n)], dtype=torch.float32)
                C = C.split('[')[0].split(':')[1]
                C = component_embeddings_dict[C]
                r = component_embeddings_dict[r]
                r = (r + C) / 2
                T = component_embeddings_dict['⊤']
                if '≤' in innermost:
                    emb = self.Le.encode(r, T)
                    # print(emb)
                    return emb

                elif '≥' in innermost:
                    emb = self.NAND.encode(self.Le.encode(r, T), self.Le.encode(r, T))
                    # print(emb)
                    return emb
            else:
                if '⁻' in r:
                    r = r.replace('⁻', '')
                    r = encodings.get(encodings_mapping.get(r, ''),
                                      component_embeddings_dict.get(r))
                    r = self.Inverse.encode(r)
                else:
                    r = encodings.get(encodings_mapping.get(r, ''),
                                      component_embeddings_dict.get(r))
                if '⊥' in C:
                    C = component_embeddings_dict.get('⊤')
                    C = self.NAND.encode(C, C)
                    emb = self.Le.encode(r, C)
                elif '{True}' in C or '{False}' in C:
                    C = component_embeddings_dict.get('⊤')
                    emb1 = self.Le.encode(r, C)
                    emb2 = self.NAND.encode(emb1, emb1)
                    emb = self.NAND.encode(self.NAND.encode(emb1, emb2),
                                           self.NAND.encode(emb1, emb2))
                else:
                    C = self.process_negation(C, component_embeddings_dict, encodings,
                                              encodings_mapping) if '¬' in C else encodings.get(
                        encodings_mapping.get(C, ''), component_embeddings_dict.get(C))
                    emb = self.Le.encode(r, C)
                return self.NAND.encode(emb, emb)
        elif not re.search(r'[⊔.∃∀⊓¬]', innermost):
            return component_embeddings_dict.get(innermost)
        else:
            print('innermost:', innermost, 'not implemented yet')

    def parse_batch(self, expr_batch, component_embeddings_dict_batch, counter=0, encodings={},
                    encodings_mapping={}):
        expr_embs = []

        for expr, component_embeddings_dict in zip(expr_batch, component_embeddings_dict_batch):
            # local variables for each batch item
            expr = expr.replace("{True}", "⊤").replace("{False}", "⊥")
            expr = expr.replace("{true}", "⊤").replace("{false}", "⊥")
            local_encodings = encodings.copy()
            local_encodings_mapping = encodings_mapping.copy()

            innermost = self.find_innermost_parentheses(expr)
            if innermost:
                enc_parse = self.get_expression_embedding(innermost, component_embeddings_dict,
                                                          local_encodings, local_encodings_mapping)
                local_encodings[innermost] = enc_parse
                replace_with = 'X' + str(counter)
                expr = expr.replace(f'({innermost})', replace_with)
                counter += 1
                local_encodings_mapping[replace_with] = innermost
                expr_emb = self.parse_batch([expr], [component_embeddings_dict], counter,
                                            local_encodings, local_encodings_mapping)
            else:
                expr_emb = self.get_expression_embedding(expr, component_embeddings_dict,
                                                         local_encodings, local_encodings_mapping)

            expr_embs.append(expr_emb.squeeze())
        return torch.stack(expr_embs)

    def parse_single(self, expr, component_embeddings_dict, counter=0, encodings={},
                     encodings_mapping={}):
        expr = expr.replace("{True}", "⊤").replace("{False}", "⊥")
        expr = expr.replace("{true}", "⊤").replace("{false}", "⊥")
        innermost = self.find_innermost_parentheses(expr)
        if innermost:
            enc_parse = self.get_expression_embedding(innermost, component_embeddings_dict,
                                                      encodings, encodings_mapping)
            encodings[innermost] = enc_parse
            replace_with = 'X' + str(counter)
            expr = expr.replace(f'({innermost})', replace_with)
            counter += 1
            encodings_mapping[replace_with] = innermost
            return self.parse_single(expr, component_embeddings_dict, counter, encodings,
                                     encodings_mapping)
        else:
            return self.get_expression_embedding(expr, component_embeddings_dict, encodings,
                                                 encodings_mapping)

    def forward(self, expr, ind_emb, component_embeddings_dict, label=None):
        if self.batch_training:
            x_embs = self.parse_batch(expr, component_embeddings_dict)
            batch_size = len(ind_emb)
            x = []
            for i in range(batch_size):
                current_emb = x_embs[i]
                n = len(ind_emb[i])
                current_emb_expanded = current_emb.unsqueeze(0).expand(n, -1)
                out = torch.cat((current_emb_expanded, ind_emb[i]), dim=-1)
                out = self.activation(self.projection_layer(out))
                out = self.head(out)
                out = torch.sigmoid(out)
                x.append(out.squeeze())
            x = torch.cat(x, dim=0)
        else:
            x = self.parse_single(expr, component_embeddings_dict)
            n = len(ind_emb)
            x_expanded = x.repeat(n, 1)
            out = torch.cat((x_expanded, ind_emb), dim=-1)
            out = self.activation(self.projection_layer(out))
            out = self.head(out)
            out = torch.sigmoid(out)
            x = out.squeeze()
        if label is not None:
            if self.batch_training:
                label = torch.cat(label, dim=0)
            loss = self.loss_fn(x, label)
            return x, loss
        else:
            return x
