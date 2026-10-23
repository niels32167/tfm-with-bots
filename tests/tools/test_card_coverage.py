"""The coverage check (`uv run python -m tools.card_coverage`) lists every catalog card without
a scenario test file, `tests/cards/test_<id>.py`. It only reports until ticket 24."""

import warnings

from tools.card_coverage import report, untested_cards


def test_a_card_counts_as_tested_once_it_has_its_own_test_file(tmp_path):
    (tmp_path / "test_mine.py").write_text("")
    (tmp_path / "test_credicor.py").write_text("")

    untested = [card["id"] for card in untested_cards(tmp_path)]

    assert len(untested) == 220 - 2
    assert "mine" not in untested and "credicor" not in untested
    assert untested[:2] == ["colonizer_training_camp", "asteroid_mining_consortium"]


def test_the_report_names_each_untested_card_by_number_and_name():
    cards = [card for card in untested_cards() if card["id"] in ("birds", "credicor")]

    assert report(cards).splitlines() == [
        "2 of 220 cards have no scenario test (tests/cards/test_<id>.py):",
        "  #072 Birds (birds)",
        "  CrediCor (credicor)",
    ]
    assert report([]) == "All 220 cards have a scenario test."


def test_the_cards_without_a_scenario_test_are_reported():
    # Report only: ticket 24 turns this warning into a failure.
    untested = untested_cards()
    if untested:
        count = report(untested).splitlines()[0]
        warnings.warn(f"{count} `uv run python -m tools.card_coverage` lists them.", stacklevel=1)
