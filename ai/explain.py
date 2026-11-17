"""Why a Controller picked what it picked: the Prices of the top Options and what made them, for the
Card Economy Bot and any later Controller that can explain itself (ticket 11).

    uv run python -m ai.explain saved-game.json --step 120
    uv run python -m ai.explain match-failures/some-game.json --step 120 --controller card_economy --top 8

The file is a Replay file, as the GUI saves it, or a bare Replay. The Decision explained is the one
waiting after `--step` picks (by default the last), as the Player answering it saw it; the Controller
is the one the file names for that Player, or --controller. Its random source is the server's for that
step, so a Game played in the GUI is explained as it was played. A Match seeds Controllers otherwise,
so a Game from a Match may be explained from another Sampled Position than it was played on.

The dev panel shows the same explanation beside each step a Controller answered.
"""

import argparse
import json
import random
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from ai.controller import Controller, Handle, handle_at
from ai.controllers import REGISTERED, make_controller

# How many of an Option's Prices that changed are given as reasons.
REASONS = 6


def server_random(seed: int, step: int) -> random.Random:
    """The random source the server gives a Controller answering the Decision after `step` picks."""
    return random.Random(f"{seed}/{step}")


def explanation(controller: Controller, handle: Handle, name: str) -> dict[str, Any] | None:
    """`controller`'s explanation of its pick from `handle`, as plain data, or None if it can't explain
    itself. Every Option is listed, best first, with its value and its Prices that changed most."""
    explain = getattr(controller, "explain", None)
    if explain is None:
        return None
    explained = explain(handle)
    return {
        "controller": REGISTERED[name].label if name in REGISTERED else name,
        "player": explained.player,
        "kind": explained.kind,
        "generations_left": explained.generations_left,
        "options": [
            {
                "index": option.index,
                "label": option.label,
                "price": option.price,
                "reasons": [
                    [part, change]
                    for part, change in sorted(option.parts.items(), key=lambda part: -abs(part[1]))[:REASONS]
                    if abs(change) >= 0.05
                ],
            }
            for option in explained.options
        ],
    }


def text(explained: dict[str, Any], top: int) -> str:
    """An explanation as lines to read: the Decision, then the `top` Options with their reasons."""
    lines = [
        (
            f"Player {explained['player'] + 1}, {explained['kind']} Decision, {len(explained['options'])} Options; "
            f"about {explained['generations_left']:.1f} Generations left, held for every Option."
        )
    ]
    for rank, option in enumerate(explained["options"][:top], 1):
        lines.append(f"{rank}. {option['label']}: {option['price']:+.1f}")
        if option["reasons"]:
            lines.append("   " + ", ".join(f"{part} {change:+.1f}" for part, change in option["reasons"]))
    return "\n".join(lines)


def seed_of(replay: dict[str, Any]) -> int:
    start = replay["start"]
    return (start.get("settings") or start.get("scenario"))["seed"]


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", type=Path, help="a Replay file, or a bare Replay")
    parser.add_argument("--step", type=int, help="the picks made before the Decision (by default all)")
    parser.add_argument("--controller", help="a registered Controller's name (by default the file's)")
    parser.add_argument("--top", type=int, default=5, help="how many Options to show (5)")
    options = parser.parse_args(arguments)

    file = json.loads(options.file.read_text())
    replay = file.get("replay", file)
    step = len(replay["picks"]) if options.step is None else options.step
    if not 0 <= step <= len(replay["picks"]):
        parser.error(f"--step must be from 0 to {len(replay['picks'])}")
    handle = handle_at(replay, step, server_random(seed_of(replay), step))
    named = file.get("controllers", [None] * (handle.player + 1))[handle.player]
    name = options.controller or (named if named in REGISTERED else "card_economy")
    explained = explanation(make_controller(name), handle, name)
    if explained is None:
        print(f"The {REGISTERED[name].label} can't explain its picks.", file=sys.stderr)
        return 1
    print(f"{explained['controller']}, step {step}:")
    print(text(explained, options.top))
    if step < len(replay["picks"]):
        print(f"Picked in the Replay: {handle.decision['options'][replay['picks'][step]]['label']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
