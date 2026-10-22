"""The Asteroid Standard Project: 14 MegaCredits to raise Temperature one step."""

from tests.helpers import offered, pick, player, player_board, scenario


def test_asteroid_costs_14_megacredits_and_raises_temperature_one_step_for_one_terraform_rating():
    game = scenario(player(megacredits=20, terraform_rating=20), player(), temperature=-30)

    pick(game, "Asteroid")

    assert game.player_view(0)["temperature"] == -28
    assert player_board(game, 0)["megacredits"] == 6
    assert player_board(game, 0)["terraform_rating"] == 21


def test_asteroid_is_offered_with_exactly_14_megacredits():
    game = scenario(player(megacredits=14), player())

    assert offered(game, "Asteroid")


def test_asteroid_is_not_offered_when_the_player_cannot_afford_it():
    game = scenario(player(megacredits=13), player())

    assert not offered(game, "Asteroid")
    assert offered(game, "Pass")


def test_asteroid_at_maximum_temperature_costs_14_megacredits_and_does_nothing_else():
    # Rulebook: you may still take Actions that raise a maxed Global Parameter,
    # ignoring that part of the effect (docs/rules-notes.md).
    game = scenario(player(megacredits=20, terraform_rating=30), player(), temperature=8)

    pick(game, "Asteroid")

    assert game.player_view(0)["temperature"] == 8
    assert player_board(game, 0)["megacredits"] == 6
    assert player_board(game, 0)["terraform_rating"] == 30
