"""#093 Bushes (10 MegaCredits, plant Tag): requires -10 °C or warmer. Increase your plant
Production 2 steps. Gain 2 plants."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_bushes_needs_minus_10_degrees_or_warmer():
    assert not offered(scenario(player(hand=["bushes"]), player(), temperature=-12), "Play Bushes")
    assert offered(scenario(player(hand=["bushes"]), player(), temperature=-10), "Play Bushes")


def test_bushes_raises_plant_production_by_2_and_gives_2_plants():
    game = scenario(player(megacredits=10, hand=["bushes"]), player(), temperature=-10)

    pick(game, "Play Bushes (10 MegaCredits)")

    assert production(game, 0)["plants"] == 2
    assert resources(game, 0)["plants"] == 2
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 gains 2 plants." in game.log


def test_bushes_is_worth_no_victory_points():
    game = scenario(player(played_cards=["bushes"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
