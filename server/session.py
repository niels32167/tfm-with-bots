"""A Game in progress on the server, with a Controller attached to each Player."""

from collections.abc import Callable
from typing import Any

import tm_engine

from ai.controller import Controller, Handle, handle_for, offered
from ai.controllers import MOST_PLAYERS, REGISTERED, advisers, available, make_controller, name_and_settings
from ai.explain import explanation, server_random
from server.advice import advise
from server.card_choice import picks_for_cards
from server.drawing import cards_left, what_it_draws
from tests.fuzzing.invariants import (
    each_reserved_area_used_only_by_its_card,
    special_tiles_where_their_cards_put_them,
    tiles_only_on_legal_areas,
)

# The phases in which a Player takes Turns, or plays their Prelude Cards as one: where a human ends theirs themselves.
TURNS = ("prelude_cards", "action", "final_greenery")

# A Controller's name: "human", who answers through the GUI, or a registered Controller's, such as
# "random_bot". Replay files name each Player's Controller this way.
type ControllerName = str
HUMAN = "human"


def controllers_on_offer() -> list[dict[str, Any]]:
    """The Controllers the setup screen offers, by name and label, with what each does and in Games of how many Players
    at most: a human, then the registered ones that are available. Only these can play on the server; a Replay file
    can't name a module to import."""
    human = {"name": HUMAN, "label": "Human", "description": "You, at this screen.", "most_players": MOST_PLAYERS}
    return [human] + [
        {
            "name": name,
            "label": REGISTERED[name].label,
            "description": REGISTERED[name].description,
            "most_players": REGISTERED[name].most_players,
        }
        for name in available()
    ]


def warm_up() -> None:
    """Makes each available registered Controller once, so that the models they load are loaded before a Visitor's
    bot first thinks: on a tenth of a core (Render's free instance), loading torch and the models takes about 25 s."""
    for name in available():
        make_controller(name)


def check_hosted(controllers: Any) -> None:
    """Refuses what a hosted server (ADR 0014) doesn't play though the local one does: Controllers named other than as
    a list of names; a Game without a human, so that registered Controllers don't play each other on a shared
    computer; and settings after a registered Controller's name, such as a Search Bot's budget. GameSession checks
    the rest."""
    if not isinstance(controllers, list) or not all(isinstance(name, str) for name in controllers):
        raise ValueError(f"the Controllers must be a list of names, not {controllers!r}")
    if HUMAN not in controllers:
        raise ValueError("a hosted server needs a human in every Game")
    tuned = [name for name in controllers if name_and_settings(name)[1]]
    if tuned:
        raise ValueError(f"a hosted server plays its bots without settings, not {tuned[0]!r}")


def label_of(name: ControllerName) -> str:
    """How the setup screen names the Controller called `name`, with any settings after its label."""
    name, settings = name_and_settings(name)
    label = next((offered["label"] for offered in controllers_on_offer() if offered["name"] == name), name)
    return f"{label} ({settings.replace('&', ', ')})" if settings else label


# What the fuzzer checks that a position must keep to and a Scenario doesn't refuse, so that the dev
# panel can say so of a position. They stay the one place that says what is legal.
POSITION_INVARIANTS = (
    tiles_only_on_legal_areas,
    special_tiles_where_their_cards_put_them,
    each_reserved_area_used_only_by_its_card,
)


class GameSession:
    """One Game plus who answers each Player's Decisions.

    A human answers through the GUI; a registered Controller, such as a Random Bot, is asked through
    the handle a Match uses (ADR 0013). Its random source depends only on the Game's seed and the
    Decision's sequence number, so the same seed and the same human picks give the same Game, also
    after an undo or after loading a Replay file, for Controllers that use only that source.
    """

    def __init__(self, game: tm_engine.Game, controllers: list[ControllerName], bot_delay: float) -> None:
        known = [controller["name"] for controller in controllers_on_offer()]
        # Settings may follow a name ("search?seconds=5"); the Controller refuses those it doesn't take when made.
        unknown = [controller for controller in controllers if name_and_settings(controller)[0] not in known]
        if unknown:
            raise ValueError(f"unknown Controller {unknown[0]!r}; expected one of {known}")
        if len(controllers) != game.players:
            raise ValueError(f"the Game has {game.players} Players, but {len(controllers)} Controllers were given")
        self.game = game
        self.controllers = list(controllers)
        self.bot_delay = bot_delay
        self.answering: list[Controller | None] = []
        self.new_controllers()
        self.log_lines_sent = 0
        # The sequence numbers of the Decisions undo may go back to, latest last (see `_pick`).
        self.undoable: list[int] = []
        # Whether the human's Turn is over, but the registered Controllers wait for them to say so.
        self.turn_over = False

    @classmethod
    def new(
        cls,
        controllers: list[ControllerName],
        seed: int,
        bot_delay: float,
        *,
        draft: bool = True,
        prelude: bool = False,
    ) -> GameSession:
        """A new Game with one Player for each Controller, with the Draft unless `draft` is false, and
        with Prelude if `prelude` is true."""
        game = tm_engine.Game(
            seed=seed,
            players=len(controllers),
            draft=draft,
            prelude=prelude,
            # A human plays each of their Prelude Cards with a click (ADR 0015).
            ask_last_prelude_card=prelude and HUMAN in controllers,
        )
        return cls(game, controllers, bot_delay)

    @classmethod
    def from_replay_file(cls, file: dict[str, Any], bot_delay: float) -> GameSession:
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
        registered Controllers play, nobody at the screen has anything to hide from.
        """
        humans = [player for player, controller in enumerate(self.controllers) if controller == HUMAN]
        return humans[0] if len(humans) == 1 else None

    def deciding_controller(self) -> ControllerName | None:
        """Who answers the Decision the Game is waiting on, or None once it is over."""
        decision = self.game.decision
        return None if decision is None else self.controllers[decision["player"]]

    def new_controllers(self) -> None:
        """A new registered Controller for each Player who has one, as in a new Game. After an undo
        they start afresh, so that none remembers a future that was taken back."""
        self.answering = [None if name == HUMAN else make_controller(name) for name in self.controllers]

    def waiting_on_controller(self) -> bool:
        """Whether a registered Controller, not a human, must answer the Decision now: it doesn't while a human
        whose Turn is over hasn't said so."""
        return self.registered_controller_decides() and not self.turn_over

    def registered_controller_decides(self) -> bool:
        """Whether the Decision is a registered Controller's, not a human's."""
        controller = self.deciding_controller()
        return controller is not None and controller != HUMAN

    def waiting_on_controller_to_draft_or_buy(self) -> bool:
        """Whether a registered Controller is choosing a Corporation or Prelude Cards, drafting cards, or
        buying them at setup or in a Research phase, paying with heat included."""
        if not self.waiting_on_controller():
            return False
        phase = self.game.full_view()["phase"]
        return self.game.decision["kind"] in ("corporation", "prelude_cards", "draft", "buy_cards") or (
            self.game.decision["kind"] == "payment" and phase == "research"
        )

    def controller_pauses_before_picking(self) -> bool:
        """Whether a person watching needs a moment before this Controller's pick: not while it drafts
        or buys, and not where there is one Option and so nothing to choose, such as the one way to pay.
        Which Decisions have one Option shows only what is public: its hand is hidden, but a card it
        could play comes with a Pass, and a card in hand with Sell Patents."""
        return not self.waiting_on_controller_to_draft_or_buy() and len(self.game.decision["options"]) > 1

    def controller_turn(self) -> tuple[ControllerName, Controller, Handle]:
        """The name of the registered Controller that must answer the Decision, the Controller, and the
        handle to ask it with. The handle is plain data, so the Controller may think in another thread
        while the Game goes on serving the GUI."""
        if not self.waiting_on_controller():
            raise ValueError("no registered Controller is deciding")
        decision = self.game.decision
        player = decision["player"]
        random_numbers = server_random(self.game.seed, decision["sequence"])
        return self.controllers[player], self.answering[player], handle_for(self.game, random_numbers)

    def pick_for_controller(self, sequence: int, index: int) -> None:
        """Applies a registered Controller's pick for the Decision numbered `sequence`. Raises ValueError
        if it is stale or not offered."""
        if not self.waiting_on_controller():
            raise ValueError("this Decision doesn't belong to a registered Controller")
        if not offered(self.game.decision, index):
            options = len(self.game.decision["options"])
            raise ValueError(f"the Controller picked Option {index!r}, but {options} were offered")
        self._pick(index, sequence)

    def pick_for_human(self, sequence: int, index: int) -> None:
        """Applies a human's pick. Raises ValueError if it isn't theirs to make or is stale."""
        self._check_for_human()
        self._pick(index, sequence)

    def choose_cards(self, sequence: int, cards: list[str]) -> None:
        """Picks what chooses exactly `cards` for the Decision numbered `sequence` and those that make up one choice
        with it (server.card_choice). Raises ValueError, changing nothing, if the human can't choose them."""
        self._check_for_human(sequence)
        for number, index in enumerate(picks_for_cards(self.game, cards)):
            self._pick(index, undo_to_here=number == 0)

    def what_it_draws(self, sequence: int, index: int) -> str | None:
        """What a human's pick would have them draw or look at, or None (server.drawing). Raises ValueError if it
        isn't theirs to make, is stale or isn't offered."""
        self._check_for_human(sequence)
        if not offered(self.game.decision, index):
            raise ValueError(
                f"there is no Option {index}; the Decision has {len(self.game.decision['options'])} Options"
            )
        return what_it_draws(self.game, index)

    def _check_for_human(self, sequence: int | None = None) -> None:
        """Raises ValueError unless a human answers the Decision, which is numbered `sequence` if given."""
        if self.registered_controller_decides():
            raise ValueError(f"this Decision belongs to a {label_of(self.deciding_controller())}, not a human")
        decision = self.game.decision
        if sequence is not None and decision is not None and decision["sequence"] != sequence:
            raise ValueError(f"stale pick: it answers Decision {sequence}, not {decision['sequence']}")
        if decision is None:
            raise ValueError("the Game is over, so there is no Decision to answer")

    def adviser(self, sequence: int, name: ControllerName) -> Callable[[], dict[str, Any]]:
        """What finds what the registered Controller `name` would do at the human's Decision numbered `sequence`, as an
        advice message. It thinks on a copy of the Game, so it may run in another thread. Raises ValueError if the
        Decision isn't a human's or is stale, or that Controller gives no advice in this Game."""
        self._check_for_human(sequence)
        if name not in self.advisers():
            raise ValueError(f"no Controller {name!r} gives advice in this Game; those that do are {self.advisers()}")
        game = self.game.copy()
        about = {"type": "advice", "sequence": sequence, "controller": name}
        return lambda: {**about, **advise(game, name)}

    def advisers(self) -> list[ControllerName]:
        """The registered Controllers a human may ask for advice in this Game, the one suggested first."""
        return advisers(self.game.players)

    def end_turn(self) -> None:
        """The human, whose Turn is over, says so, and the others go on."""
        if not self.turn_over:
            raise ValueError("the Turn is not over")
        self.turn_over = False

    @property
    def can_undo(self) -> bool:
        return bool(self.undoable)

    def undo(self) -> None:
        """Goes back to the Decision a human answered last, so they can answer it again, unless that would give
        them an advantage (see `_pick`).

        Every pick made since, the registered Controllers' included, is dropped.
        """
        if not self.undoable:
            raise ValueError("there is no Decision to go back to, or what followed it can't be taken back")
        # A Decision's sequence number counts the picks before it, so the Replay
        # rebuilt at that step is waiting on that Decision again.
        sequence = self.undoable.pop()
        self.game = tm_engine.Game.from_replay(self.game.replay, step=sequence)
        self.turn_over = False
        self.new_controllers()
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
            "explanation": self._explanation(shown, at),
        }

    def _explanation(self, game: tm_engine.Game, step: int) -> dict[str, Any] | None:
        """Why the registered Controller answering the Decision at `step` picks what it picks, asked with
        the handle and random source it was given (see `controller_turn`); None for a human's Decision,
        once the Game is over, or for a Controller that can't explain itself."""
        decision = game.decision
        if decision is None or self.controllers[decision["player"]] == HUMAN:
            return None
        name = self.controllers[decision["player"]]
        return explanation(make_controller(name), handle_for(game, server_random(game.seed, step)), name)

    def catch_up(self) -> list[dict[str, Any]]:
        """Everything a newly connected GUI needs, with the whole game log."""
        return self._messages(log_start=0)

    def news(self) -> list[dict[str, Any]]:
        """What changed since the last news: an update with only the new game log lines,
        followed by a game over message once the Game has ended."""
        messages = self._messages(log_start=self.log_lines_sent)
        self.log_lines_sent += len(messages[0]["log"])
        return messages

    def _pick(self, index: int, sequence: int | None = None, *, undo_to_here: bool = True) -> None:
        """Applies a pick, and notes what it means for undo and whether it ends a human's Turn. Undo may come back to a human's Decision unless `undo_to_here` is false, as for all but the
        first pick of one choice."""
        decision = self.game.decision
        before = self.game.full_view()
        self.game.pick(index, sequence)
        after = self.game.full_view()
        by_human = self.controllers[decision["player"]] == HUMAN
        if by_human and undo_to_here:
            self.undoable.append(decision["sequence"])
        if self.viewer is None:
            return  # The screen shows everything, so undo gives nothing away, and no Turn is waited for.
        if not by_human or shows_what_was_hidden(before, after):
            self.undoable.clear()
        self.turn_over = (
            by_human
            and before["phase"] in TURNS
            and after["current_player"] not in (None, self.viewer)
            and not ends_turn(before["phase"], decision["options"][index]["details"]["type"])
        )

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
            "turn_over": self.turn_over,
            "advisers": self.advisers(),
            "view": self._view_of(self.game),
            # The Decision goes to the GUI only when a human must answer it.
            "decision": self.game.decision if self.deciding_controller() == HUMAN else None,
            "log_start": log_start,
            "log": self.game.log[log_start:],
        }
        if self.game.is_over:
            return [update, {"type": "game_over", "scores": self.game.scores}]
        return [update]


def shows_what_was_hidden(before: dict[str, Any], after: dict[str, Any]) -> bool:
    """Whether a pick that led from one full view to the other showed its Player what they couldn't know: it drew,
    looked at, dealt or passed on cards, or ended the Generation, the Game, or a phase everyone chooses in secretly. The end of
    the last Player's Prelude Cards, which Generation 1's first Turn follows, shows nothing."""
    if cards_left(before) != cards_left(after) or before["generation"] != after["generation"]:
        return True
    if [board["passed_in_draft"] for board in before["players"]] != [
        board["passed_in_draft"] for board in after["players"]
    ]:
        return True
    phases = (before["phase"], after["phase"])
    return phases[0] != phases[1] and phases != ("prelude_cards", "action")


def ends_turn(phase: str, option_type: str) -> bool:
    """Whether a human picking an Option of `option_type` says with it that their Turn is over."""
    return option_type in ("end_turn", "pass") or (phase == "final_greenery" and option_type == "done")
