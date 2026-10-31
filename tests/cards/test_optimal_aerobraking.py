"""#031 Optimal Aerobraking (7 MegaCredits, space Tag): Effect: when you play a Space Event, you gain
3 MegaCredits and 3 heat."""

from tests.helpers import final_scores, pick, player, resources, scenario, terraformed_mars


def test_optimal_aerobraking_has_no_requirements_and_costs_7_megacredits():
    game = scenario(player(megacredits=7, hand=["optimal_aerobraking"]), player())

    pick(game, "Play Optimal Aerobraking (7 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert resources(game, 0)["heat"] == 0


def test_with_optimal_aerobraking_an_event_with_a_space_tag_gains_3_megacredits_and_3_heat():
    game = scenario(player(megacredits=23, hand=["ice_asteroid"], played_cards=["optimal_aerobraking"]), player())

    pick(game, "Play Ice Asteroid")

    assert resources(game, 0)["megacredits"] == 3
    assert resources(game, 0)["heat"] == 3
    assert "Player 1's Optimal Aerobraking takes effect." in game.log


def test_optimal_aerobraking_gives_nothing_for_an_event_without_a_space_tag_or_a_space_card_that_is_no_event():
    holding = player(megacredits=17, hand=["bribed_committee", "satellites"], played_cards=["optimal_aerobraking"])
    game = scenario(holding, player())

    pick(game, "Play Bribed Committee")
    pick(game, "Play Satellites")

    assert resources(game, 0)["megacredits"] == 0
    assert resources(game, 0)["heat"] == 0


def test_optimal_aerobraking_gives_nothing_for_another_players_space_event():
    game = scenario(player(megacredits=23, hand=["ice_asteroid"]), player(played_cards=["optimal_aerobraking"]))

    pick(game, "Play Ice Asteroid")

    assert resources(game, 1)["heat"] == 0


def test_optimal_aerobraking_is_worth_no_victory_points():
    game = scenario(player(played_cards=["optimal_aerobraking"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
