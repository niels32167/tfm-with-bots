"""The Controller seam (ADR 0013): a Controller is handed a read-only handle and returns the index of
an Option. The handle holds the deciding Player's Player View and the Decision, never the Game, so
that no Controller can see a card its Player can't. To look ahead, it asks the handle for Sampled
Positions: Games dealt from what the Player View holds.

The handle can only make sure nothing hidden is handed over. A Controller that made Games of its own
with the engine could still cheat: a Match's seeds are small, so the cards dealt to it would give the
seed away. So no Controller imports the engine; tests/ai/test_fair_play.py checks it.
"""

import random
from dataclasses import dataclass
from typing import Any, Protocol

import tm_engine


@dataclass(frozen=True, slots=True)
class Handle:
    """What a Controller gets to answer a Decision: plain data only, so that nothing reachable from it
    is the Game, a copy of it, or a hidden card.

    `player_view` is the deciding Player's Player View and `decision` the Decision they answer, as the
    engine module gives them but without its sequence number, which counts every pick so far, hidden
    ones too; changing either changes nothing in the Game. `random` is the Controller's random source:
    a Controller that draws its random numbers only from it plays the same way from the same position.
    `sampler` is the engine object that makes Sampled Positions; it holds the position inside the
    engine and offers nothing else.
    """

    player: int
    player_view: dict[str, Any]
    decision: dict[str, Any]
    random: random.Random
    sampler: tm_engine.Sampler

    def sample(self, *, seed: int) -> tm_engine.Game:
        """A Sampled Position for the deciding Player: a new Game, with the cards they can't see dealt
        at random from `seed`, and the same Decision to answer. The same seed gives the same Game, and
        so does any position the Player can't tell from this one."""
        return self.sampler.sample(seed=seed)


class Controller(Protocol):
    """Whoever answers a Player's Decisions. One is made for each Player in each Game, so it may keep
    what it learns during the Game."""

    def pick(self, handle: Handle) -> int:
        """The index of the Option to pick, among `handle.decision["options"]`."""
        ...


def offered(decision: dict[str, Any], index: object) -> bool:
    """Whether `index` names one of `decision`'s Options: what a Controller's pick must be."""
    return type(index) is int and 0 <= index < len(decision["options"])


def handle_for(game: tm_engine.Game, random_numbers: random.Random) -> Handle:
    """The handle for the Player who answers the Decision `game` is waiting on."""
    decision = game.decision
    if decision is None:
        raise ValueError("the Game is over, so there is no Decision to answer")
    player = decision["player"]
    del decision["sequence"]
    return Handle(player, game.player_view(player), decision, random_numbers, game.sampler(player))
