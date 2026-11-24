"""Undo: back to the human's previous Decision, as long as it gives nothing away. Against registered Controllers that
is until another Player picks, cards are drawn or looked at, or everyone's hidden choices are revealed. In Hotseat,
where the screen shows everything anyway, undo goes back any number of times."""

import time

import tm_engine

from tests.helpers import player, terraformed_mars
from tests.server.helpers import Gui, connect

BOT_DELAY = 0.2


def start_at(gui: Gui, controllers: list[str], *players: dict, **fields) -> dict:
    return gui.load({"players": list(players), **fields}, controllers)


def refuse_to_undo(gui: Gui) -> bool:
    gui.send({"type": "undo"})
    return "can't be taken back" in gui.receive_error()


def test_undo_goes_back_through_the_humans_own_picks_this_turn():
    with connect() as gui:
        first = start_at(gui, ["human", "random_bot"], player(megacredits=40), player())
        assert not first["can_undo"]
        gui.pick(first, "Aquifer")
        areas = gui.next_update()
        gui.pick(areas, "Place the Ocean on A2")
        gui.next_update()

        assert gui.undo()["decision"] == areas["decision"]
        undone = gui.undo()
        assert undone["decision"] == first["decision"]
        assert not undone["can_undo"]
        assert refuse_to_undo(gui)


def test_another_players_pick_ends_undo():
    with connect() as gui:
        update = start_at(gui, ["human", "random_bot"], player(megacredits=14), player(megacredits=100))
        gui.pick(update, "Asteroid")
        gui.pick(gui.next_update(), "End Turn")
        after = gui.wait_for_human()

        assert not after["can_undo"]
        assert refuse_to_undo(gui)


def test_drawing_cards_ends_undo_but_what_comes_after_can_be_undone():
    with connect() as gui:
        update = start_at(gui, ["human", "random_bot"], player(hand=["research"]), player(), deck=["mine", "trees"])
        gui.pick(update, "Play Research")
        drawn = gui.next_update()
        assert not drawn["can_undo"]
        assert refuse_to_undo(gui)
        gui.pick(drawn, "Asteroid")
        assert gui.next_update()["can_undo"]
        undone = gui.undo()

    assert undone["decision"] == drawn["decision"]
    assert not undone["can_undo"]


def test_looking_at_cards_ends_undo():
    with connect() as gui:
        update = start_at(
            gui,
            ["human", "random_bot"],
            player(hand=["business_contacts"]),
            player(),
            deck=["mine", "trees", "birds", "fish"],
        )
        gui.pick(update, "Play Business Contacts")
        assert not gui.next_update()["can_undo"]


def test_buying_at_setup_can_be_undone_until_everyone_is_done():
    with connect() as gui:
        # Player 2, the human, chooses after the Random Bot, so being done reveals everyone's Corporation.
        update = gui.start(["random_bot", "human"], seed=2)
        corporation = gui.choose_a_corporation(update)
        assert corporation["can_undo"]
        gui.pick(corporation, "Done")
        assert not gui.next_update()["can_undo"]


def test_a_draft_pick_after_which_the_hands_are_passed_on_ends_undo():
    # The Random Bot is the first player of Generation 2, so the human picks last and then sees the hand passed on.
    seed = next(seed for seed in range(100) if tm_engine.Game(seed=seed).full_view()["first_player"] == 1)
    with connect() as gui:
        update = gui.skip_drafting_and_buying(gui.start(["random_bot", "human"], seed=seed))
        while update["decision"]["kind"] != "draft":
            gui.pick(update, "Pass")
            update = gui.wait_for_human()
        gui.send({"type": "set_bot_delay", "bot_delay": 0})
        gui.next_update()
        gui.choose(update, [update["decision"]["options"][0]["details"]["card"]])
        passed_on = gui.next_update()

    assert len(update["view"]["players"][1]["drafting"]["picking_from"]) == 4
    assert len(passed_on["view"]["players"][1]["drafting"]["picking_from"]) == 3
    assert not passed_on["can_undo"]


def test_passing_into_the_next_generation_ends_undo():
    with connect() as gui:
        update = start_at(gui, ["human", "random_bot"], player(), player(passed=True), draft=False)
        gui.pick(update, "Pass")
        assert not gui.next_update()["can_undo"]


def test_in_hotseat_undo_goes_back_any_number_of_times():
    with connect() as gui:
        first = gui.start(["human", "human"], seed=8, draft=False)
        update = gui.skip_drafting_and_buying(first)
        for label in ("Pass", "Pass"):
            gui.pick(update, label)
            update = gui.next_update()
        assert update["view"]["generation"] == 2

        while update["can_undo"]:
            update = gui.undo()

    assert update["decision"] == first["decision"]


def test_undo_while_a_random_bot_is_about_to_take_its_turn_stops_it():
    with connect() as gui:
        before = gui.skip_drafting_and_buying(gui.start(["human", "random_bot"], seed=5, bot_delay=BOT_DELAY))
        gui.pick(before, "Pass")
        assert gui.next_update()["decision"] is None  # the Random Bot's Turn

        undone = gui.undo()
        # A Random Bot that was not stopped would pick within this time; there is no
        # message to wait for when it, correctly, does nothing.
        time.sleep(3 * BOT_DELAY)
        saved = gui.save_replay()

    assert undone["decision"] == before["decision"]
    assert len(saved["replay"]["picks"]) == before["decision"]["sequence"]


def test_once_the_game_is_over_nothing_is_undone():
    # One Asteroid short of a terraformed Mars, so the Game ends after this Generation.
    with connect() as gui:
        update = start_at(
            gui,
            ["human", "random_bot"],
            player(megacredits=14),
            player(megacredits=0, passed=True),
            **terraformed_mars(temperature=6),
        )
        gui.pick(update, "Asteroid")
        gui.pick(gui.next_update(), "Pass")
        over = gui.next_update()

    assert over["view"]["phase"] == "over"
    assert not over["can_undo"]


def test_after_undo_the_same_human_picks_bring_the_same_random_bot_picks():
    with connect() as gui:
        before = gui.skip_drafting_and_buying(gui.start(["human", "random_bot"], seed=5, bot_delay=BOT_DELAY))
        gui.pick(before, "Pass")
        gui.next_update()
        gui.undo()
        gui.pick(before, "Pass")
        second_time = gui.wait_for_human()
        log_second_time = gui.log

        again = gui.skip_drafting_and_buying(gui.start(["human", "random_bot"], seed=5))
        gui.pick(again, "Pass")
        first_time = gui.wait_for_human()

    assert second_time["view"] == first_time["view"]
    assert gui.log == log_second_time
