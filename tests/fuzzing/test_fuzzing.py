"""The fuzzer: Random Bot Games with 2 to 5 Players, checked after every Decision. A short
run is part of the normal test suite; `uv run python -m tests.fuzzing` is the full one."""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import tm_engine

from tests.fuzzing.runner import fuzz, fuzz_game, save_failure, settings_for
from tests.helpers import CORPORATIONS, PRELUDE_CORPORATIONS


def test_about_a_thousand_fuzzed_games_break_no_invariant_and_play_nearly_every_card():
    run = fuzz(games=1000, first_seed=0)

    assert run.games == 1000
    assert not run.failures, "\n".join(failure.description() for failure in run.failures)
    # Random Bots seldom reach some Requirements, such as Anti-Gravity Technology's 7 science Tags.
    assert len(run.cards_never_played) <= 5, run.cards_never_played


def test_fuzzed_games_cover_2_to_5_players_and_the_draft_and_prelude_on_and_off():
    settings = [settings_for(seed) for seed in range(16)]

    assert [each["players"] for each in settings] == [2, 3, 4, 5] * 4
    assert [each["draft"] for each in settings] == ([True] * 4 + [False] * 4) * 2
    assert [each["prelude"] for each in settings] == [False] * 8 + [True] * 8


def test_fuzzed_games_play_every_corporation():
    played = set()
    for seed in range(40):
        game = tm_engine.Game(seed=seed, **settings_for(seed))
        game.play_randomly(seed=seed, picks=120)
        played |= {board["corporation"] for board in game.full_view()["players"]}

    assert played - {None} == set(CORPORATIONS) | set(PRELUDE_CORPORATIONS)


def test_a_fuzzed_game_that_breaks_nothing_has_no_failure():
    game = fuzz_game(seed=1, players=3)

    assert game.failure is None
    assert game.decisions > 0


def temperature_stays_below(limit: int):
    """A planted invariant that real Games break, to see what the fuzzer does with a failure."""

    def check(view: dict[str, Any], decision: dict[str, Any] | None) -> Iterator[str]:
        if view["temperature"] >= limit:
            yield f"Temperature reached {view['temperature']} °C"

    return check


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def test_a_broken_invariant_is_saved_as_a_replay_file_that_reproduces_it(tmp_path):
    check = temperature_stays_below(-20)
    failure = fuzz_game(seed=1, players=3, after_every_decision=[check]).failure

    file = load(save_failure(failure, tmp_path))

    game = tm_engine.Game.from_replay(file["replay"])
    assert list(check(game.full_view(), game.decision)) == ["Temperature reached -20 °C"]
    picks = len(file["replay"]["picks"])
    before = tm_engine.Game.from_replay(file["replay"], step=picks - 1)
    assert list(check(before.full_view(), before.decision)) == []
    assert file["problems"] == ["Temperature reached -20 °C"]


def test_a_saved_failure_opens_in_the_gui_with_every_player_human_to_undo_from(tmp_path):
    failure = fuzz_game(seed=1, players=3, after_every_decision=[temperature_stays_below(-20)]).failure

    path = save_failure(failure, tmp_path)

    assert path.name == "3-players-seed-1.json"
    assert load(path)["controllers"] == ["human", "human", "human"]


def test_an_engine_error_on_a_pick_is_saved_as_a_replay_up_to_that_pick_and_the_pick_that_raises_it(tmp_path):
    def picks_an_option_never_offered_at_decision_10(random_numbers, decision):
        options = len(decision["options"])
        return options if decision["sequence"] == 10 else random_numbers.randrange(options)

    failure = fuzz_game(seed=1, players=2, pick=picks_an_option_never_offered_at_decision_10).failure

    assert failure.problems[0].startswith("picking Option ")
    assert "(not offered) raised ValueError: there is no Option" in failure.problems[0]
    file = load(save_failure(failure, tmp_path))
    # The Replay stops before the failing pick, so it loads (in the GUI too) at that Decision.
    game = tm_engine.Game.from_replay(file["replay"])
    assert game.decision["sequence"] == 10
    with pytest.raises(ValueError, match="there is no Option"):
        game.pick(file["failing_pick"])


def test_an_error_while_checking_a_position_is_saved_as_a_replay_of_that_position():
    def breaks_at(view, decision):
        if view["temperature"] >= -20:
            raise KeyError("planted")
        yield from ()

    failure = fuzz_game(seed=1, players=2, after_every_decision=[breaks_at]).failure

    assert failure.problems == ["checking the Game raised KeyError: 'planted'"]
    assert failure.failing_pick is None
    assert tm_engine.Game.from_replay(failure.replay).full_view()["temperature"] == -20


def test_a_game_still_going_past_the_generation_limit_is_a_failure():
    failure = fuzz_game(seed=1, players=2, generation_limit=3).failure

    assert failure.problems == ["the Game is still going in Generation 4, past the fuzzing limit of 3 Generations"]
    game = tm_engine.Game.from_replay(failure.replay)
    assert game.player_view(0)["generation"] == 4
    assert not game.is_over


def test_a_game_still_going_past_the_pick_limit_is_a_failure():
    failure = fuzz_game(seed=1, players=2, pick_limit=50).failure

    assert failure.problems == ["the Game is still going after 50 picks, past the fuzzing limit"]
    assert len(failure.replay["picks"]) == 50


def test_the_end_of_game_checks_run_once_the_game_is_over():
    def always_broken(view, decision):
        yield "planted"

    failure = fuzz_game(seed=1, players=2, at_the_end=[always_broken]).failure

    assert failure.problems == ["planted"]
    assert tm_engine.Game.from_replay(failure.replay).is_over
