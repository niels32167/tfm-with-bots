"""What a Controller would do at a Decision, for a human to learn from: the Option it would pick, and how it rates those
it weighed."""

import random

import pytest
import tm_engine
import torch

from ai.advice import PRICE, STRONG_PLAYERS, WINS, Advice, advice
from ai.card_economy import CardEconomyBot
from ai.controller import handle_for
from ai.imitation.bot import DRAFT_AND_BUY, ImitationBot
from ai.imitation.model import ImitationModel, ModelShape, save_model
from ai.random_bot import RandomBot
from ai.search import SearchBot
from ai.value.bot import ValueBot
from ai.value.model import warm_started

TINY = ModelShape(width=16, layers=1, heads=2)


@pytest.fixture
def policy_path(tmp_path):
    path = tmp_path / "imitation.pt"
    torch.manual_seed(0)
    save_model(path, ImitationModel(TINY), {"note": "untrained"})
    return path


@pytest.fixture
def value_path(tmp_path, policy_path):
    path = tmp_path / "value.pt"
    torch.manual_seed(1)
    save_model(path, warm_started(policy_path), {"settings": {"policy": str(policy_path)}})
    return path


def games():
    """Positions at setup and in the Action phase, each with a choice."""
    for picks in (0, 1, 80, 150):
        game = tm_engine.Game(seed=6, players=2, draft=True, prelude=True)
        game.play_randomly(seed=6, picks=picks)
        while len(game.decision["options"]) == 1:
            game.play_randomly(seed=6, picks=1)
        yield game


def check(bot, *measures):
    """The bot advises what it would pick itself, rates it by `measures`, and lists it first."""
    for game in games():
        advised = advice(bot, handle_for(game, random.Random(4)))
        assert advised.picked == bot.pick(handle_for(game, random.Random(4)))
        assert list(advised.measures) == list(measures)
        assert advised.ranked()[0] == advised.picked
        assert all(len(values) == len(measures) for values in advised.measured.values())
        yield game, advised


def test_the_imitation_bot_rates_every_option_by_the_chance_a_strong_player_picks_it(policy_path):
    for game, advised in check(ImitationBot(policy_path), STRONG_PLAYERS):
        assert set(advised.measured) == set(range(len(game.decision["options"])))
        assert sum(values[0] for values in advised.measured.values()) == pytest.approx(1)


def test_the_value_bot_rates_the_options_it_tried_by_the_chance_to_win_and_the_rest_by_the_policys(value_path):
    for game, advised in check(ValueBot(value_path, samples=2), WINS, STRONG_PLAYERS):
        assert set(advised.measured) == set(range(len(game.decision["options"])))
        wins, strong = advised.measured[advised.picked]
        assert 0 <= wins <= 1 and 0 <= strong <= 1
        tried = [values[0] for values in advised.measured.values() if values[0] is not None]
        assert wins == max(tried)


def test_the_search_bot_rates_the_options_it_searched(value_path):
    for _, advised in check(SearchBot(value_path, seconds=None, samples=2), WINS, STRONG_PLAYERS):
        assert 0 <= advised.measured[advised.picked][1] <= 1


def test_the_card_economy_bot_rates_every_option_by_its_price():
    for game, advised in check(CardEconomyBot(), PRICE):
        assert len(advised.measured) == len(game.decision["options"])


def test_ticket_13s_bot_rates_what_it_leaves_to_the_card_economy_bot_by_its_price(policy_path):
    bot = ImitationBot(policy_path, imitated=DRAFT_AND_BUY)
    for game in games():
        advised = advice(bot, handle_for(game, random.Random(4)))
        imitated = game.decision["kind"] in DRAFT_AND_BUY
        assert list(advised.measures) == [STRONG_PLAYERS if imitated else PRICE]
        assert advised.picked == bot.pick(handle_for(game, random.Random(4)))


def test_of_any_other_controller_only_the_pick_is_known():
    game = next(games())
    advised = advice(RandomBot(), handle_for(game, random.Random(4)))

    assert advised == Advice(RandomBot().pick(handle_for(game, random.Random(4))))


def test_options_without_a_value_come_after_those_with_one():
    advised = Advice(2, (WINS, STRONG_PLAYERS), {0: [None, 0.2], 1: [0.4, 0.1], 2: [0.5, 0.1], 3: [None, 0.6]})

    assert advised.ranked() == [2, 1, 3, 0]
