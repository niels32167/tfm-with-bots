"""A Game in progress on the server, with a Controller attached to each Player."""

import random
from typing import Any, Literal

import tm_engine

type Controller = Literal["human", "random_bot"]
CONTROLLERS: tuple[Controller, ...] = ("human", "random_bot")


class GameSession:
    """One Game plus who answers each Player's Decisions.

    A human answers through the GUI; a Random Bot picks one of the offered Options
    at random. The bots' own random numbers come from the Game's seed, so the same
    seed and the same human picks give the same Game.
    """

    def __init__(self, controllers: list[Controller], seed: int, bot_delay: float) -> None:
        unknown = [controller for controller in controllers if controller not in CONTROLLERS]
        if unknown:
            raise ValueError(f"unknown Controller {unknown[0]!r}; expected one of {list(CONTROLLERS)}")
        self.game = tm_engine.Game(seed=seed, players=len(controllers))
        self.controllers = list(controllers)
        self.bot_delay = bot_delay
        self.random_bot = random.Random(seed)
        self.log_lines_sent = 0

    @property
    def viewer(self) -> int:
        """The Player whose Player View the GUI shows: the first human, else Player 1."""
        return self.controllers.index("human") if "human" in self.controllers else 0

    def bot_to_move(self) -> bool:
        decision = self.game.decision
        return decision is not None and self.controllers[decision["player"]] == "random_bot"

    def pick_for_bot(self) -> None:
        options = self.game.decision["options"]
        self.game.pick(self.random_bot.randrange(len(options)))

    def pick_for_human(self, sequence: int, index: int) -> None:
        """Applies a human's pick. Raises ValueError if it isn't theirs to make or is stale."""
        decision = self.game.decision
        if decision is not None and self.controllers[decision["player"]] != "human":
            raise ValueError("it is not a human Player's Decision")
        self.game.pick(index, sequence)

    def update(self, log_start: int) -> dict[str, Any]:
        """The message telling the GUI the current state, with game log lines from `log_start` on.

        The current Decision is included only when a human must answer it.
        """
        decision = self.game.decision
        if decision is not None and self.controllers[decision["player"]] != "human":
            decision = None
        return {
            "type": "update",
            "controllers": self.controllers,
            "viewer": self.viewer,
            "view": self.game.player_view(self.viewer),
            "decision": decision,
            "log_start": log_start,
            "log": self.game.log[log_start:],
        }

    def next_update(self) -> dict[str, Any]:
        """The update carrying only the game log lines not yet sent."""
        message = self.update(self.log_lines_sent)
        self.log_lines_sent += len(message["log"])
        return message

    def game_over(self) -> dict[str, Any]:
        return {"type": "game_over", "scores": self.game.scores}
