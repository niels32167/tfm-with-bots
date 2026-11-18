"""The Imitation Bot answers setup, Draft and buy Decisions with the Imitation Model and leaves the rest to the
Card Economy Bot (ticket 13 of phase 2). It is a registered Controller once a model is trained, and a pick takes
well under a second."""

import random
import subprocess
import sys
import time

import pytest
import tm_engine

from ai.card_economy import CardEconomyBot
from ai.controller import handle_for
from ai.controllers import REGISTERED, available, make_controller
from ai.imitation.bot import IMITATED, ImitationBot
from ai.imitation.model import ImitationModel, ModelShape, save_model

MAX_PICKS = 3_000


@pytest.fixture
def model_path(tmp_path):
    path = tmp_path / "imitation.pt"
    save_model(path, ImitationModel(ModelShape()), {"note": "untrained"})
    return path


def decisions_until_the_action_phase_of_generation_2(bot: ImitationBot):
    """Plays a Game with the bot on both sides, giving each handle it answered and its pick."""
    game = tm_engine.Game(seed=2, players=2, draft=True, prelude=True)
    for step in range(MAX_PICKS):
        handle = handle_for(game, random.Random(step))
        if handle.player_view["generation"] == 2 and handle.player_view["phase"] == "action":
            return
        pick = bot.pick(handle)
        yield handle, pick
        game.pick(pick)


def test_setup_draft_and_buy_picks_come_from_the_model_and_the_rest_from_the_card_economy_bot(model_path):
    bot = ImitationBot(model_path)
    kinds = set()
    for handle, pick in decisions_until_the_action_phase_of_generation_2(bot):
        assert 0 <= pick < len(handle.decision["options"])
        kinds.add(handle.decision["kind"])
        if handle.decision["kind"] not in IMITATED:
            assert pick == CardEconomyBot().pick(handle)

    assert IMITATED <= kinds


def test_a_pick_takes_well_under_a_second(model_path):
    bot = ImitationBot(model_path)
    handles = [handle for handle, _ in decisions_until_the_action_phase_of_generation_2(bot)]
    draft = next(handle for handle in handles if handle.decision["kind"] == "draft")

    started = time.perf_counter()
    bot.pick(draft)
    assert time.perf_counter() - started < 0.25


def test_the_imitation_bot_is_registered_and_offered_once_a_model_is_trained(model_path, monkeypatch):
    assert REGISTERED["imitation"].label == "Imitation Bot"
    monkeypatch.setattr("ai.imitation.MODEL", model_path)
    assert "imitation" in available()
    assert isinstance(make_controller("imitation"), ImitationBot)

    monkeypatch.setattr("ai.imitation.MODEL", model_path.with_name("missing.pt"))
    assert "imitation" not in available()
    with pytest.raises(ValueError, match="ai.imitation.train"):
        make_controller("imitation")


def test_the_bot_loads_no_dataset_reader_or_replay_code():
    # Fair play (ADR 0013): a Controller reads only its handle. The engine itself comes in through ai.controller, the
    # seam that builds handles; the code that replays Recorded Games through it must not.
    imported = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, ai.imitation.bot; print(sorted(m for m in sys.modules if 'recorded_games' in m))",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )

    assert imported.stdout.strip() == "[]"
