"""#159 Lichen (7 MegaCredits, plant Tag): requires −24 °C or warmer. Increase your plant
Production 1 step."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_lichen_needs_minus_24_degrees_or_warmer():
    assert not offered(scenario(player(hand=["lichen"]), player(), temperature=-26), "Play Lichen")
    assert offered(scenario(player(hand=["lichen"]), player(), temperature=-24), "Play Lichen")


def test_lichen_raises_plant_production_by_1():
    game = scenario(player(megacredits=7, hand=["lichen"]), player(), temperature=-24)

    pick(game, "Play Lichen (7 MegaCredits)")

    assert production(game, 0)["plants"] == 1
    assert resources(game, 0)["megacredits"] == 0


def test_lichen_is_worth_no_victory_points():
    game = scenario(player(played_cards=["lichen"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
