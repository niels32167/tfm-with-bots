"""#142 Mohole Area (20 MegaCredits, building Tag): increase your heat Production 4 steps. Place this
Tile ON AN AREA RESERVED FOR OCEAN."""

from tests.helpers import (
    OCEAN_AREAS,
    area,
    areas_offered,
    final_scores,
    ocean,
    pick,
    player,
    production,
    scenario,
    special,
    terraformed_mars,
)


def test_mohole_area_raises_heat_production_4_steps_and_places_its_tile_on_a_free_ocean_area():
    game = scenario(
        player(megacredits=20, hand=["mohole_area"]), player(), tiles=[ocean("A2")]
    )

    pick(game, "Play Mohole Area (20 MegaCredits)")

    assert production(game, 0)["heat"] == 4
    assert areas_offered(game) == OCEAN_AREAS[1:]
    pick(game, "Place the Mohole Area Tile on A4")
    assert area(game, "A4")["tile"] == {
        "type": "special",
        "card": "mohole_area",
        "owner": 0,
    }
    assert game.decision["kind"] == "action"


def test_mohole_areas_tile_is_no_ocean_and_takes_an_ocean_area():
    tiles = [special("A4", "mohole_area", owner=0)]
    game = scenario(player(megacredits=18), player(), tiles=tiles)

    pick(game, "Aquifer")

    assert game.player_view(0)["oceans"] == 0
    assert "A4" not in areas_offered(game)


def test_mohole_area_is_worth_no_victory_points():
    game = scenario(
        player(played_cards=["mohole_area"]), player(), **terraformed_mars()
    )

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
