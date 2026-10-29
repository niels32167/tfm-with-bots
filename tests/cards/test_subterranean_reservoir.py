"""#127 Subterranean Reservoir (11 MegaCredits, Event Tag): place 1 Ocean Tile."""

from tests.helpers import (
    OCEAN_AREAS,
    area,
    areas_offered,
    final_scores,
    ocean,
    offered,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)


def test_subterranean_reservoir_places_an_ocean():
    game = scenario(player(megacredits=11, hand=["subterranean_reservoir"]), player())

    pick(game, "Play Subterranean Reservoir (11 MegaCredits)")
    assert areas_offered(game) == OCEAN_AREAS
    pick(game, area="E5")

    assert area(game, "E5")["tile"] == {"type": "ocean", "owner": None}
    assert player_board(game, 0)["terraform_rating"] == 21
    assert resources(game, 0)["megacredits"] == 0
    assert game.decision["kind"] == "action"


def test_once_9_oceans_are_placed_subterranean_reservoir_is_still_offered_and_places_none():
    game = scenario(player(hand=["subterranean_reservoir"]), player(), tiles=[ocean(name) for name in OCEAN_AREAS[:9]])

    assert offered(game, "Play Subterranean Reservoir")
    pick(game, "Play Subterranean Reservoir")

    assert "All 9 Oceans are already placed, so no Ocean is placed." in game.log
    assert player_board(game, 0)["terraform_rating"] == 20
    assert game.decision["kind"] == "action"


def test_subterranean_reservoir_has_no_victory_points():
    game = scenario(player(played_cards=["subterranean_reservoir"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
