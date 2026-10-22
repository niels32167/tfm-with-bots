"""Terraforming Mars rules engine (Rust, built with PyO3).

Everything returned is plain, JSON-serializable data: dicts, lists, strings, numbers
and None. Players are indexed from 0; their names ("Player 1", ...) count from 1.
"""

from typing import Any

class Game:
    """A Game of Terraforming Mars, always either over or waiting on one Decision."""

    def __init__(self, *, seed: int, players: int = 2) -> None:
        """A new Game from its settings. Raises ValueError for an unsupported Player count."""

    @staticmethod
    def from_scenario(scenario: dict[str, Any]) -> Game:
        """A Game started from a Scenario. Anything left out takes the normal defaults.

        Fields: seed, generation, temperature, and players: a list of
        {megacredits, production: {megacredits}, terraform_rating}.
        Raises ValueError for unknown fields or impossible values.
        """

    @property
    def seed(self) -> int:
        """The seed this Game was created with."""

    @property
    def decision(self) -> dict[str, Any] | None:
        """The Decision the Game is waiting on, or None once it is over.

        {"player": int, "kind": str, "sequence": int,
         "options": [{"index": int, "label": str, "details": {"type": str, ...}}]}
        """

    def pick(self, index: int, sequence: int | None = None) -> None:
        """Answers the current Decision with its Option at `index`.

        Pass the Decision's `sequence` to have a stale pick rejected. Raises ValueError
        for a stale pick, an index that isn't offered, or a Game that is over.
        """

    def player_view(self, player: int) -> dict[str, Any]:
        """Everything `player` is allowed to know."""

    @property
    def log(self) -> list[str]:
        """The game log: one plain-language line for each thing that has happened."""

    @property
    def is_over(self) -> bool:
        """Whether the Game is over."""

    @property
    def scores(self) -> list[dict[str, Any]] | None:
        """Each Player's final score once the Game is over, otherwise None."""
