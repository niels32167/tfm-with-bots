"""#118 Farming (16 MegaCredits, plant Tag, 2 Victory Points): requires +4 °C or warmer. Increase
your MegaCredit Production 2 steps and your plant Production 2 steps. Gain 2 plants."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_farming_needs_plus_4_degrees_or_warmer():
    assert not offered(scenario(player(hand=["farming"]), player(), temperature=2), "Play Farming")
    assert offered(scenario(player(hand=["farming"]), player(), temperature=4), "Play Farming")


def test_farming_raises_megacredit_and_plant_production_by_2_and_gives_2_plants():
    game = scenario(player(megacredits=16, hand=["farming"]), player(), temperature=4)

    pick(game, "Play Farming (16 MegaCredits)")

    assert production(game, 0)["megacredits"] == 2
    assert production(game, 0)["plants"] == 2
    assert resources(game, 0)["plants"] == 2
    assert resources(game, 0)["megacredits"] == 0


def test_farming_is_worth_2_victory_points():
    game = scenario(player(played_cards=["farming"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [2, 0]
