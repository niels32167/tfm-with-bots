"""#106 Acquired Company (Corporate Era, 10 MegaCredits, Earth Tag): increase your MegaCredit
Production 3 steps."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_acquired_company_raises_megacredit_production_by_3():
    game = scenario(player(megacredits=10, hand=["acquired_company"]), player())

    pick(game, "Play Acquired Company (10 MegaCredits)")

    assert production(game, 0)["megacredits"] == 3
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 raises their MegaCredit Production by 3." in game.log


def test_acquired_company_is_worth_no_victory_points():
    game = scenario(player(played_cards=["acquired_company"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
