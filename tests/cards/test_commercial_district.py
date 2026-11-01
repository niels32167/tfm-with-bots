"""#085 Commercial District (Corporate Era, 16 MegaCredits, building Tag): decrease your energy
Production 1 step and increase your MegaCredit Production 4 steps. Place this Tile. 1 Victory Point
per adjacent City Tile."""

from tests.helpers import (
    LAND_AREAS,
    area,
    areas_offered,
    city,
    final_scores,
    offered,
    pick,
    player,
    production,
    scenario,
    special,
    terraformed_mars,
)


def test_commercial_district_needs_1_energy_production_to_lower():
    assert not offered(
        scenario(player(megacredits=16, hand=["commercial_district"]), player()),
        "Play Commercial District",
    )


def test_commercial_district_trades_production_and_places_its_tile_on_any_free_land():
    holding = player(
        megacredits=16, hand=["commercial_district"], production={"energy": 1}
    )
    game = scenario(holding, player())

    pick(game, "Play Commercial District (16 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["megacredits"] == 4
    assert areas_offered(game) == LAND_AREAS
    pick(game, "Place the Commercial District Tile on C4")
    assert area(game, "C4")["tile"] == {
        "type": "special",
        "card": "commercial_district",
        "owner": 0,
    }


def test_commercial_district_is_worth_1_victory_point_per_city_next_to_its_tile_whoever_owns_it():
    # C4 is next to B3, B4, C3, C5, D4 and D5; Capital's City counts as a City.
    tiles = [
        special("C4", "commercial_district", owner=0),
        city("C3", owner=1),
        city("B4", owner=0),
        special("D5", "capital", owner=1),
        city("C7", owner=0),
    ]
    game = scenario(
        player(played_cards=["commercial_district"]),
        player(),
        **terraformed_mars(tiles=tiles),
    )

    assert final_scores(game)[0]["cards"] == 3
