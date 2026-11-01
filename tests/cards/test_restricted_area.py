"""#199 Restricted Area (Corporate Era, 11 MegaCredits, science Tag): Action: spend 2 MegaCredits to
draw a card. Place this Tile."""

from tests.helpers import (
    LAND_AREAS,
    area,
    areas_offered,
    final_scores,
    hand,
    offered,
    pick,
    player,
    resources,
    scenario,
    special,
    terraformed_mars,
)


def test_restricted_area_places_its_tile_on_any_free_land():
    game = scenario(player(megacredits=11, hand=["restricted_area"]), player())

    pick(game, "Play Restricted Area (11 MegaCredits)")

    assert areas_offered(game) == LAND_AREAS
    pick(game, "Place the Restricted Area Tile on H3")
    assert area(game, "H3")["tile"] == {
        "type": "special",
        "card": "restricted_area",
        "owner": 0,
    }
    assert "Player 1 places the Restricted Area Tile on H3." in game.log
    # H3 has a card for its placement bonus.
    assert len(hand(game, 0)) == 1


def test_restricted_areas_action_spends_2_megacredits_to_draw_a_card():
    tiles = [special("C4", "restricted_area", owner=0)]
    game = scenario(
        player(megacredits=3, played_cards=["restricted_area"]),
        player(),
        tiles=tiles,
        deck=["mine"],
    )

    pick(game, "Use the action of Restricted Area")

    assert resources(game, 0)["megacredits"] == 1
    assert hand(game, 0) == ["mine"]


def test_restricted_areas_action_needs_2_megacredits():
    tiles = [special("C4", "restricted_area", owner=0)]
    game = scenario(
        player(megacredits=1, played_cards=["restricted_area"]), player(), tiles=tiles
    )

    assert not offered(game, type="use_action")


def test_restricted_area_is_worth_no_victory_points():
    game = scenario(
        player(played_cards=["restricted_area"]), player(), **terraformed_mars()
    )

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
