"""#017 Noctis City (18 MegaCredits, building and city Tags): decrease your energy Production 1 step
and increase your MegaCredit Production 3 steps. Place a City Tile ON THE RESERVED AREA, disregarding
normal placement restrictions."""

from tests.helpers import (
    NOCTIS_CITY,
    area,
    areas_offered,
    city,
    final_scores,
    offered,
    pick,
    player,
    production,
    resources,
    scenario,
    terraformed_mars,
)

HOLDING = player(megacredits=18, hand=["noctis_city"], production={"energy": 1})


def test_noctis_city_needs_1_energy_production_to_lower():
    assert not offered(
        scenario(player(megacredits=18, hand=["noctis_city"]), player()),
        "Play Noctis City",
    )


def test_noctis_city_places_its_city_on_its_reserved_area_even_next_to_another_city():
    # E2 is next to E3.
    game = scenario(HOLDING, player(), tiles=[city("E2", owner=1)])

    pick(game, "Play Noctis City (18 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["megacredits"] == 3
    assert areas_offered(game) == [NOCTIS_CITY]
    assert offered(game, area="E3", on="noctis_city")
    pick(game, "Place the City on E3 (Noctis City)")
    assert area(game, "E3")["tile"] == {"type": "city", "owner": 0}
    # The placement bonus printed on it: 2 plants.
    assert resources(game, 0)["plants"] == 2


def test_no_other_tile_goes_on_noctis_citys_area():
    game = scenario(player(megacredits=25), player(), tiles=[city("A1", owner=0)])

    pick(game, "City (25 MegaCredits)")

    assert NOCTIS_CITY not in areas_offered(game)


def test_noctis_citys_city_sets_off_rover_construction_and_immigrant_city():
    other = player(megacredits=0, played_cards=["rover_construction", "immigrant_city"])
    game = scenario(HOLDING, other)

    pick(game, "Play Noctis City")
    pick(game, area="E3")

    assert resources(game, 1)["megacredits"] == 2
    assert production(game, 1)["megacredits"] == 1


def test_noctis_city_is_worth_no_victory_points():
    game = scenario(
        player(played_cards=["noctis_city"]), player(), **terraformed_mars()
    )

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
