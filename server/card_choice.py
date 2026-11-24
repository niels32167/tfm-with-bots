"""Choosing cards on the screen: a human toggles them, and once they press Done the cards answer as many Decisions as
it takes (ADR 0015). The engine goes on asking for one card at a time (ADR 0002)."""

from typing import Any

import tm_engine

# Kinds of Decisions a choice answers one after another, until it is done. At setup, the Corporation, Prelude Cards
# and Project Cards are one choice; of the other kinds, such as a Draft pick, a choice answers one Decision.
SETUP = frozenset({"corporation", "prelude_cards", "buy_cards"})
ANSWERED_TO_THE_END = (SETUP, frozenset({"keep_cards"}), frozenset({"sell_patents"}))

# The Options that choose a card.
CHOOSING_A_CARD = frozenset(
    {
        "choose_corporation",
        "keep_prelude_card",
        "play_prelude_card",
        "draft_card",
        "buy_card",
        "keep_card",
        "sell_card",
        "discard_card",
    }
)


def picks_for_cards(game: tm_engine.Game, cards: list[str]) -> list[int]:
    """The picks that choose exactly `cards` (card ids) for the Decision `game` waits on and those that make up one
    choice with it, being done once they are chosen. Raises ValueError, as the choice is one the Player can't make, if
    one of the cards isn't offered or another is still to be chosen. `game` stays as it is."""
    trying = game.copy()
    started = trying.decision
    if started is None:
        raise ValueError("the Game is over, so there is nothing to choose")
    left = list(cards)
    picks: list[int] = []
    decision = started
    while True:
        index, done = option_for(decision, left)
        trying.pick(index)
        picks.append(index)
        decision = trying.decision
        if done or not continues_choice(started, decision):
            break
    if left:
        raise ValueError(f"{left[0]!r} can't be chosen here, or not as well")
    return picks


def continues_choice(started: dict[str, Any], decision: dict[str, Any] | None) -> bool:
    """Whether `decision` follows in the choice that `started` began, before its Player was done."""
    group = next((kinds for kinds in ANSWERED_TO_THE_END if started["kind"] in kinds), frozenset())
    return decision is not None and decision["player"] == started["player"] and decision["kind"] in group


def option_for(decision: dict[str, Any], left: list[str]) -> tuple[int, bool]:
    """The index of the Option that chooses one of the cards `left`, which it is then taken off; with none, the index
    of Done; and whether it is Done."""
    for option in decision["options"]:
        details = option["details"]
        if details["type"] in CHOOSING_A_CARD and details["card"] in left:
            left.remove(details["card"])
            return option["index"], False
    for option in decision["options"]:
        if option["details"]["type"] == "done":
            return option["index"], True
    if left:
        raise ValueError(f"{left[0]!r} can't be chosen here")
    raise ValueError("choose one more card first")
