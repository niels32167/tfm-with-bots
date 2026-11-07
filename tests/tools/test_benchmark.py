"""The speed benchmark (`uv run python -m tools.benchmark`) still runs. A tiny run here
only checks that it works; its numbers mean nothing at this size."""

from tools.benchmark import mean_generations, measure, play_out, report


def test_the_benchmark_measures_games_per_second_copy_times_and_a_python_loop():
    results = measure(seconds=0.2, processes=2, games_for_mean_generations=10)

    assert results.games_per_second_in_one_process > 0
    assert results.games_per_second_in_all_processes > 0
    assert [copy.moment for copy in results.copies] == ["at the start", "halfway", "at the end"]
    assert all(copy.microseconds > 0 for copy in results.copies)
    assert results.copies[-1].log_lines > results.copies[0].log_lines
    assert results.python_decisions_per_second > 0
    assert "Games per second" in report(results)


def test_the_benchmark_can_measure_games_with_prelude():
    results = measure(seconds=0.2, processes=2, prelude=True, games_for_mean_generations=10)

    assert play_out(seed=1, prelude=True).replay["start"]["settings"]["prelude"] is True
    assert "prelude" not in play_out(seed=1).replay["start"]["settings"]
    assert results.games_per_second_in_all_processes > 0
    assert "2-player Games with the Draft and Prelude" in report(results)


def test_prelude_shortens_random_bot_games_as_the_benchmark_reports():
    # ADR 0011: Prelude shortens Games.
    assert mean_generations(games=200, prelude=True) < mean_generations(games=200, prelude=False)

    text = report(measure(seconds=0.2, processes=2, games_for_mean_generations=10))

    assert "Mean Generations of Random Bot Games, without Prelude:" in text
    assert "with Prelude:" in text
