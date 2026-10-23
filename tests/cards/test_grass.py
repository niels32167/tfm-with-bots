"""#087 Grass (11 MegaCredits, plant Tag): requires -16 °C or warmer. Increase your plant
Production 1 step. Gain 3 plants."""

from tests.helpers import offered, pick, player, production, resources, scenario


def test_grass_needs_minus_16_degrees_or_warmer():
    assert not offered(scenario(player(hand=["grass"]), player(), temperature=-18), "Play Grass")
    assert offered(scenario(player(hand=["grass"]), player(), temperature=-16), "Play Grass")


def test_grass_raises_plant_production_by_1_and_gives_3_plants():
    game = scenario(player(hand=["grass"]), player(), temperature=-16)

    pick(game, "Play Grass (11 MegaCredits)")

    assert production(game, 0)["plants"] == 1
    assert resources(game, 0)["plants"] == 3
    assert "Player 1 gains 3 plants." in game.log
