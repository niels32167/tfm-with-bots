"""Position encoding (spec, "Models"; ticket 12 of phase 2): a position and its Options as numbers, for models
that score each Option given the position (ADR 0002).

`encode(view, decision)` reads one Player's Player View and the Decision they answer, and nothing else, so
two positions that Player can't tell apart encode alike. A Recorded Game's Draft and buy records give the
same two dicts (ai.recorded_games.records), with what the records don't hold left out of the view: an
absent key is unknown, and the encoding marks it missing instead of guessing it. So are the Prices that need
what is missing: the Prices of Tags and cards read the hand and the Tiles, and so does how far a card is from a
Tile Requirement, so without them these are 0 and marked unknown (in `missing` for the global row, by
`facts_known` in card and Option rows), never worked out as if the hand and the board were empty.

An Encoding is four tables, each of fixed width, read from the deciding Player's side ("mine" and "theirs";
2-player Games only, as the AI plays no others):
- `globals`, one row: the Global Parameters, the phase and Decision, both Players' boards, Milestones and
  Awards, and the strategy facts of ADR 0013: the Generations left and the Prices of what Players have.
  `missing` marks, field by field, what the view didn't give.
- `cards`, one row per card the Player can see: which card (its number in `card_table()`, from 1), where it
  is (`ZONES`), whose it is, and computed facts: its cost now, Card Resources, its Price, payback and
  distance to its Requirements.
- `areas`, one row per Area in the order of `areas()`: its Tile and owner.
- `options`, one row per Option, in the Decision's order: its type and every number in its details, plus,
  for an Option that plays, keeps, buys or gives up a card, that card's Price.

Printed card facts are the same in every position, so they sit once in `card_table()` (one row per catalog
card, `CARD_FACTS`) and a model looks them up by card number, as it looks up a learned identity. Area facts
sit in `area_table()` likewise.

The format is versioned (`FORMAT_VERSION` and `layout_hash()`): every encoded file and model saves both, and
`check_format` refuses one made with another layout.

Per-card statistics from Recorded Games (keep rates and the like) are not in this version: they need the
training Games, which ticket 13 sets apart from the held-out ones.
"""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache
from typing import Any, NamedTuple

from ai.controller import board_layout, card_catalog
from ai.prices import DEFAULT, Prices, generations_left, steps_left

# Bump by hand whenever what a field means changes; `layout_hash` catches changes to the fields themselves.
FORMAT_VERSION = 1

PLAYERS = 2

RESOURCES = ("megacredits", "steel", "titanium", "plants", "energy", "heat")
GLOBAL_PARAMETERS = ("temperature", "oxygen", "oceans")
TAGS = ("building", "space", "science", "power", "earth", "jovian", "plant", "microbe", "animal", "city", "wild")
CARD_TYPES = ("corporation", "prelude", "automated", "active", "event")
CARD_RESOURCES = ("animal", "microbe", "science", "fighter")
PHASES = ("setup", "draft", "research", "prelude_cards", "action", "final_greenery", "over")
DECISION_KINDS = (
    "action",
    "area",
    "payment",
    "production",
    "keep_cards",
    "resources",
    "effects",
    "add_to_card",
    "corporation",
    "prelude_cards",
    "play_prelude_card",
    "play_card",
    "draft",
    "buy_cards",
    "sell_patents",
    "discard_to_draw",
    "olympus_conference",
    "viral_enhancers",
    "target",
    "final_greenery",
    "free_award",
)
TILES = ("ocean", "greenery", "city", "special")
SPECIAL_TILES = (
    "capital",
    "natural_preserve",
    "mining_area",
    "mining_rights",
    "commercial_district",
    "nuclear_zone",
    "industrial_center",
    "lava_flows",
    "mohole_area",
    "restricted_area",
    "ecological_zone",
)
# Where an Area Option's Tile may go, when not the usual Areas of its kind.
PLACEMENTS = (
    "ocean_areas",
    "land",
    "next_to_two_cities",
    "next_to_no_other_tile",
    "next_to_a_city",
    "next_to_a_greenery",
    "steel_or_titanium_bonus",
    "steel_or_titanium_bonus_next_to_own_tile",
    "volcanoes",
    "noctis_city",
    "phobos_space_haven",
    "ganymede_colony",
)
STANDARD_PROJECTS = ("sell_patents", "power_plant", "asteroid", "aquifer", "greenery", "city")
MILESTONES = ("terraformer", "mayor", "gardener", "builder", "planner")
AWARDS = ("landlord", "banker", "scientist", "thermalist", "miner")
BONUSES = ("steel", "titanium", "plant", "card")

# Where a card the Player can see is. "passed" are the cards they passed on in the Draft, known to be with
# the other Player unless since played.
ZONES = (
    "hand",
    "played",
    "played_prelude",
    "corporation",
    "corporation_dealt",
    "prelude_dealt",
    "prelude_kept",
    "buying",
    "bought",
    "drafting",
    "drafted",
    "looking_at",
    "kept",
    "passed",
    "playing",
    "next_card",
)
# Zones whose cards the Player may yet play, keep or buy: those get Prices and the other computed facts.
PRICED_ZONES = frozenset(
    {"hand", "corporation_dealt", "prelude_dealt", "prelude_kept", "buying", "bought", "drafting", "drafted"}
    | {"looking_at", "kept", "playing"}
)

# Options that play, keep, buy, sell or discard a card: their row holds that card's Price, what the Option gains
# or gives up. Other Options naming a card (using its action, paying for it, taking from it) don't.
CARD_PRICED_OPTIONS = frozenset(
    {"play_card", "choose_corporation", "keep_prelude_card", "play_prelude_card", "draft_card", "keep_card"}
    | {"buy_card", "sell_card", "discard_card"}
)

# Option types and the details each may have besides "type"; an Option with any other is refused, so that a
# new engine field can't go unencoded.
OPTION_DETAILS: dict[str, frozenset[str]] = {
    name: frozenset(keys)
    for name, keys in {
        "play_card": ("card", "cost"),
        "use_action": ("card",),
        "choose_corporation": ("card",),
        "keep_prelude_card": ("card",),
        "play_prelude_card": ("card", "playable"),
        "first_action": ("card",),
        "draft_card": ("card",),
        "keep_card": ("card",),
        "buy_card": ("card", "cost"),
        "discard_card": ("card",),
        "lower_production": ("card", "player", "production"),
        "remove_resources": ("card", "player", "resources", "stolen"),
        "move_card_resource": ("card", "player", "from", "kind"),
        "remove_card_resources": ("card", "player", "from", "kind", "amount"),
        "remove_nothing": ("card",),
        "olympus_conference": ("card", "draw"),
        "viral_enhancers": ("card", "add"),
        "sell_card": ("card", "megacredits"),
        "payment": ("card", "action", "paying_for", "cost", "megacredits", "steel", "titanium", "heat", "microbes"),
        "choose_production": ("card", "production"),
        "copy_production_box": ("card",),
        "choose_resources": ("card", "resources"),
        "choose_effects": ("card", "alternative"),
        "add_card_resources": ("card", "to", "kind", "amount"),
        "standard_project": ("project", "cost"),
        "claim_milestone": ("milestone", "cost"),
        "fund_award": ("award", "cost"),
        "convert_plants": ("plants",),
        "convert_heat": ("heat",),
        "end_turn": (),
        "pass": (),
        "done": (),
        "area": ("area", "tile", "on", "card"),
        "claim_area": ("area",),
    }.items()
}
OPTION_TYPES = tuple(OPTION_DETAILS)

# What a Payment Option pays for.
PAYING_FOR = ("card", "card_action", "standard_project", "milestone", "award", "cards_bought")
# The ways a Payment Option pays.
PAYMENT_RESOURCES = ("megacredits", "steel", "titanium", "heat", "microbes")

# Payback beyond this many Generations, or none at all, counts as never.
PAYBACK_NEVER = 20.0


def _index(names: tuple[str, ...]) -> dict[str, int]:
    return {name: number for number, name in enumerate(names)}


def _one_hot(prefix: str, names: tuple[str, ...]) -> list[str]:
    return [f"{prefix}_{name}" for name in names]


def _player_fields(side: str) -> list[str]:
    return [
        *_one_hot(f"{side}_resources", RESOURCES),
        *_one_hot(f"{side}_production", RESOURCES),
        f"{side}_terraform_rating",
        f"{side}_passed",
        f"{side}_hand_size",
        *_one_hot(f"{side}_tags", TAGS),
        f"{side}_first_action_due",
        f"{side}_terraform_rating_raised",
        f"{side}_played_cards",
        f"{side}_events",
        f"{side}_actions_used",
        *_one_hot(f"{side}_tiles", TILES),
    ]


GLOBAL_FIELDS: tuple[str, ...] = (
    "generation",
    "generations_left",
    *_one_hot("phase", PHASES),
    *_one_hot("deciding", DECISION_KINDS),
    "prelude",
    "my_turn",
    "first_player_mine",
    "actions_this_turn",
    "temperature",
    "oxygen",
    "oceans",
    "steps_left",
    "deck_size",
    "discard_size",
    "prelude_deck_size",
    "milestone_cost",
    "award_cost",
    "board_known",
    "hand_known",
    "buying_megacredits",
    "keeping_keep",
    "keeping_price",
    *(
        f"milestone_{milestone}_{fact}"
        for milestone in MILESTONES
        for fact in ("mine", "theirs", "my_count", "their_count")
    ),
    *(f"award_{award}_{fact}" for award in AWARDS for fact in ("mine", "theirs", "my_count", "their_count")),
    *_player_fields("my"),
    *_player_fields("their"),
    "price_victory_point",
    "price_megacredit",
    *_one_hot("price_production", RESOURCES),
    *_one_hot("price_resource", RESOURCES),
    "price_terraform_rating",
    "price_card_drawn",
    "price_ocean",
    "price_city",
    "price_greenery",
    *_one_hot("price_tag", TAGS),
)

CARD_FIELDS: tuple[str, ...] = (
    "card",
    "zone",
    "mine",
    "cost",
    "card_resources",
    "card_resources_known",
    "action_used",
    "generations_ago",
    "price",
    "held_price",
    "requirements_share",
    "global_steps_short",
    "tags_short",
    "production_short",
    "tiles_short",
    "too_late",
    "payback",
    "facts_known",
)

AREA_FIELDS: tuple[str, ...] = ("tile", "special_tile", "mine", "theirs", "claimed_mine", "claimed_theirs")

OPTION_FIELDS: tuple[str, ...] = (
    "type",
    "card",
    "other_card",
    "area",
    "tile",
    "special_tile",
    "placement",
    "target",
    "project",
    "milestone",
    "award",
    "paying_for",
    "card_resource",
    "cost",
    *_one_hot("payment", PAYMENT_RESOURCES),
    *_one_hot("resources", RESOURCES),
    *_one_hot("production", RESOURCES),
    "amount",
    "alternative",
    "playable",
    "draw",
    "add",
    "stolen",
    "action",
    "price",
    "facts_known",
    "requirements_share",
    "payback",
)

CARD_FACTS: tuple[str, ...] = (
    *_one_hot("type", CARD_TYPES),
    "cost",
    *_one_hot("tag", (*TAGS, "event")),
    "temperature_min",
    "temperature_max",
    "oxygen_min",
    "oxygen_max",
    "oceans_min",
    "oceans_max",
    *_one_hot("tag_required", TAGS),
    "production_required",
    "tiles_required",
    "victory_points",
    "victory_points_per",
    *_one_hot("victory_points_per_card_resource", CARD_RESOURCES),
    "victory_points_per_tag",
    "victory_points_per_tile",
    *_one_hot("resources", RESOURCES),
    *_one_hot("production", RESOURCES),
    "temperature",
    "oxygen",
    "terraform_rating",
    "draw",
    *_one_hot("tiles", TILES),
    *_one_hot("holds", CARD_RESOURCES),
    "action",
    "first_action",
    "triggers",
    "harms",
    "discount",
    "per",
    "choice",
    "next_card",
    "pays_with",
    "other",
)

AREA_FACTS: tuple[str, ...] = (
    "on_mars",
    "row",
    "position",
    "reserved_ocean",
    "reserved_card",
    *_one_hot("bonus", BONUSES),
)

_PHASE = _index(PHASES)
_KIND = _index(DECISION_KINDS)
_ZONE = _index(ZONES)
_OPTION_TYPE = _index(OPTION_TYPES)
_TILE = _index(TILES)
_SPECIAL_TILE = _index(SPECIAL_TILES)
_PLACEMENT = _index(PLACEMENTS)
_PROJECT = _index(STANDARD_PROJECTS)
_MILESTONE = _index(MILESTONES)
_AWARD = _index(AWARDS)
_CARD_RESOURCE = _index(CARD_RESOURCES)
_PAYING_FOR = _index(PAYING_FOR)
_GLOBAL = _index(GLOBAL_FIELDS)
_CARD_FIELD = _index(CARD_FIELDS)
_OPTION_FIELD = _index(OPTION_FIELDS)
_CARD_FACT = _index(CARD_FACTS)

# The effect data counted only as "other": present, but too varied to summarise as numbers.
_OTHER_EFFECTS = (
    "add_to_another",
    "card_resources",
    "cube_values",
    "look_at",
    "requirement_steps",
    "reveal",
    "production_at_least",
    "claim_area",
    "greenery_discount",
    "production_choice",
    "resources_choice",
)


@cache
def card_numbers() -> dict[str, int]:
    """Each card's number in the encoding, from 1 (0 is no card), in the card catalog's order."""
    return {card: number for number, card in enumerate(card_catalog(), start=1)}


def card_number(card: str) -> int:
    return card_numbers()[card]


@cache
def cards_by_name() -> dict[str, str]:
    """Each card's id by its printed name."""
    return {printed["name"]: card for card, printed in card_catalog().items()}


def _printed_facts(printed: dict[str, Any]) -> list[float]:
    row = [0.0] * len(CARD_FACTS)

    def put(name: str, number: float) -> None:
        row[_CARD_FACT[name]] = float(number)

    put(f"type_{printed['type']}", 1)
    put("cost", printed["cost"] or 0)
    for tag in printed["tags"]:
        row[_CARD_FACT[f"tag_{tag}"]] += 1
    for requirement in printed["requirements"]:
        kind = requirement["type"]
        if kind in GLOBAL_PARAMETERS:
            for bound in ("min", "max"):
                if bound in requirement:
                    put(f"{kind}_{bound}", requirement[bound])
        elif kind == "tag":
            put(f"tag_required_{requirement['tag']}", requirement["min"])
        else:
            put(f"{kind}_required", requirement["min"])
    points = printed["victory_points"]
    if isinstance(points, int):
        put("victory_points", points)
    elif isinstance(points, dict):
        put("victory_points", points["points"])
        put("victory_points_per", points.get("per", points.get("at_least", 1)))
        of = points["of"]
        if "card_resource" in of:
            put(f"victory_points_per_card_resource_{of['card_resource']}", 1)
        elif "tag" in of:
            put("victory_points_per_tag", 1)
        else:
            put("victory_points_per_tile", 1)
    effects = printed.get("effects") or {}
    for resource in RESOURCES:
        put(f"resources_{resource}", (effects.get("resources") or {}).get(resource, 0))
        put(f"production_{resource}", (effects.get("production") or {}).get(resource, 0))
    for name in ("temperature", "oxygen", "terraform_rating", "draw"):
        put(name, effects.get(name) or 0)
    for tile in effects.get("tiles") or []:
        row[_CARD_FACT[f"tiles_{tile if isinstance(tile, str) else tile['tile']}"]] += 1
    if effects.get("holds"):
        put(f"holds_{effects['holds']}", 1)
    put("action", bool(effects.get("action")))
    put("first_action", bool(effects.get("first_action")))
    put("triggers", len(effects.get("when") or []))
    put("harms", bool(effects.get("any_player")))
    discount = effects.get("discount")
    put("discount", sum(d.get("amount", 0) for d in discount) if isinstance(discount, list) else bool(discount))
    put(
        "per",
        bool(effects.get("production_per") or effects.get("resources_per") or effects.get("terraform_rating_per")),
    )
    put("choice", len(effects.get("choice") or []))
    put("next_card", bool(effects.get("next_card")))
    put("pays_with", bool(effects.get("pay")))
    put("other", sum(bool(effects.get(name)) for name in _OTHER_EFFECTS))
    return row


@cache
def _card_basics() -> dict[str, tuple[float, float]]:
    """Each card's number and printed cost, as card rows start."""
    return {card: (float(number), float(card_catalog()[card]["cost"] or 0)) for card, number in card_numbers().items()}


@cache
def payback(card: str) -> float:
    """The Generations a card's Production takes to repay its cost, at the starting Prices of a unit of each
    Resource against a MegaCredit (ai.prices.Weights); `PAYBACK_NEVER` if it never does."""
    printed = card_catalog()[card]
    production = (printed.get("effects") or {}).get("production") or {}
    per_generation = sum(amount * DEFAULT.unit(resource) for resource, amount in production.items())
    if per_generation <= 0:
        return PAYBACK_NEVER
    return min((printed["cost"] or 0) / per_generation, PAYBACK_NEVER)


# A card row's fields after its cost, before any are filled in.
_UNPRICED = (0.0,) * (len(CARD_FIELDS) - _CARD_FIELD["cost"] - 1)


class CardFacts(NamedTuple):
    """The computed facts of a card its Player may play, keep or buy."""

    price: float
    requirements_share: float
    global_steps_short: float
    tags_short: float
    production_short: float
    tiles_short: float
    too_late: float
    payback: float


@cache
def card_table() -> tuple[tuple[float, ...], ...]:
    """The printed facts of every card (`CARD_FACTS`), by card number: row 0 is no card."""
    return ((0.0,) * len(CARD_FACTS), *(tuple(_printed_facts(printed)) for printed in card_catalog().values()))


@cache
def areas() -> tuple[str, ...]:
    """Every Area, in the order of the board in a Player View."""
    return tuple(area["area"] for area in board_layout())


@cache
def area_table() -> tuple[tuple[float, ...], ...]:
    """The printed facts of every Area (`AREA_FACTS`), in the order of `areas()`."""
    rows = []
    for area in board_layout():
        bonus = [float(area["bonus"].count(kind)) for kind in BONUSES]
        reserved = area["reserved"]
        on_mars = area["row"] is not None
        rows.append(
            (
                float(on_mars),
                float(area["row"] or 0),
                float(area["position"] or 0),
                float(reserved == "ocean"),
                float(reserved not in (None, "ocean")),
                *bonus,
            )
        )
    return tuple(rows)


@cache
def layout_hash() -> str:
    """A fingerprint of every field and vocabulary, and of the card and Area tables: it changes whenever the
    layout does, even if `FORMAT_VERSION` wasn't bumped."""
    layout = {
        "fields": [GLOBAL_FIELDS, CARD_FIELDS, AREA_FIELDS, OPTION_FIELDS, CARD_FACTS, AREA_FACTS],
        "vocabularies": [
            RESOURCES,
            GLOBAL_PARAMETERS,
            TAGS,
            CARD_TYPES,
            CARD_RESOURCES,
            PHASES,
            DECISION_KINDS,
            TILES,
            SPECIAL_TILES,
            PLACEMENTS,
            STANDARD_PROJECTS,
            MILESTONES,
            AWARDS,
            BONUSES,
            ZONES,
            sorted(PRICED_ZONES),
            sorted(CARD_PRICED_OPTIONS),
            OPTION_TYPES,
            {kind: sorted(details) for kind, details in OPTION_DETAILS.items()},
            PAYING_FOR,
            PAYMENT_RESOURCES,
            areas(),
        ],
        "cards": list(card_numbers()),
        "tables": [card_table(), area_table()],
        # The computed facts change with the Prices' weights.
        "prices": [DEFAULT.vector(), PAYBACK_NEVER],
    }
    return hashlib.sha256(json.dumps(layout).encode()).hexdigest()[:16]


def format_stamp() -> dict[str, Any]:
    """What to save with every encoded file and model: the format version and the layout hash."""
    return {"format_version": FORMAT_VERSION, "layout_hash": layout_hash()}


class FormatMismatch(ValueError):
    """An encoded file or model made with another encoding format."""


def check_format(stamp: dict[str, Any]) -> None:
    """Refuses `stamp` (saved by `format_stamp`) unless it is this format's."""
    if stamp.get("format_version") != FORMAT_VERSION or stamp.get("layout_hash") != layout_hash():
        raise FormatMismatch(
            f"made with encoding format {stamp.get('format_version')} ({stamp.get('layout_hash')}), "
            f"but this is format {FORMAT_VERSION} ({layout_hash()}): encode it again, or retrain"
        )


@dataclass(frozen=True, slots=True)
class Encoding:
    """One position and its Options as numbers: see the module's description."""

    globals: list[float]
    missing: list[float]
    cards: list[list[float]]
    areas: list[list[float]]
    options: list[list[float]]

    def global_fields(self) -> dict[str, float]:
        return dict(zip(GLOBAL_FIELDS, self.globals, strict=True))

    def missing_fields(self) -> list[str]:
        return [name for name, flag in zip(GLOBAL_FIELDS, self.missing, strict=True) if flag]

    def card(self, index: int) -> dict[str, float]:
        return dict(zip(CARD_FIELDS, self.cards[index], strict=True))

    def option(self, index: int) -> dict[str, float]:
        return dict(zip(OPTION_FIELDS, self.options[index], strict=True))

    def numbers(self) -> int:
        """How many numbers it holds."""
        return (
            len(self.globals)
            + len(self.missing)
            + len(self.cards) * len(CARD_FIELDS)
            + len(self.areas) * len(AREA_FIELDS)
            + len(self.options) * len(OPTION_FIELDS)
        )


class _Absent:
    """A key the view leaves out: unknown, as in a Recorded Game's record."""

    def __bool__(self) -> bool:
        return False


ABSENT = _Absent()


def encode(view: dict[str, Any], decision: dict[str, Any]) -> Encoding:
    """The Encoding of the position `view` shows its viewer, who answers `decision`."""
    return _Encoder(view, decision).encoding()


class _Encoder:
    def __init__(self, view: dict[str, Any], decision: dict[str, Any]) -> None:
        if len(view["players"]) != PLAYERS:
            raise ValueError(f"the encoding is for {PLAYERS}-player Games, not {len(view['players'])}")
        self.view = view
        self.decision = decision
        self.me = view["viewer"]
        self.them = 1 - self.me
        self.prices = Prices(view, self.me, generations_left(view, DEFAULT))
        # The Prices of Tags and cards read the Player's hand and the Tiles, and Tile Requirements the Tiles:
        # without them, these facts are unknown.
        self.facts_known = "board" in view and "hand" in view["players"][self.me]
        self.globals = [0.0] * len(GLOBAL_FIELDS)
        self.missing = [0.0] * len(GLOBAL_FIELDS)
        self.card_facts: dict[str, CardFacts] = {}
        self.costs = view["players"][self.me].get("card_costs") or {}
        self.tiles = self.count_tiles()

    def encoding(self) -> Encoding:
        self.put_globals()
        return Encoding(self.globals, self.missing, self.card_rows(), self.area_rows(), self.option_rows())

    # The global row.

    def put(self, name: str, number: Any) -> None:
        """Puts `number` in the global field `name`, or marks it missing if the view left it out."""
        if number is ABSENT:
            self.missing[_GLOBAL[name]] = 1.0
        else:
            self.globals[_GLOBAL[name]] = float(number or 0)

    def put_globals(self) -> None:
        view, get = self.view, self.view.get
        self.put("generation", view["generation"])
        self.put("generations_left", self.prices.generations_left)
        self.put(f"phase_{view['phase']}", 1)
        self.put(f"deciding_{self.decision['kind']}", 1)
        self.put("prelude", view["prelude"])
        current = get("current_player", ABSENT)
        self.put("my_turn", current if current is ABSENT else current == self.me)
        first = get("first_player", ABSENT)
        self.put("first_player_mine", first if first is ABSENT else first == self.me)
        self.put("actions_this_turn", get("actions_this_turn", ABSENT))
        for name in GLOBAL_PARAMETERS:
            self.put(name, view[name])
        self.put("steps_left", steps_left(view))
        for name in ("deck_size", "discard_size", "prelude_deck_size", "milestone_cost", "award_cost"):
            self.put(name, get(name, ABSENT))
        self.put("board_known", "board" in view)
        own = view["players"][self.me]
        self.put("hand_known", "hand" in own)
        buying = own.get("buying", ABSENT)
        self.put("buying_megacredits", buying and buying.get("megacredits", ABSENT))
        keeping = own.get("keeping", ABSENT)
        self.put("keeping_keep", keeping and keeping["keep"])
        self.put("keeping_price", keeping and keeping["price"])
        self.put_claims("milestone", get("milestones", ABSENT), "claimed_by")
        self.put_claims("award", get("awards", ABSENT), "funded_by")
        tiles = self.tiles
        for side, player in (("my", self.me), ("their", self.them)):
            self.put_player(side, view["players"][player], tiles[player] if tiles else ABSENT)
        self.put_prices()

    def put_claims(self, kind: str, claims: Any, by: str) -> None:
        if claims is ABSENT:
            for field, number in _GLOBAL.items():
                if field.startswith(f"{kind}_"):
                    self.missing[number] = 1.0
            return
        for claim in claims:
            name = f"{kind}_{claim[kind]}"
            self.put(f"{name}_mine", claim[by] == self.me)
            self.put(f"{name}_theirs", claim[by] == self.them)
            counts = claim.get("counts", ABSENT)
            self.put(f"{name}_my_count", counts and counts[self.me])
            self.put(f"{name}_their_count", counts and counts[self.them])

    def count_tiles(self) -> list[dict[str, int]] | None:
        if "board" not in self.view:
            return None
        counts: list[dict[str, int]] = [dict.fromkeys(TILES, 0) for _ in range(PLAYERS)]
        for area in self.view["board"]:
            tile = area["tile"]
            if tile is not None and tile["owner"] is not None:
                counts[tile["owner"]][tile["type"]] += 1
        return counts

    def put_player(self, side: str, board: dict[str, Any], tiles: Any) -> None:
        get = board.get
        for resource in RESOURCES:
            self.put(f"{side}_resources_{resource}", board["resources"][resource])
            self.put(f"{side}_production_{resource}", board["production"][resource])
        self.put(f"{side}_terraform_rating", board["terraform_rating"])
        self.put(f"{side}_passed", get("passed", ABSENT))
        self.put(f"{side}_hand_size", get("hand_size", ABSENT))
        for tag in TAGS:
            self.put(f"{side}_tags_{tag}", board["tags"].get(tag, 0))
        self.put(f"{side}_first_action_due", get("first_action_due", ABSENT))
        self.put(f"{side}_terraform_rating_raised", get("terraform_rating_raised", ABSENT))
        played = board["played_cards"]
        self.put(f"{side}_played_cards", len(played))
        catalog = card_catalog()
        self.put(f"{side}_events", sum(catalog[card]["type"] == "event" for card in played))
        used = get("used_actions", ABSENT)
        self.put(f"{side}_actions_used", used if used is ABSENT else len(used))
        for tile in TILES:
            self.put(f"{side}_tiles_{tile}", tiles if tiles is ABSENT else tiles[tile])

    def put_prices(self) -> None:
        prices = self.prices
        self.put("price_victory_point", prices.victory_point())
        self.put("price_megacredit", prices.megacredit())
        for resource in RESOURCES:
            self.put(f"price_production_{resource}", prices.production(resource))
            self.put(f"price_resource_{resource}", prices.resource(resource))
        self.put("price_terraform_rating", prices.terraform_rating())
        self.put("price_card_drawn", prices.card_drawn())
        self.put("price_ocean", prices.ocean())
        self.put("price_city", prices.city())
        self.put("price_greenery", prices.greenery())
        for tag in TAGS:
            self.put(f"price_tag_{tag}", prices.tag(tag) if self.facts_known else ABSENT)

    # The card rows.

    def card_rows(self) -> list[list[float]]:
        rows: list[list[float]] = []
        view = self.view
        for player in (self.me, self.them):
            board = view["players"][player]
            mine = player == self.me
            resources = board.get("card_resources", ABSENT)
            used = board.get("used_actions", ABSENT)
            self.add_cards(rows, "hand", mine, board.get("hand") or ())
            for card in board["played_cards"]:
                row = self.card_row(card, "played", mine)
                self.put_card_resources(row, card, resources)
                if used is not ABSENT:
                    row[_CARD_FIELD["action_used"]] = float(card in used)
                rows.append(row)
            self.add_cards(rows, "played_prelude", mine, board.get("played_prelude_cards") or ())
            if board.get("corporation"):
                row = self.card_row(board["corporation"], "corporation", mine)
                self.put_card_resources(row, board["corporation"], resources)
                rows.append(row)
            if board.get("next_card"):
                rows.append(self.card_row(board["next_card"], "next_card", mine))
            choosing = board.get("choosing_corporation")
            if choosing:
                self.add_cards(rows, "corporation_dealt", mine, choosing["dealt"])
            preludes = board.get("prelude_cards")
            if preludes:
                self.add_cards(rows, "prelude_dealt", mine, [c for c in preludes["dealt"] if c not in preludes["kept"]])
                self.add_cards(rows, "prelude_kept", mine, preludes["kept"])
            buying = board.get("buying")
            if buying:
                self.add_cards(rows, "buying", mine, [c for c in buying["dealt"] if c not in buying["bought"]])
                self.add_cards(rows, "bought", mine, buying["bought"])
            drafting = board.get("drafting")
            if drafting:
                self.add_cards(rows, "drafting", mine, drafting["picking_from"])
                self.add_cards(rows, "drafted", mine, drafting["kept"])
            keeping = board.get("keeping")
            if keeping:
                self.add_cards(rows, "looking_at", mine, keeping["looking_at"])
                self.add_cards(rows, "kept", mine, keeping["kept"])
            for passed in board.get("passed_in_draft") or ():
                # A card passed on and since played is a played card of the Player it went to.
                played = view["players"][passed["to"]]["played_cards"]
                for card in passed["cards"]:
                    if card in played:
                        continue
                    row = self.card_row(card, "passed", mine)
                    row[_CARD_FIELD["generations_ago"]] = float(view["generation"] - passed["generation"])
                    rows.append(row)
        for playing in (view.get("playing_card"), view.get("playing_prelude_card")):
            if playing:
                rows.append(self.card_row(playing, "playing", view.get("current_player") == self.me))
        return rows

    def add_cards(self, rows: list[list[float]], zone: str, mine: bool, cards: Any) -> None:
        rows.extend(self.card_row(card, zone, mine) for card in cards)

    def put_card_resources(self, row: list[float], card: str, resources: Any) -> None:
        if resources is ABSENT:
            return
        row[_CARD_FIELD["card_resources"]] = float(resources.get(card, 0))
        row[_CARD_FIELD["card_resources_known"]] = 1.0

    def card_row(self, card: str, zone: str, mine: bool) -> list[float]:
        number, printed_cost = _card_basics()[card]
        # What the Player would pay now, after their discounts, which the view gives for the hand only.
        cost = self.costs.get(card, printed_cost) if zone == "hand" else printed_cost
        row = [number, float(_ZONE[zone]), float(mine), float(cost), *_UNPRICED]
        if mine and zone in PRICED_ZONES:
            facts = self.facts(card)
            for name, fact in zip(CardFacts._fields, facts, strict=True):
                row[_CARD_FIELD[name]] = fact
            row[_CARD_FIELD["facts_known"]] = float(self.facts_known)
            if zone == "hand":
                row[_CARD_FIELD["held_price"]] = self.prices.card_in_hand(card)
        return row

    def facts(self, card: str) -> CardFacts:
        """The computed facts of a card the Player may play, keep or buy; those that need the hand or the Tiles are
        0 when unknown."""
        if card not in self.card_facts:
            printed = card_catalog()[card]
            global_steps, tags, production, tiles, too_late = self.distance(printed)
            self.card_facts[card] = CardFacts(
                price=self.prices.card(card) if self.facts_known else 0.0,
                requirements_share=self.prices.requirements_met(printed),
                global_steps_short=global_steps,
                tags_short=tags,
                production_short=production,
                tiles_short=tiles,
                too_late=too_late,
                payback=payback(card),
            )
        return self.card_facts[card]

    def distance(self, printed: dict[str, Any]) -> tuple[float, float, float, float, float]:
        """How far the Player is from a card's Requirements: Global Parameter steps, Tags, Production steps and
        Tiles short (0 if the board is unknown), and whether a maximum has passed."""
        view = self.view
        board = view["players"][self.me]
        steps = tags = production = tiles = 0.0
        too_late = 0.0
        for requirement in printed["requirements"]:
            kind = requirement["type"]
            if kind in GLOBAL_PARAMETERS:
                step = 2 if kind == "temperature" else 1
                if "min" in requirement:
                    steps += max(requirement["min"] - view[kind], 0) / step
                if "max" in requirement and view[kind] > requirement["max"]:
                    too_late = 1.0
            elif kind == "tag":
                have = board["tags"].get(requirement["tag"], 0) + board["tags"].get("wild", 0)
                tags += max(requirement["min"] - have, 0)
            elif kind == "production":
                production += max(requirement["min"] - board["production"][requirement["resource"]], 0)
            elif kind == "tiles" and self.tiles:
                tiles += max(requirement["min"] - self.tiles[self.me][requirement["tile"]], 0)
        return steps, tags, production, tiles, too_late

    # The Area rows.

    def area_rows(self) -> list[list[float]]:
        if "board" not in self.view:
            return [[0.0] * len(AREA_FIELDS) for _ in areas()]
        rows = []
        for area in self.view["board"]:
            tile = area["tile"]
            claimed = area["claimed_by"]
            if tile is None:
                rows.append([0.0, 0.0, 0.0, 0.0, float(claimed == self.me), float(claimed == self.them)])
                continue
            owner = tile["owner"]
            special = tile.get("card")
            rows.append(
                [
                    float(_TILE[tile["type"]] + 1),
                    float(_SPECIAL_TILE[special] + 1) if special else 0.0,
                    float(owner == self.me),
                    float(owner == self.them),
                    float(claimed == self.me),
                    float(claimed == self.them),
                ]
            )
        return rows

    # The Option rows.

    def option_rows(self) -> list[list[float]]:
        return [self.option_row(option["details"]) for option in self.decision["options"]]

    def option_row(self, details: dict[str, Any]) -> list[float]:
        kind = details["type"]
        allowed = OPTION_DETAILS.get(kind)
        if allowed is None or not details.keys() - {"type"} <= allowed:
            raise ValueError(f"an Option the encoding doesn't know: {details}")
        row = [0.0] * len(OPTION_FIELDS)

        def put(name: str, number: float) -> None:
            row[_OPTION_FIELD[name]] = float(number)

        put("type", _OPTION_TYPE[kind])
        card = details.get("card")
        if kind == "area":
            put("area", areas().index(details["area"]) + 1)
            put("tile", _TILE[details["tile"]] + 1)
            if card:
                put("special_tile", _SPECIAL_TILE[card] + 1)
            if details.get("on"):
                put("placement", _PLACEMENT[details["on"]] + 1)
            card = None
        elif kind == "claim_area":
            put("area", areas().index(details["area"]) + 1)
        if card:
            put("card", card_number(card))
        if card and kind in CARD_PRICED_OPTIONS:
            facts = self.facts(card)
            put("price", facts.price)
            put("facts_known", self.facts_known)
            put("requirements_share", facts.requirements_share)
            put("payback", facts.payback)
        other = details.get("from") or details.get("to")
        if other:
            put("other_card", card_number(other))
        if "player" in details:
            put("target", 1 if details["player"] == self.me else 2)
        if kind == "standard_project":
            put("project", _PROJECT[details["project"]] + 1)
        if kind == "claim_milestone":
            put("milestone", _MILESTONE[details["milestone"]] + 1)
        if kind == "fund_award":
            put("award", _AWARD[details["award"]] + 1)
        if "kind" in details:
            put("card_resource", _CARD_RESOURCE[details["kind"]] + 1)
        put("cost", details.get("cost", 0))
        for resource in RESOURCES:
            put(f"resources_{resource}", (details.get("resources") or {}).get(resource, 0))
            put(f"production_{resource}", (details.get("production") or {}).get(resource, 0))
        # How many: Card Resources moved, plants or heat converted, MegaCredits a sold card brings.
        amounts = {"convert_plants": "plants", "convert_heat": "heat", "sell_card": "megacredits"}
        put("amount", details.get(amounts.get(kind, "amount"), 0))
        if kind == "payment":
            self.put_payment(details, put)
        put("alternative", details.get("alternative", 0))
        put("playable", details.get("playable", False))
        put("draw", details.get("draw", False))
        put("add", details.get("add", False))
        put("stolen", details.get("stolen", False))
        put("action", details.get("action", False))
        return row

    def put_payment(self, details: dict[str, Any], put: Callable[[str, float], None]) -> None:
        for paid in PAYMENT_RESOURCES:
            put(f"payment_{paid}", details.get(paid, 0))
        paying_for = details.get("paying_for")
        if paying_for is None:
            put("paying_for", _PAYING_FOR["card_action" if details.get("action") else "card"] + 1)
            return
        kind, field, number = _paying_for(paying_for)
        put("paying_for", _PAYING_FOR[kind] + 1)
        put(field, number)


def _paying_for(text: str) -> tuple[str, str, int]:
    """What a Payment Option's `paying_for` names ("2 cards", "the Asteroid Standard Project", "the Mayor
    Milestone", "the Banker Award", or a Prelude Card's price by its name, "Aquifer Turbines"): its kind in
    `PAYING_FOR`, and the Option field and number that say which or how many."""
    if text in cards_by_name():
        return "card", "card", card_number(cards_by_name()[text])
    words = text.split()
    named = "_".join(words[1:-2] if words[-1] == "Project" else words[1:-1]).lower()
    if words[-1] in ("card", "cards"):
        return "cards_bought", "amount", int(words[0])
    if words[-1] == "Project":
        return "standard_project", "project", _PROJECT[named] + 1
    if words[-1] == "Milestone":
        return "milestone", "milestone", _MILESTONE[named] + 1
    if words[-1] == "Award":
        return "award", "award", _AWARD[named] + 1
    raise ValueError(f"a Payment for something the encoding doesn't know: {text!r}")
