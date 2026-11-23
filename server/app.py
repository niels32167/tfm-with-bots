"""The server: the GUI talks to it over one WebSocket, and it drives the engine.

Messages from the GUI:
    {"type": "new_game", "controllers": ["human", "random_bot"], "seed": 7, "bot_delay": 0.8, "draft": true,
     "prelude": false}
        (2 to 5 Controllers, each "human" or a registered Controller's name; seed, bot_delay, draft and
        prelude are optional; the Draft is on unless draft is false, and Prelude is off unless prelude is
        true; the setup screen sends it on by default)
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
    {"type": "controllers", "controllers": [{"name": "human", "label": "Human"},
                                            {"name": "random_bot", "label": "Random Bot"}, ...],
     "hosted": false}
        (the Controllers the setup screen offers, sent next: a human and the registered ones; and whether the
         server is hosted for anyone with its link, where the dev panel is off, every Game needs a human and
         bots play without settings)
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
        (also when a registered Controller raises an error or picks an Option not offered; the Game
         then waits, and Undo, a new Game or Load Replay… go on from there. A hosted server sends one
         instead of the card catalog when it turns a connection away, and then closes it: without a
         Visitor id (close code 1008), or when it is full (1013))

The server holds one Game at a time, shared by every open connection, so reloading
the page picks the Game up where it was. Hosted for anyone with its link (`Hosting`, ADR 0014), it holds one
Game for each Visitor instead, found again by the Visitor id the GUI keeps and sends as `/ws?visitor=<id>`. A registered Controller thinks in a worker thread, handed
only plain data (ADR 0013), so that the server goes on answering while it does; its pick is dropped
if the Game has moved on by then, after an undo, say.
"""

import asyncio
import contextlib
import os
import random
import re
import time
from collections.abc import Callable
from concurrent.futures import Executor, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tm_engine
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from server.session import GameSession, check_hosted, controllers_on_offer, label_of

DEFAULT_BOT_DELAY = 0.8
# What a visitor id looks like: the GUI makes one with crypto.randomUUID() and keeps it in the browser.
VISITOR_ID = re.compile(r"[A-Za-z0-9-]{8,64}")


@dataclass(frozen=True)
class Hosting:
    """How the server runs when hosted for anyone with its link (ADR 0014): each Visitor has their own Game, and at
    most `most_visitors` are kept. A Visitor with no open connection for `idle_seconds` is forgotten, Game and all.
    At most `thinkers` registered Controllers think at once, across every Visitor's Game, by default one for each
    core this process may use, so that one Visitor's Search Bot slows the others' bots rather than the server."""

    most_visitors: int = 100
    idle_seconds: float = 6 * 60 * 60
    thinkers: int = field(default_factory=lambda: os.process_cpu_count() or 1)
    clock: Callable[[], float] = field(default=time.monotonic)


class GameHost:
    """Hosts a Game for its open connections (every one, or a Visitor's on a hosted server), and plays the
    registered Controllers' picks, in `thinking`'s threads if given. A `hosted` one refuses what a hosted server
    doesn't play (server.session.check_hosted) and the dev panel."""

    def __init__(self, *, hosted: bool = False, thinking: Executor | None = None) -> None:
        self.hosted = hosted
        # Where registered Controllers think: asyncio's own threads, unless the hosted server shares a few.
        self.thinking = thinking
        self.session: GameSession | None = None
        self.connections: set[WebSocket] = set()
        self.controller_task: asyncio.Task | None = None
        # The card catalog never changes, so it is read from the engine once.
        self.card_catalog_message = {"type": "card_catalog", "cards": tm_engine.card_catalog()}

    async def join(self, websocket: WebSocket) -> None:
        self.connections.add(websocket)
        await websocket.send_json(self.card_catalog_message)
        await websocket.send_json({"type": "controllers", "controllers": controllers_on_offer(), "hosted": self.hosted})
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
                    file = message["file"]
                    if self.hosted and isinstance(file, dict):
                        check_hosted(file.get("controllers"))
                    await self.start(GameSession.from_replay_file(file, bot_delay(message)))
                case "dev_view":
                    if self.hosted:
                        raise ValueError("the dev panel is off on a hosted server")
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
        if self.hosted:
            check_hosted(message["controllers"])
        session = GameSession.new(message["controllers"], seed, bot_delay(message), draft=draft, prelude=prelude)
        await self.start(session)

    async def start(self, session: GameSession) -> None:
        """Replaces the current Game, if any, with `session`."""
        self.stop_controllers()
        self.session = session
        await self.share_news()

    async def pick(self, message: dict[str, Any]) -> None:
        self.current_session().pick_for_human(sequence=int(message["sequence"]), index=int(message["index"]))
        await self.share_news()

    async def undo(self) -> None:
        self.current_session().undo()
        # The Controllers may be mid-Turn in the Game as it was; they must not pick in the Game as it is now.
        self.stop_controllers()
        await self.share_news()

    def current_session(self) -> GameSession:
        if self.session is None:
            raise ValueError("there is no Game yet; start a new Game first")
        return self.session

    def stop_controllers(self) -> None:
        if self.controller_task is not None:
            # A cancelled task only reports done once it next runs, so forget it now
            # rather than wait for it. A Controller still thinking in its thread finishes, unheard.
            self.controller_task.cancel()
            self.controller_task = None

    async def share_news(self) -> None:
        """Sends what changed, then lets the registered Controllers pick if the Decision is theirs."""
        session = self.session
        for message in session.news():
            await self.broadcast(message)
        controllers_idle = self.controller_task is None or self.controller_task.done()
        if session.waiting_on_controller() and controllers_idle:
            self.controller_task = asyncio.create_task(self.play_controllers(session))

    async def play_controllers(self, session: GameSession) -> None:
        """Answers registered Controllers' Decisions one at a time, at a pace a person can follow: each
        pick takes at least the bot delay, thinking included. A Controller drafts and buys cards without
        that pause, so that how long it takes says less about what it keeps or how many it buys, and
        doesn't pause for a Decision with one Option."""
        loop = asyncio.get_running_loop()
        while session.waiting_on_controller():
            started = loop.time()
            pauses = session.controller_pauses_before_picking()
            sequence = session.game.decision["sequence"]
            name, controller, handle = session.controller_turn()
            try:
                index = await loop.run_in_executor(self.thinking, controller.pick, handle)
            except Exception as error:  # noqa: BLE001 - shown to the GUI, which can undo or start afresh.
                await self.broadcast({"type": "error", "message": f"{label_of(name)} raised {error!r}"})
                return
            if pauses:
                await asyncio.sleep(max(0.0, session.bot_delay - (loop.time() - started)))
            decision = session.game.decision
            if self.session is not session or decision is None or decision["sequence"] != sequence:
                return  # The Game moved on while it thought.
            try:
                session.pick_for_controller(sequence, index)
            except ValueError as error:
                await self.broadcast({"type": "error", "message": f"{label_of(name)}: {error}"})
                return
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
    """The bot delay a message asks for, in seconds: how long each registered Controller's pick takes
    at least, where a person watching needs a moment."""
    delay = float(message.get("bot_delay", DEFAULT_BOT_DELAY))
    if not delay >= 0:
        raise ValueError(f"the bot delay must be 0 seconds or more, not {delay}")
    return delay


class Visitors:
    """The hosted server's Visitors, each with their own GameHost, within `hosting`'s limits."""

    def __init__(self, hosting: Hosting) -> None:
        self.hosting = hosting
        self.hosts: dict[str, GameHost] = {}
        self.last_left: dict[str, float] = {}
        self.thinking = ThreadPoolExecutor(max_workers=hosting.thinkers, thread_name_prefix="thinking")

    def host_for(self, visitor: str) -> GameHost | None:
        """`visitor`'s GameHost, new if they have none, or None if the server is full. Visitors idle too long are
        forgotten first; one with a connection open never is."""
        self.forget_the_idle()
        if visitor not in self.hosts:
            if len(self.hosts) >= self.hosting.most_visitors:
                return None
            self.hosts[visitor] = GameHost(hosted=True, thinking=self.thinking)
        return self.hosts[visitor]

    def left(self, visitor: str) -> None:
        """Notes when `visitor` closed a connection, from which their idle time counts once none is open."""
        self.last_left[visitor] = self.hosting.clock()

    def forget_the_idle(self) -> None:
        now = self.hosting.clock()
        for visitor, host in list(self.hosts.items()):
            if not host.connections and now - self.last_left.get(visitor, now) > self.hosting.idle_seconds:
                host.stop_controllers()
                del self.hosts[visitor]
                del self.last_left[visitor]


async def turn_away(websocket: WebSocket, message: str, code: int) -> None:
    """Tells the GUI why its connection is refused, and closes it."""
    await websocket.send_json({"type": "error", "message": message})
    await websocket.close(code=code)


def create_app(hosting: Hosting | None = None, gui: Path | None = None) -> FastAPI:
    """The server: for one Game shared by every connection, or with `hosting`, for one Game per Visitor. With
    `gui`, the folder of the built GUI (`npm run build` makes gui/dist), it also sends the GUI's pages, so that
    one port serves both; otherwise vite's dev server does."""
    app = FastAPI(title="Terraforming Mars")
    shared = GameHost()
    visitors = Visitors(hosting) if hosting is not None else None

    @app.websocket("/ws")
    async def play(websocket: WebSocket, visitor: str | None = None) -> None:
        await websocket.accept()
        if visitors is not None and (visitor is None or not VISITOR_ID.fullmatch(visitor)):
            await turn_away(websocket, "this server needs a visitor id; reload the page", code=1008)
            return
        host = shared if visitors is None else visitors.host_for(visitor)
        if host is None:
            await turn_away(websocket, "the server is full: too many have a Game on it; try again later", code=1013)
            return
        try:
            await host.join(websocket)
            while True:
                await host.handle(websocket, await websocket.receive_json())
        except WebSocketDisconnect:
            pass
        finally:
            host.leave(websocket)
            if visitors is not None:
                visitors.left(visitor)

    if gui is not None:
        app.mount("/", StaticFiles(directory=gui, html=True), name="gui")
    return app
