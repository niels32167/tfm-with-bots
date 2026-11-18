"""A position as numpy arrays (`Position`), and positions stacked into a batch (`stack`): what the Imitation Model reads,
in training and in play. It imports nothing that reads the dataset or the engine, so the Imitation Bot, a
Controller, can use it."""

from dataclasses import dataclass
from typing import Any

import numpy as np

from ai.encoding import CARD_FIELDS, OPTION_FIELDS, encode


@dataclass(frozen=True, eq=False)
class Position:
    """One training Decision, encoded (ai.encoding) as numpy arrays, with the Option the Player picked and what
    evaluation reports it by."""

    game: str
    player: int
    kind: str
    generation: int
    rating: int
    source: str
    globals: np.ndarray
    missing: np.ndarray
    cards: np.ndarray
    areas: np.ndarray
    options: np.ndarray
    picked: int
    # What the Card Economy Bot picks, if asked for and the view holds the hand its Prices read.
    card_economy_pick: int | None = None

    @classmethod
    def of(
        cls,
        view: dict[str, Any],
        decision: dict[str, Any],
        *,
        game: str = "",
        rating: int = 0,
        source: str = "play",
        picked: int = 0,
        card_economy_pick: int | None = None,
    ) -> Position:
        """The position `view` shows its viewer, who answers `decision`, encoded (ai.encoding). In play there is no
        Game id, rating or pick to note, so those keep their defaults."""
        encoding = encode(view, decision)
        return cls(
            game=game,
            player=view["viewer"],
            kind=decision["kind"],
            generation=view["generation"],
            rating=rating,
            source=source,
            globals=np.asarray(encoding.globals, dtype=np.float32),
            missing=np.asarray(encoding.missing, dtype=np.float32),
            cards=np.asarray(encoding.cards, dtype=np.float32).reshape(-1, len(CARD_FIELDS)),
            areas=np.asarray(encoding.areas, dtype=np.float32),
            options=np.asarray(encoding.options, dtype=np.float32),
            picked=picked,
            card_economy_pick=card_economy_pick,
        )


def padded(tables: list[np.ndarray], width: int) -> tuple[np.ndarray, np.ndarray]:
    """`tables` (one per position) stacked into one array padded with zeros, and where rows are real."""
    most = max(len(table) for table in tables)
    stacked = np.zeros((len(tables), most, width), dtype=np.float32)
    real = np.zeros((len(tables), most), dtype=bool)
    for number, table in enumerate(tables):
        stacked[number, : len(table)] = table
        real[number, : len(table)] = True
    return stacked, real


def stack(found: list[Position]) -> dict[str, np.ndarray]:
    """Positions as one array per table, padded to the most card rows and Options among them: "card_mask" and
    "option_mask" are True where a row is real, and "picked" holds the Option each Player picked."""
    cards, card_mask = padded([position.cards for position in found], len(CARD_FIELDS))
    options, option_mask = padded([position.options for position in found], len(OPTION_FIELDS))
    return {
        "globals": np.stack([position.globals for position in found]),
        "missing": np.stack([position.missing for position in found]),
        "cards": cards,
        "card_mask": card_mask,
        "areas": np.stack([position.areas for position in found]),
        "options": options,
        "option_mask": option_mask,
        "picked": np.asarray([position.picked for position in found], dtype=np.int64),
    }
