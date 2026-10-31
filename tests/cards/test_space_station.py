"""#025 Space Station (Corporate Era, 10 MegaCredits, space Tag, 1 Victory Point): Effect: when you
play a Space card, you pay 2 MegaCredits less for it."""

from tests.helpers import final_scores, offered, pick, player, resources, scenario, terraformed_mars


def test_space_station_has_no_requirements_and_costs_10_megacredits():
    game = scenario(player(megacredits=10, hand=["space_station"]), player())

    pick(game, "Play Space Station (10 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0


def test_with_space_station_a_card_with_a_space_tag_costs_2_megacredits_less_and_others_do_not():
    game = scenario(player(megacredits=8, hand=["satellites", "sponsors"], played_cards=["space_station"]), player())

    assert offered(game, "Play Satellites (8 MegaCredits)", cost=8)
    assert offered(game, "Play Sponsors (6 MegaCredits)", cost=6)
    pick(game, "Play Satellites")
    assert resources(game, 0)["megacredits"] == 0


def test_space_station_makes_an_event_with_a_space_tag_cheaper_too():
    game = scenario(player(megacredits=21, hand=["ice_asteroid"], played_cards=["space_station"]), player())

    assert offered(game, "Play Ice Asteroid (21 MegaCredits)")


def test_space_station_does_not_make_itself_cheaper():
    assert not offered(scenario(player(megacredits=9, hand=["space_station"]), player()), "Play Space Station")


def test_space_station_is_worth_1_victory_point():
    game = scenario(player(played_cards=["space_station"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
