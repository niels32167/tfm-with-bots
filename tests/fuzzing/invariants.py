"""What must hold in every Game. The fuzzer checks these after every Decision and at the
end of every Game (ticket 06).

Each check reads only what an outsider can see, the full view and the Decision the Game
is waiting on, and yields one line for each thing that is wrong. The printed rules and
board facts are written out here and in tests/helpers.py rather than read from the
engine, so a mistake in the engine can't hide behind the same mistake in its checks.
Invariants for rules that don't exist yet join these lists when their ticket lands.
"""

from collections.abc import Callable, Iterator
from typing import Any

from tests.helpers import ADJACENT_AREAS, LAND_AREAS, OCEAN_AREAS, RESOURCES

type View = dict[str, Any]
type Decision = dict[str, Any]
# A check is shown the full view and the Decision the Game is waiting on (None once it is
# over), and yields what is wrong.
type Check = Callable[[View, Decision | None], Iterator[str]]

MIN_TEMPERATURE, MAX_TEMPERATURE, TEMPERATURE_STEP = -30, 8, 2
MAX_OXYGEN = 14
MAX_OCEANS = 9
MIN_MEGACREDIT_PRODUCTION = -5
MILESTONE_COST = 8
AWARD_COSTS = (8, 14, 20)
MAX_MILESTONES_CLAIMED = 3
MILESTONE_VICTORY_POINTS = 5

# How the game log names each Resource: an amount of it, and its Production.
AMOUNT_NAMES = {name: name for name in RESOURCES} | {"megacredits": "MegaCredits"}
PRODUCTION_NAMES = {name: name for name in RESOURCES} | {"megacredits": "MegaCredit", "plants": "plant"}
TILE_NAMES = {"ocean": "Ocean", "greenery": "Greenery", "city": "City"}
# The six parts of a final score, which add up to its total.
SCORE_PARTS = ("terraform_rating", "milestones", "awards", "greeneries", "cities", "cards")


def no_negative_resources(view: View, decision: Decision | None) -> Iterator[str]:
    for player_board in view["players"]:
        for resource in RESOURCES:
            amount = player_board["resources"][resource]
            if amount < 0:
                yield f"{player_board['name']} has {amount} {AMOUNT_NAMES[resource]}"


def production_within_its_limits(view: View, decision: Decision | None) -> Iterator[str]:
    """MegaCredit Production stays at -5 or above, every other Production at 0 or above."""
    for player_board in view["players"]:
        for resource in RESOURCES:
            limit = MIN_MEGACREDIT_PRODUCTION if resource == "megacredits" else 0
            amount = player_board["production"][resource]
            if amount < limit:
                name = PRODUCTION_NAMES[resource]
                yield f"{player_board['name']}'s {name} Production is {amount}, below its limit of {limit}"


def global_parameters_within_range(view: View, decision: Decision | None) -> Iterator[str]:
    temperature, oxygen, oceans = view["temperature"], view["oxygen"], view["oceans"]
    on_step = (temperature - MIN_TEMPERATURE) % TEMPERATURE_STEP == 0
    if not (MIN_TEMPERATURE <= temperature <= MAX_TEMPERATURE and on_step):
        track = f"the track from {MIN_TEMPERATURE} to {MAX_TEMPERATURE} °C"
        yield f"Temperature is {temperature} °C, not a step on {track}"
    if not 0 <= oxygen <= MAX_OXYGEN:
        yield f"Oxygen is {oxygen} %, not on the track from 0 to {MAX_OXYGEN} %"
    if not 0 <= oceans <= MAX_OCEANS:
        yield f"Oceans are at {oceans}, not on the track from 0 to {MAX_OCEANS}"
    ocean_tiles = sum(1 for tile in tiles_on_the_board(view).values() if tile["type"] == "ocean")
    if oceans != ocean_tiles:
        yield f"Oceans are at {oceans}, but the board has {counted(ocean_tiles, 'Ocean Tile')}"


def tiles_only_on_legal_areas(view: View, decision: Decision | None) -> Iterator[str]:
    """Oceans lie on Areas reserved for Oceans and belong to nobody. Greeneries and Cities
    lie on Areas of Mars reserved for nothing, belong to a Player, and no two Cities touch."""
    tiles = tiles_on_the_board(view)
    for area_id, tile in tiles.items():
        name, owner = TILE_NAMES[tile["type"]], tile["owner"]
        if tile["type"] == "ocean":
            if area_id not in OCEAN_AREAS:
                yield f"the Ocean on {area_id} is not on an Area reserved for Oceans"
            if owner is not None:
                yield f"the Ocean on {area_id} belongs to Player {owner + 1}, but Oceans belong to nobody"
            continue
        if area_id not in LAND_AREAS:
            yield f"the {name} on {area_id} is not on an Area of Mars that is reserved for nothing"
        if owner not in range(len(view["players"])):
            yield f"the {name} on {area_id} belongs to no Player in the Game"
        if tile["type"] == "city":
            for next_area in ADJACENT_AREAS.get(area_id, []):
                if next_area > area_id and tiles.get(next_area, {}).get("type") == "city":
                    yield f"the Cities on {area_id} and {next_area} are next to each other"


def only_legal_areas_offered(view: View, decision: Decision | None) -> Iterator[str]:
    """A choose-an-Area Decision offers exactly the Areas where its Tile may go."""
    if decision is None or decision["kind"] != "area" or not decision["options"]:
        return
    tile = decision["options"][0]["details"]["tile"]
    offered = {option["details"]["area"] for option in decision["options"]}
    legal = legal_areas(view, tile, decision["player"])
    article_and_name = f"{'an' if tile == 'ocean' else 'a'} {TILE_NAMES[tile]}"
    for area_id in sorted(offered - legal):
        yield f"the Area Decision for {article_and_name} offers {area_id}, where it may not go"
    for area_id in sorted(legal - offered):
        yield f"the Area Decision for {article_and_name} leaves out {area_id}, where it may go"


def legal_areas(view: View, tile: str, player: int) -> set[str]:
    """Where `player` may place `tile`: an Ocean on a free Area reserved for Oceans; a City on
    free land on Mars next to no City; a Greenery on free land next to one of its owner's
    Tiles, or on any free land if there is no such Area."""
    tiles = tiles_on_the_board(view)
    if tile == "ocean":
        return {area_id for area_id in OCEAN_AREAS if area_id not in tiles}
    free_land = {area_id for area_id in LAND_AREAS if area_id not in tiles}

    def next_to(area_id: str, wanted: Callable[[dict[str, Any]], bool]) -> bool:
        return any(wanted(tiles[next_area]) for next_area in ADJACENT_AREAS[area_id] if next_area in tiles)

    if tile == "city":
        return {area_id for area_id in free_land if not next_to(area_id, lambda each: each["type"] == "city")}
    next_to_own = {area_id for area_id in free_land if next_to(area_id, lambda each: each["owner"] == player)}
    return next_to_own or free_land


def at_most_three_milestones_and_awards(view: View, decision: Decision | None) -> Iterator[str]:
    """At most three Milestones are claimed and three Awards funded, and the prices of the
    next ones follow: 8 for a Milestone, and 8, 14 and 20 for the Awards."""
    claimed = sum(1 for milestone in view["milestones"] if milestone["claimed_by"] is not None)
    funded = sum(1 for award in view["awards"] if award["funded_by"] is not None)
    if claimed > MAX_MILESTONES_CLAIMED:
        yield f"{claimed} Milestones are claimed, but at most {MAX_MILESTONES_CLAIMED} may be"
    if funded > len(AWARD_COSTS):
        yield f"{funded} Awards are funded, but at most {len(AWARD_COSTS)} may be"
    milestone_cost = MILESTONE_COST if claimed < MAX_MILESTONES_CLAIMED else None
    if view["milestone_cost"] != milestone_cost:
        claimed_so_far = counted(claimed, "Milestone")
        yield f"with {claimed_so_far} claimed, milestone_cost is {view['milestone_cost']}, not {milestone_cost}"
    award_cost = AWARD_COSTS[funded] if funded < len(AWARD_COSTS) else None
    if view["award_cost"] != award_cost:
        yield f"with {counted(funded, 'Award')} funded, award_cost is {view['award_cost']}, not {award_cost}"


def every_decision_has_an_option(view: View, decision: Decision | None) -> Iterator[str]:
    """A Game is either over or waiting on one Decision, which offers at least one Option."""
    over = view["phase"] == "over"
    if decision is None and not over:
        yield "the Game is not over, but waits on no Decision"
    if decision is not None and over:
        yield "the Game is over, but still waits on a Decision"
    if decision is not None and not decision["options"]:
        yield f"Player {decision['player'] + 1}'s {decision['kind']} Decision offers no Option"


def score_breakdown_adds_up(view: View, decision: Decision | None) -> Iterator[str]:
    """Each score's six parts add up to its total, and the parts the board shows agree with
    it: Terraform Rating, Milestones, Greeneries, Cities, and MegaCredits (the tiebreak).
    Ranks follow Victory Points, then MegaCredits."""
    scores = view["scores"]
    if scores is None:
        yield "the Game is over, but has no scores"
        return
    for score, player_board in zip(scores, view["players"], strict=True):
        name = player_board["name"]
        parts = sum(score[part] for part in SCORE_PARTS)
        if parts != score["total"]:
            yield f"{name}'s score adds up to {parts}, but its total is {score['total']}"
        for part, from_the_board in parts_shown_on_the_board(view, score["player"]).items():
            if score[part] != from_the_board:
                on_score = counted(score[part], "Victory Point")
                yield f"{name}'s score has {on_score} for {part.capitalize()}, but the board gives {from_the_board}"
        terraform_rating, megacredits = player_board["terraform_rating"], player_board["resources"]["megacredits"]
        if score["terraform_rating"] != terraform_rating:
            on_score = score["terraform_rating"]
            yield f"{name}'s score has Terraform Rating {on_score}, but their board has {terraform_rating}"
        if score["megacredits"] != megacredits:
            yield f"{name}'s score has {score['megacredits']} MegaCredits, but their board has {megacredits}"
        standing = (score["total"], score["megacredits"])
        above = sum(1 for other in scores if (other["total"], other["megacredits"]) > standing)
        if score["rank"] != 1 + above:
            ranks = "Player ranks" if above == 1 else "Players rank"
            yield f"{name} has rank {score['rank']}, but {above} {ranks} above them"


def parts_shown_on_the_board(view: View, player: int) -> dict[str, int]:
    """The Victory Points `player` should score for Milestones, Greeneries and Cities: 5 for
    each Milestone they claimed, 1 for each of their Greeneries, and 1 for each Greenery next
    to each of their Cities, whoever owns it."""
    tiles = tiles_on_the_board(view)
    owned = {area_id: tile["type"] for area_id, tile in tiles.items() if tile["owner"] == player}
    claimed = sum(1 for milestone in view["milestones"] if milestone["claimed_by"] == player)
    greeneries_next_to_cities = sum(
        1
        for area_id, kind in owned.items()
        if kind == "city"
        for next_area in ADJACENT_AREAS.get(area_id, [])
        if tiles.get(next_area, {}).get("type") == "greenery"
    )
    return {
        "milestones": MILESTONE_VICTORY_POINTS * claimed,
        "greeneries": sum(1 for kind in owned.values() if kind == "greenery"),
        "cities": greeneries_next_to_cities,
    }


def counted(count: int, thing: str) -> str:
    """"1 Award", "0 Milestones"."""
    return f"{count} {thing}{'' if count == 1 else 's'}"


def tiles_on_the_board(view: View) -> dict[str, dict[str, Any]]:
    """Every Tile on the board, by Area."""
    return {entry["area"]: entry["tile"] for entry in view["board"] if entry["tile"] is not None}


AFTER_EVERY_DECISION: tuple[Check, ...] = (
    no_negative_resources,
    production_within_its_limits,
    global_parameters_within_range,
    tiles_only_on_legal_areas,
    only_legal_areas_offered,
    at_most_three_milestones_and_awards,
    every_decision_has_an_option,
)

AT_THE_END_OF_THE_GAME: tuple[Check, ...] = (score_breakdown_adds_up,)
