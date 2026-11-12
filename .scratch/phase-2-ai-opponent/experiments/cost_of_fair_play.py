"""The cost of playing fair (ticket 07): the Flat Playout Bot (ai/flat_playout.py) against itself, one
side looking ahead on Sampled Positions as every Controller must, the other cheating on copies of the
real Game, as bots_experiment.py's flat_mc does. Same algorithm, same seeds; only the positions differ.

    PYTHONPATH=. uv run python .scratch/phase-2-ai-opponent/experiments/cost_of_fair_play.py --games 200 --playouts 20

It may import the engine and hand a Controller the real Game: it is an experiment, not a Controller.
The report is the Match tool's, with "fair" as a and "cheating" as b.
"""

import argparse
import dataclasses
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat

import tm_engine

from ai.controller import handle_for, offered
from ai.flat_playout import FlatPlayout
from ai.match import PLAYERS, GameResult, MatchResult, MatchSettings, report

NAMES = ("fair", "cheating")


class Copies:
    """A sampler that cheats: each 'sample' is a copy of the real Game, hidden cards and all."""

    def __init__(self, game: tm_engine.Game) -> None:
        self.game = game

    def sample(self, *, seed: int) -> tm_engine.Game:
        return self.game.copy()


def play_game(seed: int, sides: tuple[int, int], playouts: int, settings: MatchSettings) -> GameResult:
    """One Game: Player 1 is side `sides[0]`, Player 2 side `sides[1]`; side 0 plays fair."""
    game = tm_engine.Game(seed=seed, players=PLAYERS, draft=settings.draft, prelude=settings.prelude)
    start, first_player = game.replay["start"], game.player_view(0)["first_player"]
    bots = [FlatPlayout(playouts) for _ in sides]
    random_sources = [random.Random(f"{seed}/{player}") for player in range(PLAYERS)]
    picks: list[int] = []
    while (decision := game.decision) is not None and len(picks) < settings.pick_limit:
        player = decision["player"]
        handle = handle_for(game, random_sources[player])
        if sides[player] == 1:
            handle = dataclasses.replace(handle, sampler=Copies(game))
        index = bots[player].pick(handle)
        assert offered(decision, index)
        game.pick(index, decision["sequence"])
        picks.append(index)
    return GameResult(
        seed=seed,
        controllers=(NAMES[sides[0]], NAMES[sides[1]]),
        sides=sides,
        outcome="over" if game.is_over else "stalled",
        replay={"start": start, "picks": picks},
        generations=game.player_view(0)["generation"],
        first_player=first_player,
        scores=game.scores,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--games", type=int, default=200, help="an even number (default 200)")
    parser.add_argument("--first-seed", type=int, default=0)
    parser.add_argument("--playouts", type=int, default=20, help="per Option (default 20)")
    parser.add_argument("--processes", type=int)
    arguments = parser.parse_args()
    settings = MatchSettings()
    seeds = [seed for seed in range(arguments.first_seed, arguments.first_seed + arguments.games // 2) for _ in (0, 1)]
    sides = [(first, 1 - first) for _ in range(arguments.games // 2) for first in (0, 1)]
    started = time.perf_counter()
    with ProcessPoolExecutor(arguments.processes) as pool:
        games = tuple(pool.map(play_game, seeds, sides, repeat(arguments.playouts), repeat(settings), chunksize=1))
    print(report(MatchResult(NAMES, settings, games)))
    print(f"\n{arguments.playouts} playouts per Option; {time.perf_counter() - started:,.0f} s.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
