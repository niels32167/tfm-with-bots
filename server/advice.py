"""What a registered Controller would do at a human's Decision, for the GUI (ADR 0015; ai.advice)."""

from typing import Any

import tm_engine

from ai.advice import Advice, advice
from ai.controller import handle_for
from ai.controllers import make_controller
from ai.explain import server_random
from server.card_choice import CHOOSING_A_CARD, continues_choice

# The Options shown of a Decision, best first.
MOST_OPTIONS = 8


def advise(game: tm_engine.Game, name: str) -> dict[str, Any]:
    """What the registered Controller `name` would do at the Decision `game` waits on, from its Player's handle, as plain
    data: the ids of the "cards" it would choose, and the "decisions" it would make, with how it rates their Options.
    Where cards are chosen one after another and sent together (server.card_choice), as at setup, it goes on as that
    Player on a copy, until it would be done, and gives its advice on the first Decision of each kind. Nothing is looked
    at beyond the choice. `game` stays as it is."""
    controller = make_controller(name)
    trying = game.copy()
    started = trying.decision
    cards: list[str] = []
    decisions: dict[str, dict[str, Any]] = {}
    while True:
        decision = trying.decision
        handle = handle_for(trying, server_random(trying.seed, decision["sequence"]))
        # Of the later Decisions of a kind the pick is enough, and quicker to find.
        advised = Advice(controller.pick(handle)) if decision["kind"] in decisions else advice(controller, handle)
        decisions.setdefault(decision["kind"], decision_data(decision, advised))
        details = decision["options"][advised.picked]["details"]
        if details["type"] not in CHOOSING_A_CARD:
            break
        cards.append(details["card"])
        trying.pick(advised.picked)
        if not continues_choice(started, trying.decision):
            break
    return {"cards": cards, "decisions": list(decisions.values())}


def decision_data(decision: dict[str, Any], advised: Advice) -> dict[str, Any]:
    """The advice on one Decision, its best Options first."""
    options = decision["options"]
    listed = advised.ranked()[:MOST_OPTIONS] or [advised.picked]
    return {
        "kind": decision["kind"],
        "picked": advised.picked,
        "measures": [{"name": measure.name, "percent": measure.percent} for measure in advised.measures],
        "options": [
            {"index": index, "label": options[index]["label"], "measured": advised.measured.get(index, [])}
            for index in listed
        ],
        "more": max(0, len(options) - len(listed)),
    }
