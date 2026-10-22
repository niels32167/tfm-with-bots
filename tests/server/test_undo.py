"""Undo: back to the human's previous Decision, skipping Random Bot picks, any number of times."""

import time

from tests.helpers import matching_options
from tests.server.helpers import MAX_MESSAGES, connect

BOT_DELAY = 0.2


def test_undo_returns_to_the_humans_previous_decision_and_drops_the_random_bots_picks_since():
    with connect() as gui:
        before = gui.start(["human", "random_bot"], seed=5)
        log_before = gui.log
        gui.pick(before, "Pass")
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
        for _ in range(3):
            gui.pick(update, "Pass")
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
        gui.pick(first, "Asteroid")
        second = gui.next_update()
        gui.pick(second, "Pass")
        gui.next_update()

        assert gui.undo()["decision"] == second["decision"]
        assert gui.undo()["decision"] == first["decision"]


def test_undo_while_a_random_bot_is_taking_its_turn_stops_it():
    with connect() as gui:
        before = gui.start(["human", "random_bot"], seed=5, bot_delay=BOT_DELAY)
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
    with connect() as gui:
        update = gui.start(["human", "random_bot"], seed=2)
        last_decision = None
        for _ in range(MAX_MESSAGES):
            if update["decision"] is None:
                break
            last_decision = update["decision"]
            asteroid_offered = bool(matching_options(update["decision"]["options"], "Asteroid"))
            gui.pick(update, "Asteroid" if asteroid_offered else "Pass")
            update = gui.wait_for_human()
        assert update["view"]["phase"] == "over"

        undone = gui.undo()

    assert undone["decision"] == last_decision
    assert undone["view"]["phase"] == "action"


def test_after_undo_the_same_human_picks_bring_the_same_random_bot_picks():
    with connect() as gui:
        before = gui.start(["human", "random_bot", "random_bot"], seed=5)
        gui.pick(before, "Pass")
        first_time = gui.wait_for_human()
        log_first_time = gui.log

        gui.undo()
        gui.pick(before, "Pass")
        second_time = gui.wait_for_human()

    assert second_time["view"] == first_time["view"]
    assert gui.log == log_first_time
