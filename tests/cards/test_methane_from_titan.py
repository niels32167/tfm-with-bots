"""#018 Methane from Titan (28 MegaCredits, space and jovian Tags, 2 Victory Points): requires 2 %
Oxygen. Increase your heat Production 2 steps and your plant Production 2 steps."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_methane_from_titan_needs_2_percent_oxygen():
    assert not offered(scenario(player(hand=["methane_from_titan"]), player(), oxygen=1), "Play Methane from Titan")
    assert offered(scenario(player(hand=["methane_from_titan"]), player(), oxygen=2), "Play Methane from Titan")


def test_methane_from_titan_raises_heat_and_plant_production_by_2_each():
    game = scenario(player(megacredits=28, hand=["methane_from_titan"]), player(), oxygen=2)

    pick(game, "Play Methane from Titan (28 MegaCredits)")

    assert production(game, 0)["heat"] == 2
    assert production(game, 0)["plants"] == 2
    assert resources(game, 0)["megacredits"] == 0


def test_methane_from_titan_is_worth_2_victory_points():
    game = scenario(player(played_cards=["methane_from_titan"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [2, 0]
