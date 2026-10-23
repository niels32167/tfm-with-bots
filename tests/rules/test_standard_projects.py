"""Which Standard Projects and conversions are offered: only those the Player can afford, with room for their Tile."""

import pytest

from tests.helpers import LAND_AREAS, city, greenery, labels, offered, pick, player, production, resources, scenario


@pytest.mark.parametrize(
    ("project", "cost"), [("power_plant", 11), ("asteroid", 14), ("aquifer", 18), ("greenery", 23), ("city", 25)]
)
def test_a_standard_project_is_offered_with_exactly_its_price_and_not_with_less(project, cost):
    assert offered(scenario(player(megacredits=cost), player()), project=project, cost=cost)
    assert not offered(scenario(player(megacredits=cost - 1), player()), project=project)


def test_with_no_free_area_left_on_land_no_greenery_or_city_can_be_placed():
    every_free_area_taken = [greenery(name, owner=1) for name in LAND_AREAS]
    game = scenario(player(megacredits=60, plants=8), player(), tiles=every_free_area_taken)

    assert not offered(game, project="greenery")
    assert not offered(game, project="city")
    assert not offered(game, type="convert_plants")
    assert offered(game, project="aquifer")


def test_with_the_only_free_area_next_to_a_city_a_greenery_can_be_placed_but_not_a_city():
    # A1 is next to A2 (reserved for Oceans), B1 and B2.
    tiles = [greenery(name, owner=1) for name in LAND_AREAS if name not in ("A1", "B1")] + [city("B1", owner=1)]
    game = scenario(player(megacredits=60), player(), tiles=tiles)

    assert not offered(game, project="city")
    assert offered(game, project="greenery")


def test_power_plant_costs_11_megacredits_and_raises_energy_production_by_1():
    game = scenario(player(megacredits=11, production={"energy": 2}), player())

    pick(game, project="power_plant")

    assert resources(game, 0)["megacredits"] == 0
    assert production(game, 0)["energy"] == 3
    assert game.log[-2:] == [
        "Player 1 uses the Power Plant Standard Project for 11 MegaCredits.",
        "Player 1 raises their energy Production by 1.",
    ]
    assert game.player_view(0)["actions_this_turn"] == 1


def test_standard_projects_are_offered_in_the_order_printed_on_the_board():
    game = scenario(player(megacredits=25), player())

    assert labels(game)[:5] == [
        "Power Plant (11 MegaCredits)",
        "Asteroid (14 MegaCredits)",
        "Aquifer (18 MegaCredits)",
        "Greenery (23 MegaCredits)",
        "City (25 MegaCredits)",
    ]
