"""Registered Controllers (ai.controllers) in the GUI: the setup screen lists them, the server asks them
for their picks through the same handle a Match uses, and a slow one doesn't hold the server up."""

import threading
import time
from typing import ClassVar

import pytest

from ai.controller import Handle
from ai.controllers import REGISTERED, Registered
from tests.server.helpers import connect

THINKING = 1.0
# Player 1 goes first on this seed, so a Controller for Player 1 is asked first.
PLAYER_1_FIRST = 2


class FirstOption:
    def pick(self, handle: Handle) -> int:
        return 0


class SlowBot:
    """Thinks for a while before every pick, as a search would, and remembers what it was handed."""

    handles: ClassVar[list[Handle]] = []
    picked: ClassVar[threading.Event] = threading.Event()

    def pick(self, handle: Handle) -> int:
        time.sleep(THINKING)
        SlowBot.handles.append(handle)
        SlowBot.picked.set()
        return 0


class SlowAtActions(SlowBot):
    """Thinks only about its Actions, and picks the first Option at once otherwise."""

    def pick(self, handle: Handle) -> int:
        return super().pick(handle) if handle.decision["kind"] == "action" else 0


class Broken:
    def pick(self, handle: Handle) -> int:
        raise RuntimeError("out of ideas")


@pytest.fixture(autouse=True)
def registered(monkeypatch):
    monkeypatch.setitem(REGISTERED, "first_option", Registered("First Option", FirstOption))
    monkeypatch.setitem(REGISTERED, "slow_bot", Registered("Slow Bot", SlowBot))
    monkeypatch.setitem(REGISTERED, "slow_at_actions", Registered("Slow At Actions", SlowAtActions))
    monkeypatch.setitem(REGISTERED, "broken", Registered("Broken", Broken))
    SlowBot.handles = []
    SlowBot.picked = threading.Event()


def test_the_gui_is_told_the_controllers_it_can_offer():
    with connect() as gui:
        gui.send({"type": "save_replay"})  # anything, to read what the server sent on connecting
        gui.receive_error()

    named = {controller["name"]: controller for controller in gui.controllers}
    assert gui.controllers[0]["label"] == "Human"
    assert named["random_bot"]["label"] == "Random Bot"
    assert named["first_option"]["label"] == "First Option"
    assert "at random" in named["random_bot"]["description"]
    assert named["random_bot"]["most_players"] == 5


def test_a_registered_controller_plays_a_player_and_is_saved_in_the_replay_file():
    with connect() as gui:
        update = gui.start(["first_option", "human"], seed=3, prelude=True)
        update = gui.skip_drafting_and_buying(update)
        file = gui.save_replay()

    assert update["controllers"] == ["first_option", "human"]
    assert file["controllers"] == ["first_option", "human"]
    # First Option chose the first Corporation dealt to it.
    board = update["view"]["players"][0]
    assert board["corporation"] is not None


def test_a_replay_file_with_a_registered_controller_loads_and_plays_on():
    with connect() as gui:
        update = gui.start(["first_option", "human"], seed=3, prelude=True)
        gui.skip_drafting_and_buying(update)
        file = gui.save_replay()

        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        loaded = gui.wait_for_human()

    assert loaded["controllers"] == ["first_option", "human"]
    assert loaded["decision"]["player"] == 1


@pytest.mark.parametrize("name", ["deep_blue", "ai.random_bot:RandomBot"])
def test_a_replay_naming_an_unregistered_controller_is_refused(name):
    # Not even by module and attribute: loading a file must never import code it names.
    file = {"controllers": [name, "human"], "replay": {"start": {"settings": {"players": 2, "seed": 1}}, "picks": []}}
    with connect() as gui:
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        error = gui.receive_error()

    assert f"unknown Controller {name!r}" in error
    assert "random_bot" in error and "human" in error


def test_the_server_answers_while_a_slow_controller_thinks():
    with connect() as gui:
        gui.send({"type": "new_game", "controllers": ["slow_bot", "human"], "seed": PLAYER_1_FIRST, "bot_delay": 0})
        gui.next_update()
        started = time.monotonic()
        file = gui.save_replay()
        answered_in = time.monotonic() - started

    assert answered_in < THINKING / 2
    assert file["controllers"] == ["slow_bot", "human"]


def test_the_controller_is_handed_its_players_view_not_the_full_view():
    with connect() as gui:
        gui.send({"type": "new_game", "controllers": ["slow_bot", "human"], "seed": PLAYER_1_FIRST, "bot_delay": 0})
        assert SlowBot.picked.wait(THINKING * 5)

    handle = SlowBot.handles[0]
    assert handle.player == 0
    assert handle.player_view["viewer"] == 0
    assert handle.player_view["players"][1]["hand"] is None


def test_a_pick_that_comes_back_after_an_undo_is_dropped():
    with connect() as gui:
        update = gui.start(["human", "slow_at_actions"], seed=PLAYER_1_FIRST)
        update = gui.skip_drafting_and_buying(update)
        # Into the Action phase, where the human goes first: they pass, so the bot thinks about its Turn.
        while update["decision"]["kind"] != "action":
            gui.pick(update, update["decision"]["options"][0]["label"])
            update = gui.wait_for_human()
        sequence = update["decision"]["sequence"]
        gui.pick(update, "Pass")
        gui.next_update()
        before = gui.undo()
        time.sleep(THINKING * 1.5)
        file = gui.save_replay()

    assert before["decision"]["sequence"] == sequence
    assert len(file["replay"]["picks"]) == sequence


def test_a_controller_that_raises_is_reported_to_the_gui():
    with connect() as gui:
        gui.send({"type": "new_game", "controllers": ["broken", "human"], "seed": PLAYER_1_FIRST, "bot_delay": 0})
        gui.next_update()
        error = gui.receive_error()

    assert "Broken" in error and "out of ideas" in error


class Patient:
    """Takes a setting, as the Search Bot takes its budget."""

    def __init__(self, seconds: float = 1.0) -> None:
        self.seconds = seconds

    def pick(self, handle: Handle) -> int:
        return 0


def test_a_registered_controller_can_be_given_its_settings_by_name(monkeypatch):
    # The Search Bot's budget is a setting: "search?seconds=5" in a new Game or a Replay file.
    monkeypatch.setitem(REGISTERED, "patient", Registered("Patient", Patient, settings=("seconds",)))
    with connect() as gui:
        update = gui.start(["patient?seconds=0.5", "human"], seed=3)
        file = gui.save_replay()
        gui.send({"type": "new_game", "controllers": ["patient?minutes=5", "human"], "seed": 3})
        error = gui.receive_error()

    assert update["controllers"] == ["patient?seconds=0.5", "human"]
    assert file["controllers"] == ["patient?seconds=0.5", "human"]
    assert "minutes" in error
