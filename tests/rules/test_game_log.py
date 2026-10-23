"""The game log: a plain-language line for everything that happens."""

from tests.helpers import end_the_generation, ocean, pick, player, scenario, terraformed_mars


def test_a_new_game_log_starts_with_generation_1_and_its_first_player():
    game = scenario(player(), player(), player(), first_player=2)

    assert game.log == ["Generation 1 begins, with Player 3 as first player."]


def test_the_log_describes_what_each_player_does_in_plain_language():
    game = scenario(player(megacredits=20), player(), temperature=-30)

    pick(game, "Asteroid")
    pick(game, "End Turn")
    pick(game, "Pass")

    assert game.log == [
        "Generation 1 begins, with Player 1 as first player.",
        "Player 1 uses the Asteroid Standard Project for 14 MegaCredits.",
        "Player 1 raises Temperature to -28 °C and gains 1 Terraform Rating.",
        "Player 1 ends their Turn.",
        "Player 2 passes.",
    ]


def test_the_log_describes_placing_a_tile_and_everything_it_gives():
    game = scenario(player(megacredits=20), player(), tiles=[ocean("A4")])

    pick(game, project="aquifer")
    pick(game, area="A5")

    assert game.log[-4:] == [
        "Player 1 uses the Aquifer Standard Project for 18 MegaCredits.",
        "Player 1 places an Ocean on A5.",
        "Player 1 raises Oceans to 2 of 9 and gains 1 Terraform Rating.",
        "Player 1 gains 2 MegaCredits for 1 adjacent Ocean.",
    ]


def test_the_log_names_an_area_by_its_printed_name_too():
    game = scenario(player(megacredits=25), player())

    pick(game, project="city")
    pick(game, area="B2")

    assert game.log[-2:] == [
        "Player 1 places a City on B2 (Tharsis Tholus).",
        "Player 1 gains 1 steel from the placement bonus.",
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
        "Generation 3 begins, with Player 2 as first player.",
    ]


def test_the_log_ends_with_the_final_scores():
    game = scenario(player(terraform_rating=31), player(terraform_rating=27), **terraformed_mars())

    end_the_generation(game)

    assert game.log[-3:] == [
        "The Game is over.",
        "Player 1 finishes with 31 Victory Points.",
        "Player 2 finishes with 27 Victory Points.",
    ]
