"""Reading the dataset the importer wrote (see ai/recorded_games/__init__.py for its format)."""

import gzip
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

DATASET_FOLDER = Path(__file__).parents[2] / ".cache" / "recorded-games"


def read_lines(folder: Path, name: str) -> Iterator[dict[str, Any]]:
    for shard in sorted((folder / "shards").glob("*")):
        if not (shard / "shard.done").exists():
            continue
        with gzip.open(shard / name, "rt", encoding="utf-8") as lines:
            for line in lines:
                yield json.loads(line)


def read_games(folder: Path = DATASET_FOLDER) -> Iterator[dict[str, Any]]:
    """Each kept Game: its settings, results, public states and Decisions."""
    return read_lines(folder, "games.jsonl.gz")


def read_moves(folder: Path = DATASET_FOLDER) -> Iterator[dict[str, Any]]:
    """Each kept Game's slim moves (ai.recorded_games.moves), in the same order as read_games."""
    return read_lines(folder, "moves.jsonl.gz")
