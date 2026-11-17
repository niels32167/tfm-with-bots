"""The speed benchmark (ADR 0004), on 2-player Games with the Draft and a Random Bot for every Player:

    uv run python -m tools.benchmark
    uv run python -m tools.benchmark --seconds 10 --processes 8
    uv run python -m tools.benchmark --prelude

`--prelude` plays Games with Prelude instead. It reports:
- complete Games per second, played out inside the engine, in one process and across all
  cores (the target is 1,000 across the development machine's 16);
- how long copying a Game takes at its start, halfway and at its end, since the Replay and
  the game log grow as it is played (the target is under 10 µs);
- how long making a Sampled Position takes at those moments, for the Player whose Decision it is
  (the target is under 10 µs, as for a copy), and for information, how long making the Sampler that
  makes them takes, which every Controller's handle does once;
- for information only, how long encoding a position and its Options (ai.encoding, ticket 12 of phase 2)
  takes at the start of a Game, halfway and near its end, beside the Player View it is made from; a Random
  Bot buys more cards than people do, so its hands, and the time, are larger;
- for information only, how many Decisions per second a Python loop gets through, reading
  each Decision and picking an Option at random, as a Python Controller would;
- for information only, the mean Generations of these Games without Prelude and with it
  (both, whether or not `--prelude` is given), as a check that Prelude shortens Games (ADR 0011).

The exit status is 1 if a target is missed.
"""

import argparse
import functools
import multiprocessing
import os
import random
import sys
import threading
import time
import timeit
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import tm_engine

from ai.encoding import encode

PLAYERS = 2
TARGET_GAMES_PER_SECOND = 1_000
# ADR 0004 asks for copies "in microseconds"; this reads that as under 10 µs. Ticket 07 of phase 2 asks the
# same of a Sampled Position.
TARGET_COPY_MICROSECONDS = 10
TARGET_SAMPLE_MICROSECONDS = 10

# A guard, so that a Game that never ends stops the benchmark instead of hanging it.
MAX_PICKS = 10_000

# How many copies or samples each timing makes, and how many timings are made: the fastest one counts.
CALLS_PER_TIMING = 10_000
TIMINGS = 5

# Encoding takes far longer than a copy, so fewer calls make each of its timings.
ENCODINGS_PER_TIMING = 200

# How many Games the mean Generations are taken over, with Prelude and without.
GAMES_FOR_MEAN_GENERATIONS = 2_000


@dataclass(frozen=True)
class CopyTime:
    moment: str
    generation: int
    picks: int
    log_lines: int
    microseconds: float


@dataclass(frozen=True)
class SampleTime:
    moment: str
    generation: int
    microseconds: float
    sampler_microseconds: float

    @property
    def fast_enough(self) -> bool:
        return self.microseconds < TARGET_SAMPLE_MICROSECONDS


@dataclass(frozen=True)
class EncodingTime:
    moment: str
    generation: int
    microseconds: float
    player_view_microseconds: float


@dataclass(frozen=True)
class MeanGenerations:
    games: int
    without_prelude: float
    with_prelude: float


@dataclass(frozen=True)
class Results:
    seconds: float
    processes: int
    prelude: bool
    games_per_second_in_one_process: float
    games_per_second_in_all_processes: float
    copies: list[CopyTime]
    samples: list[SampleTime]
    encodings: list[EncodingTime]
    python_decisions_per_second: float
    mean_generations: MeanGenerations

    @property
    def targets_met(self) -> bool:
        fast_enough = self.games_per_second_in_all_processes >= TARGET_GAMES_PER_SECOND
        copies_fast = all(copy.microseconds < TARGET_COPY_MICROSECONDS for copy in self.copies)
        return fast_enough and copies_fast and all(sample.fast_enough for sample in self.samples)


def new_game(seed: int, prelude: bool) -> tm_engine.Game:
    """A new Game as the benchmark plays it: 2 Players, the Draft, and Prelude if `prelude` is true."""
    return tm_engine.Game(seed=seed, players=PLAYERS, draft=True, prelude=prelude)


def play_out(seed: int, prelude: bool = False) -> tm_engine.Game:
    """A whole Game, played out inside the engine."""
    game = new_game(seed, prelude)
    game.play_randomly(seed=seed, picks=MAX_PICKS)
    if not game.is_over:
        raise RuntimeError(f"Game {seed} was not over after {MAX_PICKS:,} picks")
    return game


def play_out_games(first_seed: int, seconds: float, prelude: bool) -> int:
    """Plays whole Games out inside the engine for `seconds`. Returns how many it finished."""
    stop_at = time.perf_counter() + seconds
    games = 0
    while time.perf_counter() < stop_at:
        play_out(first_seed + games, prelude)
        games += 1
    return games


# In each worker process: the barrier that makes all of them start at once.
_start_together: threading.Barrier | None = None


def _share_barrier(barrier: threading.Barrier) -> None:
    global _start_together
    _start_together = barrier


def play_out_games_together(first_seed: int, seconds: float, prelude: bool) -> int:
    """`play_out_games` in a worker process, once every worker is ready to start."""
    _start_together.wait()
    return play_out_games(first_seed, seconds, prelude)


def games_per_second(processes: int, seconds: float, prelude: bool) -> float:
    """Complete Games per second across `processes` worker processes running side by side.
    Each one waits for the others, so all are playing for the same `seconds`."""
    barrier = multiprocessing.Barrier(processes)
    # Each process plays from its own range of seeds.
    first_seeds = [process * 1_000_000_000 for process in range(processes)]
    with ProcessPoolExecutor(processes, initializer=_share_barrier, initargs=(barrier,)) as pool:
        games = pool.map(play_out_games_together, first_seeds, [seconds] * processes, [prelude] * processes)
        return sum(games) / seconds


def moments(prelude: bool) -> list[tuple[str, int, tm_engine.Game]]:
    """A Game at its start, halfway through and at its end, each with its name and pick count, as the
    Replay and the game log grow while it is played."""
    finished = play_out(seed=1, prelude=prelude)
    picks = len(finished.replay["picks"])
    steps = [("at the start", 0), ("halfway", picks // 2), ("at the end", picks)]
    return [(moment, step, tm_engine.Game.from_replay(finished.replay, step=step)) for moment, step in steps]


def microseconds_per_call(call: Callable[[], object], calls: int = CALLS_PER_TIMING) -> float:
    """How long one call takes, by the fastest of a few timings of `calls` calls."""
    return min(timeit.repeat(call, repeat=TIMINGS, number=calls)) / calls * 1e6


def copy_times(prelude: bool) -> list[CopyTime]:
    """How long one copy takes at the start of a Game, halfway through, and at its end."""
    times = []
    for moment, step, game in moments(prelude):
        generation = game.player_view(0)["generation"]
        times.append(CopyTime(moment, generation, step, len(game.log), microseconds_per_call(game.copy)))
    return times


def sample_times(prelude: bool) -> list[SampleTime]:
    """How long one Sampled Position, and one Sampler, take at the start of a Game, halfway through, and
    at its end, for the Player whose Decision it is (Player 1's at the end)."""
    times = []
    for moment, _, game in moments(prelude):
        player = game.decision["player"] if game.decision else 0
        sample = functools.partial(game.sampler(player).sample, seed=1)
        sampler = functools.partial(game.sampler, player)
        generation = game.player_view(0)["generation"]
        times.append(SampleTime(moment, generation, microseconds_per_call(sample), microseconds_per_call(sampler)))
    return times


def encoding_times(prelude: bool) -> list[EncodingTime]:
    """How long encoding the deciding Player's position and Options takes, and for comparison their Player
    View, at the start of a Game, halfway through, and at its last Decision."""
    times = []
    for moment, step, game in moments(prelude):
        if game.decision is None:
            moment, game = "near the end", tm_engine.Game.from_replay(game.replay, step=step - 1)
        decision = game.decision
        view = game.player_view(decision["player"])
        generation = view["generation"]
        encoding = microseconds_per_call(functools.partial(encode, view, decision), ENCODINGS_PER_TIMING)
        player_view = microseconds_per_call(functools.partial(game.player_view, decision["player"]))
        times.append(EncodingTime(moment, generation, encoding, player_view))
    return times


def python_decisions_per_second(seconds: float, prelude: bool) -> float:
    """Decisions per second for a Python loop that reads each Decision and picks at random."""
    random_numbers = random.Random(1)
    decisions, seed = 0, 0
    started = time.perf_counter()
    while time.perf_counter() - started < seconds:
        game = new_game(seed, prelude)
        for _ in range(MAX_PICKS):
            if (decision := game.decision) is None:
                break
            game.pick(random_numbers.randrange(len(decision["options"])))
            decisions += 1
        else:
            raise RuntimeError(f"Game {seed} was not over after {MAX_PICKS:,} picks")
        seed += 1
    return decisions / (time.perf_counter() - started)


def mean_generations(games: int, prelude: bool) -> float:
    """The mean of the Generations that `games` Games, from seed 0 on, last."""
    return sum(play_out(seed, prelude).player_view(0)["generation"] for seed in range(games)) / games


def measure(
    seconds: float = 5.0,
    processes: int | None = None,
    prelude: bool = False,
    games_for_mean_generations: int = GAMES_FOR_MEAN_GENERATIONS,
) -> Results:
    """Runs each measurement for about `seconds`, with `processes` (one per core by default)
    for the all-cores one, on Games with Prelude if `prelude` is true. The mean Generations are
    taken over `games_for_mean_generations` Games with Prelude and as many without."""
    processes = processes or os.cpu_count() or 1
    return Results(
        seconds=seconds,
        processes=processes,
        prelude=prelude,
        games_per_second_in_one_process=play_out_games(0, seconds, prelude) / seconds,
        games_per_second_in_all_processes=games_per_second(processes, seconds, prelude),
        copies=copy_times(prelude),
        samples=sample_times(prelude),
        encodings=encoding_times(prelude),
        python_decisions_per_second=python_decisions_per_second(seconds, prelude),
        mean_generations=MeanGenerations(
            games_for_mean_generations,
            without_prelude=mean_generations(games_for_mean_generations, prelude=False),
            with_prelude=mean_generations(games_for_mean_generations, prelude=True),
        ),
    )


def report(results: Results) -> str:
    def met(fast_enough: bool) -> str:
        return "met" if fast_enough else "NOT met"

    games_target = met(results.games_per_second_in_all_processes >= TARGET_GAMES_PER_SECOND)
    played_with = "the Draft and Prelude" if results.prelude else "the Draft"
    lines = [
        f"Speed benchmark (ADR 0004): {PLAYERS}-player Games with {played_with} and a Random Bot for every Player.",
        "",
        "Complete Games played out inside the engine:",
        f"  1 process:    {results.games_per_second_in_one_process:9,.0f} Games per second",
        f"  {results.processes} processes: {results.games_per_second_in_all_processes:9,.0f} Games per second "
        f"(target {TARGET_GAMES_PER_SECOND:,}: {games_target})",
        "",
        f"Copying a Game (target under {TARGET_COPY_MICROSECONDS} µs):",
        *(
            f"  {copy.moment:12} (Generation {copy.generation:2}, {copy.picks:4} picks, "
            f"{copy.log_lines:5} log lines): {copy.microseconds:6.2f} µs "
            f"({met(copy.microseconds < TARGET_COPY_MICROSECONDS)})"
            for copy in results.copies
        ),
        "",
        (
            f"Making a Sampled Position for the deciding Player (target under {TARGET_SAMPLE_MICROSECONDS} µs), "
            "and for information, its Sampler:"
        ),
        *(
            f"  {sample.moment:12} (Generation {sample.generation:2}): {sample.microseconds:6.2f} µs "
            f"({met(sample.fast_enough)}); Sampler {sample.sampler_microseconds:6.2f} µs"
            for sample in results.samples
        ),
        "",
        "Encoding a position and its Options for the deciding Player (ai.encoding), for information, beside their Player View:",
        *(
            f"  {encoding.moment:12} (Generation {encoding.generation:2}): {encoding.microseconds:6.0f} µs; "
            f"Player View {encoding.player_view_microseconds:4.0f} µs"
            for encoding in results.encodings
        ),
        "",
        "For information, a Python loop reading each Decision and picking at random:",
        f"  1 process: {results.python_decisions_per_second:,.0f} Decisions per second",
        "",
        f"For information, over {results.mean_generations.games:,} Games each:",
        f"  Mean Generations of Random Bot Games, without Prelude: {results.mean_generations.without_prelude:5.2f}",
        f"                                           with Prelude: {results.mean_generations.with_prelude:5.2f}",
        "",
        "Every target met." if results.targets_met else "A target was NOT met.",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.benchmark", description=__doc__.splitlines()[0])
    parser.add_argument("--seconds", type=float, default=5.0, help="how long each measurement runs (default 5)")
    parser.add_argument(
        "--processes", type=int, default=os.cpu_count(), help="for the all-cores run (default: one per core)"
    )
    parser.add_argument("--prelude", action="store_true", help="play Games with Prelude")
    arguments = parser.parse_args()
    results = measure(arguments.seconds, arguments.processes, arguments.prelude)
    print(report(results))
    return 0 if results.targets_met else 1


if __name__ == "__main__":
    sys.exit(main())
