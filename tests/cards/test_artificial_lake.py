"""#116 Artificial Lake (15 MegaCredits, building Tag, 1 Victory Point): requires -6 °C or warmer.
Place 1 Ocean Tile ON AN AREA NOT RESERVED FOR OCEAN."""

from tests.helpers import (
    LAND_AREAS,
    OCEAN_AREAS,
    area,
    areas_offered,
    city,
    final_scores,
    greenery,
    ocean,
    offered,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)


def test_artificial_lake_needs_minus_6_degrees_or_warmer():
    assert not offered(scenario(player(hand=["artificial_lake"]), player(), temperature=-8), "Play Artificial Lake")
    assert offered(scenario(player(hand=["artificial_lake"]), player(), temperature=-6), "Play Artificial Lake")


def test_artificial_lake_places_an_ocean_on_any_free_area_reserved_for_nothing():
    # Land next to the City on C3 is no exception: only Cities keep apart.
    tiles = [city("C3", owner=1), ocean("A2")]
    game = scenario(player(megacredits=15, hand=["artificial_lake"]), player(), temperature=-6, tiles=tiles)

    pick(game, "Play Artificial Lake (15 MegaCredits)")

    assert game.decision["kind"] == "area"
    assert areas_offered(game) == [name for name in LAND_AREAS if name != "C3"]
    assert offered(game, area="J1", on="land")
    pick(game, area="J1")  # 1 steel printed on it
    assert area(game, "J1")["tile"] == {"type": "ocean", "owner": None}
    assert game.player_view(0)["oceans"] == 2
    assert player_board(game, 0)["terraform_rating"] == 21
    assert resources(game, 0)["steel"] == 1
    assert "Player 1 places an Ocean on J1." in game.log
    assert game.decision["kind"] == "action"


def test_artificial_lakes_ocean_on_land_pays_the_adjacency_bonus_like_any_other_ocean():
    game = scenario(player(megacredits=40, hand=["artificial_lake"]), player(), temperature=-6)

    pick(game, "Play Artificial Lake")
    pick(game, area="C3")
    pick(game, "City (25 MegaCredits)")
    pick(game, area="C4")

    assert resources(game, 0)["megacredits"] == 40 - 15 - 25 + 2


def test_artificial_lakes_ocean_next_to_an_ocean_collects_2_megacredits_for_it():
    game = scenario(player(megacredits=15, hand=["artificial_lake"]), player(), temperature=-6, tiles=[ocean("A2")])

    pick(game, "Play Artificial Lake")
    pick(game, area="A1")  # 2 steel printed on it, and next to the Ocean on A2

    assert resources(game, 0)["steel"] == 2
    assert resources(game, 0)["megacredits"] == 2


def test_artificial_lake_is_not_offered_without_free_land():
    tiles = [greenery(name, owner=1) for name in LAND_AREAS]
    assert not offered(scenario(player(hand=["artificial_lake"]), player(), temperature=-6, tiles=tiles), "Play Artificial Lake")


def test_once_9_oceans_are_placed_artificial_lake_needs_no_free_land():
    tiles = [ocean(name) for name in OCEAN_AREAS[:9]] + [greenery(name, owner=1) for name in LAND_AREAS]
    assert offered(scenario(player(hand=["artificial_lake"]), player(), temperature=-6, tiles=tiles), "Play Artificial Lake")


def test_once_9_oceans_are_placed_artificial_lake_places_none():
    tiles = [ocean(name) for name in OCEAN_AREAS[:9]]
    game = scenario(player(hand=["artificial_lake"]), player(), temperature=-6, tiles=tiles)

    pick(game, "Play Artificial Lake")

    assert game.decision["kind"] == "action"
    assert game.player_view(0)["oceans"] == 9
    assert player_board(game, 0)["terraform_rating"] == 20


def test_artificial_lake_is_worth_1_victory_point():
    game = scenario(player(played_cards=["artificial_lake"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
