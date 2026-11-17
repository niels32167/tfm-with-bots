"""Prices (CONTEXT.md): what something is worth in MegaCredits at a given moment, to one Player, read from
their Player View. They depend on the Generations left and on the Player's cards.

The Generations left are estimated once from a Player View and then held fixed: a Controller that
compares a Decision's Options must price all of them with the same estimate. Otherwise each step of
terraforming shortens the estimate, lowers the worth of everything its Player owns, and the Player
refuses to terraform (spec, "What we measured"). So a `Prices` is made once per Decision, from the
deciding Player's view, and then prices any position that may follow (`position`).

Knowledge goes in as Prices, never as fixed rules (ADR 0013). The numbers that judge are weights
that fitting changes, in `Weights`. The rest are the rules' own numbers (what Standard Projects cost, 8
plants to a Greenery) and a few rough guesses, named below, left out of the fit to keep it small.
"""

import math
from dataclasses import dataclass, fields
from functools import cache
from typing import Any

from ai.controller import card_catalog

RESOURCES = ("megacredits", "steel", "titanium", "plants", "energy", "heat")

# The steps each Global Parameter takes from the start to its goal.
TEMPERATURE_STEPS, OXYGEN_STEPS, OCEAN_STEPS = 19, 14, 9
TEMPERATURE_GOAL, OXYGEN_GOAL, OCEAN_GOAL = 8, 14, 9

# The Generations a Prelude Game lasts from Generation 1 (spec, "What we measured"), for scaling
# what the published fit found there.
GENERATIONS_FROM_THE_START = 10.7

# Victory Points for a Milestone, and for winning a funded Award: in a 2-player Game second place
# gets none.
MILESTONE_POINTS = AWARD_POINTS = 5

# Actions that the card catalog leaves to the engine's code, as Prices read them: Robinson Industries
# raises its Player's lowest Production a step for 4 MegaCredits.
CODE_ACTIONS: dict[str, dict[str, Any]] = {"robinson_industries": {"production_lowest": 1}}

# MegaCredits a unit of steel and titanium pays towards a card with the right Tag.
METAL_PAYS = {"steel": 2, "titanium": 3}

# The cheapest Award, which a free funding saves.
FREE_AWARD_COST = 8

# What a Project Card typically costs, for another Player's hidden hand, and the most a discount on
# the next card played saves on a typical card.
TYPICAL_COST = 14

# Rough guesses, not fitted. The Global Parameters share the pace of terraforming, so the one a
# Requirement waits on rises at about a third of it.
GLOBAL_PARAMETERS = 3
# The chance of finding each Tag a card in hand still lacks before the Game ends.
TAG_CHANCE = 0.5
# What a Resource added to another card is worth, in MegaCredits.
ADDED_RESOURCE = 1.0
# What a step of leeway on a card's Global Parameter Requirement is worth, in MegaCredits: once for the
# next card, or each Generation for an effect that lasts.
REQUIREMENT_LEEWAY = 2.0
LASTING_REQUIREMENT_LEEWAY = 1.0
# The share of what the other Player loses that counts as the Player's gain: they may not have had it
# to lose, or may make it up.
HARM_SHARE = 0.5
# Triggers per Generation, for Triggers not counted from cards or Tiles.
STANDARD_PROJECT_TRIGGERS = 0.5
PLACEMENT_BONUS_TRIGGERS = 0.3
OTHER_TRIGGERS = 0.5

# How often a Tile of each kind is placed per Generation in a 2-player Game, by anyone: a Game with
# Prelude has 9 Oceans in about 10.7 Generations, and Players place somewhat more Greeneries and
# Cities. For Triggers on Tiles placed.
TILES_PER_GENERATION = {"ocean": 0.85, "city": 1.0, "greenery": 1.6}


@dataclass(frozen=True)
class Weights:
    """The numbers Prices are made from, fitted.

    Starting values came from the published fit for Generation 1 of Prelude Games (spec, "Prices"): a
    MegaCredit Production step there is worth 5.7, and the other Resources' steps are worth so many
    times as much (steel 10, titanium 14, plants 9, energy 7, heat 4.5); a card at setup 4. The values
    below are the mean of a separable CMA-ES over Matches against the starting values (ai.fit_prices:
    14 generations of 10 candidates, 100 Games each), rounded to 3 figures; each comment gives the
    starting value. The fitted weights won 63.3% (60.3%–66.2%) of 1,000 Games against the starting
    ones. `discount` and `end_megacredit` stopped at their bounds in ai.fit_prices.UPPER.
    """

    # What a MegaCredit one Generation from now is worth now: money now buys cards that pay. Start 0.9.
    discount: float = 0.97
    # Global Parameter steps raised per Generation, before the Game shows its own pace; and how many
    # Generations of that pace count against the pace seen so far. Start 4.2 and 2.
    pace: float = 4.57
    pace_weight: float = 4.44
    # What a unit of each Resource is worth, against a MegaCredit, when it arrives by Production. Start
    # steel 1.75, titanium 2.46, plants 1.58, energy 1.23, heat 0.79.
    steel: float = 1.84
    titanium: float = 2.38
    plants: float = 1.54
    energy: float = 1.28
    heat: float = 0.849
    # What a Victory Point is worth in the last Generation, about what Standard Projects charge for
    # one, and what it loses each Generation further from the end: the published fit rates one at
    # only 1.5 in Generation 1. Start 10 and 0.83.
    end_victory_point: float = 13.3
    victory_point_decay: float = 0.834
    # What a MegaCredit kept for a card in hand is worth in the last Generation. Start 0.6; the fit
    # took it to 1, as money that no card needs is priced apart (`Prices.surplus_megacredit`).
    end_megacredit: float = 1.0
    # What a kept MegaCredit is worth above 1 before then: spending now forgoes a better buy later.
    # Start 0.05.
    spending: float = 0.0283
    # Plants and heat kept are worth this share of the Greenery or Temperature step 8 of them make.
    # Start 0.85.
    conversion: float = 0.605
    # What a Tag is worth in Generation 1 for what it may bring later, science and the rest; the
    # published fit has 3.6 and 1. It falls as the Game nears its end.
    science_tag: float = 2.96
    other_tag: float = 0.918
    # What a Tag is worth for bringing a card in hand one Tag closer to its Requirement, over the
    # Tags still missing. Start 4.
    requirement_tag: float = 3.34
    # A card in hand: the share of what playing it would gain that holding it is worth; what a card
    # drawn is worth in Generation 1, and in how many Generations before the end that starts to fall.
    # Start 0.8, 6 and 4. The card's start departs from the published 4 for a card at setup, which the
    # check against Recorded Games found low: there a card in hand was worth about 6 MegaCredits with 5
    # Generations left (ai.recorded_games.price_check). That check moved a starting value only; the
    # fit, by Matches alone, took it on to 9.7.
    holding: float = 0.560
    card: float = 9.71
    card_horizon: float = 4.46
    # Cards played per Generation, for Triggers and discounts on the cards to come. Start 2.5; fitted,
    # it is more a price on Triggers than a count.
    cards_per_generation: float = 5.94
    # Steel and titanium kept are worth this share of what they pay for: not every unit finds a card.
    # Start 0.7.
    kept_metal: float = 0.370
    # What an Ocean's placement brings beyond its Terraform Rating step: neighbouring Oceans' and the
    # Area's bonuses. Start 2.5.
    ocean_bonus: float = 2.15
    # What a City brings beyond the Greeneries next to it: Cards and Awards that count Cities, and its
    # placement. With the Greeneries to come, the published fit's 9 for a City in Generation 1. Start 6.5.
    city_bonus: float = 9.72
    # Each Victory Point of a City's free neighbouring land, as a share of a point: Greeneries to come.
    # Start 0.25.
    city_room: float = 0.161
    # What a Milestone is worth beyond its points: claiming it shuts the other Player out. Start 6.
    milestone: float = 9.50
    # How uncertain an Award's winner is, in its count, per Generation left. Start 1.5.
    award_spread: float = 1.84
    # How much the other Player's worth counts against the Player's own. Start 1.
    opponent: float = 1.38

    def unit(self, resource: str) -> float:
        return 1.0 if resource == "megacredits" else getattr(self, resource)

    def vector(self) -> list[float]:
        return [getattr(self, field.name) for field in fields(self)]


DEFAULT = Weights()


def steps_left(view: dict[str, Any]) -> int:
    """The Global Parameter steps still to raise before the Game ends."""
    return (
        max(TEMPERATURE_GOAL - view["temperature"], 0) // 2
        + max(OXYGEN_GOAL - view["oxygen"], 0)
        + max(OCEAN_GOAL - view["oceans"], 0)
    )


def generations_left(view: dict[str, Any], weights: Weights = DEFAULT) -> float:
    """The Production phases still to come, this Generation's included: 1 once the Game ends this
    Generation. Estimated from the steps left and the pace seen so far, starting from `weights.pace`."""
    done = TEMPERATURE_STEPS + OXYGEN_STEPS + OCEAN_STEPS - steps_left(view)
    pace = (done + weights.pace * weights.pace_weight) / (view["generation"] - 1 + weights.pace_weight)
    return 1 + steps_left(view) / max(pace, 0.5)


def annuity(discount: float, generations: float) -> float:
    """What 1 a Generation is worth now, paid at each of the next `generations` Generations' ends."""
    if generations <= 0:
        return 0.0
    return discount * (1 - discount**generations) / (1 - discount)


@cache
def project_cards() -> list[dict[str, Any]]:
    return [card for card in card_catalog().values() if card["type"] in ("automated", "active", "event")]


@cache
def share_of_cards(tag: str | None = None, kind: str | None = None, cost_at_least: int = 0) -> float:
    """The share of Project Cards with `tag` and of `kind`, and costing at least so much: how likely
    the next card played is to be one."""
    cards = project_cards()
    matching = [
        card
        for card in cards
        if (tag is None or tag in card["tags"])
        and (kind is None or card["type"] == kind)
        and (card["cost"] or 0) >= cost_at_least
    ]
    return len(matching) / len(cards)


def has_victory_points(printed: dict[str, Any]) -> bool:
    """Whether a card shows a Victory Point icon that isn't negative."""
    points = printed["victory_points"]
    return isinstance(points, dict) or (isinstance(points, (int, float)) and points >= 0)


@cache
def share_of_cards_with_victory_points() -> float:
    cards = project_cards()
    return sum(1 for card in cards if has_victory_points(card)) / len(cards)


@cache
def neighbours() -> dict[str, tuple[str, ...]]:
    """The Areas next to each Area on Mars, counted as the engine does: in half-Areas from the left
    edge of the widest row, neighbours in the rows above and below are one half-Area to either side,
    and those in the same row two."""
    rows = [5, 6, 7, 8, 9, 8, 7, 6, 5]
    letters = "ABCDEFGHJ"
    at: dict[tuple[int, int], str] = {}
    for row, length in enumerate(rows):
        for position in range(1, length + 1):
            at[(row, 2 * position + 9 - length)] = f"{letters[row]}{position}"
    steps = [(-1, -1), (-1, 1), (0, -2), (0, 2), (1, -1), (1, 1)]
    return {
        area: tuple(at[(row + down, column + across)] for down, across in steps if (row + down, column + across) in at)
        for (row, column), area in at.items()
    }


def trigger_condition(on: str | dict[str, Any]) -> dict[str, Any]:
    """A Trigger's "on", always as a dict: some are a bare word, such as "standard_project"."""
    return {on: True} if isinstance(on, str) else on


@dataclass(frozen=True)
class PricedPosition:
    """What a position is worth to one Player, in MegaCredits, part by part."""

    parts: dict[str, float]

    @property
    def total(self) -> float:
        return sum(self.parts.values())


class Prices:
    """The Prices for one Player at one moment, with the Generations left held fixed. `view` is what
    the Prices are read from: the Player's own view, whose hand gives Tags their context."""

    def __init__(self, view: dict[str, Any], player: int, generations_left: float, weights: Weights = DEFAULT):
        self.view = view
        self.player = player
        self.generations_left = generations_left
        self.weights = weights
        self.cards: dict[str, float] = {}
        self.persisting: dict[str, float] = {}
        self.money_needed: float | None = None
        self.tags: dict[tuple[str, int], float] = {}
        self.prelude: float | None = None

    @staticmethod
    def of(view: dict[str, Any], player: int | None = None, weights: Weights = DEFAULT) -> Prices:
        """The Prices for `player` (the viewer by default), with the Generations left estimated from
        `view`."""
        return Prices(view, view["viewer"] if player is None else player, generations_left(view, weights), weights)

    # The Prices of what a Player has.

    def victory_point(self) -> float:
        """A Victory Point, which only counts at the end: worth more the nearer the end is."""
        return self.weights.end_victory_point * self.weights.victory_point_decay ** (self.generations_left - 1)

    def megacredit(self) -> float:
        """A MegaCredit kept: a little over 1, as spending it now forgoes a better buy later, until the
        last Generation, when what isn't spent is lost."""
        last = min(max(2 - self.generations_left, 0.0), 1.0)
        return 1 + self.weights.spending - last * (1 + self.weights.spending - self.weights.end_megacredit)

    def megacredits(self, amount: int, player: int, board: dict[str, Any]) -> float:
        """MegaCredits kept: each worth `megacredit()` up to what the Player's worthwhile cards in hand
        cost, and the rest worth what the best Standard Project makes of them. Money nothing in hand
        needs is only worth what it can still buy."""
        needed = min(amount, self.needed(player, board))
        return needed * self.megacredit() + (amount - needed) * self.surplus_megacredit()

    def needed(self, player: int, board: dict[str, Any]) -> float:
        """What the cards in a Player's hand that are worth playing cost; for another Player's hidden
        hand, a typical card's cost each."""
        if player != self.player or board["hand"] is None:
            return board["hand_size"] * TYPICAL_COST
        if self.money_needed is None:
            own = self.board()
            costs = own["card_costs"] or {}
            self.money_needed = sum(
                costs.get(card, card_catalog()[card]["cost"] or 0)
                for card in own["hand"] or []
                if self.card_in_hand(card) > self.megacredit()
            )
        return self.money_needed

    def surplus_megacredit(self) -> float:
        """A MegaCredit beyond what the hand needs: a share of the best that a Standard Project turns
        one into, and never more than one kept for cards."""
        best = max(
            self.step("temperature") / 14,
            self.ocean() / 18,
            self.greenery() / 23,
            self.city() / 25,
            self.production("energy") / 11,
        )
        return min(self.weights.conversion * best, self.megacredit())

    def production(self, resource: str) -> float:
        """A Production step of `resource`: what it brings at each Production phase still to come
        that leaves time to use it. Plants still count in the last one, as they become a Greenery."""
        paid = self.generations_left - (0 if resource == "plants" else 1)
        return self.weights.unit(resource) * annuity(self.weights.discount, paid)

    def terraform_rating(self) -> float:
        """A Terraform Rating step: a Victory Point, and a MegaCredit at each Production phase."""
        return self.victory_point() + self.production("megacredits")

    def step(self, parameter: str) -> float:
        """Raising a Global Parameter one step: a Terraform Rating step, if it isn't at its goal."""
        goal, now = {
            "temperature": (TEMPERATURE_GOAL, self.view["temperature"]),
            "oxygen": (OXYGEN_GOAL, self.view["oxygen"]),
            "oceans": (OCEAN_GOAL, self.view["oceans"]),
        }[parameter]
        return self.terraform_rating() if now < goal else 0.0

    def greenery(self) -> float:
        """A Greenery: its Victory Point, and the oxygen step it raises."""
        return self.victory_point() + self.step("oxygen")

    def resource(self, resource: str) -> float:
        """A unit of `resource` kept. Plants and heat are worth a share of the Greenery and Temperature
        step that 8 of them make; energy becomes heat at the next Production phase."""
        if resource == "plants":
            return self.weights.conversion * self.greenery() / 8
        if resource == "heat":
            heat = self.weights.conversion * self.step("temperature") / 8
            return max(heat, self.megacredit()) if self.board()["corporation"] == "helion" else heat
        if resource == "energy":
            return max(self.resource("heat"), self.weights.energy * self.megacredit() / 2)
        if resource in METAL_PAYS:
            more = (self.board()["corporation"] and self.cube_price(resource)) or 0
            return self.weights.kept_metal * (METAL_PAYS[resource] + more) * self.megacredit()
        return self.weights.unit(resource) * self.megacredit()

    def cube_price(self, resource: str) -> int:
        """How much more each steel or titanium pays for the Player, from their cards in play."""
        board = self.board()
        in_play = [*board["played_cards"], *([board["corporation"]] if board["corporation"] else [])]
        return sum(
            ((card_catalog()[card].get("effects") or {}).get("cube_values") or {}).get(resource, 0) for card in in_play
        )

    def card_drawn(self) -> float:
        """A card drawn to the hand, before anyone knows which: worth less near the end."""
        return self.weights.card * min(1.0, max(self.generations_left - 1, 0.25) / self.weights.card_horizon)

    def uses_left(self) -> float:
        """An action's uses in the Generations to come. This Generation's use is no asset: it is gained by
        using the action, and lost at the Generation's end if not used."""
        return annuity(self.weights.discount, self.generations_left - 1)

    def ocean(self) -> float:
        """An Ocean Tile: its oxygen-free Terraform Rating step and the MegaCredits for its neighbours."""
        return self.step("oceans") + self.weights.ocean_bonus * self.megacredit()

    def city(self) -> float:
        """A City to be placed, before its neighbours are known: the Greeneries that will come next to
        its 6 free neighbours, and what Cities bring besides. Once placed, `worth` counts the same."""
        return self.victory_point() * 6 * self.weights.city_room + self.weights.city_bonus * self.megacredit()

    def tag(self, tag: str, player: int | None = None) -> float:
        """A Tag in play for `player` (the Prices' own Player by default): what it may bring later, how
        much closer it brings the Requirements of cards in hand, and the Victory Points of played cards
        that count it. Read from the Prices' own view, so that a card drawn in a Sampled Position
        doesn't move it; another Player's hidden hand gives it no context."""
        player = self.player if player is None else player
        if (tag, player) not in self.tags:
            self.tags[(tag, player)] = self.tag_now(tag, self.view["players"][player])
        return self.tags[(tag, player)]

    def tag_now(self, tag: str, board: dict[str, Any]) -> float:
        later = self.weights.science_tag if tag == "science" else self.weights.other_tag
        price = later * max(self.generations_left - 1, 0) / (GENERATIONS_FROM_THE_START - 1)
        have = board["tags"]
        for card in board["hand"] or []:
            for requirement in card_catalog()[card]["requirements"]:
                if requirement["type"] == "tag" and requirement["tag"] == tag:
                    missing = requirement["min"] - have.get(tag, 0) - have.get("wild", 0)
                    if missing > 0:
                        price += self.weights.requirement_tag / missing
        for card in board["played_cards"]:
            points = card_catalog()[card]["victory_points"]
            if isinstance(points, dict) and points["of"].get("tag") == tag:
                price += self.victory_point() * points["points"] / points["per"]
        return price

    # What cards are worth.

    def card(self, card: str) -> float:
        """What playing `card` now would bring the Player, before its cost: its effects, the payback of
        its Production, its Victory Points and its Tags, and what it triggers on cards in play."""
        if card not in self.cards:
            printed = card_catalog()[card]
            effects = printed.get("effects") or {}
            price = self.effects(effects) + self.persisting_price(card)
            if printed["type"] != "event":
                price += sum(self.tag(tag) for tag in printed["tags"])
            if printed["type"] == "corporation" and effects.get("first_action"):
                price += self.effects(effects["first_action"])
            price += self.triggered_by(printed)
            self.cards[card] = price
        return self.cards[card]

    def card_in_hand(self, card: str) -> float:
        """A card held: a share of what playing it would gain over its cost, less when its
        Requirements are still far off, and at least what selling it brings."""
        printed = card_catalog()[card]
        costs = self.board()["card_costs"] or {}
        cost = costs.get(card, printed["cost"] or 0)
        gain = self.card(card) - cost * self.megacredit()
        gain *= self.requirements_met(printed)
        return max(self.weights.holding * gain, self.megacredit())

    def requirements_met(self, printed: dict[str, Any]) -> float:
        """How near the Player is to meeting a card's Requirements: 1 when met, 0 when they never will
        be, and in between as Generations of waiting discount it."""
        share = 1.0
        for requirement in printed["requirements"]:
            kind = requirement["type"]
            if kind in ("temperature", "oxygen", "oceans"):
                now = self.view[kind]
                step = 2 if kind == "temperature" else 1
                if "max" in requirement and now > requirement["max"]:
                    return 0.0
                if "min" in requirement and now < requirement["min"]:
                    steps = (requirement["min"] - now) / step
                    pace = max(steps_left(self.view), 1) / max(self.generations_left - 1, 0.5)
                    waiting = steps / (pace / GLOBAL_PARAMETERS)
                    if waiting > self.generations_left - 1:
                        return 0.0
                    share *= self.weights.discount**waiting
            elif kind == "tag":
                have = self.board()["tags"]
                missing = requirement["min"] - have.get(requirement["tag"], 0) - have.get("wild", 0)
                if missing > 0:
                    share *= TAG_CHANCE**missing
        return share

    def effects(self, effects: dict[str, Any]) -> float:
        """What a card's or an action's effects bring the Player as they happen."""
        price = 0.0
        for resource, amount in (effects.get("resources") or {}).items():
            price += amount * self.resource(resource)
        for resource, steps in (effects.get("production") or {}).items():
            price += steps * self.production(resource)
        if per := effects.get("production_per"):
            price += per["steps"] * self.count(per["of"]) // per["per"] * self.production(per["resource"])
        at_least = effects.get("production_at_least")
        if at_least and self.count(at_least["of"]) >= at_least["at_least"]:
            price += at_least["steps"] * self.production(at_least["resource"])
        if choice := effects.get("production_choice"):
            price += max(sum(steps * self.production(r) for r, steps in each.items()) for each in choice)
        if choice := effects.get("resources_choice"):
            price += max(sum(amount * self.resource(r) for r, amount in each.items()) for each in choice)
        if per := effects.get("resources_per"):
            price += per["amount"] * (self.count(per["of"]) // per["per"]) * self.resource(per["resource"])
        price += effects.get("temperature", 0) * self.step("temperature")
        price += effects.get("oxygen", 0) * self.step("oxygen")
        price += effects.get("terraform_rating", 0) * self.terraform_rating()
        if per := effects.get("terraform_rating_per"):
            price += per["steps"] * (self.count(per["of"]) // per["per"]) * self.terraform_rating()
        price += effects.get("draw", 0) * self.card_drawn()
        if reveal := effects.get("reveal"):
            price += reveal["count"] * self.card_drawn()
        price += effects.get("prelude_cards", 0) and self.prelude_played()
        if effects.get("fund_award"):
            price += FREE_AWARD_COST * self.megacredit() + AWARD_POINTS * self.victory_point() / 2
        if look := effects.get("look_at"):
            price += look.get("keep", 0) * self.card_drawn()
            price += look.get("buy", 0) * max(self.card_drawn() - 3 * self.megacredit(), 0)
        for tile in effects.get("tiles") or []:
            kind = tile if isinstance(tile, str) else tile["tile"]
            price += {"ocean": self.ocean(), "greenery": self.greenery(), "city": self.city()}.get(kind, 1.0)
        if pay := effects.get("pay"):
            price -= pay.get("megacredits", 0) * self.megacredit()
        if any_player := effects.get("any_player"):
            price += self.harm(any_player)
        if alternatives := effects.get("choice"):
            price += max(self.effects(each) for each in alternatives)
        price += ADDED_RESOURCE * sum(each.get("amount", 0) for each in effects.get("add_to_another") or [])
        if next_card := effects.get("next_card"):
            saved = min(next_card.get("discount", 0), TYPICAL_COST)
            price += saved * self.megacredit() + REQUIREMENT_LEEWAY * next_card.get("requirement_steps", 0)
        return price

    def harm(self, any_player: dict[str, Any]) -> float:
        """What taking from the other Player is worth to the Player: their loss counts against them."""
        loss = 0.0
        for resource, steps in (any_player.get("production") or {}).items():
            loss += -steps * self.production(resource)
        removals = any_player.get("remove") or any_player.get("steal") or []
        if removals:
            loss += max(
                sum(-amount * self.resource(r) for r, amount in each.items() if r in RESOURCES) for each in removals
            )
        return self.weights.opponent * max(loss, 0.0) * HARM_SHARE

    def count(self, of: dict[str, Any], board: dict[str, Any] | None = None) -> int:
        """How many of something there are, as cards count them: Tags, Tiles or Events."""
        board = self.board() if board is None else board
        if "tag" in of:
            return board["tags"].get(of["tag"], 0)
        if "tags_of_opponents" in of:
            return sum(
                other["tags"].get(of["tags_of_opponents"], 0) for other in self.view["players"] if other is not board
            )
        if "tiles_in_play" in of or "tiles_on_mars" in of:
            kind = of.get("tiles_in_play") or of.get("tiles_on_mars")
            return sum(1 for area in self.view["board"] if area["tile"] and area["tile"]["type"] == kind)
        if "events_played" in of:
            return sum(1 for card in board["played_cards"] if card_catalog()[card]["type"] == "event")
        return 0

    def persisting_price(self, card: str) -> float:
        """What a played card goes on bringing in the Generations to come: its action, its Triggers and its
        discounts. Not its Victory Points, which `worth` counts as they stand."""
        if card not in self.persisting:
            printed = card_catalog()[card]
            effects = printed.get("effects") or {}
            price = 0.0
            later = self.uses_left()
            if action := effects.get("action"):
                price += self.action_use(printed, action) * later
            for trigger in effects.get("when") or []:
                gained = self.repeated(trigger) + self.card_resource_points(printed, trigger)
                price += gained * self.trigger_rate(trigger["on"]) * later
            if discount := effects.get("discount"):
                share = share_of_cards(discount.get("tag"))
                price += discount["megacredits"] * share * self.weights.cards_per_generation * later
            for resource, more in (effects.get("cube_values") or {}).items():
                price += more * (1 + self.board()["production"][resource]) * later
            price += effects.get("requirement_steps", 0) * LASTING_REQUIREMENT_LEEWAY * later
            price += effects.get("greenery_discount", 0) * self.resource("plants") * later
            self.persisting[card] = price
        return self.persisting[card]

    def action_use(self, printed: dict[str, Any], action: dict[str, Any]) -> float:
        """What one use of an action brings on average. An alternative that removes Card Resources the
        others add can only be chosen once enough are saved up, so it is spread over the uses that
        take: Regolith Eaters raises the oxygen once in 3 uses."""
        action = {**action, **CODE_ACTIONS.get(printed["id"], {})}
        alternatives = action.get("choice") or []
        if not alternatives:
            return max(self.repeated(action) + self.card_resource_points(printed, action), 0.0)
        common = self.repeated({key: entry for key, entry in action.items() if key != "choice"})
        adding = max((each.get("card_resources", 0) for each in alternatives), default=0)
        best = 0.0
        for each in alternatives:
            once = self.repeated(each) + self.card_resource_points(printed, each)
            removed = -each.get("card_resources", 0)
            if removed > 0 and adding > 0:
                once /= removed / adding + 1
            best = max(best, once)
        return max(common + best, 0.0)

    def repeated(self, effects: dict[str, Any]) -> float:
        """What effects bring when they come again and again over the Generations left, as Triggers and
        actions do: a Production step gained partway through pays for about half as long."""
        price = self.effects(effects)
        for resource, steps in (effects.get("production") or {}).items():
            price -= steps * self.production(resource) / 2
        if effects.get("production_lowest"):
            lowest = min(self.board()["production"].get(r, 0) for r in RESOURCES)
            raised = [r for r in RESOURCES if self.board()["production"].get(r, 0) == lowest]
            price += effects["production_lowest"] * max(self.production(r) for r in raised) / 2
        return price

    def prelude_played(self) -> float:
        """A Prelude Card played, before anyone knows which: the mean of their Prices."""
        if self.prelude is None:
            preludes = [card for card, printed in card_catalog().items() if printed["type"] == "prelude"]
            self.prelude = sum(self.card(card) for card in preludes) / len(preludes)
        return self.prelude

    def card_resource_points(self, printed: dict[str, Any], effects: dict[str, Any]) -> float:
        """The Victory Points that Card Resources added to a card are worth."""
        points = printed["victory_points"]
        added = effects.get("card_resources", 0)
        if not added or not isinstance(points, dict) or "card_resource" not in points["of"]:
            return 0.0
        per = points.get("per") or points.get("at_least", 1)
        return added * points["points"] / per * self.victory_point()

    def trigger_rate(self, on: dict[str, Any]) -> float:
        """How often a Trigger fires in a Generation."""
        cards = self.weights.cards_per_generation
        on = trigger_condition(on)
        if "card_played" in on:
            return cards * share_of_cards(on["card_played"].get("tag"), on["card_played"].get("type"))
        if "tag_played" in on:
            return cards * sum(share_of_cards(tag) for tag in on["tag_played"])
        if "tag_played_by_anyone" in on:
            return 2 * cards * sum(share_of_cards(tag) for tag in on["tag_played_by_anyone"])
        if "tile_placed" in on:
            placed = on["tile_placed"]
            rate = TILES_PER_GENERATION.get(placed.get("tile"), 1.0)
            return rate / 2 if placed.get("by") == "you" else rate
        if "cost_at_least" in on:
            return cards * share_of_cards(cost_at_least=on["cost_at_least"])
        if "standard_project" in on:
            return STANDARD_PROJECT_TRIGGERS
        if "card_with_victory_points" in on:
            return cards * share_of_cards_with_victory_points()
        if "placement_bonus" in on:
            return PLACEMENT_BONUS_TRIGGERS
        return OTHER_TRIGGERS

    def triggered_by(self, printed: dict[str, Any]) -> float:
        """What playing a card triggers on the Player's cards in play."""
        price = 0.0
        board = self.board()
        in_play = list(board["played_cards"]) + ([board["corporation"]] if board["corporation"] else [])
        tags = printed["tags"]
        for card in in_play:
            for trigger in (card_catalog()[card].get("effects") or {}).get("when") or []:
                on = trigger_condition(trigger["on"])
                times = 0
                if played := on.get("card_played"):
                    if played.get("type") in (None, printed["type"]) and played.get("tag") in (None, *tags):
                        times = 1
                elif "tag_played" in on:
                    times = sum(tags.count(tag) for tag in on["tag_played"])
                elif "tag_played_by_anyone" in on:
                    times = sum(tags.count(tag) for tag in on["tag_played_by_anyone"])
                elif "card_with_victory_points" in on:
                    times = int(has_victory_points(printed))
                elif "cost_at_least" in on:
                    times = int((printed["cost"] or 0) >= on["cost_at_least"])
                if times:
                    gained = self.effects(trigger) + self.card_resource_points(card_catalog()[card], trigger)
                    price += times * gained
        return price

    # What a whole position is worth.

    def board(self) -> dict[str, Any]:
        return self.view["players"][self.player]

    def position(self, view: dict[str, Any], player: int) -> PricedPosition:
        """What `player`'s position in `view` is worth to them, part by part, at these Prices: what
        they have, and what they will score as things stand. Cards in their hand that the Prices' own
        view doesn't show are priced as cards drawn, unseen, so that a lucky draw in a Sampled
        Position doesn't sway a Decision."""
        board = view["players"][player]
        known_hand = set(self.board()["hand"] or []) if player == self.player else set()
        parts: dict[str, float] = {}
        parts["MegaCredits"] = self.megacredits(board["resources"]["megacredits"], player, board)
        parts["Resources"] = sum(board["resources"][r] * self.resource(r) for r in RESOURCES[1:])
        parts["Production"] = sum(board["production"][r] * self.production(r) for r in RESOURCES)
        parts["Terraform Rating"] = board["terraform_rating"] * self.terraform_rating()
        parts["Tiles"] = self.tiles(view, player)
        parts["Victory Points on cards"] = self.victory_points_on_cards(view, board) * self.victory_point()
        persisting = sum(self.persisting_price(card) for card in board["played_cards"])
        if board["corporation"]:
            persisting += self.persisting_price(board["corporation"])
        parts["Cards in play"] = persisting
        parts["Tags"] = sum(count * self.tag(tag, player) for tag, count in board["tags"].items() if count)
        hand = board["hand"]
        if hand is None:
            parts["Hand"] = board["hand_size"] * self.card_drawn() * self.weights.holding
        else:
            parts["Hand"] = sum(
                self.card_in_hand(card) if card in known_hand else self.card_drawn() * self.weights.holding
                for card in hand
            )
        parts["Milestones"] = sum(
            MILESTONE_POINTS * self.victory_point() + self.weights.milestone
            for milestone in view["milestones"]
            if milestone["claimed_by"] == player
        )
        parts["Awards"] = sum(
            AWARD_POINTS * self.victory_point() * self.chance_of_winning(award["counts"], player)
            for award in view["awards"]
            if award["funded_by"] is not None
        )
        return PricedPosition(parts)

    def tiles(self, view: dict[str, Any], player: int) -> float:
        """The Victory Points of `player`'s Greeneries and Cities as they stand, with the room their
        Cities have for Greeneries to come, and what Cities bring besides."""
        tile_at = {area["area"]: area["tile"] for area in view["board"]}
        points = 0.0
        cities = 0
        for area in view["board"]:
            tile = area["tile"]
            if not tile or tile.get("owner") != player:
                continue
            if tile["type"] == "greenery":
                points += 1
            elif tile["type"] == "city":
                cities += 1
                if area["area"] in neighbours():
                    around = [tile_at[next_area] for next_area in neighbours()[area["area"]]]
                    points += sum(1 for each in around if each and each["type"] == "greenery")
                    points += self.weights.city_room * sum(1 for each in around if each is None)
        return points * self.victory_point() + cities * self.weights.city_bonus * self.megacredit()

    def victory_points_on_cards(self, view: dict[str, Any], board: dict[str, Any]) -> float:
        """The Victory Points printed on a Player's played cards as things stand, Card Resources counted
        in fractions of a point, so that each one added is seen to count."""
        points = 0.0
        tile_at = {area["area"]: area["tile"] for area in view["board"]}
        for card in board["played_cards"]:
            printed = card_catalog()[card]["victory_points"]
            if isinstance(printed, (int, float)):
                points += printed
            elif isinstance(printed, dict):
                of = printed["of"]
                if "card_resource" in of:
                    held = board["card_resources"].get(card, 0)
                    if "at_least" in printed:
                        points += printed["points"] * (held >= printed["at_least"])
                    else:
                        points += printed["points"] * held / printed["per"]
                elif "adjacent" in of:
                    own = next((a for a, t in tile_at.items() if t and t.get("card") == card), None)
                    if own:
                        around = [tile_at[next_area] for next_area in neighbours().get(own, ())]
                        points += sum(1 for each in around if each and each["type"] == of["adjacent"])
                else:
                    points += printed["points"] * (self.count(of, board) // printed["per"])
        return points

    def chance_of_winning(self, counts: list[int], player: int) -> float:
        """How likely `player` is to win an Award, given each Player's count now: more certain the
        nearer the end. A tie for first wins it too."""
        best_other = max(count for index, count in enumerate(counts) if index != player)
        spread = 0.5 + self.weights.award_spread * (self.generations_left - 1)
        lead = (counts[player] - best_other + 0.5) / spread
        return 1 / (1 + math.exp(-min(max(lead, -50.0), 50.0)))

    def margin(self, view: dict[str, Any]) -> tuple[PricedPosition, PricedPosition]:
        """What a position is worth to the Player, and to the best other Player."""
        mine = self.position(view, self.player)
        others = [self.position(view, player) for player in range(len(view["players"])) if player != self.player]
        return mine, max(others, key=lambda position: position.total)
