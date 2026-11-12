"""The registered Controllers: what the Match tool, the server and the GUI's setup screen offer, and how
Replay files name them. A Controller moves in here once it is finished enough to play against.

A human is no registered Controller: they answer through the GUI, and the server handles them itself.
"""

import importlib
from collections.abc import Callable
from dataclasses import dataclass

from ai.controller import Controller
from ai.flat_playout import FlatPlayout
from ai.random_bot import RandomBot


@dataclass(frozen=True)
class Registered:
    """A registered Controller: its `label` for people, and how to `make` one for one Player in one Game."""

    label: str
    make: Callable[[], Controller]


# By the name Replay files and the Match tool use, in the order the setup screen lists them.
REGISTERED: dict[str, Registered] = {
    "random_bot": Registered("Random Bot", RandomBot),
    "flat_playout": Registered("Flat Playout Bot", FlatPlayout),
}


def make_controller(name: str) -> Controller:
    """A new Controller for one Player in one Game: a registered one by its name, or, for trying one
    out before it is registered, one named "module:attribute", such as "ai.random_bot:RandomBot".

    Raises ValueError for a name that is neither.
    """
    if name in REGISTERED:
        return REGISTERED[name].make()
    if ":" in name:
        module_name, _, attribute = name.partition(":")
        try:
            make = getattr(importlib.import_module(module_name), attribute)
        except (ImportError, AttributeError) as error:
            raise ValueError(f"can't load the Controller {name!r}: {error}") from error
        return make()
    raise ValueError(f"unknown Controller {name!r}; registered ones are {list(REGISTERED)}")
