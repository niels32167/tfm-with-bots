"""#P08 Donation (Prelude Card): gain 21 MegaCredits."""

from tests.helpers import player, player_board, resources, scenario


def test_donation_gains_21_megacredits():
    game = scenario(player(prelude_cards=["donation"]), player(), prelude=True)

    assert resources(game, 0)["megacredits"] == 63
    assert player_board(game, 0)["played_prelude_cards"] == ["donation"]
    assert "Player 1 gains 21 MegaCredits." in game.log
