"""The Controller seam (ADR 0013): a Controller is handed a read-only handle and returns the index of
an Option. The handle holds the deciding Player's Player View and the Decision, never the Game, so
that no Controller can see a card its Player can't. To look ahead, it asks the handle for Sampled
Positions: Games dealt from what the Player View holds.

The handle can only make sure nothing hidden is handed over. A Controller that made Games of its own
with the engine could still cheat: a Match's seeds are small, so the cards dealt to it would give the
seed away. So no Controller imports the engine; tests/ai/test_fair_play.py checks it.
"""

import functools
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


def last_prelude_card(decision: dict[str, Any]) -> bool:
    """Whether `decision` is only to play a last Prelude Card, as a Game at a human's screen asks it and any other Game
    plays it at once (ADR 0015). A Controller looking ahead picks it as a follow-up, so that both Games look alike."""
    return decision["kind"] == "play_prelude_card" and len(decision["options"]) == 1


@functools.cache
def card_catalog() -> dict[str, dict[str, Any]]:
    """The card catalog by card id: every card's printed data, which every Player may read. For
    Controllers, which never import the engine. Shared, so never to be changed."""
    return {card["id"]: card for card in tm_engine.card_catalog()}


@functools.cache
def board_layout() -> tuple[dict[str, Any], ...]:
    """Every Area as printed, without Tiles, in the order of the board in a Player View: what every Player
    may read, for Controllers, which never import the engine. Shared, so never to be changed."""
    board = tm_engine.Game(seed=0, players=2).player_view(0)["board"]
    return tuple({key: value for key, value in area.items() if key not in ("tile", "claimed_by")} for area in board)


def handle_at(replay: dict[str, Any], step: int, random_numbers: random.Random) -> Handle:
    """The handle for the Decision a Replay waits on after its first `step` picks: to explain a pick
    made in a past Game."""
    return handle_for(tm_engine.Game.from_replay(replay, step=step), random_numbers)
