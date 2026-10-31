"""#105 Earth Office (Corporate Era, 1 MegaCredit, Earth Tag): Effect: when you play an Earth card,
you pay 3 MegaCredits less for it."""

from tests.helpers import final_scores, offered, pick, player, resources, scenario, terraformed_mars


def test_earth_office_has_no_requirements_and_costs_1_megacredit():
    game = scenario(player(megacredits=1, hand=["earth_office"]), player())

    pick(game, "Play Earth Office (1 MegaCredit)")

    assert resources(game, 0)["megacredits"] == 0


def test_with_earth_office_a_card_with_an_earth_tag_costs_3_megacredits_less_and_others_do_not():
    game = scenario(player(megacredits=3, hand=["sponsors", "satellites"], played_cards=["earth_office"]), player())

    assert offered(game, "Play Sponsors (3 MegaCredits)", cost=3)
    assert not offered(game, "Play Satellites")
    pick(game, "Play Sponsors")
    assert resources(game, 0)["megacredits"] == 0


def test_earth_office_takes_a_cost_down_to_0_and_no_further():
    game = scenario(player(megacredits=0, hand=["investment_loan"], played_cards=["earth_office"]), player())

    pick(game, "Play Investment Loan (0 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 10
    assert "Player 1 plays Investment Loan, paying 0 MegaCredits." in game.log


def test_earth_office_is_worth_no_victory_points():
    game = scenario(player(played_cards=["earth_office"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
