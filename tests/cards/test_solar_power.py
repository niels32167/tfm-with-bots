"""#113 Solar Power (11 MegaCredits, building and power Tags, 1 Victory Point): increase your
energy Production 1 step."""

from tests.helpers import final_scores, pick, player, production, scenario, terraformed_mars


def test_solar_power_raises_energy_production_by_1():
    game = scenario(player(hand=["solar_power"]), player())

    pick(game, "Play Solar Power (11 MegaCredits)")

    assert production(game, 0)["energy"] == 1


def test_solar_power_is_worth_1_victory_point():
    game = scenario(player(played_cards=["solar_power"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
