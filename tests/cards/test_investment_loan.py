"""#151 Investment Loan (3 MegaCredits, Event and Earth Tags): decrease your MegaCredit
Production 1 step. Gain 10 MegaCredits."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_investment_loan_trades_1_megacredit_production_for_10_megacredits():
    game = scenario(player(megacredits=3, hand=["investment_loan"]), player())

    pick(game, "Play Investment Loan (3 MegaCredits)")

    assert production(game, 0)["megacredits"] == -1
    assert resources(game, 0)["megacredits"] == 10
    assert "Player 1 lowers their MegaCredit Production by 1." in game.log


def test_investment_loan_cannot_take_megacredit_production_below_minus_5():
    at_minus_4 = scenario(player(hand=["investment_loan"], production={"megacredits": -4}), player())
    at_minus_5 = scenario(player(hand=["investment_loan"], production={"megacredits": -5}), player())

    assert offered(at_minus_4, "Play Investment Loan")
    assert not offered(at_minus_5, "Play Investment Loan")


def test_investment_loan_has_no_victory_points():
    game = scenario(player(played_cards=["investment_loan"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
