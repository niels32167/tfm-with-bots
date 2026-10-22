"""Starting a Game, from settings and a seed or from a Scenario."""

import pytest
import tm_engine

from tests.helpers import player, player_board, scenario


def test_a_new_game_starts_in_generation_1_with_temperature_at_minus_30():
    game = tm_engine.Game(seed=7)

    view = game.player_view(0)
    assert view["generation"] == 1
    assert view["phase"] == "action"
    assert view["temperature"] == -30
    assert game.seed == 7
    assert not game.is_over


def test_until_corporations_exist_every_player_starts_with_42_megacredits_and_terraform_rating_20():
    game = tm_engine.Game(seed=7)

    for index in (0, 1):
        assert player_board(game, index) == {
            "name": f"Player {index + 1}",
            "megacredits": 42,
            "production": {"megacredits": 0},
            "terraform_rating": 20,
            "passed": False,
        }


def test_a_game_has_two_to_five_players():
    for count in (2, 3, 4, 5):
        game = tm_engine.Game(seed=7, players=count)
        assert game.players == count
        assert len(game.player_view(0)["players"]) == count

    with pytest.raises(ValueError, match="2 to 5 Players"):
        tm_engine.Game(seed=7, players=1)
    with pytest.raises(ValueError, match="2 to 5 Players"):
        tm_engine.Game(seed=7, players=6)


def test_a_scenario_sets_the_generation_temperature_and_each_players_board():
    game = scenario(
        player(megacredits=30, production={"megacredits": 3}, terraform_rating=25),
        player(megacredits=0),
        generation=4,
        temperature=-10,
        seed=99,
    )

    view = game.player_view(0)
    assert view["generation"] == 4
    assert view["temperature"] == -10
    assert game.seed == 99
    assert player_board(game, 0)["megacredits"] == 30
    assert player_board(game, 0)["production"] == {"megacredits": 3}
    assert player_board(game, 0)["terraform_rating"] == 25
    assert player_board(game, 1)["megacredits"] == 0
    assert player_board(game, 1)["terraform_rating"] == 20


def test_an_empty_scenario_is_a_new_two_player_game_with_player_1_as_first_player():
    view = scenario().player_view(0)
    new_game = tm_engine.Game(seed=0).player_view(0)

    assert view["first_player"] == 0
    assert view["current_player"] == 0
    whose_turn = {"first_player": 0, "current_player": 0}
    assert {**view, **whose_turn} == {**new_game, **whose_turn}


def test_a_scenario_with_an_unknown_field_is_rejected():
    with pytest.raises(ValueError, match="megacredit"):
        scenario(player(megacredit=30), player())


def test_a_scenario_temperature_must_be_a_step_on_the_track():
    with pytest.raises(ValueError, match="Temperature"):
        scenario(temperature=-29)
    with pytest.raises(ValueError, match="Temperature"):
        scenario(temperature=10)


def test_there_is_no_player_view_for_a_player_not_in_the_game():
    game = tm_engine.Game(seed=7)

    with pytest.raises(ValueError, match="no Player with index 2"):
        game.player_view(2)


def test_a_seed_is_a_whole_number_that_every_json_reader_keeps_exactly():
    # JSON readers such as the browser's hold numbers as doubles, exact only up to 2**53 - 1.
    assert tm_engine.MAX_SEED == 2**53 - 1
    assert tm_engine.Game(seed=tm_engine.MAX_SEED).seed == tm_engine.MAX_SEED

    with pytest.raises(ValueError, match="seed"):
        tm_engine.Game(seed=tm_engine.MAX_SEED + 1)
    with pytest.raises(ValueError, match="seed"):
        scenario(seed=tm_engine.MAX_SEED + 1)
