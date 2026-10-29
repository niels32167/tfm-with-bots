"""#100 Fueled Generators (1 MegaCredit, building and power Tags): decrease your MegaCredit
Production 1 step and increase your energy Production 1 step."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_fueled_generators_trades_1_megacredit_production_for_1_energy_production():
    game = scenario(player(hand=["fueled_generators"]), player())

    pick(game, "Play Fueled Generators (1 MegaCredit)")

    assert production(game, 0)["megacredits"] == -1
    assert production(game, 0)["energy"] == 1
    assert "Player 1 raises their energy Production by 1." in game.log


def test_fueled_generators_cannot_take_megacredit_production_below_minus_5():
    at_minus_4 = scenario(player(hand=["fueled_generators"], production={"megacredits": -4}), player())
    at_minus_5 = scenario(player(hand=["fueled_generators"], production={"megacredits": -5}), player())

    assert offered(at_minus_4, "Play Fueled Generators")
    assert not offered(at_minus_5, "Play Fueled Generators")


def test_fueled_generators_is_worth_no_victory_points():
    game = scenario(player(played_cards=["fueled_generators"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
