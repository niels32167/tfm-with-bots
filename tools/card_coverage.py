"""Lists the catalog cards, Project Cards and Corporations alike, that have no scenario test
(spec story 97). The exit status is 1 if there are any, and the test suite fails too:

    uv run python -m tools.card_coverage

Each card's scenario tests live in `tests/cards/test_<id>.py`, such as
`tests/cards/test_black_polar_dust.py`. A card has a scenario test if that file holds a test
function that names the card by its id, asserts something, and isn't marked to be skipped or to fail.
"""

import ast
import sys
from pathlib import Path
from typing import Any

import tm_engine

from tools.card_import import PROJECT

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


def untested_cards(card_tests: Path = CARD_TESTS) -> list[dict[str, Any]]:
    """The catalog cards, in catalog order, that have no scenario test in `card_tests`."""
    return [
        card for card in tm_engine.card_catalog() if not has_a_test_of(card_tests / f"test_{card['id']}.py", card["id"])
    ]


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


def main(card_tests: Path = CARD_TESTS) -> int:
    untested = untested_cards(card_tests)
    print(report(untested))
    return 1 if untested else 0


if __name__ == "__main__":
    sys.exit(main())
