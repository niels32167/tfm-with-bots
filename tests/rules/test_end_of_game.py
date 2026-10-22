"""The end of the Game: after the Generation in which Temperature reaches its maximum."""

from tests.helpers import end_the_generation, pick, player, player_board, scenario


def test_the_generation_carries_on_after_temperature_reaches_its_maximum():
    game = scenario(player(megacredits=14), player(), temperature=6)

    pick(game, "Asteroid")

    assert game.player_view(0)["temperature"] == 8
    assert not game.is_over
    assert game.decision["player"] == 0


def test_the_game_ends_after_the_production_phase_of_the_generation_in_which_temperature_reached_its_maximum():
    game = scenario(player(megacredits=14, terraform_rating=37), player(megacredits=0), temperature=6)

    pick(game, "Asteroid")
    end_the_generation(game)

    assert game.is_over
    assert game.decision is None
    assert player_board(game, 0)["megacredits"] == 0 + 38  # the final Production phase still pays


def test_the_game_goes_on_while_temperature_is_below_its_maximum():
    game = scenario(player(), player(), temperature=6, generation=5)

    end_the_generation(game)

    assert not game.is_over
    assert game.player_view(0)["generation"] == 6


def test_a_game_started_at_maximum_temperature_ends_after_that_generation():
    game = scenario(player(), player(), temperature=8)

    end_the_generation(game)

    assert game.is_over


def test_the_final_score_is_each_players_terraform_rating():
    game = scenario(player(terraform_rating=31), player(terraform_rating=27), temperature=8)

    end_the_generation(game)

    assert game.scores == [
        {"player": 0, "terraform_rating": 31, "total": 31},
        {"player": 1, "terraform_rating": 27, "total": 27},
    ]


def test_every_player_sees_the_final_scores():
    game = scenario(player(terraform_rating=31), player(terraform_rating=27), temperature=8)

    end_the_generation(game)

    view = game.player_view(1)
    assert view["phase"] == "over"
    assert view["scores"] == game.scores


def test_there_are_no_scores_before_the_game_is_over():
    game = scenario(player(), player())

    assert game.scores is None
    assert game.player_view(0)["scores"] is None


def test_nobody_has_a_turn_once_the_game_is_over():
    game = scenario(player(), player(), temperature=8)

    end_the_generation(game)

    assert game.player_view(0)["current_player"] is None
