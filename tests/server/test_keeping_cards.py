"""Cards that let a Player look at cards and keep some of them, over the WebSocket."""

from tests.helpers import player
from tests.server.helpers import connect


def test_a_human_playing_business_contacts_sees_the_cards_to_keep_and_keeps_two():
    scenario = {"players": [player(hand=["business_contacts"]), player()], "deck": ["mine", "trees", "birds", "fish"]}
    file = {"controllers": ["human", "random_bot"], "replay": {"start": {"scenario": scenario}, "picks": []}}
    with connect() as gui:
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        gui.pick(gui.wait_for_human(), "Play Business Contacts")
        looking = gui.wait_for_human()
        gui.pick(looking, "Keep Trees")
        gui.pick(gui.wait_for_human(), "Keep Fish")
        after = gui.wait_for_human()

    assert looking["decision"]["kind"] == "keep_cards"
    assert [option["details"] for option in looking["decision"]["options"]][:2] == [
        {"type": "keep_card", "card": "fish"},
        {"type": "keep_card", "card": "mine"},
    ]
    assert looking["view"]["players"][0]["keeping"]["looking_at"] == ["fish", "mine", "trees", "birds"]
    assert after["view"]["players"][0]["hand"] == ["fish", "trees"]
    assert "Player 1 keeps 2 cards and discards 2." in gui.log
