"""Thorgate (power Tag): Effect: when playing a power card OR THE STANDARD PROJECT POWER PLANT, you
pay 3 MegaCredits less for it. You start with 1 energy Production and 48 MegaCredits."""

from tests.helpers import (
    offered,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
    start_as,
)


def test_thorgate_starts_with_1_energy_production_48_megacredits_and_a_power_tag():
    game, first = start_as("thorgate")

    assert resources(game, first) == {
        "megacredits": 48,
        "steel": 0,
        "titanium": 0,
        "plants": 0,
        "energy": 0,
        "heat": 0,
    }
    assert production(game, first) == {
        "megacredits": 0,
        "steel": 0,
        "titanium": 0,
        "plants": 0,
        "energy": 1,
        "heat": 0,
    }
    assert player_board(game, first)["tags"]["power"] == 1


def test_a_card_with_a_power_tag_costs_3_megacredits_less_and_others_do_not():
    game = scenario(
        player(
            corporation="thorgate", megacredits=7, hand=["nuclear_power", "satellites"]
        ),
        player(),
    )

    assert offered(game, "Play Nuclear Power (7 MegaCredits)", cost=7)
    assert not offered(game, "Play Satellites")


def test_the_power_plant_standard_project_costs_8_megacredits():
    game = scenario(player(corporation="thorgate", megacredits=8), player())

    assert offered(game, "Power Plant (8 MegaCredits)", project="power_plant", cost=8)
    pick(game, "Power Plant")

    assert resources(game, 0)["megacredits"] == 0
    assert production(game, 0)["energy"] == 1
    assert (
        "Player 1 uses the Power Plant Standard Project for 8 MegaCredits." in game.log
    )


def test_with_7_megacredits_it_cannot_pay_for_the_power_plant():
    game = scenario(player(corporation="thorgate", megacredits=7), player())

    assert not offered(game, project="power_plant")


def test_other_standard_projects_cost_what_they_always_do():
    game = scenario(player(corporation="thorgate", megacredits=14), player())

    assert offered(game, "Asteroid (14 MegaCredits)", cost=14)


def test_another_player_pays_11_megacredits_for_the_power_plant():
    game = scenario(player(megacredits=11), player(corporation="thorgate"))

    assert offered(game, "Power Plant (11 MegaCredits)", cost=11)
