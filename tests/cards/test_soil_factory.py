"""#179 Soil Factory (9 MegaCredits, building Tag, 1 Victory Point): decrease your energy
Production 1 step and increase your plant Production 1 step."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_soil_factory_needs_1_energy_production_to_lower():
    assert not offered(scenario(player(hand=["soil_factory"]), player()), "Play Soil Factory")


def test_soil_factory_trades_1_energy_production_for_1_plant_production():
    game = scenario(player(megacredits=9, hand=["soil_factory"], production={"energy": 1}), player())

    pick(game, "Play Soil Factory (9 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["plants"] == 1
    assert resources(game, 0)["megacredits"] == 0


def test_soil_factory_is_worth_1_victory_point():
    game = scenario(player(played_cards=["soil_factory"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
