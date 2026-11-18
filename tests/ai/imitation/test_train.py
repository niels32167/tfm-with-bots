"""One command trains the Imitation Model within the laptop's limits, can resume, and saves the model with its
encoding format and the settings used (ticket 13 of phase 2, box 1)."""

import pytest

from ai.encoding import format_stamp
from ai.imitation.model import load_model
from ai.imitation.train import main
from tests.ai.imitation.test_positions import example, write_dataset

TINY = ["--width", "16", "--layers", "1", "--heads", "2", "--batch", "8", "--workers", "0", "--device", "cpu"]
TINY += ["--validation-share", "1"]


@pytest.fixture
def dataset(tmp_path):
    games = [example("trained", date="2024-01-01"), example("validated", date="2025-09-15")]
    return write_dataset(tmp_path / "dataset", games, [])


def train(dataset, out, *extra):
    return main(["--dataset", str(dataset), "--out", str(out), "--validate-every", "40", *TINY, *extra])


def test_training_saves_the_model_with_its_format_and_settings(dataset, tmp_path):
    out = tmp_path / "model.pt"

    assert train(dataset, out, "--positions", "60", "--min-rating", "450") == 0

    saved = load_model(out)[1]
    assert saved["format"] == format_stamp()
    assert saved["settings"]["min_rating"] == 450
    assert saved["settings"]["width"] == 16
    assert saved["positions_seen"] >= 60
    assert saved["validation"]["positions"] > 0


def test_a_run_resumes_from_its_checkpoint_and_refuses_other_settings(dataset, tmp_path, capsys):
    out = tmp_path / "model.pt"
    train(dataset, out, "--positions", "40")
    first = load_model(out)[1]["positions_seen"]

    assert train(dataset, out, "--positions", "80") == 0
    assert "resuming from" in capsys.readouterr().out
    assert load_model(out)[1]["positions_seen"] >= 80 > first

    assert train(dataset, out, "--positions", "120", "--min-rating", "600") == 2
    assert "other settings" in capsys.readouterr().err
