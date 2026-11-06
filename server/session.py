"""A Game in progress on the server, with a Controller attached to each Player."""

import random
from typing import Any, Literal

import tm_engine

from tests.fuzzing.invariants import (
    each_reserved_area_used_only_by_its_card,
    special_tiles_where_their_cards_put_them,
    tiles_only_on_legal_areas,
)

type Controller = Literal["human", "random_bot"]
CONTROLLERS: tuple[Controller, ...] = ("human", "random_bot")

# What the fuzzer checks that a position must keep to and a Scenario doesn't refuse, so that the dev
# panel can say so of a position. They stay the one place that says what is legal.
POSITION_INVARIANTS = (
    tiles_only_on_legal_areas,
    special_tiles_where_their_cards_put_them,
    each_reserved_area_used_only_by_its_card,
)


class GameSession:
    """One Game plus who answers each Player's Decisions.

    A human answers through the GUI; a Random Bot picks one of the offered Options
    at random. A Random Bot's pick depends only on the Game's seed and the Decision's
    sequence number, so the same seed and the same human picks give the same Game,
    also after an undo or after loading a Replay file.
    """

    def __init__(self, game: tm_engine.Game, controllers: list[Controller], bot_delay: float) -> None:
        unknown = [controller for controller in controllers if controller not in CONTROLLERS]
        if unknown:
            raise ValueError(f"unknown Controller {unknown[0]!r}; expected one of {list(CONTROLLERS)}")
        if len(controllers) != game.players:
            raise ValueError(f"the Game has {game.players} Players, but {len(controllers)} Controllers were given")
        self.game = game
        self.controllers = list(controllers)
        self.bot_delay = bot_delay
        self.log_lines_sent = 0
        # The sequence number of every Decision a human has answered, latest last, for undo.
        self.answered_by_humans: list[int] = []

    @classmethod
    def new(
        cls,
        controllers: list[Controller],
        seed: int,
        bot_delay: float,
        *,
        draft: bool = True,
    ) -> "GameSession":
        """A new Game with one Player for each Controller, with the Draft unless `draft` is false."""
        game = tm_engine.Game(seed=seed, players=len(controllers), draft=draft)
        return cls(game, controllers, bot_delay)

    @classmethod
    def from_replay_file(cls, file: dict[str, Any], bot_delay: float) -> "GameSession":
        """The Game saved in a Replay file, resumed where its Replay ends.

        Its picks are replayed one by one, so undo can go back through them too.
        """
        if not isinstance(file, dict) or not {"controllers", "replay"} <= file.keys():
            raise ValueError('this is not a Replay file: it needs "controllers" and "replay"')
        replay = file["replay"]
        # The engine checks the whole Replay first, and names the pick at fault if one is.
        tm_engine.Game.from_replay(replay)
        session = cls(tm_engine.Game.from_replay(replay, step=0), file["controllers"], bot_delay)
        for index in replay["picks"]:
            session._pick(index)
        return session

    @property
    def viewer(self) -> int | None:
        """The Player whose Player View the GUI shows, or None for the full view.

        With exactly one human, the screen is theirs. In Hotseat, and when only
        Random Bots play, nobody at the screen has anything to hide from.
        """
        humans = [player for player, controller in enumerate(self.controllers) if controller == "human"]
        return humans[0] if len(humans) == 1 else None

    def deciding_controller(self) -> Controller | None:
        """Who answers the Decision the Game is waiting on, or None once it is over."""
        decision = self.game.decision
        return None if decision is None else self.controllers[decision["player"]]

    def waiting_on_random_bot(self) -> bool:
        return self.deciding_controller() == "random_bot"

    def waiting_on_random_bot_to_draft_or_buy(self) -> bool:
        """Whether a Random Bot is choosing a Corporation, drafting cards, or buying them at setup or in
        a Research phase, paying with heat included."""
        if not self.waiting_on_random_bot():
            return False
        phase = self.game.full_view()["phase"]
        return self.game.decision["kind"] in ("corporation", "draft", "buy_cards") or (
            self.game.decision["kind"] == "payment" and phase == "research"
        )

    def random_bot_pauses_before_picking(self) -> bool:
        """Whether a person watching needs a moment before this Random Bot pick: not while it drafts or
        buys, and not where there is one Option and so nothing to choose, such as the one way to pay.
        Which Decisions have one Option shows only what is public: its hand is hidden, but a card it
        could play comes with a Pass, and a card in hand with Sell Patents."""
        return not self.waiting_on_random_bot_to_draft_or_buy() and len(self.game.decision["options"]) > 1

    def pick_for_random_bot(self) -> None:
        decision = self.game.decision
        random_numbers = random.Random(f"{self.game.seed}/{decision['sequence']}")
        self._pick(random_numbers.randrange(len(decision["options"])))

    def pick_for_human(self, sequence: int, index: int) -> None:
        """Applies a human's pick. Raises ValueError if it isn't theirs to make or is stale."""
        if self.waiting_on_random_bot():
            raise ValueError("this Decision belongs to a Random Bot, not a human")
        self._pick(index, sequence)

    @property
    def can_undo(self) -> bool:
        return bool(self.answered_by_humans)

    def undo(self) -> None:
        """Goes back to the Decision a human answered last, so they can answer it again.

        Every pick made since, the Random Bots' included, is dropped.
        """
        if not self.answered_by_humans:
            raise ValueError("there is no earlier human Decision to go back to")
        # A Decision's sequence number counts the picks before it, so the Replay
        # rebuilt at that step is waiting on that Decision again.
        sequence = self.answered_by_humans.pop()
        self.game = tm_engine.Game.from_replay(self.game.replay, step=sequence)
        # The game log is now shorter. The next news starts where it ends, which tells
        # the GUI to drop the lines after that.
        self.log_lines_sent = min(self.log_lines_sent, len(self.game.log))

    def replay_file(self) -> dict[str, Any]:
        """What a saved Replay file holds: the Replay, plus each Player's Controller."""
        return {"controllers": self.controllers, "replay": self.game.replay}

    def dev_view(self, step: int | None = None) -> dict[str, Any]:
        """What the dev panel shows at `step`, or at the latest step if it is None or beyond the end:
        "view" as the screen shows it, and the "full_view". It holds what Players hide from each other,
        so it goes only to the GUI that asked, and it leaves the Game as it is: an earlier step is a
        Game rebuilt from the Replay. A position that real play can't reach, which a Scenario may
        describe, says why in "position_problems"."""
        picks = self.game.replay["picks"]
        if step is not None and step < 0:
            raise ValueError(f"there is no step {step}; the first is step 0")
        at = len(picks) if step is None else min(step, len(picks))
        shown = self.game if at == len(picks) else tm_engine.Game.from_replay(self.game.replay, step=at)
        full_view = shown.full_view()
        return {
            "type": "dev_view",
            "step": at,
            "steps": len(picks),
            "seed": shown.seed,
            "view": self._view_of(shown),
            "full_view": full_view,
            "decision": shown.decision,
            "picked": picks[at] if at < len(picks) else None,
            "log": shown.log,
            "scenario": shown.to_scenario(),
            "position_problems": [
                problem for invariant in POSITION_INVARIANTS for problem in invariant(full_view, shown.decision)
            ],
        }

    def catch_up(self) -> list[dict[str, Any]]:
        """Everything a newly connected GUI needs, with the whole game log."""
        return self._messages(log_start=0)

    def news(self) -> list[dict[str, Any]]:
        """What changed since the last news: an update with only the new game log lines,
        followed by a game over message once the Game has ended."""
        messages = self._messages(log_start=self.log_lines_sent)
        self.log_lines_sent += len(messages[0]["log"])
        return messages

    def _pick(self, index: int, sequence: int | None = None) -> None:
        decision = self.game.decision
        self.game.pick(index, sequence)
        if self.controllers[decision["player"]] == "human":
            self.answered_by_humans.append(decision["sequence"])

    def _view_of(self, game: tm_engine.Game) -> dict[str, Any]:
        """What the screen shows of `game`: see `viewer`."""
        viewer = self.viewer
        return game.full_view() if viewer is None else game.player_view(viewer)

    def _messages(self, log_start: int) -> list[dict[str, Any]]:
        update = {
            "type": "update",
            "controllers": self.controllers,
            "viewer": self.viewer,
            "seed": self.game.seed,
            "bot_delay": self.bot_delay,
            "can_undo": self.can_undo,
            "view": self._view_of(self.game),
            # The Decision goes to the GUI only when a human must answer it.
            "decision": self.game.decision if self.deciding_controller() == "human" else None,
            "log_start": log_start,
            "log": self.game.log[log_start:],
        }
        if self.game.is_over:
            return [update, {"type": "game_over", "scores": self.game.scores}]
        return [update]
