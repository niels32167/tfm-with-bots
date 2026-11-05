"""Card Resources over the WebSocket: the view shows them, and a human picks the card they go on."""

from tests.helpers import player
from tests.server.helpers import connect


def test_a_human_picks_the_card_that_gets_the_microbes():
    playing = player(
        megacredits=26,
        hand=["aerobraked_ammonia_asteroid"],
        played_cards=["tardigrades", "regolith_eaters"],
        card_resources={"tardigrades": 1},
    )
    scenario = {"players": [playing, player()]}
    file = {
        "controllers": ["human", "random_bot"],
        "replay": {"start": {"scenario": scenario}, "picks": []},
    }
    with connect() as gui:
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        gui.pick(gui.wait_for_human(), "Play Aerobraked Ammonia Asteroid")
        adding = gui.wait_for_human()
        gui.pick(adding, "Add 2 microbes to Tardigrades")
        after = gui.wait_for_human()

    assert adding["decision"]["kind"] == "add_to_card"
    assert adding["decision"]["options"][0]["details"] == {
        "type": "add_card_resources",
        "card": "aerobraked_ammonia_asteroid",
        "to": "regolith_eaters",
        "kind": "microbe",
        "amount": 2,
    }
    assert after["view"]["players"][0]["card_resources"] == {
        "regolith_eaters": 0,
        "tardigrades": 3,
    }
    assert "Player 1 adds 2 microbes to Tardigrades." in gui.log


def test_a_human_moves_a_microbe_with_ants_from_a_card_picked():
    playing = player(played_cards=["ants"])
    holding = player(
        played_cards=["tardigrades", "regolith_eaters"],
        card_resources={"tardigrades": 2, "regolith_eaters": 1},
    )
    scenario = {"players": [playing, holding]}
    file = {
        "controllers": ["human", "random_bot"],
        "replay": {"start": {"scenario": scenario}, "picks": []},
    }
    with connect() as gui:
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        gui.pick(gui.wait_for_human(), "Use the action of Ants")
        moving = gui.wait_for_human()
        gui.pick(moving, "Remove 1 microbe from Player 2's Tardigrades")
        after = gui.wait_for_human()

    assert moving["decision"]["kind"] == "target"
    assert after["view"]["players"][0]["card_resources"] == {"ants": 1}
    assert after["view"]["players"][1]["card_resources"] == {
        "regolith_eaters": 1,
        "tardigrades": 1,
    }


def test_a_human_chooses_what_an_action_does():
    playing = player(
        played_cards=["regolith_eaters"], card_resources={"regolith_eaters": 2}
    )
    scenario = {"players": [playing, player()]}
    file = {
        "controllers": ["human", "random_bot"],
        "replay": {"start": {"scenario": scenario}, "picks": []},
    }
    with connect() as gui:
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        gui.pick(gui.wait_for_human(), "Use the action of Regolith Eaters")
        choosing = gui.wait_for_human()
        gui.pick(
            choosing, "Remove 2 microbes from Regolith Eaters to raise Oxygen 1 step"
        )
        after = gui.wait_for_human()

    assert choosing["decision"]["kind"] == "effects"
    assert after["view"]["oxygen"] == 1
    assert after["view"]["players"][0]["card_resources"] == {"regolith_eaters": 0}


def test_a_human_orders_olympus_conference_and_mars_university():
    playing = player(
        megacredits=13,
        hand=["regolith_eaters", "mine"],
        played_cards=["mars_university", "olympus_conference"],
        card_resources={"olympus_conference": 1},
    )
    scenario = {"players": [playing, player()], "deck": ["sponsors"]}
    file = {
        "controllers": ["human", "random_bot"],
        "replay": {"start": {"scenario": scenario}, "picks": []},
    }
    with connect() as gui:
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        gui.pick(gui.wait_for_human(), "Play Regolith Eaters")
        both = gui.wait_for_human()
        gui.pick(both, "Discard Mine to draw a card")
        then = gui.wait_for_human()
        gui.pick(then, "Add 1 science to Olympus Conference")
        after = gui.wait_for_human()

    assert both["decision"]["kind"] == "olympus_conference"
    assert then["decision"]["kind"] == "olympus_conference"
    assert after["view"]["players"][0]["hand"] == ["sponsors"]
    assert after["view"]["players"][0]["card_resources"]["olympus_conference"] == 2


def test_a_human_chooses_what_a_card_played_does():
    playing = player(
        megacredits=1, heat=5, hand=["local_heat_trapping"], played_cards=["fish"]
    )
    scenario = {"players": [playing, player()]}
    file = {
        "controllers": ["human", "random_bot"],
        "replay": {"start": {"scenario": scenario}, "picks": []},
    }
    with connect() as gui:
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        gui.pick(gui.wait_for_human(), "Play Local Heat Trapping")
        choosing = gui.wait_for_human()
        gui.pick(choosing, "Add 2 animals to another card")
        after = gui.wait_for_human()

    assert choosing["decision"]["kind"] == "effects"
    assert after["view"]["players"][0]["card_resources"] == {"fish": 2}


def test_a_human_removes_animals_with_virus_from_a_card_picked():
    playing = player(megacredits=1, hand=["virus"])
    holding = player(played_cards=["fish"], card_resources={"fish": 3})
    scenario = {"players": [playing, holding]}
    file = {
        "controllers": ["human", "random_bot"],
        "replay": {"start": {"scenario": scenario}, "picks": []},
    }
    with connect() as gui:
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        gui.pick(gui.wait_for_human(), "Play Virus")
        removing = gui.wait_for_human()
        gui.pick(removing, "Remove 2 animals from Player 2's Fish")
        after = gui.wait_for_human()

    assert removing["decision"]["kind"] == "target"
    assert removing["decision"]["options"][0]["details"] == {
        "type": "remove_card_resources",
        "card": "virus",
        "player": 1,
        "from": "fish",
        "kind": "animal",
        "amount": 2,
    }
    assert after["view"]["players"][1]["card_resources"] == {"fish": 1}


def test_a_human_chooses_what_viral_enhancers_does():
    playing = player(
        megacredits=4, hand=["tardigrades"], played_cards=["viral_enhancers"]
    )
    scenario = {"players": [playing, player()]}
    file = {
        "controllers": ["human", "random_bot"],
        "replay": {"start": {"scenario": scenario}, "picks": []},
    }
    with connect() as gui:
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        gui.pick(gui.wait_for_human(), "Play Tardigrades")
        choosing = gui.wait_for_human()
        gui.pick(choosing, "Gain 1 plant")
        after = gui.wait_for_human()

    assert choosing["decision"]["kind"] == "viral_enhancers"
    assert after["view"]["players"][0]["resources"]["plants"] == 1
