"""Lists the implemented catalog cards, of every type, that have no scenario test (spec story 97).
The exit status is 1 if there are any, and the test suite fails too:

    uv run python -m tools.card_coverage

A card is implemented once it has effect data. Until then a Game never holds it, so it needs no
test yet, and the report says how many such cards there are.

Each card's scenario tests live in `tests/cards/test_<id>.py`, such as
`tests/cards/test_black_polar_dust.py`. A card has a scenario test if that file holds a test
function that names the card by its id, asserts something, and isn't marked to be skipped or to fail.
"""

import ast
import sys
from pathlib import Path
from typing import Any

import tm_engine

from tools.card_import import PROJECT, printed_number

CARD_TESTS = PROJECT / "tests" / "cards"


NOT_RUN_OR_ALLOWED_TO_FAIL = {"skip", "skipif", "xfail"}


def is_a_test_of(statement: ast.stmt, card_id: str) -> bool:
    """Whether `statement` is a test function that names `card_id` and asserts something, unmarked."""
    if not isinstance(statement, ast.FunctionDef) or not statement.name.startswith("test_"):
        return False
    marks = {
        node.attr for mark in statement.decorator_list for node in ast.walk(mark) if isinstance(node, ast.Attribute)
    }
    nodes = list(ast.walk(statement))
    return (
        not marks & NOT_RUN_OR_ALLOWED_TO_FAIL
        and any(isinstance(node, ast.Assert) for node in nodes)
        and any(isinstance(node, ast.Constant) and node.value == card_id for node in nodes)
    )


def has_a_test_of(path: Path, card_id: str) -> bool:
    """Whether the test file at `path` exists and has a test of the card `card_id`."""
    if not path.exists():
        return False
    return any(is_a_test_of(statement, card_id) for statement in ast.parse(path.read_text(encoding="utf-8")).body)


def is_implemented(card: dict[str, Any]) -> bool:
    """Whether `card` is implemented, as it is once it has effect data, and so needs a scenario test."""
    return "effects" in card


def not_implemented_cards() -> list[dict[str, Any]]:
    """The catalog cards, in catalog order, that are not implemented yet."""
    return [card for card in tm_engine.card_catalog() if not is_implemented(card)]


def untested_cards(card_tests: Path = CARD_TESTS) -> list[dict[str, Any]]:
    """The implemented catalog cards, in catalog order, that have no scenario test in `card_tests`."""
    return [
        card
        for card in tm_engine.card_catalog()
        if is_implemented(card) and not has_a_test_of(card_tests / f"test_{card['id']}.py", card["id"])
    ]


def report(untested: list[dict[str, Any]]) -> str:
    """'209 of 220 implemented cards have no scenario test:' and one line per card, or that every
    implemented card has one, and then how many cards are not implemented yet."""
    not_implemented = len(not_implemented_cards())
    total = len(tm_engine.card_catalog()) - not_implemented
    if untested:
        lines = [f"{len(untested)} of {total} implemented cards have no scenario test (tests/cards/test_<id>.py):"]
        for card in untested:
            number = printed_number(card)
            lines.append(f"  {f'{number} ' if number else ''}{card['name']} ({card['id']})")
    else:
        lines = [f"All {total} implemented cards have a scenario test."]
    if not_implemented:
        lines.append(f"{not_implemented} more cards are not implemented yet, so they need no test yet.")
    return "\n".join(lines)


def main(card_tests: Path = CARD_TESTS) -> int:
    untested = untested_cards(card_tests)
    print(report(untested))
    return 1 if untested else 0


if __name__ == "__main__":
    sys.exit(main())
