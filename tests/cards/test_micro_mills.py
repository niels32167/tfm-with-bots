"""#164 Micro-Mills (3 MegaCredits, no Tags): increase your heat Production 1 step."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_micro_mills_raises_heat_production_by_1():
    game = scenario(player(megacredits=3, hand=["micro_mills"]), player())

    pick(game, "Play Micro-Mills (3 MegaCredits)")

    assert production(game, 0)["heat"] == 1
    assert resources(game, 0)["megacredits"] == 0


def test_micro_mills_is_worth_no_victory_points():
    game = scenario(player(played_cards=["micro_mills"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
