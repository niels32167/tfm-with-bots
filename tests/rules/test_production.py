"""The Production phase, which follows once every Player has passed."""

from tests.helpers import end_the_generation, player, player_board, scenario


def test_each_player_gains_megacredits_equal_to_terraform_rating_plus_megacredit_production():
    game = scenario(
        player(megacredits=5, terraform_rating=23, production={"megacredits": 2}),
        player(megacredits=0, terraform_rating=20, production={"megacredits": -3}),
    )

    end_the_generation(game)

    assert player_board(game, 0)["megacredits"] == 5 + 23 + 2
    assert player_board(game, 1)["megacredits"] == 0 + 20 - 3


def test_production_is_shown_on_the_player_board():
    game = scenario(player(production={"megacredits": 4}), player())

    assert player_board(game, 0)["production"] == {"megacredits": 4}
    assert player_board(game, 1)["production"] == {"megacredits": 0}


def test_a_new_generation_begins_after_production_with_nobody_passed():
    game = scenario(player(), player(), generation=3)

    end_the_generation(game)

    assert game.player_view(0)["generation"] == 4
    assert not player_board(game, 0)["passed"]
    assert not player_board(game, 1)["passed"]
    assert game.decision is not None
