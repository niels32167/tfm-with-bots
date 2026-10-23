"""Track bonuses: heat Production at -24 °C and -20 °C, an Ocean at 0 °C, and a Temperature
step at 8 % Oxygen. Each goes to the Player who raised the parameter."""

import pytest

from tests.helpers import (
    OCEAN_AREAS,
    area,
    areas_offered,
    ocean,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
)


@pytest.mark.parametrize("bonus_temperature", [-24, -20])
def test_reaching_a_heat_production_step_raises_the_heat_production_of_the_player_who_raised_temperature(
    bonus_temperature,
):
    game = scenario(
        player(), player(megacredits=14, production={"heat": 1}), first_player=1, temperature=bonus_temperature - 2
    )

    pick(game, "Asteroid")

    assert production(game, 1)["heat"] == 2
    assert production(game, 0)["heat"] == 0
    assert game.log[-2:] == [
        f"Player 2 raises Temperature to {bonus_temperature} °C and gains 1 Terraform Rating.",
        f"Reaching {bonus_temperature} °C raises Player 2's heat Production by 1.",
    ]


@pytest.mark.parametrize("reached", [-28, -26, -22, -18, -2, 8])
def test_the_other_temperature_steps_give_no_heat_production(reached):
    game = scenario(player(megacredits=14), player(), temperature=reached - 2)

    pick(game, "Asteroid")

    assert production(game, 0)["heat"] == 0


def test_reaching_0_degrees_gives_the_player_who_raised_temperature_an_ocean_to_place():
    game = scenario(player(megacredits=14, terraform_rating=20), player(), temperature=-2)

    pick(game, "Asteroid")

    assert game.decision["player"] == 0
    assert game.decision["kind"] == "area"
    assert areas_offered(game) == OCEAN_AREAS
    assert game.log[-1] == "Reaching 0 °C gives Player 1 an Ocean to place."

    pick(game, area="J5")  # two titanium

    assert area(game, "J5")["tile"] == {"type": "ocean", "owner": None}
    assert game.player_view(0)["oceans"] == 1
    assert player_board(game, 0)["terraform_rating"] == 22  # one for Temperature, one for the Ocean
    assert resources(game, 0)["titanium"] == 2
    assert game.player_view(0)["actions_this_turn"] == 1


def test_converting_heat_up_to_0_degrees_also_gives_an_ocean_to_place():
    game = scenario(player(megacredits=0, heat=8), player(), temperature=-2)

    pick(game, type="convert_heat")

    assert game.decision["kind"] == "area"
    assert game.player_view(0)["actions_this_turn"] == 0


def test_when_the_ocean_bonus_comes_with_the_second_action_the_turn_ends_once_the_ocean_is_placed():
    game = scenario(player(megacredits=28), player(), temperature=-4)
    pick(game, "Asteroid")

    pick(game, "Asteroid")
    assert game.decision["player"] == 0
    pick(game, area="A2")

    assert game.decision["player"] == 1
    assert game.decision["kind"] == "action"


def test_once_9_oceans_are_placed_reaching_0_degrees_places_no_ocean():
    nine_oceans = [ocean(name) for name in OCEAN_AREAS[:9]]
    game = scenario(player(megacredits=14, terraform_rating=20), player(), temperature=-2, tiles=nine_oceans)

    pick(game, "Asteroid")

    assert game.player_view(0)["oceans"] == 9
    assert player_board(game, 0)["terraform_rating"] == 21
    assert game.decision["kind"] == "action"
    assert game.player_view(0)["actions_this_turn"] == 1
    assert game.log[-2:] == [
        "Reaching 0 °C gives Player 1 an Ocean to place.",
        "All 9 Oceans are already placed, so no Ocean is placed.",
    ]


def test_reaching_8_percent_oxygen_also_raises_temperature_for_the_player_who_raised_oxygen():
    game = scenario(player(), player(megacredits=23, terraform_rating=20), first_player=1, oxygen=7)

    pick(game, project="greenery")
    pick(game, area="C3")  # no placement bonus

    assert game.player_view(0)["oxygen"] == 8
    assert game.player_view(0)["temperature"] == -28
    assert player_board(game, 1)["terraform_rating"] == 22
    assert player_board(game, 0)["terraform_rating"] == 20
    assert game.log[-3:] == [
        "Player 2 raises Oxygen to 8 % and gains 1 Terraform Rating.",
        "Reaching 8 % Oxygen gives Player 2 a Temperature step.",
        "Player 2 raises Temperature to -28 °C and gains 1 Terraform Rating.",
    ]


@pytest.mark.parametrize("oxygen", [6, 8, 13])
def test_the_other_oxygen_steps_do_not_raise_temperature(oxygen):
    game = scenario(player(plants=8), player(), oxygen=oxygen)

    pick(game, type="convert_plants")
    pick(game, area="C3")

    assert game.player_view(0)["temperature"] == -30


def test_at_maximum_temperature_reaching_8_percent_oxygen_raises_nothing_more():
    game = scenario(player(plants=8, terraform_rating=30), player(), oxygen=7, temperature=8)

    pick(game, type="convert_plants")
    pick(game, area="C3")

    assert game.player_view(0)["temperature"] == 8
    assert player_board(game, 0)["terraform_rating"] == 31
    assert game.log[-1] == "Temperature is already at its maximum, so it does not rise."


def test_8_percent_oxygen_can_raise_temperature_onto_a_heat_production_step():
    game = scenario(player(plants=8), player(), oxygen=7, temperature=-26)

    pick(game, type="convert_plants")
    pick(game, area="C3")

    assert game.player_view(0)["temperature"] == -24
    assert production(game, 0)["heat"] == 1


def test_8_percent_oxygen_can_raise_temperature_to_0_degrees_and_the_ocean_is_placed_before_the_greenerys_bonus():
    game = scenario(player(megacredits=0, plants=8, terraform_rating=20), player(), oxygen=7, temperature=-2)

    pick(game, type="convert_plants")
    pick(game, area="D7")  # one plant, next to D8, which is reserved for Oceans

    assert game.decision["kind"] == "area"
    assert areas_offered(game) == OCEAN_AREAS
    assert game.log[-3:] == [
        "Reaching 8 % Oxygen gives Player 1 a Temperature step.",
        "Player 1 raises Temperature to 0 °C and gains 1 Terraform Rating.",
        "Reaching 0 °C gives Player 1 an Ocean to place.",
    ]
    assert resources(game, 0)["plants"] == 0  # the Greenery's bonus waits for the Ocean

    pick(game, area="D8")  # two plants, next to no other Ocean

    assert game.log[-6:] == [
        "Player 1 places an Ocean on D8.",
        "Player 1 raises Oceans to 1 of 9 and gains 1 Terraform Rating.",
        "Player 1 gains 2 plants from the placement bonus.",
        "Player 1 collects the placement bonus of the Greenery on D7.",
        "Player 1 gains 1 plant from the placement bonus.",
        "Player 1 gains 2 MegaCredits for 1 adjacent Ocean.",
    ]
    assert resources(game, 0)["plants"] == 2 + 1
    assert resources(game, 0)["megacredits"] == 2  # the Greenery is next to the new Ocean
    assert player_board(game, 0)["terraform_rating"] == 23
    assert game.player_view(0)["actions_this_turn"] == 1


def test_a_greenery_whose_ocean_bonus_gives_nothing_to_collect_adds_no_line_for_it():
    game = scenario(player(plants=8), player(), oxygen=7, temperature=-2)

    pick(game, type="convert_plants")
    pick(game, area="C3")  # no placement bonus and no Ocean Area nearby
    pick(game, area="A2")

    assert not any("collects the placement bonus" in line for line in game.log)
