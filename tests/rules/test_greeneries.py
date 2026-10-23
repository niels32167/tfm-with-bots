"""Greenery Tiles: the Greenery Standard Project, converting plants, Oxygen and where Greeneries go."""

from tests.helpers import (
    LAND_AREAS,
    area,
    areas_offered,
    city,
    greenery,
    ocean,
    offered,
    options,
    pick,
    player,
    player_board,
    resources,
    scenario,
)


def test_greenery_costs_23_megacredits_and_places_a_greenery_that_raises_oxygen_for_one_terraform_rating():
    game = scenario(player(megacredits=23, terraform_rating=20), player(), oxygen=3)

    pick(game, project="greenery")
    pick(game, area="C3")  # no placement bonus

    assert area(game, "C3")["tile"] == {"type": "greenery", "owner": 0}
    assert game.player_view(0)["oxygen"] == 4
    assert resources(game, 0)["megacredits"] == 0
    assert player_board(game, 0)["terraform_rating"] == 21
    assert game.log[-2:] == [
        "Player 1 places a Greenery on C3.",
        "Player 1 raises Oxygen to 4 % and gains 1 Terraform Rating.",
    ]


def test_at_maximum_oxygen_a_greenery_is_still_placed_but_oxygen_and_terraform_rating_stay():
    game = scenario(player(megacredits=23, terraform_rating=30), player(), oxygen=14)

    pick(game, project="greenery")
    pick(game, area="C3")

    assert area(game, "C3")["tile"] == {"type": "greenery", "owner": 0}
    assert game.player_view(0)["oxygen"] == 14
    assert player_board(game, 0)["terraform_rating"] == 30
    assert game.log[-1] == "Oxygen is already at its maximum, so it does not rise."


def test_a_greenery_goes_next_to_one_of_its_owners_tiles_when_possible():
    # C3 is next to B2, B3, C2, C4, D3 and D4. Player 2's City elsewhere does not count.
    game = scenario(player(megacredits=23), player(), tiles=[city("C3", owner=0), city("H2", owner=1)])

    pick(game, project="greenery")

    assert areas_offered(game) == ["B2", "B3", "C2", "C4", "D3", "D4"]


def test_a_greenery_never_goes_on_an_area_reserved_for_oceans_or_for_noctis_city_even_next_to_its_owners_tiles():
    # E2 is next to D1, D2, E1, E3 (Noctis City), F1 and F2;
    # D7 is next to C6, C7, D6, D8 (reserved for Oceans), E7 and E8.
    game = scenario(player(megacredits=23), player(), tiles=[city("E2", owner=0), greenery("D7", owner=0)])

    pick(game, project="greenery")

    assert areas_offered(game) == ["C6", "C7", "D1", "D2", "D6", "E1", "E7", "E8", "F1", "F2"]


def test_with_no_free_area_next_to_its_owners_tiles_a_greenery_goes_on_any_free_area_not_reserved():
    # A1 is next to A2 (an Ocean), B1 and B2 (Player 2's).
    tiles = [city("A1", owner=0), ocean("A2"), greenery("B1", owner=1), greenery("B2", owner=1)]
    game = scenario(player(megacredits=23), player(), tiles=tiles)

    pick(game, project="greenery")

    assert areas_offered(game) == [name for name in LAND_AREAS if name not in ("A1", "B1", "B2")]


def test_a_player_may_convert_8_plants_into_a_greenery_as_an_action():
    game = scenario(player(megacredits=0, plants=9, terraform_rating=20), player(), oxygen=3)

    pick(game, type="convert_plants")
    pick(game, area="C3")

    assert area(game, "C3")["tile"] == {"type": "greenery", "owner": 0}
    assert resources(game, 0)["plants"] == 1
    assert game.player_view(0)["oxygen"] == 4
    assert player_board(game, 0)["terraform_rating"] == 21
    assert "Player 1 converts 8 plants into a Greenery." in game.log
    assert game.player_view(0)["actions_this_turn"] == 1


def test_converting_plants_is_offered_with_8_plants_and_not_with_7():
    game = scenario(player(plants=8), player())
    conversions = [option for option in options(game) if option["details"]["type"] == "convert_plants"]
    assert [(option["label"], option["details"]) for option in conversions] == [
        ("Convert 8 plants into a Greenery", {"type": "convert_plants", "plants": 8})
    ]

    assert not offered(scenario(player(plants=7), player()), type="convert_plants")


def test_converting_plants_at_maximum_oxygen_still_places_a_greenery_but_raises_nothing():
    game = scenario(player(plants=8, terraform_rating=30), player(), oxygen=14)

    pick(game, type="convert_plants")
    pick(game, area="C3")

    assert area(game, "C3")["tile"] == {"type": "greenery", "owner": 0}
    assert resources(game, 0)["plants"] == 0
    assert game.player_view(0)["oxygen"] == 14
    assert player_board(game, 0)["terraform_rating"] == 30

