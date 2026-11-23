"""Saved Value Models measured on held-out positions of Recorded Games with Prelude, the Games the Value Model plays
(ticket 16's box 3). Every model is measured on the same positions, so a new warm start can be compared with the
registered model before any Match:

    uv run python -m ai.value.evaluate .cache/models/value.pt .cache/models/value-runs/<run>/versions/v000.pt

Each line gives a model's cross-entropy of the result (lower is better; a coin scores 0.693) and how often the
Player it rated likelier won. The loss compares models that learned from the same Games; a model that learned from
its own Games may rate these Players' positions worse and still play better, which only a Match can tell.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import torch

from ai.imitation.model import load_model
from ai.recorded_games.dataset import DATASET_FOLDER, shards
from ai.value.model import ValueModel
from ai.value.samples import budgeted, sample_batches
from ai.value.train import measured

# Validation positions measured: enough for a loss to two decimals.
VALIDATION_POSITIONS = 100_000


def validated(
    model: ValueModel,
    sources: list[Path],
    *,
    keep: float,
    workers: int,
    size: int,
    device: str,
    positions: int = VALIDATION_POSITIONS,
) -> dict[str, Any]:
    """`model` measured (ai.value.train.measured) on up to `positions` of the validation Games with Prelude of the
    dataset shards `sources`, a share `keep` of each Game's, always the same ones for the same arguments."""

    def made(_: int):
        return sample_batches(sources, "validation", workers=workers, seed=0, size=size, buffer=size, keep=keep)

    return measured(model, budgeted(made, positions, passes=1), device)


def arguments(given: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m ai.value.evaluate", description=__doc__.split("\n\n")[0])
    parser.add_argument("models", type=Path, nargs="+", help="saved Value Models")
    parser.add_argument("--dataset", type=Path, default=DATASET_FOLDER)
    parser.add_argument("--keep", type=float, default=0.1, help="share of each Recorded Game's positions measured")
    parser.add_argument("--positions", type=int, default=VALIDATION_POSITIONS, help="at most this many")
    parser.add_argument("--workers", type=int, default=4, help="processes making batches (0: this one)")
    parser.add_argument("--batch", type=int, default=256)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    return parser.parse_args(given)


def main(given_arguments: Sequence[str] | None = None) -> int:
    given = arguments(given_arguments)
    found = shards(given.dataset)
    for path in given.models:
        model = load_model(path, given.device, kind=ValueModel)[0]
        result = validated(
            model,
            found,
            keep=given.keep,
            workers=given.workers,
            size=given.batch,
            device=given.device,
            positions=given.positions,
        )
        print(
            f"{path} validation loss {result['loss']:.4f}, the winner rated likelier at {result['accuracy']:.1%} of "
            f"{result['positions']:,} positions",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
