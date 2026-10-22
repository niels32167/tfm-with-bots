"""Replays: a Game's settings and seed (or Scenario) plus the Options picked, in order.
A Replay reproduces its Game exactly (ADR 0010)."""

import json

import pytest
import tm_engine

from tests.helpers import MAX_PICKS, city, everything_about, ocean, pick, play_randomly, player, scenario


def test_a_replay_holds_the_settings_and_seed_and_the_options_picked():
    game = tm_engine.Game(seed=7, players=3)

    pick(game, "Asteroid")
    pick(game, "End Turn")
    pick(game, "Pass")

    # With 28 MegaCredits left: Asteroid, Aquifer, Greenery, City, End Turn, Pass.
    # Then with 42: Asteroid, Aquifer, Greenery, City, Pass.
    assert game.replay == {"start": {"settings": {"players": 3, "seed": 7}}, "picks": [0, 4, 4]}


def test_loading_an_exported_replay_gives_back_the_same_game():
    game = tm_engine.Game(seed=7, players=3)
    play_randomly(game, seed=1, picks=25)

    loaded = tm_engine.Game.from_replay(game.replay)

    assert everything_about(loaded) == everything_about(game)
    assert loaded.replay == game.replay
    assert loaded.seed == 7


def test_a_finished_game_loads_from_its_replay_with_its_final_scores():
    game = tm_engine.Game(seed=8, players=4)
    play_randomly(game, seed=2)

    loaded = tm_engine.Game.from_replay(game.replay)

    assert loaded.is_over
    assert loaded.scores == game.scores
    assert everything_about(loaded) == everything_about(game)


def test_a_game_started_from_a_scenario_loads_from_its_replay():
    game = scenario(
        player(megacredits=60, plants=12, production={"megacredits": 3}),
        player(terraform_rating=25, steel=4),
        player(megacredits=0),
        generation=3,
        temperature=-10,
        oxygen=6,
        tiles=[ocean("A2"), city("C3", owner=1)],
        first_player=1,
        seed=11,
    )
    play_randomly(game, seed=3, picks=20)

    loaded = tm_engine.Game.from_replay(game.replay)

    assert game.replay["start"]["scenario"]["temperature"] == -10
    assert game.replay["start"]["scenario"]["tiles"] == [
        {"area": "A2", "tile": "ocean", "owner": None},
        {"area": "C3", "tile": "city", "owner": 1},
    ]
    assert everything_about(loaded) == everything_about(game)
    assert loaded.replay == game.replay


def test_a_replay_survives_being_saved_as_json():
    game = scenario(player(megacredits=60), player(), temperature=-20, seed=4)
    play_randomly(game, seed=4, picks=15)

    saved = json.dumps(game.replay)
    loaded = tm_engine.Game.from_replay(json.loads(saved))

    assert everything_about(loaded) == everything_about(game)


def test_a_replay_rebuilds_the_game_as_it_was_at_any_step():
    game = tm_engine.Game(seed=9, players=2)
    as_it_was = [everything_about(game)]
    for step in range(MAX_PICKS):
        if game.is_over:
            break
        play_randomly(game, seed=step, picks=1)
        as_it_was.append(everything_about(game))
    assert game.is_over
    replay = game.replay

    for step, expected in enumerate(as_it_was):
        assert everything_about(tm_engine.Game.from_replay(replay, step=step)) == expected


def test_a_game_rebuilt_at_an_earlier_step_has_only_that_part_of_the_replay():
    game = tm_engine.Game(seed=9, players=2)
    play_randomly(game, seed=5, picks=12)

    earlier = tm_engine.Game.from_replay(game.replay, step=4)

    assert earlier.replay == {**game.replay, "picks": game.replay["picks"][:4]}


def test_there_is_no_step_beyond_the_end_of_a_replay():
    game = tm_engine.Game(seed=9, players=2)
    play_randomly(game, seed=5, picks=3)

    with pytest.raises(ValueError, match="no step 4; the Replay has 3 picks"):
        tm_engine.Game.from_replay(game.replay, step=4)


def test_a_replay_with_a_pick_the_game_does_not_offer_is_rejected():
    replay = {"start": {"settings": {"players": 2, "seed": 1}}, "picks": [0, 7]}

    with pytest.raises(ValueError, match="pick 2 of the Replay: there is no Option 7"):
        tm_engine.Game.from_replay(replay)


def test_a_replay_with_picks_after_the_game_is_over_is_rejected():
    game = tm_engine.Game(seed=9, players=2)
    play_randomly(game, seed=5)
    replay = {**game.replay, "picks": [*game.replay["picks"], 0]}

    with pytest.raises(ValueError, match="the Game is over"):
        tm_engine.Game.from_replay(replay)


def test_a_replay_that_is_not_a_replay_is_rejected():
    with pytest.raises(ValueError, match="invalid Replay"):
        tm_engine.Game.from_replay({"start": {"settings": {"players": 2, "seed": 1}}})
    with pytest.raises(ValueError, match="invalid Replay"):
        tm_engine.Game.from_replay({"start": {"rules": {}}, "picks": []})
    with pytest.raises(ValueError, match="2 to 5 Players"):
        tm_engine.Game.from_replay({"start": {"settings": {"players": 9, "seed": 1}}, "picks": []})
