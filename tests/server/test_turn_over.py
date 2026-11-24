"""A human playing registered Controllers ends their Turn themselves: after their second Action the others wait for
End Turn, so that the human can still undo."""

import time

from tests.helpers import player
from tests.server.helpers import Gui, connect


def start_at(gui: Gui, controllers: list[str], *players: dict, **fields) -> dict:
    return gui.load({"players": list(players), **fields}, controllers)


def take_two_actions(gui: Gui, update: dict) -> dict:
    """Two Asteroids: the update after the first one's, and the update after the second."""
    gui.pick(update, "Asteroid")
    second = gui.next_update()
    gui.pick(second, "Asteroid")
    return gui.next_update()


def test_after_the_second_action_the_others_wait_for_end_turn():
    with connect() as gui:
        update = start_at(gui, ["human", "random_bot"], player(megacredits=28), player())
        assert update["turn_over"] is False
        over = take_two_actions(gui, update)
        time.sleep(0.3)
        picks = len(gui.save_replay()["replay"]["picks"])
        gui.send({"type": "end_turn"})
        after = gui.next_update()

    assert (over["turn_over"], over["decision"], over["can_undo"]) == (True, None, True)
    assert picks == 2
    assert after["turn_over"] is False


def test_undo_takes_back_the_second_action_while_the_others_wait():
    with connect() as gui:
        over = take_two_actions(gui, start_at(gui, ["human", "random_bot"], player(megacredits=28), player()))
        undone = gui.undo()

    assert over["turn_over"]
    assert undone["turn_over"] is False
    assert undone["decision"]["sequence"] == 1


def test_end_turn_and_pass_as_options_need_no_second_click():
    with connect() as gui:
        update = start_at(gui, ["human", "random_bot"], player(megacredits=28), player())
        gui.pick(update, "Asteroid")
        gui.pick(gui.next_update(), "End Turn")
        assert gui.next_update()["turn_over"] is False


def test_selling_patents_as_the_second_action_waits_for_end_turn():
    with connect() as gui:
        update = start_at(gui, ["human", "random_bot"], player(megacredits=14, hand=["mine", "trees"]), player())
        gui.pick(update, "Asteroid")
        gui.pick(gui.next_update(), "Sell Patents")
        gui.choose(gui.next_update(), ["mine"])
        assert gui.next_update()["turn_over"] is True


def test_nobody_waits_once_the_others_have_passed_nor_in_hotseat():
    with connect() as gui:
        update = start_at(gui, ["human", "random_bot"], player(megacredits=28), player(passed=True))
        over = take_two_actions(gui, update)
        assert (over["turn_over"], over["decision"]["player"]) == (False, 0)

        update = start_at(gui, ["human", "human"], player(megacredits=28), player())
        over = take_two_actions(gui, update)
        assert (over["turn_over"], over["decision"]["player"]) == (False, 1)


def test_the_last_prelude_card_waits_for_end_turn_before_the_others_play_theirs():
    with connect() as gui:
        update = start_at(
            gui,
            ["human", "random_bot"],
            player(prelude_cards=["loan"]),
            player(prelude_cards=["donation"]),
            prelude=True,
            ask_last_prelude_card=True,
        )
        gui.choose(update, ["loan"])
        assert gui.next_update()["turn_over"] is True


def test_end_turn_is_refused_unless_the_turn_is_over():
    with connect() as gui:
        start_at(gui, ["human", "random_bot"], player(), player())
        gui.send({"type": "end_turn"})
        assert "not over" in gui.receive_error()


def test_a_game_saved_while_the_others_wait_loads_waiting():
    with connect() as gui:
        take_two_actions(gui, start_at(gui, ["human", "random_bot"], player(megacredits=28), player()))
        file = gui.save_replay()
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        assert gui.next_update()["turn_over"] is True
