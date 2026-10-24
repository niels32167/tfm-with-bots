"""Undo: back to the human's previous Decision, skipping Random Bot picks, any number of times."""

import time

from tests.helpers import player, terraformed_mars
from tests.server.helpers import connect

BOT_DELAY = 0.2


def test_undo_returns_to_the_humans_previous_decision_and_drops_the_random_bots_picks_since():
    with connect() as gui:
        before = gui.start(["human", "random_bot"], seed=5)
        log_before = gui.log
        gui.pick(before, "Done")  # buying no card at setup
        after = gui.wait_for_human()

        undone = gui.undo()

    assert after["decision"]["sequence"] > before["decision"]["sequence"] + 1  # the Random Bot picked
    assert undone["decision"] == before["decision"]
    assert undone["view"] == before["view"]
    assert gui.log == log_before


def test_undo_can_go_back_any_number_of_times_until_the_first_human_decision():
    with connect() as gui:
        first = gui.start(["random_bot", "human", "random_bot"], seed=8)
        assert not first["can_undo"]
        update = first
        for label in ("Done", "Pass", "Done"):  # at setup, in Generation 1, and in Generation 2's Research phase
            gui.pick(update, label)
            update = gui.wait_for_human()
            assert update["can_undo"]

        for _ in range(3):
            update = gui.undo()

        assert update["decision"] == first["decision"]
        assert not update["can_undo"]
        gui.send({"type": "undo"})
        assert "no earlier human Decision" in gui.receive_error()


def test_in_hotseat_undo_goes_back_one_human_decision_at_a_time():
    with connect() as gui:
        first = gui.start(["human", "human"], seed=8)
        gui.pick(first, "Done")
        second = gui.next_update()
        gui.pick(second, "Done")
        gui.next_update()

        assert gui.undo()["decision"] == second["decision"]
        assert gui.undo()["decision"] == first["decision"]


def test_undo_while_a_random_bot_is_taking_its_turn_stops_it():
    with connect() as gui:
        # Past the setup buy, in which a Random Bot picks without pausing.
        before = gui.skip_buying(gui.start(["human", "random_bot"], seed=5, bot_delay=BOT_DELAY))
        gui.pick(before, "Pass")
        assert gui.next_update()["decision"] is None  # the Random Bot's Turn

        undone = gui.undo()
        # A Random Bot that was not stopped would pick within this time; there is no
        # message to wait for when it, correctly, does nothing.
        time.sleep(3 * BOT_DELAY)
        saved = gui.save_replay()

    assert undone["decision"] == before["decision"]
    assert len(saved["replay"]["picks"]) == before["decision"]["sequence"]


def test_undo_after_the_game_is_over_returns_to_the_last_human_decision():
    # One Asteroid short of a terraformed Mars, so the Game ends after this Generation.
    scenario = {"players": [player(megacredits=14), player(megacredits=0)], **terraformed_mars(temperature=6)}
    file = {"controllers": ["human", "random_bot"], "replay": {"start": {"scenario": scenario}, "picks": []}}
    with connect() as gui:
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        gui.pick(gui.wait_for_human(), "Asteroid")
        last = gui.wait_for_human()
        gui.pick(last, "Pass")
        over = gui.wait_for_human()
        assert over["view"]["phase"] == "over"

        undone = gui.undo()

    assert undone["decision"] == last["decision"]
    assert undone["view"]["phase"] == "action"


def test_after_undo_the_same_human_picks_bring_the_same_random_bot_picks():
    with connect() as gui:
        before = gui.start(["human", "random_bot", "random_bot"], seed=5)
        gui.pick(before, "Done")
        first_time = gui.wait_for_human()
        log_first_time = gui.log

        gui.undo()
        gui.pick(before, "Done")
        second_time = gui.wait_for_human()

    assert second_time["view"] == first_time["view"]
    assert gui.log == log_first_time
