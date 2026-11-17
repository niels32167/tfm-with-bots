"""The Card Economy Bot (CONTEXT.md): the first strong, explainable rung of the ladder (ADR 0013). It
compares Options by their Prices (`ai.prices`).

Cards being chosen, drafted, bought or sold are priced from their printed data. Every other Option is
tried one step ahead: picked on a Sampled Position, the Bot's own follow-up Decisions (paying, placing
a Tile, choosing an effect) answered quickly, and the position that follows priced, the Bot's worth
less the other Player's. All Options of a Decision are tried on the same sample and priced with the
same estimate of the Generations left, made once from the Bot's view (see `ai.prices`).

It looks ahead only through the handle's Sampled Positions, never a copy of the real Game.
"""

from dataclasses import dataclass, field
from typing import Any

from ai.controller import Handle
from ai.prices import DEFAULT, Prices, Weights, neighbours

# Seeds for the engine are whole numbers below 2^63.
SEEDS = 1 << 63

# Decisions priced from the cards' printed data, without looking ahead.
PRICED_BY_CARD = {"corporation", "prelude_cards", "draft", "buy_cards", "sell_patents"}

# The Decisions that finish what a pick started: one step ahead ends once none of these is next.
FOLLOW_UPS = {
    "payment",
    "area",
    "production",
    "keep_cards",
    "resources",
    "effects",
    "viral_enhancers",
    "add_to_card",
    "olympus_conference",
    "discard_to_draw",
    "target",
    "sell_patents",
}

# A guard on a chain of follow-up Decisions in a Sampled Position.
MOST_FOLLOW_UPS = 50

# Board placement bonuses, by the Resource they give.
BONUSES = {"plant": "plants", "steel": "steel", "titanium": "titanium", "heat": "heat"}

# Options that keep what the Player has, priced at 0 without looking ahead: after a Pass the Game may
# run on through the Production phase, whose gains are no gain of passing's.
KEEPING = {"pass", "end_turn"}

# When Options are priced alike, the Bot keeps its choices open: it ends its Turn rather than pass,
# and is done rather than give more up.
TIE_BREAKS = {"end_turn": 2e-9, "done": 1e-9}


@dataclass(frozen=True)
class PricedOption:
    """An Option and what the Bot thought it worth: `value` against doing nothing, and `parts`, the
    Prices that changed and by how much."""

    index: int
    label: str
    price: float
    parts: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Explanation:
    """Why the Bot picked what it picked: every Option priced, best first."""

    player: int
    kind: str
    generations_left: float
    options: list[PricedOption]

    @property
    def picked(self) -> int:
        return self.options[0].index


class CardEconomyBot:
    """A Controller that picks the Option whose position it prices highest, with the Prices of `weights`
    (the fitted `ai.prices.DEFAULT` unless given). `explain` gives every Option's Price and why."""

    def __init__(self, weights: Weights = DEFAULT) -> None:
        self.weights = weights

    def pick(self, handle: Handle) -> int:
        if len(handle.decision["options"]) == 1:
            return 0
        return self.explain(handle).picked

    def explain(self, handle: Handle) -> Explanation:
        """Every Option of the handle's Decision, priced, best first."""
        prices = Prices.of(handle.player_view, handle.player, self.weights)
        decision = handle.decision
        if decision["kind"] in PRICED_BY_CARD:
            priced = [self.priced_by_card(option, prices) for option in decision["options"]]
        else:
            priced = self.priced_one_step_ahead(handle, prices)
        ranked = sorted(
            priced,
            key=lambda option: (
                -(option.price + TIE_BREAKS.get(decision["options"][option.index]["details"]["type"], 0))
            ),
        )
        return Explanation(handle.player, decision["kind"], prices.generations_left, ranked)

    def priced_by_card(self, option: dict[str, Any], prices: Prices) -> PricedOption:
        details = option["details"]
        kind = details["type"]
        card = details.get("card")
        if kind in ("choose_corporation", "keep_prelude_card"):
            parts = {"Card": prices.card(card)}
        elif kind == "draft_card":
            parts = {"Card in hand": prices.card_in_hand(card)}
        elif kind == "buy_card":
            parts = {"Card in hand": prices.card_in_hand(card), "MegaCredits": -details["cost"] * prices.megacredit()}
        elif kind == "sell_card":
            parts = {
                "Card in hand": -prices.card_in_hand(card),
                "MegaCredits": details["megacredits"] * prices.megacredit(),
            }
        else:
            parts = {}
        return PricedOption(option["index"], option["label"], sum(parts.values()), parts)

    def priced_one_step_ahead(self, handle: Handle, prices: Prices) -> list[PricedOption]:
        mine_now, other_now = prices.margin(handle.player_view)
        seed = handle.random.randrange(SEEDS)
        priced = []
        for option in handle.decision["options"]:
            if option["details"]["type"] in KEEPING:
                priced.append(PricedOption(option["index"], option["label"], 0.0))
                continue
            game = handle.sample(seed=seed)
            game.pick(option["index"])
            self.follow_up(game, handle, prices, depth=1)
            mine, other = prices.margin(game.player_view(handle.player))
            parts = {name: price - mine_now.parts[name] for name, price in mine.parts.items()}
            parts["Other Player"] = -self.weights.opponent * (other.total - other_now.total)
            priced.append(PricedOption(option["index"], option["label"], sum(parts.values()), parts))
        return priced

    def follow_up(self, game: Any, handle: Handle, prices: Prices, depth: int) -> None:
        """Answers the Bot's follow-up Decisions in a Sampled Position, until what was picked is done."""
        for _ in range(MOST_FOLLOW_UPS):
            decision = game.decision
            if decision is None or decision["player"] != handle.player or decision["kind"] not in FOLLOW_UPS:
                return
            game.pick(self.quick_pick(game, decision, handle, prices, depth))

    def quick_pick(self, game: Any, decision: dict[str, Any], handle: Handle, prices: Prices, depth: int) -> int:
        """A follow-up Decision answered without the full price of each Option where a cheap one will do:
        paying with what is worth least, and placing a Tile where its bonuses and neighbours pay most."""
        options = decision["options"]
        if len(options) == 1:
            return 0
        if decision["kind"] == "payment":
            return min(range(len(options)), key=lambda i: spent(options[i]["details"], prices))
        if decision["kind"] == "area":
            return max(range(len(options)), key=lambda i: placed(options[i]["details"], handle, prices))
        if depth <= 0:
            return 0
        margins = []
        for index in range(len(options)):
            tried = game.copy()
            tried.pick(index)
            self.follow_up(tried, handle, prices, depth - 1)
            mine, other = prices.margin(tried.player_view(handle.player))
            margins.append(mine.total - self.weights.opponent * other.total)
        return margins.index(max(margins))


def spent(payment: dict[str, Any], prices: Prices) -> float:
    """What a payment gives up."""
    price = payment.get("megacredits", 0) * prices.megacredit()
    for resource in ("steel", "titanium", "heat"):
        price += payment.get(resource, 0) * prices.resource(resource)
    return price


def placed(area: dict[str, Any], handle: Handle, prices: Prices) -> float:
    """A quick price of placing a Tile on an Area: its placement bonus, the MegaCredits for neighbouring
    Oceans, and the Victory Points it makes or gives away next to Cities and Greeneries."""
    if area.get("type") != "area":
        return 0.0
    board = {each["area"]: each for each in handle.player_view["board"]}
    here = board.get(area["area"])
    if here is None:
        return 0.0
    price = 0.0
    for bonus in here["bonus"]:
        price += prices.card_drawn() if bonus == "card" else prices.resource(BONUSES.get(bonus, "megacredits"))
    around = [board[next_area]["tile"] for next_area in neighbours().get(area["area"], ())]
    # The rules give 2 MegaCredits for each Ocean next to a Tile placed.
    price += 2 * prices.megacredit() * sum(1 for tile in around if tile and tile["type"] == "ocean")
    point = prices.victory_point()
    me = handle.player
    if area["tile"] == "greenery":
        for tile in around:
            if tile and tile["type"] == "city":
                price += point if tile.get("owner") == me else -prices.weights.opponent * point
    elif area["tile"] == "city":
        price += point * sum(1 for tile in around if tile and tile["type"] == "greenery")
        price += point * prices.weights.city_room * sum(1 for tile in around if tile is None)
    return price
