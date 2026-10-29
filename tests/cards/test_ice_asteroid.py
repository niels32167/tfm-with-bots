"""#078 Ice Asteroid (23 MegaCredits, Event and space Tags): place 2 Ocean Tiles."""

from tests.helpers import (
    OCEAN_AREAS,
    area,
    areas_offered,
    final_scores,
    ocean,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)


def test_ice_asteroid_places_2_oceans_one_after_the_other():
    game = scenario(player(megacredits=23, hand=["ice_asteroid"]), player())

    pick(game, "Play Ice Asteroid (23 MegaCredits)")
    pick(game, area="F6")
    assert game.decision["kind"] == "area"
    assert "F6" not in areas_offered(game)
    pick(game, area="F7")  # next to the Ocean on F6

    assert area(game, "F6")["tile"]["type"] == area(game, "F7")["tile"]["type"] == "ocean"
    assert player_board(game, 0)["terraform_rating"] == 22
    assert resources(game, 0)["megacredits"] == 2
    assert game.decision["kind"] == "action"


def test_with_8_oceans_placed_ice_asteroid_places_the_last_one():
    game = scenario(player(hand=["ice_asteroid"]), player(), tiles=[ocean(name) for name in OCEAN_AREAS[:8]])

    pick(game, "Play Ice Asteroid")
    pick(game, area=OCEAN_AREAS[8])

    assert game.player_view(0)["oceans"] == 9
    assert player_board(game, 0)["terraform_rating"] == 21
    assert "All 9 Oceans are already placed, so no Ocean is placed." in game.log
    assert game.decision["kind"] == "action"


def test_ice_asteroid_has_no_victory_points():
    game = scenario(player(played_cards=["ice_asteroid"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
