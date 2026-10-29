"""#117 Geothermal Power (11 MegaCredits, building and power Tags): increase your energy Production
2 steps."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_geothermal_power_raises_energy_production_by_2():
    game = scenario(player(megacredits=11, hand=["geothermal_power"]), player())

    pick(game, "Play Geothermal Power (11 MegaCredits)")

    assert production(game, 0)["energy"] == 2
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 raises their energy Production by 2." in game.log


def test_geothermal_power_is_worth_no_victory_points():
    game = scenario(player(played_cards=["geothermal_power"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
