"""Helpers that let scenario tests read like play.

A test sets up a Scenario (or a seed), picks Options the way a Player would, and
checks only what an outsider can see: the Options offered, the Player View, the
game log and the scores. Tests never look inside the engine.

    game = scenario(player(megacredits=20), player(), temperature=-2)
    pick(game, "Asteroid")
    assert player_board(game, 0)["terraform_rating"] == 21
"""

import random
from typing import Any

import tm_engine

# A generous guard so a Game that never ends fails the test instead of hanging it.
MAX_PICKS = 10_000


def scenario(*players: dict[str, Any], **fields: Any) -> tm_engine.Game:
    """Start a Game from a Scenario. Anything left out takes the normal defaults.

    Give one `player(...)` per Player; with none, the Game has two default Players.
    Keyword arguments describe the rest, e.g. `generation=3, temperature=-10`.
    """
    description = dict(fields)
    if players:
        description["players"] = list(players)
    return tm_engine.Game.from_scenario(description)


def player(**fields: Any) -> dict[str, Any]:
    """One Player's part of a Scenario.

    For example `player(megacredits=30, terraform_rating=25, production={"megacredits": 2})`.
    """
    return fields


def options(game: tm_engine.Game) -> list[dict[str, Any]]:
    """The Options of the Decision the Game is waiting on."""
    decision = game.decision
    assert decision is not None, "the Game is over, so no Decision is waiting"
    return decision["options"]


def labels(game: tm_engine.Game) -> list[str]:
    """The labels of the current Decision's Options, in order."""
    return [option["label"] for option in options(game)]


def offered(game: tm_engine.Game, label: str | None = None, **details: Any) -> bool:
    """Whether the current Decision offers an Option matching `label` and `details`.

    See `pick` for how matching works.
    """
    return bool(_matching(game, label, details))


def pick(game: tm_engine.Game, label: str | None = None, **details: Any) -> None:
    """Pick the one Option whose label contains `label` and whose details include `details`.

    The label match ignores case, so `pick(game, "asteroid")` works. Details are
    matched by equality, e.g. `pick(game, type="pass")`. Fails the test unless
    exactly one Option matches.
    """
    found = _matching(game, label, details)
    if len(found) != 1:
        wanted = " ".join(filter(None, [repr(label) if label else "", str(details) if details else ""]))
        raise AssertionError(
            f"expected exactly one Option matching {wanted}, found {len(found)}; offered: {labels(game)}"
        )
    game.pick(found[0]["index"])


def end_the_generation(game: tm_engine.Game) -> None:
    """Every Player who is still in passes, which ends the Generation (and maybe the Game)."""
    generation = game.player_view(0)["generation"]
    while not game.is_over and game.player_view(0)["generation"] == generation:
        pick(game, "Pass")


def play_randomly(game: tm_engine.Game, seed: int, picks: int | None = None) -> None:
    """Pick random Options the way a Random Bot would: `picks` of them, or until the Game is over.

    The same `seed` always picks the same way from the same position.
    """
    random_numbers = random.Random(seed)
    for _ in range(MAX_PICKS if picks is None else picks):
        if game.is_over:
            return
        game.pick(random_numbers.randrange(len(options(game))))
    if picks is None:
        raise AssertionError(f"the Game was not over after {MAX_PICKS} picks")


def everything_about(game: tm_engine.Game) -> dict[str, Any]:
    """All an outsider can see of a Game, for checking that two Games are identical."""
    return {"full_view": game.full_view(), "decision": game.decision, "log": game.log}


def player_board(game: tm_engine.Game, player: int) -> dict[str, Any]:
    """What everyone can see of a Player: Resources, Production, Terraform Rating, whether they passed."""
    return game.player_view(player)["players"][player]


def matching_options(offered: list[dict[str, Any]], label: str | None = None, **details: Any) -> list[dict[str, Any]]:
    """The Options in `offered` whose label contains `label` (ignoring case) and whose details include `details`."""
    return [
        option
        for option in offered
        if (label is None or label.lower() in option["label"].lower())
        and all(option["details"].get(key) == value for key, value in details.items())
    ]


def _matching(game: tm_engine.Game, label: str | None, details: dict[str, Any]) -> list[dict[str, Any]]:
    return matching_options(options(game), label, **details)
