"""Hand-written Recorded Games as the dataset holds them, for the replay's tests: a Game's record (its setup,
Draft and buy Decisions) and its slim moves, in the wording newer versions of the logs use.

The Game: 2 Players with Prelude. Player 1 is first and takes Mining Guild, Donation and Supplier; Player 2
takes Teractor, Business Empire and Galilean Mining. Each buys 3 cards.
"""

import copy
from typing import Any

from ai.recorded_games.moves import changes

FIRST_CARDS = [
    "mine", "power_plant", "sponsors", "heat_trappers", "solar_power",
    "lichen", "tardigrades", "fish", "birds", "space_station",
]  # fmt: skip
SECOND_CARDS = [
    "comet", "research", "asteroid", "satellites", "media_group",
    "investment_loan", "great_dam", "strip_mine", "power_grid", "ironworks",
]  # fmt: skip
FIRST_BUYS = ["mine", "power_plant", "sponsors"]
SECOND_BUYS = ["satellites", "media_group", "great_dam"]

TRACKER_NAMES = {
    "m": "M€", "steel": "Steel", "titanium": "Titanium", "plants": "Plant", "energy": "Energy", "heat": "Heat",
    "m_production": "M€ Production", "steel_production": "Steel Production", "hand": "Hand Counter",
}  # fmt: skip


class RecordedGame:
    """Builds a Recorded Game move by move. Trackers given to a move are its Player's new values; the slim
    moves store each move's game state as what changed since the last, as the dataset does."""

    def __init__(self, *, conceded: bool = True, generations: int = 1) -> None:
        self.moves: list[dict[str, Any]] = []
        self.state: dict[str, Any] = {
            "generation": 1,
            "temperature": -30,
            "oxygen": 0,
            "oceans": 0,
            "player_trackers": {},
        }
        self.decisions = [
            setup(0, ["mining_guild", "ecoline"], ["donation", "supplier", "loan", "biofuels"], FIRST_CARDS,
                  "mining_guild", ["donation", "supplier"], FIRST_BUYS),
            setup(1, ["teractor", "credicor"],
                  ["business_empire", "galilean_mining", "metal_rich_asteroid", "smelting_plant"],
                  SECOND_CARDS, "teractor", ["business_empire", "galilean_mining"], SECOND_BUYS),
        ]  # fmt: skip
        self.conceded = conceded
        self.generations = generations
        self.victory_points = [0, 0]
        self.move(0, "Module: Corporate Era | Map: Tharsis | Player 1 is starting player for this generation")

    def move(self, player: int, description: str, *, action_type: str = "other", **fields: Any) -> RecordedGame:
        """A move by `player` (0 or 1). `trackers={0: {"m": 30}}` sets trackers; `generation`, `temperature`,
        `oxygen` and `oceans` set the board's."""
        for key in ("generation", "temperature", "oxygen", "oceans"):
            if key in fields:
                self.state[key] = fields.pop(key)
        for who, values in fields.pop("trackers", {}).items():
            trackers = self.state["player_trackers"].setdefault(str(who), {})
            trackers.update({TRACKER_NAMES[name]: value for name, value in values.items()})
        self.moves.append({
            "move_number": len(self.moves) + 1, "player": player, "action_type": action_type,
            "description": description, **fields, "game_state": copy.deepcopy(self.state),
        })  # fmt: skip
        return self

    def play(self, player: int, card: str, *after: str, paid: tuple[str, ...] = (), **fields: Any) -> RecordedGame:
        """A move in which `player` plays `card`: "Player 1 pays 2 Steel | Player 1 plays card Mine | …", the
        lines `paid` and `after` without their subject."""
        who = f"Player {player + 1}"
        lines = [*(f"{who} {line}" for line in paid), f"{who} plays card {card}", *(f"{who} {line}" for line in after)]
        return self.move(player, " | ".join(lines), action_type="play_card", card_played=card, **fields)

    def setup_moves(self) -> RecordedGame:
        """The setup keeps and both Players' Prelude Cards, played as the log gives them."""
        second = ["Teractor", "Satellites", "Media Group", "Great Dam", "Business Empire", "Galilean Mining"]
        first = ["Mining Guild", "Mine", "Power Plant", "Sponsors", "Donation", "Supplier"]
        return (
            self.move(1, keeps("Player 2", second), action_type="draft")
            .move(0, keeps("Player 1", first) + " | Player 1 pays 9 M€")
            .play(0, "Donation", "gains 21 M€ (immediate effect of Donation)")
            .play(0, "Supplier", "increases Energy Production by 2", "gains 4 Steel")
            .play(1, "Business Empire", "increases M€ Production by 6", "pays 6 M€")
            .play(1, "Galilean Mining", "increases Titanium Production by 2", "pays 5 M€")
        )

    def game(self) -> dict[str, Any]:
        """The Game's record, as read_games() gives it."""
        return {
            "game": "replay-test", "prelude": True, "conceded": self.conceded, "generations": self.generations,
            "scraper_version": "v2025.10.07.1844", "decisions": self.decisions,
            "players": [{"rating": 500, "victory_points": points} for points in self.victory_points],
        }  # fmt: skip

    def slim(self) -> dict[str, Any]:
        """The Game's slim moves, as read_moves() gives them."""
        slim_moves, previous = [], {}
        for move in self.moves:
            slim = {key: value for key, value in move.items() if key != "game_state"}
            changed = changes(previous, move["game_state"])
            if changed:
                slim["game_state"] = changed
            previous = move["game_state"]
            slim_moves.append(slim)
        return {"game": "replay-test", "moves": slim_moves}


def setup(
    player: int,
    corporations: list[str],
    prelude_cards: list[str],
    cards: list[str],
    corporation: str,
    kept: list[str],
    bought: list[str],
) -> dict[str, Any]:
    return {
        "kind": "setup", "player": player, "generation": 1, "position": 0,
        "offer": {"corporations": corporations, "prelude_cards": prelude_cards, "cards": cards},
        "picked": {"corporation": corporation, "prelude_cards": kept, "cards": bought},
    }  # fmt: skip


def keeps(who: str, names: list[str]) -> str:
    return f"{who} keeps {len(names)} cards: {', '.join(names)}"
