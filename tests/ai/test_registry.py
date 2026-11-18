"""Registered Controllers are named once, in ai.controllers: the Match tool, the server and the GUI's
setup screen all take them from there, and Replay files name them by that name."""

import random

import pytest
import tm_engine

from ai.controller import handle_for
from ai.controllers import REGISTERED, available, make_controller
from ai.random_bot import RandomBot


def test_the_random_bot_is_registered_with_a_label():
    assert REGISTERED["random_bot"].label == "Random Bot"
    assert isinstance(make_controller("random_bot"), RandomBot)


def test_each_player_gets_a_controller_of_their_own():
    assert make_controller("random_bot") is not make_controller("random_bot")


def test_an_unregistered_controller_can_be_named_by_module_and_attribute():
    # For trying a Controller out in a Match before it is registered.
    assert isinstance(make_controller("ai.random_bot:RandomBot"), RandomBot)


def test_an_unknown_controller_is_refused_with_the_known_names():
    with pytest.raises(ValueError, match="unknown Controller 'deep_blue'.*random_bot"):
        make_controller("deep_blue")
    with pytest.raises(ValueError, match="no_such_module"):
        make_controller("no_such_module:Bot")


def test_human_is_not_a_registered_controller():
    # A human answers through the GUI; the server handles them itself.
    assert "human" not in REGISTERED


def test_a_registered_controller_picks_an_offered_option():
    game = tm_engine.Game(seed=2, players=2, draft=True, prelude=True)
    for name in available():
        index = make_controller(name).pick(handle_for(game, random.Random(0)))
        assert 0 <= index < len(game.decision["options"])
