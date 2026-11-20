"""The registered Controllers: what the Match tool, the server and the GUI's setup screen offer, and how
Replay files name them. A Controller moves in here once it is finished enough to play against.

A human is no registered Controller: they answer through the GUI, and the server handles them itself. A
Controller that needs a trained model is available only once the model is there.
"""

import importlib
from collections.abc import Callable
from dataclasses import dataclass, field

import ai.imitation
import ai.value
from ai.card_economy import CardEconomyBot
from ai.controller import Controller
from ai.flat_playout import FlatPlayout
from ai.random_bot import RandomBot


@dataclass(frozen=True)
class Registered:
    """A registered Controller: its `label` for people, how to `make` one for one Player in one Game, and whether
    it is `available` (its model trained, if it needs one), with `missing` saying what to do if not."""

    label: str
    make: Callable[[], Controller]
    available: Callable[[], bool] = field(default=lambda: True)
    missing: str = ""


def imitation_bot() -> Controller:
    # Imported when asked for, so that only processes playing it load PyTorch.
    from ai.imitation.bot import ImitationBot

    return ImitationBot()


def draft_and_buy_imitation_bot() -> Controller:
    from ai.imitation.bot import DRAFT_AND_BUY, ImitationBot

    return ImitationBot(ai.imitation.DRAFT_AND_BUY_MODEL, imitated=DRAFT_AND_BUY)


def value_bot() -> Controller:
    from ai.value.bot import ValueBot

    return ValueBot()


# By the name Replay files and the Match tool use, in the order the setup screen lists them.
REGISTERED: dict[str, Registered] = {
    "random_bot": Registered("Random Bot", RandomBot),
    "flat_playout": Registered("Flat Playout Bot", FlatPlayout),
    "card_economy": Registered("Card Economy Bot", CardEconomyBot),
    "imitation": Registered(
        "Imitation Bot",
        imitation_bot,
        available=lambda: ai.imitation.MODEL.exists(),
        missing="train its model first: uv run python -m ai.imitation.train",
    ),
    "imitation_draft_buy": Registered(
        "Imitation Bot (Draft and buy)",
        draft_and_buy_imitation_bot,
        available=lambda: ai.imitation.DRAFT_AND_BUY_MODEL.exists(),
        missing="save ticket 13's model as .cache/models/imitation-draft-buy.pt",
    ),
    "value": Registered(
        "Value Bot",
        value_bot,
        available=lambda: ai.value.MODEL.exists(),
        missing="run the self-play loop, then register its best version: uv run python -m ai.value.loop --register",
    ),
}


def available() -> list[str]:
    """The registered Controllers that can play now, in the registry's order."""
    return [name for name, registered in REGISTERED.items() if registered.available()]


def make_controller(name: str) -> Controller:
    """A new Controller for one Player in one Game: a registered one by its name, or, for trying one
    out before it is registered, one named "module:attribute", such as "ai.random_bot:RandomBot".

    Raises ValueError for a name that is neither.
    """
    if name in REGISTERED:
        registered = REGISTERED[name]
        if not registered.available():
            raise ValueError(f"the {registered.label} isn't available: {registered.missing}")
        return registered.make()
    if ":" in name:
        module_name, _, attribute = name.partition(":")
        try:
            make = getattr(importlib.import_module(module_name), attribute)
        except (ImportError, AttributeError) as error:
            raise ValueError(f"can't load the Controller {name!r}: {error}") from error
        return make()
    raise ValueError(f"unknown Controller {name!r}; registered ones are {list(REGISTERED)}")
