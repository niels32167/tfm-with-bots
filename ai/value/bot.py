"""The Value Bot: a Controller that tries the Options the Imitation Model rates likeliest (`tried` of them) on the
same few Sampled Positions (`samples`), and picks the one after which the Value Model gives its Player the best mean
chance of winning. This is the TD-Gammon recipe (ticket 15 of phase 2): Sampled Positions cost little to make, and the
Game has chance in it.

"After" means once the Decisions that follow from the Option in its Player's chain are answered, as the Imitation Model
rates likeliest: playing a card is rated once it is paid for and its Tile placed. Before that, the Player View hardly
changes (ai.value.encoded.FOLLOW_UPS).

The Imitation Model's policy narrows the Options tried, which the user chose on 2026-11-20: a Payment with 166
Options or an Area with 48 costs no more than a Draft pick, and what was imitated stays the starting point. An
Option that ends the Game is rated by the Player's result. Ties go to the Option the policy rates likelier.

It reads only its handle: its Player View and Decision, and Sampled Positions, the same ones for every Option, so
that Options are compared on equal terms. It imports neither the engine nor Recorded Game code.
"""

import functools
from pathlib import Path
from typing import Any

import torch

import ai.value
from ai.controller import Handle
from ai.imitation.bot import ImitationBot
from ai.imitation.encoded import Position
from ai.imitation.model import load_model
from ai.value.encoded import FOLLOW_UPS, result_of, view_position
from ai.value.model import ValueModel, chances_of_winning

# The Options tried and the Sampled Positions each is tried on, by default: about 30 ms a Decision on one core.
TRIED = 6
SAMPLES = 4
# An Option is tried only if the Imitation Model gives it at least this share of the likeliest Option's chance: 0
# tries all `tried`, 1 only the likeliest, as the Imitation Bot picks. Measured on 2026-11-20 with the first
# warm-started Value Model, 40 Games against the Imitation Bot each: 0 lost all 20 it played, 0.2 scored 47.5% and
# 0.5 scored 70.0% (54.6-81.9%). Where the Imitation Model is sure, the Value Model's error shouldn't overrule it.
SHARE = 0.5
# A guard: the most follow-up Decisions answered after an Option tried (a card's Payment, Tile and target take 3).
MOST_FOLLOW_UPS = 12
# Seeds for the engine are whole numbers below 2^53 (tm_engine.MAX_SEED).
SEEDS = 1 << 53


@functools.cache
def loaded(path: Path) -> tuple[ValueModel, dict[str, Any]]:
    """The Value Model saved at `path` and what was saved with it, loaded once per process, on the CPU."""
    torch.set_num_threads(1)
    return load_model(path, kind=ValueModel)


class ValueBot:
    """Picks with the Value Model saved at `path` (by default the registered one, ai.value.MODEL), narrowed by the
    Imitation Model it was trained beside (saved with it as the setting "policy")."""

    def __init__(
        self, path: Path | None = None, tried: int = TRIED, samples: int = SAMPLES, share: float = SHARE
    ) -> None:
        self.model, saved = loaded(Path(path or ai.value.MODEL))
        self.policy = ImitationBot(Path(saved["settings"]["policy"]))
        self.tried = tried
        self.samples = samples
        self.share = share

    def pick(self, handle: Handle) -> int:
        if len(handle.decision["options"]) == 1:
            return 0
        tried = self.likeliest(handle)
        if len(tried) == 1:
            return tried[0]
        rated = self.rated(handle, tried)
        return max(rated, key=lambda index: rated[index])  # The likeliest first, so it wins a tie.

    def likeliest(self, handle: Handle) -> list[int]:
        """The Options tried: of the `tried` the Imitation Model rates likeliest, those it gives at least `share` of the
        likeliest Option's chance, likeliest first."""
        return narrowed(self.policy.chances(handle), self.tried, self.share)

    def trials(self, handle: Handle, tried: list[int] | None = None) -> list[tuple[int, Any]]:
        """Each Option tried (by default the `likeliest`) on each Sampled Position (a Game), once the Decisions that
        follow from it in its Player's chain (FOLLOW_UPS) are answered as the Imitation Model rates likeliest: by
        Sampled Position, then Option."""
        tried = self.likeliest(handle) if tried is None else tried
        samples = [handle.sample(seed=handle.random.randrange(SEEDS)) for _ in range(self.samples)]
        trials = []
        for sample in samples:
            for index in tried:
                after = sample.copy()
                after.pick(index)
                trials.append((index, after))
        for _ in range(MOST_FOLLOW_UPS):
            waiting = [after for _, after in trials if follows_up(after.decision, handle.player)]
            if not waiting:
                break
            positions = [Position.of(after.player_view(handle.player), after.decision) for after in waiting]
            for after, picked in zip(waiting, self.policy.likeliest_picks(positions), strict=True):
                after.pick(picked)
        return trials

    def rated(self, handle: Handle, tried: list[int] | None = None) -> dict[int, float]:
        """For each Option tried (by default the `likeliest`), the likeliest first: its Player's mean chance of winning
        once it is picked and its follow-ups answered, over the Sampled Positions."""
        found: dict[int, list[float]] = {}
        going: list[tuple[int, Position]] = []
        for index, after in self.trials(handle, tried):
            found.setdefault(index, [])
            if after.scores is not None:
                found[index].append(result_of(after.scores, handle.player))
            else:
                going.append((index, view_position(after.player_view(handle.player))))
        chances = chances_of_winning(self.model, [position for _, position in going]) if going else []
        for (index, _), chance in zip(going, chances, strict=True):
            found[index].append(chance)
        return {index: sum(values) / len(values) for index, values in found.items()}


def narrowed(chances: list[float], tried: int, share: float) -> list[int]:
    """Of the `tried` Options with the highest `chances`, those with at least `share` of the highest, highest first:
    the Options the Value Bot and the Search Bot (ai.search) try."""
    least = share * max(chances)
    ranked = sorted(range(len(chances)), key=lambda index: -chances[index])[:tried]
    return [index for index in ranked if chances[index] >= least]


def follows_up(decision: dict[str, Any] | None, player: int) -> bool:
    """Whether `decision` is `player`'s and follows from the one before (FOLLOW_UPS)."""
    return decision is not None and decision["player"] == player and decision["kind"] in FOLLOW_UPS
