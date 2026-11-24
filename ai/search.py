"""The Search Bot (ticket 16 of phase 2): a Controller that turns a time budget per Decision into strength by searching
a tree over Sampled Positions. It is information set Monte Carlo tree search, the user's call on 2026-11-21: one tree
for the deciding Player, whose nodes are their own Decisions as they see them, and a fresh Sampled Position for each
walk down it, so that what the Player can't see is averaged over rather than known.

- **The Options searched** at the Decision asked are those the Value Bot tries (ai.value.bot): of the `tried` the
  Imitation Model rates likeliest, those it gives at least `share` of the likeliest Option's chance. If one is left,
  it is picked at once, without spending the budget.
- **Each Sampled Position is walked once for every Option searched**, from the same seeds, so that Options are
  compared on equal terms (as the Flat Playout and Value Bots do), and each Sampled Position gives a paired difference
  between each other Option's result and the likeliest's. The likeliest is kept unless another beats it clearly: by
  a mean paired difference of more than `margin` standard errors. Of those that do, the one with the best mean result is picked; ties go to the
  likelier. A `margin` of 0 picks the best mean outright. This is ticket 15's lesson, that the Value Model's errors
  shouldn't overrule a confident Imitation Model, applied to the search.
- **A walk** picks the Option, then answers what follows:
  - follow-ups of anyone's (ai.value.encoded.is_follow_up: Payment, Area, target...) as the Imitation Model rates
    likeliest, as the Value Bot does;
  - the other Player's Decisions by drawing an Option at random in proportion to the Imitation Model's chances,
    narrowed by `share`: they are chance to this Player, like the cards drawn, which the Sampled Position deals;
  - the Player's own later Decisions by the tree: each Decision there is a node, its Options found again by their
    labels (one Sampled Position may offer Options another doesn't), picked by PUCT with the Imitation Model's chances
    as priors and `exploration` as its constant.
- **A walk stops** when the Game ends (rated by its result), or at the Player's own next Decision, or once the other
  Player has answered `horizon` Decisions. The position there is rated by the Value Model, from the Player's view,
  as the Value Bot rates it, or by a random playout (`leaves`, to compare the two). A node grows below an Option only once it has been
  rated there, so the tree deepens where the walks keep going.
- **The budget** (`seconds`) is spent a Sampled Position at a time: one more is begun only if it would end in time
  at the pace of the slowest so far, and one is left out if a walk on it might not end in time, at the pace of the
  slowest walk so far. The first is always walked whole. `samples` caps the Sampled Positions instead or as well, which
  makes picks repeatable: with `seconds` alone, how many fit depends on the computer's speed.

It reads only its handle: its Player View and Decision, and Sampled Positions, and draws every random number from
the handle's random source. It imports neither the engine nor Recorded Game code (ADR 0013).
"""

import math
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import ai.value
from ai.advice import STRONG_PLAYERS, WINS, Advice
from ai.controller import Handle
from ai.imitation.bot import ImitationBot
from ai.imitation.encoded import Position
from ai.value.bot import SEEDS, SHARE, TRIED, loaded, narrowed, policy_path
from ai.value.encoded import is_follow_up, result_of, view_position
from ai.value.model import chances_of_winning

# The budget per Decision by default, in seconds: the user's choice on 2026-11-21. Against the Value Bot (ticket 16's
# Comments), 0.1 seconds scored 60.5% in 100 Games and then 51.5% in the 400 of a final Match, 1 second 59.0% in 100.
SECONDS = 1.0
# How many of the other Player's Decisions (not counting follow-ups) a walk answers before the position is rated.
HORIZON = 2
# PUCT's constant at the Player's own later Decisions: how much a prior counts against the results so far.
EXPLORATION = 0.25
# How many standard errors of the paired difference another Option must beat the likeliest by to be picked instead;
# 0 by default, Claude's call on 2026-11-21: at 1 second a margin of 2 scored 56.5% against the Value Bot in 200
# Games and then 50.2% in the 400 of a final Match, where 0 scored 53.0% on the same seeds.
MARGIN = 0.0
# How the positions where walks stop are rated: by the Value Model, or by a random playout (to compare them).
LEAVES = ("value", "playouts")
# A guard: the most Decisions one walk answers before its position is rated wherever it is.
MOST_ANSWERED = 60


@dataclass
class Edge:
    """An Option at a node of the tree: the Imitation Model's chance for it, how often it was offered, picked and
    what the walks through it ended with, and the node of the Player's next Decision below it, once grown."""

    prior: float
    offered: int = 0
    visits: int = 0
    total: float = 0.0
    below: dict[str, Edge] | None = None

    @property
    def mean(self) -> float:
        return self.total / self.visits if self.visits else 0.0

    def add(self, result: float) -> None:
        self.visits += 1
        self.total += result


@dataclass
class Searched:
    """What a search found: for each Option searched (by index, likeliest first), its Edge; how many Sampled Positions
    it took; and on each of them, the result of each Option's walk, in the same order."""

    options: dict[int, Edge] = field(default_factory=dict)
    samples: int = 0
    paired: list[list[float]] = field(default_factory=list)

    def add(self, results: list[float]) -> None:
        """Adds one Sampled Position's results, one for each Option searched, in the order of `options`."""
        for edge, result in zip(self.options.values(), results, strict=True):
            edge.offered += 1
            edge.add(result)
        self.paired.append(results)
        self.samples += 1

    def picked(self, margin: float) -> int:
        """The likeliest Option, unless another beats it on the same Sampled Positions by a mean difference over
        `margin` standard errors of that difference: then the best mean of those that do. With one Sampled Position
        there is no standard error, so only a `margin` of 0 lets another Option win."""
        indexes = list(self.options)
        beating = [indexes[0]]
        for column, index in enumerate(indexes[1:], start=1):
            differences = [row[column] - row[0] for row in self.paired]
            mean = sum(differences) / len(differences) if differences else 0.0
            if len(differences) > 1:
                variance = sum((difference - mean) ** 2 for difference in differences) / (len(differences) - 1)
                standard_error = math.sqrt(variance / len(differences))
            else:
                standard_error = math.inf
            if mean > 0 and (margin == 0 or mean > margin * standard_error):
                beating.append(index)
        return max(beating, key=lambda index: self.options[index].mean)  # The likeliest wins a tie.


class SearchBot:
    """Searches with the Value Model saved at `path` (by default the registered one, ai.value.MODEL) and the Imitation
    Model it was trained beside, within `seconds` and at most `samples` Sampled Positions per Decision."""

    def __init__(
        self,
        path: Path | None = None,
        seconds: float | None = SECONDS,
        samples: int | None = None,
        tried: int = TRIED,
        share: float = SHARE,
        horizon: int = HORIZON,
        exploration: float = EXPLORATION,
        leaves: str = "value",
        margin: float = MARGIN,
    ) -> None:
        if seconds is None and samples is None:
            raise ValueError("a search needs a budget: seconds, samples or both")
        if not (seconds is None or (isinstance(seconds, int | float) and seconds > 0)):
            raise ValueError(f"seconds must be a number above 0, not {seconds!r}")
        if not (isinstance(margin, int | float) and margin >= 0):
            raise ValueError(f"margin must be a number of at least 0, not {margin!r}")
        if leaves not in LEAVES:
            raise ValueError(f"leaves must be one of {LEAVES}, not {leaves!r}")
        self.model, saved = loaded(Path(path or ai.value.MODEL))
        self.policy = ImitationBot(policy_path(saved))
        self.seconds = seconds
        self.samples = samples
        self.tried = tried
        self.share = share
        self.horizon = horizon
        self.exploration = exploration
        self.leaves = leaves
        self.margin = margin

    def pick(self, handle: Handle) -> int:
        if len(handle.decision["options"]) == 1:
            return 0
        searched = self.search(handle)
        return searched.picked(self.margin)

    def advise(self, handle: Handle) -> Advice:
        """The mean result of the Options searched, if more than one was, and the chance that a strong Player picks
        them."""
        searched = self.search(handle)
        measured = {index: [edge.mean if edge.visits else None, edge.prior] for index, edge in searched.options.items()}
        return Advice(searched.picked(self.margin), (WINS, STRONG_PLAYERS), measured)

    def narrowed(self, chances: list[float]) -> list[int]:
        """The Options searched among those with these chances, likeliest first (ai.value.bot.narrowed)."""
        return narrowed(chances, self.tried, self.share)

    def search(self, handle: Handle) -> Searched:
        """The search from `handle`'s Decision, within the budget. With one Option left after narrowing, none."""
        started = time.perf_counter()
        chances = self.policy.chances(handle)
        searched = Searched({index: Edge(chances[index]) for index in self.narrowed(chances)})
        if len(searched.options) == 1:
            return searched
        deadline = math.inf if self.seconds is None else started + self.seconds
        slowest_sample = slowest_walk = 0.0
        while self.samples is None or searched.samples < self.samples:
            begun = time.perf_counter()
            if searched.samples and begun + slowest_sample > deadline:
                break
            sample = handle.sample(seed=handle.random.randrange(SEEDS))
            walk_seed = handle.random.randrange(SEEDS)
            results = []
            for index, edge in searched.options.items():
                walk_begun = time.perf_counter()
                if searched.samples and walk_begun + slowest_walk > deadline:
                    return searched  # This Sampled Position is left out, so that every Option is rated on the same.
                results.append(self.walk(sample.copy(), index, edge, handle.player, random.Random(walk_seed)))
                slowest_walk = max(slowest_walk, time.perf_counter() - walk_begun)
            searched.add(results)
            slowest_sample = max(slowest_sample, time.perf_counter() - begun)
        return searched

    def walk(self, game: Any, index: int, edge: Edge, player: int, rng: random.Random) -> float:
        """Picks Option `index` in `game` and walks on (see the module's docstring): the result for `player`, which
        every Edge on the way below `edge` adds; `edge` itself is left to the caller."""
        game.pick(index)
        stopped_at_own = self.answer_until_rated(game, player, rng)
        if game.scores is not None:
            return result_of(game.scores, player)
        if not stopped_at_own or edge.visits == 0:
            return self.rated(game, player, rng)
        if edge.below is None:
            edge.below = {}
        return self.walk_below(game, edge.below, player, rng)

    def walk_below(self, game: Any, node: dict[str, Edge], player: int, rng: random.Random) -> float:
        """At `player`'s own Decision in `game`, a node of the tree: picks an Option by PUCT and walks on."""
        options = game.decision["options"]
        keys = keys_of(options)
        if len(options) == 1:
            chosen = 0
        else:
            chances = self.policy.chances_at(Position.of(game.player_view(player), game.decision))
            offered = []
            for index in self.narrowed(chances):
                edge = node.setdefault(keys[index], Edge(chances[index]))
                edge.offered += 1
                offered.append((index, edge))
            chosen, _ = max(offered, key=lambda found: self.puct(found[1], node))
        edge = node.setdefault(keys[chosen], Edge(1.0))
        if len(options) == 1:
            edge.offered += 1
        result = self.walk(game, chosen, edge, player, rng)
        edge.add(result)
        return result

    def puct(self, edge: Edge, node: dict[str, Edge]) -> float:
        """PUCT's score for `edge` at `node`, counting the times it was offered rather than its node's visits, since
        not every Sampled Position offers every Option. An Option not yet picked scores the node's mean so far."""
        visits = sum(other.visits for other in node.values())
        mean = edge.mean if edge.visits else (sum(other.total for other in node.values()) / visits if visits else 0.5)
        return mean + self.exploration * edge.prior * math.sqrt(edge.offered) / (1 + edge.visits)

    def answer_until_rated(self, game: Any, player: int, rng: random.Random) -> bool:
        """Answers `game`'s Decisions until the Game ends, `player` decides anew, the other Player has answered
        `horizon` Decisions, or the guard's count. Whether it stopped at `player`'s own Decision."""
        answered = 0
        for _ in range(MOST_ANSWERED):
            decision = game.decision
            if decision is None:
                return False
            follow_up = is_follow_up(decision)
            if not follow_up and (decision["player"] == player or answered >= self.horizon):
                return decision["player"] == player
            game.pick(self.answer(game, decision, follow_up, rng))
            answered += decision["player"] != player and not follow_up
        return False

    def answer(self, game: Any, decision: dict[str, Any], follow_up: bool, rng: random.Random) -> int:
        """A follow-up's likeliest Option, or for the other Player's Decision one drawn by the narrowed chances."""
        if len(decision["options"]) == 1:
            return 0
        chances = self.policy.chances_at(Position.of(game.player_view(decision["player"]), decision))
        if follow_up:
            return chances.index(max(chances))
        narrowed = self.narrowed(chances)
        return rng.choices(narrowed, weights=[chances[index] for index in narrowed])[0]

    def rated(self, game: Any, player: int, rng: random.Random) -> float:
        """`player`'s chance of winning from where a walk stopped, by the Value Model or random playouts."""
        if self.leaves == "playouts":
            game.play_randomly(seed=rng.randrange(SEEDS))
            return result_of(game.scores, player)
        return chances_of_winning(self.model, [view_position(game.player_view(player))])[0]


def keys_of(options: list[dict[str, Any]]) -> list[str]:
    """How a node of the tree finds each Option again on another Sampled Position: by its label, and by how many
    Options before it share that label, should any."""
    seen: dict[str, int] = {}
    keys = []
    for option in options:
        label = option["label"]
        keys.append(f"{label} #{seen[label]}" if label in seen else label)
        seen[label] = seen.get(label, 0) + 1
    return keys
