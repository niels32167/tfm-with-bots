"""#068 Sponsors (Corporate Era, 6 MegaCredits, Earth Tag): increase your MegaCredit Production 2
steps."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_sponsors_raises_megacredit_production_by_2():
    game = scenario(player(megacredits=6, hand=["sponsors"]), player())

    pick(game, "Play Sponsors (6 MegaCredits)")

    assert production(game, 0)["megacredits"] == 2
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 raises their MegaCredit Production by 2." in game.log


def test_sponsors_is_worth_no_victory_points():
    game = scenario(player(played_cards=["sponsors"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
