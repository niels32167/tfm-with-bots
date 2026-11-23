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

import torch

from ai.imitation.model import load_model
from ai.recorded_games.dataset import DATASET_FOLDER, shards
from ai.value.model import ValueModel
from ai.value.train import VALIDATION_POSITIONS, validated


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
