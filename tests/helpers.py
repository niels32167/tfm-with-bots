"""Helpers that let scenario tests read like play.

A test sets up a Scenario (or a seed), picks Options the way a Player would, and
checks only what an outsider can see: the Options offered, the Player View, the
game log and the scores. Tests never look inside the engine.

    game = scenario(player(megacredits=20), player(), temperature=-2)
    pick(game, "Asteroid")
    assert player_board(game, 0)["terraform_rating"] == 21
"""

import json
from typing import Any

import tm_engine

# A generous guard so a Game that never ends fails the test instead of hanging it.
MAX_PICKS = 10_000

# The Areas on Mars as printed on the Tharsis board: rows A to J (there is no row I) with
# 5 to 9 Areas each, 12 of them reserved for Oceans and E3 for the Noctis City card.
ROW_LENGTHS = {"A": 5, "B": 6, "C": 7, "D": 8, "E": 9, "F": 8, "G": 7, "H": 6, "J": 5}
AREAS_ON_MARS = [f"{row}{position}" for row, length in ROW_LENGTHS.items() for position in range(1, length + 1)]
OCEAN_AREAS = ["A2", "A4", "A5", "B6", "D8", "E4", "E5", "E6", "F6", "F7", "F8", "J5"]
NOCTIS_CITY = "E3"
# The Areas reserved for a card's City, on Mars and off it, by the card's id.
RESERVED_FOR_CARDS = {
    NOCTIS_CITY: "noctis_city",
    "phobos_space_haven": "phobos_space_haven",
    "ganymede_colony": "ganymede_colony",
}
# The cards printed with a Card Resource to hold, and its kind.
CARDS_HOLDING_CARD_RESOURCES = {
    "search_for_life": "science",
    "regolith_eaters": "microbe",
    "ghg_producing_bacteria": "microbe",
    "ants": "microbe",
    "tardigrades": "microbe",
    "physics_complex": "science",
    "decomposers": "microbe",
    "nitrite_reducing_bacteria": "microbe",
    "olympus_conference": "science",
}
# Every Area on Mars that is reserved for nothing, in board order.
LAND_AREAS = [name for name in AREAS_ON_MARS if name not in OCEAN_AREAS and name != NOCTIS_CITY]


def _row_and_half_column(area_id: str) -> tuple[int, int]:
    """Where an Area on Mars is: its row from the top, and how many half-Areas it is from the
    left edge of the widest row, since every row is centred under that one."""
    row, position = area_id[0], int(area_id[1:])
    widest = max(ROW_LENGTHS.values())
    return list(ROW_LENGTHS).index(row), 2 * (position - 1) + widest - ROW_LENGTHS[row]


def _next_to_each_other(one: str, other: str) -> bool:
    """Neighbours in the same row are one Area (two half-Areas) apart; in the rows above and
    below, they are half an Area to either side."""
    (row, column), (other_row, other_column) = _row_and_half_column(one), _row_and_half_column(other)
    return (abs(row - other_row), abs(column - other_column)) in {(0, 2), (1, 1)}


# The Areas next to each Area on Mars, as printed. The Areas off Mars have none.
ADJACENT_AREAS = {
    area_id: [other for other in AREAS_ON_MARS if _next_to_each_other(area_id, other)] for area_id in AREAS_ON_MARS
}


def terraformed_mars(*, tiles: list[dict[str, Any]] = (), **fields: Any) -> dict[str, Any]:
    """Scenario fields with all three Global Parameters at their maximum: +8 °C, 14 % Oxygen
    and 9 Oceans (on the first 9 Ocean Areas), plus any other `tiles` and `fields`."""
    oceans = [ocean(name) for name in OCEAN_AREAS[:9]]
    return {"temperature": 8, "oxygen": 14, "tiles": [*oceans, *tiles], **fields}


def scenario(*players: dict[str, Any], **fields: Any) -> tm_engine.Game:
    """Start a Game from a Scenario. Anything left out takes the normal defaults.

    Give one `player(...)` per Player; with none, the Game has two default Players.
    Keyword arguments describe the rest, e.g. `generation=3, temperature=-10`.
    """
    description = dict(fields)
    if players:
        description["players"] = list(players)
    return tm_engine.Game.from_scenario(description)


# Every Project Card by catalog id, in number order (#001 first).
PROJECT_CARDS = [card["id"] for card in tm_engine.card_catalog() if card["type"] != "corporation"]

# Every card's printed name, by catalog id.
CARD_NAMES = {card["id"]: card["name"] for card in tm_engine.card_catalog()}


def has_printed_production_box(card: dict[str, Any]) -> bool:
    """Whether a card of the card catalog is printed with a production box, the brown box of
    Production changes, as its face draws it."""
    return "production-box" in json.dumps(card["face"])

# The Tags counted on a player board, in the card list's order: every Tag but the Event Tag,
# since no Tag on a played Event counts.
TAGS_THAT_COUNT = ("building", "space", "power", "science", "jovian", "earth", "plant", "microbe", "animal", "city")

# The six Resources, as the Scenario, the Player View and Production name them.
RESOURCES = ("megacredits", "steel", "titanium", "plants", "energy", "heat")


def player(**fields: Any) -> dict[str, Any]:
    """One Player's part of a Scenario.

    For example `player(megacredits=30, plants=8, terraform_rating=25, production={"heat": 2},
    hand=["mine"], played_cards=["trees"])`, naming cards by their catalog id.
    Resources are given by name and go into the Scenario's "resources"; the rest is passed as is.
    """
    given = {name: fields.pop(name) for name in RESOURCES if name in fields}
    return {"resources": given, **fields} if given else fields


def ocean(area: str) -> dict[str, Any]:
    """An Ocean Tile for a Scenario's `tiles`, e.g. `scenario(tiles=[ocean("A2")])`. Oceans belong to nobody."""
    return {"area": area, "tile": "ocean"}


def greenery(area: str, owner: int) -> dict[str, Any]:
    """A Greenery Tile owned by Player `owner` (indexed from 0), for a Scenario's `tiles`."""
    return {"area": area, "tile": "greenery", "owner": owner}


def city(area: str, owner: int) -> dict[str, Any]:
    """A City Tile owned by Player `owner` (indexed from 0), for a Scenario's `tiles`."""
    return {"area": area, "tile": "city", "owner": owner}


def special(area: str, card: str, owner: int) -> dict[str, Any]:
    """The special Tile of `card` (a catalog id) owned by Player `owner`, for a Scenario's `tiles`,
    e.g. `special("C4", "nuclear_zone", owner=0)`. Capital's is a City."""
    tile = "city" if card == "capital" else "special"
    return {"area": area, "tile": tile, "card": card, "owner": owner}


def claimed(milestone: str, by: int) -> dict[str, Any]:
    """A Milestone claimed by Player `by` (indexed from 0), for a Scenario's `milestones`,
    e.g. `scenario(milestones=[claimed("mayor", by=1)])`."""
    return {"milestone": milestone, "claimed_by": by}


def funded(award: str, by: int) -> dict[str, Any]:
    """An Award funded by Player `by` (indexed from 0), for a Scenario's `awards`,
    e.g. `scenario(awards=[funded("landlord", by=0)])`."""
    return {"award": award, "funded_by": by}


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
    game.pick(index_of(game, label, **details))


def index_of(game: tm_engine.Game, label: str | None = None, **details: Any) -> int:
    """The index of the one Option matching `label` and `details`; see `pick` for how matching works."""
    found = _matching(game, label, details)
    if len(found) != 1:
        wanted = " ".join(filter(None, [repr(label) if label else "", str(details) if details else ""]))
        raise AssertionError(
            f"expected exactly one Option matching {wanted}, found {len(found)}; offered: {labels(game)}"
        )
    return found[0]["index"]


def end_the_action_phase(game: tm_engine.Game) -> None:
    """Every Player who is still in passes. The Production phase follows, then the next Generation
    begins with its Research phase; once Mars is terraformed, the final Greenery conversion or the
    end of the Game follows instead."""
    generation = game.player_view(0)["generation"]
    for _ in range(MAX_PICKS):
        view = game.player_view(0)
        if view["phase"] != "action" or view["generation"] != generation:
            return
        pick(game, "Pass")
    raise AssertionError(f"Generation {generation}'s Action phase had not ended after {MAX_PICKS} picks")


def buy(game: tm_engine.Game, *cards: str) -> None:
    """The Player deciding, in the setup or a Research phase, buys `cards` and is done."""
    for card in cards:
        pick(game, type="buy_card", card=card)
    pick(game, "Done")


def keep_the_first_cards_offered(game: tm_engine.Game) -> list[int]:
    """In the Draft, every Player keeps the first card offered until every card is kept.
    Returns who picked, in order."""
    deciding = []
    for _ in range(MAX_PICKS):
        if game.decision is None or game.decision["kind"] != "draft":
            return deciding
        deciding.append(game.decision["player"])
        game.pick(0)
    raise AssertionError(f"the Draft was not over after {MAX_PICKS} picks")


def skip_buying(game: tm_engine.Game) -> None:
    """In the setup or a Research phase, every Player still to decide is done without buying."""
    for _ in range(MAX_PICKS):
        if game.decision is None or game.decision["kind"] != "buy_cards":
            return
        pick(game, "Done")
    raise AssertionError(f"buying had not ended after {MAX_PICKS} picks")


def end_the_generation(game: tm_engine.Game) -> None:
    """Every Player who is still in passes, which ends the Generation: the next one begins, and
    in its Research phase each Player keeps the first cards offered in the Draft (if it is on)
    and buys none. Once Mars is terraformed, the final Greenery conversion or the end of the Game
    follows instead."""
    end_the_action_phase(game)
    keep_the_first_cards_offered(game)
    skip_buying(game)


def final_scores(game: tm_engine.Game) -> list[dict[str, Any]]:
    """Each Player's final score, once the Generation under way ends and with it the Game,
    as it does on a `terraformed_mars()`. Players with 8 plants convert none of them."""
    end_the_generation(game)
    for _ in range(MAX_PICKS):
        if game.is_over:
            return game.scores
        pick(game, "Done")
    raise AssertionError(f"the Game was not over after {MAX_PICKS} picks")


def play_randomly(game: tm_engine.Game, seed: int, picks: int | None = None) -> None:
    """Play on with the engine's Random Bot for every Player: `picks` random Options, or until
    the Game is over. A Game still going after MAX_PICKS fails the test instead of hanging it.

    The same `seed` always picks the same way from the same position.
    """
    game.play_randomly(seed=seed, picks=MAX_PICKS if picks is None else picks)
    if picks is None and not game.is_over:
        raise AssertionError(f"the Game was not over after {MAX_PICKS} picks")


def everything_about(game: tm_engine.Game) -> dict[str, Any]:
    """All an outsider can see of a Game, for checking that two Games are identical."""
    return {"full_view": game.full_view(), "decision": game.decision, "log": game.log}


def player_board(game: tm_engine.Game, player: int) -> dict[str, Any]:
    """What everyone can see of a Player: Resources, Production, Terraform Rating, whether they passed."""
    return game.player_view(player)["players"][player]


def resources(game: tm_engine.Game, player: int) -> dict[str, int]:
    """A Player's six Resources, such as `resources(game, 0)["megacredits"]`."""
    return player_board(game, player)["resources"]


def production(game: tm_engine.Game, player: int) -> dict[str, int]:
    """A Player's Production of each of the six Resources."""
    return player_board(game, player)["production"]


def hand(game: tm_engine.Game, player: int) -> list[str]:
    """The cards in a Player's hand, by catalog id, as that Player sees them."""
    return player_board(game, player)["hand"]


def buying(game: tm_engine.Game, player: int) -> dict[str, list[str]] | None:
    """What a Player is buying from, as that Player sees it, in the setup or a Research phase:
    `{"dealt": [...], "bought": [...]}` by catalog id, the cards bought among those dealt.
    None outside those phases."""
    return player_board(game, player)["buying"]


def drafting(game: tm_engine.Game, player: int) -> dict[str, Any] | None:
    """What a Player is drafting, as that Player sees it, from Generation 2 with the Draft on:
    `{"picking_from": [...], "kept": [...], "passing_to": int}`, the cards by catalog id: those
    they keep one of and pass the rest on, and those kept so far. None outside the Draft."""
    return player_board(game, player)["drafting"]


def keeping(game: tm_engine.Game, player: int) -> dict[str, Any] | None:
    """What a Player is looking at to keep some of, as that Player sees it, while they play
    Business Contacts or Invention Contest: `{"card": ..., "looking_at": [...], "kept": [...],
    "keep": int}`, the card they play, then by catalog id the cards they may still keep and those
    kept so far, and how many more they keep. The rest are discarded. None otherwise."""
    return player_board(game, player)["keeping"]


def played_cards(game: tm_engine.Game, player: int) -> list[str]:
    """The cards a Player has played, by catalog id, as everyone sees them."""
    return player_board(game, player)["played_cards"]


def card_resources(game: tm_engine.Game, player: int) -> dict[str, int]:
    """The Card Resources on each of a Player's played cards that can hold some, by catalog id, as
    everyone sees them."""
    return player_board(game, player)["card_resources"]


def area(game: tm_engine.Game, area_id: str) -> dict[str, Any]:
    """One Area of the board as everyone sees it: "E3", or "phobos_space_haven" off Mars."""
    found = [entry for entry in game.full_view()["board"] if entry["area"] == area_id]
    assert len(found) == 1, f"there is no Area {area_id!r} on the board"
    return found[0]


def milestone(game: tm_engine.Game, name: str) -> dict[str, Any]:
    """One Milestone as everyone sees it, such as `milestone(game, "mayor")`."""
    found = [entry for entry in game.full_view()["milestones"] if entry["milestone"] == name]
    assert len(found) == 1, f"there is no Milestone {name!r}"
    return found[0]


def award(game: tm_engine.Game, name: str) -> dict[str, Any]:
    """One Award as everyone sees it, such as `award(game, "landlord")`."""
    found = [entry for entry in game.full_view()["awards"] if entry["award"] == name]
    assert len(found) == 1, f"there is no Award {name!r}"
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
