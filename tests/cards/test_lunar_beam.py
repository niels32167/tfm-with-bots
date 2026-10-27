"""#030 Lunar Beam (13 MegaCredits, power and earth Tags): decrease your MegaCredit Production 2
steps and increase your heat Production and energy Production 2 steps each."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_lunar_beam_trades_2_megacredit_production_for_2_heat_and_2_energy_production():
    game = scenario(player(hand=["lunar_beam"]), player())

    pick(game, "Play Lunar Beam (13 MegaCredits)")

    assert production(game, 0)["megacredits"] == -2
    assert production(game, 0)["heat"] == 2
    assert production(game, 0)["energy"] == 2


def test_lunar_beam_cannot_take_megacredit_production_below_minus_5():
    at_minus_3 = scenario(player(hand=["lunar_beam"], production={"megacredits": -3}), player())
    at_minus_4 = scenario(player(hand=["lunar_beam"], production={"megacredits": -4}), player())

    assert offered(at_minus_3, "Play Lunar Beam")
    assert not offered(at_minus_4, "Play Lunar Beam")


def test_lunar_beam_is_worth_no_victory_points():
    game = scenario(player(played_cards=["lunar_beam"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
