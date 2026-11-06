"""The coverage check (`uv run python -m tools.card_coverage`) lists every catalog card without
a scenario test: `tests/cards/test_<id>.py`, holding a test that names the card. The suite fails
while any card is on the list, and so does the command."""

import pytest
import tm_engine

from tools.card_coverage import main, report, untested_cards


def card_test(card):
    return f'def test_it():\n    game = scenario(player(hand=["{card}"]), player())\n    assert game\n'


def test_a_card_counts_as_tested_once_a_test_in_its_own_file_names_it(tmp_path):
    (tmp_path / "test_mine.py").write_text(card_test("mine"))
    (tmp_path / "test_credicor.py").write_text(card_test("credicor"))

    untested = [card["id"] for card in untested_cards(tmp_path)]

    assert len(untested) == 220 - 2
    assert "mine" not in untested and "credicor" not in untested
    assert untested[:2] == ["colonizer_training_camp", "asteroid_mining_consortium"]


def test_every_project_card_and_corporation_needs_a_scenario_test(tmp_path):
    untested = untested_cards(tmp_path)

    assert sum(card["type"] != "corporation" for card in untested) == 208
    assert sum(card["type"] == "corporation" for card in untested) == 12


def test_a_file_without_a_test_does_not_count(tmp_path):
    (tmp_path / "test_mine.py").write_text('"""#056 Mine, tests to come."""\n\nCARD = "mine"\n')

    assert "mine" in [card["id"] for card in untested_cards(tmp_path)]


def test_a_test_that_never_names_the_card_does_not_count(tmp_path):
    (tmp_path / "test_mine.py").write_text(card_test("trees"))

    assert "mine" in [card["id"] for card in untested_cards(tmp_path)]


def test_a_test_that_asserts_nothing_does_not_count(tmp_path):
    (tmp_path / "test_mine.py").write_text('def test_it():\n    "mine"\n')

    assert "mine" in [card["id"] for card in untested_cards(tmp_path)]


@pytest.mark.parametrize("mark", ["skip", "skipif(True, reason='later')", "xfail"])
def test_a_test_marked_to_be_skipped_or_to_fail_does_not_count(tmp_path, mark):
    (tmp_path / "test_mine.py").write_text(
        f'import pytest\n\n@pytest.mark.{mark}\ndef test_it():\n    assert "mine"\n'
    )

    assert "mine" in [card["id"] for card in untested_cards(tmp_path)]


def test_the_report_names_each_untested_card_by_number_and_name(tmp_path):
    cards = [card for card in untested_cards(tmp_path) if card["id"] in ("credicor", "ecoline")]

    assert report(cards).splitlines() == [
        "2 of 220 cards have no scenario test (tests/cards/test_<id>.py):",
        "  CrediCor (credicor)",
        "  EcoLine (ecoline)",
    ]
    assert report([]) == "All 220 cards have a scenario test."


def test_the_command_fails_while_a_card_is_untested(tmp_path, capsys):
    assert main(tmp_path) == 1
    assert "220 of 220 cards have no scenario test" in capsys.readouterr().out

    for card in tm_engine.card_catalog():
        (tmp_path / f"test_{card['id']}.py").write_text(card_test(card["id"]))

    assert main(tmp_path) == 0
    assert "All 220 cards have a scenario test." in capsys.readouterr().out


def test_every_card_has_a_scenario_test():
    untested = untested_cards()

    assert not untested, report(untested)
