"""The Imitation Model scores each Option given the position (ADR 0002). A small training run overfits a few
hand-written positions on the CPU (spec, "Testing Decisions"), and a saved model refuses another encoding format."""

import pytest
import torch

from ai.encoding import FormatMismatch
from ai.imitation.model import ImitationModel, ModelShape, collate, load_model, save_model
from ai.imitation.positions import PositionSettings, game_positions
from tests.ai.imitation.test_positions import EXAMPLE_DECISIONS, example

SMALL = ModelShape(width=32, layers=1, heads=2)


def example_positions():
    return list(game_positions(example("a", date="2024-01-01"), None, PositionSettings()))


def test_scores_are_one_per_option_and_padding_never_wins():
    found = example_positions()
    batch = collate(found)
    scores = ImitationModel(SMALL)(batch)

    assert scores.shape == (len(found), max(len(p.options) for p in found))
    for row, position in zip(scores, found, strict=True):
        assert torch.isfinite(row[: len(position.options)]).all()
        assert (row[len(position.options) :] == float("-inf")).all()


def test_a_small_training_run_learns_every_pick_of_a_few_positions_on_the_cpu():
    torch.manual_seed(0)
    found = example_positions()
    assert len(found) == EXAMPLE_DECISIONS
    batch = collate(found)
    model = ImitationModel(SMALL)
    optimizer = torch.optim.Adam(model.parameters(), lr=3e-3)
    for _ in range(300):
        loss = torch.nn.functional.cross_entropy(model(batch), batch.picked)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    assert (model(batch).argmax(dim=1) == batch.picked).all()


def test_a_saved_model_scores_alike_and_one_of_another_format_is_refused(tmp_path):
    batch = collate(example_positions())
    model = ImitationModel(SMALL).eval()
    save_model(tmp_path / "model.pt", model, {"note": "test"})

    loaded, saved = load_model(tmp_path / "model.pt")
    assert saved["note"] == "test"
    assert torch.equal(loaded(batch), model(batch))

    checkpoint = torch.load(tmp_path / "model.pt", weights_only=True)
    checkpoint["format"]["layout_hash"] = "another"
    torch.save(checkpoint, tmp_path / "old.pt")
    with pytest.raises(FormatMismatch):
        load_model(tmp_path / "old.pt")
