"""The full fuzz run, on all cores:

    uv run python -m tests.fuzzing                 # 100,000 Games from a random first seed
    uv run python -m tests.fuzzing --games 5000 --first-seed 0

Failures are saved in fuzz-failures/ as Replay files; the exit status is 1 if there are any.
"""

import argparse
import os
import random
import sys
import time

import tm_engine

from tests.fuzzing.runner import FAILURES_FOLDER, GENERATION_LIMIT, FuzzRun, fuzz


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m tests.fuzzing", description="Fuzz the engine with Random Bots.")
    parser.add_argument("--games", type=int, default=100_000, help="how many Games to play (default 100,000)")
    parser.add_argument("--first-seed", type=int, help="the seed of the first Game (default: a random one)")
    parser.add_argument("--processes", type=int, default=os.cpu_count(), help="worker processes (default: 1 per core)")
    arguments = parser.parse_args()
    first_seed = arguments.first_seed
    if first_seed is None:
        first_seed = random.randrange(tm_engine.MAX_SEED - arguments.games)

    print(
        f"Fuzzing {arguments.games:,} Games with 2 to 5 Players, seeds {first_seed} to "
        f"{first_seed + arguments.games - 1}, on {arguments.processes} processes."
    )
    started = time.perf_counter()
    reported = 0

    def report_progress(run: FuzzRun) -> None:
        nonlocal reported
        if run.games - reported >= arguments.games // 20 or run.games == arguments.games:
            reported = run.games
            seconds = time.perf_counter() - started
            print(f"  {run.games:,} Games, {len(run.failures)} failures, {seconds:.0f} s", flush=True)

    run = fuzz(arguments.games, first_seed=first_seed, processes=arguments.processes, on_progress=report_progress)
    seconds = time.perf_counter() - started
    print(
        f"{run.games:,} Games and {run.decisions:,} Decisions in {seconds:.0f} s "
        f"({run.decisions / seconds:,.0f} Decisions per second, checked). "
        f"The longest Game lasted {run.most_generations} Generations (the limit is {GENERATION_LIMIT})."
    )
    if not run.failures:
        print("No failures.")
        return 0
    print(f"{len(run.failures)} failures, saved as Replay files in {FAILURES_FOLDER}:")
    for failure in run.failures:
        print(f"  {failure.description()}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
