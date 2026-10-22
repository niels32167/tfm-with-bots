# Terraforming Mars

A digital Terraforming Mars with a fast rules engine, built so an AI opponent can later
be trained against it by self-play. Phase 1 is a playable, well-tested game; see
`.scratch/phase-1-playable-game/spec.md`.

So far (ticket 01) it plays an Asteroid-only Game: two Players raise Temperature with
the Asteroid Standard Project until it is maxed, and the higher Terraform Rating wins.

## How it fits together

```
Rust engine  →  Python engine module (tm_engine)  →  local Python server  →  browser GUI
engine/          built by maturin, used by tests      server/ (FastAPI,       gui/ (React +
                                                      WebSocket)              TypeScript, Vite)
```

Tests, the server and the future AI all go through the Python engine module; nothing
else reaches into the engine.

## Setup (once)

You need [Rust](https://rustup.rs), [uv](https://docs.astral.sh/uv/) and Node.js 22.
Then, in the project folder:

```bash
uv sync
```

```bash
npm --prefix gui install
```

`uv sync` creates `.venv` and builds the engine. After that, `uv run` rebuilds the
engine by itself whenever a Rust file changes, so there is no separate build step.

## Run the tests

```bash
uv run pytest
```

## Play

Start the server in one terminal:

```bash
uv run python -m server
```

and the GUI in another:

```bash
npm --prefix gui run dev
```

Then open http://localhost:5173 and click **New Game** to play against a Random Bot.
The server keeps the Game in memory, so reloading the page picks it up again.

## Other checks

- Rust lint: `cargo clippy --manifest-path engine/Cargo.toml`
- GUI type check: `npm --prefix gui run typecheck`

## Where things are

| Path | What |
| --- | --- |
| `engine/src/game.rs` | The rules: Game state, Decisions and Options |
| `engine/src/scenario.rs` | Starting a Game from a Scenario |
| `engine/src/view.rs` | The Player View and Decisions as plain data for Python |
| `engine/src/log.rs` | The game log |
| `engine/src/lib.rs` | The Python bindings (`tm_engine`) |
| `engine/tm_engine.pyi` | The Python API, for your editor |
| `tests/rules/` | Scenario tests of the rules, through `tm_engine` |
| `tests/helpers.py` | `scenario()`, `player()`, `pick()`, `offered()`: helpers that make tests read like play |
| `server/` | The local server and the Random Bot |
| `gui/src/` | The browser GUI |
| `CONTEXT.md` | The glossary; code, tests and messages use its terms |
| `docs/adr/` | Architecture decisions |
| `docs/rules-notes.md` | Every rules judgment call |
| `.scratch/phase-1-playable-game/` | The phase-1 spec and tickets |
