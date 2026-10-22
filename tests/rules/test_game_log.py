"""The game log: a plain-language line for everything that happens."""

import tm_engine

from tests.helpers import end_the_generation, pick, player, scenario


def test_a_new_game_log_starts_with_generation_1():
    game = tm_engine.Game(seed=1)

    assert game.log == ["Generation 1 begins."]


def test_the_log_describes_what_each_player_does_in_plain_language():
    game = scenario(player(megacredits=20), player(), temperature=-30)

    pick(game, "Asteroid")
    pick(game, "End Turn")
    pick(game, "Pass")

    assert game.log == [
        "Generation 1 begins.",
        "Player 1 uses the Asteroid Standard Project for 14 MegaCredits.",
        "Player 1 raises Temperature to -28 °C and gains 1 Terraform Rating.",
        "Player 1 ends their Turn.",
        "Player 2 passes.",
    ]


def test_the_log_says_when_temperature_is_already_at_its_maximum():
    game = scenario(player(megacredits=20), player(), temperature=8)

    pick(game, "Asteroid")

    assert game.log[-1] == "Temperature is already at its maximum, so it does not rise."


def test_the_log_shows_the_production_phase_and_the_next_generation():
    game = scenario(player(terraform_rating=25, production={"megacredits": 2}), player(), generation=2)

    end_the_generation(game)

    assert game.log[-4:] == [
        "Production phase.",
        "Player 1 gains 27 MegaCredits (Terraform Rating 25 + MegaCredit Production 2).",
        "Player 2 gains 20 MegaCredits (Terraform Rating 20 + MegaCredit Production 0).",
        "Generation 3 begins.",
    ]


def test_the_log_ends_with_the_final_scores():
    game = scenario(player(terraform_rating=31), player(terraform_rating=27), temperature=8)

    end_the_generation(game)

    assert game.log[-3:] == [
        "The Game is over.",
        "Player 1 finishes with 31 Victory Points.",
        "Player 2 finishes with 27 Victory Points.",
    ]
