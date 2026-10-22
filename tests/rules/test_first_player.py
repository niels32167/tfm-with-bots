"""The first-player marker: who takes the first Turn of each Generation."""

import pytest
import tm_engine

from tests.helpers import end_the_generation, pick, player, scenario


def test_the_first_player_marker_moves_to_the_next_player_every_generation():
    game = scenario(player(), player(), player(), first_player=0)

    first_players = []
    for _ in range(4):
        first_players.append(game.player_view(0)["first_player"])
        end_the_generation(game)

    assert first_players == [0, 1, 2, 0]


def test_the_first_player_takes_the_first_turn_and_turns_go_round_the_table_from_them():
    game = scenario(player(), player(), player(), first_player=2)

    turns = []
    for _ in range(3):
        turns.append(game.decision["player"])
        pick(game, "Pass")

    assert turns == [2, 0, 1]


def test_a_new_game_picks_the_first_player_from_the_seed():
    def first_player(seed: int) -> int:
        return tm_engine.Game(seed=seed, players=5).player_view(0)["first_player"]

    first_players = [first_player(seed) for seed in range(40)]

    assert set(first_players) == {0, 1, 2, 3, 4}
    assert [first_player(seed) for seed in range(40)] == first_players


def test_a_scenarios_first_player_must_be_in_the_game():
    with pytest.raises(ValueError, match="first player"):
        scenario(player(), player(), first_player=2)
