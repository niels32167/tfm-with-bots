"""Asking a bot what it would do at a human's Decision: which Option it would pick, and how it rates them."""

import threading
import time
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient

from ai.advice import PRICE, Advice
from ai.controller import Handle
from ai.controllers import REGISTERED, Registered
from server.app import create_app
from tests.helpers import player
from tests.server.helpers import Gui, connect


class LastOption:
    """Advises the last Option, priced at its index, and remembers what it was handed."""

    handles: ClassVar[list[Handle]] = []

    def pick(self, handle: Handle) -> int:
        LastOption.handles.append(handle)
        return len(handle.decision["options"]) - 1

    def advise(self, handle: Handle) -> Advice:
        picked = self.pick(handle)
        return Advice(picked, (PRICE,), {index: [float(index)] for index in range(picked + 1)})


class Slow(LastOption):
    asked: ClassVar[threading.Event] = threading.Event()

    def advise(self, handle: Handle) -> Advice:
        Slow.asked.set()
        time.sleep(1.0)
        return super().advise(handle)


class Broken:
    def pick(self, handle: Handle) -> int:
        raise RuntimeError("out of ideas")


@pytest.fixture(autouse=True)
def registered(monkeypatch):
    names = {"last": LastOption, "slow": Slow, "broken": Broken}
    for name, controller in names.items():
        monkeypatch.setitem(REGISTERED, name, Registered(name.title(), controller))
    monkeypatch.setitem(REGISTERED, "two_only", Registered("Two Only", LastOption, most_players=2))
    monkeypatch.setattr("ai.controllers.ADVISERS", ("two_only", "last", "slow", "broken"))
    LastOption.handles = []


def ask(gui: Gui, update: dict, name: str = "last") -> dict:
    gui.send({"type": "advice", "sequence": update["decision"]["sequence"], "controller": name})
    return gui.receive()


def test_a_bot_rates_the_options_of_an_action_best_first_and_nothing_is_picked():
    with connect() as gui:
        update = gui.load({"players": [player(megacredits=14), player()]})
        advice = ask(gui, update)
        picks = gui.save_replay()["replay"]["picks"]

    options = update["decision"]["options"]
    assert advice == {
        "type": "advice",
        "sequence": 0,
        "controller": "last",
        "cards": [],
        "decisions": [
            {
                "kind": "action",
                "picked": len(options) - 1,
                "measures": [{"name": "Price in MegaCredits", "percent": False}],
                "options": [
                    {"index": option["index"], "label": option["label"], "measured": [float(option["index"])]}
                    for option in reversed(options[-8:])
                ],
                "more": max(0, len(options) - 8),
            }
        ],
    }
    assert picks == []


def test_at_setup_the_bot_chooses_everything_and_rates_each_kind_of_decision_once():
    with connect() as gui:
        update = gui.start(["human", "random_bot"], seed=5, prelude=True)
        board = update["view"]["players"][0]
        advice = ask(gui, update)

    corporations, prelude_cards = board["choosing_corporation"]["dealt"], board["prelude_cards"]["dealt"]
    assert [each["kind"] for each in advice["decisions"]] == ["corporation", "prelude_cards", "buy_cards"]
    # Its last Option of each Decision: the last Corporation, the last two Prelude Cards, and Done.
    assert advice["cards"] == [corporations[-1], prelude_cards[-1], prelude_cards[-2]]


def test_advice_is_found_from_the_humans_own_view():
    with connect() as gui:
        update = gui.start(["random_bot", "human"], seed=5, prelude=True)
        ask(gui, update)

    assert {handle.player for handle in LastOption.handles} == {1}
    assert all(handle.player_view["players"][0]["hand"] is None for handle in LastOption.handles)


def test_the_advice_for_a_draft_pick_is_one_card():
    with connect() as gui:
        update = gui.start(["human", "human"], seed=8)
        update = gui.skip_drafting_and_buying(update)
        for _ in range(2):
            gui.pick(update, "Pass")
            update = gui.wait_for_human()
        advice = ask(gui, update)

    assert advice["cards"] == [update["decision"]["options"][-1]["details"]["card"]]


def test_the_server_answers_while_a_slow_bot_thinks_about_its_advice():
    with connect() as gui:
        update = gui.load({"players": [player(), player()]})
        started = time.monotonic()
        gui.send({"type": "advice", "sequence": 0, "controller": "slow"})
        assert Slow.asked.wait(5)
        gui.save_replay()
        answered_in = time.monotonic() - started
        advice = gui.receive()

    assert answered_in < 0.5
    assert (advice["type"], advice["controller"]) == ("advice", "slow")
    assert advice["sequence"] == update["decision"]["sequence"]


def test_a_newer_question_replaces_the_one_before():
    with connect() as gui:
        gui.load({"players": [player(), player()]})
        gui.send({"type": "advice", "sequence": 0, "controller": "slow"})
        gui.send({"type": "advice", "sequence": 0, "controller": "last"})
        assert gui.receive()["controller"] == "last"
        time.sleep(1.2)
        gui.save_replay()  # would come after the slow one's advice


def test_every_update_names_the_bots_that_can_advise_in_this_game():
    with connect() as gui:
        assert gui.start(["human", "random_bot"], seed=5)["advisers"] == ["two_only", "last", "slow", "broken"]
        assert gui.start(["human", "random_bot", "random_bot"], seed=5)["advisers"] == ["last", "slow", "broken"]


def test_advice_that_cant_be_given_is_refused():
    with connect() as gui:
        update = gui.load({"players": [player(), player()]})
        gui.send({"type": "advice", "sequence": 0, "controller": "random_bot"})
        assert "gives advice" in gui.receive_error()
        gui.send({"type": "advice", "sequence": 0, "controller": ["last"]})
        assert "gives advice" in gui.receive_error()
        gui.send({"type": "advice", "sequence": 7, "controller": "last"})
        assert "stale" in gui.receive_error()
        gui.send({"type": "advice", "sequence": update["decision"]["sequence"], "controller": "broken"})
        assert "out of ideas" in gui.receive_error()


def test_two_tabs_on_the_same_game_are_both_answered():
    with (
        TestClient(create_app()) as client,
        client.websocket_connect("/ws") as one,
        client.websocket_connect("/ws") as two,
    ):
        tabs = [Gui(one), Gui(two)]
        tabs[0].load({"players": [player(), player()]})
        tabs[1].wait_for_human()
        for tab in tabs:
            tab.send({"type": "advice", "sequence": 0, "controller": "slow"})
        time.sleep(1.5)
        # Anything the server answers a tab with comes after its advice, so that a tab left without fails, not hangs.
        for tab in tabs:
            tab.send({"type": "save_replay"})
        answers = [tab.receive()["type"] for tab in tabs]

    assert answers == ["advice", "advice"]
