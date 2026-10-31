"""Using the action of a played card over the WebSocket."""

from tests.helpers import player
from tests.server.helpers import connect


def test_a_human_uses_an_action_pays_for_it_with_titanium_and_places_its_ocean():
    using = player(megacredits=12, titanium=1, played_cards=["water_import_from_europa"])
    file = {
        "controllers": ["human", "random_bot"],
        "replay": {"start": {"scenario": {"players": [using, player()]}}, "picks": []},
    }
    with connect() as gui:
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        acting = gui.wait_for_human()
        gui.pick(acting, "Use the action of Water Import from Europa")
        paying = gui.wait_for_human()
        gui.pick(paying, "Pay 9 MegaCredits and 1 titanium")
        gui.pick(gui.wait_for_human(), "Place the Ocean on A2")
        after = gui.wait_for_human()

    assert {"type": "use_action", "card": "water_import_from_europa"} in [
        option["details"] for option in acting["decision"]["options"]
    ]
    assert paying["decision"]["kind"] == "payment"
    assert paying["decision"]["options"][1]["details"] == {
        "type": "payment",
        "card": "water_import_from_europa",
        "action": True,
        "megacredits": 9,
        "steel": 0,
        "titanium": 1,
    }
    assert after["view"]["players"][0]["used_actions"] == ["water_import_from_europa"]
    assert after["view"]["oceans"] == 1
    assert "Player 1 uses the action of Water Import from Europa." in gui.log


def test_a_human_chooses_how_much_energy_power_infrastructure_spends():
    using = player(megacredits=0, energy=2, played_cards=["power_infrastructure"])
    file = {
        "controllers": ["human", "random_bot"],
        "replay": {"start": {"scenario": {"players": [using, player()]}}, "picks": []},
    }
    with connect() as gui:
        gui.send({"type": "load_replay", "file": file, "bot_delay": 0})
        gui.pick(gui.wait_for_human(), "Use the action of Power Infrastructure")
        choosing = gui.wait_for_human()
        gui.pick(choosing, "Spend 2 energy to gain 2 MegaCredits")
        after = gui.wait_for_human()

    assert choosing["decision"]["kind"] == "resources"
    assert after["view"]["players"][0]["resources"]["megacredits"] == 2
