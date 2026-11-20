"""What the Value Model learns from (ticket 15 of phase 2): one Player's view of each position of a Game, with
whether that Player won and by how many Victory Points. The positions come from Recorded Games' replays through
the engine, and from the loop's own Games."""

import gzip
import json
import random

import tm_engine

from ai.encoding import GLOBAL_FIELDS, OPTION_FIELDS
from ai.imitation.encoded import Position
from ai.value.encoded import FOLLOW_UPS, view_position
from ai.value.samples import recorded_samples, replay_samples, results_of, self_play_samples, stack_samples
from tests.ai.imitation.test_positions import example, replay_of_the_example, write_dataset

DECIDING = [index for index, name in enumerate(GLOBAL_FIELDS) if name.startswith("deciding_")]


def played(seed: int = 3) -> tm_engine.Game:
    game = tm_engine.Game(seed=seed, players=2, draft=True, prelude=True)
    game.play_randomly(seed=seed)
    return game


def settled_positions(replay: dict) -> int:
    """The Decisions of a Replay that aren't a follow-up of the Decision before (ai.value.encoded.FOLLOW_UPS): the
    positions the Value Bot rates, and so those it learns from."""
    game = tm_engine.Game.from_replay({"start": replay["start"], "picks": []})
    count = 0
    for picked in replay["picks"]:
        count += game.decision["kind"] not in FOLLOW_UPS
        game.pick(picked)
    return count


def test_a_view_position_is_the_player_view_alone_with_no_decision_or_options():
    game = tm_engine.Game(seed=1, players=2, draft=True, prelude=True)
    view = game.player_view(1)

    position = view_position(view)

    assert position.options.shape == (0, len(OPTION_FIELDS))
    assert not position.globals[DECIDING].any()
    assert (position.cards == Position.of(view, game.decision).cards).all()
    assert position.player == 1


def test_results_say_who_won_a_draw_counting_half_and_each_players_margin():
    scores = [{"player": 0, "total": 80, "rank": 2}, {"player": 1, "total": 92, "rank": 1}]
    assert results_of(scores) == ([0.0, 1.0], [-12, 12])
    drawn = [{"player": 0, "total": 80, "rank": 1}, {"player": 1, "total": 80, "rank": 1}]
    assert results_of(drawn) == ([0.5, 0.5], [0, 0])


def test_a_replay_gives_one_players_view_of_each_position_with_that_players_result():
    game = played()
    results, margins = results_of(game.scores)

    samples = list(replay_samples(game.replay, results, margins, random.Random(0)))

    assert len(samples) == settled_positions(game.replay)
    assert {sample.position.player for sample in samples} == {0, 1}
    for sample in samples[::50]:
        assert sample.result == results[sample.position.player]
        assert sample.margin == margins[sample.position.player]


def test_the_loops_games_are_read_back_from_their_file(tmp_path):
    game = played()
    results, margins = results_of(game.scores)
    path = tmp_path / "round-001.jsonl.gz"
    with gzip.open(path, "wt") as file:
        file.write(json.dumps({"replay": game.replay, "results": results, "margins": margins}) + "\n")

    samples = list(self_play_samples(path, random.Random(0)))

    assert len(samples) == settled_positions(game.replay)


def recorded(game_id: str, *, conceded: bool = False, date: str = "2024-01-01") -> dict:
    game = example(game_id, date=date)
    points = [90, 75]
    players = [
        {**board, "winner": won, "victory_points": vp} for board, won, vp in zip(game["players"], [True, False], points)
    ]
    return {**game, "players": players, "conceded": conceded}


def test_recorded_games_give_their_replays_positions_with_the_logs_winner(tmp_path):
    replay = replay_of_the_example()
    games = [recorded("example"), recorded("given_up", conceded=True), recorded("later", date="2026-01-01")]
    replays = [replay, {**replay, "game": "given_up"}, {**replay, "game": "later"}]
    folder = write_dataset(tmp_path, games, replays)
    shards = sorted((folder / "shards").iterdir())

    trained = [sample for shard in shards for sample in recorded_samples(shard, "train", random.Random(0))]

    assert len(trained) == settled_positions(replay["replay"])
    assert {(sample.result, sample.margin) for sample in trained if sample.position.player == 0} == {(1.0, 15)}
    assert {(sample.result, sample.margin) for sample in trained if sample.position.player == 1} == {(0.0, -15)}


def test_samples_stack_into_arrays_with_their_targets():
    game = played()
    samples = list(replay_samples(game.replay, *results_of(game.scores), random.Random(0)))[:5]

    stacked = stack_samples(samples)

    assert stacked["result"].shape == (5,)
    assert stacked["margin"].tolist() == [sample.margin for sample in samples]
    assert stacked["cards"].shape[0] == 5


def test_a_recorded_game_whose_replay_never_started_gives_nothing(tmp_path):
    # The Game stopped before the engine could start it (ai.recorded_games.replay).
    folder = write_dataset(tmp_path, [recorded("example")], [{**replay_of_the_example(), "replay": None}])

    assert list(recorded_samples(next((folder / "shards").iterdir()), "train", random.Random(0))) == []


def test_only_a_share_of_a_games_positions_is_kept_so_that_a_batch_mixes_many_games():
    # Every position of a Game has the same result: with all of them, a model learns which Game it is in.
    game = played()
    results, margins = results_of(game.scores)

    kept = list(replay_samples(game.replay, results, margins, random.Random(0), keep=0.25))

    assert 0.15 * settled_positions(game.replay) < len(kept) < 0.35 * settled_positions(game.replay)
