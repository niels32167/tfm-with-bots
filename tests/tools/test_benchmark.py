"""The speed benchmark (`uv run python -m tools.benchmark`) still runs. A tiny run here
only checks that it works; its numbers mean nothing at this size."""

from tools.benchmark import measure, report


def test_the_benchmark_measures_games_per_second_copy_times_and_a_python_loop():
    results = measure(seconds=0.2, processes=2)

    assert results.games_per_second_in_one_process > 0
    assert results.games_per_second_in_all_processes > 0
    assert [copy.moment for copy in results.copies] == ["at the start", "halfway", "at the end"]
    assert all(copy.microseconds > 0 for copy in results.copies)
    assert results.copies[-1].log_lines > results.copies[0].log_lines
    assert results.python_decisions_per_second > 0
    assert "Games per second" in report(results)
