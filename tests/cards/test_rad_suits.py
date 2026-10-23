"""#186 Rad-Suits (6 MegaCredits, no Tags, 1 Victory Point): requires two Cities in play.
Increase your MegaCredit Production 1 step."""

from tests.helpers import city, final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_rad_suits_needs_2_cities_in_play_whoever_owns_them():
    one_city = scenario(player(hand=["rad_suits"]), player(), tiles=[city("A1", 1)])
    two_cities = scenario(player(hand=["rad_suits"]), player(), tiles=[city("A1", 1), city("J1", 1)])

    assert not offered(one_city, "Play Rad-Suits")
    assert offered(two_cities, "Play Rad-Suits")


def test_rad_suits_raises_megacredit_production_by_1():
    game = scenario(player(hand=["rad_suits"]), player(), tiles=[city("A1", 0), city("J1", 1)])

    pick(game, "Play Rad-Suits")

    assert production(game, 0)["megacredits"] == 1


def test_rad_suits_is_worth_1_victory_point():
    game = scenario(player(played_cards=["rad_suits"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
