"""Helpers for talking to the local server over its WebSocket, the way the GUI does."""

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

from fastapi.testclient import TestClient

from server.app import create_app
from tests.helpers import corporation_to_choose, matching_options

# A generous guard so a broken server fails the test instead of hanging it.
MAX_MESSAGES = 10_000


class Gui:
    """One browser tab on the server: sends what the GUI sends, and keeps the card catalog and the
    Controllers on offer, and rebuilds the game log from the messages it receives, as the GUI does."""

    def __init__(self, websocket: Any) -> None:
        self.websocket = websocket
        self.card_catalog: list[dict[str, Any]] | None = None
        self.controllers: list[dict[str, str]] | None = None
        self.log: list[str] = []

    def send(self, message: dict[str, Any]) -> None:
        self.websocket.send_json(message)

    def receive(self) -> dict[str, Any]:
        """The next message from the server after the card catalog and the Controllers on offer; an error
        message fails the test."""
        message = self._next_message()
        assert message["type"] != "error", message["message"]
        if message["type"] == "update":
            self.log = self.log[: message["log_start"]] + message["log"]
        return message

    def receive_error(self) -> str:
        """The next message after the card catalog and the Controllers, which must be an error; returns its
        text."""
        message = self._next_message()
        assert message["type"] == "error", message
        return message["message"]

    def _next_message(self) -> dict[str, Any]:
        message = self.websocket.receive_json()
        while message["type"] in ("card_catalog", "controllers"):
            if message["type"] == "card_catalog":
                self.card_catalog = message["cards"]
            else:
                self.controllers = message["controllers"]
            message = self.websocket.receive_json()
        return message

    def next_update(self) -> dict[str, Any]:
        """The next update, skipping any other messages."""
        return self._receive_until(lambda message: message["type"] == "update", "an update")

    def wait_for_human(self) -> dict[str, Any]:
        """Updates until a human must answer a Decision or the Game is over, ending the human's Turn once it
        is over; returns that update."""

        def wanted(message: dict[str, Any]) -> bool:
            if message["type"] != "update":
                return False
            if message["turn_over"]:
                self.send({"type": "end_turn"})
            return message["decision"] is not None or message["view"]["phase"] == "over"

        return self._receive_until(wanted, "a human Decision")

    def save_replay(self) -> dict[str, Any]:
        """Asks for the Replay file of the current Game and returns it."""
        self.send({"type": "save_replay"})
        return self._receive_until(lambda message: message["type"] == "replay_file", "a Replay file")["file"]

    def dev_view(self, step: int | None = None) -> dict[str, Any]:
        """What the dev panel shows at `step`, or at the latest step. No other message comes between,
        unless a Random Bot is picking."""
        self.send({"type": "dev_view"} if step is None else {"type": "dev_view", "step": step})
        return self._receive_until(lambda message: message["type"] == "dev_view", "a dev view")

    def start(self, controllers: list[str], **fields: Any) -> dict[str, Any]:
        """Starts a new Game (Random Bots pick at once unless `bot_delay` is given) and
        returns the first update in which a human must decide, or the Game is over."""
        self.send({"type": "new_game", "controllers": controllers, "bot_delay": 0, **fields})
        return self.wait_for_human()

    def choose_a_corporation(self, update: dict[str, Any]) -> dict[str, Any]:
        """The human deciding chooses a Corporation, as `corporation_to_choose` says; returns the first
        update in which a human must decide next."""
        decision = update["decision"]
        self.send({"type": "pick", "sequence": decision["sequence"], "index": corporation_to_choose(decision)})
        return self.wait_for_human()

    def skip_drafting_and_buying(self, update: dict[str, Any]) -> dict[str, Any]:
        """While a human must choose a Corporation or Prelude Cards, draft or buy cards (at setup or in a
        Research phase), they choose one as `corporation_to_choose` says, keep the first Prelude Card or
        card offered and are done without buying any; returns the first update in which a human must
        decide something else."""
        for _ in range(MAX_MESSAGES):
            decision = update["decision"]
            if decision is None or decision["kind"] not in ("corporation", "prelude_cards", "draft", "buy_cards"):
                return update
            if decision["kind"] == "corporation":
                update = self.choose_a_corporation(update)
            else:
                self.pick(update, "Done" if decision["kind"] == "buy_cards" else decision["options"][0]["label"])
                update = self.wait_for_human()
        raise AssertionError(f"still drafting or buying after {MAX_MESSAGES} picks")

    def load(self, scenario: dict[str, Any], controllers: Sequence[str] = ("human", "random_bot")) -> dict[str, Any]:
        """Starts a Game from a Scenario; returns the first update in which a human must decide."""
        file = {"controllers": list(controllers), "replay": {"start": {"scenario": scenario}, "picks": []}}
        self.send({"type": "load_replay", "file": file, "bot_delay": 0})
        return self.wait_for_human()

    def choose(self, update: dict[str, Any], cards: list[str]) -> None:
        """Chooses `cards` (their ids), and is done, in answer to `update`'s Decision."""
        self.send({"type": "choose_cards", "sequence": update["decision"]["sequence"], "cards": cards})

    def pick(self, update: dict[str, Any], label: str, **fields: Any) -> None:
        """Picks the one Option in `update`'s Decision whose label contains `label`."""
        decision = update["decision"]
        found = matching_options(decision["options"], label)
        assert len(found) == 1, f"expected one Option matching {label!r}, offered: {decision['options']}"
        self.send({"type": "pick", "sequence": decision["sequence"], "index": found[0]["index"], **fields})

    def undo(self) -> dict[str, Any]:
        self.send({"type": "undo"})
        return self.next_update()

    def _receive_until(self, wanted: Any, description: str) -> dict[str, Any]:
        for _ in range(MAX_MESSAGES):
            message = self.receive()
            if wanted(message):
                return message
        raise AssertionError(f"no {description} after {MAX_MESSAGES} messages")


@contextmanager
def connect() -> Iterator[Gui]:
    """A GUI connected to a freshly started server."""
    with TestClient(create_app()).websocket_connect("/ws") as websocket:
        yield Gui(websocket)
