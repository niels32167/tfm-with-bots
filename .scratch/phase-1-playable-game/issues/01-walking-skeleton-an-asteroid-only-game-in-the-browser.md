# 01 — Walking skeleton: an Asteroid-only Game in the browser

**What to build:** The thinnest complete path through every layer, so that every later ticket only adds rules and screens.

Two Players play a Game where the only Actions are the Asteroid Standard Project (14 MegaCredits: raise Temperature one step, gain one Terraform Rating) and Passing. Each Generation has an Action phase, where Players take Turns of one or two Actions or Pass, and a Production phase that pays MegaCredits equal to Terraform Rating plus MegaCredit Production. The Game ends after the Generation in which Temperature reaches its maximum. Until Corporations exist, Players start with a fixed temporary amount of MegaCredits and Terraform Rating 20, and the final score is just Terraform Rating.

In the browser, a human plays against a Random Bot. The GUI shows Temperature, each Player's MegaCredits and Terraform Rating, the game log, and a status bar listing the current Decision's Options as buttons.

This ticket also sets up the project:
- the Rust engine built around Decisions and Options (ADR 0002);
- the Python engine module (ADR 0007);
- the local Python server with a WebSocket (ADR 0008);
- the React and TypeScript GUI (ADR 0006);
- the testing pattern every later ticket copies.

Installing the Rust toolchain (rustup) and the Python and npm packages needs the user's OK first. Python 3.14 is installed, so check that PyO3 and its build tool support it.

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [x] The engine is always either over or waiting on exactly one Decision for one Player. Picking an Option by index moves it forward, and a pick carrying a stale Decision sequence number is rejected.
- [x] The Python engine module can:
  - create a Game from settings and a seed;
  - create a Game from a Scenario (Generation, Global Parameters, and each Player's MegaCredits, Production and Terraform Rating);
  - read the current Decision and its Options (index, label, structured details);
  - pick an Option;
  - return a Player View;
  - read the game log;
  - report when the Game is over, with a score for each Player.
- [x] Test helpers let a test build a Scenario in a few readable lines and pick an Option by matching its label or details.
- [x] Scenario tests cover:
  - Asteroid's cost and effect;
  - Asteroid not offered when it is unaffordable, and still offered at maximum Temperature, where it costs 14 MegaCredits and does nothing (the rules authority order says so; recorded in docs/rules-notes.md);
  - one or two Actions per Turn;
  - Passing for the rest of the Generation;
  - Production income;
  - the end of the Game.
- [x] The server runs locally, attaches a human or Random Bot Controller to each Player, and streams updates (the Decision, the Player View, new game log lines) over the WebSocket.
- [x] A WebSocket smoke test plays a Random Bot vs Random Bot Game to the end.
- [x] A human can play a full Game against a Random Bot in the browser and see the final scores.
- [x] The project README gives one command each to run the tests and to start the server with the GUI.

## Comments

### 2026-10-22 — implemented (Claude)

**How to run** (also in the README): `uv sync` and `npm --prefix gui install` once. Then `uv run pytest` for the tests, `uv run python -m server` for the server, and `npm --prefix gui run dev` for the GUI at http://localhost:5173.

**Toolchain:**
- Rust 1.99.1, installed with rustup into `~/.cargo`.
- PyO3 0.29.3 and pythonize 0.29. Both support CPython up to 3.15, so Python 3.14 is fine.
- maturin 1.15 as the build backend. uv runs it and rebuilds the engine whenever a `.rs` file changes.
- FastAPI 0.159 and uvicorn 0.54.
- React 19.3.0, Vite 8.3.3 and TypeScript 7.0.2, pinned to releases about two weeks old.

**Rules calls** (details and sources in `docs/rules-notes.md`):
- Asteroid at maximum Temperature is offered and does nothing. The rulebook, the community FAQ and the open-source game agree. The user chose this over the ticket's first wording, which is now updated above.
- Pass is offered at any point in a Turn, including after one Action. This was the user's choice, and the open-source game does the same.
- End Turn is not offered once every other Player has passed.

**Temporary choices for later tickets to replace:**
- Players start with 42 MegaCredits, the Beginner Corporation's amount, until Corporations exist.
- Player 1 starts every Generation; the first-player marker comes with ticket 02. The seed is stored and exposed, but nothing in the engine is random yet.
- The engine already accepts 2–5 Players, but only 2 are tested; ticket 02 owns that.
- A new Game in the GUI is always "you against one Random Bot". Random Bots pick every 0.8 s (the server's default); the speed control is ticket 02.

**Testing pattern for later tickets** (`tests/helpers.py`):
- Helpers: `scenario(player(...), player(...), temperature=...)`, `pick(game, "Asteroid")` or `pick(game, type="pass")`, `offered(...)`, `labels(...)`, `player_board(game, i)` and `end_the_generation(game)`.
- Rule tests live in `tests/rules/` and import only `tm_engine` and these helpers.
- The one server smoke test is in `tests/server/`.
- Everything was written test-first, one behaviour at a time.

**Design notes:**
- The engine works the Decision out from the state each time it is asked, so the state is a plain `Clone` value.
- The game log is stored as small Copy events (`engine/src/log.rs`) and turned into text only when read. It still grows with the Game, so ticket 06's copy-time benchmark should check it against ADR 0004.
- The server sends a Decision to the GUI only when a human must answer it, as the spec's server section says.
- The server holds one Game shared by every connection. A page reload resumes it; after a server restart the GUI goes back to the New Game screen.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - a race where starting a New Game while Random Bots were mid-Turn could leave the new Game stuck;
  - the glossary's _Avoid_ terms "move" and "seat";
  - each Standard Project's name and cost, now kept in one place;
  - `end_the_generation`, moved into the shared helpers;
  - the GUI's "Back to the board" and "Show final scores" buttons.
- Left as is:
  - the GUI hard-codes the thermometer's −30 to +8, which is printed on the board;
  - the log view highlights lines starting with "Generation" by their text.

**Open points:**
- Starlette 1.9 warns that using `httpx` with its TestClient is deprecated in favour of `httpx2`. Switching means a new package, so it waits for the user's OK.
- The Status line is still `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done" label.
