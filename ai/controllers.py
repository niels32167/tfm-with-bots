"""The registered Controllers: what the Match tool, the server and the GUI's setup screen offer, and how
Replay files name them. A Controller moves in here once it is finished enough to play against.

A human is no registered Controller: they answer through the GUI, and the server handles them itself. A
Controller that needs a trained model is available only once the model is there. Settings may follow a name, as in
"search?seconds=0.1&leaves=playouts", for a Controller registered as taking them.
"""

import importlib
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import ai.imitation
import ai.value
from ai.card_economy import CardEconomyBot
from ai.controller import Controller
from ai.flat_playout import FlatPlayout
from ai.random_bot import RandomBot


# The most Players a Game has, and how many the models' position encoding (ai.encoding) is for.
MOST_PLAYERS = 5
MODELS_PLAYERS = 2


@dataclass(frozen=True)
class Registered:
    """A registered Controller: its `label` for people, how to `make` one for one Player in one Game, and whether
    it is `available` (its model trained, if it needs one), with `missing` saying what to do if not. The setup screen
    says what it does in its `description`, and offers it in Games of at most `most_players`."""

    label: str
    make: Callable[[], Controller]
    available: Callable[[], bool] = field(default=lambda: True)
    missing: str = ""
    # The settings `make` takes by keyword, if any, named after a "?" in the Controller's name.
    settings: tuple[str, ...] = ()
    description: str = ""
    most_players: int = MOST_PLAYERS


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


def search_bot(**settings: Any) -> Controller:
    from ai.search import SearchBot

    return SearchBot(**settings)


# By the name Replay files and the Match tool use, in the order the setup screen lists them.
REGISTERED: dict[str, Registered] = {
    "random_bot": Registered("Random Bot", RandomBot, description="Picks at random. For learning the rules."),
    "flat_playout": Registered(
        "Flat Playout Bot", FlatPlayout, description="Plays every Option out at random. Easy."
    ),
    "card_economy": Registered(
        "Card Economy Bot", CardEconomyBot, description="Prices everything in MegaCredits. Medium."
    ),
    "imitation": Registered(
        "Imitation Bot",
        imitation_bot,
        available=lambda: ai.imitation.MODEL.exists(),
        missing="train its model first: uv run python -m ai.imitation.train",
        description="Plays as strong humans do. Hard.",
        most_players=MODELS_PLAYERS,
    ),
    "imitation_draft_buy": Registered(
        "Imitation Bot (Draft and buy)",
        draft_and_buy_imitation_bot,
        available=lambda: ai.imitation.DRAFT_AND_BUY_MODEL.exists(),
        missing="save ticket 13's model as .cache/models/imitation-draft-buy.pt",
        description="Chooses cards as strong humans do. Medium to hard.",
        most_players=MODELS_PLAYERS,
    ),
    "value": Registered(
        "Value Bot",
        value_bot,
        available=lambda: ai.value.MODEL.exists(),
        missing="run the self-play loop, then register its best version: uv run python -m ai.value.loop --register",
        description="Looks ahead for the best chance to win. Very hard.",
        most_players=MODELS_PLAYERS,
    ),
    "search": Registered(
        "Search Bot",
        search_bot,
        available=lambda: ai.value.MODEL.exists(),
        missing="register a Value Model first: uv run python -m ai.value.loop --register",
        description="Searches for a second before each pick. Very hard.",
        most_players=MODELS_PLAYERS,
        settings=("seconds", "samples", "tried", "share", "horizon", "exploration", "leaves", "margin"),
    ),
}


# The Controllers a human may ask what they would do, the one suggested first: the strongest that answers at once.
ADVISERS = ("value", "search", "imitation", "card_economy")


def advisers(players: int) -> list[str]:
    """The Controllers that can give advice in a Game of `players` Players now, the one suggested first."""
    return [name for name in ADVISERS if name in available() and players <= REGISTERED[name].most_players]


def available() -> list[str]:
    """The registered Controllers that can play now, in the registry's order."""
    return [name for name, registered in REGISTERED.items() if registered.available()]


def make_controller(name: str) -> Controller:
    """A new Controller for one Player in one Game: a registered one by its name, with any settings it
    takes after a "?" ("search?seconds=0.1"), or, for trying one out before it is registered, one named
    "module:attribute", such as "ai.random_bot:RandomBot".

    Raises ValueError for a name that is neither, or for settings it doesn't take.
    """
    name, given = name_and_settings(name)
    if name in REGISTERED:
        registered = REGISTERED[name]
        if not registered.available():
            raise ValueError(f"the {registered.label} isn't available: {registered.missing}")
        return registered.make(**settings_of(registered, given))
    if ":" in name:
        module_name, _, attribute = name.partition(":")
        try:
            make = getattr(importlib.import_module(module_name), attribute)
        except (ImportError, AttributeError) as error:
            raise ValueError(f"can't load the Controller {name!r}: {error}") from error
        if given:
            raise ValueError(f"a Controller named by module and attribute takes no settings: {name!r}")
        return make()
    raise ValueError(f"unknown Controller {name!r}; registered ones are {list(REGISTERED)}")


def name_and_settings(name: str) -> tuple[str, str]:
    """A Controller's name without its settings, and the settings: ("search", "seconds=5") for "search?seconds=5"."""
    name, _, settings = name.partition("?")
    return name, settings


def settings_of(registered: Registered, given: str) -> dict[str, float | str]:
    """The settings named in `given`, as in "seconds=0.1&leaves=playouts": numbers as numbers, the rest as words."""
    if not given:
        return {}
    if not registered.settings:
        raise ValueError(f"the {registered.label} takes no settings")
    settings: dict[str, float | str] = {}
    for setting in given.split("&"):
        key, equals, value = setting.partition("=")
        if not equals:
            raise ValueError(f"the setting {key!r} needs a value, as in {key}=1")
        if key not in registered.settings:
            raise ValueError(f"the {registered.label} has no setting {key!r}; it has {list(registered.settings)}")
        try:
            settings[key] = int(value)
        except ValueError:
            try:
                settings[key] = float(value)
            except ValueError:
                settings[key] = value
    return settings
