"""#P27 Power Generation (Prelude Card, power Tag): increase your energy Production 3 steps."""

from tests.helpers import player, player_board, production, scenario


def test_power_generation_raises_energy_production_by_3():
    game = scenario(player(prelude_cards=["power_generation"]), player(), prelude=True)

    assert production(game, 0)["energy"] == 3
    assert player_board(game, 0)["tags"]["power"] == 1
