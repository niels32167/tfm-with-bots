"""#P15 Huge Asteroid (Prelude Card): increase the Temperature 3 steps. Pay 5 MegaCredits."""

from tests.helpers import player, player_board, production, resources, scenario


def test_huge_asteroid_raises_the_temperature_3_steps_and_costs_5_megacredits():
    game = scenario(player(prelude_cards=["huge_asteroid"]), player(), prelude=True)

    assert game.full_view()["temperature"] == -24
    assert player_board(game, 0)["terraform_rating"] == 23
    # The Temperature passing -24 °C raises heat Production 1 step.
    assert production(game, 0)["heat"] == 1
    assert resources(game, 0)["megacredits"] == 37
    assert "Player 1 pays 5 MegaCredits for Huge Asteroid." in game.log


def test_with_the_temperature_at_its_maximum_it_is_still_played_and_paid_for():
    game = scenario(player(prelude_cards=["huge_asteroid"]), player(), prelude=True, temperature=8)

    assert player_board(game, 0)["played_prelude_cards"] == ["huge_asteroid"]
    assert player_board(game, 0)["terraform_rating"] == 20
    assert resources(game, 0)["megacredits"] == 37


def test_with_fewer_than_5_megacredits_it_cant_be_played_and_is_discarded_for_15_megacredits():
    game = scenario(player(prelude_cards=["huge_asteroid"], megacredits=4), player(), prelude=True)

    assert game.full_view()["temperature"] == -30
    assert resources(game, 0)["megacredits"] == 19
