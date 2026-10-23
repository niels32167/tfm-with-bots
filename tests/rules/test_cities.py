"""City Tiles: the City Standard Project, and where Cities may go."""

import pytest

from tests.helpers import (
    LAND_AREAS,
    area,
    areas_offered,
    city,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
)


def test_city_costs_25_megacredits_raises_megacredit_production_by_1_and_places_a_city():
    game = scenario(player(megacredits=25, terraform_rating=20, production={"megacredits": 2}), player())

    pick(game, project="city")
    pick(game, area="C3")  # no placement bonus

    assert area(game, "C3")["tile"] == {"type": "city", "owner": 0}
    assert resources(game, 0)["megacredits"] == 0
    assert production(game, 0)["megacredits"] == 3
    assert player_board(game, 0)["terraform_rating"] == 20
    assert game.log[-3:] == [
        "Player 1 uses the City Standard Project for 25 MegaCredits.",
        "Player 1 raises their MegaCredit Production by 1.",
        "Player 1 places a City on C3.",
    ]


def test_a_city_goes_on_any_free_area_not_reserved_for_oceans_or_a_card():
    game = scenario(player(megacredits=25), player())

    pick(game, project="city")

    assert areas_offered(game) == LAND_AREAS
    assert "E3" not in areas_offered(game)  # Noctis City


# Each City's neighbours, at the edges of the board and on both sides of the widest row.
NEIGHBOURS = {
    "A1": ["A2", "B1", "B2"],
    "C7": ["B6", "C6", "D7", "D8"],
    "D4": ["C3", "C4", "D3", "D5", "E4", "E5"],
    "E9": ["D8", "E8", "F8"],
    "F4": ["E4", "E5", "F3", "F5", "G3", "G4"],
    "J3": ["H3", "H4", "J2", "J4"],
}


@pytest.mark.parametrize("other_city", NEIGHBOURS)
def test_a_city_never_goes_next_to_another_city_whoever_owns_it(other_city):
    game = scenario(player(megacredits=25), player(), tiles=[city(other_city, owner=1)])

    pick(game, project="city")

    ruled_out = [other_city, *NEIGHBOURS[other_city]]
    assert areas_offered(game) == [name for name in LAND_AREAS if name not in ruled_out]
