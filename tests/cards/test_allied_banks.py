"""#P01 Allied Banks (Prelude Card, Earth Tag): increase your MegaCredit Production 4 steps. Gain 3 MegaCredits."""

from tests.helpers import player, player_board, production, resources, scenario


def test_allied_banks_raises_megacredit_production_by_4_and_gains_3_megacredits():
    game = scenario(player(prelude_cards=["allied_banks"]), player(), prelude=True)

    assert production(game, 0)["megacredits"] == 4
    assert resources(game, 0)["megacredits"] == 45
    assert player_board(game, 0)["played_prelude_cards"] == ["allied_banks"]
    assert player_board(game, 0)["tags"]["earth"] == 1
    assert "Player 1 plays Allied Banks." in game.log
