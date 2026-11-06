"""The rules notes (`docs/rules-notes.md`) list every judgment call: each note gives the call, why,
and the tests that pin it down, so those tests must exist."""

import ast
import re

from tools.card_import import PROJECT

NOTES = (PROJECT / "docs" / "rules-notes.md").read_text(encoding="utf-8")
SECTIONS = re.split(r"\n(?=### )", NOTES)[1:]


def functions_in(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def test_every_note_gives_its_call_its_reasons_and_its_tests():
    incomplete = [
        section.splitlines()[0]
        for section in SECTIONS
        if not all(part in section for part in ("**Call", "**Why:**", "**Tests:**"))
    ]

    assert incomplete == []


def test_every_test_a_note_names_exists():
    tests = {
        str(path.relative_to(PROJECT)): functions_in(path)
        for path in (PROJECT / "tests").rglob("test_*.py")
    }
    missing = []
    for path, name in re.findall(r"`(tests/[\w/]+\.py)(?:::(\w+))?`", NOTES):
        if path not in tests or (name and name not in tests[path]):
            missing.append(f"{path}::{name}")
    every_test = set().union(*tests.values())
    missing += [
        name for name in re.findall(r"`(test_\w+)`", NOTES) if name not in every_test
    ]

    assert missing == []
