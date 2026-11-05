"""Helpers for talking to the local server over its WebSocket, the way the GUI does."""

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from fastapi.testclient import TestClient

from server.app import create_app
from tests.helpers import corporation_to_choose, matching_options

# A generous guard so a broken server fails the test instead of hanging it.
MAX_MESSAGES = 10_000


class Gui:
    """One browser tab on the server: sends what the GUI sends, and keeps the card catalog
    and rebuilds the game log from the messages it receives, as the GUI does."""

    def __init__(self, websocket: Any) -> None:
        self.websocket = websocket
        self.card_catalog: list[dict[str, Any]] | None = None
        self.log: list[str] = []

    def send(self, message: dict[str, Any]) -> None:
        self.websocket.send_json(message)

    def receive(self) -> dict[str, Any]:
        """The next message from the server after the card catalog; an error message fails the test."""
        message = self._next_message()
        assert message["type"] != "error", message["message"]
        if message["type"] == "update":
            self.log = self.log[: message["log_start"]] + message["log"]
        return message

    def receive_error(self) -> str:
        """The next message after the card catalog, which must be an error; returns its text."""
        message = self._next_message()
        assert message["type"] == "error", message
        return message["message"]

    def _next_message(self) -> dict[str, Any]:
        message = self.websocket.receive_json()
        if message["type"] == "card_catalog":
            self.card_catalog = message["cards"]
            message = self.websocket.receive_json()
        return message

    def next_update(self) -> dict[str, Any]:
        """The next update, skipping any other messages."""
        return self._receive_until(lambda message: message["type"] == "update", "an update")

    def wait_for_human(self) -> dict[str, Any]:
        """Updates until a human must answer a Decision or the Game is over; returns that update."""
        return self._receive_until(
            lambda message: message["type"] == "update"
            and (message["decision"] is not None or message["view"]["phase"] == "over"),
            "a human Decision",
        )

    def save_replay(self) -> dict[str, Any]:
        """Asks for the Replay file of the current Game and returns it."""
        self.send({"type": "save_replay"})
        return self._receive_until(lambda message: message["type"] == "replay_file", "a Replay file")["file"]

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
        """While a human must choose a Corporation, draft or buy cards (at setup or in a Research
        phase), they choose one as `corporation_to_choose` says, keep the first card offered in the
        Draft and are done without buying any; returns the first update in which a human must decide
        something else."""
        for _ in range(MAX_MESSAGES):
            decision = update["decision"]
            if decision is None or decision["kind"] not in ("corporation", "draft", "buy_cards"):
                return update
            if decision["kind"] == "corporation":
                update = self.choose_a_corporation(update)
            else:
                self.pick(update, decision["options"][0]["label"] if decision["kind"] == "draft" else "Done")
                update = self.wait_for_human()
        raise AssertionError(f"still drafting or buying after {MAX_MESSAGES} picks")

    def pick(self, update: dict[str, Any], label: str) -> None:
        """Picks the one Option in `update`'s Decision whose label contains `label`."""
        decision = update["decision"]
        found = matching_options(decision["options"], label)
        assert len(found) == 1, f"expected one Option matching {label!r}, offered: {decision['options']}"
        self.send({"type": "pick", "sequence": decision["sequence"], "index": found[0]["index"]})

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
