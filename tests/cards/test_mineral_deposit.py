"""#062 Mineral Deposit (5 MegaCredits, Event Tag): gain 5 steel."""

from tests.helpers import final_scores, pick, player, resources, scenario, terraformed_mars


def test_mineral_deposit_gains_5_steel():
    game = scenario(player(megacredits=5, hand=["mineral_deposit"]), player())

    pick(game, "Play Mineral Deposit (5 MegaCredits)")

    assert resources(game, 0)["steel"] == 5
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 gains 5 steel." in game.log


def test_mineral_deposit_has_no_victory_points():
    game = scenario(player(played_cards=["mineral_deposit"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
