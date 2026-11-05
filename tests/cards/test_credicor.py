"""CrediCor: Effect: after you pay for a card or Standard Project with a basic cost of 20 MegaCredits
or more, you gain 4 MegaCredits. You start with 57 MegaCredits."""

from tests.helpers import (
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
    start_as,
)


def test_credicor_starts_with_57_megacredits_and_no_tags():
    game, first = start_as("credicor")

    assert resources(game, first) == {
        "megacredits": 57,
        "steel": 0,
        "titanium": 0,
        "plants": 0,
        "energy": 0,
        "heat": 0,
    }
    assert set(production(game, first).values()) == {0}
    assert set(player_board(game, first)["tags"].values()) == {0}


def test_a_card_with_a_cost_of_20_megacredits_gains_4_megacredits_after_paying_for_it():
    game = scenario(
        player(corporation="credicor", megacredits=20, hand=["mohole_area"]), player()
    )

    pick(game, "Play Mohole Area")
    pick(game, type="area", area="A2")

    assert resources(game, 0)["megacredits"] == 4


def test_a_card_with_a_lower_cost_gains_nothing():
    game = scenario(
        player(corporation="credicor", megacredits=14, hand=["asteroid"]), player()
    )

    pick(game, "Play Asteroid")

    assert resources(game, 0)["megacredits"] == 0


def test_the_basic_cost_counts_so_a_discount_does_not_take_a_card_below_20():
    game = scenario(
        player(
            corporation="credicor",
            megacredits=18,
            hand=["mohole_area"],
            played_cards=["earth_catapult"],
        ),
        player(),
    )

    pick(game, "Play Mohole Area (18 MegaCredits)")
    pick(game, type="area", area="A2")

    assert resources(game, 0)["megacredits"] == 4


def test_the_greenery_and_city_standard_projects_gain_4_megacredits():
    greenery = scenario(player(corporation="credicor", megacredits=23), player())
    pick(greenery, "Greenery (23 MegaCredits)")
    pick(greenery, type="area", area="C3")
    assert resources(greenery, 0)["megacredits"] == 4

    city = scenario(player(corporation="credicor", megacredits=25), player())
    pick(city, "City (25 MegaCredits)")
    pick(city, type="area", area="C3")
    assert resources(city, 0)["megacredits"] == 4


def test_the_aquifer_standard_project_gains_nothing_at_18_megacredits():
    game = scenario(player(corporation="credicor", megacredits=18), player())

    pick(game, "Aquifer (18 MegaCredits)")
    pick(game, type="area", area="A4")

    assert resources(game, 0)["megacredits"] == 0


def test_another_players_card_gains_nothing():
    game = scenario(player(megacredits=23), player(corporation="credicor"))

    pick(game, "Greenery (23 MegaCredits)")
    pick(game, type="area", area="C3")

    assert resources(game, 1)["megacredits"] == 42
