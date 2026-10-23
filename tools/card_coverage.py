"""Lists the catalog cards that have no scenario test yet (spec story 97):

    uv run python -m tools.card_coverage

Each card's scenario tests live in `tests/cards/test_<id>.py`, such as
`tests/cards/test_black_polar_dust.py`, so a card without that file has none. For now the
list is only a report, which the test suite shows as a warning; ticket 24 makes the suite
fail while any card is left on it.
"""

from pathlib import Path
from typing import Any

import tm_engine

from tools.card_import import PROJECT

CARD_TESTS = PROJECT / "tests" / "cards"


def untested_cards(card_tests: Path = CARD_TESTS) -> list[dict[str, Any]]:
    """The catalog cards, in catalog order, that have no test file in `card_tests`."""
    return [card for card in tm_engine.card_catalog() if not (card_tests / f"test_{card['id']}.py").exists()]


def report(untested: list[dict[str, Any]]) -> str:
    """'209 of 220 cards have no scenario test:' and one line per card, or that every card has one."""
    total = len(tm_engine.card_catalog())
    if not untested:
        return f"All {total} cards have a scenario test."
    lines = [f"{len(untested)} of {total} cards have no scenario test (tests/cards/test_<id>.py):"]
    for card in untested:
        number = f"#{card['number']:03} " if card["number"] is not None else ""
        lines.append(f"  {number}{card['name']} ({card['id']})")
    return "\n".join(lines)


def main() -> None:
    print(report(untested_cards()))


if __name__ == "__main__":
    main()
