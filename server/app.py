"""The local server: the GUI talks to it over one WebSocket, and it drives the engine.

Messages from the GUI:
    {"type": "new_game", "controllers": ["human", "random_bot"], "seed": 7, "bot_delay": 0.8}
        (seed and bot_delay are optional)
    {"type": "pick", "sequence": 12, "index": 0}

Messages to the GUI:
    {"type": "update", "view": ..., "decision": ... or null, "log_start": n, "log": [...], ...}
    {"type": "game_over", "scores": [...]}
    {"type": "error", "message": "..."}

The server holds one Game at a time, shared by every open connection, so reloading
the page picks the Game up where it was.
"""

import asyncio
import contextlib
import random
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from server.session import GameSession

DEFAULT_BOT_DELAY = 0.8


class GameHost:
    """Hosts the current Game for every open connection, and plays the Random Bots' picks."""

    def __init__(self) -> None:
        self.session: GameSession | None = None
        self.connections: set[WebSocket] = set()
        self.random_bot_task: asyncio.Task | None = None

    async def join(self, websocket: WebSocket) -> None:
        self.connections.add(websocket)
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
                case other:
                    raise ValueError(f"unknown message type {other!r}")
        except (ValueError, KeyError, TypeError) as error:
            await websocket.send_json({"type": "error", "message": str(error)})

    async def new_game(self, message: dict[str, Any]) -> None:
        seed = message.get("seed")
        if seed is None:
            seed = random.randrange(2**32)
        session = GameSession(
            controllers=message["controllers"],
            seed=int(seed),
            bot_delay=float(message.get("bot_delay", DEFAULT_BOT_DELAY)),
        )
        if self.random_bot_task is not None:
            # A cancelled task only reports done once it next runs, so forget it now
            # rather than wait for it.
            self.random_bot_task.cancel()
            self.random_bot_task = None
        self.session = session
        await self.share_news()

    async def pick(self, message: dict[str, Any]) -> None:
        if self.session is None:
            raise ValueError("there is no Game yet; start a new Game first")
        self.session.pick_for_human(sequence=int(message["sequence"]), index=int(message["index"]))
        await self.share_news()

    async def share_news(self) -> None:
        """Sends what changed, then lets the Random Bots pick if the Decision is theirs."""
        session = self.session
        for message in session.news():
            await self.broadcast(message)
        bots_idle = self.random_bot_task is None or self.random_bot_task.done()
        if session.waiting_on_random_bot() and bots_idle:
            self.random_bot_task = asyncio.create_task(self.play_random_bots(session))

    async def play_random_bots(self, session: GameSession) -> None:
        """Answers Random Bot Decisions one at a time, at a pace a person can follow."""
        while session.waiting_on_random_bot():
            await asyncio.sleep(session.bot_delay)
            session.pick_for_random_bot()
            for message in session.news():
                await self.broadcast(message)

    async def broadcast(self, message: dict[str, Any]) -> None:
        for websocket in list(self.connections):
            with contextlib.suppress(WebSocketDisconnect, RuntimeError):
                await websocket.send_json(message)


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
