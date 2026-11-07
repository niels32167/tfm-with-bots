"""The coverage check (`uv run python -m tools.card_coverage`) lists every implemented catalog card
without a scenario test: `tests/cards/test_<id>.py`, holding a test that names the card. The suite
fails while any card is on the list, and so does the command. A card without effect data isn't
implemented yet, so it needs no test until it gets some; it is named as not implemented instead."""

import pytest
import tm_engine

from tools.card_coverage import (
    is_implemented,
    main,
    not_implemented_cards,
    report,
    untested_cards,
)


NOT_IMPLEMENTED_NOTE = "21 more cards are not implemented yet, so they need no test yet."


def card_test(card):
    return f'def test_it():\n    game = scenario(player(hand=["{card}"]), player())\n    assert game\n'


def test_a_card_counts_as_tested_once_a_test_in_its_own_file_names_it(tmp_path):
    (tmp_path / "test_mine.py").write_text(card_test("mine"))
    (tmp_path / "test_credicor.py").write_text(card_test("credicor"))

    untested = [card["id"] for card in untested_cards(tmp_path)]

    assert len(untested) == 246 - 2
    assert "mine" not in untested and "credicor" not in untested
    assert untested[:2] == ["colonizer_training_camp", "asteroid_mining_consortium"]


def test_every_implemented_project_card_and_corporation_needs_a_scenario_test(tmp_path):
    untested = untested_cards(tmp_path)

    assert sum(card["type"] not in ("corporation", "prelude") for card in untested) == 208
    assert sum(card["type"] == "corporation" for card in untested) == 12
    assert sum(card["type"] == "prelude" for card in untested) == 26


def test_a_card_is_implemented_as_soon_as_it_has_effect_data():
    assert not is_implemented({"id": "research_network"})
    assert is_implemented({"id": "research_network", "effects": {}})


def test_cards_not_implemented_yet_are_not_on_the_list(tmp_path):
    untested = [card["id"] for card in untested_cards(tmp_path)]
    not_implemented = [card["id"] for card in not_implemented_cards()]

    assert len(not_implemented) == 21
    assert "research_network" in not_implemented and "vitor" in not_implemented and "house_printing" in not_implemented
    assert "donation" not in not_implemented
    assert not set(untested) & set(not_implemented)


def test_only_the_prelude_boxs_cards_may_lack_effect_data():
    # Ticket 05 ends this: by then, every card must have it.
    assert {card["expansion"] for card in not_implemented_cards()} == {"prelude"}


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
        "2 of 246 implemented cards have no scenario test (tests/cards/test_<id>.py):",
        "  CrediCor (credicor)",
        "  EcoLine (ecoline)",
        NOT_IMPLEMENTED_NOTE,
    ]
    assert report([]).splitlines() == ["All 246 implemented cards have a scenario test.", NOT_IMPLEMENTED_NOTE]


def test_the_report_gives_a_card_of_the_prelude_box_its_printed_number():
    house_printing = next(card for card in tm_engine.card_catalog() if card["id"] == "house_printing")
    mine = next(card for card in tm_engine.card_catalog() if card["id"] == "mine")

    assert report([mine, house_printing]).splitlines()[1:3] == [
        "  #056 Mine (mine)",
        "  #P36 House Printing (house_printing)",
    ]


def test_the_command_fails_while_a_card_is_untested(tmp_path, capsys):
    assert main(tmp_path) == 1
    assert "246 of 246 implemented cards have no scenario test" in capsys.readouterr().out

    for card in tm_engine.card_catalog():
        (tmp_path / f"test_{card['id']}.py").write_text(card_test(card["id"]))

    assert main(tmp_path) == 0
    assert "All 246 implemented cards have a scenario test." in capsys.readouterr().out


def test_every_card_has_a_scenario_test():
    untested = untested_cards()

    assert not untested, report(untested)
