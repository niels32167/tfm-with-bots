"""#P17 Loan (Prelude Card): gain 30 MegaCredits. Decrease your MegaCredit Production 2 steps."""

from tests.helpers import player, player_board, production, resources, scenario


def test_loan_gains_30_megacredits_and_lowers_megacredit_production_by_2():
    game = scenario(player(prelude_cards=["loan"]), player(), prelude=True)

    assert resources(game, 0)["megacredits"] == 72
    assert production(game, 0)["megacredits"] == -2


def test_with_megacredit_production_at_minus_4_it_cant_be_played_and_is_discarded_for_15_megacredits():
    game = scenario(player(prelude_cards=["loan"], production={"megacredits": -4}), player(), prelude=True)

    assert resources(game, 0)["megacredits"] == 57
    assert production(game, 0)["megacredits"] == -4
    assert player_board(game, 0)["played_prelude_cards"] == []
    assert "Player 1 can't play Loan, so they discard it and gain 15 MegaCredits." in game.log
