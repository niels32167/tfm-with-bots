"""A Game in progress on the server, with a Controller attached to each Player."""

import random
from typing import Any, Literal

import tm_engine

type Controller = Literal["human", "random_bot"]
CONTROLLERS: tuple[Controller, ...] = ("human", "random_bot")


class GameSession:
    """One Game plus who answers each Player's Decisions.

    A human answers through the GUI; a Random Bot picks one of the offered Options
    at random. The Random Bots' random numbers come from the Game's seed, so the same
    seed and the same human picks give the same Game.
    """

    def __init__(self, controllers: list[Controller], seed: int, bot_delay: float) -> None:
        unknown = [controller for controller in controllers if controller not in CONTROLLERS]
        if unknown:
            raise ValueError(f"unknown Controller {unknown[0]!r}; expected one of {list(CONTROLLERS)}")
        self.game = tm_engine.Game(seed=seed, players=len(controllers))
        self.controllers = list(controllers)
        self.bot_delay = bot_delay
        self.random_numbers = random.Random(seed)
        self.log_lines_sent = 0

    @property
    def viewer(self) -> int:
        """The Player whose Player View the GUI shows: the first human, else Player 1."""
        return self.controllers.index("human") if "human" in self.controllers else 0

    def deciding_controller(self) -> Controller | None:
        """Who answers the Decision the Game is waiting on, or None once it is over."""
        decision = self.game.decision
        return None if decision is None else self.controllers[decision["player"]]

    def waiting_on_random_bot(self) -> bool:
        return self.deciding_controller() == "random_bot"

    def pick_for_random_bot(self) -> None:
        options = self.game.decision["options"]
        self.game.pick(self.random_numbers.randrange(len(options)))

    def pick_for_human(self, sequence: int, index: int) -> None:
        """Applies a human's pick. Raises ValueError if it isn't theirs to make or is stale."""
        if self.waiting_on_random_bot():
            raise ValueError("this Decision belongs to a Random Bot, not a human")
        self.game.pick(index, sequence)

    def catch_up(self) -> list[dict[str, Any]]:
        """Everything a newly connected GUI needs, with the whole game log."""
        return self._messages(log_start=0)

    def news(self) -> list[dict[str, Any]]:
        """What changed since the last news: an update with only the new game log lines,
        followed by a game over message once the Game has ended."""
        messages = self._messages(log_start=self.log_lines_sent)
        self.log_lines_sent += len(messages[0]["log"])
        return messages

    def _messages(self, log_start: int) -> list[dict[str, Any]]:
        update = {
            "type": "update",
            "controllers": self.controllers,
            "viewer": self.viewer,
            "view": self.game.player_view(self.viewer),
            # The Decision goes to the GUI only when a human must answer it.
            "decision": self.game.decision if self.deciding_controller() == "human" else None,
            "log_start": log_start,
            "log": self.game.log[log_start:],
        }
        if self.game.is_over:
            return [update, {"type": "game_over", "scores": self.game.scores}]
        return [update]
