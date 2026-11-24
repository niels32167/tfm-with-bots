"""A pick that shows its Player cards they couldn't see, such as drawing one, can't be taken back. The GUI asks for it
with `ask_before_drawing`, and the server then answers with what it would draw instead of picking."""

from tests.helpers import player
from tests.server.helpers import Gui, connect


def start_with(gui: Gui, *deck: str, **fields) -> dict:
    """A human's Turn with these cards on top of the deck, and the `fields` of their Player."""
    return gui.load({"players": [player(**fields), player()], "deck": list(deck)})


def ask(gui: Gui, update: dict, label: str) -> dict:
    """What the server answers when the GUI asks for the Option labelled `label`."""
    gui.pick(update, label, ask_before_drawing=True)
    return gui.receive()


def test_playing_a_card_that_draws_is_asked_first_and_then_drawn():
    with connect() as gui:
        update = start_with(gui, "mine", "trees", hand=["research"])
        asked = ask(gui, update, "Play Research")
        unchanged = gui.save_replay()["replay"]["picks"]
        gui.pick(update, "Play Research")
        after = gui.wait_for_human()

    index = next(o["index"] for o in update["decision"]["options"] if o["label"].startswith("Play Research"))
    assert asked == {
        "type": "confirm_pick",
        "sequence": update["decision"]["sequence"],
        "index": index,
        "label": "Draw 2 cards",
    }
    assert unchanged == []
    assert after["view"]["players"][0]["hand"] == ["mine", "trees"]


def test_a_placement_bonus_of_a_card_is_asked_first():
    with connect() as gui:
        update = start_with(gui, "mine", megacredits=23)
        gui.pick(update, "Greenery")
        areas = gui.wait_for_human()
        bonuses = {area["area"]: area["bonus"] for area in areas["view"]["board"]}
        draws = [o for o in areas["decision"]["options"] if bonuses[o["details"]["area"]].count("card") == 1]
        answered = ask(gui, areas, draws[0]["label"])

    assert answered["label"] == "Draw 1 card"


def test_looking_at_cards_is_asked_first():
    with connect() as gui:
        update = start_with(gui, "mine", "trees", "birds", "fish", hand=["business_contacts"])
        assert ask(gui, update, "Play Business Contacts")["label"] == "See the top 4 cards of the deck"
        update = start_with(gui, "mine", played_cards=["search_for_life"])
        assert ask(gui, update, "Search For Life")["label"] == "See the top card of the deck"


def test_a_pick_that_draws_nothing_is_picked_at_once():
    with connect() as gui:
        update = start_with(gui, megacredits=14)
        assert ask(gui, update, "Asteroid")["type"] == "update"


def test_passing_into_the_next_research_phase_is_not_asked():
    with connect() as gui:
        file = {
            "controllers": ["human", "human"],
            "replay": {
                "start": {"scenario": {"players": [player(), player(passed=True)], "draft": False}},
                "picks": [],
            },
        }
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        answered = ask(gui, gui.wait_for_human(), "Pass")

    assert answered["type"] == "update"
    assert answered["view"]["phase"] == "research"


def test_a_stale_or_unknown_pick_is_refused_as_ever():
    with connect() as gui:
        update = start_with(gui)
        gui.send({"type": "pick", "sequence": 9, "index": 0, "ask_before_drawing": True})
        assert "stale" in gui.receive_error()
        gui.send({"type": "pick", "sequence": update["decision"]["sequence"], "index": 99, "ask_before_drawing": True})
        assert "no Option 99" in gui.receive_error()
