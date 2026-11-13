"""A slim copy of a kept Game's moves, so that rebuilding hands (ticket 09) and replaying Games through
the engine (ticket 10) don't need the 147 GB archive.

Players are named by their place: 0 and 1 in fields, "Player 1" and "Player 2" in descriptions. Names,
Board Game Arena ids and timestamps are left out. Each move's game state is stored as what changed
since the previous one; expand_moves() puts the whole states back.

Unlike Decision records, these moves name both Players' cards, as the logs do. They are raw material
for rebuilding what each Player could see, never training data as they stand.
"""

import re
from typing import Any

from ai.recorded_games.importer import FORMAT, anonymous, game_id

DROPPED = {"timestamp", "player_name", "claimed_by", "funded_by"}
# The fields that are text about the Players. Elsewhere a Player's name may also be a card's: "Moss".
TEXT = {"description", "reason"}
REMOVED = "-"  # In a stored game state: the keys it no longer has.


class Anonymiser:
    def __init__(self, log: dict[str, Any]) -> None:
        players = list(log["players"].values())
        self.places = {str(player["player_id"]): str(index) for index, player in enumerate(players)}
        names = sorted((player.get("player_name") or "" for player in players), key=len, reverse=True)
        self.by_name = {player.get("player_name"): f"Player {index + 1}" for index, player in enumerate(players)}
        alternatives = "|".join(re.escape(name) for name in names if name)
        self.pattern = re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)") if alternatives else None

    def text(self, text: str) -> str:
        if self.pattern is None:
            return text
        return self.pattern.sub(lambda found: self.by_name[found.group(0)], text)

    def anonymise(self, value: Any) -> Any:
        """The value with Player ids as places, names left out, and names in text as "Player 1" or 2."""
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                if key in DROPPED:
                    continue
                if key == "player_id":
                    result["player"] = int(self.places[str(item)]) if str(item) in self.places else None
                elif key in TEXT and isinstance(item, str):
                    result[key] = self.text(item)
                else:
                    result[self.places.get(key, key)] = self.anonymise(item)
            return result
        if isinstance(value, list):
            return [self.anonymise(item) for item in value]
        return value


def changes(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """What changed from one game state to the next: changed and new keys, nested dicts by their own
    changes, and the keys removed listed under "-"."""
    changed: dict[str, Any] = {}
    for key, value in after.items():
        if key not in before:
            changed[key] = value
        elif isinstance(value, dict) and isinstance(before[key], dict):
            inner = changes(before[key], value)
            if inner:
                changed[key] = inner
        elif value != before[key]:
            changed[key] = value
    removed = [key for key in before if key not in after]
    if removed:
        changed[REMOVED] = removed
    return changed


def apply(before: dict[str, Any], changed: dict[str, Any]) -> dict[str, Any]:
    after = dict(before)
    for key in changed.get(REMOVED, []):
        after.pop(key, None)
    for key, value in changed.items():
        if key == REMOVED:
            continue
        if isinstance(value, dict) and isinstance(after.get(key), dict):
            after[key] = apply(after[key], value)
        else:
            after[key] = value
    return after


def slim_moves(log: dict[str, Any], salt: bytes) -> dict[str, Any]:
    """The slim copy of a log's moves, with anonymous ids matching import_game's for the same salt."""
    anonymiser = Anonymiser(log)
    moves = []
    previous: dict[str, Any] = {}
    for move in log.get("moves") or []:
        slim = {key: value for key, value in anonymiser.anonymise(move).items() if value is not None}
        slim.pop("game_state", None)
        state = anonymiser.anonymise(move.get("game_state") or {})
        changed = changes(previous, state)
        if changed:
            slim["game_state"] = changed
        previous = state
        moves.append(slim)
    return {
        "format": FORMAT,
        "game": game_id(log, salt),
        "players": [anonymous("player", player["player_id"], salt) for player in log["players"].values()],
        "moves": moves,
    }


def expand_moves(slim: dict[str, Any]) -> list[dict[str, Any]]:
    """A slim copy's moves, each with its whole game state."""
    state: dict[str, Any] = {}
    moves = []
    for move in slim["moves"]:
        state = apply(state, move.get("game_state") or {})
        moves.append({**move, "game_state": state})
    return moves
