"""Choosing cards with a Done button: the GUI toggles cards on the screen and sends those chosen at once, and the
server answers as many Decisions with them as it takes, all or none."""

from tests.helpers import player
from tests.server.helpers import connect


def setup_choices(update: dict) -> tuple[list[str], list[str], list[str]]:
    """The Corporations, Prelude Cards and Project Cards dealt to the human deciding."""
    board = update["view"]["players"][update["decision"]["player"]]
    return (
        board["choosing_corporation"]["dealt"],
        board["prelude_cards"]["dealt"],
        board["buying"]["dealt"],
    )


def test_corporation_prelude_cards_and_project_cards_are_chosen_at_setup_all_at_once():
    with connect() as gui:
        update = gui.start(["human", "human"], seed=5, prelude=True)
        player_deciding = update["decision"]["player"]
        corporations, prelude_cards, projects = setup_choices(update)
        # In any order: the server finds the Decision each card answers.
        gui.choose(update, [projects[3], prelude_cards[2], corporations[1], projects[0], prelude_cards[0]])
        after = gui.next_update()

    board = after["view"]["players"][player_deciding]
    assert board["choosing_corporation"]["picked"] == corporations[1]
    assert board["prelude_cards"]["kept"] == [prelude_cards[0], prelude_cards[2]]
    assert board["buying"]["bought"] == [projects[0], projects[3]]
    assert after["decision"]["player"] != player_deciding


def test_buying_no_project_cards_is_choosing_none():
    with connect() as gui:
        update = gui.start(["human", "human"], seed=5, prelude=True)
        corporations, prelude_cards, _ = setup_choices(update)
        gui.choose(update, [corporations[0], *prelude_cards[:2]])
        after = gui.next_update()

    assert after["view"]["players"][update["decision"]["player"]]["buying"]["bought"] == []
    assert after["decision"]["player"] != update["decision"]["player"]


def test_a_choice_that_falls_short_or_goes_too_far_is_refused_and_changes_nothing():
    with connect() as gui:
        update = gui.start(["human", "human"], seed=5, prelude=True)
        corporations, prelude_cards, projects = setup_choices(update)

        gui.choose(update, [corporations[0], prelude_cards[0]])
        assert "more" in gui.receive_error()
        gui.choose(update, [corporations[0], corporations[1], *prelude_cards[:2]])
        assert "can't be chosen" in gui.receive_error()
        gui.choose(update, [corporations[0], *prelude_cards[:2], "mars_university", projects[0]])
        assert "can't be chosen" in gui.receive_error()
        gui.send({"type": "choose_cards", "sequence": 99, "cards": [corporations[0]]})
        assert "stale" in gui.receive_error()
        gui.send({"type": "choose_cards", "sequence": 0, "cards": "corporation"})
        assert "list of card ids" in gui.receive_error()

        assert gui.save_replay()["replay"]["picks"] == []


def test_undo_takes_a_choice_back_whole():
    with connect() as gui:
        update = gui.start(["human", "human"], seed=5, prelude=True)
        corporations, prelude_cards, projects = setup_choices(update)
        gui.choose(update, [corporations[0], *prelude_cards[:2], *projects[:3]])
        gui.next_update()
        undone = gui.undo()

    assert undone["decision"] == update["decision"]


def test_a_draft_pick_answers_one_decision_only():
    with connect() as gui:
        update = gui.start(["human", "human"], seed=8)
        update = gui.skip_drafting_and_buying(update)
        for _ in range(2):
            gui.pick(update, "Pass")
            update = gui.wait_for_human()
        assert update["decision"]["kind"] == "draft"
        card = update["decision"]["options"][0]["details"]["card"]
        gui.choose(update, [card, update["decision"]["options"][1]["details"]["card"]])
        assert "can't be chosen" in gui.receive_error()
        gui.choose(update, [card])
        after = gui.next_update()

    assert after["view"]["players"][update["decision"]["player"]]["drafting"]["kept"] == [card]


def test_cards_looked_at_are_kept_at_once():
    with connect() as gui:
        update = gui.load(
            {
                "players": [player(hand=["business_contacts"]), player()],
                "deck": ["mine", "trees", "birds", "fish"],
            },
        )
        gui.pick(update, "Play Business Contacts")
        gui.choose(gui.wait_for_human(), ["fish", "trees"])
        after = gui.wait_for_human()

    assert after["view"]["players"][0]["hand"] == ["fish", "trees"]


def test_cards_are_sold_at_once():
    with connect() as gui:
        update = gui.load({"players": [player(megacredits=0, hand=["mine", "trees", "fish"]), player()]})
        gui.pick(update, "Sell Patents")
        gui.choose(gui.wait_for_human(), ["mine", "fish"])
        after = gui.next_update()

    assert after["view"]["players"][0]["hand"] == ["trees"]
    assert after["view"]["players"][0]["resources"]["megacredits"] == 2


def test_choosing_the_prelude_card_to_play_first_plays_that_one_only():
    with connect() as gui:
        update = gui.load(
            {
                "players": [player(prelude_cards=["donation", "loan"]), player()],
                "prelude": True,
                "ask_last_prelude_card": True,
            },
        )
        gui.choose(update, ["loan"])
        after = gui.wait_for_human()

    assert after["view"]["players"][0]["played_prelude_cards"] == ["loan"]
    assert [option["label"] for option in after["decision"]["options"]] == ["Play Donation"]


def test_a_new_game_with_a_human_asks_for_the_last_prelude_card():
    with connect() as gui:
        gui.start(["human", "random_bot"], seed=5, prelude=True)
        with_prelude = gui.save_replay()["replay"]["start"]["settings"]
        gui.start(["human", "random_bot"], seed=5)
        without = gui.save_replay()["replay"]["start"]["settings"]

    assert with_prelude["ask_last_prelude_card"] is True
    assert "ask_last_prelude_card" not in without
