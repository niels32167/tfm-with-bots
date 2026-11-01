"""#008 Capital (26 MegaCredits, building and city Tags): requires 4 Ocean Tiles. Place this Tile.
Decrease your energy Production 2 steps and increase your MegaCredit Production 5 steps. 1 additional
Victory Point for each Ocean Tile adjacent to this City Tile."""

from tests.helpers import (
    OCEAN_AREAS,
    area,
    areas_offered,
    city,
    final_scores,
    greenery,
    milestone,
    ocean,
    offered,
    pick,
    player,
    production,
    resources,
    scenario,
    special,
    terraformed_mars,
)

FOUR_OCEANS = [ocean(name) for name in OCEAN_AREAS[:4]]
HOLDING = player(megacredits=26, hand=["capital"], production={"energy": 2})


def test_capital_needs_4_oceans():
    assert not offered(
        scenario(HOLDING, player(), tiles=FOUR_OCEANS[:3]), "Play Capital"
    )
    assert offered(scenario(HOLDING, player(), tiles=FOUR_OCEANS), "Play Capital")


def test_capital_needs_2_energy_production_to_lower():
    holding = player(megacredits=26, hand=["capital"], production={"energy": 1})

    assert not offered(scenario(holding, player(), tiles=FOUR_OCEANS), "Play Capital")


def test_capital_trades_production_and_places_its_city_where_a_city_may_go():
    game = scenario(HOLDING, player(), tiles=[*FOUR_OCEANS, city("C3", owner=1)])

    pick(game, "Play Capital (26 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["megacredits"] == 5
    assert "C4" not in areas_offered(game)
    pick(game, "Place the Capital Tile on C5")
    assert area(game, "C5")["tile"] == {"type": "city", "card": "capital", "owner": 0}
    assert game.decision["kind"] == "action"


def test_capitals_city_sets_off_rover_construction_and_immigrant_city():
    holding = player(megacredits=26, hand=["capital"], production={"energy": 2})
    other = player(megacredits=0, played_cards=["rover_construction", "immigrant_city"])
    game = scenario(holding, other, tiles=FOUR_OCEANS)

    pick(game, "Play Capital")
    pick(game, area="C3")

    assert resources(game, 1)["megacredits"] == 2
    assert production(game, 1)["megacredits"] == 1


def test_capitals_city_keeps_other_cities_away_and_counts_as_a_city():
    tiles = [
        *FOUR_OCEANS,
        special("C3", "capital", owner=0),
        city("H1", owner=0),
        city("J3", owner=0),
    ]
    game = scenario(player(megacredits=25), player(), tiles=tiles)

    pick(game, "City (25 MegaCredits)")

    assert "C4" not in areas_offered(game)
    assert milestone(game, "mayor")["counts"][0] == 3


def test_capital_scores_1_victory_point_per_ocean_next_to_it_and_its_greeneries_as_a_city():
    # D7 is next to C6, C7, D6, D8, E7 and E8; D8 is an Ocean Area.
    tiles = [
        special("D7", "capital", owner=0),
        greenery("C7", owner=1),
        city("E7", owner=1),
    ]
    game = scenario(
        player(played_cards=["capital"]), player(), **terraformed_mars(tiles=tiles)
    )

    scores = final_scores(game)
    assert scores[0]["cards"] == 1
    assert scores[0]["cities"] == 1
