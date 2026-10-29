"""#169 Tundra Farming (16 MegaCredits, plant Tag, 2 Victory Points): requires −6 °C or warmer.
Increase your plant Production 1 step and your MegaCredit Production 2 steps. Gain 1 plant."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_tundra_farming_needs_minus_6_degrees_or_warmer():
    assert not offered(scenario(player(hand=["tundra_farming"]), player(), temperature=-8), "Play Tundra Farming")
    assert offered(scenario(player(hand=["tundra_farming"]), player(), temperature=-6), "Play Tundra Farming")


def test_tundra_farming_raises_plant_and_megacredit_production_and_gives_1_plant():
    game = scenario(player(megacredits=16, hand=["tundra_farming"]), player(), temperature=-6)

    pick(game, "Play Tundra Farming (16 MegaCredits)")

    assert production(game, 0)["plants"] == 1
    assert production(game, 0)["megacredits"] == 2
    assert resources(game, 0)["plants"] == 1
    assert resources(game, 0)["megacredits"] == 0


def test_tundra_farming_is_worth_2_victory_points():
    game = scenario(player(played_cards=["tundra_farming"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [2, 0]
