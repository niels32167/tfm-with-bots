"""#P18 Martian Industries (Prelude Card, building Tag): increase your energy and steel Production 1
step. Gain 6 MegaCredits."""

from tests.helpers import player, player_board, production, resources, scenario


def test_martian_industries_raises_energy_and_steel_production_and_gains_6_megacredits():
    game = scenario(player(prelude_cards=["martian_industries"]), player(), prelude=True)

    assert (production(game, 0)["energy"], production(game, 0)["steel"]) == (1, 1)
    assert resources(game, 0)["megacredits"] == 48
    assert player_board(game, 0)["tags"]["building"] == 1
