"""The Imitation Bot: a Controller that answers every Decision with the Imitation Model, picking the Option it
scores highest (ticket 14 of phase 2). Ticket 13's answered only setup, the Draft and buying cards and left the
rest to the Card Economy Bot; `imitated=DRAFT_AND_BUY` plays like it, to play against.

It reads only its handle's Player View and Decision, encoded as for training (ai.encoding), so it plays fair.
"""

import functools
from pathlib import Path

import torch

import ai.imitation
from ai.card_economy import CardEconomyBot, Explanation, PricedOption
from ai.controller import Handle
from ai.imitation.encoded import Position
from ai.imitation.model import ImitationModel, collate, load_model
from ai.prices import Prices

# The Decisions ticket 13's model was trained on.
DRAFT_AND_BUY = frozenset({"corporation", "prelude_cards", "draft", "buy_cards"})


@functools.cache
def loaded(path: Path) -> ImitationModel:
    """The model saved at `path`, loaded once per process, on the CPU: a pick needs no GPU."""
    torch.set_num_threads(1)
    return load_model(path)[0]


class ImitationBot:
    """Picks with the Imitation Model saved at `path` (by default the registered one, ai.imitation.MODEL): every
    Decision, or only the kinds `imitated`, leaving the rest to the Card Economy Bot."""

    def __init__(self, path: Path | None = None, imitated: frozenset[str] | None = None) -> None:
        self.model = loaded(path or ai.imitation.MODEL)
        self.imitated = imitated
        self.card_economy = CardEconomyBot()

    def answers(self, handle: Handle) -> bool:
        return self.imitated is None or handle.decision["kind"] in self.imitated

    def chances(self, handle: Handle) -> list[float]:
        """For each Option, the model's chance that a strong Player picks it."""
        with torch.no_grad():
            scores = self.model(collate([Position.of(handle.player_view, handle.decision)]))[0]
        return torch.softmax(scores, dim=0).tolist()

    def pick(self, handle: Handle) -> int:
        if len(handle.decision["options"]) == 1:
            return 0
        if not self.answers(handle):
            return self.card_economy.pick(handle)
        chances = self.chances(handle)
        return chances.index(max(chances))

    def explain(self, handle: Handle) -> Explanation:
        """For the Decisions it answers, every Option with the model's chance (in percent) that a strong Player
        picks it, best first; the Card Economy Bot's explanation for the rest."""
        if not self.answers(handle):
            return self.card_economy.explain(handle)
        prices = Prices.of(handle.player_view, handle.player, self.card_economy.weights)
        options = [
            PricedOption(
                option["index"], option["label"], 100 * chance, {"Chance a strong Player picks it (%)": 100 * chance}
            )
            for option, chance in zip(handle.decision["options"], self.chances(handle), strict=True)
        ]
        ranked = sorted(options, key=lambda option: -option.price)
        return Explanation(handle.player, handle.decision["kind"], prices.generations_left, ranked)
