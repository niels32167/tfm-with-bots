"""Trains the Imitation Model on the dataset's training Games (ai.imitation.split), encoding positions while it
trains (ai.imitation.positions), so that only the gzipped Games and a shuffle buffer sit in memory.

    uv run python -m ai.imitation.train --positions 20000000
    uv run python -m ai.imitation.train --min-rating 500 --prelude-games-only --out .cache/models/strong.pt

`--positions` is how many training positions to learn from in all, counting repeats; the learning rate warms up
and then falls along a cosine to a tenth by then. Every `--validate-every` positions it reports the loss and
accuracy on the validation Games and saves the model (`--out`) and a checkpoint beside it (`<out>.checkpoint`).
Run the same command again, with the same or a larger `--positions`, and it resumes from the checkpoint; with
other settings it refuses, and says so.

The model is saved with the encoding's format, its settings and its validation results (ai.imitation.model).
Exit status: 0, or 2 for wrong arguments or settings that don't match the checkpoint.
"""

import argparse
import math
import random
import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.nn.functional import cross_entropy

from ai.encoding import format_stamp
from ai.imitation import MODEL
from ai.imitation.model import Batch, ImitationModel, ModelShape, batch_of, save_model, scored
from ai.imitation.positions import PositionSettings, batches
from ai.recorded_games.dataset import DATASET_FOLDER

WRONG_ARGUMENTS = 2

# Positions each worker process holds to shuffle: with as many again sorted into batches, about 70 MB a worker.
SHUFFLE_BUFFER = 4_096
# Worker processes for validation, which start while the training's still hold their buffers.
VALIDATION_WORKERS = 4
# The share of the training budget spent warming up the learning rate, and where the cosine ends.
WARM_UP = 0.02
LAST_LEARNING_RATE = 0.1
# The settings a resumed run must share with its checkpoint.
FIXED_SETTINGS = ("dataset", "min_rating", "prelude_games_only", "width", "layers", "heads", "batch")
FIXED_SETTINGS += ("learning_rate", "seed", "validation_share")


def arguments(given: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m ai.imitation.train", description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", type=Path, default=DATASET_FOLDER, help="(default .cache/recorded-games)")
    parser.add_argument("--out", type=Path, default=MODEL, help="where to save the model")
    parser.add_argument("--positions", type=int, default=10_000_000, help="training positions in all")
    parser.add_argument("--min-rating", type=int, help="learn only from Players rated at least this")
    parser.add_argument("--prelude-games-only", action="store_true", help="leave out Games without Prelude")
    parser.add_argument("--width", type=int, default=ModelShape.width)
    parser.add_argument("--layers", type=int, default=ModelShape.layers)
    parser.add_argument("--heads", type=int, default=ModelShape.heads)
    parser.add_argument("--batch", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--workers", type=int, default=12, help="processes encoding positions (0: this one)")
    parser.add_argument("--validate-every", type=int, default=500_000, help="positions between validations")
    parser.add_argument("--validation-share", type=int, default=8, help="validate on every n-th shard")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--compile", action="store_true", help="compile the model (faster on the GPU)")
    return parser.parse_args(given)


def settings_of(given: argparse.Namespace) -> dict[str, Any]:
    """What the run is trained with, as saved with the model."""
    return {
        "dataset": str(given.dataset),
        "min_rating": given.min_rating,
        "prelude_games_only": given.prelude_games_only,
        "width": given.width,
        "layers": given.layers,
        "heads": given.heads,
        "batch": given.batch,
        "learning_rate": given.learning_rate,
        "seed": given.seed,
        "validation_share": given.validation_share,
        "positions": given.positions,
    }


def on_device(stacked: dict[str, np.ndarray], device: str) -> Batch:
    batch = batch_of(stacked)
    if device.startswith("cuda"):
        batch = Batch(**{name: tensor.pin_memory() for name, tensor in vars(batch).items()})
    return batch.to(device)


def learning_rate(peak: float, seen: int, budget: int) -> float:
    progress = seen / budget
    if progress < WARM_UP:
        return peak * max(progress / WARM_UP, 0.01)
    cosine = (1 + math.cos(math.pi * min((progress - WARM_UP) / (1 - WARM_UP), 1.0))) / 2
    return peak * (LAST_LEARNING_RATE + (1 - LAST_LEARNING_RATE) * cosine)


@torch.no_grad()
def validate(model: ImitationModel, given: argparse.Namespace, position_settings: PositionSettings) -> dict[str, Any]:
    """The loss and accuracy on the validation Games of every `validation_share`-th shard."""
    model.eval()
    count, loss, right = 0, 0.0, 0
    made = batches(
        given.dataset,
        "validation",
        position_settings,
        workers=min(given.workers, VALIDATION_WORKERS),
        seed=0,
        size=given.batch,
        buffer=given.batch,
        shard_share=(0, given.validation_share),
    )
    for stacked in made:
        batch = on_device(stacked, given.device)
        scores = scored(model, batch, given.device)
        loss += cross_entropy(scores, batch.picked, reduction="sum").item()
        right += (scores.argmax(dim=1) == batch.picked).sum().item()
        count += len(batch.picked)
    model.train()
    return {"positions": count, "loss": loss / max(count, 1), "accuracy": right / max(count, 1)}


def main(given_arguments: Sequence[str] | None = None) -> int:
    given = arguments(given_arguments)
    settings = settings_of(given)
    checkpoint_path = given.out.with_name(given.out.name + ".checkpoint")
    torch.manual_seed(given.seed)
    model = ImitationModel(ModelShape(given.width, given.layers, given.heads)).to(given.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=given.learning_rate, weight_decay=0.01)
    seen, passes, history = 0, 0, []
    if checkpoint_path.exists():
        checkpoint = torch.load(checkpoint_path, map_location=given.device, weights_only=True)
        differing = [name for name in FIXED_SETTINGS if checkpoint["settings"][name] != settings[name]]
        if differing or checkpoint["format"] != format_stamp():
            print(
                f"{checkpoint_path} was trained with other settings ({', '.join(differing) or 'encoding format'}): "
                "give the same ones, or another --out",
                file=sys.stderr,
            )
            return WRONG_ARGUMENTS
        model.load_state_dict(checkpoint["weights"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        seen, passes, history = checkpoint["seen"], checkpoint["passes"], checkpoint["history"]
        print(f"resuming from {seen:,} positions seen")
    if not given.device.startswith("cuda"):
        print("no GPU found: training on the CPU, which is much slower", flush=True)
    print(f"training on {given.device}: {settings}", flush=True)
    forward = torch.compile(model, dynamic=True) if given.compile else model
    position_settings = PositionSettings(given.min_rating, given.prelude_games_only)
    started, seen_at_start = time.time(), seen
    losses: list[torch.Tensor] = []
    next_validation = (seen // given.validate_every + 1) * given.validate_every

    def report_and_save() -> None:
        result = validate(model, given, position_settings)
        train_loss = torch.stack(losses).mean().item() if losses else float("nan")
        losses.clear()
        rate = (seen - seen_at_start) / max(time.time() - started, 1e-9)
        history.append({"seen": seen, "train_loss": train_loss, **result})
        print(
            f"{seen:,} positions ({rate:,.0f}/s): train loss {train_loss:.4f}, validation loss {result['loss']:.4f}, "
            f"accuracy {result['accuracy']:.2%} on {result['positions']:,}",
            flush=True,
        )
        saved = {"format": format_stamp(), "settings": settings, "positions_seen": seen, "validation": result}
        save_model(given.out, model, saved | {"history": history})
        partial = checkpoint_path.with_name(checkpoint_path.name + ".partial")
        torch.save(
            {
                "format": format_stamp(),
                "settings": settings,
                "weights": model.state_dict(),
                "optimizer": optimizer.state_dict(),
                "seen": seen,
                "passes": passes,
                "history": history,
            },
            partial,
        )
        partial.replace(checkpoint_path)

    model.train()
    while seen < given.positions:
        made = batches(
            given.dataset,
            "train",
            position_settings,
            workers=given.workers,
            seed=random.Random(f"{given.seed}:{passes}:{seen}").randrange(2**32),
            size=given.batch,
            buffer=SHUFFLE_BUFFER,
        )
        in_pass = 0
        for stacked in made:
            batch = on_device(stacked, given.device)
            for group in optimizer.param_groups:
                group["lr"] = learning_rate(given.learning_rate, seen, given.positions)
            loss = cross_entropy(scored(forward, batch, given.device), batch.picked)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            losses.append(loss.detach())
            seen += len(batch.picked)
            in_pass += len(batch.picked)
            if seen >= next_validation or seen >= given.positions:
                report_and_save()
                next_validation += given.validate_every
            if seen >= given.positions:
                break
        else:
            print(f"pass {passes + 1} over the training Games: {in_pass:,} positions", flush=True)
        made.close()
        if not in_pass:
            print("no training positions with these settings", file=sys.stderr)
            return WRONG_ARGUMENTS
        passes += 1
    if not history or history[-1]["seen"] != seen:
        report_and_save()
    return 0


if __name__ == "__main__":
    sys.exit(main())
