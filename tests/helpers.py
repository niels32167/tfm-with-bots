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

# The Areas on Mars as printed on the Tharsis board: rows A to J (there is no row I) with
# 5 to 9 Areas each, 12 of them reserved for Oceans and E3 for the Noctis City card.
ROW_LENGTHS = {"A": 5, "B": 6, "C": 7, "D": 8, "E": 9, "F": 8, "G": 7, "H": 6, "J": 5}
OCEAN_AREAS = ["A2", "A4", "A5", "B6", "D8", "E4", "E5", "E6", "F6", "F7", "F8", "J5"]
NOCTIS_CITY = "E3"
# Every Area on Mars that is reserved for nothing, in board order.
LAND_AREAS = [
    name
    for name in (f"{row}{position}" for row, length in ROW_LENGTHS.items() for position in range(1, length + 1))
    if name not in OCEAN_AREAS and name != NOCTIS_CITY
]


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

    For example `player(megacredits=30, plants=8, terraform_rating=25, production={"megacredits": 2})`.
    """
    return fields


def ocean(area: str) -> dict[str, Any]:
    """An Ocean Tile for a Scenario's `tiles`, e.g. `scenario(tiles=[ocean("A2")])`. Oceans belong to nobody."""
    return {"area": area, "tile": "ocean"}


def greenery(area: str, owner: int) -> dict[str, Any]:
    """A Greenery Tile owned by Player `owner` (indexed from 0), for a Scenario's `tiles`."""
    return {"area": area, "tile": "greenery", "owner": owner}


def city(area: str, owner: int) -> dict[str, Any]:
    """A City Tile owned by Player `owner` (indexed from 0), for a Scenario's `tiles`."""
    return {"area": area, "tile": "city", "owner": owner}


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


def area(game: tm_engine.Game, area_id: str) -> dict[str, Any]:
    """One Area of the board as everyone sees it: "E3", or "phobos_space_haven" off Mars."""
    found = [entry for entry in game.full_view()["board"] if entry["area"] == area_id]
    assert len(found) == 1, f"there is no Area {area_id!r} on the board"
    return found[0]


def areas_on_mars(game: tm_engine.Game) -> list[dict[str, Any]]:
    """Every Area on Mars, row by row from the top and each row from the left."""
    return [entry for entry in game.full_view()["board"] if entry["row"] is not None]


def areas_offered(game: tm_engine.Game) -> list[str]:
    """The Areas the current choose-an-Area Decision offers, in board order."""
    return [option["details"]["area"] for option in options(game)]



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
