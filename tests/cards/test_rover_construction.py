"""#038 Rover Construction (8 MegaCredits, building Tag, 1 Victory Point): Effect: when any City Tile
is placed, gain 2 MegaCredits."""

from tests.helpers import final_scores, pick, player, resources, scenario, terraformed_mars


def test_rover_construction_has_no_requirements_and_costs_8_megacredits():
    game = scenario(player(megacredits=8, hand=["rover_construction"]), player())

    pick(game, "Play Rover Construction (8 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0


def test_with_rover_construction_its_player_gains_2_megacredits_for_their_own_city():
    game = scenario(player(megacredits=25, played_cards=["rover_construction"]), player())

    pick(game, "City (25 MegaCredits)")
    pick(game, "Place the City on C3")

    assert resources(game, 0)["megacredits"] == 2
    assert "Player 1's Rover Construction takes effect." in game.log


def test_with_rover_construction_its_player_gains_2_megacredits_for_another_players_city_too():
    game = scenario(player(megacredits=25), player(megacredits=0, played_cards=["rover_construction"]))

    pick(game, "City (25 MegaCredits)")
    pick(game, "Place the City on C3")

    assert resources(game, 1)["megacredits"] == 2


def test_rover_construction_gives_nothing_for_a_greenery_or_an_ocean():
    game = scenario(player(megacredits=41, played_cards=["rover_construction"]), player())

    pick(game, "Aquifer")
    pick(game, "Place the Ocean on A4")
    pick(game, "Greenery")
    pick(game, "Place the Greenery on C3")

    assert resources(game, 0)["megacredits"] == 0


def test_rover_construction_is_worth_1_victory_point():
    game = scenario(player(played_cards=["rover_construction"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
