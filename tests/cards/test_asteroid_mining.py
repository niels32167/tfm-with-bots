"""#040 Asteroid Mining (30 MegaCredits, space and jovian Tags, 2 Victory Points): increase your
titanium Production 2 steps."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_asteroid_mining_has_no_requirement_and_raises_titanium_production_by_2():
    game = scenario(player(megacredits=30, hand=["asteroid_mining"]), player())

    pick(game, "Play Asteroid Mining (30 MegaCredits)")

    assert production(game, 0)["titanium"] == 2
    assert resources(game, 0)["megacredits"] == 0


def test_asteroid_mining_is_worth_2_victory_points():
    game = scenario(player(played_cards=["asteroid_mining"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [2, 0]
