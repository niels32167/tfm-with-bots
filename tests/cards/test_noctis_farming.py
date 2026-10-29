"""#176 Noctis Farming (10 MegaCredits, building and plant Tags, 1 Victory Point): requires −20 °C
or warmer. Increase your MegaCredit Production 1 step and gain 2 plants."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_noctis_farming_needs_minus_20_degrees_or_warmer():
    assert not offered(scenario(player(hand=["noctis_farming"]), player(), temperature=-22), "Play Noctis Farming")
    assert offered(scenario(player(hand=["noctis_farming"]), player(), temperature=-20), "Play Noctis Farming")


def test_noctis_farming_raises_megacredit_production_by_1_and_gives_2_plants():
    game = scenario(player(megacredits=10, hand=["noctis_farming"]), player(), temperature=-20)

    pick(game, "Play Noctis Farming (10 MegaCredits)")

    assert production(game, 0)["megacredits"] == 1
    assert resources(game, 0)["plants"] == 2
    assert resources(game, 0)["megacredits"] == 0


def test_noctis_farming_is_worth_1_victory_point():
    game = scenario(player(played_cards=["noctis_farming"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
