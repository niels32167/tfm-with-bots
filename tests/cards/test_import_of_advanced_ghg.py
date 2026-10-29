"""#167 Import of Advanced GHG (9 MegaCredits, Event, space and Earth Tags): increase your heat
Production 2 steps."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_import_of_advanced_ghg_raises_heat_production_by_2():
    game = scenario(player(megacredits=9, hand=["import_of_advanced_ghg"]), player())

    pick(game, "Play Import of Advanced GHG (9 MegaCredits)")

    assert production(game, 0)["heat"] == 2
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 raises their heat Production by 2." in game.log


def test_import_of_advanced_ghg_has_no_victory_points():
    game = scenario(player(played_cards=["import_of_advanced_ghg"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
