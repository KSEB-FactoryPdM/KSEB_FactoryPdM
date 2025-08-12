from __future__ import annotations

from typing import List, Union

import torch
import torch.nn as nn


def _mlp(sizes: List[int], last_act: bool = True) -> nn.Sequential:
    layers: List[nn.Module] = []
    for i in range(len(sizes) - 1):
        layers.append(nn.Linear(sizes[i], sizes[i + 1]))
        if i < len(sizes) - 2 or last_act:
            layers.append(nn.ReLU())
    return nn.Sequential(*layers)


class AE(nn.Module):
    """
    다층 MLP AutoEncoder
    - hidden: int 또는 List[int]
    - latent_dim: int
    """

    def __init__(self, input_dim: int, hidden: Union[int, List[int]], latent_dim: int) -> None:
        super().__init__()
        if isinstance(hidden, int):
            enc_sizes = [input_dim, hidden, latent_dim]
            dec_sizes = [latent_dim, hidden, input_dim]
        else:
            enc_sizes = [input_dim, *hidden, latent_dim]
            dec_hidden = list(reversed(hidden))
            dec_sizes = [latent_dim, *dec_hidden, input_dim]

        # latent 앞은 ReLU, latent층/출력층은 Linear
        self.enc = _mlp(enc_sizes, last_act=False)
        self.dec = _mlp(dec_sizes, last_act=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # type: ignore[override]
        z = self.enc(x)
        xh = self.dec(z)
        return xh

    @torch.no_grad()
    def encode(self, x: torch.Tensor) -> torch.Tensor:
        return self.enc(x)


