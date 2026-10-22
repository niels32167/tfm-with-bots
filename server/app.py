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


class Table:
    """The current Game, the open connections, and the task playing Random Bot moves."""

    def __init__(self) -> None:
        self.session: GameSession | None = None
        self.connections: set[WebSocket] = set()
        self.bots: asyncio.Task | None = None

    async def join(self, websocket: WebSocket) -> None:
        self.connections.add(websocket)
        if self.session is not None:
            await websocket.send_json(self.session.update(log_start=0))
            if self.session.game.is_over:
                await websocket.send_json(self.session.game_over())

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
        if self.bots is not None:
            self.bots.cancel()
        self.session = session
        await self.broadcast_progress()

    async def pick(self, message: dict[str, Any]) -> None:
        if self.session is None:
            raise ValueError("there is no Game yet; start a new Game first")
        self.session.pick_for_human(sequence=int(message["sequence"]), index=int(message["index"]))
        await self.broadcast_progress()

    async def broadcast_progress(self) -> None:
        """Sends what changed, then lets the Random Bots move if it's their turn."""
        session = self.session
        await self.broadcast(session.next_update())
        if session.game.is_over:
            await self.broadcast(session.game_over())
        elif session.bot_to_move() and (self.bots is None or self.bots.done()):
            self.bots = asyncio.create_task(self.play_bots(session))

    async def play_bots(self, session: GameSession) -> None:
        """Plays Random Bot moves one at a time, at a pace a person can follow."""
        while session is self.session and session.bot_to_move():
            await asyncio.sleep(session.bot_delay)
            session.pick_for_bot()
            await self.broadcast(session.next_update())
        if session is self.session and session.game.is_over:
            await self.broadcast(session.game_over())

    async def broadcast(self, message: dict[str, Any]) -> None:
        for websocket in list(self.connections):
            with contextlib.suppress(WebSocketDisconnect, RuntimeError):
                await websocket.send_json(message)


def create_app() -> FastAPI:
    app = FastAPI(title="Terraforming Mars")
    table = Table()

    @app.websocket("/ws")
    async def play(websocket: WebSocket) -> None:
        await websocket.accept()
        await table.join(websocket)
        try:
            while True:
                await table.handle(websocket, await websocket.receive_json())
        except WebSocketDisconnect:
            table.leave(websocket)

    return app
