"""What a pick would draw, so that the GUI asks its human first: cards seen can't be unseen, so such a pick can't be
undone either (ADR 0015)."""

from typing import Any

import tm_engine

# Phases in which cards are dealt to everyone: what a pick that leads there deals isn't drawn by it.
DEALING = ("setup", "draft", "research")


def cards_left(view: dict[str, Any]) -> tuple[int, int]:
    """How many cards are left to draw, in the deck and the Prelude deck. They change whenever anyone draws, looks at
    or reveals one (a discard pile shuffled into a new deck changes them too)."""
    return view["deck_size"], view["prelude_deck_size"]


def what_it_draws(game: tm_engine.Game, index: int) -> str | None:
    """What picking the Option at `index` would have its Player draw or look at, as a button says it ("Draw 2 cards"),
    or None if nothing. It says nothing that the Player can't know before: the Option and the rules tell how many."""
    before = game.full_view()
    player = game.decision["player"]
    after_pick = game.copy()
    after_pick.pick(index)
    after = after_pick.full_view()
    if before["phase"] in DEALING or after["phase"] in DEALING or after["generation"] != before["generation"]:
        return None
    if cards_left(before) == cards_left(after):
        return None
    prelude_cards = before["prelude_deck_size"] - after["prelude_deck_size"]
    if prelude_cards > 0:
        return f"Draw {counted(prelude_cards, 'Prelude Card')}"
    board, board_after = before["players"][player], after["players"][player]
    drawn = len(set(board_after["hand"]) - set(board["hand"]))
    if drawn > 0:
        return f"Draw {counted(drawn, 'card')}"
    looked_at = before["deck_size"] - after["deck_size"]
    if looked_at <= 0:  # The discard pile was shuffled into a new deck on the way.
        return "See the top cards of the deck"
    return "See the top card of the deck" if looked_at == 1 else f"See the top {looked_at} cards of the deck"


def counted(count: int, what: str) -> str:
    return f"{count} {what}" if count == 1 else f"{count} {what}s"
