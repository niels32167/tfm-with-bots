"""Training the Value Model on batches of samples (ai.value.samples): the loss is the cross-entropy of the result
(a draw is ½) plus MARGIN_WEIGHT times the squared error of the scaled Victory Point margin."""

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import torch
from torch.nn.functional import binary_cross_entropy_with_logits, mse_loss

from ai.imitation.model import Batch, batch_of, scored
from ai.imitation.train import learning_rate as scheduled
from ai.value.model import MARGIN, MARGIN_SCALE, WIN, ValueModel
from ai.value.samples import ValueSample, budgeted, sample_batches, stack_samples

# Validation positions measured: enough for a loss to two decimals.
VALIDATION_POSITIONS = 100_000
# How much the margin counts beside the result.
MARGIN_WEIGHT = 0.25
# Margins beyond this many MARGIN_SCALEs are learned as this many: a rout teaches no more than a clear win.
MARGIN_CLIP = 3.0


def on_device(samples: list[ValueSample], device: str) -> tuple[Batch, torch.Tensor, torch.Tensor]:
    """A Batch of the samples' positions, their results, and their scaled margins, on `device`."""
    stacked = stack_samples(samples)
    result = torch.from_numpy(stacked.pop("result"))
    margin = (torch.from_numpy(stacked.pop("margin")) / MARGIN_SCALE).clamp(-MARGIN_CLIP, MARGIN_CLIP)
    return batch_of(stacked).to(device), result.to(device), margin.to(device)


def losses(model: ValueModel, samples: list[ValueSample], device: str) -> tuple[torch.Tensor, torch.Tensor]:
    """The training loss of a batch, and its result's cross-entropy alone, each a mean over the batch."""
    batch, result, margin = on_device(samples, device)
    out = scored(model, batch, device)
    win = binary_cross_entropy_with_logits(out[:, WIN], result)
    return win + MARGIN_WEIGHT * mse_loss(out[:, MARGIN], margin), win


def fit(
    model: ValueModel,
    batches: Iterable[list[ValueSample]],
    *,
    learning_rate: float,
    device: str,
    budget: int | None = None,
) -> dict[str, Any]:
    """Trains `model` on `batches` with AdamW. With a `budget` of positions, the learning rate warms up and falls
    along a cosine (as the Imitation Model's does), and training stops there; otherwise it stays at
    `learning_rate` for every batch. Returns how many positions it learned from and the mean loss."""
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    seen, total = 0, []
    for samples in batches:
        if budget is not None:
            for group in optimizer.param_groups:
                group["lr"] = scheduled(learning_rate, seen, budget)
        loss, _ = losses(model, samples, device)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        total.append(loss.detach())
        seen += len(samples)
        if budget is not None and seen >= budget:
            break
    model.eval()
    return {"positions": seen, "loss": torch.stack(total).mean().item() if total else float("nan")}


@torch.no_grad()
def measured(model: ValueModel, batches: Iterable[list[ValueSample]], device: str) -> dict[str, Any]:
    """On held-out batches: the result's cross-entropy, and how often the likelier Player per the model won (draws
    left out of that)."""
    model.eval()
    count, loss, decided, right = 0, 0.0, 0, 0
    for samples in batches:
        batch, result, _ = on_device(samples, device)
        logits = scored(model, batch, device)[:, WIN]
        loss += binary_cross_entropy_with_logits(logits, result, reduction="sum").item()
        count += len(samples)
        clear = result != 0.5
        decided += int(clear.sum().item())
        right += int(((logits > 0) == (result > 0.5))[clear].sum().item())
    return {"positions": count, "loss": loss / max(count, 1), "accuracy": right / max(decided, 1)}


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
