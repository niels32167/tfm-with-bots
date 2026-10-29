"""#203 Soletta (35 MegaCredits, space Tag): increase your heat Production 7 steps."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_soletta_raises_heat_production_by_7():
    game = scenario(player(megacredits=35, hand=["soletta"]), player())

    pick(game, "Play Soletta (35 MegaCredits)")

    assert production(game, 0)["heat"] == 7
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 raises their heat Production by 7." in game.log


def test_soletta_is_worth_no_victory_points():
    game = scenario(player(played_cards=["soletta"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
