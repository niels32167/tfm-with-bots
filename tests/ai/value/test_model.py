"""The Value Model (ticket 15 of phase 2): the Imitation Model's transformer, read at its global token, gives a
Player's chance of winning and their expected Victory Point margin. It starts from the Imitation Model's weights,
and a small training run learns a few positions' results. No GPU is needed."""

import random

import pytest
import torch

from ai.encoding import format_stamp
from ai.imitation.model import ImitationModel, ModelShape, load_model, save_model
from ai.value.model import ValueModel, chances_of_winning, warm_started
from ai.value.samples import replay_samples, results_of, sample_batches
from ai.value.train import fit, measured
from tests.ai.value.test_samples import played, settled_positions

TINY = ModelShape(width=16, layers=1, heads=2)


@pytest.fixture
def policy_path(tmp_path):
    path = tmp_path / "imitation.pt"
    torch.manual_seed(0)
    save_model(path, ImitationModel(TINY), {"note": "untrained"})
    return path


def test_it_starts_from_the_imitation_models_weights_with_a_new_head(policy_path):
    policy = load_model(policy_path)[0]

    model = warm_started(policy_path)

    assert model.shape == policy.shape
    assert torch.equal(model.card_identity.weight, policy.card_identity.weight)
    assert model.out[-1].out_features == 2


def test_it_is_saved_and_loaded_with_the_encoding_format(policy_path, tmp_path):
    model = warm_started(policy_path)
    path = tmp_path / "value.pt"

    save_model(path, model, {"settings": {"seed": 3}})
    loaded, saved = load_model(path, kind=ValueModel)

    assert isinstance(loaded, ValueModel)
    assert saved["settings"]["seed"] == 3
    assert torch.load(path, weights_only=True)["format"] == format_stamp()


def samples_of_one_game():
    game = played()
    return list(replay_samples(game.replay, *results_of(game.scores), random.Random(0)))


def test_chances_of_winning_are_between_zero_and_one(policy_path):
    samples = samples_of_one_game()[:10]

    chances = chances_of_winning(warm_started(policy_path), [sample.position for sample in samples])

    assert len(chances) == 10
    assert all(0.0 < chance < 1.0 for chance in chances)


def test_a_small_training_run_learns_a_few_positions_results(policy_path, tmp_path):
    torch.manual_seed(0)
    samples = samples_of_one_game()[100:132]
    model = warm_started(policy_path)
    before = measured(model, [samples], device="cpu")

    fit(model, [samples] * 150, learning_rate=3e-3, device="cpu")

    after = measured(model, [samples], device="cpu")
    assert after["loss"] < before["loss"] / 2
    assert after["accuracy"] == 1.0


def test_batches_are_streamed_from_the_loops_games_with_their_targets(tmp_path):
    import gzip
    import json

    game = played()
    results, margins = results_of(game.scores)
    path = tmp_path / "round-001.jsonl.gz"
    with gzip.open(path, "wt") as file:
        file.write(json.dumps({"replay": game.replay, "results": results, "margins": margins}) + "\n")

    made = list(sample_batches([path], "train", workers=0, seed=0, size=64, buffer=128))

    assert sum(len(batch) for batch in made) == settled_positions(game.replay)
    assert all(len(batch) <= 64 for batch in made)
