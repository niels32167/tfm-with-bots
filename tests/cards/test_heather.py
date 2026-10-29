"""#088 Heather (6 MegaCredits, plant Tag): requires -14 °C or warmer. Increase your plant
Production 1 step. Gain 1 plant."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_heather_needs_minus_14_degrees_or_warmer():
    assert not offered(scenario(player(hand=["heather"]), player(), temperature=-16), "Play Heather")
    assert offered(scenario(player(hand=["heather"]), player(), temperature=-14), "Play Heather")


def test_heather_raises_plant_production_by_1_and_gives_1_plant():
    game = scenario(player(megacredits=6, hand=["heather"]), player(), temperature=-14)

    pick(game, "Play Heather (6 MegaCredits)")

    assert production(game, 0)["plants"] == 1
    assert resources(game, 0)["plants"] == 1
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 gains 1 plant." in game.log


def test_heather_is_worth_no_victory_points():
    game = scenario(player(played_cards=["heather"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
