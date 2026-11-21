"""The self-play loop (ticket 15 of phase 2) runs end to end on a tiny model, on the CPU, in the normal test suite
(box 5): a warm start on Recorded Games, the panel of old Controllers rated, and rounds of self-play, training,
a gating Match and a rating. It stops and resumes safely (box 1), its Controllers answer through the fair handle,
and each model is saved with its run's settings, seed and engine version (box 6)."""

import gzip
import json

import pytest
import torch

import ai.match
import ai.value.loop
from ai.controller import Handle
from ai.imitation.model import ImitationModel, ModelShape, load_model, save_model
from ai.value.bot import ValueBot
from ai.value.loop import main
from ai.value.model import ValueModel
from tests.ai.imitation.test_positions import replay_of_the_example, write_dataset
from tests.ai.value.test_samples import recorded, settled_positions


@pytest.fixture
def given(tmp_path):
    policy = tmp_path / "imitation.pt"
    torch.manual_seed(0)
    save_model(policy, ImitationModel(ModelShape(width=16, layers=1, heads=2)), {"note": "untrained"})
    replay = replay_of_the_example()
    games = [recorded("example"), recorded("checked", date="2025-09-15")]
    dataset = write_dataset(tmp_path / "dataset", games, [replay, {**replay, "game": "checked"}])
    return [
        "--run", str(tmp_path / "run"), "--policy", str(policy), "--dataset", str(dataset),
        "--warm-positions", "48", "--games", "4", "--train-passes", "1", "--gate-games", "2",
        "--rating-games", "2", "--panel", "random_bot", "--pool-bots", "random_bot", "--tried", "2", "--samples", "1",
        "--batch", "16", "--workers", "0", "--processes", "1", "--device", "cpu", "--validation-share", "1",
    ]  # fmt: skip


class Crash(Exception):
    pass


def test_the_loop_runs_stops_and_resumes_through_the_fair_handle(given, tmp_path, monkeypatch, capsys):
    run = tmp_path / "run"
    handles = []
    real_handle_for, real_pick = ai.match.handle_for, ValueBot.pick

    def counted_handle_for(game, random_numbers):
        handles.append(real_handle_for(game, random_numbers))
        return handles[-1]

    def checked_pick(bot, handle):
        assert type(handle) is Handle
        return real_pick(bot, handle)

    monkeypatch.setattr(ai.match, "handle_for", counted_handle_for)
    monkeypatch.setattr(ValueBot, "pick", checked_pick)

    # A first run stops in round 1's gating Match, as if the laptop were switched off.
    real_gate = ai.value.loop.Loop.gate
    monkeypatch.setattr(ai.value.loop.Loop, "gate", lambda loop, number: (_ for _ in ()).throw(Crash()))
    with pytest.raises(Crash):
        main([*given, "--rounds", "1"])
    played = (run / "games" / "round-001.jsonl.gz").stat().st_mtime_ns
    monkeypatch.setattr(ai.value.loop.Loop, "gate", real_gate)

    assert main([*given, "--rounds", "1"]) == 0
    assert (run / "games" / "round-001.jsonl.gz").stat().st_mtime_ns == played  # not played again

    state = json.loads((run / "state.json").read_text())
    assert state["done"] == ["warm start", "panel", "rate v000", "play 1", "train 1", "gate 1", "rate 1"]
    assert [row["version"] for row in state["ratings"]] == ["v000", "candidate-001"]
    assert (run / "ratings.tsv").read_text().count("\n") == 3  # a header and a row each
    assert state["rounds"][0]["games"] == 4
    # One pass over the round's Games: no position is learned twice.
    with gzip.open(run / "games" / "round-001.jsonl.gz") as lines:
        kept = sum(settled_positions(json.loads(line)["replay"]) for line in lines)
    assert 0 < state["rounds"][0]["trained"]["positions"] <= kept
    assert set(state["rounds"][0]["scores"]) == {"v000", "random_bot"}  # against itself and the pool
    assert handles, "no Game was played through ai.match"
    assert all(type(handle) is Handle for handle in handles)

    # With no time left, a later invocation starts no step, and says how to go on.
    capsys.readouterr()
    assert main([*given, "--rounds", "2", "--minutes", "0"]) == 0
    assert "before play 2" in capsys.readouterr().out
    assert json.loads((run / "state.json").read_text())["done"] == state["done"]

    model, saved = load_model(run / "versions" / "v000.pt", kind=ValueModel)
    assert isinstance(model, ValueModel)
    assert saved["settings"]["seed"] == 0
    assert saved["settings"]["games"] == 4
    assert saved["provenance"]["engine"]
    assert saved["provenance"]["commit"]
    assert json.loads((run / "run.json").read_text())["settings"] == saved["settings"]

    # Other settings for the same run are refused.
    capsys.readouterr()
    assert main([*given, "--seed", "5", "--rounds", "2"]) == 2
    assert "seed" in capsys.readouterr().err


def test_a_run_can_start_from_a_saved_value_model_instead_of_a_warm_start(given, tmp_path):
    # As the second run started from the first run's best version (2026-11-21).
    first = tmp_path / "first"
    assert main([*given, "--run", str(first), "--rounds", "0"]) == 0
    earlier = first / "versions" / "v000.pt"

    assert main([*given, "--run", str(tmp_path / "second"), "--rounds", "0", "--start-from", str(earlier)]) == 0

    model, saved = load_model(tmp_path / "second" / "versions" / "v000.pt", kind=ValueModel)
    before = load_model(earlier, kind=ValueModel)[0]
    assert all(torch.equal(a, b) for a, b in zip(model.state_dict().values(), before.state_dict().values()))
    assert saved["started_from"] == str(earlier)
    assert saved["settings"]["start_from"] == str(earlier)
