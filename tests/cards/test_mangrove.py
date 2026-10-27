"""#059 Mangrove (12 MegaCredits, plant Tag, 1 Victory Point): requires +4 °C or warmer. Place a
Greenery Tile ON AN AREA RESERVED FOR OCEAN and raise Oxygen 1 step. Disregard normal placement
restrictions for this."""

from tests.helpers import (
    OCEAN_AREAS,
    area,
    areas_offered,
    award,
    city,
    end_the_action_phase,
    final_scores,
    milestone,
    ocean,
    offered,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)


def test_mangrove_needs_4_degrees_or_warmer():
    assert not offered(scenario(player(hand=["mangrove"]), player(), temperature=2), "Play Mangrove")
    assert offered(scenario(player(hand=["mangrove"]), player(), temperature=4), "Play Mangrove")


def test_mangrove_places_a_greenery_on_any_free_area_reserved_for_oceans_whatever_is_next_to_it():
    # A Greenery would usually have to go next to the Player's City on C3.
    tiles = [city("C3", owner=0), ocean("A2"), ocean("E5")]
    game = scenario(player(megacredits=12, hand=["mangrove"]), player(), temperature=4, oxygen=5, tiles=tiles)

    pick(game, "Play Mangrove (12 MegaCredits)")

    assert game.decision["kind"] == "area"
    assert areas_offered(game) == [name for name in OCEAN_AREAS if name not in ("A2", "E5")]
    assert offered(game, area="E4", on="ocean_areas")
    pick(game, area="E4")  # 2 plants printed on it, and next to the Ocean on E5
    assert area(game, "E4")["tile"] == {"type": "greenery", "owner": 0}
    assert game.player_view(0)["oxygen"] == 6
    assert player_board(game, 0)["terraform_rating"] == 21
    assert resources(game, 0)["plants"] == 2
    assert resources(game, 0)["megacredits"] == 2
    assert "Player 1 places a Greenery on E4." in game.log
    assert game.decision["kind"] == "action"


def test_mangroves_greenery_is_the_players_own_for_milestones_awards_and_their_next_greenery():
    game = scenario(player(plants=8, hand=["mangrove"]), player(), temperature=4)

    pick(game, "Play Mangrove")
    pick(game, area="E4")
    pick(game, "Convert 8 plants")

    # A Greenery goes next to its owner's Tiles: E4's neighbours on land, but not E3 (Noctis City).
    assert areas_offered(game) == ["D3", "D4", "F3", "F4"]
    assert milestone(game, "gardener")["counts"] == [1, 0]
    assert award(game, "landlord")["counts"] == [1, 0]


def test_mangroves_greenery_scores_as_a_greenery_and_the_card_1_victory_point():
    game = scenario(player(hand=["mangrove"]), player(), **terraformed_mars())
    free_ocean_area = OCEAN_AREAS[9]

    pick(game, "Play Mangrove")
    pick(game, area=free_ocean_area)
    end_the_action_phase(game)

    assert [(score["greeneries"], score["cards"]) for score in final_scores(game)] == [(1, 1), (0, 0)]
