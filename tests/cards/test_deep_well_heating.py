"""#003 Deep Well Heating (13 MegaCredits, building and power Tags): increase your energy
Production 1 step. Raise Temperature 1 step."""

from tests.helpers import pick, player, player_board, production, scenario


def test_deep_well_heating_raises_energy_production_and_temperature():
    game = scenario(player(hand=["deep_well_heating"]), player(), temperature=-26)

    pick(game, "Play Deep Well Heating")

    assert production(game, 0)["energy"] == 1
    assert game.player_view(0)["temperature"] == -24
    assert player_board(game, 0)["terraform_rating"] == 21
    assert production(game, 0)["heat"] == 1  # the bonus at -24 °C
