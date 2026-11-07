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
    CARDS_HOLDING_CARD_RESOURCES,
    CORPORATIONS,
    LAND_AREAS,
    NOCTIS_CITY,
    OCEAN_AREAS,
    PRELUDE_CARDS,
    PRELUDE_PROJECT_CARDS,
    PROJECT_CARDS,
    RESERVED_FOR_CARDS,
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
PLANTS_PER_GREENERY = 8
CORPORATIONS_DEALT = 2
PRELUDE_CARDS_DEALT, PRELUDE_CARDS_KEPT = 4, 2
STEEL_VALUE, TITANIUM_VALUE = 2, 3

# How the game log names each Resource: an amount of it, and its Production.
AMOUNT_NAMES = {name: name for name in RESOURCES} | {"megacredits": "MegaCredits"}
PRODUCTION_NAMES = {name: name for name in RESOURCES} | {"megacredits": "MegaCredit", "plants": "plant"}
TILE_NAMES = {"ocean": "Ocean", "greenery": "Greenery", "city": "City", "special": "special Tile"}
# The six parts of a final score, which add up to its total.
SCORE_PARTS = ("terraform_rating", "milestones", "awards", "greeneries", "cities", "cards")

CARDS = {card["id"]: card for card in tm_engine.card_catalog()}

# The cards printed with "Place a greenery tile ON AN AREA RESERVED FOR OCEAN".
GREENERY_ON_AN_OCEAN_AREA_CARDS = ("mangrove", "protected_valley")
# The cards printed with "Place 1 ocean tile ON AN AREA NOT RESERVED FOR OCEAN".
OCEAN_ON_LAND_CARDS = ("artificial_lake",)
# The cards printed with "Place a city tile ADJACENT TO AT LEAST 2 OTHER CITY TILES".
CITY_NEXT_TO_CITIES_CARDS = ("urbanized_area",)
# The card printed with "Place this tile ON AN AREA RESERVED FOR OCEAN".
SPECIAL_TILE_ON_AN_OCEAN_AREA_CARDS = ("mohole_area",)
# The four volcanoes: Tharsis Tholus, Ascraeus Mons, Pavonis Mons and Arsia Mons.
VOLCANOES = ("B2", "C1", "D1", "E1")
# The land whose placement bonus has steel or titanium, as printed on the Tharsis board.
STEEL_OR_TITANIUM_LAND = ("A1", "B2", "C7", "D1", "H1", "H6", "J1", "J2")
# The building cards whose printed production box is part of their action, which Robotic Workforce
# doesn't copy.
PRODUCTION_BOX_IN_THE_ACTION = ("equatorial_magnetizer", "industrial_center", "underground_detonations")
# The building Corporation whose printed production box is part of its effect, which Robotic Workforce
# doesn't copy either.
PRODUCTION_BOX_IN_THE_EFFECT = ("tharsis_republic",)
# How the fuzzer's messages describe a Tile that goes on other Areas than usual, by the Area
# Decision's "on".
OTHER_AREAS = {
    "ocean_areas": " on an Area reserved for Oceans",
    "land": " on an Area reserved for nothing",
    "next_to_two_cities": " next to at least 2 Cities",
    "next_to_no_other_tile": " next to no other Tile",
    "next_to_a_city": " next to a City",
    "next_to_a_greenery": " next to a Greenery",
    "volcanoes": " on a volcano",
    "steel_or_titanium_bonus": " on a steel or titanium bonus",
    "steel_or_titanium_bonus_next_to_own_tile": " on a steel or titanium bonus next to its owner's Tile",
    "noctis_city": " on Noctis City's Area",
    "phobos_space_haven": " on Phobos Space Haven's Area",
    "ganymede_colony": " on Ganymede Colony's Area",
}
# The MegaCredits off each card its Player plays, as printed on the cards with such an effect:
# off every card, or only off those with a Tag.
DISCOUNTS = {
    "research_outpost": (1, None),
    "space_station": (2, "space"),
    "earth_catapult": (2, None),
    "quantum_extractor": (2, "space"),
    "mass_converter": (2, "space"),
    "earth_office": (3, "earth"),
    "anti_gravity_technology": (2, None),
    "shuttles": (2, "space"),
    "teractor": (3, "earth"),
    "thorgate": (3, "power"),
}
# The Standard Projects' printed costs, by Option details' "project".
STANDARD_PROJECT_COSTS = {"power_plant": 11, "asteroid": 14, "aquifer": 18, "greenery": 23, "city": 25}
# The Corporations printed with a first action, and how the Decision details describe them.
CORPORATIONS_WITH_A_FIRST_ACTION = ("inventrix", "tharsis_republic")
# The Corporation printed with "Your may use heat as MC".
HEAT_AS_MEGACREDITS = "helion"
# What raises what a steel or a titanium pays, printed on these cards: (steel, titanium).
CUBE_VALUES = {"advanced_alloys": (1, 1), "phobolog": (0, 1)}
# The Resources a card loses when it is played, printed on the only one that loses heat.
HEAT_LOST = {"local_heat_trapping": 5}
# The Events printed with an effect on the next card played this Generation, and what they take
# off its cost.
NEXT_CARD_DISCOUNTS = {"indentured_workers": 8, "special_design": 0}
# What each Prelude Card printed "Pay X M€" costs once its other effects are done.
PRELUDE_CARD_PRICES = {
    card["id"]: card["effects"]["pay"]["megacredits"]
    for card in CARDS.values()
    if card["type"] == "prelude" and "pay" in card.get("effects", {})
}
# What each Prelude Card that plays a card from the hand takes off its cost.
PRELUDE_NEXT_CARD_DISCOUNTS = {"excentric_sponsor": 25, "ecology_experts": 0}


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
    """Oceans lie on Areas reserved for Oceans and belong to nobody. Greeneries, Cities and
    special Tiles lie on Areas of Mars reserved for nothing, belong to a Player, and no two
    Cities touch. A special Tile is one of its owner's played cards. The exceptions, each allowed
    once for every card played that makes it:
    - a Player's Greenery on an Area reserved for Oceans (Mangrove);
    - an Ocean on an Area reserved for nothing (Artificial Lake);
    - a Player's City next to at least 2 other Cities (Urbanized Area);
    - Mohole Area's Tile on an Area reserved for Oceans;
    - a City on the Area reserved for its card (see `each_reserved_area_used_only_by_its_card`),
      which for Noctis City may touch other Cities."""
    tiles = tiles_on_the_board(view)
    greeneries_on_ocean_areas: Counter[int] = Counter()
    oceans_on_land = 0
    for area_id, tile in tiles.items():
        name, owner = tile_name(tile["type"], tile.get("card")), tile["owner"]
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
        elif area_id not in LAND_AREAS and not exception_to_land(area_id, tile):
            yield f"the {name} on {area_id} is not on an Area of Mars that is reserved for nothing"
        if not owned_by_a_player:
            yield f"the {name} on {area_id} belongs to no Player in the Game"
        elif "card" in tile and tile["card"] not in view["players"][owner]["played_cards"]:
            yield f"the {name} on {area_id} belongs to Player {owner + 1}, who has not played its card"
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


def exception_to_land(area_id: str, tile: dict[str, Any]) -> bool:
    """Whether `tile` may lie on `area_id`, which is not land, because its card puts it there:
    Mohole Area's Tile on an Area reserved for Oceans, or a City on the Area reserved for it."""
    if tile.get("card") in SPECIAL_TILE_ON_AN_OCEAN_AREA_CARDS:
        return area_id in OCEAN_AREAS
    return tile["type"] == "city" and "card" not in tile and area_id in RESERVED_FOR_CARDS


def cities_apart(view: View, tiles: dict[str, dict[str, Any]]) -> Iterator[str]:
    """No two Cities touch, unless one is Noctis City's, or one is the City a Player placed next to at least 2
    other Cities with a card that puts one there (Urbanized Area): a Player may have one such
    City for each of those cards they played. Every pair of touching Cities left over is
    reported, for the choice of such Cities that leaves the fewest."""
    cities = {area_id for area_id, tile in tiles.items() if tile["type"] == "city"}
    # Noctis City's City disregards the normal placement restrictions. A City placed next to it
    # later breaks them, but this can't tell which came first; Area Decisions are checked instead.
    touching = [
        (area_id, next_area)
        for area_id in sorted(cities)
        for next_area in ADJACENT_AREAS.get(area_id, [])
        if next_area > area_id and next_area in cities and NOCTIS_CITY not in (area_id, next_area)
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


def special_tiles_where_their_cards_put_them(view: View, decision: Decision | None) -> Iterator[str]:
    """Each special Tile lies where its card puts it, as far as later Tiles can't change it: Lava
    Flows' on a volcano, the Mining cards' on land with a steel or titanium bonus, Mining Area's next
    to another of its owner's Tiles, Industrial Center's next to a City, Ecological Zone's next to a
    Greenery and Mohole Area's on an Area reserved for Oceans. (Natural Preserve's was next to no Tile
    only when placed.)"""
    tiles = tiles_on_the_board(view)

    def next_to(area_id: str, wanted: Callable[[dict[str, Any]], bool]) -> bool:
        return any(wanted(tiles[next_area]) for next_area in ADJACENT_AREAS.get(area_id, []) if next_area in tiles)

    for area_id, tile in tiles.items():
        card, owner = tile.get("card"), tile["owner"]
        where = {
            "lava_flows": ("on a volcano", area_id in VOLCANOES),
            "mining_rights": ("on a steel or titanium bonus", area_id in STEEL_OR_TITANIUM_LAND),
            "mining_area": (
                "on a steel or titanium bonus next to another of its owner's Tiles",
                area_id in STEEL_OR_TITANIUM_LAND
                and next_to(area_id, lambda each, owner=owner: each["owner"] == owner),
            ),
            "industrial_center": ("next to a City", next_to(area_id, lambda each: each["type"] == "city")),
            "ecological_zone": ("next to a Greenery", next_to(area_id, lambda each: each["type"] == "greenery")),
            "mohole_area": ("on an Area reserved for Oceans", area_id in OCEAN_AREAS),
        }.get(card)
        if where is not None and not where[1]:
            yield f"the {tile_name(tile['type'], card)} on {area_id} is not {where[0]}"


def each_reserved_area_used_only_by_its_card(view: View, decision: Decision | None) -> Iterator[str]:
    """A City on an Area reserved for a card's City is owned by a Player who played the card. An
    Area claimed with Land Claim is land, claimed by a Player who played
    Land Claim, and holds no other Player's Tile."""
    for entry in view["board"]:
        area_id, tile, claimant = entry["area"], entry["tile"], entry["claimed_by"]
        card = RESERVED_FOR_CARDS.get(area_id)
        # Any other Tile there is off land, which `tiles_only_on_legal_areas` reports.
        if card is not None and tile is not None and tile["type"] == "city" and "card" not in tile:
            owner = tile["owner"]
            if owner not in range(len(view["players"])) or card not in view["players"][owner]["played_cards"]:
                yield f"the City on {area_id} is not {CARDS[card]['name']}'s: its owner has not played the card"
        if claimant is None:
            continue
        if area_id not in LAND_AREAS:
            yield f"{area_id} is claimed with Land Claim, but is not an Area of Mars reserved for nothing"
        if claimant not in range(len(view["players"])) or "land_claim" not in view["players"][claimant]["played_cards"]:
            yield f"{area_id} is claimed by Player {claimant + 1}, who has not played Land Claim"
        if tile is not None and tile["owner"] not in (None, claimant):
            name = tile_name(tile["type"], tile.get("card"))
            yield (
                f"the {name} on {area_id} belongs to Player {tile['owner'] + 1}, "
                f"but Player {claimant + 1} claimed the Area"
            )


def cards_played(view: View, player: int, cards: tuple[str, ...]) -> int:
    """How many of `cards` `player` has played."""
    return sum(1 for card_id in view["players"][player]["played_cards"] if card_id in cards)


def only_legal_areas_offered(view: View, decision: Decision | None) -> Iterator[str]:
    """A choose-an-Area Decision offers exactly the Areas where its Tile may go, or that Land
    Claim may claim. An Ocean placed for a Prelude Card with a price (Aquifer Turbines) goes only where
    the Oceans next to it gain its Player enough to pay that price."""
    if decision is None or decision["kind"] != "area" or not decision["options"]:
        return
    details = decision["options"][0]["details"]
    offered = {option["details"]["area"] for option in decision["options"]}
    if details["type"] == "claim_area":
        legal = claimable_areas(view)
        article_and_name = "Land Claim"
    else:
        tile, on = details["tile"], details.get("on", "usual")
        legal = legal_areas(view, tile, decision["player"], on)
        price = PRELUDE_CARD_PRICES.get(view["playing_prelude_card"], 0)
        if tile == "ocean" and price:
            spendable = spendable_megacredits(view["players"][decision["player"]])
            legal = {
                area_id for area_id in legal if spendable + megacredits_from_oceans_next_to(view, area_id) >= price
            }
        name = tile_name(tile, details.get("card"))
        article_and_name = f"{'an' if tile == 'ocean' else 'a'} {name}{OTHER_AREAS.get(on, '')}"
    for area_id in sorted(offered - legal):
        yield f"the Area Decision for {article_and_name} offers {area_id}, where it may not go"
    for area_id in sorted(legal - offered):
        yield f"the Area Decision for {article_and_name} leaves out {area_id}, where it may go"


def megacredits_from_oceans_next_to(view: View, area_id: str) -> int:
    """What an Ocean placed on `area_id` gains its Player for the Oceans next to it: 2 MegaCredits each."""
    tiles = tiles_on_the_board(view)
    return 2 * sum(1 for next_area in ADJACENT_AREAS[area_id] if tiles.get(next_area, {}).get("type") == "ocean")


def legal_areas(view: View, tile: str, player: int, on: str = "usual") -> set[str]:
    """Where `player` may place `tile`: an Ocean on a free Area reserved for Oceans; a City on
    free land on Mars next to no City; a Greenery on free land next to one of its owner's
    Tiles, or on any free land if there is no such Area. A Tile `on` other Areas goes on:
    - "ocean_areas" (Mangrove's Greenery): any free Area reserved for Oceans;
    - "land" (Artificial Lake's Ocean): any free land, an Area reserved for nothing;
    - "next_to_two_cities" (Urbanized Area's City): any free land next to at least 2 Cities;
    - "next_to_no_other_tile" (Research Outpost's City): any free land next to no Tile;
    - "next_to_a_city" (Industrial Center's Tile): any free land next to a City;
    - "next_to_a_greenery" (Ecological Zone's Tile): any free land next to a Greenery, whoever owns it;
    - "volcanoes" (Lava Flows' Tile): any free volcano;
    - "steel_or_titanium_bonus" (Mining Rights' Tile): any free land with such a bonus;
    - "steel_or_titanium_bonus_next_to_own_tile" (Mining Area's): the same, next to its owner's Tile;
    - a card's reserved Area (Noctis City, Phobos Space Haven, Ganymede Colony): that Area, if free.
    A special Tile goes on any free land otherwise. Land claimed by another Player is never free."""
    tiles = tiles_on_the_board(view)
    if on in RESERVED_FOR_CARDS.values():
        (area_id,) = [area_id for area_id, card in RESERVED_FOR_CARDS.items() if card == on]
        return set() if area_id in tiles else {area_id}
    if on == "ocean_areas" or (tile == "ocean" and on == "usual"):
        return {area_id for area_id in OCEAN_AREAS if area_id not in tiles}
    claimed_by_others = {
        entry["area"] for entry in view["board"] if entry["claimed_by"] not in (None, player)
    }
    free_land = {area_id for area_id in LAND_AREAS if area_id not in tiles and area_id not in claimed_by_others}

    def next_to(area_id: str, wanted: Callable[[dict[str, Any]], bool]) -> bool:
        return any(wanted(tiles[next_area]) for next_area in ADJACENT_AREAS[area_id] if next_area in tiles)

    def cities_next_to(area_id: str) -> int:
        return sum(1 for next_area in ADJACENT_AREAS[area_id] if tiles.get(next_area, {}).get("type") == "city")

    if on == "land" or (tile == "special" and on == "usual"):
        return free_land
    if on == "next_to_a_city":
        return {area_id for area_id in free_land if cities_next_to(area_id) >= 1}
    if on == "next_to_a_greenery":
        return {area_id for area_id in free_land if next_to(area_id, lambda each: each["type"] == "greenery")}
    if on == "volcanoes":
        return free_land & set(VOLCANOES)
    if on == "steel_or_titanium_bonus":
        return free_land & set(STEEL_OR_TITANIUM_LAND)
    if on == "steel_or_titanium_bonus_next_to_own_tile":
        mining_land = free_land & set(STEEL_OR_TITANIUM_LAND)
        return {area_id for area_id in mining_land if next_to(area_id, lambda each: each["owner"] == player)}
    if on == "next_to_two_cities":
        return {area_id for area_id in free_land if cities_next_to(area_id) >= 2}
    if on == "next_to_no_other_tile":
        return {area_id for area_id in free_land if not next_to(area_id, lambda each: True)}
    if tile == "city":
        return {area_id for area_id in free_land if not next_to(area_id, lambda each: each["type"] == "city")}
    next_to_own = {area_id for area_id in free_land if next_to(area_id, lambda each: each["owner"] == player)}
    return next_to_own or free_land


def claimable_areas(view: View) -> set[str]:
    """The Areas Land Claim may claim: free land that nobody has claimed."""
    return {
        entry["area"]
        for entry in view["board"]
        if entry["area"] in LAND_AREAS and entry["tile"] is None and entry["claimed_by"] is None
    }


def robotic_workforce_copies_only_your_building_cards(view: View, decision: Decision | None) -> Iterator[str]:
    """Robotic Workforce copies only the production box of a building card the Player has
    played: an Automated or Active card with a building Tag and a printed production box that is
    not part of its action."""
    if decision is None:
        return
    player = decision["player"]
    played = cards_in_play(view["players"][player])
    for option in decision["options"]:
        details = option["details"]
        if details["type"] != "copy_production_box":
            continue
        card = CARDS[details["card"]]
        building_card = (
            card["id"] in played
            and card["type"] in ("automated", "active", "corporation", "prelude")
            and "building" in card["tags"]
            and has_printed_production_box(card)
            and card["id"] not in PRODUCTION_BOX_IN_THE_ACTION
            and card["id"] not in PRODUCTION_BOX_IN_THE_EFFECT
        )
        if not building_card:
            yield (
                f"Robotic Workforce offers to copy the production box of {card['name']}, "
                f"not a building card of Player {player + 1}'s"
            )


def cards_in_play(player_board: dict[str, Any]) -> list[str]:
    """A Player's played Project Cards and Prelude Cards, and their Corporation, once it is revealed."""
    corporation = player_board["corporation"]
    return player_board["played_cards"] + player_board["played_prelude_cards"] + ([corporation] if corporation else [])


def spendable_megacredits(player_board: dict[str, Any]) -> int:
    """What a Player may spend on a cost that neither steel nor titanium may pay: their MegaCredits, and
    with Helion their heat."""
    resources = player_board["resources"]
    return resources["megacredits"] + (resources["heat"] if player_board["corporation"] == HEAT_AS_MEGACREDITS else 0)


def card_actions_used_once_per_generation(view: View, decision: Decision | None) -> Iterator[str]:
    """A Player has used only the actions of cards they played, and only in the Action phase: the
    Production phase ends the Generation, and every action with it. An Action Decision offers
    only the actions of the deciding Player's own played cards that they haven't used yet, and United
    Nations Mars Initiative's only if their Terraform Rating was raised this Generation."""
    for player_board in view["players"]:
        name, used = player_board["name"], player_board["used_actions"]
        if used and view["phase"] != "action":
            yield f"in the {view['phase']} phase, {name} has used the actions of {', '.join(used)}"
        for card_id in used:
            if card_id not in cards_in_play(player_board) or "action" not in CARDS[card_id].get("effects", {}):
                yield f"{name} has used the action of '{card_id}', which is not a card with an action they played"
    if decision is None:
        return
    player_board = view["players"][decision["player"]]
    for option in decision["options"]:
        details = option["details"]
        if details["type"] != "use_action":
            continue
        card_id = details["card"]
        if card_id not in cards_in_play(player_board) or "action" not in CARDS[card_id].get("effects", {}):
            yield f"{player_board['name']} is offered the action of '{card_id}', not a card with an action they played"
        elif card_id in player_board["used_actions"]:
            yield f"{player_board['name']} is offered the action of '{card_id}' again this Generation"
        elif card_id == "united_nations_mars_initiative" and not player_board["terraform_rating_raised"]:
            yield f"{player_board['name']} is offered the action of '{card_id}' without a raise this Generation"


def cards_cost_what_the_discounts_leave(view: View, decision: Decision | None) -> Iterator[str]:
    """The costs shown for the cards in each hand, and the Options to play a card, are what
    `card_cost` gives. Only an Event with an effect on the next card waits on it, in the Action
    phase, among the Player's played cards, or a Prelude Card that plays a card from the hand, while
    its Player plays them."""
    for player, player_board in enumerate(view["players"]):
        name, played, next_card = player_board["name"], player_board["played_cards"], player_board["next_card"]
        if next_card in PRELUDE_NEXT_CARD_DISCOUNTS:
            if next_card not in player_board["played_prelude_cards"]:
                yield f"{name}'s next card waits on '{next_card}', a Prelude Card they haven't played"
            if view["phase"] != "prelude_cards":
                yield f"in the {view['phase']} phase, {name}'s next card still waits on the Prelude Card '{next_card}'"
        elif next_card is not None:
            if next_card not in NEXT_CARD_DISCOUNTS or next_card not in played:
                yield f"{name}'s next card waits on '{next_card}', not an Event with such an effect they played"
            # An Event played for a Prelude Card (Excentric Sponsor) may wait on the next card at once.
            if view["phase"] not in ("action", "prelude_cards"):
                yield f"in the {view['phase']} phase, {name}'s next card still waits on '{next_card}'"
        for card_id, shown in player_board["card_costs"].items():
            cost = card_cost(view, player, card_id)
            if shown != cost:
                yield f"{name}'s {CARDS[card_id]['name']} costs {shown}, not {cost}"
    if decision is None:
        return
    for option in decision["options"]:
        details = option["details"]
        if details["type"] != "play_card":
            continue
        cost = card_cost(view, decision["player"], details["card"])
        if details["cost"] != cost:
            yield f"{option['label']} is offered at {details['cost']}, not at {cost}"


def card_cost(view: View, player: int, card_id: str) -> int:
    """What `player` pays for `card_id`: its printed cost less the discounts of their played
    cards and of the Event they played for their next card, or the Prelude Card playing it, never
    below 0."""
    player_board = view["players"][player]
    card, played = CARDS[card_id], cards_in_play(player_board)
    discount = sum(
        amount
        for discounting, (amount, tag) in DISCOUNTS.items()
        if discounting in played and (tag is None or tag in card["tags"])
    )
    next_card = player_board["next_card"]
    discount += NEXT_CARD_DISCOUNTS.get(next_card, 0) + PRELUDE_NEXT_CARD_DISCOUNTS.get(next_card, 0)
    return max(0, card["cost"] - discount)


def card_resources_only_on_played_cards_that_hold_them(view: View, decision: Decision | None) -> Iterator[str]:
    """Each Player's board shows the Card Resources on exactly their played cards printed with one to
    hold, and never fewer than none."""
    for player_board in view["players"]:
        name, played = player_board["name"], player_board["played_cards"]
        wanted = sorted(card_id for card_id in played if card_id in CARDS_HOLDING_CARD_RESOURCES)
        shown = player_board["card_resources"]
        if sorted(shown) != wanted:
            yield f"{name}'s board shows Card Resources on {sorted(shown)}, not on {wanted}"
        for card_id, amount in shown.items():
            if amount < 0:
                yield f"{name}'s {card_id} has {amount} Card Resources"


def cards_with_card_resources(player_board: dict[str, Any], kind: str | None) -> list[str]:
    """The cards of a Player's holding Card Resources of `kind` (any, for None), in card-number
    order."""
    return [
        card_id
        for card_id in player_board["played_cards"]
        if card_id in player_board["card_resources"] and kind in (None, CARDS_HOLDING_CARD_RESOURCES.get(card_id))
    ]


# The kinds of Card Resource that Protected Habitats keeps from its Player's opponents.
PROTECTED_KINDS = ("animal", "microbe")
# The card whose Card Resources nobody may remove, as printed.
CARDS_NOBODY_REMOVES_FROM = ("pets",)


def has_protected_habitats(board: dict[str, Any]) -> bool:
    return "protected_habitats" in board["played_cards"]


def cards_to_remove_from(view: View, owner: int, kind: str, by: int) -> list[str]:
    """The cards of `owner`'s that Player `by` may remove a Card Resource of `kind` from: those with
    some on them, but for Pets, and none of an opponent's with Protected Habitats."""
    board = view["players"][owner]
    if owner != by and kind in PROTECTED_KINDS and has_protected_habitats(board):
        return []
    return [
        card_id
        for card_id in cards_with_card_resources(board, kind)
        if board["card_resources"][card_id] > 0 and card_id not in CARDS_NOBODY_REMOVES_FROM
    ]


def card_resource_actions_can_be_carried_out(view: View, decision: Decision | None) -> Iterator[str]:
    """The actions spending Resources or Card Resources for Card Resources are offered only if they
    can be carried out: Physics Complex with 6 energy, Search for Life with a MegaCredit and a card
    to reveal, Security Fleet with a titanium, and Ants and Predators with a card to take a microbe or
    an animal from."""
    if decision is None:
        return
    player = decision["player"]
    board = view["players"][player]

    def can_take(kind: str) -> bool:
        return any(cards_to_remove_from(view, owner, kind, player) for owner in range(len(view["players"])))

    can_carry_out = {
        "physics_complex": board["resources"]["energy"] >= 6,
        "search_for_life": spendable_megacredits(board) >= 1 and bool(view["deck"] or view["discard"]),
        "security_fleet": board["resources"]["titanium"] >= 1,
        "ants": can_take("microbe"),
        "predators": can_take("animal"),
    }
    for option in decision["options"]:
        details = option["details"]
        if details["type"] == "use_action" and not can_carry_out.get(details["card"], True):
            yield f"{option['label']} is offered, but {board['name']} cannot carry it out"


# The cards that add Card Resources to another card, as printed, each addition: the kind (any, for
# None), how many, and how many the card must have on it already.
ADDING_TO_ANOTHER_CARD = {
    "aerobraked_ammonia_asteroid": (("microbe", 2, 0),),
    "symbiotic_fungus": (("microbe", 1, 0),),
    "extreme_cold_fungus": (("microbe", 2, 0),),
    "ceos_favorite_project": ((None, 1, 1),),
    "eos_chasma_national_park": (("animal", 1, 0),),
    "imported_hydrogen": (("microbe", 3, 0), ("animal", 2, 0)),
    "large_convoy": (("animal", 4, 0),),
    "imported_nitrogen": (("microbe", 3, 0), ("animal", 2, 0)),
    "local_heat_trapping": (("animal", 2, 0),),
}


def cards_to_add_to_are_those_the_rules_allow(view: View, decision: Decision | None) -> Iterator[str]:
    """Adding Card Resources to another card offers every card of the deciding Player's that may
    get them, of the kind printed, with as many on it as printed, and there is a Decision only with
    two cards or more."""
    if decision is None or decision["kind"] != "add_to_card":
        return
    board = view["players"][decision["player"]]
    cards = {option["details"]["card"] for option in decision["options"]}
    if len(cards) != 1 or not cards <= set(ADDING_TO_ANOTHER_CARD):
        yield f"an add_to_card Decision is about {sorted(cards)}, not one card that adds to another"
        return
    card_id = cards.pop()
    found = [
        (option["details"]["to"], option["details"]["kind"], option["details"]["amount"])
        for option in decision["options"]
    ]
    # A card that adds two kinds asks about one at a time, so the Options say which this is.
    additions = ADDING_TO_ANOTHER_CARD[card_id]
    kind, amount, at_least = next((each for each in additions if each[0] in (None, found[0][1])), additions[0])
    wanted = [
        (to, CARDS_HOLDING_CARD_RESOURCES[to], amount)
        for to in cards_with_card_resources(board, kind)
        if board["card_resources"][to] >= at_least
    ]
    if found != wanted:
        yield f"{CARDS[card_id]['name']} offers to add {found}, not {wanted}"
    if len(found) < 2:
        yield f"{CARDS[card_id]['name']}'s add_to_card Decision has {len(found)} Option"


# The actions with alternatives that remove Card Resources from the card itself, and how many.
REMOVING_FROM_ITSELF = {"regolith_eaters": 2, "ghg_producing_bacteria": 2, "nitrite_reducing_bacteria": 3}
# The cards that let their Player choose their effects when played, as printed: for each alternative,
# the kind of Card Resource it adds to another card, or None for the plants.
ALTERNATIVES_WHEN_PLAYED = {
    "imported_hydrogen": (None, "microbe", "animal"),
    "large_convoy": (None, "animal"),
    "local_heat_trapping": (None, "animal"),
}


def effects_offered_are_those_the_rules_allow(view: View, decision: Decision | None) -> Iterator[str]:
    """An action's alternatives come as a Decision only when both can be carried out: the Card
    Resources they remove are on the card, or there is a card to add them to. A card played offers
    its plants, and adding Card Resources only with a card for them, with a Decision only if there
    is more than the plants."""
    if decision is None or decision["kind"] != "effects":
        return
    board = view["players"][decision["player"]]
    cards = {option["details"]["card"] for option in decision["options"]}
    if len(cards) != 1:
        yield f"an effects Decision is about {sorted(cards)}, not one card"
        return
    card_id = cards.pop()
    offered = [option["details"]["alternative"] for option in decision["options"]]
    if card_id in ALTERNATIVES_WHEN_PLAYED:
        wanted = [
            index
            for index, kind in enumerate(ALTERNATIVES_WHEN_PLAYED[card_id])
            if kind is None or cards_with_card_resources(board, kind)
        ]
        if offered != wanted:
            yield f"{CARDS[card_id]['name']} offers the alternatives {offered}, not {wanted}"
        if len(offered) < 2:
            yield f"{CARDS[card_id]['name']}'s effects Decision has {len(offered)} Option"
        return
    if offered != [0, 1]:
        yield f"{CARDS[card_id]['name']}'s effects Decision does not offer its 2 alternatives"
    if card_id == "extreme_cold_fungus":
        if not cards_with_card_resources(board, "microbe"):
            yield f"{CARDS[card_id]['name']} offers to add microbes, but {board['name']} has no card for them"
    elif card_id not in REMOVING_FROM_ITSELF:
        yield f"an effects Decision is about '{card_id}', which has no such choice"
    elif board["card_resources"][card_id] < REMOVING_FROM_ITSELF[card_id]:
        needed = REMOVING_FROM_ITSELF[card_id]
        yield f"{CARDS[card_id]['name']} offers to remove {needed}, but has {board['card_resources'][card_id]}"


def olympus_conference_offers_what_the_card_says(view: View, decision: Decision | None) -> Iterator[str]:
    """Olympus Conference's Decision offers adding a science and, with one on it and a card to draw,
    removing it to draw a card. With a card in the hand, it may offer Mars University's Options too,
    if the Player has played that card. There is no Decision without something to remove."""
    if decision is None or decision["kind"] != "olympus_conference":
        return
    board = view["players"][decision["player"]]
    offered = [option["details"] for option in decision["options"]]
    wanted = [
        {"type": "olympus_conference", "card": "olympus_conference", "draw": False},
        {"type": "olympus_conference", "card": "olympus_conference", "draw": True},
    ]
    if "olympus_conference" not in board["played_cards"]:
        yield f"{board['name']} is offered Olympus Conference's Decision without having played it"
        return
    if offered[:2] != wanted:
        yield f"Olympus Conference's Decision offers {offered[:2]}, not {wanted}"
    if board["card_resources"]["olympus_conference"] < 1:
        yield "Olympus Conference offers to remove a science, but has none"
    if not view["deck"] and not view["discard"]:
        yield "Olympus Conference offers to draw a card, but none is left"
    discards = [{"type": "discard_card", "card": card_id} for card_id in board["hand"]] + [{"type": "done"}]
    if offered[2:] not in ([], discards):
        yield f"Olympus Conference's Decision also offers {offered[2:]}, not every card in the hand and Done"
    if offered[2:] and "mars_university" not in board["played_cards"]:
        yield f"Olympus Conference's Decision offers {offered[2:]} without Mars University in play"


def viral_enhancers_offers_what_the_card_says(view: View, decision: Decision | None) -> Iterator[str]:
    """Viral Enhancers asks only about a card its Player has played that holds a Card Resource and has
    a plant, microbe or animal Tag, offering to add 1 to that card or gain 1 plant."""
    if decision is None or decision["kind"] != "viral_enhancers":
        return
    board = view["players"][decision["player"]]
    offered = [option["details"] for option in decision["options"]]
    card_id = offered[0]["card"]
    wanted = [{"type": "viral_enhancers", "card": card_id, "add": add} for add in (True, False)]
    if offered != wanted:
        yield f"Viral Enhancers' Decision offers {offered}, not {wanted}"
    if "viral_enhancers" not in board["played_cards"]:
        yield f"{board['name']} is offered Viral Enhancers' Decision without having played it"
    if card_id not in board["played_cards"] or card_id not in CARDS_HOLDING_CARD_RESOURCES:
        yield f"Viral Enhancers asks about '{card_id}', not a card of {board['name']}'s that holds Card Resources"
    if not set(CARDS[card_id]["tags"]) & {"plant", "microbe", "animal"}:
        yield f"Viral Enhancers asks about {CARDS[card_id]['name']}, which has no plant, microbe or animal Tag"


def discard_to_draw_offers_every_card_in_hand(view: View, decision: Decision | None) -> Iterator[str]:
    """Mars University's Decision offers to discard each card in the deciding Player's hand, or to
    be done."""
    if decision is None or decision["kind"] != "discard_to_draw":
        return
    hand = view["players"][decision["player"]]["hand"]
    offered = [option["details"] for option in decision["options"]]
    wanted = [{"type": "discard_card", "card": card_id} for card_id in hand] + [{"type": "done"}]
    if offered != wanted:
        yield f"Mars University's Decision offers {offered}, not every card in the hand and Done"


# What each card that takes from any Player takes, as printed: Production steps lowered, or
# Resources removed up to these amounts, one of them (Sabotage's titanium, steel or MegaCredits).
PRODUCTION_TAKEN = {
    "asteroid_mining_consortium": ("titanium", 1),
    "cloud_seeding": ("heat", 1),
    "great_escarpment_consortium": ("steel", 1),
    "hackers": ("megacredits", 2),
    "power_supply_consortium": ("energy", 1),
    "heat_trappers": ("heat", 2),
    "biomass_combustors": ("plants", 1),
    "energy_tapping": ("energy", 1),
    "fish": ("plants", 1),
    "small_animals": ("plants", 1),
    "birds": ("plants", 2),
    "herbivores": ("plants", 1),
}
RESOURCES_TAKEN = {
    "asteroid": (("plants", 3),),
    "comet": (("plants", 3),),
    "big_asteroid": (("plants", 4),),
    "deimos_down": (("plants", 8),),
    "mining_expedition": (("plants", 2),),
    "giant_ice_asteroid": (("plants", 6),),
    "sabotage": (("titanium", 3), ("steel", 4), ("megacredits", 7)),
    "hired_raiders": (("steel", 2), ("megacredits", 3)),
    "flooding": (("megacredits", 4),),
    "virus": (("plants", 5),),
}
# What each card that removes Card Resources from one card takes, as printed, up to this many.
CARD_RESOURCES_TAKEN = {"virus": ("animal", 2)}
STEALING_CARDS = ("hired_raiders",)
# The actions that move 1 Card Resource from any card to themselves, and its kind.
MOVING_A_CARD_RESOURCE = {"ants": "microbe", "predators": "animal"}
# Flooding takes only from the owners of Tiles next to its Ocean, which the view doesn't name.
TAKING_NEXT_TO_ITS_OCEAN = ("flooding",)


def targets_offered_are_those_the_rules_allow(view: View, decision: Decision | None) -> Iterator[str]:
    """A target Decision is about one card's taking. Lowering Production: it offers every opponent
    who can lose every step, or if none can, only the deciding Player, and there is a Decision
    only with two targets or more. Removing Resources: it offers each opponent who has some of an
    alternative's Resources, as much as they have up to the amount printed, and for Virus each of
    their cards with animals on it, then Remove nothing (for Flooding, some of those opponents).
    Protected Habitats keeps its Player's plants, animals and microbes from their opponents. Moving a
    Card Resource: it offers each opponent's card they may take from, or if there is none, the
    deciding Player's own, and there is a Decision only with two cards or more."""
    if decision is None or decision["kind"] != "target":
        return
    player, players = decision["player"], view["players"]
    offered = [option["details"] for option in decision["options"]]
    cards = {details["card"] for details in offered}
    if len(cards) != 1:
        yield f"a target Decision is about {sorted(cards)}, not one card"
        return
    card_id = cards.pop()
    if card_id in MOVING_A_CARD_RESOURCE:
        yield from cards_to_take_from_are_those_the_rules_allow(view, card_id, player, offered)
        return
    if card_id in PRODUCTION_TAKEN:
        resource, steps = PRODUCTION_TAKEN[card_id]
        lowest = MIN_MEGACREDIT_PRODUCTION if resource == "megacredits" else 0
        can_lose = [index for index, board in enumerate(players) if board["production"][resource] - steps >= lowest]
        opponents = [index for index in can_lose if index != player]
        wanted = opponents or [index for index in can_lose if index == player]
        targets = [details.get("player") for details in offered]
        if [details["type"] for details in offered] != ["lower_production"] * len(offered) or targets != wanted:
            yield f"{CARDS[card_id]['name']} offers to lower the Production of {targets}, not of {wanted}"
        if len(offered) < 2:
            yield f"{CARDS[card_id]['name']}'s target Decision has {len(offered)} Option"
        for details in offered:
            if changed(details["production"]) != {resource: -steps}:
                yield f"{CARDS[card_id]['name']} offers to lower Production by {details['production']}"
        return
    if card_id not in RESOURCES_TAKEN:
        yield f"a target Decision is about '{card_id}', which takes nothing from any Player"
        return
    wanted = []
    for index, board in enumerate(players):
        if index == player:
            continue
        if card_id in CARD_RESOURCES_TAKEN:
            kind, amount = CARD_RESOURCES_TAKEN[card_id]
            wanted += [
                (index, other, -min(amount, board["card_resources"][other]))
                for other in cards_to_remove_from(view, index, kind, player)
            ]
        protected = has_protected_habitats(board)
        wanted += [
            (index, resource, -min(amount, board["resources"][resource]))
            for resource, amount in RESOURCES_TAKEN[card_id]
            if board["resources"][resource] > 0 and not (resource == "plants" and protected)
        ]
    removals = offered[:-1]
    from_cards = {
        index: (details["player"], details["from"], -details["amount"])
        for index, details in enumerate(removals)
        if details["type"] == "remove_card_resources"
    }
    resources_taken = {
        index: (details["player"], *next(iter(changed(details["resources"]).items())))
        for index, details in enumerate(removals)
        if details["type"] == "remove_resources" and len(changed(details["resources"])) == 1
    }
    found = [{**from_cards, **resources_taken}[index] for index in sorted({*from_cards, *resources_taken})]
    complete = card_id not in TAKING_NEXT_TO_ITS_OCEAN
    if len(found) != len(removals) or (found != wanted if complete else not set(found) <= set(wanted)):
        yield f"{CARDS[card_id]['name']} offers to remove {found}, not {wanted}"
    if offered[-1] != {"type": "remove_nothing", "card": card_id}:
        yield f"{CARDS[card_id]['name']}'s target Decision ends with {offered[-1]}, not Remove nothing"
    steals = card_id in STEALING_CARDS
    if any(details.get("stolen", False) != steals for details in removals if details["type"] == "remove_resources"):
        yield f"{CARDS[card_id]['name']} offers to {'only remove' if steals else 'steal'} Resources"


def cards_to_take_from_are_those_the_rules_allow(
    view: View, card_id: str, player: int, offered: list[dict[str, Any]]
) -> Iterator[str]:
    """See `targets_offered_are_those_the_rules_allow`."""
    players, kind = view["players"], MOVING_A_CARD_RESOURCE[card_id]

    def of_owner(index: int) -> list[tuple[int, str]]:
        return [(index, other) for other in cards_to_remove_from(view, index, kind, player)]

    from_opponents = [each for index in range(len(players)) if index != player for each in of_owner(index)]
    wanted = from_opponents or of_owner(player)
    found = [(details.get("player"), details.get("from")) for details in offered]
    if found != wanted:
        yield f"{CARDS[card_id]['name']} offers to take from {found}, not {wanted}"
    if len(offered) < 2:
        yield f"{CARDS[card_id]['name']}'s target Decision has {len(offered)} Option"


def changed(amounts: dict[str, int]) -> dict[str, int]:
    """The Resources or Production steps of a change that are not 0."""
    return {name: amount for name, amount in amounts.items() if amount != 0}


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


def corporations_stay_hidden_until_they_are_revealed(view: View, decision: Decision | None) -> Iterator[str]:
    """At setup a Player has none revealed and may be choosing from 2 Corporations dealt, picking one
    of those, and nobody was dealt one that another was; after setup, none is being chosen and no
    two Players have the same one. A Corporation Decision offers exactly those dealt to the Player
    deciding, while they have chosen none."""
    dealt_so_far: list[str] = []
    for player_board in view["players"]:
        name, corporation, choosing = (
            player_board["name"],
            player_board["corporation"],
            player_board["choosing_corporation"],
        )
        if view["phase"] != "setup" and choosing is not None:
            yield f"in the {view['phase']} phase, {name} is choosing a Corporation"
        if view["phase"] == "setup" and corporation is not None:
            yield f"at setup, {name}'s Corporation {corporation} is revealed"
        if corporation is not None and corporation not in CORPORATIONS:
            yield f"{name}'s Corporation is '{corporation}', which is none"
        if corporation is not None:
            dealt_so_far.append(corporation)
        if choosing is None:
            continue
        if len(choosing["dealt"]) != CORPORATIONS_DEALT or not set(choosing["dealt"]) <= set(CORPORATIONS):
            yield f"{name} was dealt {choosing['dealt']}, not {CORPORATIONS_DEALT} Corporations"
        if choosing["picked"] is not None and choosing["picked"] not in choosing["dealt"]:
            yield f"{name} chose {choosing['picked']}, which was not dealt to them"
        dealt_so_far += choosing["dealt"]
    for corporation, times in Counter(dealt_so_far).items():
        if times > 1:
            yield f"{corporation} is with {times} Players"
    if decision is None or decision["kind"] != "corporation":
        return
    choosing = view["players"][decision["player"]]["choosing_corporation"]
    offered = [option["details"]["card"] for option in decision["options"]]
    if choosing is None or choosing["picked"] is not None or offered != choosing["dealt"]:
        yield f"Player {decision['player'] + 1} is offered the Corporations {offered}, not those dealt to them"


def first_action_comes_first(view: View, decision: Decision | None) -> Iterator[str]:
    """Only a Corporation printed with a first action has one due. While it is due and can be carried
    out, an Action Decision offers its Player that or Pass; a first action is offered for nothing else."""
    for player_board in view["players"]:
        if player_board["first_action_due"] and player_board["corporation"] not in CORPORATIONS_WITH_A_FIRST_ACTION:
            yield f"{player_board['name']} has a first action due with {player_board['corporation']}"
    if decision is None or decision["kind"] != "action":
        return
    player_board = view["players"][decision["player"]]
    corporation, due = player_board["corporation"], player_board["first_action_due"]
    types = sorted(option["details"]["type"] for option in decision["options"])
    can_place = corporation != "tharsis_republic" or legal_areas(view, "city", decision["player"])
    if due and can_place and types != ["first_action", "pass"]:
        yield f"{player_board['name']} must take the first action of {corporation} first, but is offered {types}"
    for option in decision["options"]:
        if option["details"]["type"] == "first_action" and (not due or option["details"]["card"] != corporation):
            yield f"{player_board['name']} is offered the first action of {option['details']['card']}"


def costs_of_standard_projects_and_greeneries_are_as_printed(view: View, decision: Decision | None) -> Iterator[str]:
    """A Standard Project costs what is printed, 3 MegaCredits less for Thorgate's Power Plant, and
    converting plants into a Greenery takes 8, or 7 with EcoLine. Whoever is offered one can pay for it."""
    if decision is None:
        return
    player_board = view["players"][decision["player"]]
    in_play = cards_in_play(player_board)
    resources = player_board["resources"]
    spendable = spendable_megacredits(player_board)
    for option in decision["options"]:
        details = option["details"]
        if details["type"] == "standard_project" and details["project"] != "sell_patents":
            cost = STANDARD_PROJECT_COSTS[details["project"]]
            if details["project"] == "power_plant" and "thorgate" in in_play:
                cost -= 3
            if details["cost"] != cost:
                yield f"{option['label']} is offered at {details['cost']}, not at {cost}"
            # What is below 0 `no_negative_resources` reports.
            if 0 <= spendable < cost:
                yield f"{option['label']} is offered to {player_board['name']}, who can spend {spendable}"
        if details["type"] == "convert_plants":
            plants = PLANTS_PER_GREENERY - ("ecoline" in in_play)
            if details["plants"] != plants:
                yield f"{option['label']} takes {details['plants']} plants, not {plants}"
            if resources["plants"] < plants:
                yield f"{option['label']} is offered to {player_board['name']}, who has {resources['plants']} plants"


def ways_to_pay_cover_the_cost(view: View, decision: Decision | None) -> Iterator[str]:
    """Each way to pay spends only what the Player has, heat only with Helion and never the heat the
    card itself loses, and what it spends covers the cost at what their steel and titanium are worth."""
    if decision is None or decision["kind"] != "payment":
        return
    player_board = view["players"][decision["player"]]
    in_play, resources = cards_in_play(player_board), player_board["resources"]
    steel_value = STEEL_VALUE + sum(steel for card, (steel, _) in CUBE_VALUES.items() if card in in_play)
    titanium_value = TITANIUM_VALUE + sum(titanium for card, (_, titanium) in CUBE_VALUES.items() if card in in_play)
    for option in decision["options"]:
        details = option["details"]
        paid = {part: details[part] for part in ("megacredits", "steel", "titanium", "heat")}
        worth = paid["megacredits"] + steel_value * paid["steel"] + titanium_value * paid["titanium"] + paid["heat"]
        if "paying_for" in details:
            cost = details["cost"]
        elif details.get("action"):
            cost = CARDS[details["card"]]["effects"]["action"]["pay"]["megacredits"]
        else:
            cost = card_cost(view, decision["player"], details["card"])
        if worth < cost:
            yield f"{option['label']} is worth {worth}, but the cost is {cost}"
        kept_heat = HEAT_LOST.get(details.get("card"), 0)
        if paid["heat"] > 0 and (HEAT_AS_MEGACREDITS not in in_play or paid["heat"] > resources["heat"] - kept_heat):
            yield f"{option['label']} is offered to {player_board['name']}, who may not spend that heat"
        for part, amount in paid.items():
            if not 0 <= amount <= resources[part]:
                yield f"{option['label']} is offered to {player_board['name']}, who has {resources[part]} {part}"


def tags_shown_count_the_corporation(view: View, decision: Decision | None) -> Iterator[str]:
    """The Tags on a board count those printed on its Player's Corporation."""
    for player_board in view["players"]:
        if player_board["corporation"] is None:
            continue
        for tag, printed in Counter(CARDS[player_board["corporation"]]["tags"]).items():
            if player_board["tags"][tag] < printed:
                shown = player_board["tags"][tag]
                yield f"{player_board['name']} shows {shown} {tag} Tags, but their Corporation has {printed}"


def every_card_in_exactly_one_place(view: View, decision: Decision | None) -> Iterator[str]:
    """Every Project Card is in exactly one place: the deck, the discard pile, a hand, a Player's
    played cards, the cards a Player drafts from or has kept in the Draft, the cards dealt to a
    Player to buy from in the setup or a Research phase, among which are those they have bought,
    or the cards a Player looks at or has kept while playing Business Contacts or Invention
    Contest, or using the action of Inventors' Guild or Business Network. The sizes shown agree
    with the cards."""
    project_cards = PROJECT_CARDS + (PRELUDE_PROJECT_CARDS if view["prelude"] else [])
    places: dict[str, list[str]] = {card_id: [] for card_id in project_cards}
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
        if card_id not in project_cards:
            yield f"'{card_id}' is not a Project Card, but is in {' and '.join(found)}"
        elif not found:
            yield f"'{card_id}' is nowhere"
        elif len(found) > 1:
            yield f"'{card_id}' is in {len(found)} places: {' and '.join(found)}"


def prelude_cards_stay_hidden_until_played(view: View, decision: Decision | None) -> Iterator[str]:
    """Without Prelude nobody has Prelude Cards. With it, at setup each Player was dealt 4, none dealt to
    two Players, and has kept up to 2 of them; once setup is over, those not kept are gone, and each holds
    at most 2 still to play or played, and none still to play from the Action phase on. A Prelude Card is
    in one place at most. A Decision to keep one offers those dealt and not kept, and a Decision to play
    one offers those kept."""
    seen: list[str] = []
    for player_board in view["players"]:
        name, cards, played = player_board["name"], player_board["prelude_cards"], player_board["played_prelude_cards"]
        seen += played
        if not view["prelude"]:
            if cards is not None or played:
                yield f"without Prelude, {name} has Prelude Cards"
            continue
        if cards is None:
            yield f"with Prelude, the full view shows no Prelude Cards of {name}'s"
            continue
        dealt, kept = cards["dealt"], cards["kept"]
        if not set(dealt + kept + played) <= set(PRELUDE_CARDS):
            yield f"{name} has {dealt + kept + played} as Prelude Cards, which are not all Prelude Cards"
        if view["phase"] == "setup":
            if len(dealt) != PRELUDE_CARDS_DEALT or not set(kept) <= set(dealt) or len(kept) > PRELUDE_CARDS_KEPT:
                yield f"at setup, {name} was dealt {dealt} and kept {kept}"
            seen += dealt
        else:
            seen += kept
            if dealt:
                yield f"in the {view['phase']} phase, {name} still holds the Prelude Cards {dealt} dealt to them"
            if len(kept) + len(played) > PRELUDE_CARDS_KEPT:
                yield f"{name} has {kept} still to play and {played} played, more than {PRELUDE_CARDS_KEPT}"
            if view["phase"] not in ("setup", "prelude_cards") and kept:
                yield f"in the {view['phase']} phase, {name} has {kept} still to play"
    for card_id, times in Counter(seen).items():
        if times > 1:
            yield f"the Prelude Card {card_id} is in {times} places"
    if decision is None or decision["kind"] not in ("prelude_cards", "play_prelude_card"):
        return
    cards = view["players"][decision["player"]]["prelude_cards"] or {"dealt": [], "kept": []}
    offered = [option["details"]["card"] for option in decision["options"]]
    expected = cards["kept"] if decision["kind"] == "play_prelude_card" else [
        card for card in cards["dealt"] if card not in cards["kept"]
    ]
    if offered != expected:
        yield f"Player {decision['player'] + 1} is offered the Prelude Cards {offered}, not {expected}"


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
    every so many of their Tags in play (no Tag on a played Event counts), of the Tiles in
    play, of the Tiles next to the card's own Tile (Capital's Oceans, Commercial District's
    Cities), or of the Card Resources on the card."""
    card_resources = view["players"][player]["card_resources"]
    played = [CARDS[card_id] for card_id in cards_in_play(view["players"][player])]
    tags = Counter(tag for card in played if card["type"] != "event" for tag in card["tags"])
    on_the_board = tiles_on_the_board(view)
    tiles = Counter(tile["type"] for tile in on_the_board.values())

    def count(card_id: str, of: dict[str, str]) -> int:
        ((kind, what),) = of.items()
        if kind == "adjacent":
            own_tile = [area_id for area_id, tile in on_the_board.items() if tile.get("card") == card_id]
            next_to = [next_area for area_id in own_tile for next_area in ADJACENT_AREAS.get(area_id, [])]
            return sum(1 for next_area in next_to if on_the_board.get(next_area, {}).get("type") == what)
        if kind == "card_resource":
            return card_resources[card_id]
        return {"tag": tags[what], "tiles_in_play": tiles[what]}.get(kind, 0)

    points = 0
    for card in played:
        printed = card["victory_points"]
        if isinstance(printed, int):
            points += printed
        elif printed is not None and "per" in printed:
            points += printed["points"] * (count(card["id"], printed["of"]) // printed["per"])
        elif printed is not None and count(card["id"], printed["of"]) >= printed["at_least"]:
            points += printed["points"]
    return points


def counted(count: int, thing: str, things: str | None = None) -> str:
    """"1 Award", "0 Milestones", or with `things` for an irregular plural, "2 Greeneries"."""
    return f"{count} {thing if count == 1 else things or thing + 's'}"


def tile_name(kind: str, card: str | None = None) -> str:
    """How messages name a Tile of `kind`: "City", or for the special Tile of `card`, "Nuclear
    Zone Tile"."""
    return f"{CARDS[card]['name']} Tile" if card else TILE_NAMES[kind]


def tiles_on_the_board(view: View) -> dict[str, dict[str, Any]]:
    """Every Tile on the board, by Area."""
    return {entry["area"]: entry["tile"] for entry in view["board"] if entry["tile"] is not None}


AFTER_EVERY_DECISION: tuple[Check, ...] = (
    no_negative_resources,
    production_within_its_limits,
    global_parameters_within_range,
    tiles_only_on_legal_areas,
    special_tiles_where_their_cards_put_them,
    each_reserved_area_used_only_by_its_card,
    only_legal_areas_offered,
    robotic_workforce_copies_only_your_building_cards,
    card_actions_used_once_per_generation,
    cards_cost_what_the_discounts_leave,
    discard_to_draw_offers_every_card_in_hand,
    card_resources_only_on_played_cards_that_hold_them,
    card_resource_actions_can_be_carried_out,
    cards_to_add_to_are_those_the_rules_allow,
    effects_offered_are_those_the_rules_allow,
    olympus_conference_offers_what_the_card_says,
    viral_enhancers_offers_what_the_card_says,
    targets_offered_are_those_the_rules_allow,
    at_most_three_milestones_and_awards,
    corporations_stay_hidden_until_they_are_revealed,
    first_action_comes_first,
    costs_of_standard_projects_and_greeneries_are_as_printed,
    ways_to_pay_cover_the_cost,
    tags_shown_count_the_corporation,
    every_card_in_exactly_one_place,
    prelude_cards_stay_hidden_until_played,
    every_decision_has_an_option,
)

AT_THE_END_OF_THE_GAME: tuple[Check, ...] = (score_breakdown_adds_up,)
