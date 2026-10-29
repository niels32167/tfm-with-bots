"""#089 Peroxide Power (7 MegaCredits, building and power Tags): decrease your MegaCredit
Production 1 step and increase your energy Production 2 steps."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_peroxide_power_trades_1_megacredit_production_for_2_energy_production():
    game = scenario(player(hand=["peroxide_power"]), player())

    pick(game, "Play Peroxide Power (7 MegaCredits)")

    assert production(game, 0)["megacredits"] == -1
    assert production(game, 0)["energy"] == 2
    assert "Player 1 lowers their MegaCredit Production by 1." in game.log


def test_peroxide_power_cannot_take_megacredit_production_below_minus_5():
    at_minus_4 = scenario(player(hand=["peroxide_power"], production={"megacredits": -4}), player())
    at_minus_5 = scenario(player(hand=["peroxide_power"], production={"megacredits": -5}), player())

    assert offered(at_minus_4, "Play Peroxide Power")
    assert not offered(at_minus_5, "Play Peroxide Power")


def test_peroxide_power_is_worth_no_victory_points():
    game = scenario(player(played_cards=["peroxide_power"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
