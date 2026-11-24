"""The Value Bot (ticket 15 of phase 2): it tries the Options the Imitation Model rates likeliest, each on the same
few Sampled Positions, and picks the one after which the Value Model gives its Player the best mean chance of
winning. It sees only its handle, so it picks the same from any two Games its Player can't tell apart."""

import ast
import random
import subprocess
import sys
import time

import pytest
import tm_engine
import torch

from ai.card_economy import CardEconomyBot
from ai.controller import handle_for
from ai.imitation.model import ImitationModel, ModelShape, save_model
from ai.value.bot import ValueBot
from ai.value.encoded import FOLLOW_UPS
from ai.value.model import ValueModel, warm_started
from ai.value.samples import results_of

MAX_PICKS = 3_000


@pytest.fixture
def value_path(tmp_path):
    """An untrained Value Model of the full size, warm-started from an untrained Imitation Model, both seeded."""
    policy = tmp_path / "imitation.pt"
    torch.manual_seed(0)
    save_model(policy, ImitationModel(ModelShape()), {"note": "untrained"})
    torch.manual_seed(1)
    path = tmp_path / "value.pt"
    save_model(path, warm_started(policy), {"settings": {"policy": str(policy)}})
    return path


def handles_of_a_game(bot: ValueBot, seed: int = 2, until_generation: int = 2):
    """Plays a Game with the bot on both sides until the Action phase of `until_generation`, giving the handle of each
    Decision with more than one Option, the bot's pick and the pick's number."""
    game = tm_engine.Game(seed=seed, players=2, draft=True, prelude=True)
    for step in range(MAX_PICKS):
        handle = handle_for(game, random.Random(step))
        if handle.player_view["generation"] == until_generation and handle.player_view["phase"] == "action":
            return
        pick = bot.pick(handle)
        if len(handle.decision["options"]) > 1:
            yield handle, pick, step
        game.pick(pick)


def test_it_picks_among_the_policys_likeliest_options_the_one_rated_best(value_path):
    bot = ValueBot(value_path, tried=3, samples=2, share=0.0)
    checked = 0
    for handle, pick, step in handles_of_a_game(bot):
        chances = bot.policy.chances(handle)
        likeliest = sorted(range(len(chances)), key=lambda index: -chances[index])[:3]
        rated = bot.rated(handle_for_again(handle, step))
        assert sorted(rated) == sorted(likeliest)
        assert pick in likeliest
        assert rated[pick] == max(rated.values())
        checked += 1
    assert checked > 20


def handle_for_again(handle, step):
    """The same handle with its random source set back, so that the bot draws the same samples again."""
    return type(handle)(handle.player, handle.player_view, handle.decision, random.Random(step), handle.sampler)


def test_it_picks_the_same_from_two_games_its_player_cant_tell_apart(value_path):
    bot = ValueBot(value_path, tried=4, samples=2, share=0.0)
    game = tm_engine.Game(seed=6, players=2, draft=True, prelude=True)
    game.play_randomly(seed=6, picks=80)
    player = game.decision["player"]
    other = game.sampler(player).sample(seed=99)

    assert bot.pick(handle_for(game, random.Random(5))) == bot.pick(handle_for(other, random.Random(5)))


def test_an_option_that_ends_the_game_is_rated_by_the_players_result(value_path):
    game = tm_engine.Game(seed=8, players=2, draft=True, prelude=True)
    game.play_randomly(seed=8)
    replay = game.replay
    last = tm_engine.Game.from_replay(replay, step=len(replay["picks"]) - 1)
    handle = handle_for(last, random.Random(0))
    bot = ValueBot(value_path, tried=len(handle.decision["options"]), samples=2, share=0.0)
    result = results_of(game.scores)[0][handle.player]

    rated = bot.rated(handle)

    assert rated[replay["picks"][-1]] == result


def test_a_pick_takes_well_under_a_second(value_path):
    bot = ValueBot(value_path, share=0.0)  # every Option tried: the slowest
    torch.set_num_threads(1)
    widest = max(handles_of_a_game(bot, seed=3), key=lambda found: len(found[0].decision["options"]))[0]

    started = time.perf_counter()
    bot.pick(widest)

    assert time.perf_counter() - started < 0.5


def test_the_value_model_it_loads_is_a_value_model(value_path):
    assert isinstance(ValueBot(value_path).model, ValueModel)


def modules_loaded_by(module: str, pattern: str) -> list[str]:
    script = f"import sys, {module}; print(sorted(m for m in sys.modules if {pattern!r} in m))"
    imported = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=120, check=True)
    return ast.literal_eval(imported.stdout)


def test_the_bot_loads_no_dataset_reader_or_replay_code():
    # Fair play (ADR 0013): a Controller reads only its handle, and the samples it learned from come from code that
    # replays Games through the engine; the bot itself must not load it.
    assert modules_loaded_by("ai.value.bot", "recorded_games") == []
    assert modules_loaded_by("ai.value.bot", "ai.value.samples") == []


def test_the_processes_that_make_training_batches_load_no_pytorch():
    # 12 worker processes holding PyTorch once ran the laptop out of memory (ticket 13).
    assert modules_loaded_by("ai.value.samples", "torch") == []


def test_it_is_registered_once_the_loop_has_registered_a_model(value_path, tmp_path, monkeypatch):
    import ai.value
    from ai.controllers import REGISTERED, available, make_controller

    monkeypatch.setattr(ai.value, "MODEL", tmp_path / "none-yet.pt")
    assert REGISTERED["value"].label == "Value Bot"
    assert "value" not in available()

    monkeypatch.setattr(ai.value, "MODEL", value_path)
    assert "value" in available()
    assert isinstance(make_controller("value"), ValueBot)


def an_action_that_plays_a_card(seed: int = 11):
    """A Game waiting on an Action that can play a card, and that Option's index."""
    game = tm_engine.Game(seed=seed, players=2, draft=True, prelude=True)
    game.play_randomly(seed=seed, picks=150)
    for _ in range(MAX_PICKS):
        decision = game.decision
        types = [option["details"]["type"] for option in decision["options"]]
        if decision["kind"] == "action" and "play_card" in types:
            return game, types.index("play_card")
        game.play_randomly(seed=1, picks=1)
    raise AssertionError("no card could be played")


def test_an_option_is_rated_once_the_imitation_model_has_answered_what_follows_from_it(value_path):
    # Playing a card first asks for its Payment and then, say, its Tile's Area: until those are answered the card is
    # still in hand and nothing is paid, so the Value Model would see the same position after every Action.
    game, playing = an_action_that_plays_a_card()
    handle = handle_for(game, random.Random(0))
    card = handle.decision["options"][playing]["details"]["card"]
    bot = ValueBot(value_path, tried=len(handle.decision["options"]), samples=2, share=0.0)

    trials = bot.trials(handle)

    assert len(trials) == 2 * len(handle.decision["options"])
    for _, after in trials:
        decision = after.decision
        assert decision is None or decision["player"] != handle.player or decision["kind"] not in FOLLOW_UPS
    for index, after in trials:
        if index == playing:
            assert card in after.player_view(handle.player)["players"][handle.player]["played_cards"]


def test_an_option_is_tried_only_if_the_policy_gives_it_a_share_of_the_likeliest_options_chance(value_path):
    # Where the Imitation Model is sure, the Value Model's noise shouldn't overrule it on an Option Players rarely
    # pick, such as passing in Generation 1.
    # The untrained Imitation Model gives the Options nearly equal chances, so only a high share narrows them here.
    bot = ValueBot(value_path, tried=6, samples=1, share=0.9)
    narrowed = 0
    for handle, pick, _ in handles_of_a_game(bot):
        chances = bot.policy.chances(handle)
        top_six = sorted(range(len(chances)), key=lambda index: -chances[index])[:6]
        tried = bot.likeliest(handle)
        assert tried == [index for index in top_six if chances[index] >= 0.9 * max(chances)]
        assert pick in tried
        narrowed += len(tried) < min(6, len(chances))
    assert narrowed > 0


def test_with_a_share_of_one_it_picks_as_the_imitation_bot(value_path):
    bot = ValueBot(value_path, share=1.0)
    for handle, pick, _ in handles_of_a_game(bot):
        chances = bot.policy.chances(handle)
        assert pick == chances.index(max(chances))


def test_a_value_model_moved_to_another_computer_finds_its_policy_in_the_models_folder(tmp_path, monkeypatch):
    # The policy's path is saved as it was on the computer that trained it; a Docker image has the project elsewhere.
    import ai.imitation

    models = tmp_path / "models"
    models.mkdir()
    torch.manual_seed(0)
    save_model(models / "imitation.pt", ImitationModel(ModelShape(width=16, layers=1, heads=2)), {"note": "untrained"})
    path = models / "value.pt"
    gone = tmp_path / "the-training-computer" / "imitation.pt"
    save_model(path, warm_started(models / "imitation.pt"), {"settings": {"policy": str(gone)}})
    monkeypatch.setattr(ai.imitation, "MODELS_FOLDER", models)

    from ai.imitation.bot import loaded

    assert ValueBot(path).policy.model is loaded(models / "imitation.pt")


def playing_prelude_cards(*, asked: bool):
    """The same Game both ways: a Player choosing which Prelude Card to play first."""
    scenario = {
        "players": [{"prelude_cards": ["donation", "loan"]}, {"prelude_cards": ["supplier", "mohole"]}],
        "prelude": True,
        "ask_last_prelude_card": asked,
    }
    return tm_engine.Game.from_scenario(scenario)


def test_a_prelude_card_is_rated_once_the_last_one_is_played_whether_or_not_the_game_asks_for_it(value_path):
    bot = ValueBot(value_path, samples=2, share=0.0)

    rated = [bot.rated(handle_for(playing_prelude_cards(asked=asked), random.Random(0))) for asked in (False, True)]

    assert len(rated[0]) == 2
    assert rated[0] == rated[1]


def test_the_card_economy_bot_prices_a_prelude_card_once_the_last_one_is_played_either_way():
    explained = [
        CardEconomyBot().explain(handle_for(playing_prelude_cards(asked=asked), random.Random(0)))
        for asked in (False, True)
    ]

    assert explained[0] == explained[1]
