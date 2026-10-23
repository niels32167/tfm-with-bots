"""The end of the Game: after the Generation in which all three Global Parameters reach their maximum."""

import pytest

from tests.helpers import (
    OCEAN_AREAS,
    end_the_generation,
    ocean,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)

# Mars with one Global Parameter a step short of its maximum.
TEMPERATURE_SHORT = terraformed_mars(temperature=6)
OXYGEN_SHORT = terraformed_mars(oxygen=13)
OCEANS_SHORT = {"temperature": 8, "oxygen": 14, "tiles": [ocean(name) for name in OCEAN_AREAS[:8]]}


@pytest.mark.parametrize(
    "almost_terraformed", [TEMPERATURE_SHORT, OXYGEN_SHORT, OCEANS_SHORT], ids=["temperature", "oxygen", "oceans"]
)
def test_the_game_goes_on_while_any_global_parameter_is_below_its_maximum(almost_terraformed):
    game = scenario(player(), player(), generation=5, **almost_terraformed)

    end_the_generation(game)

    assert not game.is_over
    assert game.player_view(0)["generation"] == 6


def test_the_generation_carries_on_after_the_last_global_parameter_reaches_its_maximum():
    game = scenario(player(megacredits=14), player(), **terraformed_mars(temperature=6))

    pick(game, "Asteroid")

    assert game.player_view(0)["temperature"] == 8
    assert not game.is_over
    assert game.decision["player"] == 0


@pytest.mark.parametrize(
    ("almost_terraformed", "raise_it"),
    [
        (TEMPERATURE_SHORT, ["Asteroid"]),
        (OXYGEN_SHORT, ["Greenery", "C3"]),
        (OCEANS_SHORT, ["Aquifer", OCEAN_AREAS[8]]),
    ],
    ids=["temperature", "oxygen", "oceans"],
)
def test_the_game_ends_after_the_production_phase_of_the_generation_in_which_all_three_reached_their_maximum(
    almost_terraformed, raise_it
):
    game = scenario(player(megacredits=25, terraform_rating=37), player(megacredits=0), **almost_terraformed)

    for label in raise_it:
        pick(game, label)
    end_the_generation(game)

    assert game.is_over
    assert game.decision is None
    assert resources(game, 0)["megacredits"] > 25  # the final Production phase still pays
    assert player_board(game, 0)["terraform_rating"] == 38


def test_a_game_started_with_mars_terraformed_ends_after_that_generation():
    game = scenario(player(), player(), **terraformed_mars())

    end_the_generation(game)

    assert game.is_over


def test_every_player_sees_the_final_scores():
    game = scenario(player(terraform_rating=31), player(terraform_rating=27), **terraformed_mars())

    end_the_generation(game)

    view = game.player_view(1)
    assert view["phase"] == "over"
    assert view["scores"] == game.scores


def test_there_are_no_scores_before_the_game_is_over():
    game = scenario(player(), player())

    assert game.scores is None
    assert game.player_view(0)["scores"] is None


def test_nobody_has_a_turn_once_the_game_is_over():
    game = scenario(player(), player(), **terraformed_mars())

    end_the_generation(game)

    assert game.player_view(0)["current_player"] is None
