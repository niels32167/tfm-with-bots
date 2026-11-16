"""Replays the dataset's Recorded Games through the engine on all cores (ticket 10 of phase 2).

    uv run python -m ai.recorded_games.replay_dataset              # every suitable Game; writes the replays
    uv run python -m ai.recorded_games.replay_dataset --sample 2000  # about 2,000 Games; writes nothing

A suitable Game has setup Decision records for both Players, which the versions naming both Players' cards
give. Each replayed Game's line in shards/NNN/replays.jsonl.gz holds the engine's Replay up to its first
difference (see ai/recorded_games/__init__.py), and the report says how many replay fully, how far the others
get, and their differences grouped by cause.
"""

import argparse
import gzip
import json
import os
import statistics
from collections import Counter, defaultdict
from collections.abc import Iterator
from multiprocessing import Pool
from pathlib import Path
from typing import Any

from ai.recorded_games.dataset import DATASET_FOLDER
from ai.recorded_games.replay import replay_game

REPLAYS = "replays.jsonl.gz"
REPORT = "replays-report.txt"
SAMPLE_REPORT = "replays-sample-report.txt"
RATING_BANDS = ((0, "below 300"), (300, "300-399"), (400, "400-499"), (500, "500-599"), (600, "600+"))
EXAMPLES = 3


def suitable(game: dict[str, Any]) -> bool:
    """Whether a Game names both Players' dealt cards, as its setup records show."""
    return {d["player"] for d in game["decisions"] if d["kind"] == "setup"} == {0, 1}


def rating_band(game: dict[str, Any]) -> str:
    ratings = [player.get("rating") for player in game["players"]]
    if None in ratings:
        return "unknown"
    return [band for floor, band in RATING_BANDS if min(ratings) >= floor][-1]


def games_in(shard: Path) -> Iterator[tuple[dict[str, Any], dict[str, Any]]]:
    with (
        gzip.open(shard / "games.jsonl.gz", "rt", encoding="utf-8") as games,
        gzip.open(shard / "moves.jsonl.gz", "rt", encoding="utf-8") as moves,
    ):
        for game_line, moves_line in zip(games, moves, strict=True):
            yield json.loads(game_line), json.loads(moves_line)


def replay_shard(job: tuple[Path, int, bool]) -> list[dict[str, Any]]:
    """Replays every `every`-th suitable Game of a shard; with `write`, saves them in the shard."""
    shard, every, write = job
    rows, records = [], []
    seen = 0
    for game, slim in games_in(shard):
        if not suitable(game):
            continue
        seen += 1
        if (seen - 1) % every:
            continue
        outcome = replay_game(game, slim)
        difference = outcome.difference.__dict__ if outcome.difference else None
        records.append({
            "game": outcome.game,
            "complete": outcome.complete,
            "decisions": len(outcome.replay.get("picks", [])),
            "difference": difference,
            "moves": outcome.moves,
            "moves_reached": outcome.moves_reached,
            "generation": outcome.generation,
            "replay": outcome.replay,
            "inferred": outcome.inferred,
        })  # fmt: skip
        rows.append({
            "game": outcome.game,
            "complete": outcome.complete,
            "cause": difference["cause"] if difference else None,
            "detail": difference["detail"] if difference else None,
            "prelude": game["prelude"],
            "conceded": game["conceded"],
            "band": rating_band(game),
            "generations": game["generations"],
            "generation": outcome.generation,
            "moves": outcome.moves,
            "moves_reached": outcome.moves_reached,
            "decisions": len(outcome.replay.get("picks", [])),
            "unlogged": dict(outcome.unlogged),
        })  # fmt: skip
    if write:
        temporary = shard / f"{REPLAYS}.partial"
        with gzip.open(temporary, "wt", encoding="utf-8") as out:
            for record in records:
                out.write(json.dumps(record, separators=(",", ":")) + "\n")
        os.replace(temporary, shard / REPLAYS)
    return rows


def share(part: float, whole: float) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "-"


def report(rows: list[dict[str, Any]]) -> str:
    lines = []
    total = len(rows)
    complete = sum(row["complete"] for row in rows)
    lines.append(f"Games replayed: {total}; replayed fully: {complete} ({share(complete, total)})")
    lines.append("")
    lines.append(f"{'':34}{'Games':>8}{'fully':>8}{'share':>8}")
    groups: dict[str, list[dict[str, Any]]] = {
        "Prelude, not conceded": [r for r in rows if r["prelude"] and not r["conceded"]],
        "Prelude, conceded": [r for r in rows if r["prelude"] and r["conceded"]],
        "No Prelude, not conceded": [r for r in rows if not r["prelude"] and not r["conceded"]],
        "No Prelude, conceded": [r for r in rows if not r["prelude"] and r["conceded"]],
    }
    for _, band in RATING_BANDS:
        groups[f"Lower rating {band}"] = [r for r in rows if r["band"] == band]
    for _, band in RATING_BANDS[3:]:
        groups[f"Lower rating {band}, not conceded"] = [r for r in rows if r["band"] == band and not r["conceded"]]
    for label, group in groups.items():
        done = sum(r["complete"] for r in group)
        lines.append(f"{label:34}{len(group):8}{done:8}{share(done, len(group)):>8}")
    partial = [r for r in rows if not r["complete"]]
    if partial:
        reached = [r["moves_reached"] / r["moves"] for r in partial if r["moves"]]
        lines.append("")
        lines.append(f"Games replayed partly: {len(partial)}")
        mean, median = statistics.mean(reached), statistics.median(reached)
        lines.append(f"  share of their moves replayed: mean {mean:.2f}, median {median:.2f}")
        lines.append(
            f"  Decisions before the first difference: mean {statistics.mean(r['decisions'] for r in partial):.0f}"
        )
        by_generation = Counter(min(r["generation"], 12) for r in partial)
        lines.append(
            "  Generation of the first difference: "
            + ", ".join(f"{g}{'+' if g == 12 else ''}: {by_generation[g]}" for g in sorted(by_generation))
        )
    decisions = sum(r["decisions"] for r in rows)
    lines.append("")
    lines.append(f"Decisions in the replays (every Decision before a Game's first difference): {decisions}")
    lines.append("")
    lines.append("Differences by cause (the first in each Game):")
    causes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in partial:
        causes[row["cause"]].append(row)
    for cause, group in sorted(causes.items(), key=lambda item: -len(item[1])):
        examples = "; ".join(f"{r['game']} ({r['detail'][:60]})" for r in group[:EXAMPLES])
        lines.append(f"  {len(group):6} {share(len(group), total):>6}  {cause}  e.g. {examples}")
    unlogged = Counter()
    for row in rows:
        unlogged.update(row["unlogged"])
    lines.append("")
    lines.append("Decisions the log left open, settled by the trackers, the engine or hindsight:")
    for kind, count in unlogged.most_common():
        lines.append(f"  {count:8}  {kind}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--sample", type=int, help="replay about this many Games, spread over the shards, and write nothing"
    )
    parser.add_argument("--folder", type=Path, default=DATASET_FOLDER)
    arguments = parser.parse_args()
    shards = sorted(path for path in (arguments.folder / "shards").glob("*") if (path / "shard.done").exists())
    every = 1
    if arguments.sample:
        suitable_games = 44_714  # Games with both Players' setup records; only sets the spacing.
        every = max(1, suitable_games // arguments.sample)
    with Pool() as pool:
        rows = [
            row
            for shard_rows in pool.imap_unordered(replay_shard, [(s, every, not arguments.sample) for s in shards])
            for row in shard_rows
        ]
    text = report(rows)
    (arguments.folder / (SAMPLE_REPORT if arguments.sample else REPORT)).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
