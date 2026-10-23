"""#060 Trees (13 MegaCredits, plant Tag, 1 Victory Point): requires -4 °C or warmer.
Increase your plant Production 3 steps. Gain 1 plant."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_trees_needs_minus_4_degrees_or_warmer():
    assert not offered(scenario(player(hand=["trees"]), player(), temperature=-6), "Play Trees")
    assert offered(scenario(player(hand=["trees"]), player(), temperature=-4), "Play Trees")


def test_trees_raises_plant_production_by_3_and_gives_1_plant():
    game = scenario(player(megacredits=13, hand=["trees"]), player(), temperature=-4)

    pick(game, "Play Trees (13 MegaCredits)")

    assert production(game, 0)["plants"] == 3
    assert resources(game, 0)["plants"] == 1
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 gains 1 plant." in game.log


def test_trees_is_worth_1_victory_point():
    game = scenario(player(played_cards=["trees"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
