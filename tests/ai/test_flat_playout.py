"""The Flat Playout Bot: for each Option, it plays Sampled Positions out at random after picking it,
and picks the Option whose playouts end with the best mean Victory Point margin. It sees ahead only
through the handle's Sampled Positions. How strong it is is for Matches to say, not these tests."""

import dataclasses
import random

import tm_engine

from ai.controller import handle_for
from ai.controllers import REGISTERED, make_controller
from ai.flat_playout import FlatPlayout
from tests.helpers import MAX_PICKS


class CountingSampler:
    """Makes the real samples, and counts them."""

    def __init__(self, sampler: tm_engine.Sampler) -> None:
        self.sampler = sampler
        self.seeds: list[int] = []

    def sample(self, *, seed: int) -> tm_engine.Game:
        self.seeds.append(seed)
        return self.sampler.sample(seed=seed)


def a_decision_with(options: int) -> tm_engine.Game:
    """A Game waiting on its first Decision with exactly `options` Options."""
    game = tm_engine.Game(seed=2, players=2, draft=True, prelude=True)
    for _ in range(MAX_PICKS):
        if len(game.decision["options"]) == options:
            return game
        game.play_randomly(seed=1, picks=1)
    raise AssertionError(f"no Decision with {options} Options")


def test_the_flat_playout_bot_is_registered():
    assert REGISTERED["flat_playout"].label == "Flat Playout Bot"
    assert isinstance(make_controller("flat_playout"), FlatPlayout)


def test_it_plays_each_option_out_on_the_same_sampled_positions_and_picks_an_offered_one():
    game = a_decision_with(3)
    handle = handle_for(game, random.Random(4))
    sampler = CountingSampler(handle.sampler)

    index = FlatPlayout(playouts=3).pick(dataclasses.replace(handle, sampler=sampler))

    assert 0 <= index < len(game.decision["options"])
    options = len(game.decision["options"])
    assert len(sampler.seeds) == 3 * options
    assert sampler.seeds == sampler.seeds[:3] * options


def test_it_picks_the_same_from_the_same_random_state():
    game = a_decision_with(3)

    picks = {FlatPlayout(playouts=2).pick(handle_for(game, random.Random(9))) for _ in range(3)}

    assert len(picks) == 1


def test_it_takes_the_only_option_without_looking_ahead():
    game = a_decision_with(1)
    handle = handle_for(game, random.Random(4))
    sampler = CountingSampler(handle.sampler)

    assert FlatPlayout(playouts=3).pick(dataclasses.replace(handle, sampler=sampler)) == 0
    assert sampler.seeds == []
