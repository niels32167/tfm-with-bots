"""Games are held out for testing by whole Game, and by date where the date is known (ticket 13 of phase 2):
training on earlier Games and testing on later ones, as the AI will meet Players after it was trained."""

from collections import Counter

from ai.imitation.split import TEST_FROM, VALIDATION_FROM, split_of


def a_game(game_id: str, date: str | None) -> dict:
    return {"game": game_id, "date": date}


def test_dated_games_train_before_the_validation_dates_and_test_on_the_latest():
    assert split_of(a_game("a", "2024-03-01")) == "train"
    assert split_of(a_game("a", "2025-09-08")) == "train"
    assert split_of(a_game("a", "2025-09-09")) == "validation"
    assert split_of(a_game("a", "2025-09-29")) == "validation"
    assert split_of(a_game("a", "2025-09-30")) == "test"
    assert split_of(a_game("a", "2026-01-07")) == "test"
    assert VALIDATION_FROM < TEST_FROM


def test_a_game_without_a_date_goes_by_its_id_the_same_way_every_time_in_80_10_10():
    parts = Counter(split_of(a_game(f"game-{number}", None)) for number in range(10_000))

    assert split_of(a_game("game-7", None)) == split_of(a_game("game-7", None))
    assert 7_700 < parts["train"] < 8_300
    assert 850 < parts["validation"] < 1_150
    assert 850 < parts["test"] < 1_150
