"""The Imitation Bot answers every Decision with the Imitation Model (ticket 14 of phase 2). Ticket 13's, which
answered setup, Draft and buy Decisions and left the rest to the Card Economy Bot, stays registered beside it to
play against. Each is a registered Controller once its model is trained, and a pick takes well under a second."""

import random
import subprocess
import sys
import time

import pytest
import tm_engine
import torch

from ai.card_economy import CardEconomyBot
from ai.controller import handle_for
from ai.controllers import REGISTERED, available, make_controller
from ai.imitation.bot import DRAFT_AND_BUY, ImitationBot
from ai.imitation.model import ImitationModel, ModelShape, save_model

MAX_PICKS = 3_000


@pytest.fixture
def model_path(tmp_path):
    path = tmp_path / "imitation.pt"
    torch.manual_seed(0)  # The same untrained weights, so the same Game, every run.
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


def test_every_pick_with_a_choice_is_the_option_the_model_rates_highest(model_path):
    bot = ImitationBot(model_path)
    kinds = set()
    for handle, pick in decisions_until_the_action_phase_of_generation_2(bot):
        if len(handle.decision["options"]) > 1:
            kinds.add(handle.decision["kind"])
            chances = bot.chances(handle)
            assert chances[pick] == max(chances)

    assert DRAFT_AND_BUY | {"play_prelude_card", "action"} <= kinds


def test_ticket_13s_bot_answers_setup_draft_and_buy_and_leaves_the_rest_to_the_card_economy_bot(model_path):
    bot = ImitationBot(model_path, imitated=DRAFT_AND_BUY)
    kinds = set()
    for handle, pick in decisions_until_the_action_phase_of_generation_2(bot):
        assert 0 <= pick < len(handle.decision["options"])
        kinds.add(handle.decision["kind"])
        if handle.decision["kind"] not in DRAFT_AND_BUY:
            assert pick == CardEconomyBot().pick(handle)

    assert DRAFT_AND_BUY <= kinds


def test_a_pick_takes_well_under_a_second(model_path):
    bot = ImitationBot(model_path)
    handles = [handle for handle, _ in decisions_until_the_action_phase_of_generation_2(bot)]
    most_options = max(handles, key=lambda handle: len(handle.decision["options"]))
    assert len(most_options.decision["options"]) >= 15

    started = time.perf_counter()
    bot.pick(most_options)
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


def test_ticket_13s_bot_is_registered_apart_with_its_own_model(model_path, monkeypatch):
    assert REGISTERED["imitation_draft_buy"].label == "Imitation Bot (Draft and buy)"
    monkeypatch.setattr("ai.imitation.DRAFT_AND_BUY_MODEL", model_path)
    assert "imitation_draft_buy" in available()
    bot = make_controller("imitation_draft_buy")
    assert bot.imitated == DRAFT_AND_BUY

    monkeypatch.setattr("ai.imitation.DRAFT_AND_BUY_MODEL", model_path.with_name("missing.pt"))
    assert "imitation_draft_buy" not in available()


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
