"""The Match tool (`uv run python -m ai.match a b --games N`): two Controllers play N Games on N/2 seeds,
each Controller taking each Player on every seed, and it reports how they did."""

import functools
import json

import pytest
import tm_engine

from ai.controller import Handle
from ai.match import Claim, MatchSettings, game_summary, main, report, run_match
from tests.helpers import city, pick, player, scenario


class FirstOption:
    """Always picks the first Option, ignoring its random source."""

    def pick(self, handle: Handle) -> int:
        return 0


class Broken:
    """Raises on its first Action."""

    def pick(self, handle: Handle) -> int:
        if handle.decision["kind"] == "action":
            raise RuntimeError("out of ideas")
        return 0


class OutOfRange:
    def pick(self, handle: Handle) -> int:
        return len(handle.decision["options"])


def test_each_controller_takes_each_player_on_every_seed():
    match = run_match("random_bot", "tests.ai.test_match:FirstOption", games=6, first_seed=40, processes=1)

    assert [(game.seed, game.controllers) for game in match.games] == [
        (seed, order)
        for seed in (40, 41, 42)
        for order in (
            ("random_bot", "tests.ai.test_match:FirstOption"),
            ("tests.ai.test_match:FirstOption", "random_bot"),
        )
    ]
    assert all(game.outcome == "over" for game in match.games)
    # Prelude Games with the Draft, by default (ADR 0011).
    settings = match.games[0].replay["start"]["settings"]
    assert settings == {"players": 2, "seed": 40, "draft": True, "corporations": True, "prelude": True}


def test_the_results_agree_with_the_games_replayed():
    match = run_match("random_bot", "random_bot", games=8, first_seed=0, processes=1)

    for game in match.games:
        scores = tm_engine.Game.from_replay(game.replay).scores
        assert game.scores == scores
    a, b = match.sides
    winners = [
        [score["rank"] for score in game.scores].count(1) == 1 and game.scores[game.player_of(0)]["rank"] == 1
        for game in match.games
    ]
    draws = sum([score["rank"] for score in game.scores].count(1) == 2 for game in match.games)
    assert a.wins == sum(winners)
    assert a.wins + b.wins + draws == 8
    assert a.score + b.score == pytest.approx(1)
    assert a.interval[0] <= a.score <= a.interval[1]


def test_the_report_has_win_rates_with_intervals_points_generations_and_player_order():
    match = run_match("random_bot", "random_bot", games=10, first_seed=0, processes=1)

    text = report(match)

    for wanted in [
        "random_bot",
        "95% interval",
        "Victory Points",
        "card Victory Points",
        "Terraform Rating",
        "Generations",
        "Player 1 won",
        "first player won",
        "stalled: 0",
    ]:
        assert wanted in text, wanted


def test_the_same_seeds_and_controllers_give_the_same_results():
    first = run_match("random_bot", "random_bot", games=6, first_seed=3, processes=1)
    again = run_match("random_bot", "random_bot", games=6, first_seed=3, processes=1)
    on_two_processes = run_match("random_bot", "random_bot", games=6, first_seed=3, processes=2)

    assert first == again == on_two_processes


def test_a_controller_against_itself_does_not_play_the_same_game_twice_on_a_seed():
    # Otherwise a mirror Match would show exactly 50% and prove nothing.
    match = run_match("random_bot", "random_bot", games=2, first_seed=7, processes=1)

    assert match.games[0].replay["picks"] != match.games[1].replay["picks"]


def test_a_game_past_the_pick_limit_is_counted_as_stalled_and_not_in_the_win_rate(tmp_path):
    settings = MatchSettings(pick_limit=30, failures_folder=tmp_path)
    match = run_match("random_bot", "random_bot", games=4, first_seed=0, processes=1, settings=settings)

    assert [game.outcome for game in match.games] == ["stalled"] * 4
    assert match.stalled == 4
    assert match.sides[0].finished == 0
    assert "stalled: 4" in report(match)
    assert len(list(tmp_path.glob("*.json"))) == 4


@pytest.mark.parametrize("broken", ["Broken", "OutOfRange"])
def test_a_game_that_goes_wrong_is_saved_as_a_replay_file(tmp_path, broken):
    settings = MatchSettings(failures_folder=tmp_path)
    name = f"tests.ai.test_match:{broken}"
    match = run_match(name, "random_bot", games=2, first_seed=0, processes=1, settings=settings)

    assert [game.outcome for game in match.games] == ["failed", "failed"]
    assert all(name in game.problem for game in match.games)
    files = sorted(tmp_path.glob("*.json"))
    assert len(files) == 2
    file = json.loads(files[0].read_text())
    assert file["controllers"] in ([name, "random_bot"], ["random_bot", name])
    # The Replay stops just before the pick that went wrong, so loading it shows that moment.
    resumed = tm_engine.Game.from_replay(file["replay"])
    assert resumed.decision is not None


def test_the_exit_status_says_whether_the_threshold_was_met(tmp_path, capsys):
    common = ["random_bot", "random_bot", "--games", "20", "--failures-folder", str(tmp_path)]

    assert main([*common, "--threshold", "0.0"]) == 0
    assert main([*common, "--threshold", "0.5"]) == 1  # a Random Bot can't beat itself
    assert main(common) == 0
    assert "Win rate" in capsys.readouterr().out


def test_the_exit_status_says_when_a_game_failed(tmp_path):
    arguments = ["tests.ai.test_match:Broken", "random_bot", "--games", "2", "--failures-folder", str(tmp_path)]

    assert main(arguments) == 3


def test_the_number_of_games_must_be_even_and_the_controllers_known():
    with pytest.raises(SystemExit):
        main(["random_bot", "random_bot", "--games", "3"])
    with pytest.raises(SystemExit):
        main(["random_bot", "deep_blue", "--games", "2"])


def test_games_without_prelude_or_the_draft_can_be_played():
    settings = MatchSettings(draft=False, prelude=False)
    match = run_match("random_bot", "random_bot", games=2, first_seed=0, processes=1, settings=settings)

    assert match.games[0].replay["start"]["settings"]["draft"] is False
    assert "prelude" not in match.games[0].replay["start"]["settings"]
    assert all(game.outcome == "over" for game in match.games)


class Picking:
    """Always picks the Option at a fixed index, or the last if there are fewer: a Controller made with
    a setting, as the fitting of Prices makes them."""

    def __init__(self, index: int) -> None:
        self.index = index

    def pick(self, handle: Handle) -> int:
        return min(self.index, len(handle.decision["options"]) - 1)


def test_a_match_can_be_played_between_controllers_made_by_factories():
    match = run_match(
        "first",
        "second",
        games=4,
        first_seed=3,
        processes=2,
        makers=(functools.partial(Picking, 0), functools.partial(Picking, 1)),
    )

    assert [game.controllers for game in match.games] == [("first", "second"), ("second", "first")] * 2
    assert all(game.outcome == "over" for game in match.games)
    # The names only label the factories.
    makers = (functools.partial(Picking, 0), functools.partial(Picking, 1))
    renamed = run_match("x", "y", games=4, first_seed=3, processes=1, makers=makers)
    assert [game.replay for game in renamed.games] == [game.replay for game in match.games]


def test_a_games_summary_gives_each_claim_with_its_generation_and_whether_a_funded_award_was_lost():
    # Ticket 14, box 4. Player 1 claims Terraformer and funds Landlord in Generation 4, while Player 2 owns more
    # Tiles: an Award its funder loses at the end (the flip rate's case).
    game = scenario(
        player(terraform_rating=35, megacredits=40),
        player(),
        generation=4,
        tiles=[city("C3", owner=1), city("H2", owner=1)],
    )
    pick(game, type="claim_milestone", milestone="terraformer")
    pick(game, type="fund_award", award="landlord")

    summary = game_summary(game.replay)

    assert summary.milestones == [Claim("terraformer", player=0, generation=4)]
    assert summary.awards == [Claim("landlord", player=0, generation=4, lost=True)]
    assert summary.generations == 4
