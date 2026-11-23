"""What the Value Model learns from: one Player's view of each position of a finished Game, with that Player's result
(1 for a win, ½ for a draw, 0 for a loss) and Victory Point margin over the other Player.

Two kinds of Games give them, both as Replays the engine plays through (ai.match.views_along):
- Recorded Games not conceded, each up to its replay's first difference (ticket 10), with the result of the Recorded
  Game's log. A conceded Game's final score is no evidence of who would have won. Games whose replay never started,
  or whose log lacks a final score, give none. Games without Prelude count only if asked for: the Value Model plays
  with Prelude, but such a Game still shows who is ahead.
- the loop's own Games, which it saves a round at a time as lines of {"replay", "results", "margins"}.

At each Decision that isn't a follow-up (ai.value.encoded.FOLLOW_UPS), one of the two Players is chosen at random as
the viewer, the deciding one or not, since the Value Bot rates positions after its pick and its follow-ups, often
while the other Player decides. This module doesn't import PyTorch: it runs in the worker processes that make
training batches.
"""

import functools
import random
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from ai.imitation.encoded import Position, stack
from ai.imitation.positions import BATCHES_SORTED_TOGETHER, from_workers, shuffled
from ai.imitation.split import Split, split_of
from ai.match import PLAYERS, views_along
from ai.recorded_games.dataset import read_shard
from ai.value.encoded import FOLLOW_UPS, result_of, view_position


@dataclass(frozen=True, eq=False)
class ValueSample:
    """A position as its viewer saw it, how the Game ended for them, and their Victory Point margin."""

    position: Position
    result: float
    margin: float


def results_of(scores: list[dict[str, Any]]) -> tuple[list[float], list[int]]:
    """Each Player's result and margin over the other Player, from the engine's final scores."""
    totals = {score["player"]: score["total"] for score in scores}
    results = [result_of(scores, player) for player in range(PLAYERS)]
    margins = [totals[player] - totals[1 - player] for player in range(PLAYERS)]
    return results, margins


def replay_samples(
    replay: dict[str, Any], results: list[float], margins: list[float], rng: random.Random, keep: float = 1.0
) -> Iterator[ValueSample]:
    """A sample at a share `keep`, chosen at random, of the Decisions of `replay` that don't follow from the one
    before (FOLLOW_UPS), each seen by a Player chosen at random."""

    def viewer_at(decision: dict[str, Any]) -> int | None:
        if decision["kind"] in FOLLOW_UPS or rng.random() >= keep:
            return None
        return rng.randrange(PLAYERS)

    for _, view in views_along(replay, viewer_at):
        viewer = view["viewer"]
        yield ValueSample(view_position(view), results[viewer], margins[viewer])


def recorded_samples(
    shard: Path, split: Split, rng: random.Random, keep: float = 1.0, *, prelude_only: bool = True
) -> Iterator[ValueSample]:
    """The samples (a share `keep` of them) of one dataset shard's Games in `split`, not conceded, that have a
    replay: those with Prelude, or every one if not `prelude_only`."""
    replays = {replay["game"]: replay for replay in read_shard(shard, "replays.jsonl.gz")}
    for game in read_shard(shard, "games.jsonl.gz"):
        replay = replays.get(game["game"])
        if (
            not (replay and replay["replay"])
            or (prelude_only and not game["prelude"])
            or game["conceded"]
            or split_of(game) != split
        ):
            continue
        players = game["players"]
        winners = [board["winner"] for board in players]
        points = [board["victory_points"] for board in players]
        if sum(winners) != 1 or None in points:
            continue
        results = [float(won) for won in winners]
        margins = [points[player] - points[1 - player] for player in range(PLAYERS)]
        yield from replay_samples(replay["replay"], results, margins, rng, keep)


def self_play_samples(path: Path, rng: random.Random, keep: float = 1.0) -> Iterator[ValueSample]:
    """The samples (a share `keep` of them) of a file of the loop's Games."""
    for line in read_shard(path.parent, path.name):
        yield from replay_samples(line["replay"], line["results"], line["margins"], rng, keep)


def stack_samples(samples: list[ValueSample]) -> dict[str, np.ndarray]:
    """Samples as arrays (ai.imitation.encoded.stack), with "result" and "margin" for each."""
    stacked = stack([sample.position for sample in samples])
    stacked["result"] = np.asarray([sample.result for sample in samples], dtype=np.float32)
    stacked["margin"] = np.asarray([sample.margin for sample in samples], dtype=np.float32)
    return stacked


def file_samples(
    chosen: list[Path], *, split: Split, size: int, buffer: int, seed: int, keep: float, prelude_only: bool = True
) -> Iterator[list[ValueSample]]:
    """A worker process's batches: a share `keep` of the samples of its files (dataset shards, whose Games without
    Prelude count only if not `prelude_only`, and files of the loop's Games), shuffled through `buffer` and sorted
    into batches of about as many card rows, in a random order."""
    rng = random.Random(f"{seed}:{chosen[:1]}")
    found = (
        sample
        for path in chosen
        for sample in (
            recorded_samples(path, split, rng, keep, prelude_only=prelude_only)
            if path.is_dir()
            else self_play_samples(path, rng, keep)
        )
    )
    pool: list[ValueSample] = []
    for sample in shuffled(found, buffer, rng):
        pool.append(sample)
        if len(pool) == size * BATCHES_SORTED_TOGETHER:
            yield from sorted_batches(pool, size, rng)
            pool = []
    yield from sorted_batches(pool, size, rng)


def sorted_batches(pool: list[ValueSample], size: int, rng: random.Random) -> list[list[ValueSample]]:
    pool.sort(key=lambda sample: len(sample.position.cards))
    made = [pool[start : start + size] for start in range(0, len(pool), size)]
    rng.shuffle(made)
    return made


def sample_batches(
    sources: list[Path],
    split: Split,
    *,
    workers: int,
    seed: int,
    size: int,
    buffer: int,
    keep: float = 1.0,
    prelude_only: bool = True,
) -> Iterator[list[ValueSample]]:
    """Batches of at most `size` samples from `sources` (dataset shards, whose Games in `split` count, those without
    Prelude only if not `prelude_only`, and files of the loop's Games, which count whole), a share `keep` of each
    Game's, made in `workers` processes (0: here), never all held at once."""
    chosen = list(sources)
    random.Random(seed).shuffle(chosen)
    make = functools.partial(
        file_samples, split=split, size=size, buffer=buffer, seed=seed, keep=keep, prelude_only=prelude_only
    )
    return from_workers(make, chosen, workers)


def budgeted(
    make: Callable[[int], Iterator[list[ValueSample]]], positions: int | None = None, passes: int = 1_000_000
) -> Iterator[list[ValueSample]]:
    """Batches from `make(pass_number)`, pass after pass, until `positions` (if given) have been given or `passes`
    made."""
    given = 0
    for number in range(passes):
        made = make(number)
        found = False
        try:
            for batch in made:
                found = True
                yield batch
                given += len(batch)
                if positions is not None and given >= positions:
                    return
        finally:
            made.close()  # type: ignore[attr-defined]
        if not found:
            return
