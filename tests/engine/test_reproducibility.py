"""The same settings, seed and Options always give the same Game (ADR 0010)."""

import json
import subprocess
import sys
from pathlib import Path

import tm_engine

from tests.helpers import MAX_PICKS, everything_about, play_randomly

PROJECT_FOLDER = Path(__file__).parents[2]

# Rebuilds a Game from the Replay file named on the command line and prints everything about it.
REBUILD_IN_ANOTHER_PROCESS = """
import json, sys
import tm_engine
from tests.helpers import everything_about
with open(sys.argv[1]) as file:
    game = tm_engine.Game.from_replay(json.load(file))
print(json.dumps(everything_about(game)))
"""


def test_the_same_settings_seed_and_options_give_an_identical_game_and_game_log_at_every_step():
    games = [tm_engine.Game(seed=21, players=4), tm_engine.Game(seed=21, players=4)]

    for step in range(MAX_PICKS):
        if games[0].is_over:
            break
        for game in games:
            play_randomly(game, seed=step, picks=1)
        assert everything_about(games[0]) == everything_about(games[1])

    assert games[0].is_over and games[1].is_over


def test_a_replay_gives_the_identical_game_and_game_log_in_a_separate_process(tmp_path):
    game = tm_engine.Game(seed=22, players=5)
    play_randomly(game, seed=6)
    replay_file = tmp_path / "replay.json"
    replay_file.write_text(json.dumps(game.replay))

    rebuilt = subprocess.run(
        [sys.executable, "-c", REBUILD_IN_ANOTHER_PROCESS, str(replay_file)],
        cwd=PROJECT_FOLDER,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )

    assert json.loads(rebuilt.stdout) == json.loads(json.dumps(everything_about(game)))
