"""#097 Nuclear Zone (10 MegaCredits, Earth Tag): place this Tile and raise Temperature 2 steps.
−2 Victory Points."""

from tests.helpers import (
    LAND_AREAS,
    area,
    areas_offered,
    city,
    final_scores,
    pick,
    player,
    scenario,
    terraformed_mars,
)


def test_nuclear_zone_raises_temperature_2_steps_and_places_its_tile_on_any_free_land():
    game = scenario(
        player(megacredits=10, hand=["nuclear_zone"]),
        player(),
        tiles=[city("C3", owner=1)],
    )

    pick(game, "Play Nuclear Zone (10 MegaCredits)")

    assert game.player_view(0)["temperature"] == -26
    assert game.decision["kind"] == "area"
    # Next to a City too: a special Tile has no placement restriction of its own.
    assert areas_offered(game) == [name for name in LAND_AREAS if name != "C3"]
    pick(game, "Place the Nuclear Zone Tile on C4")
    assert area(game, "C4")["tile"] == {
        "type": "special",
        "card": "nuclear_zone",
        "owner": 0,
    }
    assert game.decision["kind"] == "action"


def test_nuclear_zones_tile_counts_as_its_owners_tile_for_a_greenery():
    game = scenario(player(megacredits=10, plants=8, hand=["nuclear_zone"]), player())

    pick(game, "Play Nuclear Zone")
    pick(game, area="J3")
    pick(game, "Convert 8 plants into a Greenery")

    assert areas_offered(game) == ["H3", "H4", "J2", "J4"]


def test_nuclear_zone_is_worth_minus_2_victory_points():
    game = scenario(
        player(played_cards=["nuclear_zone"]), player(), **terraformed_mars()
    )

    assert [score["cards"] for score in final_scores(game)] == [-2, 0]
