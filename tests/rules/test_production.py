"""The Production phase, which follows once every Player has passed."""

import pytest

from tests.helpers import (
    RESOURCES,
    end_the_action_phase,
    end_the_generation,
    player,
    player_board,
    production,
    resources,
    scenario,
)


def test_each_player_gains_megacredits_equal_to_terraform_rating_plus_megacredit_production():
    game = scenario(
        player(megacredits=5, terraform_rating=23, production={"megacredits": 2}),
        player(megacredits=0, terraform_rating=20, production={"megacredits": -3}),
    )

    end_the_generation(game)

    assert resources(game, 0)["megacredits"] == 5 + 23 + 2
    assert resources(game, 1)["megacredits"] == 0 + 20 - 3


def test_energy_turns_into_heat_before_every_resource_gains_its_production():
    game = scenario(
        player(
            megacredits=1,
            steel=2,
            titanium=3,
            plants=4,
            energy=5,
            heat=6,
            terraform_rating=20,
            production={"megacredits": 1, "steel": 2, "titanium": 1, "plants": 3, "energy": 2, "heat": 1},
        ),
        player(),
    )

    end_the_generation(game)

    assert resources(game, 0) == {
        "megacredits": 1 + 20 + 1,
        "steel": 2 + 2,
        "titanium": 3 + 1,
        "plants": 4 + 3,
        "energy": 0 + 2,  # all 5 energy turned into heat first
        "heat": 6 + 5 + 1,
    }


def test_the_log_shows_energy_turning_into_heat_and_what_each_player_gains():
    game = scenario(
        player(energy=3, terraform_rating=20, production={"steel": 2, "plants": 1, "heat": 3}),
        player(terraform_rating=21),
        generation=2,
    )

    end_the_action_phase(game)

    assert game.log[-6:-2] == [
        "Production phase.",
        "Player 1's 3 energy turns into heat.",
        "Player 1 gains 20 MegaCredits (Terraform Rating 20 + MegaCredit Production 0), 2 steel, 1 plant and 3 heat.",
        "Player 2 gains 21 MegaCredits (Terraform Rating 21 + MegaCredit Production 0).",
    ]


def test_production_is_shown_on_the_player_board():
    game = scenario(player(production={"megacredits": 4}), player())

    assert production(game, 0)["megacredits"] == 4
    assert production(game, 1)["megacredits"] == 0


def test_a_new_generation_begins_after_production_with_nobody_passed():
    game = scenario(player(), player(), generation=3)

    end_the_generation(game)

    assert game.player_view(0)["generation"] == 4
    assert not player_board(game, 0)["passed"]
    assert not player_board(game, 1)["passed"]
    assert game.decision is not None


def test_megacredit_production_may_go_down_to_minus_5_and_no_further():
    game = scenario(player(megacredits=0, terraform_rating=20, production={"megacredits": -5}), player())
    end_the_generation(game)
    assert resources(game, 0)["megacredits"] == 15

    with pytest.raises(ValueError, match="MegaCredit Production must be -5 or more, not -6"):
        scenario(player(production={"megacredits": -6}), player())


@pytest.mark.parametrize("resource", [name for name in RESOURCES if name != "megacredits"])
def test_every_other_production_stays_at_0_or_above(resource):
    assert production(scenario(player(production={resource: 0}), player()), 0)[resource] == 0

    with pytest.raises(ValueError, match="Production must be 0 or more, not -1"):
        scenario(player(production={resource: -1}), player())


@pytest.mark.parametrize("resource", RESOURCES)
def test_a_scenario_cannot_give_a_player_a_negative_resource(resource):
    with pytest.raises(ValueError, match=r"Player 1 cannot have -1 \w+"):
        scenario(player(**{resource: -1}), player())
