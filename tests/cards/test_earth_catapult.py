"""#070 Earth Catapult (Corporate Era, 23 MegaCredits, Earth Tag, 2 Victory Points): Effect: when you
play a card, you pay 2 MegaCredits less for it."""

from tests.helpers import final_scores, offered, pick, player, resources, scenario, terraformed_mars


def test_earth_catapult_has_no_requirements_and_costs_23_megacredits():
    game = scenario(player(megacredits=23, hand=["earth_catapult"]), player())

    pick(game, "Play Earth Catapult (23 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0


def test_with_earth_catapult_every_card_costs_2_megacredits_less():
    game = scenario(
        player(megacredits=4, hand=["mine", "sponsors", "bribed_committee"], played_cards=["earth_catapult"]), player()
    )

    assert offered(game, "Play Mine (2 MegaCredits)")
    assert offered(game, "Play Sponsors (4 MegaCredits)")
    assert not offered(game, "Play Bribed Committee")
    pick(game, "Play Sponsors")
    assert resources(game, 0)["megacredits"] == 0


def test_earth_catapult_is_worth_2_victory_points():
    game = scenario(player(played_cards=["earth_catapult"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [2, 0]
