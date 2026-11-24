"""A Player View alone as a position (`view_position`), what the Value Model reads, and a Player's result from the
final scores (`result_of`). Like ai.imitation.encoded, it imports nothing that reads the dataset, nor the engine or
PyTorch, so the Value Bot, a Controller, and the processes that make training batches can both use it."""

from typing import Any

from ai.controller import last_prelude_card
from ai.encoding import GLOBAL_FIELDS
from ai.imitation.encoded import Position

# Decisions that follow from the one before, in the same Player's chain: paying for the card just played, placing its
# Tile, choosing whom it targets, and the like (tm_engine's Decision kinds). Until they are answered, the Player
# View hardly changes (a card played is still in hand, nothing is paid), so the Value Bot rates an Option only once
# they are answered, and the Value Model learns only from positions where none is waiting.
FOLLOW_UPS = frozenset(
    {
        "payment",
        "area",
        "production",
        "keep_cards",
        "resources",
        "effects",
        "viral_enhancers",
        "add_to_card",
        "olympus_conference",
        "target",
        "discard_to_draw",
        "sell_patents",
        "play_card",
        "free_award",
    }
)


def is_follow_up(decision: dict[str, Any]) -> bool:
    """Whether `decision` follows from the one before: one of FOLLOW_UPS, or only to play a last Prelude Card."""
    return decision["kind"] in FOLLOW_UPS or last_prelude_card(decision)


# The global fields that name the Decision being answered. A Player View doesn't say what another Player is
# deciding, so the Value Model reads none of them, whoever's Decision it is.
DECIDING = [index for index, name in enumerate(GLOBAL_FIELDS) if name.startswith("deciding_")]


def view_position(view: dict[str, Any]) -> Position:
    """The position `view` shows its viewer, encoded (ai.encoding) without a Decision or Options."""
    position = Position.of(view, {"kind": "action", "options": []})
    position.globals[DECIDING] = 0.0
    return position


def result_of(scores: list[dict[str, Any]], player: int) -> float:
    """From the engine's final scores: 1 if `player` won, ½ if they share first place, 0 if they lost."""
    winners = [score["player"] for score in scores if score["rank"] == 1]
    if player not in winners:
        return 0.0
    return 1.0 if len(winners) == 1 else 0.5
