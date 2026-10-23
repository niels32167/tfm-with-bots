"""Random Bot playouts inside the engine: a Game played on with random Options, fast enough
for the speed benchmark and, later, for search (ADR 0004)."""

import tm_engine

from tests.helpers import MAX_PICKS, everything_about, play_randomly


def test_a_random_playout_plays_the_game_to_the_end():
    game = tm_engine.Game(seed=3, players=2)

    game.play_randomly(seed=1, picks=MAX_PICKS)

    assert game.is_over
    assert game.decision is None
    assert len(game.scores) == 2


def test_a_random_playout_records_its_picks_so_the_replay_rebuilds_the_same_game():
    game = tm_engine.Game(seed=3, players=4)

    game.play_randomly(seed=1, picks=MAX_PICKS)

    assert game.is_over
    assert everything_about(tm_engine.Game.from_replay(game.replay)) == everything_about(game)


def test_the_same_seed_plays_out_the_same_way_and_another_seed_does_not():
    games = [tm_engine.Game(seed=3, players=3) for _ in range(3)]

    for game, seed in zip(games, [1, 1, 2]):
        game.play_randomly(seed=seed, picks=MAX_PICKS)

    assert all(game.is_over for game in games)
    assert games[0].replay == games[1].replay
    assert games[0].replay != games[2].replay


def test_a_random_playout_can_stop_after_a_number_of_picks():
    game = tm_engine.Game(seed=3, players=2)
    play_randomly(game, seed=1, picks=5)

    game.play_randomly(seed=2, picks=7)

    assert len(game.replay["picks"]) == 12
    assert not game.is_over


def test_a_random_playout_from_a_copy_leaves_the_original_as_it_was():
    original = tm_engine.Game(seed=3, players=2)
    play_randomly(original, seed=1, picks=20)
    before = everything_about(original)

    copy = original.copy()
    copy.play_randomly(seed=4, picks=MAX_PICKS)

    assert copy.is_over
    assert everything_about(original) == before


def test_a_random_playout_of_a_game_that_is_over_picks_nothing():
    game = tm_engine.Game(seed=3, players=2)
    play_randomly(game, seed=1)
    replay = game.replay

    game.play_randomly(seed=2)

    assert game.replay == replay
