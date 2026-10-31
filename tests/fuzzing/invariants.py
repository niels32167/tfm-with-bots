"""What must hold in every Game. The fuzzer checks these after every Decision and at the
end of every Game (ticket 06).

Each check reads only what an outsider can see, the full view and the Decision the Game
is waiting on, and yields one line for each thing that is wrong. The printed rules and
board facts are written out here and in tests/helpers.py rather than read from the
engine, so a mistake in the engine can't hide behind the same mistake in its checks. The
card catalog's printed data is the exception: it is checked against the card list itself
(tests/tools/). Invariants for rules that don't exist yet join these lists when their ticket
lands.
"""

import itertools
from collections import Counter
from collections.abc import Callable, Iterator
from typing import Any

import tm_engine

from tests.helpers import (
    ADJACENT_AREAS,
    LAND_AREAS,
    OCEAN_AREAS,
    PROJECT_CARDS,
    RESOURCES,
    has_printed_production_box,
)

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

CARDS = {card["id"]: card for card in tm_engine.card_catalog()}

# The cards printed with "Place a greenery tile ON AN AREA RESERVED FOR OCEAN".
GREENERY_ON_AN_OCEAN_AREA_CARDS = ("mangrove", "protected_valley")
# The cards printed with "Place 1 ocean tile ON AN AREA NOT RESERVED FOR OCEAN".
OCEAN_ON_LAND_CARDS = ("artificial_lake",)
# The cards printed with "Place a city tile ADJACENT TO AT LEAST 2 OTHER CITY TILES".
CITY_NEXT_TO_CITIES_CARDS = ("urbanized_area",)
# How the fuzzer's messages describe a Tile that goes on other Areas than usual, by the Area
# Decision's "on".
OTHER_AREAS = {
    "ocean_areas": " on an Area reserved for Oceans",
    "land": " on an Area reserved for nothing",
    "next_to_two_cities": " next to at least 2 Cities",
}


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
    lie on Areas of Mars reserved for nothing, belong to a Player, and no two Cities touch.
    The exceptions, each allowed once for every card played that makes it:
    - a Player's Greenery on an Area reserved for Oceans (Mangrove);
    - an Ocean on an Area reserved for nothing (Artificial Lake);
    - a Player's City next to at least 2 other Cities (Urbanized Area)."""
    tiles = tiles_on_the_board(view)
    greeneries_on_ocean_areas: Counter[int] = Counter()
    oceans_on_land = 0
    for area_id, tile in tiles.items():
        name, owner = TILE_NAMES[tile["type"]], tile["owner"]
        if tile["type"] == "ocean":
            if area_id in LAND_AREAS:
                oceans_on_land += 1
            elif area_id not in OCEAN_AREAS:
                yield f"the Ocean on {area_id} is not on an Area reserved for Oceans or for nothing"
            if owner is not None:
                yield f"the Ocean on {area_id} belongs to Player {owner + 1}, but Oceans belong to nobody"
            continue
        owned_by_a_player = owner in range(len(view["players"]))
        if tile["type"] == "greenery" and area_id in OCEAN_AREAS:
            if owned_by_a_player:
                greeneries_on_ocean_areas[owner] += 1
        elif area_id not in LAND_AREAS:
            yield f"the {name} on {area_id} is not on an Area of Mars that is reserved for nothing"
        if not owned_by_a_player:
            yield f"the {name} on {area_id} belongs to no Player in the Game"
    for owner, greeneries in sorted(greeneries_on_ocean_areas.items()):
        cards = cards_played(view, owner, GREENERY_ON_AN_OCEAN_AREA_CARDS)
        if greeneries > cards:
            yield (
                f"Player {owner + 1} has {counted(greeneries, 'Greenery', 'Greeneries')} on Areas reserved for "
                f"Oceans, but played {counted(cards, 'card')} that put one there"
            )
    cards = sum(cards_played(view, player, OCEAN_ON_LAND_CARDS) for player in range(len(view["players"])))
    if oceans_on_land > cards:
        lie_on = "lies on an Area" if oceans_on_land == 1 else "lie on Areas"
        put_was = "puts one there was" if cards == 1 else "put one there were"
        yield (
            f"{counted(oceans_on_land, 'Ocean')} {lie_on} reserved for nothing, but "
            f"{counted(cards, 'card')} that {put_was} played"
        )
    yield from cities_apart(view, tiles)


def cities_apart(view: View, tiles: dict[str, dict[str, Any]]) -> Iterator[str]:
    """No two Cities touch, unless one of them is the City a Player placed next to at least 2
    other Cities with a card that puts one there (Urbanized Area): a Player may have one such
    City for each of those cards they played. Every pair of touching Cities left over is
    reported, for the choice of such Cities that leaves the fewest."""
    cities = {area_id for area_id, tile in tiles.items() if tile["type"] == "city"}
    touching = [
        (area_id, next_area)
        for area_id in sorted(cities)
        for next_area in ADJACENT_AREAS.get(area_id, [])
        if next_area > area_id and next_area in cities
    ]
    if not touching:
        return
    # For each Player, every way to pick as many of their Cities next to 2 others as they may have.
    picks_per_player = []
    for player in range(len(view["players"])):
        allowed = cards_played(view, player, CITY_NEXT_TO_CITIES_CARDS)
        next_to_two = [
            area_id
            for area_id in sorted(cities)
            if tiles[area_id]["owner"] == player
            and sum(1 for next_area in ADJACENT_AREAS.get(area_id, []) if next_area in cities) >= 2
        ]
        picks_per_player.append(list(itertools.combinations(next_to_two, min(allowed, len(next_to_two)))))

    def left_over_with(picks: tuple[tuple[str, ...], ...]) -> list[tuple[str, str]]:
        allowed_cities = {area_id for pick in picks for area_id in pick}
        return [pair for pair in touching if not allowed_cities & set(pair)]

    fewest_left_over = min((left_over_with(picks) for picks in itertools.product(*picks_per_player)), key=len)
    for area_id, next_area in fewest_left_over:
        yield f"the Cities on {area_id} and {next_area} are next to each other"


def cards_played(view: View, player: int, cards: tuple[str, ...]) -> int:
    """How many of `cards` `player` has played."""
    return sum(1 for card_id in view["players"][player]["played_cards"] if card_id in cards)


def only_legal_areas_offered(view: View, decision: Decision | None) -> Iterator[str]:
    """A choose-an-Area Decision offers exactly the Areas where its Tile may go."""
    if decision is None or decision["kind"] != "area" or not decision["options"]:
        return
    details = decision["options"][0]["details"]
    tile, on = details["tile"], details.get("on", "usual")
    offered = {option["details"]["area"] for option in decision["options"]}
    legal = legal_areas(view, tile, decision["player"], on)
    article_and_name = f"{'an' if tile == 'ocean' else 'a'} {TILE_NAMES[tile]}{OTHER_AREAS.get(on, '')}"
    for area_id in sorted(offered - legal):
        yield f"the Area Decision for {article_and_name} offers {area_id}, where it may not go"
    for area_id in sorted(legal - offered):
        yield f"the Area Decision for {article_and_name} leaves out {area_id}, where it may go"


def legal_areas(view: View, tile: str, player: int, on: str = "usual") -> set[str]:
    """Where `player` may place `tile`: an Ocean on a free Area reserved for Oceans; a City on
    free land on Mars next to no City; a Greenery on free land next to one of its owner's
    Tiles, or on any free land if there is no such Area. A Tile `on` other Areas goes on:
    - "ocean_areas" (Mangrove's Greenery): any free Area reserved for Oceans;
    - "land" (Artificial Lake's Ocean): any free land, an Area reserved for nothing;
    - "next_to_two_cities" (Urbanized Area's City): any free land next to at least 2 Cities."""
    tiles = tiles_on_the_board(view)
    if on == "ocean_areas" or (tile == "ocean" and on == "usual"):
        return {area_id for area_id in OCEAN_AREAS if area_id not in tiles}
    free_land = {area_id for area_id in LAND_AREAS if area_id not in tiles}

    def next_to(area_id: str, wanted: Callable[[dict[str, Any]], bool]) -> bool:
        return any(wanted(tiles[next_area]) for next_area in ADJACENT_AREAS[area_id] if next_area in tiles)

    def cities_next_to(area_id: str) -> int:
        return sum(1 for next_area in ADJACENT_AREAS[area_id] if tiles.get(next_area, {}).get("type") == "city")

    if on == "land":
        return free_land
    if on == "next_to_two_cities":
        return {area_id for area_id in free_land if cities_next_to(area_id) >= 2}
    if tile == "city":
        return {area_id for area_id in free_land if not next_to(area_id, lambda each: each["type"] == "city")}
    next_to_own = {area_id for area_id in free_land if next_to(area_id, lambda each: each["owner"] == player)}
    return next_to_own or free_land


def robotic_workforce_copies_only_your_building_cards(view: View, decision: Decision | None) -> Iterator[str]:
    """Robotic Workforce copies only the production box of a building card the Player has
    played: an Automated or Active card with a building Tag and a printed production box."""
    if decision is None:
        return
    player = decision["player"]
    played = view["players"][player]["played_cards"]
    for option in decision["options"]:
        details = option["details"]
        if details["type"] != "copy_production_box":
            continue
        card = CARDS[details["card"]]
        building_card = (
            card["id"] in played
            and card["type"] in ("automated", "active")
            and "building" in card["tags"]
            and has_printed_production_box(card)
        )
        if not building_card:
            yield (
                f"Robotic Workforce offers to copy the production box of {card['name']}, "
                f"not a building card of Player {player + 1}'s"
            )


def card_actions_used_once_per_generation(view: View, decision: Decision | None) -> Iterator[str]:
    """A Player has used only the actions of cards they played, and only in the Action phase: the
    Production phase ends the Generation, and every action with it. An Action Decision offers
    only the actions of the deciding Player's own played cards that they haven't used yet."""
    for player_board in view["players"]:
        name, used = player_board["name"], player_board["used_actions"]
        if used and view["phase"] != "action":
            yield f"in the {view['phase']} phase, {name} has used the actions of {', '.join(used)}"
        for card_id in used:
            if card_id not in player_board["played_cards"] or "action" not in CARDS[card_id].get("effects", {}):
                yield f"{name} has used the action of '{card_id}', which is not a card with an action they played"
    if decision is None:
        return
    player_board = view["players"][decision["player"]]
    for option in decision["options"]:
        details = option["details"]
        if details["type"] != "use_action":
            continue
        card_id = details["card"]
        if card_id not in player_board["played_cards"] or "action" not in CARDS[card_id].get("effects", {}):
            yield f"{player_board['name']} is offered the action of '{card_id}', not a card with an action they played"
        elif card_id in player_board["used_actions"]:
            yield f"{player_board['name']} is offered the action of '{card_id}' again this Generation"


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


def every_card_in_exactly_one_place(view: View, decision: Decision | None) -> Iterator[str]:
    """Every Project Card is in exactly one place: the deck, the discard pile, a hand, a Player's
    played cards, the cards a Player drafts from or has kept in the Draft, the cards dealt to a
    Player to buy from in the setup or a Research phase, among which are those they have bought,
    or the cards a Player looks at or has kept while playing Business Contacts or Invention
    Contest, or using the action of Inventors' Guild or Business Network. The sizes shown agree
    with the cards."""
    places: dict[str, list[str]] = {card_id: [] for card_id in PROJECT_CARDS}
    for pile, name in (("deck", "the deck"), ("discard", "the discard pile")):
        if view[f"{pile}_size"] != len(view[pile]):
            yield f"{pile}_size is {view[f'{pile}_size']}, but {name} holds {counted(len(view[pile]), 'card')}"
        for card_id in view[pile]:
            places.setdefault(card_id, []).append(name)
    buying_phase = view["phase"] in ("setup", "research")
    for player_board in view["players"]:
        name, hand, buying = player_board["name"], player_board["hand"], player_board["buying"]
        if player_board["hand_size"] != len(hand):
            holds = counted(len(hand), "card")
            yield f"{name}'s hand_size is {player_board['hand_size']}, but their hand holds {holds}"
        for card_id in hand:
            places.setdefault(card_id, []).append(f"{name}'s hand")
        for card_id in player_board["played_cards"]:
            places.setdefault(card_id, []).append(f"{name}'s played cards")
        drafting = player_board["drafting"]
        if (drafting is not None) != (view["phase"] == "draft"):
            yield f"in the {view['phase']} phase, {name} is {'' if drafting else 'not '}drafting cards"
        if drafting is not None:
            for card_id in drafting["picking_from"]:
                places.setdefault(card_id, []).append(f"{name}'s cards to draft from")
            for card_id in drafting["kept"]:
                places.setdefault(card_id, []).append(f"{name}'s cards kept in the Draft")
        keeping = player_board["keeping"]
        if keeping is not None:
            for card_id in keeping["looking_at"]:
                places.setdefault(card_id, []).append(f"{name}'s cards looked at")
            for card_id in keeping["kept"]:
                places.setdefault(card_id, []).append(f"{name}'s cards kept")
        if (buying is not None) != buying_phase:
            yield f"in the {view['phase']} phase, {name} is {'' if buying else 'not '}buying cards"
        if buying is None:
            continue
        for card_id in buying["dealt"]:
            places.setdefault(card_id, []).append(f"{name}'s cards to buy from")
        for card_id in buying["bought"]:
            if card_id not in buying["dealt"]:
                yield f"{name} has bought '{card_id}', which was not dealt to them"
    for card_id, found in places.items():
        if card_id not in CARDS or CARDS[card_id]["type"] == "corporation":
            yield f"'{card_id}' is not a Project Card, but is in {' and '.join(found)}"
        elif not found:
            yield f"'{card_id}' is nowhere"
        elif len(found) > 1:
            yield f"'{card_id}' is in {len(found)} places: {' and '.join(found)}"


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
    """The Victory Points `player` should score for Milestones, Greeneries, Cities and cards:
    5 for each Milestone they claimed, 1 for each of their Greeneries, 1 for each Greenery next
    to each of their Cities, whoever owns it, and the Victory Points printed on their played
    cards."""
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
        "cards": card_victory_points(view, player),
    }


def card_victory_points(view: View, player: int) -> int:
    """The Victory Points printed on `player`'s played cards: a fixed number, or points for
    every so many of their Tags in play (no Tag on a played Event counts) or of the Tiles in
    play. Card Resources (ticket 19) and Tiles of cards (ticket 18) don't exist yet, so they
    count 0."""
    played = [CARDS[card_id] for card_id in view["players"][player]["played_cards"]]
    tags = Counter(tag for card in played if card["type"] != "event" for tag in card["tags"])
    tiles = Counter(tile["type"] for tile in tiles_on_the_board(view).values())

    def count(of: dict[str, str]) -> int:
        ((kind, what),) = of.items()
        return {"tag": tags[what], "tiles_in_play": tiles[what]}.get(kind, 0)

    points = 0
    for card in played:
        printed = card["victory_points"]
        if isinstance(printed, int):
            points += printed
        elif printed is not None and "per" in printed:
            points += printed["points"] * (count(printed["of"]) // printed["per"])
        elif printed is not None and count(printed["of"]) >= printed["at_least"]:
            points += printed["points"]
    return points


def counted(count: int, thing: str, things: str | None = None) -> str:
    """"1 Award", "0 Milestones", or with `things` for an irregular plural, "2 Greeneries"."""
    return f"{count} {thing if count == 1 else things or thing + 's'}"


def tiles_on_the_board(view: View) -> dict[str, dict[str, Any]]:
    """Every Tile on the board, by Area."""
    return {entry["area"]: entry["tile"] for entry in view["board"] if entry["tile"] is not None}


AFTER_EVERY_DECISION: tuple[Check, ...] = (
    no_negative_resources,
    production_within_its_limits,
    global_parameters_within_range,
    tiles_only_on_legal_areas,
    only_legal_areas_offered,
    robotic_workforce_copies_only_your_building_cards,
    card_actions_used_once_per_generation,
    at_most_three_milestones_and_awards,
    every_card_in_exactly_one_place,
    every_decision_has_an_option,
)

AT_THE_END_OF_THE_GAME: tuple[Check, ...] = (score_breakdown_adds_up,)
