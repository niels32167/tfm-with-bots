"""#045 Nuclear Power (10 MegaCredits, building and power Tags): decrease your MegaCredit
Production 2 steps and increase your energy Production 3 steps."""

from tests.helpers import offered, pick, player, production, scenario


def test_nuclear_power_trades_2_megacredit_production_for_3_energy_production():
    game = scenario(player(hand=["nuclear_power"]), player())

    pick(game, "Play Nuclear Power (10 MegaCredits)")

    assert production(game, 0)["megacredits"] == -2
    assert production(game, 0)["energy"] == 3
    assert "Player 1 lowers their MegaCredit Production by 2." in game.log


def test_nuclear_power_cannot_take_megacredit_production_below_minus_5():
    at_minus_3 = scenario(player(hand=["nuclear_power"], production={"megacredits": -3}), player())
    at_minus_4 = scenario(player(hand=["nuclear_power"], production={"megacredits": -4}), player())

    assert offered(at_minus_3, "Play Nuclear Power")
    assert not offered(at_minus_4, "Play Nuclear Power")
