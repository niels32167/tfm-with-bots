# Terraforming Mars

A digital Terraforming Mars with a fast rules engine, built so an AI opponent can later
be trained against it by self-play. Phase 1 is a playable, well-tested game; see
`.scratch/phase-1-playable-game/spec.md`.

So far (tickets 01–03), 2–5 Players use the Asteroid, Aquifer, Greenery and City
Standard Projects and convert plants into Greeneries on the Tharsis board. They place
Oceans, Greeneries and Cities by clicking a highlighted Area, and collect placement
bonuses and 2 MegaCredits per adjacent Ocean. The Game ends after the Generation in
which Temperature is maxed, and the highest Terraform Rating wins. Each Player is a
human or a Random Bot, every Game comes from a seed, and any Game can be undone, saved
as a Replay file and loaded again.

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

Then open http://localhost:5173. The setup screen asks for the number of Players, each
Player's Controller (human or Random Bot), a seed (empty for a random one) and how fast
Random Bots pick. With two or more humans (Hotseat), or only Random Bots, the screen shows
the full view; with one human, only that Player's Player View.

During a Game, the top bar shows the seed (click to copy) and has **Undo** (back to the
last Decision a human answered, skipping Random Bot picks), **Save Replay**,
**Load Replay…** and the Random Bot speed. The server keeps the Game in memory, so
reloading the page picks it up again.

## Other checks

- Rust lint: `cargo clippy --manifest-path engine/Cargo.toml`
- GUI type check: `npm --prefix gui run typecheck`

## Where things are

| Path | What |
| --- | --- |
| `engine/src/game.rs` | The rules: Game state, Decisions and Options |
| `engine/src/board.rs` | The Tharsis board: Areas, adjacency, and where each Tile may go |
| `engine/src/scenario.rs` | Starting a Game from a Scenario |
| `engine/src/replay.rs` | Replays: rebuilding a Game from its start and picks |
| `engine/src/random.rs` | The Game's seeded random numbers |
| `engine/src/view.rs` | The Player View and Decisions as plain data for Python |
| `engine/src/log.rs` | The game log |
| `engine/src/lib.rs` | The Python bindings (`tm_engine`) |
| `engine/tm_engine.pyi` | The Python API, for your editor |
| `tests/rules/` | Scenario tests of the rules, through `tm_engine` |
| `tests/engine/` | Tests of the engine module itself: views, copies, Replays, reproducibility |
| `tests/server/` | Tests of the local server over its WebSocket |
| `tests/helpers.py` | `scenario()`, `player()`, `ocean()`, `city()`, `pick()`, `offered()`, `area()`: helpers that make tests read like play |
| `server/` | The local server and the Random Bot |
| `gui/src/` | The browser GUI; the board is `gui/src/components/MarsBoard.tsx` |
| `CONTEXT.md` | The glossary; code, tests and messages use its terms |
| `docs/adr/` | Architecture decisions |
| `docs/rules-notes.md` | Every rules judgment call |
| `.scratch/phase-1-playable-game/` | The phase-1 spec and tickets |
