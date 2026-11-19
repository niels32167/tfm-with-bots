"""The training Decisions of the Imitation Model: every Decision of a Recorded Game, each as its Player saw it.

A Recorded Game gives them twice over. Its records (ai.recorded_games.records) cover every Game but lack the hand,
the Tiles and Card Resources, so the encoding marks those and the Prices that need them missing. Its replay through
the engine (ticket 10), where there is one, gives the full Player View, as the Controller sees it in play, up to
the replay's first difference. So each group of Decisions (one Player's setup, or their Draft or buy in one
Generation) comes from the replay when the replay holds the whole group with the records' picks, and from the
records otherwise. Each Decision says where it came from: "source" is "replay" or "records".

Every other Decision (the Prelude Cards played and the Action phases) comes from the replay alone, as far as it
goes: the records don't describe them (ticket 14). Picks the Recorded Game's log didn't give, which the replay
inferred (a pass, the cards sold chosen in hindsight), aren't the Player's own and are left out.
"""

import contextlib
import functools
import multiprocessing
import random
import sys
import traceback
from collections import defaultdict
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from ai.card_economy import CardEconomyBot
from ai.controller import Controller, Handle
from ai.imitation.encoded import Position, stack
from ai.imitation.split import Split, split_of
from ai.recorded_games.dataset import read_shard, shards
from ai.recorded_games.records import recorded_decisions
from ai.recorded_games.replay import action_decisions, recorded_kind_decisions

type Group = tuple[int, int, str]


def group_of(decision: dict[str, Any]) -> Group:
    """Whose, which Generation, and which phase: setup, the Draft or buying."""
    return decision["player"], decision["generation"], decision["view"]["phase"]


def picks_in(decisions: list[dict[str, Any]]) -> list[tuple[str, str | None]]:
    """Each Decision's kind and the card picked, in no particular order: the records pick cards bought in card
    order, a replay in the order the Player bought them."""
    return sorted(
        (decision["kind"], decision["options"][decision["picked"]]["details"].get("card") or "")
        for decision in decisions
    )


def training_decisions(
    game: dict[str, Any], replay: dict[str, Any] | None, *, also_asked: Controller | None = None
) -> Iterator[dict[str, Any]]:
    """`game`'s setup, Draft and buy Decisions in the records' order of groups, from `replay` (its line of
    replays.jsonl.gz, or None) where it holds the whole group, from the records otherwise; then the replay's
    other Decisions whose picks the Recorded Game's log gave, each with what `also_asked` picks there, if given (see
    action_decisions)."""
    replayed: dict[Group, list[dict[str, Any]]] = defaultdict(list)
    if replay is not None:
        for decision in recorded_kind_decisions(replay):
            replayed[group_of(decision)].append(decision)
    recorded: dict[Group, list[dict[str, Any]]] = defaultdict(list)
    for decision in recorded_decisions(game):
        recorded[group_of(decision)].append(decision)
    for group, from_records in recorded.items():
        from_replay = replayed.get(group, [])
        if from_replay and picks_in(from_replay) == picks_in(from_records):
            yield from ({**decision, "source": "replay"} for decision in from_replay)
        else:
            yield from ({**decision, "source": "records"} for decision in from_records)
    if replay is not None:
        for decision in action_decisions(replay, also_asked=also_asked):
            if not decision["inferred"]:
                yield {**decision, "source": "replay"}


@dataclass(frozen=True)
class PositionSettings:
    """Which training Decisions to keep: those of Players rated at least `min_rating` (Board Game Arena's
    rating; None keeps all), and only Games with Prelude if `prelude_games_only`. For evaluation,
    `card_economy_picks` also notes what the Card Economy Bot would pick."""

    min_rating: int | None = None
    prelude_games_only: bool = False
    card_economy_picks: bool = False


def card_economy_pick(decision: dict[str, Any]) -> int | None:
    """The Option the Card Economy Bot picks, or None where the view lacks the hand (records after setup). At the
    Action-phase Decisions, the replay asked it (`training_decisions`)."""
    if "also_picked" in decision:
        return decision["also_picked"]
    view, player = decision["view"], decision["player"]
    if view["players"][player].get("hand") is None:
        return None
    # Setup, Draft and buy Decisions are priced from the cards alone, without Sampled Positions.
    handle = Handle(player, view, decision, random.Random(0), sampler=None)  # type: ignore[arg-type]
    return CardEconomyBot().explain(handle).picked


def encoded(game: dict[str, Any], decision: dict[str, Any], *, with_card_economy_pick: bool = False) -> Position:
    """A training Decision of `game` as a Position."""
    player = decision["player"]
    return Position.of(
        decision["view"],
        decision,
        game=game["game"],
        rating=game["players"][player]["rating"] or 0,
        source=decision["source"],
        picked=decision["picked"],
        card_economy_pick=card_economy_pick(decision) if with_card_economy_pick else None,
    )


def game_positions(
    game: dict[str, Any], replay: dict[str, Any] | None, settings: PositionSettings
) -> Iterator[Position]:
    """The training Decisions of one Game that `settings` keep, encoded. Decisions with one Option teach nothing."""
    if settings.prelude_games_only and not game["prelude"]:
        return
    ratings = [board["rating"] or 0 for board in game["players"]]
    also_asked = CardEconomyBot() if settings.card_economy_picks else None
    for decision in training_decisions(game, replay, also_asked=also_asked):
        if len(decision["options"]) < 2:
            continue
        if settings.min_rating is not None and ratings[decision["player"]] < settings.min_rating:
            continue
        yield encoded(game, decision, with_card_economy_pick=settings.card_economy_picks)


def shard_positions(shard: Path, split: Split, settings: PositionSettings) -> Iterator[Position]:
    """The training Decisions of one shard's Games in `split`."""
    replays = {replay["game"]: replay for replay in read_shard(shard, "replays.jsonl.gz")}
    for game in read_shard(shard, "games.jsonl.gz"):
        if split_of(game) == split:
            yield from game_positions(game, replays.get(game["game"]), settings)


# Positions a worker process sends at a time, and how many messages may wait for the trainer per worker.
CHUNK = 256
WAITING = 4
# Batches sorted together by their Options and card rows, so that a batch pads little.
BATCHES_SORTED_TOGETHER = 16
# Options in bands of up to 8, 16, 32, 64… : a batch holds Decisions of one band where it can, so that a Payment
# with 240 Options pads few rows of the many with 2 to 8.
OPTION_BAND = 8


def positions(
    folder: Path,
    split: Split,
    settings: PositionSettings,
    *,
    workers: int,
    seed: int | None = None,
    shard_share: tuple[int, int] = (0, 1),
) -> Iterator[Position]:
    """The training Decisions of the dataset in `folder` for `split`, encoded while read, never all held at once.
    `workers` processes encode them (0: this process, in the shards' order). A `seed` shuffles the order of the
    shards; `shard_share` (k, n) keeps every n-th shard from the k-th, for a quicker look at a split."""
    chosen = chosen_shards(folder, seed, shard_share)
    make = functools.partial(chunked_positions, split=split, settings=settings)
    for chunk in from_workers(make, chosen, workers):
        yield from chunk


def batches(
    folder: Path,
    split: Split,
    settings: PositionSettings,
    *,
    workers: int,
    seed: int,
    size: int,
    buffer: int,
    shard_share: tuple[int, int] = (0, 1),
) -> Iterator[dict[str, np.ndarray]]:
    """Batches of at most `size` training positions, stacked by `stack`, made in the worker processes: each
    shuffles its positions through a buffer of `buffer`, so that a Game's positions spread among many others, and
    sorts them into batches with about as many Options and card rows."""
    chosen = chosen_shards(folder, seed, shard_share)
    make = functools.partial(stacked_batches, split=split, settings=settings, size=size, buffer=buffer, seed=seed)
    return from_workers(make, chosen, workers)


def chosen_shards(folder: Path, seed: int | None, shard_share: tuple[int, int]) -> list[Path]:
    chosen = shards(folder)[shard_share[0] :: shard_share[1]]
    if seed is not None:
        random.Random(seed).shuffle(chosen)
    return chosen


def chunked_positions(chosen: list[Path], *, split: Split, settings: PositionSettings) -> Iterator[list[Position]]:
    chunk: list[Position] = []
    for shard in chosen:
        for position in shard_positions(shard, split, settings):
            chunk.append(position)
            if len(chunk) == CHUNK:
                yield chunk
                chunk = []
    if chunk:
        yield chunk


def stacked_batches(
    chosen: list[Path], *, split: Split, settings: PositionSettings, size: int, buffer: int, seed: int
) -> Iterator[dict[str, np.ndarray]]:
    rng = random.Random(f"{seed}:{chosen[:1]}")
    found = (position for shard in chosen for position in shard_positions(shard, split, settings))
    pool: list[Position] = []
    for position in shuffled(found, buffer, rng):
        pool.append(position)
        if len(pool) == size * BATCHES_SORTED_TOGETHER:
            yield from sorted_batches(pool, size, rng)
            pool = []
    yield from sorted_batches(pool, size, rng)


def option_band(position: Position) -> int:
    return ((len(position.options) - 1) // OPTION_BAND).bit_length()


def sorted_batches(pool: list[Position], size: int, rng: random.Random) -> list[dict[str, np.ndarray]]:
    pool.sort(key=lambda position: (option_band(position), len(position.cards)))
    made = [stack(pool[start : start + size]) for start in range(0, len(pool), size)]
    rng.shuffle(made)
    return made


def from_workers(make: Callable[[list[Path]], Iterator[Any]], chosen: list[Path], workers: int) -> Iterator[Any]:
    """What `make` gives for the shards `chosen`, made by `workers` processes, each with its share of the shards
    (0: made here)."""
    if workers == 0:
        if chosen:
            yield from make(chosen)
        return
    context = multiprocessing.get_context("forkserver")
    context.set_forkserver_preload([__name__])
    waiting = context.Queue(maxsize=WAITING * workers)
    shares = [chosen[number::workers] for number in range(workers)]
    started = [context.Process(target=send, args=(make, share, waiting), daemon=True) for share in shares if share]
    with main_module_left_out():
        for process in started:
            process.start()
    try:
        finished = 0
        while finished < len(started):
            made = waiting.get()
            if made is None:
                finished += 1
            elif isinstance(made, str):
                raise RuntimeError(f"a worker failed reading the dataset:\n{made}")
            else:
                yield made
    finally:
        for process in started:
            process.kill()
            process.join()


@contextlib.contextmanager
def main_module_left_out() -> Iterator[None]:
    """Worker processes started meanwhile don't import the caller's main module, as Python's do by default: the
    training command's loads PyTorch, and 12 workers holding it once ran the laptop out of memory. They need only
    this module, which the forkserver preloads."""
    main = sys.modules["__main__"]
    hidden = {name: getattr(main, name) for name in ("__spec__", "__file__") if hasattr(main, name)}
    main.__spec__ = None
    if "__file__" in hidden:
        del main.__file__
    try:
        yield
    finally:
        for name, attribute in hidden.items():
            setattr(main, name, attribute)


def send(make: Callable[[list[Path]], Iterator[Any]], chosen: list[Path], waiting: Any) -> None:
    """A worker process: puts what `make` gives for its shards on the queue `waiting`, then None (or, if it
    failed, the error's traceback)."""
    try:
        for made in make(chosen):
            waiting.put(made)
        waiting.put(None)
    except Exception:  # noqa: BLE001 -- handed to the reader, which raises it
        waiting.put(traceback.format_exc())


def shuffled(found: Iterator[Position], buffer: int, rng: random.Random) -> Iterator[Position]:
    """`found` in a random order, holding at most `buffer` positions: positions of one Game come out spread
    among those of many others."""
    held: list[Position] = []
    for position in found:
        if len(held) < buffer:
            held.append(position)
            continue
        index = rng.randrange(buffer)
        yield held[index]
        held[index] = position
    rng.shuffle(held)
    yield from held
