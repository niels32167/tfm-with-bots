"""How long a Random Bot pauses before it picks, as the GUI sees it: long enough to follow what it
does, and not at all where there is nothing to follow."""

import time
from typing import Any

from tests.server.helpers import Gui, connect

# Far longer than a pick takes, so that a missing pause can't be mistaken for a slow pick.
LONG_DELAY = 5.0
SHORT_DELAY = 0.2


def seconds_until_the_human_decides(
    gui: Gui, random_bot: dict[str, Any], bot_delay: float
) -> tuple[float, dict[str, Any]]:
    """Starts from a position where a Random Bot described by `random_bot` takes the first Turn against
    a human; how long until the human must decide, and the update then."""
    players = [{"corporation": "ecoline", **random_bot}, {"corporation": "credicor"}]
    file = {
        "controllers": ["random_bot", "human"],
        "replay": {"start": {"scenario": {"players": players}}, "picks": []},
    }
    gui.send({"type": "load_replay", "file": file, "bot_delay": bot_delay})
    start = time.monotonic()
    update = gui.wait_for_human()
    return time.monotonic() - start, update


def test_a_random_bot_does_not_pause_for_a_decision_with_one_option():
    # No MegaCredits and no cards: all it can do is Pass.
    with connect() as gui:
        seconds, update = seconds_until_the_human_decides(
            gui, {"resources": {"megacredits": 0}}, LONG_DELAY
        )

    assert update["decision"]["player"] == 1
    assert update["view"]["players"][0]["passed"]
    assert seconds < LONG_DELAY


def test_a_random_bot_pauses_for_a_decision_with_several_options():
    # A card to sell makes Sell Patents a second Option, whichever it then picks.
    with connect() as gui:
        seconds, _ = seconds_until_the_human_decides(
            gui, {"resources": {"megacredits": 0}, "hand": ["mine"]}, SHORT_DELAY
        )

    assert seconds >= SHORT_DELAY


def test_a_random_bot_still_does_not_pause_to_draft_or_buy():
    with connect() as gui:
        gui.send(
            {
                "type": "new_game",
                "controllers": ["random_bot", "human"],
                "seed": 1,
                "bot_delay": LONG_DELAY,
            }
        )
        start = time.monotonic()
        update = gui.wait_for_human()

    assert update["decision"]["kind"] in ("corporation", "buy_cards")
    assert time.monotonic() - start < LONG_DELAY
