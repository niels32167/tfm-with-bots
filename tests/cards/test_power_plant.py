"""#141 Power Plant (4 MegaCredits, building and power Tags): increase your energy Production 1 step."""

from tests.helpers import pick, player, production, resources, scenario


def test_power_plant_raises_energy_production_by_1():
    game = scenario(player(megacredits=4, hand=["power_plant"]), player())

    pick(game, "Play Power Plant (4 MegaCredits)")

    assert production(game, 0)["energy"] == 1
    assert resources(game, 0)["megacredits"] == 0


def test_the_power_plant_card_is_not_the_standard_project():
    game = scenario(player(hand=["power_plant"]), player())

    pick(game, "Play Power Plant")

    assert "Player 1 plays Power Plant, paying 4 MegaCredits." in game.log
    assert not any("Standard Project" in line for line in game.log)
