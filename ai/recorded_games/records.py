"""A dataset Game's setup, Draft and buy records (ai/recorded_games/__init__.py) as the Decisions the engine would
ask: each as its Player saw it, a Player View and the Options, and the Option they picked. The same shape as
ai.recorded_games.replay.action_decisions() gives for the Action phases, so that both encode alike
(ai.encoding, ticket 12 of phase 2).

The records don't hold everything a Player View does. What they lack is left out of the view, never guessed,
and the encoding marks it missing (`as_recorded` shows what that is):
- at setup, who goes first, the decks' sizes, and the counts towards Milestones and Awards (which restate
  Terraform Ratings, Tags and Resources): the board and the hands are still empty;
- later also the hands (the Hand Counter is often stale), the Tiles on the board and Card Resources.

A setup record becomes the engine's chain: the Corporation, each Prelude Card kept, each card bought, and done.
A buy record likewise: each card bought, and done while another could be bought. Cards bought or kept are
picked in card-number order, as the records don't say in which order the Player picked them.
"""

from collections.abc import Callable, Iterator
from typing import Any

from ai.controller import board_layout, card_catalog
from ai.encoding import AWARDS, MILESTONES, card_numbers

# What a card costs to buy, and what the first and later Milestones and Awards cost.
CARD_COST = 3
MILESTONE_COST = 8
AWARD_COSTS = (8, 14, 20)
MOST_CLAIMS = 3

# The Player View's keys that the records never give.
UNKNOWN_KEYS = ("first_player", "deck_size", "discard_size", "prelude_deck_size")
# Those they give only at setup, when the board and the hands are still empty.
UNKNOWN_AFTER_SETUP = ("board",)
UNKNOWN_PLAYER_KEYS_AFTER_SETUP = ("hand", "hand_size", "card_costs", "card_resources")


def in_card_order(cards: list[str]) -> list[str]:
    """`cards` in card-number order, as the Player View lists them."""
    numbers = card_numbers()
    return sorted(cards, key=numbers.__getitem__)


def as_recorded(view: dict[str, Any]) -> dict[str, Any]:
    """An engine Player View cut down to what the records give of the same position: for comparing them, and
    for training on engine positions as on the records."""
    cut = {key: value for key, value in view.items() if key not in UNKNOWN_KEYS}
    cut["milestones"] = [{key: m[key] for key in ("milestone", "claimed_by")} for m in view["milestones"]]
    cut["awards"] = [{key: a[key] for key in ("award", "funded_by")} for a in view["awards"]]
    if view["phase"] != "setup":
        for key in UNKNOWN_AFTER_SETUP:
            del cut[key]
        cut["players"] = [
            {key: value for key, value in board.items() if key not in UNKNOWN_PLAYER_KEYS_AFTER_SETUP}
            for board in view["players"]
        ]
    return cut


def recorded_decisions(game: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Each Decision the records describe, in their order: "player", "generation", "kind", "view" (the
    Player's view, with what the records lack left out), "options" and "picked" (an index into them)."""
    for record in game["decisions"]:
        if record["kind"] == "setup":
            yield from setup_decisions(game, record)
        elif record["kind"] == "draft":
            yield draft_decision(game, record)
        elif record["kind"] == "buy":
            yield from buy_decisions(game, record)


def option(index: int, label: str, **details: Any) -> dict[str, Any]:
    return {"index": index, "label": label, "details": details}


def card_name(card: str) -> str:
    return card_catalog()[card]["name"]


def decision(view: dict[str, Any], kind: str, options: list[dict[str, Any]], picked: int) -> dict[str, Any]:
    player = view["viewer"]
    return {
        "player": player,
        "generation": view["generation"],
        "kind": kind,
        "view": view,
        "options": options,
        "picked": picked,
    }


def picked_index(options: list[dict[str, Any]], card: str | None) -> int:
    """The index of the Option naming `card`, or of done for None."""
    for offered in options:
        if offered["details"].get("card") == card or (card is None and offered["details"]["type"] == "done"):
            return offered["index"]
    raise ValueError(f"the records pick {card}, which isn't offered")


def other(player: int) -> int:
    """The other Player of a 2-player Game."""
    return 1 - player


def public_view(game: dict[str, Any], record: dict[str, Any], phase: str) -> dict[str, Any]:
    """What every Player sees at the record's position, and the deciding Player's own board without what only
    they see."""
    position = game["positions"][record["position"]]
    viewer = record["player"]
    claimed = {milestone: position["milestones"].get(milestone) for milestone in MILESTONES}
    funded = {award: position["awards"].get(award) for award in AWARDS}
    claims = sum(player is not None for player in claimed.values())
    fundings = sum(player is not None for player in funded.values())
    view: dict[str, Any] = {
        "viewer": viewer,
        "generation": position["generation"],
        "phase": phase,
        "prelude": game["prelude"],
        "playing_prelude_card": None,
        "playing_card": None,
        "temperature": position["temperature"],
        "oxygen": position["oxygen"],
        "oceans": position["oceans"],
        "deck": None,
        "discard": None,
        "current_player": viewer,
        "deciding": "draft" if phase == "draft" else "buy_cards",
        "actions_this_turn": 0,
        "players": [
            player_board(game, board, own=index == viewer, phase=phase)
            for index, board in enumerate(position["players"])
        ],
        "milestones": [{"milestone": milestone, "claimed_by": player} for milestone, player in claimed.items()],
        "milestone_cost": MILESTONE_COST if claims < MOST_CLAIMS else None,
        "awards": [{"award": award, "funded_by": player} for award, player in funded.items()],
        "award_cost": AWARD_COSTS[fundings] if fundings < MOST_CLAIMS else None,
        "scores": None,
    }
    if phase == "setup":
        view["board"] = [{**area, "tile": None, "claimed_by": None} for area in board_layout()]
    return view


def player_board(game: dict[str, Any], board: dict[str, Any], *, own: bool, phase: str) -> dict[str, Any]:
    """A Player's board in the Player View, from the record's position."""
    setup = phase == "setup"
    shown: dict[str, Any] = {
        "resources": dict(board["resources"]),
        "production": dict(board["production"]),
        "terraform_rating": board["terraform_rating"],
        # Every Player has passed by the Research phase, and none has at setup.
        "passed": not setup,
        "corporation": board["corporation"],
        "first_action_due": False,
        "terraform_rating_raised": False,
        "choosing_corporation": None,
        "prelude_cards": {"dealt": [], "kept": []} if own and game["prelude"] else None,
        "buying": None,
        "drafting": None,
        "passed_in_draft": None,
        "keeping": None,
        "played_cards": in_card_order(board["played"]),
        "played_prelude_cards": in_card_order(board["prelude_cards"]),
        "used_actions": [],
        "next_card": None,
        "tags": dict(board["tags"]),
    }
    if setup:
        shown |= {"hand_size": 0, "hand": [] if own else None, "card_costs": {} if own else None, "card_resources": {}}
    return shown


def setup_decisions(game: dict[str, Any], record: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """The setup chain: the Corporation, each Prelude Card kept, each card bought, and done."""
    offer, picked = record["offer"], record["picked"]
    corporations = in_card_order(offer["corporations"])
    preludes = in_card_order(offer.get("prelude_cards") or [])
    dealt = in_card_order(offer["cards"])
    chosen: str | None = None
    kept: list[str] = []
    bought: list[str] = []

    def view() -> dict[str, Any]:
        shown = public_view(game, record, "setup")
        own = shown["players"][record["player"]]
        own["choosing_corporation"] = {"dealt": corporations, "picked": chosen}
        if game["prelude"]:
            own["prelude_cards"] = {"dealt": preludes, "kept": list(kept)}
        own["buying"] = {"dealt": dealt, "bought": list(bought), "megacredits": starting_megacredits(chosen)}
        own["passed_in_draft"] = []
        return shown

    options = [
        option(i, f"Choose {card_name(card)}", type="choose_corporation", card=card)
        for i, card in enumerate(corporations)
    ]
    yield decision(view(), "corporation", options, picked_index(options, picked["corporation"]))
    chosen = picked["corporation"]
    for card in in_card_order(picked.get("prelude_cards") or []):
        offered = [prelude for prelude in preludes if prelude not in kept]
        options = [
            option(i, f"Keep {card_name(prelude)}", type="keep_prelude_card", card=prelude)
            for i, prelude in enumerate(offered)
        ]
        yield decision(view(), "prelude_cards", options, picked_index(options, card))
        kept.append(card)
    yield from buying(view, dealt, bought, in_card_order(picked["cards"]), starting_megacredits(chosen))


def starting_megacredits(corporation: str | None) -> int:
    """What a Player may spend on cards at setup: their Corporation's starting MegaCredits, once chosen."""
    return card_catalog()[corporation]["effects"]["resources"]["megacredits"] if corporation else 0


def buying(
    view: Callable[[], dict[str, Any]], dealt: list[str], bought: list[str], picks: list[str], megacredits: int
) -> Iterator[dict[str, Any]]:
    """Each card bought, then done: the engine asks while a card is left that the Player can pay for on top of
    those bought so far, with `megacredits`."""
    for card in [*picks, None]:
        unbought = [dealt_card for dealt_card in dealt if dealt_card not in bought]
        if not unbought or megacredits < CARD_COST * (len(bought) + 1):
            return
        options = [
            option(
                i, f"Buy {card_name(offered)} ({CARD_COST} MegaCredits)", type="buy_card", card=offered, cost=CARD_COST
            )
            for i, offered in enumerate(unbought)
        ]
        options.append(option(len(options), "Done", type="done"))
        yield decision(view(), "buy_cards", options, picked_index(options, card))
        if card is not None:
            bought.append(card)


def passes(record: dict[str, Any]) -> list[dict[str, Any]]:
    """The cards the Player passed on in the Draft, as the Player View lists them: to the other Player."""
    to = other(record["player"])
    return [
        {"generation": passed["generation"], "to": to, "cards": in_card_order(passed["cards"])}
        for passed in record["passed"]
    ]


def draft_decision(game: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    shown = public_view(game, record, "draft")
    own = shown["players"][record["player"]]
    offer = in_card_order(record["offer"])
    own["drafting"] = {
        "picking_from": offer,
        "kept": in_card_order(record["drafted"]),
        "passing_to": other(record["player"]),
    }
    own["passed_in_draft"] = passes(record)
    options = [option(i, f"Keep {card_name(card)}", type="draft_card", card=card) for i, card in enumerate(offer)]
    return decision(shown, "draft", options, picked_index(options, record["picked"]))


def buy_decisions(game: dict[str, Any], record: dict[str, Any]) -> Iterator[dict[str, Any]]:
    dealt = in_card_order(record["offer"])
    bought: list[str] = []
    board = game["positions"][record["position"]]["players"][record["player"]]
    # Helion pays with heat as MegaCredits.
    megacredits = board["resources"]["megacredits"]
    if board["corporation"] == "helion":
        megacredits += board["resources"]["heat"]

    def view() -> dict[str, Any]:
        shown = public_view(game, record, "research")
        own = shown["players"][record["player"]]
        own["buying"] = {"dealt": dealt, "bought": list(bought), "megacredits": megacredits}
        own["passed_in_draft"] = passes(record)
        return shown

    yield from buying(view, dealt, bought, in_card_order(record["picked"]), megacredits)
