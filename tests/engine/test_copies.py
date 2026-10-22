"""Copying a Game: cheap, and fully independent of the original (ADR 0004)."""

import tm_engine

from tests.helpers import everything_about, play_randomly


def test_a_copy_is_identical_to_its_original():
    original = tm_engine.Game(seed=5, players=3)
    play_randomly(original, seed=1, picks=10)

    copy = original.copy()

    assert everything_about(copy) == everything_about(original)


def test_changing_a_copied_game_never_changes_the_original():
    original = tm_engine.Game(seed=5, players=3)
    play_randomly(original, seed=1, picks=10)
    before = everything_about(original)

    copy = original.copy()
    play_randomly(copy, seed=2)

    assert copy.is_over
    assert everything_about(original) == before


def test_changing_the_original_never_changes_the_copy():
    original = tm_engine.Game(seed=5, players=3)
    play_randomly(original, seed=1, picks=10)
    copy = original.copy()
    before = everything_about(copy)

    play_randomly(original, seed=2)

    assert original.is_over
    assert everything_about(copy) == before


def test_a_copy_plays_on_exactly_as_its_original_would():
    original = tm_engine.Game(seed=5, players=3)
    play_randomly(original, seed=1, picks=10)
    copy = original.copy()

    play_randomly(original, seed=2)
    play_randomly(copy, seed=2)

    assert everything_about(copy) == everything_about(original)
