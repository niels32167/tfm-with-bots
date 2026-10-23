"""The speed benchmark (ADR 0004), on 2-player Games with a Random Bot for every Player:

    uv run python -m tools.benchmark
    uv run python -m tools.benchmark --seconds 10 --processes 8

It reports:
- complete Games per second, played out inside the engine, in one process and across all
  cores (the target is 1,000 across the development machine's 16);
- how long copying a Game takes at its start, halfway and at its end, since the Replay and
  the game log grow as it is played (the target is under 10 µs);
- for information only, how many Decisions per second a Python loop gets through, reading
  each Decision and picking an Option at random, as a Python Controller would.

The exit status is 1 if a target is missed.
"""

import argparse
import multiprocessing
import os
import random
import sys
import threading
import time
import timeit
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import tm_engine

PLAYERS = 2
TARGET_GAMES_PER_SECOND = 1_000
# ADR 0004 asks for copies "in microseconds"; this reads that as under 10 µs.
TARGET_COPY_MICROSECONDS = 10

# A guard, so that a Game that never ends stops the benchmark instead of hanging it.
MAX_PICKS = 10_000

# How many copies each timing makes, and how many timings are made: the fastest one counts.
COPIES_PER_TIMING = 10_000
TIMINGS = 5


@dataclass(frozen=True)
class CopyTime:
    moment: str
    generation: int
    picks: int
    log_lines: int
    microseconds: float


@dataclass(frozen=True)
class Results:
    seconds: float
    processes: int
    games_per_second_in_one_process: float
    games_per_second_in_all_processes: float
    copies: list[CopyTime]
    python_decisions_per_second: float

    @property
    def targets_met(self) -> bool:
        fast_enough = self.games_per_second_in_all_processes >= TARGET_GAMES_PER_SECOND
        return fast_enough and all(copy.microseconds < TARGET_COPY_MICROSECONDS for copy in self.copies)


def play_out(seed: int) -> tm_engine.Game:
    """A whole Game, played out inside the engine."""
    game = tm_engine.Game(seed=seed, players=PLAYERS)
    game.play_randomly(seed=seed, picks=MAX_PICKS)
    if not game.is_over:
        raise RuntimeError(f"Game {seed} was not over after {MAX_PICKS:,} picks")
    return game


def play_out_games(first_seed: int, seconds: float) -> int:
    """Plays whole Games out inside the engine for `seconds`. Returns how many it finished."""
    stop_at = time.perf_counter() + seconds
    games = 0
    while time.perf_counter() < stop_at:
        play_out(first_seed + games)
        games += 1
    return games


# In each worker process: the barrier that makes all of them start at once.
_start_together: threading.Barrier | None = None


def _share_barrier(barrier: threading.Barrier) -> None:
    global _start_together
    _start_together = barrier


def play_out_games_together(first_seed: int, seconds: float) -> int:
    """`play_out_games` in a worker process, once every worker is ready to start."""
    _start_together.wait()
    return play_out_games(first_seed, seconds)


def games_per_second(processes: int, seconds: float) -> float:
    """Complete Games per second across `processes` worker processes running side by side.
    Each one waits for the others, so all are playing for the same `seconds`."""
    barrier = multiprocessing.Barrier(processes)
    # Each process plays from its own range of seeds.
    first_seeds = [process * 1_000_000_000 for process in range(processes)]
    with ProcessPoolExecutor(processes, initializer=_share_barrier, initargs=(barrier,)) as pool:
        return sum(pool.map(play_out_games_together, first_seeds, [seconds] * processes)) / seconds


def copy_times() -> list[CopyTime]:
    """How long one copy takes at the start of a Game, halfway through, and at its end."""
    finished = play_out(seed=1)
    picks = len(finished.replay["picks"])
    times = []
    for moment, step in [("at the start", 0), ("halfway", picks // 2), ("at the end", picks)]:
        game = tm_engine.Game.from_replay(finished.replay, step=step)
        fastest = min(timeit.repeat(game.copy, repeat=TIMINGS, number=COPIES_PER_TIMING))
        generation = game.player_view(0)["generation"]
        times.append(CopyTime(moment, generation, step, len(game.log), fastest / COPIES_PER_TIMING * 1e6))
    return times


def python_decisions_per_second(seconds: float) -> float:
    """Decisions per second for a Python loop that reads each Decision and picks at random."""
    random_numbers = random.Random(1)
    decisions, seed = 0, 0
    started = time.perf_counter()
    while time.perf_counter() - started < seconds:
        game = tm_engine.Game(seed=seed, players=PLAYERS)
        for _ in range(MAX_PICKS):
            if (decision := game.decision) is None:
                break
            game.pick(random_numbers.randrange(len(decision["options"])))
            decisions += 1
        else:
            raise RuntimeError(f"Game {seed} was not over after {MAX_PICKS:,} picks")
        seed += 1
    return decisions / (time.perf_counter() - started)


def measure(seconds: float = 5.0, processes: int | None = None) -> Results:
    """Runs each measurement for about `seconds`, with `processes` (one per core by default)
    for the all-cores one."""
    processes = processes or os.cpu_count() or 1
    return Results(
        seconds=seconds,
        processes=processes,
        games_per_second_in_one_process=play_out_games(0, seconds) / seconds,
        games_per_second_in_all_processes=games_per_second(processes, seconds),
        copies=copy_times(),
        python_decisions_per_second=python_decisions_per_second(seconds),
    )


def report(results: Results) -> str:
    def met(fast_enough: bool) -> str:
        return "met" if fast_enough else "NOT met"

    games_target = met(results.games_per_second_in_all_processes >= TARGET_GAMES_PER_SECOND)
    lines = [
        f"Speed benchmark (ADR 0004): {PLAYERS}-player Games with a Random Bot for every Player.",
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
        "For information, a Python loop reading each Decision and picking at random:",
        f"  1 process: {results.python_decisions_per_second:,.0f} Decisions per second",
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
    arguments = parser.parse_args()
    results = measure(arguments.seconds, arguments.processes)
    print(report(results))
    return 0 if results.targets_met else 1


if __name__ == "__main__":
    sys.exit(main())
