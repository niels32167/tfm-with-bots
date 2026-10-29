"""#082 Callisto Penal Mines (Corporate Era, 24 MegaCredits, space and jovian Tags, 2 Victory
Points): increase your MegaCredit Production 3 steps."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_callisto_penal_mines_raises_megacredit_production_by_3():
    game = scenario(player(megacredits=24, hand=["callisto_penal_mines"]), player())

    pick(game, "Play Callisto Penal Mines (24 MegaCredits)")

    assert production(game, 0)["megacredits"] == 3
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 raises their MegaCredit Production by 3." in game.log


def test_callisto_penal_mines_is_worth_2_victory_points():
    game = scenario(player(played_cards=["callisto_penal_mines"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [2, 0]
