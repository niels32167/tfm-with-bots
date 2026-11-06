"""The fuzzer: it plays Random Bot Games from normal setup, each Player with a Corporation of those
dealt, and checks the invariants after every Decision and at the end of every Game (ticket 06).

Game `seed` has the settings `settings_for(seed)`, and its Random Bot picks come from the same
seed. Every failure (a broken invariant, an error from the engine or from a check, or a
Game still going past a fuzzing guard) is saved as a Replay file in fuzz-failures/, which
the GUI's Load Replay… opens at the moment it went wrong.
"""

import json
import os
import random
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tm_engine

from tests.fuzzing.invariants import (
    AFTER_EVERY_DECISION,
    AT_THE_END_OF_THE_GAME,
    Check,
    cards_in_play,
)

FAILURES_FOLDER = Path(__file__).parents[2] / "fuzz-failures"

# Fuzzing guards, not rules. Random Bot Games end after about 16 to 25 Generations on average
# (5 down to 2 Players), and about 970 to 650 picks with the Draft (750 to 510 without), at most
# about 1,500. The pick limit catches a Game that stalls inside a Generation.
GENERATION_LIMIT = 100
PICK_LIMIT = 50_000

# How many Games a worker process plays before reporting back.
GAMES_PER_BATCH = 25

type Pick = Callable[[random.Random, dict[str, Any]], int]


def pick_at_random(random_numbers: random.Random, decision: dict[str, Any]) -> int:
    """What a Random Bot picks: any offered Option, each equally likely."""
    return random_numbers.randrange(len(decision["options"]))


def settings_for(seed: int) -> dict[str, Any]:
    """The settings of fuzzed Game `seed`: 2, 3, 4 and 5 Players in turn, and the Draft on for seeds
    0 to 3, 8 to 11 and so on, and off for the others, so that every Player count meets both."""
    return {"players": 2 + seed % 4, "draft": seed // 4 % 2 == 0}


@dataclass(frozen=True)
class Failure:
    """A fuzzed Game that went wrong. Its Replay brings the Game back to that moment. If the
    engine raised an error on a pick, the Replay stops just before it, and `failing_pick` is
    the Option whose pick raised it there."""

    seed: int
    players: int
    problems: list[str]
    replay: dict[str, Any]
    failing_pick: int | None = None

    def description(self) -> str:
        picks = len(self.replay["picks"])
        return f"{self.players} Players, seed {self.seed}, after {picks} picks: {'; '.join(self.problems)}"


@dataclass(frozen=True)
class FuzzedGame:
    seed: int
    players: int
    decisions: int
    generations: int
    failure: Failure | None
    cards_played: frozenset[str]


def fuzz_game(
    seed: int,
    players: int,
    *,
    draft: bool = True,
    after_every_decision: Sequence[Check] = AFTER_EVERY_DECISION,
    at_the_end: Sequence[Check] = AT_THE_END_OF_THE_GAME,
    generation_limit: int = GENERATION_LIMIT,
    pick_limit: int = PICK_LIMIT,
    pick: Pick = pick_at_random,
) -> FuzzedGame:
    """Plays one Game with a Random Bot for every Player, checking it after every Decision,
    until it is over or something goes wrong."""
    game = tm_engine.Game(seed=seed, players=players, draft=draft)
    start = game.replay["start"]
    random_numbers = random.Random(seed)
    picks: list[int] = []
    generation = 1
    decision = None
    failing_pick = None
    view = None
    try:
        while True:
            view, decision = game.full_view(), game.decision
            generation = view["generation"]
            problems = [problem for check in after_every_decision for problem in check(view, decision)]
            if decision is None:
                problems += [problem for check in at_the_end for problem in check(view, decision)]
            if generation > generation_limit:
                problems.append(
                    f"the Game is still going in Generation {generation}, "
                    f"past the fuzzing limit of {generation_limit} Generations"
                )
            if decision is not None and len(picks) >= pick_limit:
                problems.append(f"the Game is still going after {len(picks):,} picks, past the fuzzing limit")
            if problems or decision is None:
                break
            failing_pick = pick(random_numbers, decision)
            game.pick(failing_pick, decision["sequence"])
            picks.append(failing_pick)
            failing_pick = None
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException as error:  # A panic in the engine arrives as a BaseException.
        problems = [f"{what_was_going_on(decision, failing_pick)} raised {type(error).__name__}: {error}"]
    replay = {"start": start, "picks": picks}
    failure = Failure(seed, players, problems, replay, failing_pick) if problems else None
    boards = view["players"] if view else []
    cards_played = frozenset(card for board in boards for card in cards_in_play(board))
    return FuzzedGame(seed, players, len(picks), generation, failure, cards_played)


def what_was_going_on(decision: dict[str, Any] | None, failing_pick: int | None) -> str:
    """'picking Option 3 (Pass)', or 'checking the Game' when no pick was under way."""
    if decision is None or failing_pick is None:
        return "checking the Game"
    labels = [option["label"] for option in decision["options"]]
    label = labels[failing_pick] if 0 <= failing_pick < len(labels) else "not offered"
    return f"picking Option {failing_pick} ({label})"


@dataclass
class FuzzRun:
    games: int = 0
    decisions: int = 0
    most_generations: int = 0
    failures: list[Failure] = field(default_factory=list)
    cards_played: set[str] = field(default_factory=set)

    @property
    def cards_never_played(self) -> list[str]:
        """The catalog's cards, Corporations included, that no fuzzed Game had in play at its end."""
        return [card["id"] for card in tm_engine.card_catalog() if card["id"] not in self.cards_played]

    def add(self, game: FuzzedGame) -> None:
        self.games += 1
        self.decisions += game.decisions
        self.most_generations = max(self.most_generations, game.generations)
        self.cards_played |= game.cards_played
        if game.failure:
            self.failures.append(game.failure)


def fuzz_batch(seeds: Iterable[int]) -> list[FuzzedGame]:
    """Fuzzes Game `seed` for each seed, in one worker process."""
    return [fuzz_game(seed, **settings_for(seed)) for seed in seeds]


def fuzz(
    games: int,
    *,
    first_seed: int,
    processes: int | None = None,
    failures_folder: Path = FAILURES_FOLDER,
    on_progress: Callable[[FuzzRun], None] | None = None,
) -> FuzzRun:
    """Fuzzes `games` Games from `first_seed` on, spread over `processes` (all cores by
    default), and saves every failure in `failures_folder`."""
    seeds = range(first_seed, first_seed + games)
    batches = [seeds[start : start + GAMES_PER_BATCH] for start in range(0, games, GAMES_PER_BATCH)]
    run = FuzzRun()
    with ProcessPoolExecutor(processes or os.cpu_count()) as pool:
        for batch in pool.map(fuzz_batch, batches):
            for game in batch:
                run.add(game)
                if game.failure:
                    save_failure(game.failure, failures_folder)
            if on_progress:
                on_progress(run)
    return run


def save_failure(failure: Failure, folder: Path) -> Path:
    """Saves the failure as a Replay file with every Player set to human, so that the GUI
    opens it at the moment it went wrong and Undo steps back from there."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{failure.players}-players-seed-{failure.seed}.json"
    file = {
        "controllers": ["human"] * failure.players,
        "replay": failure.replay,
        "problems": failure.problems,
        "failing_pick": failure.failing_pick,
    }
    path.write_text(json.dumps(file, indent=1, ensure_ascii=False) + "\n")
    return path
