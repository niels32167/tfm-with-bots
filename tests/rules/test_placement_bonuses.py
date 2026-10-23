"""Placement bonuses: what is printed on an Area, plus 2 MegaCredits for each Ocean next to it."""

import pytest

from tests.helpers import PROJECT_CARDS, area, hand, ocean, pick, player, resources, scenario


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


def test_a_card_bonus_draws_cards_from_the_top_of_the_deck():
    game = scenario(player(megacredits=18, hand=["mine"]), player(), deck=["birds", "trees", "grass"])

    pick(game, project="aquifer")
    pick(game, area="B6")

    assert hand(game, 0) == ["mine", "trees", "birds"]  # in card-number order
    assert game.full_view()["deck"][0] == "grass"
    assert game.full_view()["deck_size"] == 205
    assert "Player 1 draws 2 cards from the placement bonus." in game.log


def test_the_log_never_names_the_cards_drawn():
    game = scenario(player(megacredits=18), player(), deck=["birds", "trees"])

    pick(game, project="aquifer")
    pick(game, area="B6")

    assert not any("Birds" in line or "Trees" in line for line in game.log)


def test_a_card_bonus_with_the_deck_empty_draws_nothing():
    game = scenario(player(megacredits=18, hand=PROJECT_CARDS[:200]), player(hand=PROJECT_CARDS[200:]))

    pick(game, project="aquifer")
    pick(game, area="B6")

    assert game.player_view(0)["players"][0]["hand_size"] == 200
    assert "The deck is empty, so Player 1 draws no more cards." in game.log
