"""The Search Bot (ticket 16 of phase 2): within a time budget per Decision, it searches a tree over Sampled
Positions, with the Imitation Model narrowing Options and the Value Model rating positions. It sees only its handle,
so it picks the same from any two Games its Player can't tell apart, given the same random state and number of
Sampled Positions."""

import dataclasses
import random
import time

import pytest
import tm_engine
import torch

from ai.controller import handle_for
from ai.imitation.model import ImitationModel, ModelShape, save_model
from ai.search import SearchBot
from ai.value.model import warm_started

MAX_PICKS = 3_000
TINY = ModelShape(width=16, layers=1, heads=2)


@pytest.fixture
def value_path(tmp_path):
    """A tiny untrained Value Model, warm-started from a tiny untrained Imitation Model, both seeded."""
    policy = tmp_path / "imitation.pt"
    torch.manual_seed(0)
    save_model(policy, ImitationModel(TINY), {"note": "untrained"})
    torch.manual_seed(1)
    path = tmp_path / "value.pt"
    save_model(path, warm_started(policy), {"settings": {"policy": str(policy)}})
    return path


def test_it_picks_the_same_from_two_games_its_player_cant_tell_apart(value_path):
    # A count of Sampled Positions, not seconds: how many fit in a time depends on the computer's speed.
    bot = SearchBot(value_path, seconds=None, samples=4, share=0.0)
    game = tm_engine.Game(seed=6, players=2, draft=True, prelude=True)
    game.play_randomly(seed=6, picks=80)
    player = game.decision["player"]
    other = game.sampler(player).sample(seed=99)
    assert len(game.decision["options"]) > 2

    picks = [bot.pick(handle_for(game, random.Random(seed))) for seed in range(5)]
    other_picks = [bot.pick(handle_for(other, random.Random(seed))) for seed in range(5)]

    assert picks == other_picks


def handles_of_a_game(bot, seed: int = 2, until_generation: int = 2):
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


def a_wide_decision(value_path):
    """A handle at a Decision with many Options, from a Game played by a quick Search Bot."""
    quick = SearchBot(value_path, seconds=None, samples=1, share=0.0)
    return max(handles_of_a_game(quick, seed=3), key=lambda found: len(found[0].decision["options"]))[0]


def test_it_keeps_to_its_time_budget_and_spends_more_of_a_larger_one(value_path):
    handle = a_wide_decision(value_path)
    found = {}
    for seconds in (0.1, 0.4):
        bot = SearchBot(value_path, seconds=seconds, share=0.0)
        started = time.perf_counter()
        found[seconds] = bot.search(handle_for_again(handle, 0))
        assert time.perf_counter() - started < seconds

    assert 1 < found[0.1].samples < found[0.4].samples


def handle_for_again(handle, seed):
    """The same handle with a new random source."""
    return dataclasses.replace(handle, random=random.Random(seed))


def test_its_tree_grows_below_an_option_at_the_players_own_later_decisions(value_path):
    # The first walk through an Option is rated where it stops; later walks that stop at the Player's own next
    # Decision go on into a node there, whose Options are the ones that Decision offers, picked by PUCT.
    bot = SearchBot(value_path, seconds=None, samples=6, share=0.0)
    grown = 0
    for handle, _, step in handles_of_a_game(SearchBot(value_path, seconds=None, samples=1, share=0.0)):
        searched = bot.search(handle_for_again(handle, step))
        for edge in searched.options.values():
            assert edge.visits == searched.samples == 6
            if edge.below:
                grown += 1
                assert sum(below.visits for below in edge.below.values()) <= edge.visits - 1
                assert all(below.offered >= below.visits for below in edge.below.values())
    assert grown > 10


def test_an_option_that_ends_the_game_is_rated_by_the_players_result(value_path):
    game = tm_engine.Game(seed=8, players=2, draft=True, prelude=True)
    game.play_randomly(seed=8)
    replay = game.replay
    last = tm_engine.Game.from_replay(replay, step=len(replay["picks"]) - 1)
    handle = handle_for(last, random.Random(0))
    winners = [score["player"] for score in game.scores if score["rank"] == 1]
    result = 1.0 if winners == [handle.player] else 0.5 if handle.player in winners else 0.0
    bot = SearchBot(value_path, seconds=None, samples=2, share=0.0, tried=len(handle.decision["options"]))

    searched = bot.search(handle)

    assert searched.options[replay["picks"][-1]].mean == result


def test_with_a_share_of_one_it_picks_as_the_imitation_bot_at_once(value_path):
    bot = SearchBot(value_path, share=1.0)
    for handle, pick, _ in handles_of_a_game(bot):
        chances = bot.policy.chances(handle)
        assert pick == chances.index(max(chances))
        assert bot.search(handle).samples == 0


def test_with_random_playouts_at_the_leaves_each_walk_ends_in_a_result(value_path):
    bot = SearchBot(value_path, seconds=None, samples=3, share=0.0, leaves="playouts")
    handle = a_wide_decision(value_path)

    searched = bot.search(handle)

    for edge in searched.options.values():
        assert (edge.total * 2) == int(edge.total * 2)  # a sum of results 1, ½ and 0


def test_it_is_registered_once_a_value_model_is_and_its_budget_is_a_setting(value_path, tmp_path, monkeypatch):
    import ai.value
    from ai.controllers import REGISTERED, available, make_controller

    monkeypatch.setattr(ai.value, "MODEL", tmp_path / "none-yet.pt")
    assert REGISTERED["search"].label == "Search Bot"
    assert "search" not in available()

    monkeypatch.setattr(ai.value, "MODEL", value_path)
    assert "search" in available()
    bot = make_controller("search")
    assert isinstance(bot, SearchBot)
    assert bot.seconds == 1.0

    # Settings follow the name, for the Match tool, the server and Replay files alike.
    bot = make_controller("search?seconds=0.1&leaves=playouts")
    assert (bot.seconds, bot.leaves) == (0.1, "playouts")
    with pytest.raises(ValueError, match="seconds"):
        make_controller("search?second=5")
    with pytest.raises(ValueError, match="seconds"):
        make_controller("search?seconds")
    with pytest.raises(ValueError, match="seconds"):
        make_controller("search?seconds=soon")
    with pytest.raises(ValueError, match="takes no settings"):
        make_controller("random_bot?seconds=5")
