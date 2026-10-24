"""Saving the current Game as a Replay file, and loading one to carry on where it was saved."""

import json

from tests.server.helpers import Gui, connect


def play_a_few_turns(gui: Gui, controllers: list[str]) -> dict:
    """Starts a Game and has the humans take a few Actions; returns the latest update."""
    update = gui.skip_buying(gui.start(controllers, seed=12))
    for label in ("Asteroid", "End Turn", "Asteroid", "Pass"):
        gui.pick(update, label)
        update = gui.wait_for_human()
    return update


def test_a_saved_replay_file_holds_the_replay_and_every_players_controller():
    with connect() as gui:
        update = play_a_few_turns(gui, ["human", "random_bot", "random_bot"])
        file = gui.save_replay()

    assert file["controllers"] == ["human", "random_bot", "random_bot"]
    assert file["replay"]["start"] == {"settings": {"players": 3, "seed": 12, "implemented_cards_first": False}}
    assert len(file["replay"]["picks"]) == update["decision"]["sequence"]


def test_loading_a_replay_file_carries_on_the_game_where_it_was_saved():
    with connect() as gui:
        saved = play_a_few_turns(gui, ["random_bot", "human"])
        saved_log = gui.log
        file = json.loads(json.dumps(gui.save_replay()))

    with connect() as gui:
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        loaded = gui.wait_for_human()

    assert loaded["controllers"] == ["random_bot", "human"]
    assert loaded["seed"] == 12
    assert loaded["view"] == saved["view"]
    assert loaded["decision"] == saved["decision"]
    assert gui.log == saved_log


def test_after_loading_undo_goes_back_through_the_loaded_game():
    with connect() as gui:
        play_a_few_turns(gui, ["human", "human"])
        file = gui.save_replay()
        before_last_pick = gui.undo()

        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        loaded = gui.next_update()
        undone = gui.undo()

    assert loaded["can_undo"]
    assert undone["decision"] == before_last_pick["decision"]


def test_a_broken_replay_file_is_rejected_and_the_current_game_carries_on():
    with connect() as gui:
        update = gui.start(["human", "human"], seed=12)
        replay = {"start": {"settings": {"players": 2, "seed": 12}}, "picks": [0]}
        impossible_replay = {**replay, "picks": [0, 99]}

        gui.send({"type": "load_replay", "file": {"replay": replay}})
        assert "not a Replay file" in gui.receive_error()
        gui.send({"type": "load_replay", "file": {"controllers": ["human"], "replay": replay}})
        assert "2 Players, but 1 Controllers" in gui.receive_error()
        gui.send({"type": "load_replay", "file": {"controllers": ["human", "human"], "replay": impossible_replay}})
        assert "pick 2 of the Replay" in gui.receive_error()

        gui.pick(update, "Done")
        assert gui.next_update()["decision"]["sequence"] == update["decision"]["sequence"] + 1


def test_there_is_nothing_to_save_before_a_game_has_started():
    with connect() as gui:
        gui.send({"type": "save_replay"})
        assert "no Game yet" in gui.receive_error()


def test_a_loaded_game_carries_on_as_the_saved_one_would_have():
    with connect() as gui:
        saved = play_a_few_turns(gui, ["human", "random_bot", "random_bot"])
        file = gui.save_replay()
        gui.pick(saved, "Done")  # buying nothing in Generation 2's Research phase
        carried_on = gui.wait_for_human()

    with connect() as gui:
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        loaded = gui.wait_for_human()
        gui.pick(loaded, "Done")
        carried_on_after_loading = gui.wait_for_human()

    assert carried_on_after_loading["view"] == carried_on["view"]
