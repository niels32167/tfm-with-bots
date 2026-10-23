"""Placement bonuses: what is printed on an Area, plus 2 MegaCredits for each Ocean next to it."""

import pytest

from tests.helpers import area, ocean, pick, player, resources, scenario


@pytest.mark.parametrize(
    ("ocean_area", "resource", "amount"),
    [("A2", "steel", 2), ("J5", "titanium", 2), ("D8", "plants", 2), ("F6", "plants", 1)],
)
def test_a_tile_on_an_area_with_a_placement_bonus_gives_the_player_that_bonus(ocean_area, resource, amount):
    game = scenario(player(megacredits=18), player())

    pick(game, project="aquifer")
    pick(game, area=ocean_area)

    assert resources(game, 0)[resource] == amount
    assert resources(game, 1)[resource] == 0


def test_a_tile_gives_2_megacredits_for_each_ocean_next_to_it_even_when_the_tile_is_an_ocean():
    game = scenario(player(megacredits=18), player(), tiles=[ocean("E4"), ocean("E6"), ocean("F7")])

    pick(game, project="aquifer")
    pick(game, area="E5")  # next to E4 and E6, but not F7

    assert resources(game, 0)["megacredits"] == 0 + 2 * 2
    assert resources(game, 0)["plants"] == 2
    assert game.log[-2:] == [
        "Player 1 gains 2 plants from the placement bonus.",
        "Player 1 gains 4 MegaCredits for 2 adjacent Oceans.",
    ]


def test_cities_and_greeneries_get_2_megacredits_for_each_ocean_next_to_them_too():
    game = scenario(player(megacredits=25 + 23), player(), tiles=[ocean("E4"), ocean("E5")])

    pick(game, project="city")
    pick(game, area="D4")  # next to E4 and E5; 1 plant
    pick(game, project="greenery")
    pick(game, area="D5")  # next to E5 (and the City); 2 plants

    assert area(game, "D5")["tile"] == {"type": "greenery", "owner": 0}
    assert resources(game, 0)["megacredits"] == 0 + 2 * 2 + 2 * 1
    assert resources(game, 0)["plants"] == 1 + 2


def test_until_there_is_a_deck_a_card_bonus_only_says_what_it_would_give():
    game = scenario(player(megacredits=18), player())

    pick(game, project="aquifer")
    pick(game, area="B6")

    assert game.log[-1] == "Player 1 would draw 2 cards from the placement bonus, but there is no deck yet."
