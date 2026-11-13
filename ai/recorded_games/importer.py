"""Turns one Recorded Game's log into a dataset entry: its settings and results with anonymous Players,
each Player's setup, Draft and buy Decisions as that Player saw them, and the public positions they saw.

A log is the scraper's JSON for one Game from one Player's perspective. Nothing in it is ever run; it
is only parsed as JSON. The format of an entry is described in ai/recorded_games/__init__.py.
"""

import datetime
import hashlib
import re
from collections.abc import Callable
from typing import Any

from ai.recorded_games.names import award_id, card_id, milestone_id, prelude_card_ids

FORMAT = 1

# Board Game Arena's Terraforming Mars is younger than this; earlier dates are placeholders.
FIRST_YEAR = 2015

DRAFT_ACTIONS = {"draft", "draft_card"}

# Cards each Player drafts in a Research phase of a 2-player Game.
DRAFTED = 4

# The position at setup, before anyone has kept a card.
STARTING_STATE = {"generation": 1, "temperature": -30, "oxygen": 0, "oceans": 0}
STARTING_TERRAFORM_RATING = 20

# What some results name a Corporation.
UNKNOWN = "Unknown"

RESOURCES = ["megacredits", "steel", "titanium", "plants", "energy", "heat"]
RESOURCE_TRACKERS = dict(zip(["M€", "Steel", "Titanium", "Plant", "Energy", "Heat"], RESOURCES))
TAGS = ["building", "space", "science", "power", "earth", "jovian", "plant", "microbe", "animal", "city", "wild"]


class Skipped(Exception):
    """A log the dataset leaves out, and why: the reason, and for unknown names, which."""

    def __init__(self, reason: str, names: frozenset[str] = frozenset()) -> None:
        super().__init__(reason)
        self.reason = reason
        self.names = names


class Names:
    """Maps the log's card, Milestone and Award names to ids, remembering those it can't."""

    def __init__(self) -> None:
        self.unknown: set[str] = set()

    def card(self, name: str) -> str:
        return self.known(name, card_id(name))

    def cards(self, names: list[str] | None) -> list[str]:
        return [self.card(name) for name in names or []]

    def milestone(self, name: str) -> str:
        return self.known(f"Milestone {name}", milestone_id(name))

    def award(self, name: str) -> str:
        return self.known(f"Award {name}", award_id(name))

    def known(self, name: str, found: str | None) -> str:
        if found is None:
            self.unknown.add(name)
            return name
        return found


def anonymous(kind: str, raw_id: object, salt: bytes) -> str:
    """A stable id that can't be traced back to Board Game Arena without the salt."""
    return hashlib.sha256(salt + kind.encode() + b":" + str(raw_id).encode()).hexdigest()[:16]


def game_id(log: dict[str, Any], salt: bytes) -> str:
    """A Game's anonymous id, the same in its Decisions and its slim moves."""
    return anonymous("game", log.get("table_id") or log.get("replay_id"), salt)


def scraper_version(log: dict[str, Any]) -> str | None:
    return (log.get("metadata") or {}).get("scraper_version")


def check_kind(log: dict[str, Any]) -> None:
    """Raises Skipped unless the log is of a Game this project plays: 2 Players on Tharsis, with
    Corporate Era and the Draft, without Colonies or the Beginner Corporation. Prelude may be on or off."""
    players = len(log.get("players") or {})
    if players != 2:
        raise Skipped(f"{players} Players")
    if log.get("map") != "Tharsis":
        raise Skipped(f"map {log.get('map')}")
    if log.get("colonies_on"):
        raise Skipped("Colonies")
    if not log.get("corporate_era_on"):
        raise Skipped("no Corporate Era")
    if not log.get("draft_on"):
        raise Skipped("no Draft")
    if log.get("beginners_corporations_on"):
        raise Skipped("Beginner Corporations")


def completeness(log: dict[str, Any]) -> tuple[int, int, int, str, str]:
    """How much a log names: Players with dealt cards, moves with offers, moves with keeps, then the
    scraper version and perspective, only to make the choice independent of the files' order."""
    moves = log.get("moves") or []
    return (
        sum(bool(player.get("starting_hand")) for player in (log.get("players") or {}).values()),
        sum(bool(entry.get("card_options")) for entry in moves),
        sum(bool(entry.get("cards_kept")) for entry in moves),
        str(scraper_version(log) or ""),
        str(log.get("player_perspective") or ""),
    )


def choose_perspective(logs: list[dict[str, Any]]) -> dict[str, Any]:
    """Of several logs of one Game, each from another Player's perspective, the one to keep: the most
    complete. They count as one Game."""
    return max(logs, key=completeness)


def import_game(log: dict[str, Any], salt: bytes) -> dict[str, Any]:
    """The dataset entry for a log. Raises Skipped for a log the dataset leaves out."""
    check_kind(log)
    names = Names()
    reader = Reader(log, names)
    for move in log.get("moves") or []:
        reader.read(move)
    reader.end_research(conceded=bool(log.get("conceded")))
    players = list(log["players"].values())
    game = {
        "format": FORMAT,
        "game": game_id(log, salt),
        "date": valid_date(log.get("game_date")),
        "scraper_version": scraper_version(log),
        "prelude": bool(log.get("prelude_on")),
        "conceded": bool(log.get("conceded")),
        "generations": log.get("generations"),
        "players": [
            result(player, reader.corporation(index), won, salt)
            for index, (player, won) in enumerate(zip(players, winners(log)))
        ],
        "milestones": reader.claims("milestones", "milestone", names.milestone),
        "awards": reader.claims("awards", "award", names.award),
        "positions": reader.positions,
        "decisions": reader.setups() + reader.decisions,
    }
    if names.unknown:
        raise Skipped("unknown names", frozenset(names.unknown))
    return game


def valid_date(text: object) -> str | None:
    """The Game's date, or None for the invalid ones some logs hold, such as "0001-01-01"."""
    try:
        day = datetime.date.fromisoformat(str(text))
    except ValueError:
        return None
    return day.isoformat() if day.year >= FIRST_YEAR else None


def winners(log: dict[str, Any]) -> list[bool]:
    """Who won: the Player Board Game Arena places first. The log's winner is sometimes "Unknown" or a name
    since changed, so the name only decides when no places are given. Players sharing first place
    are neither the winner."""
    players = list(log["players"].values())
    places = [(player.get("elo_data") or {}).get("position") for player in players]
    if 1 in places:
        return [place == 1 and places.count(1) == 1 for place in places]
    named = log.get("winner")
    return [named is not None and player.get("player_name") == named for player in players]


def result(player: dict[str, Any], corporation: str | None, won: bool, salt: bytes) -> dict[str, Any]:
    """A Player's rating and result, without their name."""
    rating = player.get("elo_data") or {}
    return {
        "id": anonymous("player", player["player_id"], salt),
        "rating": rating.get("game_rank"),
        "rating_change": rating.get("game_rank_change"),
        "corporation": corporation,
        "victory_points": player.get("final_vp"),
        "points": player.get("vp_breakdown"),
        "winner": won,
    }


def is_draft_pick(move: dict[str, Any]) -> bool:
    """Whether a move is a Player drafting one card. Moves that keep cards name one in card_drafted too."""
    return (
        bool(move.get("card_drafted"))
        and not move.get("cards_kept")
        and (move.get("reason") == "draft" or move.get("action_type") in DRAFT_ACTIONS)
    )


class Reader:
    """Reads a log move by move, following what each Player could see, and makes each Player's Draft
    and buy Decisions as they saw them, and the public positions those Decisions point to."""

    def __init__(self, log: dict[str, Any], names: Names) -> None:
        self.names = names
        self.players = list(log["players"].values())
        self.ids = [player["player_id"] for player in self.players]
        self.by_name = {player.get("player_name"): player["player_id"] for player in self.players}
        self.generation = 1
        self.last_state: dict[str, Any] = {}
        self.played: dict[str, list[str]] = {pid: [] for pid in self.ids}
        self.setup_kept: dict[str, list[str]] = {}
        self.offers: dict[str, list[str] | None] = dict.fromkeys(self.ids)
        self.logged: dict[str, str | None] = dict.fromkeys(self.ids)
        self.drafted: dict[str, list[str]] = {pid: [] for pid in self.ids}
        self.bought: dict[str, list[str] | None] = dict.fromkeys(self.ids)
        self.starting_over: set[str] = set()
        self.passed: dict[str, list[dict[str, Any]]] = {pid: [] for pid in self.ids}
        self.generation_at: dict[int, int] = {}
        self.positions: list[dict[str, Any]] = [self.starting_position()]
        self.last_card: dict[str, str | None] = dict.fromkeys(self.ids)
        self.decisions: list[dict[str, Any]] = []

    def read(self, move: dict[str, Any]) -> None:
        state = move.get("game_state") or {}
        generation = state.get("generation")
        if generation and generation != self.generation:
            self.end_research()
            self.start_research(generation, state)
        if self.generation == 1:
            for pid, kept in (move.get("cards_kept") or {}).items():
                if pid in self.ids:
                    self.keep_at_setup(pid, kept)
        else:
            if is_draft_pick(move):
                self.note_pick(move)
            options = move.get("card_options") or {}
            if all(options.get(pid) for pid in self.ids):
                self.new_hands({pid: list(options[pid]) for pid in self.ids})
            self.cancels(move)
            for pid, kept in (move.get("cards_kept") or {}).items():
                if pid in self.drafted:
                    self.buy(pid, kept)
        if move.get("card_played"):
            self.play(move)
        if isinstance(move.get("move_number"), int):
            self.generation_at[move["move_number"]] = self.generation
        if state:
            self.last_state = state

    def claims(self, kind: str, key: str, name_to_id: Callable[[str], str]) -> list[dict[str, Any]]:
        """The Milestones claimed or Awards funded by the end, by whom and in which Generation, in order."""
        found = [
            (claim.get("move_number") or 0, name, claim)
            for name, claim in (self.last_state.get(kind) or {}).items()
            if claim.get("player_id") in self.ids
        ]
        return [
            {
                key: name_to_id(name),
                "player": self.ids.index(claim["player_id"]),
                "generation": self.generation_at.get(number),
            }
            for number, name, claim in sorted(found, key=lambda item: item[0])
        ]

    def start_research(self, generation: int, state: dict[str, Any]) -> None:
        """A new Generation begins: Production comes in, and its Research phase starts."""
        self.generation = generation
        self.offers = dict.fromkeys(self.ids)
        self.logged = dict.fromkeys(self.ids)
        self.drafted = {pid: [] for pid in self.ids}
        self.bought = dict.fromkeys(self.ids)
        self.starting_over = set()
        self.last_card = dict.fromkeys(self.ids)
        public = self.public_position(self.last_state or state)
        public["generation"] = generation
        for player in public["players"]:
            produce(player)
        self.positions.append(public)

    def starting_position(self) -> dict[str, Any]:
        """The position at setup, as the rules set it up. Not the log's first game state: a log may start
        after a Player has kept their cards, which their Resources and Production would show."""
        position = self.public_position(STARTING_STATE, corporations=False)
        for player in position["players"]:
            player["terraform_rating"] = STARTING_TERRAFORM_RATING
        return position

    def public_position(self, state: dict[str, Any], *, corporations: bool = True) -> dict[str, Any]:
        trackers = state.get("player_trackers") or {}
        points = state.get("player_vp") or {}
        return {
            "generation": state.get("generation") or 1,
            "temperature": state.get("temperature"),
            "oxygen": state.get("oxygen"),
            "oceans": state.get("oceans"),
            "milestones": {
                self.names.milestone(name): self.ids.index(claim["player_id"])
                for name, claim in (state.get("milestones") or {}).items()
                if claim.get("player_id") in self.ids
            },
            "awards": {
                self.names.award(name): self.ids.index(funding["player_id"])
                for name, funding in (state.get("awards") or {}).items()
                if funding.get("player_id") in self.ids
            },
            "players": [
                self.public_player(index, trackers.get(pid) or {}, points.get(pid) or {}, corporations)
                for index, pid in enumerate(self.ids)
            ],
        }

    def public_player(
        self, index: int, trackers: dict[str, int], points: dict[str, Any], corporations: bool
    ) -> dict[str, Any]:
        pid = self.ids[index]
        played = self.names.cards(self.played[pid])
        prelude_cards = set(prelude_card_ids().values())
        return {
            "corporation": self.corporation(index) if corporations else None,
            "terraform_rating": (points.get("total_details") or {}).get("tr"),
            "resources": {resource: trackers.get(name, 0) for name, resource in RESOURCE_TRACKERS.items()},
            "production": {
                resource: trackers.get(f"{name} Production", 0) for name, resource in RESOURCE_TRACKERS.items()
            },
            "tags": {tag: trackers.get(f"Count of {tag.capitalize()} tags", 0) for tag in TAGS},
            "events": trackers.get("Count of played Events cards", 0),
            "hand_counter": trackers.get("Hand Counter"),
            "played": [card for card in played if card not in prelude_cards],
            "prelude_cards": [card for card in played if card in prelude_cards],
        }

    def play(self, move: dict[str, Any]) -> None:
        """A card is played, by whoever the description says: the move's own Player is sometimes wrong."""
        card = move["card_played"]
        pid = move.get("player_id")
        for name, named in self.by_name.items():
            if name and re.search(
                rf"(^|\| ){re.escape(name)} plays card {re.escape(card)}($| \|)", move.get("description") or ""
            ):
                pid = named
        if pid in self.played and card not in self.played[pid]:
            self.played[pid].append(card)

    def corporation(self, index: int) -> str | None:
        """A Player's Corporation: as the result names it, or if that says "Unknown", as kept at setup."""
        named = self.players[index].get("corporation")
        if named and named != UNKNOWN:
            return self.names.card(named)
        corporations = self.dealt(self.ids[index]).get("corporations") or []
        kept = [name for name in self.setup_kept.get(self.ids[index], []) if name in corporations]
        return self.names.card(kept[0]) if kept else None

    def keep_at_setup(self, pid: str, kept: list[str]) -> None:
        """What a Player keeps at setup: the last keep naming one of their Corporations counts."""
        dealt = self.dealt(pid)
        if any(name in (dealt.get("corporations") or []) for name in kept):
            self.setup_kept[pid] = kept

    def dealt(self, pid: str) -> dict[str, list[str]]:
        return self.players[self.ids.index(pid)].get("starting_hand") or {}

    def setups(self) -> list[dict[str, Any]]:
        """Each Player's setup Decision, if the log names what they were dealt and kept."""
        decisions = []
        for index, pid in enumerate(self.ids):
            dealt, kept = self.dealt(pid), self.setup_kept.get(pid)
            corporations = dealt.get("corporations") or []
            if not corporations or kept is None:
                continue
            prelude_cards = dealt.get("preludes") or []
            project_cards = dealt.get("project_cards") or []
            decisions.append(
                {
                    "kind": "setup",
                    "player": index,
                    "generation": 1,
                    "position": 0,
                    "offer": {
                        "corporations": self.names.cards(corporations),
                        "prelude_cards": self.names.cards(prelude_cards),
                        "cards": self.names.cards(project_cards),
                    },
                    "picked": {
                        "corporation": self.names.card(next(name for name in corporations if name in kept)),
                        "prelude_cards": self.names.cards([name for name in prelude_cards if name in kept]),
                        "cards": self.names.cards([name for name in project_cards if name in kept]),
                    },
                }
            )
        return decisions

    def note_pick(self, move: dict[str, Any]) -> None:
        """The log says a Player drafts a card. It is credited to whoever holds it, as some picks are
        credited to the other Player, and only used if the next hands don't show the pick."""
        card = move["card_drafted"]
        holders = [pid for pid in self.ids if card in (self.offers[pid] or [])]
        if holders:
            pid = move.get("player_id") if move.get("player_id") in holders else holders[0]
            self.logged[pid] = card

    def new_hands(self, hands: dict[str, list[str]]) -> None:
        """The next hands of the Draft. In a 2-player Draft each Player passes the rest of their hand to
        the other, so a Player's pick is what their hand holds that the other's next hand doesn't. The
        log's own pick lines are sometimes missing or name the wrong card."""
        for pid in self.ids:
            offer = self.offers[pid]
            if not offer:
                continue
            passed_on = next(hand for other, hand in hands.items() if other != pid)
            picked = [card for card in offer if card not in passed_on]
            if set(passed_on) <= set(offer) and len(picked) == 1:
                self.record_pick(pid, picked[0])
            else:
                self.settle(pid)
        self.offers = hands
        self.logged = dict.fromkeys(self.ids)
        for pid, hand in hands.items():
            if len(hand) == 1:
                self.record_pick(pid, hand[0])  # The last card comes by itself; many logs have no move for it.

    def settle(self, pid: str) -> None:
        """A hand no next hands follow: the pick is the log's, if it names a card of the hand."""
        if self.logged[pid] in (self.offers[pid] or []):
            self.record_pick(pid, self.logged[pid])
        self.offers[pid] = None

    def record_pick(self, pid: str, card: str) -> None:
        """A Player drafts a card from their hand, passing the rest on. Taking the last card is no Decision."""
        offer = self.offers[pid] or [card]
        if len(offer) > 1:
            self.decisions.append(
                {
                    "kind": "draft",
                    "player": self.ids.index(pid),
                    "generation": self.generation,
                    "position": len(self.positions) - 1,
                    "pick": len(self.drafted[pid]) + 1,
                    "offer": self.names.cards(offer),
                    "picked": self.names.card(card),
                    "drafted": self.names.cards(self.drafted[pid]),
                    "passed": [dict(passed) for passed in self.passed[pid]],
                }
            )
        rest = [name for name in offer if name != card]
        if rest:
            self.passed[pid].append({"generation": self.generation, "cards": self.names.cards(rest)})
        if len(rest) == 1:
            self.last_card[self.other(pid)] = rest[0]
        self.drafted[pid].append(card)
        self.offers[pid] = None
        self.logged[pid] = None

    def other(self, pid: str) -> str:
        return next(other for other in self.ids if other != pid)

    def finish_draft(self) -> None:
        """Before buying: picks no next hands showed come from the log, and a Player still one card short
        gets the last card the other passed them, which many logs show no hand or move for."""
        for pid in self.ids:
            if self.offers[pid]:
                self.settle(pid)
        for pid in self.ids:
            card = self.last_card[pid]
            if len(self.drafted[pid]) == DRAFTED - 1 and card is not None and card not in self.drafted[pid]:
                self.drafted[pid].append(card)
            self.last_card[pid] = None

    def cancels(self, move: dict[str, Any]) -> None:
        """A Player who cancels their move starts their buy again with their next keep."""
        for part in (move.get("description") or "").split(" | "):
            if part.endswith(" cancels their move"):
                pid = self.by_name.get(part.removesuffix(" cancels their move"))
                if pid is not None:
                    self.starting_over.add(pid)

    def buy(self, pid: str, kept: list[str]) -> None:
        """A Player keeps some of their drafted cards. Logs list several cards kept at once, or one at a
        time, and repeat them in later moves: a keep of several cards is the whole buy, a keep of one
        adds to it, and after the Player cancels their move their next keep starts it again. Cards
        kept are listed in the order offered."""
        self.finish_draft()
        drafted = self.drafted[pid]
        if len(drafted) != DRAFTED or not set(kept) <= set(drafted):
            return
        bought = self.bought[pid]
        if bought is None or len(kept) > 1 or pid in self.starting_over:
            bought = []
        self.starting_over.discard(pid)
        self.bought[pid] = [name for name in drafted if name in kept or name in bought]
        self.record_buy(pid, self.bought[pid])

    def record_buy(self, pid: str, bought: list[str]) -> None:
        index = self.ids.index(pid)
        decision = {
            "kind": "buy",
            "player": index,
            "generation": self.generation,
            "position": len(self.positions) - 1,
            "offer": self.names.cards(self.drafted[pid]),
            "picked": self.names.cards(bought),
            "passed": [dict(passed) for passed in self.passed[pid]],
        }
        for earlier, made in enumerate(self.decisions):
            if (made["kind"], made["player"], made["generation"]) == ("buy", index, self.generation):
                self.decisions[earlier] = decision
                return
        self.decisions.append(decision)

    def end_research(self, conceded: bool = False) -> None:
        """At the end of a Generation: a Player who drafted but kept nothing, while the other Player's
        keep is in the log, bought nothing. Logs have no line for buying nothing. In the last
        Generation of a conceded Game, the Player may have conceded instead."""
        if self.generation < 2:
            return
        self.finish_draft()
        if conceded:
            return
        for pid in self.ids:
            others_bought = any(self.bought[other] is not None for other in self.ids if other != pid)
            if self.bought[pid] is None and len(self.drafted[pid]) == DRAFTED and others_bought:
                self.bought[pid] = []
                self.record_buy(pid, [])


def produce(player: dict[str, Any]) -> None:
    """The Production phase, on a Player's public position: energy becomes heat, then each Resource's
    Production comes in, and MegaCredits also gain the Terraform Rating."""
    resources, production = player["resources"], player["production"]
    resources["heat"] += resources["energy"]
    resources["energy"] = 0
    for resource in RESOURCES:
        resources[resource] += production[resource]
    resources["megacredits"] += player["terraform_rating"] or 0
