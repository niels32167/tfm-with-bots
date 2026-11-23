"""Saved Value Models measured on the same held-out positions of Recorded Games with Prelude (ticket 16's box 3), so
that a new warm start can be compared with the registered model before any Match."""

import torch

from ai.imitation.model import ModelShape, save_model
from ai.value.evaluate import main
from ai.value.model import ValueModel
from tests.ai.imitation.test_positions import replay_of_the_example, write_dataset
from tests.ai.value.test_samples import recorded, settled_positions


def test_saved_value_models_are_measured_on_the_same_validation_positions_of_prelude_games(tmp_path, capsys):
    replay = replay_of_the_example()
    games = [
        recorded("trained"),
        recorded("checked", date="2025-09-15"),
        recorded("checked plain", date="2025-09-15", prelude=False),
    ]
    dataset = write_dataset(tmp_path, games, [{**replay, "game": game["game"]} for game in games])
    models = []
    for seed in (0, 1):
        torch.manual_seed(seed)
        models.append(tmp_path / f"model-{seed}.pt")
        save_model(models[-1], ValueModel(ModelShape(width=16, layers=1, heads=2)), {"note": "untrained"})

    assert main([*map(str, models), "--dataset", str(dataset), "--keep", "1", "--workers", "0", "--device", "cpu"]) == 0

    lines = capsys.readouterr().out.splitlines()
    measured = settled_positions(replay["replay"])
    assert [line.split()[0] for line in lines] == [str(model) for model in models]
    assert all(f"{measured:,} positions" in line for line in lines)
    assert lines[0] != lines[1]
