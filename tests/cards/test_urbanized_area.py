"""#120 Urbanized Area (10 MegaCredits, building and city Tags): decrease your energy Production 1
step and increase your MegaCredit Production 2 steps. Place a City Tile ADJACENT TO AT LEAST 2
OTHER CITY TILES."""

from tests.helpers import (
    area,
    areas_offered,
    city,
    final_scores,
    offered,
    pick,
    player,
    production,
    scenario,
    terraformed_mars,
)

# C4 is the one Area next to both C3 and C5.
TWO_CITIES = [city("C3", owner=1), city("C5", owner=0)]


def test_urbanized_area_needs_1_energy_production_to_lower():
    assert not offered(scenario(player(hand=["urbanized_area"]), player(), tiles=TWO_CITIES), "Play Urbanized Area")


def test_urbanized_area_needs_free_land_next_to_2_cities():
    with_energy = player(hand=["urbanized_area"], production={"energy": 1})

    assert not offered(scenario(with_energy, player(), tiles=TWO_CITIES[:1]), "Play Urbanized Area")
    assert offered(scenario(with_energy, player(), tiles=TWO_CITIES), "Play Urbanized Area")


def test_urbanized_area_trades_production_and_places_a_city_next_to_2_cities_whoever_owns_them():
    holding = player(megacredits=10, hand=["urbanized_area"], production={"energy": 1})
    game = scenario(holding, player(), tiles=TWO_CITIES)

    pick(game, "Play Urbanized Area (10 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["megacredits"] == 2
    assert game.decision["kind"] == "area"
    assert areas_offered(game) == ["C4"]
    assert offered(game, area="C4", on="next_to_two_cities")
    pick(game, area="C4")
    assert area(game, "C4")["tile"] == {"type": "city", "owner": 0}
    assert game.decision["kind"] == "action"


def test_later_cities_keep_apart_from_urbanized_areas_city():
    # C4 and D4 are the Areas next to both C3 and D5. B4 is next to C4, but to neither of them.
    tiles = [city("C3", owner=1), city("D5", owner=1)]
    before = scenario(player(megacredits=25), player(), tiles=tiles)
    pick(before, "City (25 MegaCredits)")
    assert "B4" in areas_offered(before)
    holding = player(megacredits=35, hand=["urbanized_area"], production={"energy": 1})
    game = scenario(holding, player(), tiles=tiles)

    pick(game, "Play Urbanized Area")
    assert areas_offered(game) == ["C4", "D4"]
    pick(game, area="C4")
    pick(game, "City (25 MegaCredits)")

    assert "B4" not in areas_offered(game)


def test_urbanized_area_is_worth_no_victory_points():
    game = scenario(player(played_cards=["urbanized_area"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
