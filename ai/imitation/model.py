"""The Imitation Model: it scores each Option of a Decision given the position (ADR 0002), and the Option with the
highest score is its prediction of what a strong Player picks.

A position is a set of tokens, read by a small transformer:
- one for the global row and its missing flags, and one for the board (every Area's row);
- one per card row: a learned identity for the card, its printed facts (`card_table()`), its zone and its other
  numbers, so that the model can learn which cards go well together;
- one per Option: its type, the cards it names (the same identity and printed facts) and its other numbers.
Each Option's token gives its score. Numbers enter as sign(x)·log(1 + |x|), which keeps MegaCredits, Prices and
counts in one range without statistics from the data.

Saved models hold the encoding's `format_stamp()` and refuse to load under another format (`load_model`).
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn

from ai.encoding import (
    AREA_FIELDS,
    CARD_FACTS,
    CARD_FIELDS,
    GLOBAL_FIELDS,
    OPTION_FIELDS,
    OPTION_TYPES,
    ZONES,
    areas,
    card_table,
    check_format,
    format_stamp,
)
from ai.imitation.encoded import Position, stack

CARD_COLUMN = CARD_FIELDS.index("card")
ZONE_COLUMN = CARD_FIELDS.index("zone")
OPTION_TYPE_COLUMN = OPTION_FIELDS.index("type")
OPTION_CARD_COLUMNS = (OPTION_FIELDS.index("card"), OPTION_FIELDS.index("other_card"))
# The token kinds, which the model tells apart.
TOKEN_KINDS = (GLOBAL_TOKEN, BOARD_TOKEN, CARD_TOKEN, OPTION_TOKEN) = range(4)


@dataclass(frozen=True)
class ModelShape:
    """How big the model is: tokens of `width` numbers, `layers` transformer layers with `heads` heads each."""

    width: int = 128
    layers: int = 4
    heads: int = 4


@dataclass
class Batch:
    """Positions padded to the most card rows and Options among them: `card_mask` and `option_mask` are True where
    a row is real. `picked` is the Option each Player picked."""

    globals: torch.Tensor
    missing: torch.Tensor
    cards: torch.Tensor
    card_mask: torch.Tensor
    areas: torch.Tensor
    options: torch.Tensor
    option_mask: torch.Tensor
    picked: torch.Tensor

    def to(self, device: torch.device | str) -> Batch:
        return Batch(**{name: tensor.to(device, non_blocking=True) for name, tensor in vars(self).items()})


def collate(found: list[Position]) -> Batch:
    """A Batch of positions, on the CPU."""
    return batch_of(stack(found))


def batch_of(stacked: dict[str, np.ndarray]) -> Batch:
    """A Batch of positions stacked by ai.imitation.positions.stack, on the CPU."""
    return Batch(**{name: torch.from_numpy(array) for name, array in stacked.items()})


def squashed(numbers: torch.Tensor) -> torch.Tensor:
    return torch.sign(numbers) * torch.log1p(numbers.abs())


class ImitationModel(nn.Module):
    """Scores for each Option of each position in a Batch: -inf for padding."""

    def __init__(self, shape: ModelShape) -> None:
        super().__init__()
        self.shape = shape
        width = shape.width
        self.register_buffer("card_facts", squashed(torch.tensor(card_table(), dtype=torch.float32)))
        self.card_identity = nn.Embedding(len(card_table()), width)
        self.printed = nn.Linear(len(CARD_FACTS), width)
        self.zone = nn.Embedding(len(ZONES), width)
        self.card_numbers = nn.Linear(len(CARD_FIELDS), width)
        self.option_type = nn.Embedding(len(OPTION_TYPES), width)
        self.option_numbers = nn.Linear(len(OPTION_FIELDS), width)
        self.global_numbers = nn.Linear(2 * len(GLOBAL_FIELDS), width)
        self.board = nn.Linear(len(areas()) * len(AREA_FIELDS), width)
        self.token_kind = nn.Embedding(len(TOKEN_KINDS), width)
        layer = nn.TransformerEncoderLayer(
            width, shape.heads, dim_feedforward=2 * width, dropout=0.0, batch_first=True, norm_first=True
        )
        self.transformer = nn.TransformerEncoder(layer, shape.layers, enable_nested_tensor=False)
        self.out = nn.Sequential(nn.LayerNorm(width), nn.Linear(width, 1))

    def card(self, numbers: torch.Tensor) -> torch.Tensor:
        """What a card number gives a token: its learned identity and its printed facts."""
        numbers = numbers.long()
        return self.card_identity(numbers) + self.printed(self.card_facts[numbers])

    def forward(self, batch: Batch) -> torch.Tensor:
        cards = batch.cards
        card_tokens = (
            self.card(cards[..., CARD_COLUMN])
            + self.zone(cards[..., ZONE_COLUMN].long())
            + self.card_numbers(squashed(cards))
            + self.token_kind.weight[CARD_TOKEN]
        )
        options = batch.options
        option_tokens = (
            self.option_type(options[..., OPTION_TYPE_COLUMN].long())
            + sum(self.card(options[..., column]) for column in OPTION_CARD_COLUMNS)
            + self.option_numbers(squashed(options))
            + self.token_kind.weight[OPTION_TOKEN]
        )
        global_token = self.global_numbers(torch.cat([squashed(batch.globals), batch.missing], dim=1))
        board_token = self.board(squashed(batch.areas).flatten(1))
        tokens = torch.cat(
            [
                (global_token + self.token_kind.weight[GLOBAL_TOKEN]).unsqueeze(1),
                (board_token + self.token_kind.weight[BOARD_TOKEN]).unsqueeze(1),
                card_tokens,
                option_tokens,
            ],
            dim=1,
        )
        always = torch.ones(len(cards), 2, dtype=torch.bool, device=cards.device)
        real = torch.cat([always, batch.card_mask, batch.option_mask], dim=1)
        read = self.transformer(tokens, src_key_padding_mask=~real)
        scores = self.out(read[:, -options.shape[1] :]).squeeze(-1).float()
        return scores.masked_fill(~batch.option_mask, float("-inf"))


def scored(model: ImitationModel, batch: Batch, device: str) -> torch.Tensor:
    """The model's scores for `batch`, already on `device`: in bfloat16 on a GPU, which is about twice as fast."""
    with torch.autocast(device_type=device.split(":")[0], dtype=torch.bfloat16, enabled=device.startswith("cuda")):
        return model(batch)


def save_model(path: Path, model: ImitationModel, saved: dict[str, Any]) -> None:
    """Saves `model` with the encoding format, its shape, and `saved` (the settings it was trained with, and the
    like), written whole or not at all."""
    path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "format": format_stamp(),
        "shape": asdict(model.shape),
        "weights": model.state_dict(),
        "saved": saved,
    }
    partial = path.with_suffix(".partial")
    torch.save(checkpoint, partial)
    partial.replace(path)


def load_model(path: Path, device: torch.device | str = "cpu") -> tuple[ImitationModel, dict[str, Any]]:
    """A saved model, ready to score, and what was saved with it. Refuses one saved under another encoding format
    (ai.encoding.FormatMismatch)."""
    checkpoint = torch.load(path, map_location=device, weights_only=True)
    check_format(checkpoint["format"])
    model = ImitationModel(ModelShape(**checkpoint["shape"])).to(device)
    model.load_state_dict(checkpoint["weights"])
    return model.eval(), checkpoint["saved"]
