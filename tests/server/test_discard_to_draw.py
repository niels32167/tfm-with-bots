"""Mars University's discard-to-draw Decision over the WebSocket."""

from tests.helpers import player
from tests.server.helpers import connect


def test_a_human_discards_a_card_with_mars_university_and_draws_one():
    playing = player(megacredits=8, hand=["mars_university", "mine"])
    scenario = {"players": [playing, player()], "deck": ["sponsors"]}
    file = {"controllers": ["human", "random_bot"], "replay": {"start": {"scenario": scenario}, "picks": []}}
    with connect() as gui:
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        gui.pick(gui.wait_for_human(), "Play Mars University")
        discarding = gui.wait_for_human()
        gui.pick(discarding, "Discard Mine to draw a card")
        after = gui.wait_for_human()

    assert discarding["decision"]["kind"] == "discard_to_draw"
    assert [option["details"] for option in discarding["decision"]["options"]] == [
        {"type": "discard_card", "card": "mine"},
        {"type": "done"},
    ]
    assert after["view"]["players"][0]["hand"] == ["sponsors"]
    assert "Player 1 discards a card to draw one." in gui.log
