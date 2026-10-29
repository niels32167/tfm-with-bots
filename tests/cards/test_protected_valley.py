"""#174 Protected Valley (23 MegaCredits, building and plant Tags): increase your MegaCredit
Production 2 steps. Place a Greenery Tile ON AN AREA RESERVED FOR OCEAN, disregarding normal
placement restrictions, and increase Oxygen 1 step."""

from tests.helpers import (
    OCEAN_AREAS,
    area,
    areas_offered,
    city,
    final_scores,
    ocean,
    offered,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
    terraformed_mars,
)


def test_protected_valley_raises_megacredit_production_and_places_a_greenery_on_any_free_area_reserved_for_oceans():
    # A Greenery would usually have to go next to the Player's City on C3.
    tiles = [city("C3", owner=0), ocean("A2"), ocean("E5")]
    game = scenario(player(megacredits=23, hand=["protected_valley"]), player(), oxygen=5, tiles=tiles)

    pick(game, "Play Protected Valley (23 MegaCredits)")

    assert production(game, 0)["megacredits"] == 2
    assert resources(game, 0)["megacredits"] == 0
    assert game.decision["kind"] == "area"
    assert areas_offered(game) == [name for name in OCEAN_AREAS if name not in ("A2", "E5")]
    assert offered(game, area="E4", on="ocean_areas")
    pick(game, area="E4")  # 2 plants printed on it, and next to the Ocean on E5
    assert area(game, "E4")["tile"] == {"type": "greenery", "owner": 0}
    assert game.player_view(0)["oxygen"] == 6
    assert player_board(game, 0)["terraform_rating"] == 21
    assert resources(game, 0)["plants"] == 2
    assert resources(game, 0)["megacredits"] == 2
    assert game.decision["kind"] == "action"


def test_protected_valleys_greenery_scores_as_a_greenery_and_the_card_no_victory_points():
    game = scenario(player(hand=["protected_valley"]), player(), **terraformed_mars())
    free_ocean_area = OCEAN_AREAS[9]

    pick(game, "Play Protected Valley")
    pick(game, area=free_ocean_area)

    assert [(score["greeneries"], score["cards"]) for score in final_scores(game)] == [(1, 0), (0, 0)]
