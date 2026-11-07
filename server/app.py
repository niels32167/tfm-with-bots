"""The local server: the GUI talks to it over one WebSocket, and it drives the engine.

Messages from the GUI:
    {"type": "new_game", "controllers": ["human", "random_bot"], "seed": 7, "bot_delay": 0.8, "draft": true,
     "prelude": false}
        (2 to 5 Controllers; seed, bot_delay, draft and prelude are optional; the Draft is on unless draft
        is false, and Prelude is off unless prelude is true; the setup screen sends it on by default)
    {"type": "pick", "sequence": 12, "index": 0}
    {"type": "undo"}                  back to the Decision a human answered last
    {"type": "save_replay"}           answered with a replay_file message
    {"type": "load_replay", "file": {...}, "bot_delay": 0.8}
    {"type": "set_bot_delay", "bot_delay": 0.3}
    {"type": "dev_view", "step": 12}  answered with a dev_view message; the step is optional, and
        one left out or beyond the end means the latest

The state editor starts from an edited position with load_replay, as a Replay file whose "replay" is
{"start": {"scenario": {...}}, "picks": []}.

Messages to the GUI:
    {"type": "card_catalog", "cards": [...]}
        (the printed data of every card, sent first to each new connection)
    {"type": "update", "controllers": [...], "viewer": 0 or null, "seed": 7, "bot_delay": 0.8,
     "can_undo": true, "view": ..., "decision": ... or null, "log_start": n, "log": [...]}
        (viewer null means the view is the full view)
    {"type": "game_over", "scores": [...]}
    {"type": "replay_file", "file": {"controllers": [...], "replay": {...}}}
        (sent only to the GUI that asked)
    {"type": "dev_view", "step": 12, "steps": 40, "seed": 7, "view": ..., "full_view": ...,
     "decision": ... or null, "picked": 0 or null, "log": [...], "scenario": {...},
     "position_problems": [...]}
        (the dev panel's look at a step: the view as the screen shows it, the full view, the Decision
         waiting there whoever answers it and the index picked, the game log so far, that position as a
         Scenario, and why real play could not reach it, if it couldn't; sent only to the GUI that
         asked, as it holds what Players hide from each other, and it changes nothing in the Game)
    {"type": "error", "message": "..."}

The server holds one Game at a time, shared by every open connection, so reloading
the page picks the Game up where it was.
"""

import asyncio
import contextlib
import random
from typing import Any

import tm_engine
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from server.session import GameSession

DEFAULT_BOT_DELAY = 0.8


class GameHost:
    """Hosts the current Game for every open connection, and plays the Random Bots' picks."""

    def __init__(self) -> None:
        self.session: GameSession | None = None
        self.connections: set[WebSocket] = set()
        self.random_bot_task: asyncio.Task | None = None
        # The card catalog never changes, so it is read from the engine once.
        self.card_catalog_message = {"type": "card_catalog", "cards": tm_engine.card_catalog()}

    async def join(self, websocket: WebSocket) -> None:
        self.connections.add(websocket)
        await websocket.send_json(self.card_catalog_message)
        if self.session is not None:
            for message in self.session.catch_up():
                await websocket.send_json(message)

    def leave(self, websocket: WebSocket) -> None:
        self.connections.discard(websocket)

    async def handle(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        try:
            match message.get("type"):
                case "new_game":
                    await self.new_game(message)
                case "pick":
                    await self.pick(message)
                case "undo":
                    await self.undo()
                case "save_replay":
                    file = self.current_session().replay_file()
                    await websocket.send_json({"type": "replay_file", "file": file})
                case "load_replay":
                    await self.start(GameSession.from_replay_file(message["file"], bot_delay(message)))
                case "dev_view":
                    await websocket.send_json(self.current_session().dev_view(whole_number_or_none(message, "step")))
                case "set_bot_delay":
                    self.current_session().bot_delay = bot_delay(message)
                    await self.share_news()
                case other:
                    raise ValueError(f"unknown message type {other!r}")
        except (ValueError, KeyError, TypeError) as error:
            await websocket.send_json({"type": "error", "message": str(error)})

    async def new_game(self, message: dict[str, Any]) -> None:
        seed = message.get("seed")
        if seed is None:
            seed = random.randrange(2**32)
        if not isinstance(seed, int) or not 0 <= seed <= tm_engine.MAX_SEED:
            raise ValueError(f"the seed must be a whole number from 0 to {tm_engine.MAX_SEED}, not {seed!r}")
        draft = true_or_false(message, "draft", default=True)
        prelude = true_or_false(message, "prelude", default=False)
        session = GameSession.new(message["controllers"], seed, bot_delay(message), draft=draft, prelude=prelude)
        await self.start(session)

    async def start(self, session: GameSession) -> None:
        """Replaces the current Game, if any, with `session`."""
        self.stop_random_bots()
        self.session = session
        await self.share_news()

    async def pick(self, message: dict[str, Any]) -> None:
        self.current_session().pick_for_human(sequence=int(message["sequence"]), index=int(message["index"]))
        await self.share_news()

    async def undo(self) -> None:
        self.current_session().undo()
        # The Random Bots may be mid-Turn in the Game as it was; they must not pick in the Game as it is now.
        self.stop_random_bots()
        await self.share_news()

    def current_session(self) -> GameSession:
        if self.session is None:
            raise ValueError("there is no Game yet; start a new Game first")
        return self.session

    def stop_random_bots(self) -> None:
        if self.random_bot_task is not None:
            # A cancelled task only reports done once it next runs, so forget it now
            # rather than wait for it.
            self.random_bot_task.cancel()
            self.random_bot_task = None

    async def share_news(self) -> None:
        """Sends what changed, then lets the Random Bots pick if the Decision is theirs."""
        session = self.session
        for message in session.news():
            await self.broadcast(message)
        bots_idle = self.random_bot_task is None or self.random_bot_task.done()
        if session.waiting_on_random_bot() and bots_idle:
            self.random_bot_task = asyncio.create_task(self.play_random_bots(session))

    async def play_random_bots(self, session: GameSession) -> None:
        """Answers Random Bot Decisions one at a time, at a pace a person can follow. A Random Bot
        drafts and buys cards without pausing, so that how long it takes says nothing about what
        it keeps or how many it buys, and doesn't pause for a Decision with one Option."""
        while session.waiting_on_random_bot():
            if session.random_bot_pauses_before_picking():
                await asyncio.sleep(session.bot_delay)
            session.pick_for_random_bot()
            for message in session.news():
                await self.broadcast(message)

    async def broadcast(self, message: dict[str, Any]) -> None:
        for websocket in list(self.connections):
            with contextlib.suppress(WebSocketDisconnect, RuntimeError):
                await websocket.send_json(message)


def true_or_false(message: dict[str, Any], field: str, *, default: bool) -> bool:
    """The message's `field`, which must be true or false if given."""
    value = message.get(field, default)
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be true or false, not {value!r}")
    return value


def whole_number_or_none(message: dict[str, Any], field: str) -> int | None:
    """The message's `field`, which must be a whole number if given."""
    value = message.get(field)
    if value is None or type(value) is int:
        return value
    raise TypeError(f"{field} must be a whole number, not {value!r}")


def bot_delay(message: dict[str, Any]) -> float:
    """The Random Bot delay a message asks for, in seconds."""
    delay = float(message.get("bot_delay", DEFAULT_BOT_DELAY))
    if not delay >= 0:
        raise ValueError(f"the Random Bot delay must be 0 seconds or more, not {delay}")
    return delay


def create_app() -> FastAPI:
    app = FastAPI(title="Terraforming Mars")
    host = GameHost()

    @app.websocket("/ws")
    async def play(websocket: WebSocket) -> None:
        await websocket.accept()
        await host.join(websocket)
        try:
            while True:
                await host.handle(websocket, await websocket.receive_json())
        except WebSocketDisconnect:
            host.leave(websocket)

    return app
